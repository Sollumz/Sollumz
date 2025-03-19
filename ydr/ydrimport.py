import os
import traceback
import bpy
from typing import Optional
from mathutils import Matrix
from pathlib import Path
from ..tools.drawablehelper import get_model_xmls_by_lod
from .shader_materials import create_shader, get_detail_extra_sampler, create_tinted_shader_graph
from ..ybn.ybnimport import create_bound_composite, create_bound_object
from ..sollumz_properties import SollumType, SOLLUMZ_UI_NAMES
from ..sollumz_preferences import get_addon_preferences, get_import_settings
from ..cwxml.drawable import YDR, BoneLimit, Joints, Shader, ShaderGroup, Drawable, Bone, Skeleton, RotationLimit, DrawableModel
from ..cwxml.bound import Bound
from ..tools.blenderhelper import add_child_of_bone_constraint, create_empty_object, create_blender_object, join_objects, add_armature_modifier, parent_objs
from ..tools.utils import get_filename
from ..shared.shader_nodes import SzShaderNodeParameter
from .model_data import ModelData, get_model_data, get_model_data_split_by_group
from .mesh_builder import MeshBuilder
from .cable_mesh_builder import CableMeshBuilder
from .cable import CABLE_SHADER_NAME
from ..lods import LODLevels
from .lights import create_light_objs
from .properties import DrawableModelProperties
from .render_bucket import RenderBucket
from .. import logger


def import_ydr(filepath: str):
    import_settings = get_import_settings()

    name = get_filename(filepath)
    ydr_xml = YDR.from_xml_file(filepath)

    if import_settings.import_as_asset:
        return create_drawable_as_asset(ydr_xml, name, filepath)

    return create_drawable_obj(ydr_xml, filepath, name)


def create_drawable_obj(drawable_xml: Drawable, filepath: str, name: Optional[str] = None, split_by_group: bool = False, external_armature: Optional[bpy.types.Object] = None, external_bones: Optional[list[Bone]] = None, materials: Optional[list[bpy.types.Material]] = None):
    """Create a drawable object. ``split_by_group`` will split each Drawable Model by vertex group. ``external_armature`` allows for bones to be rigged to an armature object that is not the parent drawable."""
    name = name or drawable_xml.name
    materials = materials or shadergroup_to_materials(drawable_xml.shader_group, filepath)

    has_skeleton = len(drawable_xml.skeleton.bones) > 0

    if external_bones:
        drawable_xml.skeleton.bones = external_bones

    if has_skeleton and external_armature is None:
        drawable_obj = create_drawable_armature(drawable_xml, name)
    else:
        drawable_obj = create_drawable_empty(name, drawable_xml)

    if drawable_xml.bounds is not None:
        create_embedded_collisions(drawable_xml.bounds, drawable_obj)

    armature_obj = drawable_obj if drawable_obj.type == "ARMATURE" else external_armature
    if armature_obj is None:
        model_objs = create_drawable_models(
            drawable_xml, materials, model_names=f"{name}.model")
    else:
        model_objs = create_rigged_drawable_models(
            drawable_xml, materials, drawable_obj, armature_obj, split_by_group)

    parent_objs(model_objs, drawable_obj)

    if drawable_xml.lights:
        create_drawable_lights(drawable_xml, drawable_obj, armature_obj)

    return drawable_obj


def create_drawable_models(drawable_xml: Drawable, materials: list[bpy.types.Material], model_names: Optional[str] = None):
    model_datas = get_model_data(drawable_xml)
    model_names = model_names or SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_MODEL]

    return [create_model_obj(model_data, materials, name=model_names) for model_data in model_datas]


def create_rigged_drawable_models(drawable_xml: Drawable, materials: list[bpy.types.Material], drawable_obj: bpy.types.Object, armature_obj: bpy.types.Object, split_by_group: bool = False):
    model_datas = get_model_data(
        drawable_xml) if not split_by_group else get_model_data_split_by_group(drawable_xml)

    set_skinned_model_properties(drawable_obj, drawable_xml)

    return [create_rigged_model_obj(model_data, materials, armature_obj) for model_data in model_datas]


