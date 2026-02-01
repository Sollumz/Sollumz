import os
import traceback
import bpy
from bpy.types import (
    Object,
    Material,
    Armature,
    PoseBone,
    Bone,
    LimitLocationConstraint,
    LimitRotationConstraint,
    ShaderNodeTexImage,
)
from typing import Optional
from mathutils import Matrix
from pathlib import Path
from .shader_materials import create_shader, get_detail_extra_sampler, create_tinted_shader_graph
from ..ybn.ybnimport_io import create_bound_composite, create_bound_object
from ..sollumz_properties import SollumType, SOLLUMZ_UI_NAMES
from ..sollumz_preferences import get_addon_preferences
from szio.gta5 import (
    AssetBound,
    BoundType,
    AssetDrawable,
    Skeleton,
    SkelBone,
    SkelBoneTranslationLimit,
    SkelBoneRotationLimit,
    SkelBoneFlags,
    ShaderGroup,
    ShaderInst,
    LodLevel as IOLodLevel,
    Model,
    ShaderManager,
)
from ..tools.blenderhelper import add_child_of_bone_constraint, create_empty_object, create_blender_object, join_objects, add_armature_modifier, parent_objs
from ..shared.shader_nodes import SzShaderNodeParameter
from .model_data_io import ModelData, get_model_data, get_model_data_split_by_group
from .mesh_builder import MeshBuilder
from .cable_mesh_builder import CableMeshBuilder
from .cable import CABLE_SHADER_NAME
from ..lods import LODLevels, LODLevel
from .lights_io import create_light_objs
from .properties import DrawableModelProperties
from ..iecontext import import_context, ImportTexturesMode
from .. import logger


def import_ydr(asset: AssetDrawable, name: str) -> Object:
    if import_context().settings.import_as_asset:
        return create_drawable_as_asset(asset, name)

    return create_drawable(asset, name=name)


def create_drawable(
    drawable: AssetDrawable,
    hi_drawable: Optional[AssetDrawable] = None,
    name: Optional[str] = None,
    materials: list[Material] = None,
    hi_materials: list[Material] = None,
    external_armature: Optional[Object] = None,
    external_skeleton: Optional[Skeleton] = None,
    skip_models: bool = False
) -> Object:
    """Create a drawable object. . ``external_armature`` allows for bones to be rigged to an armature object that is not the parent drawable."""
    name = name or drawable.name

    extract_embedded_textures(drawable.shader_group)

    materials = materials or shader_group_to_materials(drawable.shader_group)
    hi_materials = hi_materials or []

    skeleton = drawable.skeleton
    has_skeleton = skeleton and len(skeleton.bones) > 0

    if external_skeleton:
        drawable.skeleton = external_skeleton

    if has_skeleton and external_armature is None:
        drawable_obj = create_drawable_root_armature(drawable, name)
    else:
        drawable_obj = create_drawable_root_empty(drawable, name)

    bounds = drawable.bounds
    if bounds is not None:
        create_embedded_collisions(bounds, drawable_obj)

    armature_obj = drawable_obj if drawable_obj.type == "ARMATURE" else external_armature

    if not skip_models:
        if armature_obj is None:
            model_objs = create_drawable_models(
                drawable, hi_drawable, materials, hi_materials, model_names=f"{name}.model"
            )
        else:
            model_objs = create_rigged_drawable_models(
                drawable, hi_drawable, materials, hi_materials, drawable_obj, armature_obj
            )

        parent_objs(model_objs, drawable_obj)

    if (lights := drawable.lights):
        lights_obj = create_light_objs(lights, armature_obj, f"{drawable_obj.name}.lights")
        lights_obj.parent = drawable_obj

    return drawable_obj


def create_drawable_models(
    drawable: AssetDrawable,
    hi_drawable: Optional[AssetDrawable],
    materials: list[Material],
    hi_materials: list[Material],
    model_names: Optional[str] = None
) -> list[Object]:
    model_datas = get_model_data(drawable, hi_drawable)
    model_names = model_names or SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_MODEL]

    return [create_model_obj(model_data, materials, hi_materials, name=model_names) for model_data in model_datas]


