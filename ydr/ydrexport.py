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

from ..cwxml.drawable import BoneLimit, Drawable, Texture, Skeleton, Bone, Joints, RotationLimit, DrawableModel, Geometry, ArrayShaderParameter, VectorShaderParameter, TextureShaderParameter, Shader, VertexBuffer
from ..tools import jenkhash
from ..tools.meshhelper import (
    get_bound_center_from_bounds,
    get_sphere_radius,
)
from ..tools.utils import get_filename, get_max_vector_list, get_min_vector_list
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
from .vertex_buffer_builder import VertexBufferBuilder, dedupe_and_get_indices, remove_arr_field, remove_unused_colors, get_bone_by_vgroup, remove_unused_uvs
from .lights import create_xml_lights
from ..cwxml.shader import ShaderManager

from .. import logger


def export_ydr(drawable_obj: bpy.types.Object, filepath: str):
    export_settings = get_export_settings()

    drawable_xml = create_drawable_xml(
        drawable_obj, auto_calc_bone_tag=export_settings.auto_calculate_bone_tag, auto_calc_inertia=export_settings.auto_calculate_inertia, auto_calc_volume=export_settings.auto_calculate_volume, apply_transforms=export_settings.apply_transforms)
    drawable_xml.write_xml(filepath)

    write_embedded_textures(drawable_obj, filepath)


def create_drawable_xml(drawable_obj: bpy.types.Object, armature_obj: Optional[bpy.types.Object] = None, auto_calc_bone_tag: bool = False, materials: Optional[list[bpy.types.Material]] = None, auto_calc_volume: bool = False, auto_calc_inertia: bool = False, apply_transforms: bool = False):
    """Create a ``Drawable`` cwxml object. Optionally specify an external ``armature_obj`` if ``drawable_obj`` is not an armature."""
    drawable_xml = Drawable()
    drawable_xml.matrix = None

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

        drawable_xml.skeleton = create_skeleton_xml(
            armature_obj, auto_calc_bone_tag, apply_transforms)
        drawable_xml.joints = create_joints_xml(
            armature_obj, auto_calc_bone_tag)

        bones = armature_obj.data.bones

        original_pose = armature_obj.data.pose_position
        armature_obj.data.pose_position = "REST"
    else:
        drawable_xml.skeleton = None
        drawable_xml.joints = None
        bones = None
        original_pose = "POSE"

    create_model_xmls(drawable_xml, drawable_obj, materials, bones)

    drawable_xml.lights = create_xml_lights(drawable_obj, armature_obj)

    set_drawable_xml_flags(drawable_xml)
    set_drawable_xml_extents(drawable_xml)

    create_embedded_collision_xmls(
        drawable_obj, drawable_xml, auto_calc_volume, auto_calc_inertia)

    if armature_obj is not None:
        armature_obj.data.pose_position = original_pose

    return drawable_xml


def create_model_xmls(drawable_xml: Drawable, drawable_obj: bpy.types.Object, materials: list[bpy.types.Material], bones: Optional[list[bpy.types.Bone]] = None):
    model_objs = get_model_objs(drawable_obj)

    if bones is not None:
        model_objs = sort_skinned_models_by_bone(model_objs, bones)

    for model_obj in model_objs:
        transforms_to_apply = get_export_transforms_to_apply(model_obj)

        for lod in model_obj.sollumz_lods.lods:
            if lod.mesh is None or lod.level == LODLevel.VERYHIGH:
                continue

            model_xml = create_model_xml(
                model_obj, lod.level, materials, bones, transforms_to_apply)

            if not model_xml.geometries:
                continue

            append_model_xml(drawable_xml, model_xml, lod.level)

    # Drawables only ever have 1 skinned drawable model per LOD level. Since, the skinned portion of the
    # drawable can be split by vertex group, we have to join each separate part into a single object.
    join_skinned_models_for_each_lod(drawable_xml)
    split_drawable_by_vert_count(drawable_xml)


def get_model_objs(drawable_obj: bpy.types.Object) -> list[bpy.types.Object]:
    """Get all non-skinned Drawable Model objects under ``drawable_obj``."""
    return [obj for obj in drawable_obj.children if obj.sollum_type == SollumType.DRAWABLE_MODEL and not obj.sollumz_is_physics_child_mesh]


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
def create_model_xml(model_obj: bpy.types.Object, lod_level: LODLevel, materials: list[bpy.types.Material], bones: Optional[list[bpy.types.Bone]] = None, transforms_to_apply: Optional[Matrix] = None):
    model_xml = DrawableModel()

    set_model_xml_properties(model_obj, lod_level, model_xml)

    obj_eval = get_evaluated_obj(model_obj)
    mesh_eval = obj_eval.to_mesh()
    triangulate_mesh(mesh_eval)

    if transforms_to_apply is not None:
        mesh_eval.transform(transforms_to_apply)

    geometries = create_geometries_xml(
        mesh_eval, materials, bones, model_obj.vertex_groups)
    model_xml.geometries = geometries

    model_xml.bone_index = get_model_bone_index(model_obj)

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


