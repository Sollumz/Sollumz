import bmesh
import bpy
from bpy.types import (
    Object,
    Material,
    Mesh,
    Bone,
    VertexGroup,
    Armature,
    PoseBone,
    ShaderNodeTexImage,
    LimitLocationConstraint,
    LimitRotationConstraint,
)
import numpy as np
from numpy.typing import NDArray
from typing import Optional
from collections import defaultdict
from dataclasses import replace
from pathlib import Path
from mathutils import Quaternion, Vector, Matrix

from ..lods import operates_on_lod_level

from szio.types import DataSource
from szio.gta5 import (
    create_asset_drawable,
    AssetBound,
    AssetDrawable,
    LodLevel as IOLodLevel,
    EmbeddedTexture,
    ShaderGroup,
    ShaderInst,
    ShaderParameter,
    Model,
    VertexDataType,
    Geometry,
    Skeleton,
    SkelBone,
    SkelBoneTranslationLimit,
    SkelBoneRotationLimit,
    SkelBoneFlags,
    CharacterCloth,
)
from szio.gta5.shader import (
    ShaderManager,
    ShaderDef,
    ShaderParameterFloatVectorDef,
    ShaderParameterType,
)
from ..tools.meshhelper import (
    get_mesh_used_colors_indices,
    get_mesh_used_texcoords_indices,
    get_used_colors,
    get_used_texcoords,
    get_uv_map_name,
    get_color_attr_name,
    get_normal_required,
    get_tangent_required,
)
from ..shared.shader_nodes import SzShaderNodeParameter
from ..tools.blenderhelper import get_child_of_constraint, remove_number_suffix, get_evaluated_obj
from ..sollumz_helper import get_export_transforms_to_apply, get_sollumz_materials
from ..sollumz_properties import (
    BOUND_TYPES,
    LODLevel,
    SollumType
)
from ..ybn.ybnexport_io import (
    create_bound_composite_asset,
    create_bound_asset,
)
from .properties import get_model_properties
from .render_bucket import RenderBucket
from .vertex_buffer_builder import VertexBufferBuilder, VBBuilderDomain, dedupe_and_get_indices, remove_arr_field, remove_unused_colors, try_get_bone_by_vgroup, remove_unused_uvs
from .cable_vertex_buffer_builder import CableVertexBufferBuilder
from .cable import is_cable_mesh
from .cloth_diagnostics import cloth_export_context
from .lights_io import export_lights

from ..iecontext import export_context, ExportBundle
from .. import logger


def export_ydr(obj: Object) -> ExportBundle:
    embedded_tex = []
    d = create_drawable_asset(obj, out_embedded_textures=embedded_tex)
    return export_context().make_bundle(d, extra_files=[t.data for t in embedded_tex])


def create_drawable_asset(
    drawable_obj: Object,
    armature_obj: Optional[Object] = None,
    materials: Optional[list[Material]] = None,
    is_frag: bool = False,
    parent_drawable: Optional[AssetDrawable] = None,
    out_embedded_textures: list[EmbeddedTexture] | None = None,
    hi: bool = False,
    char_cloth: CharacterCloth | None = None,
) -> Optional[AssetDrawable]:
    """Create a ``Drawable`` cwxml object. Optionally specify an external ``armature_obj`` if ``drawable_obj`` is not an armature."""

    materials = materials or get_sollumz_materials(drawable_obj)

    if parent_drawable is not None:
        shader_group = None
    else:
        shader_group = create_shader_group(materials)
        if not shader_group.shaders:
            logger.warning(
                f"{drawable_obj.name} has no Sollumz materials! Aborting..."
            )
            return None

        if out_embedded_textures is not None:
            out_embedded_textures.extend(shader_group.embedded_textures.values())

    drawable = create_asset_drawable(export_context().settings.targets, is_frag, parent_drawable)
    drawable.name = remove_number_suffix(drawable_obj.name.lower())
    drawable.lod_thresholds = {
        IOLodLevel.HIGH: drawable_obj.drawable_properties.lod_dist_high,
        IOLodLevel.MEDIUM: drawable_obj.drawable_properties.lod_dist_med,
        IOLodLevel.LOW: drawable_obj.drawable_properties.lod_dist_low,
        IOLodLevel.VERYLOW: drawable_obj.drawable_properties.lod_dist_vlow,
    }
    drawable.shader_group = shader_group

    if armature_obj or drawable_obj.type == "ARMATURE":
        armature_obj = armature_obj or drawable_obj
        drawable.skeleton = create_skeleton(armature_obj, export_context().settings.apply_transforms)

        original_pose = armature_obj.data.pose_position
        armature_obj.data.pose_position = "REST"
    else:
        drawable.skeleton = None

        armature_obj = None
        original_pose = None

    drawable.models = create_models(drawable, drawable_obj, materials, armature_obj, hi=hi, char_cloth=char_cloth)
    if not is_frag:
        drawable.lights = export_lights(drawable_obj)
        drawable.bounds = create_embedded_bounds_asset(drawable_obj)

    if armature_obj is not None:
        armature_obj.data.pose_position = original_pose

    return drawable


