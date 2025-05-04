import os
import shutil
import math
import bmesh
import bpy
import zlib
import numpy as np
from numpy.typing import NDArray
from typing import Callable, Optional
from collections import defaultdict
from mathutils import Quaternion, Vector, Matrix

from ..lods import operates_on_lod_level
from .model_data import get_faces_subset

from ..cwxml.drawable import (
    BoneLimit,
    Drawable,
    Texture,
    Skeleton,
    Bone,
    Joints,
    RotationLimit,
    DrawableModel,
    Geometry,
    Shader,
    ShaderParameter,
    ArrayShaderParameter,
    VectorShaderParameter,
    TextureShaderParameter,
    VertexBuffer,
)
from ..cwxml.cloth import CharacterCloth
from ..tools import jenkhash
from ..tools.meshhelper import (
    get_bound_center_from_bounds,
    get_sphere_radius,
    get_mesh_used_colors_indices,
    get_mesh_used_texcoords_indices,
    get_used_colors,
    get_used_texcoords,
    get_uv_map_name,
    get_color_attr_name,
    get_normal_required,
    get_tangent_required,
)
from ..tools.utils import get_filename, get_max_vector_list, get_min_vector_list
from ..shared.shader_nodes import SzShaderNodeParameter
from ..tools.blenderhelper import get_child_of_constraint, get_pose_inverse, remove_number_suffix, get_evaluated_obj
from ..sollumz_helper import get_export_transforms_to_apply, get_sollumz_materials
from ..sollumz_properties import (
    SOLLUMZ_UI_NAMES,
    BOUND_TYPES,
    LODLevel,
    SollumType
)
from ..sollumz_preferences import get_export_settings
from ..ybn.ybnexport import create_composite_xml, create_bound_xml
from .properties import get_model_properties
from .render_bucket import RenderBucket
from .vertex_buffer_builder import VertexBufferBuilder, VBBuilderDomain, dedupe_and_get_indices, remove_arr_field, remove_unused_colors, get_bone_by_vgroup, remove_unused_uvs
from .cable_vertex_buffer_builder import CableVertexBufferBuilder
from .cable import is_cable_mesh
from .cloth_diagnostics import cloth_export_context
from .lights import create_xml_lights
from ..cwxml.shader import ShaderManager, ShaderDef, ShaderParameterFloatVectorDef, ShaderParameterType

from .. import logger


def export_ydr(drawable_obj: bpy.types.Object, filepath: str) -> bool:
    export_settings = get_export_settings()

    drawable_xml = create_drawable_xml(drawable_obj, apply_transforms=export_settings.apply_transforms)
    drawable_xml.write_xml(filepath)

    write_embedded_textures(drawable_obj, filepath)
    return True


def create_drawable_xml(
    drawable_obj: bpy.types.Object,
    armature_obj: Optional[bpy.types.Object] = None,
    materials: Optional[list[bpy.types.Material]] = None,
    apply_transforms: bool = False,
    char_cloth_xml: Optional[CharacterCloth] = None,
):
    """Create a ``Drawable`` cwxml object. Optionally specify an external ``armature_obj`` if ``drawable_obj`` is not an armature."""
    drawable_xml = Drawable()
    drawable_xml.frag_bound_matrix = None

    drawable_xml.name = remove_number_suffix(drawable_obj.name.lower())

    set_drawable_xml_properties(drawable_obj, drawable_xml)

    materials = materials or get_sollumz_materials(drawable_obj)

    create_shader_group_xml(materials, drawable_xml)

    if not drawable_xml.shader_group.shaders:
        logger.warning(
            f"{drawable_xml.name} has no Sollumz materials! Aborting...")
        return drawable_xml

    if armature_obj or drawable_obj.type == "ARMATURE":
        armature_obj = armature_obj or drawable_obj

        drawable_xml.skeleton = create_skeleton_xml(armature_obj, apply_transforms)
        drawable_xml.joints = create_joints_xml(armature_obj)

        bones = armature_obj.data.bones

        original_pose = armature_obj.data.pose_position
        armature_obj.data.pose_position = "REST"
    else:
        drawable_xml.skeleton = None
        drawable_xml.joints = None
        bones = None
        original_pose = "POSE"

    if char_cloth_xml:
        char_cloth_xml._tmp_skeleton = drawable_xml.skeleton

    create_model_xmls(drawable_xml, drawable_obj, materials, bones, char_cloth_xml)

    drawable_xml.lights = create_xml_lights(drawable_obj)

    set_drawable_xml_flags(drawable_xml)
    set_drawable_xml_extents(drawable_xml)

    create_embedded_collision_xmls(drawable_obj, drawable_xml)

    if armature_obj is not None:
        armature_obj.data.pose_position = original_pose

    return drawable_xml