def set_model_xml_properties(model_obj: bpy.types.Object, lod_level: LODLevel, model_xml: DrawableModel):
    """Set ``DrawableModel`` properties for each lod in ``model_obj``"""
    model_props = get_model_properties(model_obj, lod_level)

    model_xml.render_mask = model_props.render_mask
    model_xml.flags = model_props.flags
    model_xml.unknown_1 = model_props.unknown_1
    model_xml.has_skin = 1 if model_obj.vertex_groups else 0


def create_geometries_xml(mesh_eval: bpy.types.Mesh, materials: list[bpy.types.Material], bones: Optional[list[bpy.types.Bone]] = None, vertex_groups: Optional[list[bpy.types.VertexGroup]] = None) -> list[Geometry]:
    if len(mesh_eval.loops) == 0:
        logger.warning(
            f"Drawable Model '{mesh_eval.original.name}' has no Geometry! Skipping...")
        return []

    if not mesh_eval.materials:
        logger.warning(
            f"Could not create geometries for Drawable Model '{mesh_eval.original.name}': Mesh has no Sollumz materials!")
        return []

    loop_inds_by_mat = get_loop_inds_by_material(mesh_eval, materials)

    geometries: list[Geometry] = []

    bone_by_vgroup = get_bone_by_vgroup(
        vertex_groups, bones) if bones and vertex_groups else None

    total_vert_buffer = VertexBufferBuilder(mesh_eval, bone_by_vgroup).build()

    for mat_index, loop_inds in loop_inds_by_mat.items():
        material = materials[mat_index]
        tangent_required = get_tangent_required(material)
        normal_required = get_normal_required(material)

        vert_buffer = total_vert_buffer[loop_inds]
        used_texcoords = get_used_texcoords(material)

        vert_buffer = remove_unused_uvs(vert_buffer, used_texcoords)
        vert_buffer = remove_unused_colors(vert_buffer)

        if not tangent_required:
            vert_buffer = remove_arr_field("Tangent", vert_buffer)

        if not normal_required:
            vert_buffer = remove_arr_field("Normal", vert_buffer)

        vert_buffer, ind_buffer = dedupe_and_get_indices(vert_buffer)

        geom_xml = Geometry()

        geom_xml.bounding_box_max, geom_xml.bounding_box_min = get_geom_extents(
            vert_buffer["Position"])
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

        loop_inds_by_mat[shader_index] = loop_indices

    return loop_inds_by_mat


def get_tangent_required(material: bpy.types.Material):
    shader_name = material.shader_properties.filename

    if shader_name not in ShaderManager.shaders:
        return False

    shader = ShaderManager.shaders[shader_name]

    return shader.required_tangent


def get_used_texcoords(material: bpy.types.Material):
    """Get TexCoords that the material's shader uses"""
    shader_name = material.shader_properties.filename

    if shader_name not in ShaderManager.shaders:
        return {"TexCoord0"}

    shader = ShaderManager.shaders[shader_name]

    return shader.used_texcoords


def get_normal_required(material: bpy.types.Material):
    # Minimap shaders dont use normals. Any other shaders like this?
    return material.shader_properties.filename != "minimap.sps"


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
    skinned_model.unknown_1 = skinned_models[0].unknown_1
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

    MAX_VERTS = 65535

    vert_buffers, ind_buffers = split_vert_buffers_by_count(
        geom_xml.vertex_buffer.data, geom_xml.index_buffer.data, MAX_VERTS)

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


def split_vert_buffers_by_count(vert_buffer: NDArray, ind_buffer: NDArray[np.uint32], count: int) -> tuple[tuple[NDArray], tuple[NDArray[np.uint32]]]:
    """Splits vertex and index buffers by vertex count. Returns tuple of split vertex buffers and tuple of index buffers"""
    num_splits = math.ceil(len(vert_buffer) / count)

    if num_splits <= 1:
        return ((vert_buffer,), (ind_buffer,))

    num_tris = math.ceil(len(ind_buffer) / 3)
    face_inds = np.arange(num_tris, dtype=np.uint32)

    split_vert_arrs = []
    split_ind_arrs = []

    for faces_split in np.array_split(face_inds, num_splits):
        split_vert_arr, split_ind_arr = get_faces_subset(
            vert_buffer, ind_buffer, faces_split)
        split_vert_arrs.append(split_vert_arr)
        split_ind_arrs.append(split_ind_arr)

    return (tuple(split_vert_arrs), tuple(split_ind_arrs))