def create_models(
    drawable: AssetDrawable,
    drawable_obj: Object,
    materials: list[Material],
    armature_obj: Object | None,
    hi: bool,
    char_cloth: CharacterCloth | None,
) -> dict[IOLodLevel, list[Model]]:
    model_objs = get_model_objs(drawable_obj)

    if armature_obj is not None:
        bones = armature_obj.data.bones
        model_objs = sort_skinned_models_by_bone(model_objs, bones)

    lod_levels = (LODLevel.VERYHIGH,) if hi else (LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW)

    models: dict[IOLodLevel, list[Model]] = defaultdict(list)
    for model_obj in model_objs:
        transforms_to_apply = get_export_transforms_to_apply(model_obj)

        lods = model_obj.sz_lods
        for lod_level in lod_levels:
            lod = lods.get_lod(lod_level)
            if lod.mesh is None:
                continue

            model = create_model(model_obj, lod_level, materials, armature_obj, transforms_to_apply, char_cloth)
            if not model.geometries:
                continue

            models[lod_level.to_io()].append(model)

    # Drawables only ever have 1 skinned drawable model per LOD level. Since, the skinned portion of the
    # drawable can be split by vertex group, we have to join each separate part into a single object.
    for lod_level in models.keys():
        models[lod_level] = join_skinned_models(models[lod_level])

    for lod_level in models.keys():
        models[lod_level] = split_models_by_vert_count(models[lod_level])

    return models


def get_model_objs(drawable_obj: Object) -> list[Object]:
    from .ydrexport import get_model_objs as impl
    return impl(drawable_obj)


def sort_skinned_models_by_bone(model_objs: list[Object], bones: list[Bone]) -> list[Object]:
    from .ydrexport import sort_skinned_models_by_bone as impl
    return impl(model_objs, bones)


@operates_on_lod_level
def create_model(
    model_obj: Object,
    lod_level: LODLevel,
    materials: list[Material],
    armature_obj: Optional[Object] = None,
    transforms_to_apply: Optional[Matrix] = None,
    char_cloth: CharacterCloth | None = None,
    mesh_domain_override: Optional[VBBuilderDomain] = None,
) -> Model:
    obj_eval = get_evaluated_obj(model_obj)
    mesh_eval = obj_eval.to_mesh()
    triangulate_mesh(mesh_eval)

    if transforms_to_apply is not None:
        mesh_eval.transform(transforms_to_apply)

    if char_cloth:
        cloth_export_context().diagnostics.drawable_model_obj_name = model_obj.name

    geometries = create_geometries(
        model_obj, mesh_eval, materials, armature_obj, char_cloth, mesh_domain_override
    )

    if lod_level == LODLevel.HIGH:
        fix_vehglass_geometry_for_shattermap_generation(mesh_eval, materials, geometries)

    bone_index = get_model_bone_index(model_obj)

    obj_eval.to_mesh_clear()

    bones = armature_obj.data.bones if armature_obj is not None else None
    model_props = get_model_properties(model_obj, lod_level)
    render_mask = model_props.render_mask
    has_skin = bool(bones and model_obj.vertex_groups)
    if has_skin:
        flags = 1  # skin flag, same meaning as has_skin
        matrix_count = len(bones)
    else:
        flags = 0
        matrix_count = 0

    return Model(
        bone_index=bone_index,
        geometries=geometries,
        render_bucket_mask=render_mask,
        has_skin=has_skin,
        matrix_count=matrix_count,
        flags=flags,
    )