def create_model_obj(model_data: ModelData, materials: list[bpy.types.Material], name: str, bones: Optional[list[bpy.types.Bone]] = None):
    model_obj = create_blender_object(SollumType.DRAWABLE_MODEL, name)
    create_lod_meshes(model_data, model_obj, materials, bones)
    create_tinted_shader_graph(model_obj)

    return model_obj


def create_rigged_model_obj(model_data: ModelData, materials: list[bpy.types.Material], armature_obj: bpy.types.Object):
    bones = armature_obj.data.bones
    bone_name = bones[model_data.bone_index].name

    model_obj = create_model_obj(model_data, materials, bone_name, bones)

    if not model_obj.vertex_groups:
        # Non-skinned models use armature constraints to link with bones
        add_child_of_bone_constraint(model_obj, armature_obj, bone_name)
    else:
        add_armature_modifier(model_obj, armature_obj)

    return model_obj


def create_lod_meshes(model_data: ModelData, model_obj: bpy.types.Object, materials: list[bpy.types.Material], bones: Optional[list[bpy.types.Bone]] = None):
    lods: LODLevels = model_obj.sz_lods
    original_mesh = model_obj.data

    for lod_level, mesh_data in model_data.mesh_data_lods.items():
        mesh_name = f"{model_obj.name}_{SOLLUMZ_UI_NAMES[lod_level].lower().replace(' ', '_')}"

        try:
            if all(m.shader_properties.filename == CABLE_SHADER_NAME for m in materials):
                mesh_builder = CableMeshBuilder(
                    mesh_name,
                    mesh_data.vert_arr,
                    mesh_data.ind_arr,
                    mesh_data.mat_inds,
                    materials
                )
            else:
                mesh_builder = MeshBuilder(
                    mesh_name,
                    mesh_data.vert_arr,
                    mesh_data.ind_arr,
                    mesh_data.mat_inds,
                    materials
                )

            lod_mesh = mesh_builder.build()
        except:
            logger.error(
                f"Error occured during creation of mesh '{mesh_name}'! Is the mesh data valid?\n{traceback.format_exc()}")
            continue

        lods.get_lod(lod_level).mesh = lod_mesh
        lods.active_lod_level = lod_level

        set_drawable_model_properties(lod_mesh.drawable_model_properties, model_data.xml_lods[lod_level])

        is_skinned = "BlendWeights" in mesh_data.vert_arr.dtype.names

        if is_skinned and bones is not None:
            mesh_builder.create_vertex_groups(model_obj, bones)

    lods.set_highest_lod_active()

    # Original mesh no longer used since the obj is managed by LODs, so delete it
    if model_obj.data != original_mesh:
        bpy.data.meshes.remove(original_mesh)


def set_skinned_model_properties(drawable_obj: bpy.types.Object, drawable_xml: Drawable):
    """Set drawable model properties for the skinned ``DrawableModel`` (only ever 1 skinned model per ``Drawable``)."""
    for lod_level, models in get_model_xmls_by_lod(drawable_xml).items():
        for model_xml in models:
            if model_xml.has_skin == 0:
                continue

            skinned_model_props = drawable_obj.skinned_model_properties.get_lod(
                lod_level)

            set_drawable_model_properties(skinned_model_props, model_xml)


def set_lod_model_properties(model_objs: list[bpy.types.Object], drawable_xml: Drawable):
    """Set drawable model properties for each LOD mesh in ``model_objs``."""
    for lod_level, models in get_model_xmls_by_lod(drawable_xml).items():
        for i, model_xml in enumerate(models):
            obj = model_objs[i]
            obj_lods: LODLevels = obj.sz_lods
            lod = obj_lods.get_lod(lod_level)
            lod_mesh = lod.mesh
            if lod_mesh is None:
                continue

            set_drawable_model_properties(lod_mesh.drawable_model_properties, model_xml[lod.level])