def create_rigged_drawable_models(
    drawable: AssetDrawable,
    hi_drawable: Optional[AssetDrawable],
    materials: list[Material],
    hi_materials: list[Material],
    drawable_obj: Object,
    armature_obj: Object
) -> list[Object]:
    if armature_obj.sollum_type == SollumType.FRAGMENT:
        # This setting is really only intended for fragments
        split_by_group = import_context().settings.split_by_group
    else:
        split_by_group = False
    model_datas = get_model_data_split_by_group(
        drawable, hi_drawable) if split_by_group else get_model_data(drawable, hi_drawable)

    set_skinned_model_properties(drawable_obj, drawable)

    return [create_rigged_model_obj(model_data, materials, hi_materials, armature_obj) for model_data in model_datas]


def create_model_obj(model_data: ModelData, materials: list[Material], hi_materials: list[Material], name: str, bones: Optional[list[Bone]] = None) -> Object:
    model_obj = create_blender_object(SollumType.DRAWABLE_MODEL, name)
    create_lod_meshes(model_data, model_obj, materials, hi_materials, bones)
    create_tinted_shader_graph(model_obj)

    return model_obj


def create_rigged_model_obj(model_data: ModelData, materials: list[Material], hi_materials: list[Material], armature_obj: Object) -> Object:
    bones = armature_obj.data.bones
    bone_name = bones[model_data.bone_index].name

    model_obj = create_model_obj(model_data, materials, hi_materials, bone_name, bones)

    if not model_obj.vertex_groups:
        # Non-skinned models use armature constraints to link with bones
        add_child_of_bone_constraint(model_obj, armature_obj, bone_name)
    else:
        add_armature_modifier(model_obj, armature_obj)

    return model_obj


def create_lod_meshes(model_data: ModelData, model_obj: Object, materials: list[Material], hi_materials: list[Material], bones: Optional[list[Bone]] = None):
    lods: LODLevels = model_obj.sz_lods
    original_mesh = model_obj.data

    for lod_level, mesh_data in model_data.mesh_data_lods.items():
        mesh_name = f"{model_obj.name}_{SOLLUMZ_UI_NAMES[lod_level].lower().replace(' ', '_')}"
        lod_materials = hi_materials if lod_level == LODLevel.VERYHIGH else materials

        try:
            if all(m.shader_properties.filename == CABLE_SHADER_NAME for m in materials):
                mesh_builder = CableMeshBuilder(
                    mesh_name,
                    mesh_data.vert_arr,
                    mesh_data.ind_arr,
                    mesh_data.mat_inds,
                    lod_materials
                )
            else:
                mesh_builder = MeshBuilder(
                    mesh_name,
                    mesh_data.vert_arr,
                    mesh_data.ind_arr,
                    mesh_data.mat_inds,
                    lod_materials
                )

            lod_mesh = mesh_builder.build()
        except:
            logger.error(
                f"Error occured during creation of mesh '{mesh_name}'! Is the mesh data valid?\n{traceback.format_exc()}")
            continue

        lods.get_lod(lod_level).mesh = lod_mesh
        lods.active_lod_level = lod_level

        set_drawable_model_properties(lod_mesh.drawable_model_properties, model_data.lods[lod_level])

        is_skinned = "BlendWeights" in mesh_data.vert_arr.dtype.names

        if is_skinned and bones is not None:
            mesh_builder.create_vertex_groups(model_obj, bones)

    lods.set_highest_lod_active()

    # Original mesh no longer used since the obj is managed by LODs, so delete it
    if model_obj.data != original_mesh:
        bpy.data.meshes.remove(original_mesh)


def set_skinned_model_properties(drawable_obj: Object, drawable: AssetDrawable):
    """Set drawable model properties for the skinned ``DrawableModel`` (only ever 1 skinned model per ``Drawable``)."""
    for lod_level, models in drawable.models.items():
        lod_level = LODLevel.from_io(lod_level)
        for model in models:
            if not model.has_skin:
                continue

            skinned_model_props = drawable_obj.skinned_model_properties.get_lod(lod_level)

            set_drawable_model_properties(skinned_model_props, model)


def set_drawable_model_properties(model_props: DrawableModelProperties, model: Model):
    model_props.render_mask = model.render_bucket_mask


def create_drawable_root_armature(drawable: AssetDrawable, name: str) -> Object:
    drawable_obj = create_armature_obj_from_skel(drawable.skeleton, name, SollumType.DRAWABLE)
    set_drawable_properties(drawable_obj, drawable)

    return drawable_obj


def create_armature_obj_from_skel(skeleton: Skeleton, name: str, sollum_type: SollumType) -> Object:
    armature = bpy.data.armatures.new(f"{name}.skel")
    obj = create_blender_object(sollum_type, name, armature)

    create_drawable_skel(obj, skeleton)

    return obj