def triangulate_mesh(mesh: Mesh):
    from .ydrexport import triangulate_mesh as impl
    impl(mesh)


def get_model_bone_index(model_obj: Object) -> int:
    from .ydrexport import get_model_bone_index as impl
    return impl(model_obj)


def create_geometries(
    model_obj: Object,
    mesh_eval: Mesh,
    materials: list[Material],
    armature_obj: Optional[Object],
    char_cloth: CharacterCloth | None,
    mesh_domain_override: Optional[VBBuilderDomain],
) -> list[Geometry]:
    is_cable = is_cable_mesh(mesh_eval)
    if len(mesh_eval.loops) == 0 and not is_cable:  # cable mesh don't have faces, so no loops either
        logger.warning(f"Drawable Model '{mesh_eval.original.name}' has no Geometry! Skipping...")
        return []

    if not mesh_eval.materials:
        logger.warning(
            f"Could not create geometries for Drawable Model '{mesh_eval.original.name}': Mesh has no Sollumz materials!")
        return []

    if is_cable:
        cable_total_vert_buffer, cable_vert_materials = CableVertexBufferBuilder(mesh_eval).build()
        cable_geometries = []
        for cable_material_index in range(len(mesh_eval.materials)):
            cable_vert_buffer = cable_total_vert_buffer[cable_vert_materials == cable_material_index]
            cable_vert_buffer, cable_ind_buffer = dedupe_and_get_indices(cable_vert_buffer)

            cable_material = mesh_eval.materials[cable_material_index].original
            cable_material_index_in_drawable = materials.index(cable_material)

            geom = Geometry(
                vertex_data_type=VertexDataType.DEFAULT,
                vertex_buffer=cable_vert_buffer,
                index_buffer=cable_ind_buffer,
                bone_ids=np.empty(0),
                shader_index=cable_material_index_in_drawable,
            )
            cable_geometries.append(geom)

        return cable_geometries

    # Validate UV maps and color attributes
    texcoords = [(t, get_uv_map_name(t)) for t in get_mesh_used_texcoords_indices(mesh_eval)]
    texcoords_missing = [(t, name) for t, name in texcoords if name not in mesh_eval.uv_layers]
    if texcoords_missing:
        texcoords_missing_str = ", ".join(name for _, name in texcoords_missing)
        logger.warning(
            f"Mesh '{mesh_eval.name}' is missing UV maps used by Sollumz shaders: {texcoords_missing_str}. "
            "Please add them to avoid rendering issues in-game."
        )

    colors = [(c, get_color_attr_name(c)) for c in get_mesh_used_colors_indices(mesh_eval)]
    colors_missing = [(c, name) for c, name in colors if name not in mesh_eval.color_attributes]
    if colors_missing:
        colors_missing_str = ", ".join(c[1] for c in colors_missing)
        logger.warning(
            f"Mesh '{mesh_eval.name}' is missing color attributes used by Sollumz shaders: {colors_missing_str}. "
            "Please add them to avoid rendering issues in-game."
        )

    colors_incorrect_format = [
        (c, name) for c, name in colors
        if (attr := mesh_eval.color_attributes.get(name, None)) and
           (attr.domain != "CORNER" or attr.data_type != "BYTE_COLOR")
    ]
    if colors_incorrect_format:
        colors_incorrect_format_str = ", ".join(name for _, name in colors_incorrect_format)
        logger.warning(
            f"Mesh '{mesh_eval.name}' has color attributes with the incorrect format: {colors_incorrect_format_str}. "
            "Their format must be 'Face Corner ▶ Byte Color'. Please convert them to avoid rendering issues in-game."
        )

    del texcoords
    del texcoords_missing
    del colors
    del colors_missing
    del colors_incorrect_format

    loop_inds_by_mat = get_loop_inds_by_material(mesh_eval, materials)

    geometries: list[Geometry] = []

    bones = armature_obj.data.bones if armature_obj is not None else None
    bone_by_vgroup = try_get_bone_by_vgroup(model_obj, armature_obj)

    domain = export_context().settings.mesh_domain if mesh_domain_override is None else mesh_domain_override
    vb_builder = VertexBufferBuilder(mesh_eval, bone_by_vgroup, domain, materials, char_cloth)
    total_vert_buffer = vb_builder.build()
    if domain == VBBuilderDomain.VERTEX:
        # bit dirty to use private data of the builder class, but we need this array here and it is already computed
        loop_to_vert_inds = vb_builder._loop_to_vert_inds

    for mat_index, loop_inds in loop_inds_by_mat.items():
        material = materials[mat_index]
        tangent_required = get_tangent_required(material)
        normal_required = get_normal_required(material)

        if domain == VBBuilderDomain.FACE_CORNER:
            vert_buffer = total_vert_buffer[loop_inds]
        elif domain == VBBuilderDomain.VERTEX:
            vert_buffer = total_vert_buffer[loop_to_vert_inds[loop_inds]]
        used_texcoords = get_used_texcoords(material)
        used_colors = get_used_colors(material)

        vert_buffer = remove_unused_uvs(vert_buffer, used_texcoords)
        vert_buffer = remove_unused_colors(vert_buffer, used_colors)

        if not tangent_required:
            vert_buffer = remove_arr_field("Tangent", vert_buffer)

        if not normal_required:
            vert_buffer = remove_arr_field("Normal", vert_buffer)

        vert_buffer, ind_buffer = dedupe_and_get_indices(vert_buffer)

        if bones and "BlendWeights" in vert_buffer.dtype.names:
            bone_ids = get_bone_ids(bones)
        else:
            bone_ids = np.empty(0)


        geom = Geometry(
            vertex_data_type=VertexDataType.DEFAULT,
            vertex_buffer=vert_buffer,
            index_buffer=ind_buffer,
            bone_ids=bone_ids,
            shader_index=mat_index,
        )
        geometries.append(geom)

    geometries = sort_geoms_by_shader(geometries)

    return geometries