def set_drawable_model_properties(model_props: DrawableModelProperties, model_xml: DrawableModel):
    model_props.render_mask = model_xml.render_mask


def create_drawable_armature(drawable_xml: Drawable, name: str):
    drawable_obj = create_armature_obj_from_skel(
        drawable_xml.skeleton, name, SollumType.DRAWABLE)
    create_joint_constraints(drawable_obj, drawable_xml.joints)

    set_drawable_properties(drawable_obj, drawable_xml)

    return drawable_obj


def create_armature_obj_from_skel(skeleton: Skeleton, name: str, sollum_type: SollumType):
    armature = bpy.data.armatures.new(f"{name}.skel")
    obj = create_blender_object(sollum_type, name, armature)

    create_drawable_skel(skeleton, obj)

    return obj


def create_joint_constraints(armature_obj: bpy.types.Object, joints: Joints):
    if joints.rotation_limits:
        apply_rotation_limits(joints.rotation_limits, armature_obj)

    if joints.translation_limits:
        apply_translation_limits(joints.translation_limits, armature_obj)


def create_drawable_empty(name: str, drawable_xml: Drawable):
    drawable_obj = create_empty_object(SollumType.DRAWABLE, name)
    set_drawable_properties(drawable_obj, drawable_xml)

    return drawable_obj


def shadergroup_to_materials(shader_group: ShaderGroup, filepath: str):
    materials = []

    for i, shader in enumerate(shader_group.shaders):
        material = shader_item_to_material(shader, shader_group, filepath)
        material.shader_properties.index = i
        materials.append(material)

    return materials


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


def is_non_color_texture(shader_filename: str, param_name: str):
    # TODO: we could specify non-color textures in shaders.xml
    # assign non-color...
    return (
        "Bump" in param_name or  # ...to normal maps
        param_name == "distanceMapSampler" or  # ...to distance maps
        (shader_filename == "decal_dirt.sps" and param_name == "DiffuseSampler") # ...to shadow maps
    )


def shader_item_to_material(shader: Shader, shader_group: ShaderGroup, filepath: str):
    texture_folder = Path(os.path.dirname(filepath) + "\\" + os.path.basename(filepath)[:-8])

    filename = shader.filename

    if not filename:
        filename = f"{shader.name}.sps"

    material = create_shader(filename)
    material.shader_properties.renderbucket = RenderBucket(shader.render_bucket).name

    for param in shader.parameters:
        for n in material.node_tree.nodes:
            if isinstance(n, bpy.types.ShaderNodeTexImage):
                if param.name == n.name:
                    texture_path = lookup_texture_file(param.texture_name, texture_folder)
                    if texture_path is not None:
                        img = bpy.data.images.load(str(texture_path), check_existing=True)
                        n.image = img

                    if not n.image:
                        # for texture shader parameters with no name
                        if not param.texture_name:
                            continue
                        # Check for existing texture
                        existing_texture = None
                        for image in bpy.data.images:
                            if image.name == param.texture_name:
                                existing_texture = image
                        texture = bpy.data.images.new(
                            name=param.texture_name, width=512, height=512) if not existing_texture else existing_texture
                        n.image = texture

                    if is_non_color_texture(filename, param.name):
                        n.image.colorspace_settings.is_data = True

                    preferences = get_addon_preferences(bpy.context)
                    text_name = preferences.use_text_name_as_mat_name
                    if text_name:
                        if param.texture_name and param.name == "DiffuseSampler":
                            material.name = param.texture_name

                    # Assign embedded texture dictionary properties
                    if shader_group.texture_dictionary is not None:
                        for texture in shader_group.texture_dictionary:
                            if texture.name == param.texture_name:
                                n.texture_properties.embedded = True

                    if not n.texture_properties.embedded and not n.image.filepath:
                        # Set external texture name for non-embedded textures
                        n.image.source = "FILE"
                        n.image.filepath = "//" + param.texture_name + ".dds"

            elif isinstance(n, SzShaderNodeParameter):
                if param.name == n.name and n.num_rows == 1:
                    n.set("X", param.x)
                    if n.num_cols > 1:
                        n.set("Y", param.y)
                    if n.num_cols > 2:
                        n.set("Z", param.z)
                    if n.num_cols > 3:
                        n.set("W", param.w)

    # assign extra detail node image for viewing
    dtl_ext = get_detail_extra_sampler(material)
    if dtl_ext:
        dtl = material.node_tree.nodes["DetailSampler"]
        dtl_ext.image = dtl.image

    return material


