import os
import shutil
import bmesh
import bpy
import zlib
from typing import Optional
from collections import defaultdict
from mathutils import Quaternion, Vector, Matrix
from ..cwxml.drawable import Drawable, Texture, Skeleton, Bone, Joints, RotationLimit, DrawableModel, Geometry, ArrayShaderParameter, VectorShaderParameter, TextureShaderParameter, Shader
from ..tools import jenkhash
from ..tools.meshhelper import (
    flip_uv,
    get_bound_center_from_bounds,
    get_sphere_radius,
)
from ..tools.utils import get_max_vector, get_min_vector
from ..tools.blenderhelper import remove_number_suffix, join_objects
from ..sollumz_helper import get_sollumz_materials
from ..sollumz_properties import (
    SOLLUMZ_UI_NAMES,
    LODLevel,
    SollumType,
    SollumzExportSettings
)
from .properties import DrawableModelProperties
from .geometry_data import GeometryBuilder
from .properties import SkinnedDrawableModelProperties
from .lights import create_xml_lights

from .. import logger


def export_ydr(drawable_obj: bpy.types.Object, filepath: str, export_settings: SollumzExportSettings):
    drawable_xml = create_drawable_xml(
        drawable_obj, auto_calc_bone_tag=export_settings.auto_calculate_bone_tag)
    drawable_xml.write_xml(filepath)

    write_embedded_textures(drawable_obj, filepath)


def create_drawable_xml(drawable_obj: bpy.types.Object, armature_obj: Optional[bpy.types.Object] = None, auto_calc_bone_tag: bool = False, materials: Optional[list[bpy.types.Material]] = None):
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
            armature_obj, auto_calc_bone_tag)
        drawable_xml.joints = create_joints_xml(
            armature_obj, auto_calc_bone_tag)

        bones = armature_obj.data.bones
    else:
        drawable_xml.skeleton = None
        drawable_xml.joints = None
        bones = None

    skinned_objs = get_skinned_model_objs(drawable_obj)

    if skinned_objs:
        model_props = drawable_obj.skinned_model_properties
        create_skinned_model_xml(
            drawable_xml, skinned_objs, model_props, materials, bones)

    model_objs = get_model_objs(drawable_obj)

    if model_objs:
        create_drawable_model_xmls(
            drawable_xml, model_objs, materials, bones)

    drawable_xml.lights = create_xml_lights(drawable_obj, armature_obj)

    set_drawable_xml_flags(drawable_xml)
    set_drawable_xml_extents(drawable_xml)

    return drawable_xml


def get_skinned_model_objs(drawable_obj: bpy.types.Object):
    """Get all skinned Drawable Model objects under ``drawable_obj``."""
    skinned_objs: list[bpy.types.Object] = []

    for child in drawable_obj.children_recursive:
        if child.sollum_type == SollumType.DRAWABLE_MODEL and child.vertex_groups and not child.sollumz_is_physics_child_mesh:
            skinned_objs.append(child)

    return skinned_objs


def create_skinned_model_xml(drawable_xml: Drawable, skinned_objs: list[bpy.types.Object], skinned_model_props: SkinnedDrawableModelProperties, materials: list[bpy.types.Material], bones: Optional[list[bpy.types.Bone]] = None):
    skinned_obj = get_joined_skinned_obj(skinned_objs)

    if skinned_obj is None:
        return

    for lod in skinned_obj.sollumz_lods.lods:
        if lod.mesh is None or lod.level == LODLevel.VERYHIGH:
            continue

        model_xml = DrawableModel()

        model_props = skinned_model_props.get_lod(lod.level)
        set_model_xml_properties(model_props, model_xml)
        model_xml.has_skin = 1

        geometries = create_geometries_xml(
            skinned_obj, lod.level, materials, bones)
        model_xml.geometries = geometries

        append_model_xml(drawable_xml, model_xml, lod.level)

    if len(skinned_objs) > 1:
        delete_all_lod_meshes(skinned_obj)