def sort_geoms_by_shader(geometries: list[Geometry]) -> list[Geometry]:
    return sorted(geometries, key=lambda g: g.shader_index)


def get_loop_inds_by_material(mesh: Mesh, drawable_mats: list[Material]) -> dict[int, NDArray[np.uint32]]:
    from .ydrexport import get_loop_inds_by_material as impl
    return impl(mesh, drawable_mats)


def get_bone_ids(bones: list[Bone]) -> list[int]:
    from .ydrexport import get_bone_ids as impl
    return impl(bones)


def fix_vehglass_geometry_for_shattermap_generation(
    mesh_eval: Mesh,
    materials: list[Material],
    geometries: list[Geometry]
):
    any_bad_geometry = False
    for geometry in geometries:
        material = materials[geometry.shader_index]
        if material.shader_properties.name in {"vehicle_vehglass", "vehicle_vehglass_inner"}:
            blue_channel = geometry.vertex_buffer['Colour0'][:, 2]
            if np.all(blue_channel == 0):
                any_bad_geometry = True
                blue_channel[:] = 255

    if any_bad_geometry:
        logger.warning(
            f"Mesh '{mesh_eval.name}' using VEHICLE VEHGLASS shader has color attribute 'Color 1' with no blue channel "
            "data (all values are black). The blue channel is used to mark where vehicle glass borders connect to the "
            "frame for shattermap generation. Please paint the blue channel on connected border vertices for correct "
            "shattering behavior. Defaulting to treating the entire mesh as connected (blue = 255)."
        )


def join_skinned_models(models: list[Model]) -> list[Model]:
    non_skinned_models = [model for model in models if not model.has_skin]
    skinned_models = [model for model in models if model.has_skin]

    if not skinned_models:
        return non_skinned_models

    skinned_geoms: list[Geometry] = [geom for model in skinned_models for geom in model.geometries]

    geoms_by_shader: dict[int, list[Geometry]] = defaultdict(list)

    for geom in skinned_geoms:
        geoms_by_shader[geom.shader_index].append(geom)

    joined_skinned_geoms = [join_geometries(geoms, shader_ind) for shader_ind, geoms in geoms_by_shader.items()]
    joined_skinned_geoms = sort_geoms_by_shader(joined_skinned_geoms)
    joined_skinned_model = Model(
        bone_index=0,
        geometries=joined_skinned_geoms,
        render_bucket_mask=skinned_models[0].render_bucket_mask,
        has_skin=True,
        matrix_count=skinned_models[0].matrix_count,
        flags=skinned_models[0].flags,
    )

    return [joined_skinned_model, *non_skinned_models]