def create_drawable_skel(skeleton_xml: Skeleton, armature_obj: bpy.types.Object):
    bpy.context.view_layer.objects.active = armature_obj
    bones = skeleton_xml.bones

    # Need to go into edit mode to modify edit bones
    bpy.ops.object.mode_set(mode="EDIT")

    for bone_xml in bones:
        create_bpy_bone(bone_xml, armature_obj.data)

    bpy.ops.object.mode_set(mode="OBJECT")

    for bone_xml in bones:
        set_bone_properties(bone_xml, armature_obj.data)

    return armature_obj


def create_bpy_bone(bone_xml: Bone, armature: bpy.types.Armature):
    # bpy.context.view_layer.objects.active = armature
    edit_bone = armature.edit_bones.new(bone_xml.name)
    if bone_xml.parent_index != -1:
        edit_bone.parent = armature.edit_bones[bone_xml.parent_index]

    # https://github.com/LendoK/Blender_GTA_V_model_importer/blob/master/importer.py
    mat_rot = bone_xml.rotation.to_matrix().to_4x4()
    mat_loc = Matrix.Translation(bone_xml.translation)
    mat_sca = Matrix.Scale(1, 4, bone_xml.scale)

    edit_bone.head = (0, 0, 0)
    edit_bone.tail = (0, 0.05, 0)
    edit_bone.matrix = mat_loc @ mat_rot @ mat_sca

    if edit_bone.parent is not None:
        edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix

    return bone_xml.name


def set_bone_properties(bone_xml: Bone, armature: bpy.types.Armature):
    bl_bone = armature.bones[bone_xml.name]
    bl_bone.bone_properties.tag = bone_xml.tag

    # LimitRotation and Unk0 have their special meanings, can be deduced if needed when exporting
    flags_restricted = set(["LimitRotation", "Unk0"])
    for _flag in bone_xml.flags:
        if _flag in flags_restricted:
            continue

        flag = bl_bone.bone_properties.flags.add()
        flag.name = _flag


def apply_rotation_limits(rotation_limits: list[RotationLimit], armature_obj: bpy.types.Object):
    bone_by_tag: dict[str, bpy.types.PoseBone] = get_bone_by_tag(armature_obj)

    for rot_limit in rotation_limits:
        if rot_limit.bone_id not in bone_by_tag:
            logger.warning(
                f"{armature_obj.name} contains a rotation limit with an invalid bone id '{rot_limit.bone_id}'! Skipping...")
            continue

        bone = bone_by_tag[rot_limit.bone_id]
        create_limit_rot_bone_constraint(rot_limit, bone)


def apply_translation_limits(translation_limits: list[BoneLimit], armature_obj: bpy.types.Object):
    bone_by_tag: dict[str, bpy.types.PoseBone] = get_bone_by_tag(armature_obj)

    for trans_limit in translation_limits:
        if trans_limit.bone_id not in bone_by_tag:
            logger.warning(
                f"{armature_obj.name} contains a translation limit with an invalid bone id '{trans_limit.bone_id}'! Skipping...")
            continue

        bone = bone_by_tag[trans_limit.bone_id]
        create_limit_pos_bone_constraint(trans_limit, bone)


def get_bone_by_tag(armature_obj: bpy.types.Object):
    bone_by_tag: dict[str, bpy.types.PoseBone] = {}

    for pose_bone in armature_obj.pose.bones:
        bone_tag = pose_bone.bone.bone_properties.tag
        bone_by_tag[bone_tag] = pose_bone

    return bone_by_tag