def create_shader_group_xml(materials: list[bpy.types.Material], drawable_xml: Drawable):
    shaders = get_shaders_from_blender(materials)
    texture_dictionary = texture_dictionary_from_materials(materials)

    drawable_xml.shader_group.shaders = shaders
    drawable_xml.shader_group.texture_dictionary = texture_dictionary
    drawable_xml.shader_group.unknown_30 = calc_shadergroup_unk30(len(shaders))


def calc_shadergroup_unk30(num_shaders: int):
    # Its still unknown what unk30 actually is. But for 98% of files it can be
    # calculated like this. It follows this pattern:
    # (ShaderCount: 1, Unk30: 8), (ShaderCount: 2, Unk30: 11), (ShaderCount: 3, Unk30: 15),
    # (ShaderCount: 4, Unk30: 18)... Unk30 increases by 3 for odd shader counts and 4 for even shader counts
    if num_shaders % 2 == 0:
        return int((0.5 * num_shaders) * 7 + 4)

    return int((0.5 * (num_shaders + 1)) * 7 + 1)


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

    texture.usage = SOLLUMZ_UI_NAMES[node.texture_properties.usage]
    texture.extra_flags = node.texture_properties.extra_flags
    texture.format = SOLLUMZ_UI_NAMES[node.texture_properties.format]
    texture.miplevels = 0
    texture.filename = texture.name + ".dds"

    set_texture_flags(node, texture)

    return texture


def set_texture_flags(node: bpy.types.ShaderNodeTexImage, texture: Texture):
    """Set the texture flags of ``texture`` from ``node.texture_flags``."""
    for prop in dir(node.texture_flags):
        value = getattr(node.texture_flags, prop)

        if value == True:
            texture.usage_flags.append(prop.upper())

    return texture


def create_skeleton_xml(armature_obj: bpy.types.Object, auto_calc_bone_tag: bool = False, apply_transforms: bool = False):
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

        bone_xml = create_bone_xml(
            pose_bone, bone_index, armature_obj.data, matrix, auto_calc_bone_tag)

        skeleton_xml.bones.append(bone_xml)

    calculate_skeleton_unks(skeleton_xml)

    return skeleton_xml


def create_bone_xml(pose_bone: bpy.types.PoseBone, bone_index: int, armature: bpy.types.Armature, armature_matrix: Matrix, auto_calc_bone_tag: bool = False):
    bone = pose_bone.bone

    bone_xml = Bone()
    bone_xml.name = bone.name
    bone_xml.index = bone_index

    if auto_calc_bone_tag:
        bone_xml.tag = calculate_bone_tag(
            bone_xml.name) if bone_xml.index > 0 else 0
    else:
        bone_xml.tag = bone.bone_properties.tag

    bone_xml.parent_index = get_bone_parent_index(bone, armature)
    bone_xml.sibling_index = get_bone_sibling_index(bone, armature)

    set_bone_xml_flags(bone_xml, pose_bone)
    set_bone_xml_transforms(bone_xml, bone, armature_matrix)

    return bone_xml


def calculate_bone_tag(bone_name: str):
    hash = 0
    x = 0

    for char in str.upper(bone_name):
        char = ord(char)
        hash = (hash << 4) + char
        x = hash & 0xF0000000

        if x != 0:
            hash ^= x >> 24

        hash &= ~x

    return hash % 0xFE8F + 0x170


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


def create_joints_xml(armature_obj: bpy.types.Object, auto_calc_bone_tag: bool = False):
    if armature_obj.pose is None:
        return None

    joints = Joints()

    for pose_bone in armature_obj.pose.bones:
        limit_rot_constraint = get_limit_rot_constraint(pose_bone)
        limit_pos_constraint = get_limit_pos_constraint(pose_bone)
        bone_tag = pose_bone.bone.bone_properties.tag if auto_calc_bone_tag else calculate_bone_tag(
            pose_bone.bone.name)

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


def create_rotation_limit_xml(constraint: bpy.types.LimitRotationConstraint, bone_tag: str):
    joint = RotationLimit()
    set_joint_properties(joint, constraint, bone_tag)

    return joint


def create_translation_limit_xml(constraint: bpy.types.LimitRotationConstraint, bone_tag: str):
    joint = BoneLimit()
    set_joint_properties(joint, constraint, bone_tag)

    return joint