def join_geometries(geometries: list[Geometry], shader_index: int) -> Geometry:
    vert_arrs = [g.vertex_buffer for g in geometries]
    ind_arrs = [g.index_buffer for g in geometries]
    vert_counts = [len(vert_arr) for vert_arr in vert_arrs]

    joined_vertex_buffer = join_vert_arrs(vert_arrs)
    joined_index_buffer = join_ind_arrs(ind_arrs, vert_counts)
    bone_ids = list(np.unique([geom.bone_ids for geom in geometries]))

    return Geometry(
        vertex_data_type=VertexDataType.DEFAULT,
        vertex_buffer=joined_vertex_buffer,
        index_buffer=joined_index_buffer,
        bone_ids=bone_ids,
        shader_index=shader_index,
    )


def join_vert_arrs(vert_arrs: list[NDArray]) -> NDArray:
    """Join vertex buffer structured arrays. Works with arrays that have different layouts."""
    num_verts = sum(len(vert_arr) for vert_arr in vert_arrs)
    struct_dtype = get_joined_vert_arr_dtype(vert_arrs)
    joined_arr = np.zeros(num_verts, dtype=struct_dtype)

    for attr_name in joined_arr.dtype.names:
        row_start = 0

        for vert_arr in vert_arrs:
            num_attr_verts = len(vert_arr)

            if attr_name in vert_arr.dtype.names:
                row_end = row_start + num_attr_verts
                joined_arr[attr_name][row_start:row_end] = vert_arr[attr_name]

            row_start += num_attr_verts

    return joined_arr


def get_joined_vert_arr_dtype(vert_arrs: list[NDArray]):
    """Create a new structured dtype containing all vertex attrs present in all vert_arrs"""
    attr_names = []

    for vert_arr in vert_arrs:
        attr_names.extend(
            name for name in vert_arr.dtype.names if name not in attr_names)

    from szio.gta5.cwxml import VertexBuffer
    return [VertexBuffer.VERT_ATTR_DTYPES[name] for name in attr_names]


def join_ind_arrs(ind_arrs: list[NDArray[np.uint32]], vert_counts: list[int]) -> NDArray[np.uint32]:
    """Join vertex index arrays by simply concatenating and offsetting indices based on vertex counts"""
    def get_vert_ind_offset(arr_ind: int) -> int:
        if arr_ind == 0:
            return 0

        return sum(num_verts for num_verts in vert_counts[:arr_ind])

    offset_ind_arrs = [ind_arr + get_vert_ind_offset(i) for i, ind_arr in enumerate(ind_arrs)]

    return np.concatenate(offset_ind_arrs)


def split_models_by_vert_count(models: list[Model]) -> list[Model]:
    models_split = []
    for model in models:
        geoms_split = [geom_split for geom in model.geometries for geom_split in split_geom_by_vert_count(geom)]
        models_split.append(replace(model, geometries=geoms_split))
    return models_split


def split_geom_by_vert_count(geom: Geometry) -> list[Geometry]:
    if geom.vertex_buffer is None or geom.index_buffer is None:
        raise ValueError(
            "Failed to split Geometry by vertex count. Vertex buffer and index buffer cannot be None!")

    vert_buffers, ind_buffers = split_vert_buffers(geom.vertex_buffer, geom.index_buffer)

    geoms: list[Geometry] = []

    for vert_buffer, ind_buffer in zip(vert_buffers, ind_buffers):
        new_geom = replace(
            geom,
            vertex_buffer=vert_buffer,
            index_buffer=ind_buffer,
        )

        geoms.append(new_geom)

    return geoms