def get_joined_skinned_obj(skinned_objs: list[bpy.types.Object]):
    """Join all the skinned objects and their LODs into a single object."""
    # Drawables only ever have 1 skinned drawable model per LOD level. Since, the skinned portion of the
    # drawable can be split by vertex group, we have to join each separate part into a sinlge object.

    if len(skinned_objs) == 1:
        return skinned_objs[0]

    lod_objs: dict[LODLevel, list[bpy.types.Object]] = defaultdict(list)
    lod_meshes = []

    for obj in skinned_objs:
        for lod in obj.sollumz_lods.lods:
            if lod.mesh is None or lod.level == LODLevel.VERYHIGH:
                continue

            lod_obj = obj.copy()
            lod_obj.data = lod.mesh.copy()
            lod_meshes.append(lod_obj.data)

            lod_obj.parent = None

            lod_obj.data.transform(lod_obj.matrix_world)
            lod_obj.matrix_world = Matrix()

            bpy.context.collection.objects.link(lod_obj)

            lod_objs[lod.level].append(lod_obj)

    skinned_obj = None

    for lod_level, objs in lod_objs.items():
        lod_obj = join_objects(objs)

        if skinned_obj is None:
            skinned_obj = bpy.data.objects.new("_temp_skinned", lod_obj.data)
            skinned_obj.sollumz_lods.add_empty_lods()

        skinned_obj.sollumz_lods.set_lod_mesh(lod_level, lod_obj.data)

        bpy.data.objects.remove(lod_obj)

    return skinned_obj


def delete_all_lod_meshes(obj: bpy.types.Object):
    lod_meshes: list[bpy.types.Mesh] = []

    for lod in obj.sollumz_lods.lods:
        if lod.mesh is None:
            continue

        lod_meshes.append(lod.mesh)

    bpy.data.objects.remove(obj)

    for mesh in lod_meshes:
        bpy.data.meshes.remove(mesh)


def get_model_objs(drawable_obj: bpy.types.Object):
    """Get all non-skinned Drawable Model objects under ``drawable_obj``."""
    model_objs: list[bpy.types.Object] = []

    for child in drawable_obj.children_recursive:
        if child.sollum_type == SollumType.DRAWABLE_MODEL and not child.vertex_groups and not child.sollumz_is_physics_child_mesh:
            model_objs.append(child)

    return model_objs


def create_drawable_model_xmls(drawable_xml: Drawable, model_objs: list[bpy.types.Object], materials: list[bpy.types.Material], bones: Optional[list[bpy.types.Bone]] = None):
    for model_obj in model_objs:
        for lod in model_obj.sollumz_lods.lods:
            if lod.mesh is None or lod.level == LODLevel.VERYHIGH:
                continue

            model_xml = create_model_xml(
                model_obj, lod.level, materials, bones)
            append_model_xml(drawable_xml, model_xml, lod.level)


def create_model_xml(model_obj: bpy.types.Object, lod_level: LODLevel, materials: list[bpy.types.Material], bones: Optional[list[bpy.types.Bone]] = None):
    model_xml = DrawableModel()

    set_lod_model_xml_properties(model_obj, model_xml)

    geometries = create_geometries_xml(model_obj, lod_level, materials, bones)
    model_xml.geometries = geometries

    model_xml.bone_index = get_model_bone_index(model_obj)

    return model_xml


def get_armature_constraint(obj: bpy.types.Object) -> Optional[bpy.types.ArmatureConstraint]:
    for constraint in obj.constraints:
        if constraint.type != "ARMATURE" or not constraint.targets:
            continue

        target = constraint.targets[0]

        if not target.target or not target.subtarget:
            continue

        return constraint


def get_model_bone_index(model_obj: bpy.types.Object):
    bone_index = 0

    constraint = get_armature_constraint(model_obj)

    if constraint is None:
        return bone_index

    target = constraint.targets[0]
    armature = target.target.data
    bone_index = armature.bones.find(target.subtarget)

    return bone_index if bone_index != -1 else 0


def set_lod_model_xml_properties(model_obj: bpy.types.Object, model_xml: DrawableModel):
    """Set ``DrawableModel`` properties for each lod in ``model_obj``"""
    for lod in model_obj.sollumz_lods.lods:
        if lod.mesh is None or lod.level == LODLevel.VERYHIGH:
            continue

        set_model_xml_properties(lod.mesh.drawable_model_properties, model_xml)