def create_limit_rot_bone_constraint(rot_limit: RotationLimit, pose_bone: bpy.types.PoseBone):
    constraint = pose_bone.constraints.new("LIMIT_ROTATION")
    constraint.owner_space = "LOCAL"
    constraint.use_limit_x = True
    constraint.use_limit_y = True
    constraint.use_limit_z = True
    constraint.max_x = rot_limit.max.x
    constraint.max_y = rot_limit.max.y
    constraint.max_z = rot_limit.max.z
    constraint.min_x = rot_limit.min.x
    constraint.min_y = rot_limit.min.y
    constraint.min_z = rot_limit.min.z


def create_limit_pos_bone_constraint(trans_limit: BoneLimit, pose_bone: bpy.types.PoseBone):
    constraint = pose_bone.constraints.new("LIMIT_LOCATION")
    constraint.owner_space = "LOCAL"
    constraint.use_min_x = True
    constraint.use_min_y = True
    constraint.use_min_z = True
    constraint.use_max_x = True
    constraint.use_max_y = True
    constraint.use_max_z = True
    constraint.max_x = trans_limit.max.x
    constraint.max_y = trans_limit.max.y
    constraint.max_z = trans_limit.max.z
    constraint.min_x = trans_limit.min.x
    constraint.min_y = trans_limit.min.y
    constraint.min_z = trans_limit.min.z


def create_embedded_collisions(bounds_xml: Bound, drawable_obj: bpy.types.Object):
    if bounds_xml.type == "Composite":
        bound_obj = create_bound_composite(bounds_xml)
        bound_obj.name = f"{drawable_obj.name}.col"
    else:
        bound_obj = create_bound_object(bounds_xml)

    bound_obj.parent = drawable_obj


def create_drawable_lights(drawable_xml: Drawable, drawable_obj: bpy.types.Object, armature_obj: Optional[bpy.types.Object] = None):
    lights = create_light_objs(drawable_xml.lights, armature_obj)
    lights.parent = drawable_obj


def set_drawable_properties(obj: bpy.types.Object, drawable_xml: Drawable):
    obj.drawable_properties.lod_dist_high = drawable_xml.lod_dist_high
    obj.drawable_properties.lod_dist_med = drawable_xml.lod_dist_med
    obj.drawable_properties.lod_dist_low = drawable_xml.lod_dist_low
    obj.drawable_properties.lod_dist_vlow = drawable_xml.lod_dist_vlow


def create_drawable_as_asset(drawable_xml: Drawable, name: str, filepath: str):
    """Create drawable as an asset with all the high LODs joined together."""
    drawable_xml.drawable_models_low = []
    drawable_xml.drawable_models_med = []
    drawable_xml.drawable_models_vlow = []

    drawable_xml.bounds = None
    drawable_xml.lights = None

    drawable_obj = create_drawable_obj(drawable_xml, filepath)
    root_transform = drawable_obj.matrix_world.copy()

    model_objs = []

    for child in drawable_obj.children:
        if child.sollum_type == SollumType.DRAWABLE_MODEL:
            model_objs.append(child)

    joined_obj = join_objects(model_objs)
    joined_transform = joined_obj.matrix_world.copy()
    joined_obj.parent = None
    joined_obj.name = name
    joined_obj.data.name = f"{name}.mesh"

    # Fix origin of the drawable, the joined object ends up with the origin of the first model selected, which does not
    # always have the same origin as the drawable itself
    joined_obj.data.transform(root_transform.inverted_safe() @ joined_transform)

    for modifier in joined_obj.modifiers:
        if modifier.type == "ARMATURE":
            joined_obj.modifiers.remove(modifier)

    for constraint in joined_obj.constraints:
        joined_obj.constraints.remove(constraint)

    bpy.context.collection.objects.unlink(joined_obj)

    armature = drawable_obj.data
    bpy.data.objects.remove(drawable_obj)
    if armature:
        bpy.data.armatures.remove(armature)

    joined_obj.asset_mark()
    joined_obj.asset_generate_preview()

    return joined_obj