def create_model_xmls(
    drawable_xml: Drawable,
    drawable_obj: bpy.types.Object,
    materials: list[bpy.types.Material],
    bones: Optional[list[bpy.types.Bone]] = None,
    char_cloth_xml: Optional[CharacterCloth] = None,
):
    model_objs = get_model_objs(drawable_obj)

    if bones is not None:
        model_objs = sort_skinned_models_by_bone(model_objs, bones)

    for model_obj in model_objs:
        transforms_to_apply = get_export_transforms_to_apply(model_obj)

        lods = model_obj.sz_lods
        for lod_level in LODLevel:
            if lod_level == LODLevel.VERYHIGH:
                continue

            lod = lods.get_lod(lod_level)
            if lod.mesh is None:
                continue

            model_xml = create_model_xml(model_obj, lod_level, materials, bones, transforms_to_apply, char_cloth_xml)
            if not model_xml.geometries:
                continue

            append_model_xml(drawable_xml, model_xml, lod_level)

    # Drawables only ever have 1 skinned drawable model per LOD level. Since, the skinned portion of the
    # drawable can be split by vertex group, we have to join each separate part into a single object.
    join_skinned_models_for_each_lod(drawable_xml)
    split_drawable_by_vert_count(drawable_xml)


def get_model_objs(drawable_obj: bpy.types.Object) -> list[bpy.types.Object]:
    """Get all non-skinned Drawable Model objects under ``drawable_obj``."""
    from .cloth import is_cloth_mesh_object
    return [obj for obj in drawable_obj.children if obj.sollum_type == SollumType.DRAWABLE_MODEL and not obj.sollumz_is_physics_child_mesh and not is_cloth_mesh_object(obj)]


def sort_skinned_models_by_bone(model_objs: list[bpy.types.Object], bones: list[bpy.types.Bone]):
    """Sort all models with vertex groups by bone index. If a model has multiple vertex group uses the vertex group
    with the lowest bone index."""
    # This is necessary to ensure proper render order of each vertex group. With many vertex groups on a single object
    # you can just change the order, but if the object is split by group there is no way of manually sorting the vertex groups.
    def get_model_bone_ind(obj: bpy.types.Object):
        bone_ind_by_name: dict[str, int] = {
            b.name: i for i, b in enumerate(bones)}
        bone_inds = [bone_ind_by_name[group.name]
                     for group in obj.vertex_groups if group.name in bone_ind_by_name]

        if not bone_inds:
            return 0

        lowest_bone_ind = min(bone_inds)

        return lowest_bone_ind

    return sorted(model_objs, key=get_model_bone_ind)


@operates_on_lod_level
def create_model_xml(
    model_obj: bpy.types.Object,
    lod_level: LODLevel,
    materials: list[bpy.types.Material],
    bones: Optional[list[bpy.types.Bone]] = None,
    transforms_to_apply: Optional[Matrix] = None,
    char_cloth_xml: Optional[CharacterCloth] = None,
    mesh_domain_override: Optional[VBBuilderDomain] = None,
):
    model_xml = DrawableModel()

    set_model_xml_properties(model_obj, lod_level, bones, model_xml)

    obj_eval = get_evaluated_obj(model_obj)
    mesh_eval = obj_eval.to_mesh()
    triangulate_mesh(mesh_eval)

    if transforms_to_apply is not None:
        mesh_eval.transform(transforms_to_apply)

    if char_cloth_xml:
        cloth_export_context().diagnostics.drawable_model_obj_name = model_obj.name

    geometries = create_geometries_xml(
        mesh_eval, materials, bones, model_obj.vertex_groups, char_cloth_xml, mesh_domain_override
    )
    model_xml.geometries = geometries

    model_xml.bone_index = get_model_bone_index(model_obj)

    obj_eval.to_mesh_clear()

    return model_xml


def triangulate_mesh(mesh: bpy.types.Mesh):
    temp_mesh = bmesh.new()
    temp_mesh.from_mesh(mesh)

    bmesh.ops.triangulate(temp_mesh, faces=temp_mesh.faces)

    temp_mesh.to_mesh(mesh)
    temp_mesh.free()

    return mesh