def create_geometries_xml(model_obj: bpy.types.Object, lod_level: LODLevel, materials: list[bpy.types.Material], bones: Optional[list[bpy.types.Bone]] = None):
    current_lod_level = model_obj.sollumz_lods.active_lod.level
    # Set the object lod level to lod_level to evaluate that lod mesh
    was_hidden = model_obj.hide_get()
    model_obj.sollumz_lods.set_active_lod(lod_level)
    mesh = evaluate_and_triangulate_object(model_obj)
    # Set the lod level back to what it was
    model_obj.sollumz_lods.set_active_lod(current_lod_level)
    model_obj.hide_set(was_hidden)

    if not mesh.materials:
        logger.warning(
            f"Mesh '{mesh.name}' has no Sollumz materials! Skipping...")
        return []

    geometries: list[Geometry] = []

    tris_by_mat = get_loop_triangles_by_mat(mesh, materials)

    for mat_index, loop_triangles in tris_by_mat.items():
        geometry_xmls = GeometryBuilder(
            loop_triangles,
            mesh,
            materials[mat_index],
            mat_index,
            model_obj.vertex_groups,
            bones or []
        ).build()

        geometries.extend(geometry_xmls)

    bpy.data.meshes.remove(mesh)

    return geometries


def get_loop_triangles_by_mat(mesh: bpy.types.Mesh, materials: list[bpy.types.Material]):
    """Return mapping of ``mesh.loop_triangles`` separated by each material in ``materials``."""
    mat_ind_by_name: dict[str, int] = {
        mat.name: i for i, mat in enumerate(materials)}

    tris_by_mat: dict[int, list[bpy.types.MeshLoopTriangle]
                      ] = defaultdict(list)

    has_unassigned_mats = False

    for tri in mesh.loop_triangles:
        if not (0 <= tri.material_index < len(mesh.materials)):
            has_unassigned_mats = True
            mat_index = 0
        else:
            mat = mesh.materials[tri.material_index]
            # Get index of material on the entire drawable
            mat_index = mat_ind_by_name[mat.name]

        tris_by_mat[mat_index].append(tri)

    if has_unassigned_mats:
        logger.warning(
            f"Mesh '{mesh.name}' has materials with no vertices assigned!")

    return tris_by_mat


def evaluate_and_triangulate_object(obj: bpy.types.Object):
    """Get an evaluated, triangulated version of the mesh (modifiers, constraints, etc applied)"""
    depsgraph = bpy.context.evaluated_depsgraph_get()
    obj_eval = obj.evaluated_get(depsgraph)

    mesh = bpy.data.meshes.new_from_object(
        obj_eval, preserve_all_data_layers=True, depsgraph=depsgraph)

    tempmesh = bmesh.new()
    tempmesh.from_mesh(mesh)
    bmesh.ops.triangulate(tempmesh, faces=tempmesh.faces)
    tempmesh.to_mesh(mesh)
    tempmesh.free()

    if mesh.uv_layers:
        mesh.calc_tangents()

    mesh.calc_loop_triangles()

    return mesh


def append_model_xml(drawable_xml: Drawable, model_xml: DrawableModel, lod_level: LODLevel):
    if lod_level == LODLevel.HIGH:
        drawable_xml.drawable_models_high.append(model_xml)

    elif lod_level == LODLevel.MEDIUM:
        drawable_xml.drawable_models_med.append(model_xml)

    elif lod_level == LODLevel.LOW:
        drawable_xml.drawable_models_low.append(model_xml)

    elif lod_level == LODLevel.VERYLOW:
        drawable_xml.drawable_models_vlow.append(model_xml)


def create_shader_group_xml(materials: list[bpy.types.Material], drawable_xml: Drawable):
    shaders = get_shaders_from_blender(materials)
    texture_dictionary = texture_dictionary_from_materials(materials)

    drawable_xml.shader_group.shaders = shaders
    drawable_xml.shader_group.texture_dictionary = texture_dictionary


def texture_dictionary_from_materials(materials: list[bpy.types.Material]):
    texture_dictionary: dict[str, Texture] = {}

    for node in get_embedded_texture_nodes(materials):
        texture_name = node.sollumz_texture_name

        if texture_name in texture_dictionary:
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
                logger.warning(
                    f"Material '{mat.name}' has no embedded texture for '{node.name}'. Material will be skipped...")
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