def split_vert_buffers(
    vert_buffer: NDArray,
    ind_buffer: NDArray[np.uint32]
) -> tuple[list[NDArray], list[NDArray[np.uint32]]]:
    """Splits vertex and index buffers on chunks that fit in 16-bit indices.
    Returns tuple of split vertex buffers and tuple of index buffers"""
    MAX_INDEX = 65535

    total_index = 0
    idx_count = len(ind_buffer)

    split_vert_arrs = []
    split_ind_arrs = []
    while total_index < idx_count:
        old_index_to_new_index = {}
        chunk_vertices_indices = []
        chunk_indices = []
        chunk_index = 0
        while total_index < idx_count and len(chunk_indices) < MAX_INDEX:
            old_index = ind_buffer[total_index]
            existing_index = old_index_to_new_index.get(old_index, None)
            if existing_index is not None:
                # we already have this index vertex addedm simply remap it to new index
                chunk_indices.append(existing_index)
            else:
                # We got new index unseen before, we have to add both vertex and index
                chunk_indices.append(chunk_index)
                chunk_vertices_indices.append(old_index)
                old_index_to_new_index[old_index] = chunk_index
                chunk_index += 1

            total_index += 1

        chunk_vertices_arr = vert_buffer[chunk_vertices_indices]
        chunk_indices_arr = np.array(chunk_indices, dtype=np.uint32)
        split_vert_arrs.append(chunk_vertices_arr)
        split_ind_arrs.append(chunk_indices_arr)

    return (split_vert_arrs, split_ind_arrs)


def create_shader_group(materials: list[Material]) -> ShaderGroup:
    return ShaderGroup(
        shaders=[create_shader(m) for m in materials],
        embedded_textures=get_embedded_textures_from_materials(materials),
    )


def create_shader(material: Material) -> ShaderInst:
    shader_def = ShaderManager.find_shader(material.shader_properties.filename)
    parameters = create_shader_parameters_list_template(shader_def)

    for node in material.node_tree.nodes:
        param = None

        if isinstance(node, bpy.types.ShaderNodeTexImage):
            param_def = shader_def.parameter_map.get(node.name, None)
            if not param_def:
                continue

            texture_name = node.sollumz_texture_name or None
            param = ShaderParameter(name=param_def.name, value=texture_name)
        elif isinstance(node, SzShaderNodeParameter):
            param_def = shader_def.parameter_map.get(node.name, None)
            if not param_def:
                continue

            is_vector = isinstance(param_def, ShaderParameterFloatVectorDef) and not param_def.is_array
            if is_vector:
                x = node.get(0)
                y = node.get(1) if node.num_cols > 1 else 0.0
                z = node.get(2) if node.num_cols > 2 else 0.0
                w = node.get(3) if node.num_cols > 3 else 0.0
                param_value = Vector((x, y, z, w))
            else:
                param_value = []
                for row in range(node.num_rows):
                    i = row * node.num_cols
                    x = node.get(i)
                    y = node.get(i + 1) if node.num_cols > 1 else 0.0
                    z = node.get(i + 2) if node.num_cols > 2 else 0.0
                    w = node.get(i + 3) if node.num_cols > 3 else 0.0

                    param_value.append(Vector((x, y, z, w)))

            param = ShaderParameter(name=param_def.name, value=param_value)

        if param is not None:
            parameter_index = next((i for i, x in enumerate(parameters) if x.name == param.name), None)

            if parameter_index is None:
                parameters.append(param)
            else:
                parameters[parameter_index] = param

    return ShaderInst(
        name=material.shader_properties.name,
        preset_filename=material.shader_properties.filename,
        render_bucket=RenderBucket[material.shader_properties.renderbucket],
        parameters=parameters,
    )