def create_drawable_root_empty(drawable: AssetDrawable, name: str) -> Object:
    drawable_obj = create_empty_object(SollumType.DRAWABLE, name)
    set_drawable_properties(drawable_obj, drawable)

    return drawable_obj


def extract_embedded_textures(shader_group: ShaderGroup | None):
    import shutil

    if not shader_group or not shader_group.embedded_textures:
        return

    ctx = import_context()
    if ctx.settings.textures_mode == ImportTexturesMode.PACK:
        return

    textures = [t.data for t in shader_group.embedded_textures.values() if t.data is not None]
    if not textures and ctx.settings.textures_mode == ImportTexturesMode.CUSTOM_DIR:
        # If no embedded textures data (e.g. importing CWXML), try to lookup external texture files in import directory
        # so we can copy them to the user custom directory
        textures_import_dir = ctx.textures_import_directory
        if textures_import_dir.is_dir():
            from szio.types import DataSource
            textures = [
                DataSource.create(p)
                for t in shader_group.embedded_textures.values()
                if (p := textures_import_dir / f"{t.name}.dds").is_file()
            ]

    if not textures:
        return

    textures_extract_dir = ctx.textures_extract_directory
    if textures_extract_dir is None:
        return

    textures_extract_dir.mkdir(parents=True, exist_ok=True)
    for tex_data in textures:
        tex_file = textures_extract_dir / tex_data.name
        if tex_file.exists():
            # Don't overwrite existing files
            continue

        with tex_data.open() as src, tex_file.open("wb") as dst:
            shutil.copyfileobj(src, dst)


def shader_group_to_materials(shader_group: ShaderGroup) -> list[Material]:
    return shader_group_to_materials_with_hi(shader_group, None)[0]


def shader_group_to_materials_with_hi(
    shader_group: ShaderGroup,
    hi_shader_group: Optional[ShaderGroup],
) -> tuple[list[Material], list[Material]]:

    materials_cache: dict[ShaderInst, Material] = {}

    def _build_materials(sg: ShaderGroup) -> list[Material]:
        result = []
        for shader in sg.shaders:
            material = materials_cache.get(shader, None)
            if material is None:
                material = shader_to_material(shader, sg)
                material.shader_properties.index = len(materials_cache)
                materials_cache[shader] = material
            result.append(material)
        return result

    materials = _build_materials(shader_group)
    hi_materials = _build_materials(hi_shader_group) if hi_shader_group is not None else []

    return materials, hi_materials


def shader_to_material(shader: ShaderInst, shader_group: ShaderGroup) -> Material:
    ctx = import_context()
    textures_dir = ctx.textures_extract_directory or ctx.textures_import_directory

    filename = shader.preset_filename or ShaderManager.find_shader_preset_name(shader.name, shader.render_bucket.value)
    if not filename:
        filename = f"{shader.name}.sps"

    # Fix for importing gen9 assets using ped_decal_exp shader. Gen9 doesn't have preset files so CW just appends
    # .sps to the shader name, which most of the time is correct, but for ped_decal_exp the preset file was
    # ped_decal_expensive.sps and that's what we have in our shader definitions. Normalize the naming here.
    if filename.lower() in {"hash_1a87324e", "ped_decal_exp.sps"}:
        filename = "ped_decal_expensive.sps"

    material = create_shader(filename)
    material.shader_properties.renderbucket = shader.render_bucket.name

    nodes = {
        n.name.lower(): n
        for n in material.node_tree.nodes
        if isinstance(n, (ShaderNodeTexImage, SzShaderNodeParameter))
    }
    for param in shader.parameters:
        param_name = param.name.lower()
        n = nodes.get(param_name, None)
        if n is None:
            continue

        if isinstance(n, ShaderNodeTexImage):
            tex_name = param.value
            if not tex_name:
                # Skip unassigned texture shader parameters
                continue

            tex_name_dds = f"{tex_name}.dds"
            pack = ctx.settings.textures_mode == ImportTexturesMode.PACK
            img = None

            if (
                pack and
                (etex := shader_group.embedded_textures.get(tex_name, None)) and
                etex.data
            ):
                # If pack mode and we have embedded texture data, load it into a packed image directly
                with etex.data.open() as src:
                    etex_dds = src.read()

                img = bpy.data.images.new(name=tex_name_dds, width=1, height=1)
                img.source = "FILE"
                img.filepath = f"//{tex_name_dds}"
                img.pack(data=etex_dds, data_len=len(etex_dds))

            if not img:
                # Try to load texture from file
                if texture_path := lookup_texture_file(tex_name, textures_dir):
                    img = bpy.data.images.load(str(texture_path), check_existing=True)
                    if pack:
                        img.pack()

            if not img:
                # Check for existing texture image
                img = bpy.data.images.get(tex_name, None) or bpy.data.images.get(tex_name_dds, None)

            if not img:
                # Create placeholder image if still not found
                img = bpy.data.images.new(name=tex_name, width=512, height=512)

            if is_non_color_texture(filename, param_name):
                img.colorspace_settings.is_data = True

            preferences = get_addon_preferences(bpy.context)
            if preferences.use_text_name_as_mat_name and param_name == "diffusesampler":
                material.name = tex_name

            if tex_name in shader_group.embedded_textures:
                n.texture_properties.embedded = True

            if not n.texture_properties.embedded and not img.filepath:
                # Set external texture name for non-embedded textures
                img.source = "FILE"
                img.filepath = f"//{tex_name_dds}"

            n.image = img

        elif isinstance(n, SzShaderNodeParameter):
            if n.num_rows == 1:
                n.set("X", param.value.x)
                if n.num_cols > 1:
                    n.set("Y", param.value.y)
                if n.num_cols > 2:
                    n.set("Z", param.value.z)
                if n.num_cols > 3:
                    n.set("W", param.value.w)

    # assign extra detail node image for viewing
    dtl_ext = get_detail_extra_sampler(material)
    if dtl_ext:
        dtl = material.node_tree.nodes["DetailSampler"]
        dtl_ext.image = dtl.image

    return material