def create_skeleton_xml(armature_obj: bpy.types.Object, auto_calc_bone_tag: bool = False):
    if armature_obj.type != "ARMATURE" or not armature_obj.pose.bones:
        return None

    skeleton_xml = Skeleton()
    bones = armature_obj.pose.bones

    for bone_index, pose_bone in enumerate(bones):

        bone_xml = create_bone_xml(
            pose_bone, bone_index, armature_obj.data, auto_calc_bone_tag)

        skeleton_xml.bones.append(bone_xml)

    calculate_skeleton_unks(skeleton_xml)

    return skeleton_xml


def create_bone_xml(pose_bone: bpy.types.PoseBone, bone_index: int, armature: bpy.types.Armature, auto_calc_bone_tag: bool = False):
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
    set_bone_xml_transforms(bone_xml, bone)

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


def set_bone_xml_transforms(bone_xml: Bone, bone: bpy.types.Bone):
    mat = bone.matrix_local

    if bone.parent is not None:
        mat = bone.parent.matrix_local.inverted() @ mat

    pos, rot, scale = mat.decompose()

    bone_xml.translation = pos
    bone_xml.rotation = rot
    bone_xml.scale = scale
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
        joint = create_rotation_limit_xml(pose_bone, auto_calc_bone_tag)

        if joint is not None:
            joints.rotation_limits.append(joint)

    return joints


def create_rotation_limit_xml(pose_bone: bpy.types.PoseBone, auto_calc_bone_tag: bool = False):
    for constraint in pose_bone.constraints:
        if constraint.type != "LIMIT_ROTATION":
            continue

        joint = RotationLimit()
        joint.bone_id = pose_bone.bone.bone_properties.tag if auto_calc_bone_tag else calculate_bone_tag(
            pose_bone.bone.name)
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
    bbmin = Vector()
    bbmax = Vector()

    for model_xml in drawable_xml.drawable_models_high:
        for geometry in model_xml.geometries:
            bbmin = get_min_vector(geometry.bounding_box_min, bbmin)
            bbmax = get_max_vector(geometry.bounding_box_max, bbmax)

    drawable_xml.bounding_sphere_center = get_bound_center_from_bounds(
        bbmin, bbmax)
    drawable_xml.bounding_sphere_radius = get_sphere_radius(
        bbmax, drawable_xml.bounding_sphere_center)
    drawable_xml.bounding_box_min = bbmin
    drawable_xml.bounding_box_max = bbmax


def set_model_xml_properties(model_props: DrawableModelProperties, model_xml: DrawableModel):
    model_xml.render_mask = model_props.render_mask
    model_xml.flags = model_props.flags
    model_xml.unknown_1 = model_props.unknown_1


def set_drawable_xml_properties(drawable_obj: bpy.types.Object, drawable_xml: Drawable):
    drawable_xml.lod_dist_high = drawable_obj.drawable_properties.lod_dist_high
    drawable_xml.lod_dist_med = drawable_obj.drawable_properties.lod_dist_med
    drawable_xml.lod_dist_low = drawable_obj.drawable_properties.lod_dist_low
    drawable_xml.lod_dist_vlow = drawable_obj.drawable_properties.lod_dist_vlow
    drawable_xml.unknown_9A = drawable_obj.drawable_properties.unknown_9A


def write_embedded_textures(drawable_obj: bpy.types.Object, filepath: str):
    materials = get_sollumz_materials(drawable_obj)
    directory = os.path.dirname(filepath)

    for node in get_embedded_texture_nodes(materials):
        folder_path = os.path.join(
            directory, remove_number_suffix(drawable_obj.name))
        texture_path = bpy.path.abspath(node.image.filepath)

        if os.path.isfile(texture_path):
            if not os.path.isdir(folder_path):
                os.mkdir(folder_path)
            dstpath = folder_path + "\\" + \
                os.path.basename(texture_path)
            # check if paths are the same because if they are no need to copy
            if texture_path != dstpath:
                shutil.copyfile(texture_path, dstpath)
        else:
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