def set_joint_properties(joint: BoneLimit, constraint: bpy.types.LimitRotationConstraint | bpy.types.LimitLocationConstraint, bone_tag: str):
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

    drawable_xml.bounding_sphere_center = get_bound_center_from_bounds(
        bbmin, bbmax)
    drawable_xml.bounding_sphere_radius = get_sphere_radius(
        bbmax, drawable_xml.bounding_sphere_center)
    drawable_xml.bounding_box_min = bbmin
    drawable_xml.bounding_box_max = bbmax


def create_embedded_collision_xmls(drawable_obj: bpy.types.Object, drawable_xml: Drawable, auto_calc_volume: bool = False, auto_calc_inertia: bool = False):
    for child in drawable_obj.children:
        bound_xml = None

        if child.sollum_type == SollumType.BOUND_COMPOSITE:
            bound_xml = create_composite_xml(
                child, auto_calc_inertia, auto_calc_volume)
        elif child.sollum_type in BOUND_TYPES:
            bound_xml = create_bound_xml(
                child, auto_calc_inertia, auto_calc_volume)

            if not bound_xml.composite_transform.is_identity:
                logger.warning(
                    f"Embedded bound '{child.name}' has transforms (location, rotation, scale) but is not parented to a Bound Composite. Parent the collision to a Bound Composite in order for the transforms to work in-game.")

        if bound_xml is not None:
            drawable_xml.bounds.append(bound_xml)


def set_drawable_xml_properties(drawable_obj: bpy.types.Object, drawable_xml: Drawable):
    drawable_xml.lod_dist_high = drawable_obj.drawable_properties.lod_dist_high
    drawable_xml.lod_dist_med = drawable_obj.drawable_properties.lod_dist_med
    drawable_xml.lod_dist_low = drawable_obj.drawable_properties.lod_dist_low
    drawable_xml.lod_dist_vlow = drawable_obj.drawable_properties.lod_dist_vlow
    drawable_xml.unknown_9A = drawable_obj.drawable_properties.unknown_9A


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
            dstpath = folder_path + "\\" + \
                os.path.basename(texture_path)
            # check if paths are the same because if they are no need to copy
            if texture_path != dstpath:
                shutil.copyfile(texture_path, dstpath)
        elif texture_path:
            logger.warning(
                f"Texture path '{texture_path}' for {node.name} not found! Skipping texture...")


def get_shaders_from_blender(materials):
    shaders = []

    for material in materials:
        shader = Shader()
        # Maybe make this a property?
        shader.name = material.shader_properties.name
        shader.filename = material.shader_properties.filename
        shader.render_bucket = material.shader_properties.renderbucket

        for node in material.node_tree.nodes:
            if isinstance(node, bpy.types.ShaderNodeTexImage):
                param = TextureShaderParameter()
                param.name = node.name
                param.type = "Texture"
                # Disable extra material writing to xml
                if param.name == "Extra":
                    continue
                else:
                    param.texture_name = node.sollumz_texture_name
                shader.parameters.append(param)
            elif isinstance(node, bpy.types.ShaderNodeValue):
                if node.name[-1] == "x":
                    param = VectorShaderParameter()
                    param.name = node.name[:-2]
                    param.type = "Vector"

                    x = node
                    y = material.node_tree.nodes[node.name[:-1] + "y"]
                    z = material.node_tree.nodes[node.name[:-1] + "z"]
                    w = material.node_tree.nodes[node.name[:-1] + "w"]

                    param.x = x.outputs[0].default_value
                    param.y = y.outputs[0].default_value
                    param.z = z.outputs[0].default_value
                    param.w = w.outputs[0].default_value

                    shader.parameters.append(param)
            elif isinstance(node, bpy.types.ShaderNodeGroup) and node.is_sollumz:
                # Only perform logic if its ArrayNode
                if node.node_tree.name == "ArrayNode" and node.name[-1] == "1":
                    node_name = node.name[:-2]
                    param = ArrayShaderParameter()
                    param.name = node_name
                    param.type = "Array"

                    all_array_nodes = [
                        x for x in material.node_tree.nodes if node_name in x.name]
                    all_array_values = []
                    for item_node in all_array_nodes:
                        x = item_node.inputs[0].default_value
                        y = item_node.inputs[1].default_value
                        z = item_node.inputs[2].default_value
                        w = item_node.inputs[3].default_value

                        all_array_values.append(Vector((x, y, z, w)))

                    param.values = all_array_values
                    shader.parameters.append(param)

        shaders.append(shader)

    return shaders