def lookup_texture_file(texture_name: str, model_textures_directory: Optional[Path]) -> Optional[Path]:
    """Searches for a DDS file with the given ``texture_name``.
    The search order is as follows:
      1. Check if file exists in ``model_textures_directory``.
      2. Check the shared textures directories defined by the user in the add-on preferences.
        2.1. These are searched in the priority order set by the user.
        2.2. The user can also set whether the search is recursive or not.
      3. If not found, returns ``None``.
    """
    texture_filename = f"{texture_name}.dds"

    def _lookup_in_directory(directory: Path, recursive: bool) -> Optional[Path]:
        if not directory.is_dir():
            return None

        if recursive:
            # NOTE: rglob returns files in arbitrary order. We are just taking whatever is the first one it returns.
            #       Maybe we should enforce some kind of sort (i.e. alphabetical), but really only makes sense to have
            #       a single texture with this the name in the directory tree.
            texture_path = next(directory.rglob(texture_filename), None)
        else:
            texture_path = directory.joinpath(texture_filename)

        return texture_path if texture_path is not None and texture_path.is_file() else None

    # First, check the textures directory next to the model we imported
    found_texture_path = model_textures_directory and _lookup_in_directory(model_textures_directory, False)
    if found_texture_path is not None:
        return found_texture_path

    # Texture not found, search the shared textures directories listed in preferences
    prefs = get_addon_preferences(bpy.context)
    for d in prefs.shared_textures_directories:
        found_texture_path = _lookup_in_directory(Path(d.path), d.recursive)
        if found_texture_path is not None:
            return found_texture_path

    # Texture still not found
    return None


def is_non_color_texture(shader_filename: str, param_name: str) -> bool:
    """Check if this texture parameter contains non-color data."""
    # TODO: we could specify non-color textures in shaders.xml
    # assign non-color...
    param_name = param_name.lower()
    return (
        "bump" in param_name or  # ...to normal maps
        param_name == "distancemapsampler" or  # ...to distance maps
        (shader_filename in {"decal_dirt.sps", "decal_amb_only.sps"}
         and param_name == "diffusesampler")  # ...to shadow maps
    )


def create_drawable_skel(armature_obj: Object, skeleton: Skeleton):
    bpy.context.view_layer.objects.active = armature_obj
    bones = skeleton.bones

    # Need to go into edit mode to modify edit bones
    bpy.ops.object.mode_set(mode="EDIT")

    for b in bones:
        add_bone(armature_obj.data, b)

    bpy.ops.object.mode_set(mode="OBJECT")

    for b in bones:
        set_bone_properties(armature_obj.data, b)
        add_bone_constraints(armature_obj, b)

    return armature_obj