def get_model_bone_index(model_obj: bpy.types.Object):
    constraint = get_child_of_constraint(model_obj)

    if constraint is None:
        return 0

    armature: bpy.types.Armature = constraint.target.data
    bone_index = armature.bones.find(constraint.subtarget)

    return bone_index if bone_index != -1 else 0


def set_model_xml_properties(model_obj: bpy.types.Object, lod_level: LODLevel, bones: Optional[list[bpy.types.Bone]], model_xml: DrawableModel):
    """Set ``DrawableModel`` properties for each lod in ``model_obj``"""
    model_props = get_model_properties(model_obj, lod_level)

    model_xml.render_mask = model_props.render_mask
    model_xml.flags = 0
    model_xml.matrix_count = 0
    model_xml.has_skin = 1 if bones and model_obj.vertex_groups else 0

    if model_xml.has_skin:
        model_xml.flags = 1  # skin flag, same meaning as has_skin
        model_xml.matrix_count = len(bones)


def create_geometries_xml(
    mesh_eval: bpy.types.Mesh,
    materials: list[bpy.types.Material],
    bones: Optional[list[bpy.types.Bone]] = None,
    vertex_groups: Optional[list[bpy.types.VertexGroup]] = None,
    char_cloth_xml: Optional[CharacterCloth] = None,
    mesh_domain_override: Optional[VBBuilderDomain] = None,
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

            geom_xml = Geometry()
            geom_xml.bounding_box_max, geom_xml.bounding_box_min = get_geom_extents(cable_vert_buffer["Position"])
            geom_xml.shader_index = cable_material_index_in_drawable
            geom_xml.vertex_buffer.data = cable_vert_buffer
            geom_xml.index_buffer.data = cable_ind_buffer
            cable_geometries.append(geom_xml)

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

    bone_by_vgroup = get_bone_by_vgroup(vertex_groups, bones) if bones and vertex_groups else None

    domain = VBBuilderDomain[get_export_settings().mesh_domain] if mesh_domain_override is None else mesh_domain_override
    vb_builder = VertexBufferBuilder(mesh_eval, bone_by_vgroup, domain, materials, char_cloth_xml, bones)
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

        geom_xml = Geometry()

        geom_xml.bounding_box_max, geom_xml.bounding_box_min = get_geom_extents(vert_buffer["Position"])
        geom_xml.shader_index = mat_index

        if bones and "BlendWeights" in vert_buffer.dtype.names:
            geom_xml.bone_ids = get_bone_ids(bones)

        geom_xml.vertex_buffer.data = vert_buffer
        geom_xml.index_buffer.data = ind_buffer

        geometries.append(geom_xml)

    geometries = sort_geoms_by_shader(geometries)

    return geometries


def sort_geoms_by_shader(geometries: list[Geometry]):
    return sorted(geometries, key=lambda g: g.shader_index)


def get_loop_inds_by_material(mesh: bpy.types.Mesh, drawable_mats: list[bpy.types.Material]):
    loop_inds_by_mat: dict[int, NDArray[np.uint32]] = {}

    if not mesh.loop_triangles:
        mesh.calc_loop_triangles()

    # Material indices for each triangle
    tri_mat_indices = np.empty(len(mesh.loop_triangles), dtype=np.uint32)
    mesh.loop_triangles.foreach_get("material_index", tri_mat_indices)

    # Material indices for each loop triangle
    loop_mat_inds = np.repeat(tri_mat_indices, 3)

    all_loop_inds = np.empty(len(mesh.loop_triangles) * 3, dtype=np.uint32)
    mesh.loop_triangles.foreach_get("loops", all_loop_inds)

    mat_inds: dict[str, int] = {mat: i for i, mat in enumerate(drawable_mats)}

    for i, mat in enumerate(mesh.materials):
        original_mat = mat.original

        if original_mat not in mat_inds:
            continue

        # Get index of material on drawable (different from mesh material index)
        shader_index = mat_inds[original_mat]
        tri_loop_inds = np.where(loop_mat_inds == i)[0]

        if tri_loop_inds.size == 0:
            continue

        loop_indices = all_loop_inds[tri_loop_inds]

        if shader_index in loop_inds_by_mat:
            logger.warning(
                f"Shader_index already in list, some geometry will be lost! This is most likely caused by a duplicate material for {mat.name} in {mesh.name}")
        loop_inds_by_mat[shader_index] = loop_indices

    return loop_inds_by_mat


def get_geom_extents(positions: NDArray[np.float32]):
    return Vector(np.max(positions, axis=0)), Vector(np.min(positions, axis=0))


def get_bone_ids(bones: list[bpy.types.Bone]):
    return [i for i in range(len(bones))]


def append_model_xml(drawable_xml: Drawable, model_xml: DrawableModel, lod_level: LODLevel):
    if lod_level == LODLevel.HIGH:
        drawable_xml.drawable_models_high.append(model_xml)

    elif lod_level == LODLevel.MEDIUM:
        drawable_xml.drawable_models_med.append(model_xml)

    elif lod_level == LODLevel.LOW:
        drawable_xml.drawable_models_low.append(model_xml)

    elif lod_level == LODLevel.VERYLOW:
        drawable_xml.drawable_models_vlow.append(model_xml)


def join_skinned_models_for_each_lod(drawable_xml: Drawable):
    drawable_xml.drawable_models_high = join_skinned_models(
        drawable_xml.drawable_models_high)
    drawable_xml.drawable_models_med = join_skinned_models(
        drawable_xml.drawable_models_med)
    drawable_xml.drawable_models_low = join_skinned_models(
        drawable_xml.drawable_models_low)
    drawable_xml.drawable_models_vlow = join_skinned_models(
        drawable_xml.drawable_models_vlow)


def join_skinned_models(model_xmls: list[DrawableModel]):
    non_skinned_models = [model for model in model_xmls if model.has_skin == 0]
    skinned_models = [model for model in model_xmls if model.has_skin == 1]

    if not skinned_models:
        return non_skinned_models

    skinned_geoms: list[Geometry] = [
        geom for model in skinned_models for geom in model.geometries]

    skinned_model = DrawableModel()
    skinned_model.has_skin = 1
    skinned_model.render_mask = skinned_models[0].render_mask
    skinned_model.matrix_count = skinned_models[0].matrix_count
    skinned_model.flags = skinned_models[0].flags

    geoms_by_shader: dict[int, list[Geometry]] = defaultdict(list)

    for geom in skinned_geoms:
        geoms_by_shader[geom.shader_index].append(geom)

    geoms = [join_geometries(
        geoms, shader_ind) for shader_ind, geoms in geoms_by_shader.items()]
    skinned_model.geometries = sort_geoms_by_shader(geoms)

    return [skinned_model, *non_skinned_models]


def join_geometries(geometry_xmls: list[Geometry], shader_index: int):
    new_geom = Geometry()
    new_geom.shader_index = shader_index

    vert_arrs = get_valid_vert_arrs(geometry_xmls)
    ind_arrs = get_valid_ind_arrs(geometry_xmls)
    vert_counts = [len(vert_arr) for vert_arr in vert_arrs]

    new_geom.vertex_buffer.data = join_vert_arrs(vert_arrs)
    new_geom.index_buffer.data = join_ind_arrs(ind_arrs, vert_counts)

    new_geom.bounding_box_max = get_max_vector_list(
        geom.bounding_box_max for geom in geometry_xmls)
    new_geom.bounding_box_min = get_min_vector_list(
        geom.bounding_box_min for geom in geometry_xmls)
    new_geom.bone_ids = list(
        np.unique([geom.bone_ids for geom in geometry_xmls]))

    return new_geom


def get_valid_vert_arrs(geometry_xmls: list[Geometry]):
    return [geom.vertex_buffer.data for geom in geometry_xmls if geom.vertex_buffer.data is not None and geom.index_buffer.data is not None]


def get_valid_ind_arrs(geometry_xmls: list[Geometry]):
    return [geom.index_buffer.data for geom in geometry_xmls if geom.vertex_buffer.data is not None and geom.index_buffer.data is not None]


def join_vert_arrs(vert_arrs: list[NDArray]):
    """Join vertex buffer structured arrays. Works with arrays that have different layouts."""
    num_verts = sum(len(vert_arr) for vert_arr in vert_arrs)
    struct_dtype = get_joined_vert_arr_dtype(vert_arrs)
    joined_arr = np.zeros(num_verts, dtype=struct_dtype)

    for attr_name in joined_arr.dtype.names:
        row_start = 0

        for vert_arr in vert_arrs:
            if attr_name not in vert_arr.dtype.names:
                continue

            attr = vert_arr[attr_name]
            num_attr_verts = len(attr)
            row_end = row_start + num_attr_verts

            joined_arr[attr_name][row_start:row_end] = attr

            row_start = row_end

    return joined_arr


def get_joined_vert_arr_dtype(vert_arrs: list[NDArray]):
    """Create a new structured dtype containing all vertex attrs present in all vert_arrs"""
    attr_names = []

    for vert_arr in vert_arrs:
        attr_names.extend(
            name for name in vert_arr.dtype.names if name not in attr_names)

    return [VertexBuffer.VERT_ATTR_DTYPES[name] for name in attr_names]


def join_ind_arrs(ind_arrs: list[NDArray[np.uint32]], vert_counts: list[int]) -> NDArray[np.uint32]:
    """Join vertex index arrays by simply concatenating and offsetting indices based on vertex counts"""
    def get_vert_ind_offset(arr_ind: int) -> int:
        if arr_ind == 0:
            return 0

        return sum(num_verts for num_verts in vert_counts[:arr_ind])

    offset_ind_arrs = [
        ind_arr + get_vert_ind_offset(i) for i, ind_arr in enumerate(ind_arrs)]

    return np.concatenate(offset_ind_arrs)


def split_drawable_by_vert_count(drawable_xml: Drawable):
    split_models_by_vert_count(drawable_xml.drawable_models_high)
    split_models_by_vert_count(drawable_xml.drawable_models_med)
    split_models_by_vert_count(drawable_xml.drawable_models_low)
    split_models_by_vert_count(drawable_xml.drawable_models_vlow)


def split_models_by_vert_count(model_xmls: list[DrawableModel]):
    for model_xml in model_xmls:
        geoms_split = [
            geom_split for geom in model_xml.geometries for geom_split in split_geom_by_vert_count(geom)]
        model_xml.geometries = geoms_split


def split_geom_by_vert_count(geom_xml: Geometry):
    if geom_xml.vertex_buffer.data is None or geom_xml.index_buffer.data is None:
        raise ValueError(
            "Failed to split Geometry by vertex count. Vertex buffer and index buffer cannot be None!")

    vert_buffers, ind_buffers = split_vert_buffers(geom_xml.vertex_buffer.data, geom_xml.index_buffer.data)

    geoms: list[Geometry] = []

    for vert_buffer, ind_buffer in zip(vert_buffers, ind_buffers):
        new_geom = Geometry()
        new_geom.bone_ids = geom_xml.bone_ids
        new_geom.shader_index = geom_xml.shader_index
        new_geom.bounding_box_max, new_geom.bounding_box_min = get_geom_extents(
            vert_buffer["Position"])

        new_geom.vertex_buffer.data = vert_buffer
        new_geom.index_buffer.data = ind_buffer

        geoms.append(new_geom)

    return tuple(geoms)


def split_vert_buffers(
    vert_buffer: NDArray,
    ind_buffer: NDArray[np.uint32]
) -> tuple[tuple[NDArray], tuple[NDArray[np.uint32]]]:
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

    return (tuple(split_vert_arrs), tuple(split_ind_arrs))


def create_shader_group_xml(materials: list[bpy.types.Material], drawable_xml: Drawable):
    shaders = get_shaders_from_blender(materials)
    texture_dictionary = texture_dictionary_from_materials(materials)

    drawable_xml.shader_group.shaders = shaders
    drawable_xml.shader_group.texture_dictionary = texture_dictionary


def texture_dictionary_from_materials(materials: list[bpy.types.Material]):
    texture_dictionary: dict[str, Texture] = {}

    for node in get_embedded_texture_nodes(materials):
        texture_name = node.sollumz_texture_name

        if texture_name in texture_dictionary or not texture_name:
            continue

        texture = texture_from_img_node(node)
        texture_dictionary[texture_name] = texture

    return list(texture_dictionary.values())


def get_embedded_texture_nodes(materials: list[bpy.types.Material]):
    nodes: list[bpy.types.ShaderNodeTexImage] = []

    for mat in materials:
        for node in mat.node_tree.nodes:
            if not isinstance(node, bpy.types.ShaderNodeTexImage) or not node.texture_properties.embedded:
                continue

            if not node.image:
                continue

            nodes.append(node)

    return nodes


def texture_from_img_node(node: bpy.types.ShaderNodeTexImage):
    texture = Texture()
    texture.name = node.sollumz_texture_name
    texture.width = node.image.size[0]
    texture.height = node.image.size[1]
    texture.filename = texture.name + ".dds"
    # Other texture properties (format, mipmaps, etc.) are set by CW when importing the texture
    return texture


def create_skeleton_xml(armature_obj: bpy.types.Object, apply_transforms: bool = False):
    if armature_obj.type != "ARMATURE" or not armature_obj.pose.bones:
        return None

    skeleton_xml = Skeleton()
    bones = armature_obj.pose.bones

    if apply_transforms:
        matrix = armature_obj.matrix_world.copy()
        matrix.translation = Vector()
    else:
        matrix = Matrix()

    for bone_index, pose_bone in enumerate(bones):

        bone_xml = create_bone_xml(pose_bone, bone_index, armature_obj.data, matrix)

        skeleton_xml.bones.append(bone_xml)

    calculate_skeleton_unks(skeleton_xml)

    return skeleton_xml


def create_bone_xml(pose_bone: bpy.types.PoseBone, bone_index: int, armature: bpy.types.Armature, armature_matrix: Matrix):
    bone = pose_bone.bone

    bone_xml = Bone()
    bone_xml.name = bone.name
    bone_xml.index = bone_index
    bone_xml.tag = bone.bone_properties.tag

    bone_xml.parent_index = get_bone_parent_index(bone, armature)
    bone_xml.sibling_index = get_bone_sibling_index(bone, armature)

    set_bone_xml_flags(bone_xml, pose_bone)
    set_bone_xml_transforms(bone_xml, bone, armature_matrix)

    return bone_xml


def get_bone_parent_index(bone: bpy.types.Bone, armature: bpy.types.Armature):
    if bone.parent is None:
        return -1

    return get_bone_index(armature, bone.parent)


def get_bone_sibling_index(bone: bpy.types.Bone, armature: bpy.types.Armature):
    sibling_index = -1

    if bone.parent is None:
        return sibling_index

    children = bone.parent.children

    for i, child_bone in enumerate(children):
        if child_bone != bone or i + 1 >= len(children):
            continue

        sibling_index = get_bone_index(armature, children[i + 1])
        break

    return sibling_index


def set_bone_xml_flags(bone_xml: Bone, pose_bone: bpy.types.PoseBone):
    bone = pose_bone.bone

    for flag in bone.bone_properties.flags:
        if not flag.name:
            continue

        bone_xml.flags.append(flag.name)

    for constraint in pose_bone.constraints:
        if constraint.type == "LIMIT_ROTATION":
            bone_xml.flags.append("LimitRotation")
            break

    if bone.children:
        bone_xml.flags.append("Unk0")


def set_bone_xml_transforms(bone_xml: Bone, bone: bpy.types.Bone, armature_matrix: Matrix):
    pos = armature_matrix @ bone.matrix_local.translation

    if bone.parent is not None:
        pos = armature_matrix @ bone.parent.matrix_local.inverted() @ bone.matrix_local.translation

    bone_xml.translation = pos
    bone_xml.rotation = bone.matrix.to_quaternion()
    bone_xml.scale = bone.matrix.to_scale()

    # transform_unk doesn't appear in openformats so oiv calcs it right
    # what does it do? the bone length?
    # default value for this seems to be <TransformUnk x="0" y="4" z="-3" w="0" />
    bone_xml.transform_unk = Quaternion((0, 0, 4, -3))


def calculate_skeleton_unks(skeleton_xml: Skeleton):
    # from what oiv calcs Unknown50 and Unknown54 are related to BoneTag and Flags, and obviously the hierarchy of bones
    # assuming those hashes/flags are all based on joaat
    # Unknown58 is related to BoneTag, Flags, Rotation, Location and Scale. Named as DataCRC so we stick to CRC-32 as a hack, since we and possibly oiv don't know how R* calc them
    # hopefully this doesn't break in game!
    # hacky solution with inaccurate results, the implementation here is only to ensure they are unique regardless the correctness, further investigation is required
    if not skeleton_xml.bones:
        return

    unk_50 = []
    unk_58 = []

    for bone in skeleton_xml.bones:
        unk_50_str = " ".join((str(bone.tag), " ".join(bone.flags)))

        translation = []
        for item in bone.translation:
            translation.append(str(item))

        rotation = []
        for item in bone.rotation:
            rotation.append(str(item))

        scale = []
        for item in bone.scale:
            scale.append(str(item))

        unk_58_str = " ".join((str(bone.tag), " ".join(bone.flags), " ".join(
            translation), " ".join(rotation), " ".join(scale)))
        unk_50.append(unk_50_str)
        unk_58.append(unk_58_str)

    skeleton_xml.unknown_50 = jenkhash.Generate(" ".join(unk_50))
    skeleton_xml.unknown_54 = zlib.crc32(" ".join(unk_50).encode())
    skeleton_xml.unknown_58 = zlib.crc32(" ".join(unk_58).encode())


def get_bone_index(armature: bpy.types.Armature, bone: bpy.types.Bone) -> Optional[int]:
    """Get bone index on armature. Returns None if not found."""
    index = armature.bones.find(bone.name)

    if index == -1:
        return None

    return index


def create_joints_xml(armature_obj: bpy.types.Object):
    if armature_obj.pose is None:
        return None

    joints = Joints()

    for pose_bone in armature_obj.pose.bones:
        limit_rot_constraint = get_limit_rot_constraint(pose_bone)
        limit_pos_constraint = get_limit_pos_constraint(pose_bone)
        bone_tag = pose_bone.bone.bone_properties.tag

        if limit_rot_constraint is not None:
            joints.rotation_limits.append(
                create_rotation_limit_xml(limit_rot_constraint, bone_tag))

        if limit_pos_constraint is not None:
            joints.translation_limits.append(
                create_translation_limit_xml(limit_pos_constraint, bone_tag))

    return joints


def get_limit_rot_constraint(pose_bone: bpy.types.PoseBone) -> bpy.types.LimitRotationConstraint:
    for constraint in pose_bone.constraints:
        if constraint.type == "LIMIT_ROTATION":
            return constraint


def get_limit_pos_constraint(pose_bone: bpy.types.PoseBone) -> bpy.types.LimitLocationConstraint:
    for constraint in pose_bone.constraints:
        if constraint.type == "LIMIT_LOCATION":
            return constraint


def create_rotation_limit_xml(constraint: bpy.types.LimitRotationConstraint, bone_tag: int):
    joint = RotationLimit()
    set_joint_properties(joint, constraint, bone_tag)

    return joint


def create_translation_limit_xml(constraint: bpy.types.LimitRotationConstraint, bone_tag: int):
    joint = BoneLimit()
    set_joint_properties(joint, constraint, bone_tag)

    return joint


def set_joint_properties(joint: BoneLimit, constraint: bpy.types.LimitRotationConstraint | bpy.types.LimitLocationConstraint, bone_tag: int):
    joint.bone_id = bone_tag
    joint.min = Vector(
        (constraint.min_x, constraint.min_y, constraint.min_z))
    joint.max = Vector(
        (constraint.max_x, constraint.max_y, constraint.max_z))

    return joint


def set_drawable_xml_flags(drawable_xml: Drawable):
    drawable_xml.flags_high = len(drawable_xml.drawable_models_high)
    drawable_xml.flags_med = len(drawable_xml.drawable_models_med)
    drawable_xml.flags_low = len(drawable_xml.drawable_models_low)
    drawable_xml.flags_vlow = len(drawable_xml.drawable_models_vlow)


def set_drawable_xml_extents(drawable_xml: Drawable):
    mins: list[Vector] = []
    maxes: list[Vector] = []

    for model_xml in drawable_xml.drawable_models_high:
        for geometry in model_xml.geometries:
            mins.append(geometry.bounding_box_min)
            maxes.append(geometry.bounding_box_max)

    bbmin = get_min_vector_list(mins)
    bbmax = get_max_vector_list(maxes)

    drawable_xml.bounding_sphere_center = get_bound_center_from_bounds(bbmin, bbmax)
    drawable_xml.bounding_sphere_radius = get_sphere_radius(bbmin, bbmax)
    drawable_xml.bounding_box_min = bbmin
    drawable_xml.bounding_box_max = bbmax


def create_embedded_collision_xmls(drawable_obj: bpy.types.Object, drawable_xml: Drawable):
    drawable_xml.bounds = None
    bound_objs = [
        child for child in drawable_obj.children
        if child.sollum_type == SollumType.BOUND_COMPOSITE or child.sollum_type in BOUND_TYPES
    ]
    if not bound_objs:
        return

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

    bound_xml = None
    if bound_obj.sollum_type == SollumType.BOUND_COMPOSITE:
        bound_xml = create_composite_xml(bound_obj)
    elif bound_obj.sollum_type in BOUND_TYPES:
        bound_xml = create_bound_xml(bound_obj, is_root=True)

        if not bound_xml.composite_transform.is_identity:
            logger.warning(
                f"Embedded bound '{bound_obj.name}' has transforms (rotation, scale) but is not parented to a Bound "
                f"Composite. Parent the collision to a Bound Composite in order for the transforms to work in-game."
            )

    drawable_xml.bounds = bound_xml


def set_drawable_xml_properties(drawable_obj: bpy.types.Object, drawable_xml: Drawable):
    drawable_xml.lod_dist_high = drawable_obj.drawable_properties.lod_dist_high
    drawable_xml.lod_dist_med = drawable_obj.drawable_properties.lod_dist_med
    drawable_xml.lod_dist_low = drawable_obj.drawable_properties.lod_dist_low
    drawable_xml.lod_dist_vlow = drawable_obj.drawable_properties.lod_dist_vlow


def write_embedded_textures(drawable_obj: bpy.types.Object, filepath: str):
    materials = get_sollumz_materials(drawable_obj)
    directory = os.path.dirname(filepath)
    filename = get_filename(filepath)

    for node in get_embedded_texture_nodes(materials):
        folder_path = os.path.join(directory, filename)
        texture_path = bpy.path.abspath(node.image.filepath)

        if os.path.isfile(texture_path):
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
            dstpath = os.path.join(folder_path, os.path.basename(texture_path))
            # check if paths are the same because if they are, no need to copy (and would throw an error otherwise)
            if not os.path.exists(dstpath) or not os.path.samefile(texture_path, dstpath):
                shutil.copyfile(texture_path, dstpath)
        elif texture_path:
            logger.warning(f"Texture path '{texture_path}' for {node.name} not found! Skipping texture...")


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
                param = TextureShaderParameter()
            case (ShaderParameterType.FLOAT |
                  ShaderParameterType.FLOAT2 |
                  ShaderParameterType.FLOAT3 |
                  ShaderParameterType.FLOAT4):
                if param_def.is_array:
                    param = ArrayShaderParameter()
                    param.values = [Vector() for _ in range(param_def.count)]
                else:
                    param = VectorShaderParameter()
            case ShaderParameterType.FLOAT4X4:
                param = ArrayShaderParameter()
                param.values = [Vector(), Vector(), Vector(), Vector()]
            case _:
                raise Exception(f"Unknown shader parameter! {param.type=} {param.name=}")

        param.name = param_def.name
        parameters.append(param)

    return parameters


def get_shaders_from_blender(materials):
    shaders = []

    for material in materials:
        shader = Shader()
        shader.name = material.shader_properties.name
        shader.filename = material.shader_properties.filename
        shader.render_bucket = RenderBucket[material.shader_properties.renderbucket].value
        shader_def = ShaderManager.find_shader(shader.filename)
        shader.parameters = create_shader_parameters_list_template(shader_def)

        for node in material.node_tree.nodes:
            param = None

            if isinstance(node, bpy.types.ShaderNodeTexImage):
                param_def = shader_def.parameter_map.get(node.name, None)
                if not param_def:
                    continue

                param = TextureShaderParameter()
                param.texture_name = node.sollumz_texture_name
            elif isinstance(node, SzShaderNodeParameter):
                param_def = shader_def.parameter_map.get(node.name, None)
                if not param_def:
                    continue

                is_vector = isinstance(param_def, ShaderParameterFloatVectorDef) and not param_def.is_array
                if is_vector:
                    param = VectorShaderParameter()
                    param.x = node.get(0)
                    param.y = node.get(1) if node.num_cols > 1 else 0.0
                    param.z = node.get(2) if node.num_cols > 2 else 0.0
                    param.w = node.get(3) if node.num_cols > 3 else 0.0
                else:
                    param = ArrayShaderParameter()
                    array_values = []
                    for row in range(node.num_rows):
                        i = row * node.num_cols
                        x = node.get(i)
                        y = node.get(i + 1) if node.num_cols > 1 else 0.0
                        z = node.get(i + 2) if node.num_cols > 2 else 0.0
                        w = node.get(i + 3) if node.num_cols > 3 else 0.0

                        array_values.append(Vector((x, y, z, w)))

                    param.values = array_values

            if param is not None:
                param.name = node.name
                parameter_index = next((i for i, x in enumerate(shader.parameters) if x.name == param.name), None)

                if parameter_index is None:
                    shader.parameters.append(param)
                else:
                    shader.parameters[parameter_index] = param

        shaders.append(shader)

    return shaders