def create_shader_parameters_list_template(shader_def: Optional[ShaderDef]) -> list[ShaderParameter]:
    """Creates a list of shader parameters ordered as defined in the ``ShaderDef`` parameters list.
    This order is only required to prevent some crashes when previewing the drawable in OpenIV, which expects
    parameters to be in the same order as vanilla files. This is not a problem for CodeWalker or the game.
    """
    if shader_def is None:
        return []

    parameters = []
    for param_def in shader_def.parameters:
        match param_def.type:
            case ShaderParameterType.TEXTURE:
                param_value = None
            case (ShaderParameterType.FLOAT |
                  ShaderParameterType.FLOAT2 |
                  ShaderParameterType.FLOAT3 |
                  ShaderParameterType.FLOAT4):
                if param_def.is_array:
                    param_value = [Vector((0.0, 0.0, 0.0, 0.0)) for _ in range(param_def.count)]
                else:
                    param_value = Vector((0.0, 0.0, 0.0, 0.0))
            case ShaderParameterType.FLOAT4X4:
                param_value = [Vector((0.0, 0.0, 0.0, 0.0)) for _ in range(4)]
            case _:
                raise Exception(f"Unknown shader parameter! {param_def.type=} {param_def.name=}")

        parameters.append(ShaderParameter(
            name=param_def.name,
            value=param_value,
        ))

    return parameters


def get_embedded_textures_from_materials(materials: list[Material]) -> dict[str, EmbeddedTexture]:
    textures = {}

    for node in get_embedded_texture_nodes_from_materials(materials):
        texture_name = node.sollumz_texture_name

        if texture_name in textures or not texture_name:
            continue

        texture_name_dds = f"{texture_name}.dds"
        texture_data = None
        img = node.image
        packed = img.packed_file
        if packed and (packed_data := packed.data):
            # Embed packed data
            if not packed_data.startswith(b"DDS "):
                logger.warning(
                    f"Embedded texture '{img.name}' packed data is not in DDS format. Please, convert it to a DDS file."
                )
            else:
                texture_data = DataSource.create(packed_data, texture_name_dds)
        else:
            # Embed external file
            texture_path = Path(bpy.path.abspath(img.filepath))
            if not texture_path.is_file():
                logger.warning(
                    f"Embedded texture '{img.name}' file does not exist and the image is not packed. "
                    f"File path: {texture_path}"
                )
            elif texture_path.suffix != ".dds":
                logger.warning(
                    f"Embedded texture '{img.name}' is not in DDS format. Please, convert it to a DDS file."
                    f"File path: {texture_path}"
                )
            else:
                texture_data = DataSource.create(texture_path, texture_name_dds)

        w, h = img.size
        texture = EmbeddedTexture(texture_name, w, h, texture_data)
        textures[texture_name] = texture

    return textures


def get_embedded_texture_nodes_from_materials(materials: list[Material]) -> list[ShaderNodeTexImage]:
    nodes: list[ShaderNodeTexImage] = []

    for mat in materials:
        for node in mat.node_tree.nodes:
            if not isinstance(node, ShaderNodeTexImage) or not node.texture_properties.embedded:
                continue

            if not node.image:
                continue

            nodes.append(node)

    return nodes


def create_skeleton(armature_obj: bpy.types.Object, apply_transforms: bool = False) -> Skeleton:
    assert armature_obj.type == "ARMATURE" and armature_obj.pose.bones

    bones = armature_obj.pose.bones

    if apply_transforms:
        matrix = armature_obj.matrix_world.copy()
        matrix.translation = Vector()
    else:
        matrix = Matrix()

    skel_bones = []
    for bone_index, pose_bone in enumerate(bones):
        skel_bone = create_bone(pose_bone, armature_obj.data, matrix)
        skel_bones.append(skel_bone)

    return Skeleton(skel_bones)


def create_bone(pose_bone: PoseBone, armature: Armature, armature_matrix: Matrix) -> SkelBone:
    bone = pose_bone.bone

    parent_index = get_bone_parent_index(bone, armature)

    flags = get_bone_flags(pose_bone)
    pos, rot, scale = get_bone_transforms(bone, armature_matrix)

    return SkelBone(
        name=bone.name,
        tag=bone.bone_properties.tag,
        flags=flags,
        position=pos,
        rotation=rot,
        scale=scale,
        parent_index=parent_index,
        translation_limit=get_bone_translation_limit(pose_bone),
        rotation_limit=get_bone_rotation_limit(pose_bone),
    )


def get_bone_parent_index(bone: Bone, armature: Armature) -> int:
    if bone.parent is None:
        return -1

    return get_bone_index(armature, bone.parent)