def add_bone(armature: Armature, bone: SkelBone):
    edit_bone = armature.edit_bones.new(bone.name)
    if bone.parent_index != -1:
        edit_bone.parent = armature.edit_bones[bone.parent_index]

    # https://github.com/LendoK/Blender_GTA_V_model_importer/blob/master/importer.py
    mat_rot = bone.rotation.to_matrix().to_4x4()
    mat_loc = Matrix.Translation(bone.position)
    mat_sca = Matrix.Scale(1, 4, bone.scale)

    edit_bone.head = (0, 0, 0)
    edit_bone.tail = (0, 0.05, 0)
    edit_bone.matrix = mat_loc @ mat_rot @ mat_sca

    if edit_bone.parent is not None:
        edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix


def set_bone_properties(armature: Armature, bone: SkelBone):
    bl_bone = armature.bones[bone.name]
    bl_bone.bone_properties.tag = bone.tag

    for _flag in bone.flags:
        # LimitRotation and Unk0 have their special meanings, can be deduced if needed when exporting
        if _flag & (SkelBoneFlags.HAS_ROTATE_LIMITS | SkelBoneFlags.HAS_CHILD):
            continue

        # flags still use the CW names for backwards compatibility
        from szio.gta5.cwxml.adapters.drawable import CW_BONE_FLAGS_INVERSE_MAP
        flag = bl_bone.bone_properties.flags.add()
        flag.name = CW_BONE_FLAGS_INVERSE_MAP[_flag]


def add_bone_constraints(armature_obj: Object, bone: SkelBone):
    pose_bone = armature_obj.pose.bones[bone.name]

    if bone.translation_limit:
        add_bone_constraint_translation_limit(pose_bone, bone.translation_limit)

    if bone.rotation_limit:
        add_bone_constraint_rotation_limit(pose_bone, bone.rotation_limit)


def add_bone_constraint_rotation_limit(pose_bone: PoseBone, limit: SkelBoneRotationLimit) -> LimitRotationConstraint:
    constraint = pose_bone.constraints.new("LIMIT_ROTATION")
    constraint.owner_space = "LOCAL"
    constraint.use_limit_x = True
    constraint.use_limit_y = True
    constraint.use_limit_z = True
    constraint.max_x = limit.max.x
    constraint.max_y = limit.max.y
    constraint.max_z = limit.max.z
    constraint.min_x = limit.min.x
    constraint.min_y = limit.min.y
    constraint.min_z = limit.min.z
    return constraint


def add_bone_constraint_translation_limit(pose_bone: PoseBone, limit: SkelBoneTranslationLimit) -> LimitLocationConstraint:
    constraint = pose_bone.constraints.new("LIMIT_LOCATION")
    constraint.owner_space = "LOCAL"
    constraint.use_min_x = True
    constraint.use_min_y = True
    constraint.use_min_z = True
    constraint.use_max_x = True
    constraint.use_max_y = True
    constraint.use_max_z = True
    constraint.max_x = limit.max.x
    constraint.max_y = limit.max.y
    constraint.max_z = limit.max.z
    constraint.min_x = limit.min.x
    constraint.min_y = limit.min.y
    constraint.min_z = limit.min.z
    return constraint


def create_embedded_collisions(bounds: AssetBound, drawable_obj: bpy.types.Object):
    if bounds.bound_type == BoundType.COMPOSITE:
        bound_obj = create_bound_composite(bounds, name=f"{drawable_obj.name}.col")
    else:
        bound_obj = create_bound_object(bounds)

    bound_obj.parent = drawable_obj


def set_drawable_properties(obj: Object, drawable: AssetDrawable):
    lod_dists = drawable.lod_thresholds
    obj.drawable_properties.lod_dist_high = lod_dists[IOLodLevel.HIGH]
    obj.drawable_properties.lod_dist_med = lod_dists[IOLodLevel.MEDIUM]
    obj.drawable_properties.lod_dist_low = lod_dists[IOLodLevel.LOW]
    obj.drawable_properties.lod_dist_vlow = lod_dists[IOLodLevel.VERYLOW]


def create_drawable_as_asset(drawable: AssetDrawable, name: str) -> Object:
    """Create drawable as an asset with all the high LODs joined together."""
    models = drawable.models
    models.pop(IOLodLevel.MEDIUM, None)
    models.pop(IOLodLevel.LOW, None)
    models.pop(IOLodLevel.VERYLOW, None)
    drawable.models = models
    drawable.bounds = None
    drawable.lights = []

    drawable_obj = create_drawable(drawable)

    from .ydrimport import convert_object_to_asset
    return convert_object_to_asset(name, drawable_obj)