def get_bone_flags(pose_bone: PoseBone) -> SkelBoneFlags:
    bone = pose_bone.bone

    flags = SkelBoneFlags(0)
    for flag in bone.bone_properties.flags:
        if not flag.name:
            continue

        # flags still use the CW names for backwards compatibility
        from szio.gta5.cwxml.adapters.drawable import CW_BONE_FLAGS_MAP
        flags |= CW_BONE_FLAGS_MAP[flag.name]

    if find_bone_constraint_rotation_limit(pose_bone):
        flags |= SkelBoneFlags.HAS_ROTATE_LIMITS

    if find_bone_constraint_translation_limit(pose_bone):
        flags |= SkelBoneFlags.HAS_TRANSLATE_LIMITS

    if bone.children:
        flags |= SkelBoneFlags.HAS_CHILD

    return flags


def get_bone_transforms(bone: Bone, armature_matrix: Matrix) -> tuple[Vector, Quaternion, Vector]:
    pos = armature_matrix @ bone.matrix_local.translation

    if bone.parent is not None:
        pos = armature_matrix @ bone.parent.matrix_local.inverted() @ bone.matrix_local.translation

    rotation = bone.matrix.to_quaternion()
    scale = bone.matrix.to_scale()
    return pos, rotation, scale


def get_bone_index(armature: Armature, bone: Bone) -> Optional[int]:
    """Get bone index on armature. Returns None if not found."""
    index = armature.bones.find(bone.name)

    if index == -1:
        return None

    return index


def find_bone_constraint_translation_limit(pose_bone: PoseBone) -> Optional[LimitLocationConstraint]:
    for constraint in pose_bone.constraints:
        if constraint.type == "LIMIT_LOCATION":
            return constraint

    return None


def find_bone_constraint_rotation_limit(pose_bone: PoseBone) -> Optional[LimitRotationConstraint]:
    for constraint in pose_bone.constraints:
        if constraint.type == "LIMIT_ROTATION":
            return constraint

    return None


def get_bone_translation_limit(pose_bone: PoseBone) -> Optional[SkelBoneTranslationLimit]:
    constraint = find_bone_constraint_translation_limit(pose_bone)
    return SkelBoneTranslationLimit(
        Vector((constraint.min_x, constraint.min_y, constraint.min_z)),
        Vector((constraint.max_x, constraint.max_y, constraint.max_z)),
    ) if constraint is not None else None


def get_bone_rotation_limit(pose_bone: PoseBone) -> Optional[SkelBoneRotationLimit]:
    constraint = find_bone_constraint_rotation_limit(pose_bone)
    return SkelBoneRotationLimit(
        Vector((constraint.min_x, constraint.min_y, constraint.min_z)),
        Vector((constraint.max_x, constraint.max_y, constraint.max_z)),
    ) if constraint is not None else None


def create_embedded_bounds_asset(drawable_obj: Object) -> Optional[AssetBound]:
    bound_objs = [
        child for child in drawable_obj.children
        if child.sollum_type == SollumType.BOUND_COMPOSITE or child.sollum_type in BOUND_TYPES
    ]
    if not bound_objs:
        return None

    bound_obj = bound_objs[0]
    if len(bound_objs) > 1:
        other_bound_objs = bound_objs[1:]
        other_bound_objs_names = [f"'{o.name}'" for o in other_bound_objs]
        other_bound_objs_names = ", ".join(other_bound_objs_names)
        logger.warning(
            f"Drawable '{drawable_obj.name}' has multiple root embedded bounds! "
            f"Only a single root bound is supported. Use a Bound Composite if you need multiple bounds.\n"
            f"Only '{bound_obj.name}' will be exported. The following bounds will be ignored: {other_bound_objs_names}."
        )

    bound = None
    if bound_obj.sollum_type == SollumType.BOUND_COMPOSITE:
        bound = create_bound_composite_asset(bound_obj)
    elif bound_obj.sollum_type in BOUND_TYPES:
        bound = create_bound_asset(bound_obj, is_root=True)

        if not bound.composite_transform.is_identity:
            logger.warning(
                f"Embedded bound '{bound_obj.name}' has transforms (rotation, scale) but is not parented to a Bound "
                f"Composite. Parent the collision to a Bound Composite in order for the transforms to work in-game."
            )

    return bound
