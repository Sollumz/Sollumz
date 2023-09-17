from __future__ import annotations

import bpy
import math
from sys import float_info
from mathutils import Quaternion, Vector, Euler, Matrix
from enum import IntFlag, IntEnum
from ..sollumz_properties import MaterialType, SollumType
from ..tools import jenkhash
from .blenderhelper import build_name_bone_map, build_bone_map, get_data_obj
from typing import Tuple
from ..cwxml.shader import ShaderManager

from .. import logger

class AnimationFlag(IntFlag):
    Default = 0
    RootMotion = 16


class Track(IntEnum):
    """An enumeration of Animation Tracks supported by GTA."""
    BonePosition = 0
    BoneRotation = 1
    BoneScale = 2
    MoverPosition = 5
    MoverRotation = 6
    CameraPosition = 7
    CameraRotation = 8
    UV0 = 17
    UV1 = 18
    Unk22 = 22
    Unk24 = 24
    Unk25 = 25
    Unk26 = 26
    CameraFOV = 27
    CameraDOF = 28
    Unk29 = 29
    Unk30 = 30
    Unk31 = 31
    Unk32 = 32
    Unk33 = 33
    Unk34 = 34
    CameraDOFStrength = 36
    CameraUnk39 = 39
    Unk40 = 40
    Unk41 = 41
    Unk42 = 42
    CameraDOFPlaneNearUnk = 43
    CameraDOFPlaneNear = 44
    CameraDOFPlaneFarUnk = 45
    CameraDOFPlaneFar = 46
    Unk47 = 47
    CameraUnk48 = 48
    CameraDOFUnk49 = 49
    Unk50 = 50
    CameraDOFUnk51 = 51
    Unk52 = 52
    Unk53 = 53
    Unk134 = 134
    Unk136 = 136
    Unk137 = 137
    Unk138 = 138
    Unk139 = 139
    Unk140 = 140

    # not a real track, refers to the uv_transforms collection
    UVTransforms = 1000


class TrackFormat(IntEnum):
    Vector3 = 0
    Quaternion = 1
    Float = 2


TrackFormatMap = {
    Track.BonePosition: TrackFormat.Vector3,
    Track.BoneRotation: TrackFormat.Quaternion,
    Track.BoneScale: TrackFormat.Vector3,
    Track.MoverPosition: TrackFormat.Vector3,
    Track.MoverRotation: TrackFormat.Quaternion,
    Track.CameraPosition: TrackFormat.Vector3,
    Track.CameraRotation: TrackFormat.Quaternion,
    Track.UV0: TrackFormat.Vector3,
    Track.UV1: TrackFormat.Vector3,
    Track.Unk22: TrackFormat.Float,
    Track.Unk24: TrackFormat.Float,
    Track.Unk25: TrackFormat.Vector3,
    Track.Unk26: TrackFormat.Quaternion,
    Track.CameraFOV: TrackFormat.Float,
    Track.CameraDOF: TrackFormat.Vector3,
    Track.Unk29: TrackFormat.Vector3,
    Track.Unk30: TrackFormat.Float,
    Track.Unk31: TrackFormat.Float,
    Track.Unk32: TrackFormat.Float,
    Track.Unk33: TrackFormat.Float,
    Track.Unk34: TrackFormat.Vector3,
    Track.CameraDOFStrength: TrackFormat.Float,
    Track.CameraUnk39: TrackFormat.Float,
    Track.Unk40: TrackFormat.Float,
    Track.Unk41: TrackFormat.Float,
    Track.Unk42: TrackFormat.Vector3,
    Track.CameraDOFPlaneNearUnk: TrackFormat.Float,
    Track.CameraDOFPlaneNear: TrackFormat.Float,
    Track.CameraDOFPlaneFarUnk: TrackFormat.Float,
    Track.CameraDOFPlaneFar: TrackFormat.Float,
    Track.Unk47: TrackFormat.Float,
    Track.CameraUnk48: TrackFormat.Float,
    Track.CameraDOFUnk49: TrackFormat.Float,
    Track.Unk50: TrackFormat.Float,
    Track.CameraDOFUnk51: TrackFormat.Float,
    Track.Unk52: TrackFormat.Float,
    Track.Unk53: TrackFormat.Float,
    Track.Unk134: TrackFormat.Float,
    Track.Unk136: TrackFormat.Float,
    Track.Unk137: TrackFormat.Float,
    Track.Unk138: TrackFormat.Float,
    Track.Unk139: TrackFormat.Float,
    Track.Unk140: TrackFormat.Float,
}


# Mapping of Track to Blender property names. See ycd.properties.AnimationTracks.
TrackToPropertyNameMap = {
    Track.MoverPosition: "mover_location",
    Track.MoverRotation: "mover_rotation",
    Track.CameraPosition: "camera_location",
    Track.CameraRotation: "camera_rotation",
    Track.UV0: "uv0",
    Track.UV1: "uv1",
    Track.Unk22: "unk_22",
    Track.Unk24: "unk_24",
    Track.Unk25: "unk_25",
    Track.Unk26: "unk_26",
    Track.CameraFOV: "camera_fov",
    Track.CameraDOF: "camera_dof",
    Track.Unk29: "unk_29",
    Track.Unk30: "unk_30",
    Track.Unk31: "unk_31",
    Track.Unk32: "unk_32",
    Track.Unk33: "unk_33",
    Track.Unk34: "unk_34",
    Track.CameraDOFStrength: "camera_dof_strength",
    Track.CameraUnk39: "camera_unk_39",
    Track.Unk40: "unk_40",
    Track.Unk41: "unk_41",
    Track.Unk42: "unk_42",
    Track.CameraDOFPlaneNearUnk: "camera_dof_plane_near_unk",
    Track.CameraDOFPlaneNear: "camera_dof_plane_near",
    Track.CameraDOFPlaneFarUnk: "camera_dof_plane_far_unk",
    Track.CameraDOFPlaneFar: "camera_dof_plane_far",
    Track.Unk47: "unk_47",
    Track.CameraUnk48: "camera_unk_48",
    Track.CameraDOFUnk49: "camera_dof_unk_49",
    Track.Unk50: "unk_50",
    Track.CameraDOFUnk51: "camera_dof_unk_51",
    Track.Unk52: "unk_52",
    Track.Unk53: "unk_53",
    Track.Unk134: "unk_134",
    Track.Unk136: "unk_136",
    Track.Unk137: "unk_137",
    Track.Unk138: "unk_138",
    Track.Unk139: "unk_139",
    Track.Unk140: "unk_140",
}

PropertyNameToTrackMap = {v: k for k, v in TrackToPropertyNameMap.items()}


def get_quantum_and_min_val(nums):
    min_val = float_info.max
    max_val = float_info.min
    min_delta = float_info.max
    last_val = 0

    for value in nums:
        min_val = min(min_val, value)
        max_val = max(max_val, value)

        if value != last_val:
            min_delta = min(min_delta, abs(value - last_val))

        last_val = value

    if min_delta == float_info.max:
        min_delta = 0

    range_value = max_val - min_val
    min_quant = range_value / 1048576
    quantum = max(min_delta, min_quant)

    return min_val, quantum


def decompose_uv_affine_matrix(
        uv0: Vector, uv1: Vector
) -> Tuple[Tuple[float, float], float, Tuple[float, float], float]:
    """
    Decompose the UV affine matrix into translation, rotation in radians, scale, and shear along X axis.
    """
    a = uv0[0]
    b = uv0[1]
    c = uv1[0]
    d = uv1[1]

    tx = uv0[2]
    ty = uv1[2]
    rotation = math.atan2(c, a)
    cos = math.cos(rotation)
    sin = math.sin(rotation)
    sx = math.sqrt(a * a + c * c)
    sy = d * cos - b * sin
    shear_x = (b * cos + d * sin) / sy if sy != 0.0 else 0.0

    return (tx, ty), rotation, (sx, sy), shear_x


# def compose_uv_affine_matrix(self, translation, rotation, scale, shear_x):
#     cos = math.cos(rotation)
#     sin = math.sin(rotation)
#
#     rotation_mat = Matrix((
#         (cos, -sin),
#         (sin, cos)
#     ))
#     shear_x_mat = Matrix((
#         (1.0, shear_x),
#         (0.0, 1.0)
#     ))
#     scale_mat = Matrix((
#         (scale[0], 0.0),
#         (0.0, scale[1])
#     ))
#
#     affine_mat = rotation_mat @ shear_x_mat @ scale_mat
#
#     self.uv0[0] = affine_mat[0][0]
#     self.uv0[1] = affine_mat[0][1]
#     self.uv1[0] = affine_mat[1][0]
#     self.uv1[1] = affine_mat[1][1]
#     self.uv0[2] = translation[0]
#     self.uv1[2] = translation[1]

def calculate_bone_space_transform_matrix(old_pose_bone, new_pose_bone):
    if old_pose_bone is None:
        old_mat = Matrix.Identity(4)
    else:
        old_bone = old_pose_bone.bone
        old_mat = old_bone.matrix_local
        if old_bone.parent is not None:
            old_mat = old_bone.parent.matrix_local.inverted() @ old_mat

    if new_pose_bone is None:
        new_mat = Matrix.Identity(4)
    else:
        new_bone = new_pose_bone.bone
        new_mat = new_bone.matrix_local
        if new_bone.parent is not None:
            new_mat = new_bone.parent.matrix_local.inverted() @ new_mat

    return new_mat.inverted() @ old_mat


def transform_bone_location_space(fcurves, old_pose_bone, new_pose_bone):
    """
    Converts the vector3 F-curves from the old pose bone's space to the new pose bone's space.
    Either bone can be None, meaning convert from/to the original local space (as stored in the animation channels).
    """
    x = fcurves[0]
    y = fcurves[1]
    z = fcurves[2]

    if x is None:
        return

    assert len(x.keyframe_points) == len(y.keyframe_points) and len(x.keyframe_points) == len(z.keyframe_points), "TODO: Handle different number of keyframes for each axis"

    transform_mat = calculate_bone_space_transform_matrix(old_pose_bone, new_pose_bone)

    for x_kfp, y_kfp, z_kfp in zip(x.keyframe_points, y.keyframe_points, z.keyframe_points):
        x_co, y_co, z_co = x_kfp.co, y_kfp.co, z_kfp.co
        assert x_co[0] == y_co[0] and x_co[0] == z_co[0], "TODO: Handle different keyframe times"

        old_vec = Vector((x_co[1], y_co[1], z_co[1]))
        new_vec = transform_mat @ old_vec
        x_co[1], y_co[1], z_co[1] = new_vec[0], new_vec[1], new_vec[2]

        x_kfp.co, y_kfp.co, z_kfp.co = x_co, y_co, z_co

    x.update()
    y.update()
    z.update()


def transform_bone_rotation_quaternion_space(fcurves, old_pose_bone, new_pose_bone):
    """
    Converts the quaternion F-curves from the old pose bone's space to the new pose bone's space.
    Either bone can be None, meaning convert from/to the original local space (as stored in the animation channels).
    """
    w = fcurves[0]
    x = fcurves[1]
    y = fcurves[2]
    z = fcurves[3]

    if w is None:
        return

    assert len(x.keyframe_points) == len(y.keyframe_points) and len(x.keyframe_points) == len(z.keyframe_points) and len(x.keyframe_points) == len(w.keyframe_points), "TODO: Handle different number of keyframes for each axis"

    transform_mat = calculate_bone_space_transform_matrix(old_pose_bone, new_pose_bone)

    prev_quat = None
    for w_kfp, x_kfp, y_kfp, z_kfp in zip(w.keyframe_points, x.keyframe_points, y.keyframe_points, z.keyframe_points):
        w_co, x_co, y_co, z_co = w_kfp.co, x_kfp.co, y_kfp.co, z_kfp.co
        assert x_co[0] == y_co[0] and x_co[0] == z_co[0] and x_co[0] == w_co[0], "TODO: Handle different keyframe times"

        quat = Quaternion((w_co[1], x_co[1], y_co[1], z_co[1]))
        quat.rotate(transform_mat)
        if prev_quat is not None and prev_quat.dot(quat) < 0:
            # Blender interpolates quaternions linearly and component-wise which can cause flickering
            # when there is a sign change. See longer rant in ycdexport.py
            quat *= -1

        w_co[1], x_co[1], y_co[1], z_co[1] = quat[0], quat[1], quat[2], quat[3]

        w_kfp.co, x_kfp.co, y_kfp.co, z_kfp.co = w_co, x_co, y_co, z_co

        prev_quat = quat

    w.update()
    x.update()
    y.update()
    z.update()


def transform_camera_rotation_quaternion(fcurves, old_camera, new_camera):
    """
    Blender cameras aim down the -Z axis, but RAGE cameras aim down the +Y axis.
    Rotate the quaternion F-curves by 90 degrees around the X axis to compensate.
    """
    w = fcurves[0]
    x = fcurves[1]
    y = fcurves[2]
    z = fcurves[3]

    if w is None:
        return

    # changing between blender cameras or non-camera targets, doesn't need to be converted
    if (old_camera is not None and new_camera is not None) or (old_camera is None and new_camera is None):
        return

    assert len(x.keyframe_points) == len(y.keyframe_points) and len(x.keyframe_points) == len(z.keyframe_points) and len(x.keyframe_points) == len(w.keyframe_points), "TODO: Handle different number of keyframes for each axis"

    # if new camera is None, we convert from Blender to RAGE; otherwise from RAGE to Blender
    angle_delta = math.radians(-90.0 if new_camera is None else 90.0)
    x_axis = Vector((1.0, 0.0, 0.0))

    prev_quat = None
    for w_kfp, x_kfp, y_kfp, z_kfp in zip(w.keyframe_points, x.keyframe_points, y.keyframe_points, z.keyframe_points):
        w_co, x_co, y_co, z_co = w_kfp.co, x_kfp.co, y_kfp.co, z_kfp.co
        assert x_co[0] == y_co[0] and x_co[0] == z_co[0] and x_co[0] == w_co[0], "TODO: Handle different keyframe times"

        quat = Quaternion((w_co[1], x_co[1], y_co[1], z_co[1]))
        x_axis_local = quat @ x_axis
        quat.rotate(Quaternion(x_axis_local, angle_delta))
        if prev_quat is not None and prev_quat.dot(quat) < 0:
            # Blender interpolates quaternions linearly and component-wise which can cause flickering
            # when there is a sign change. See longer rant in ycdexport.py
            quat *= -1

        w_co[1], x_co[1], y_co[1], z_co[1] = quat[0], quat[1], quat[2], quat[3]

        w_kfp.co, x_kfp.co, y_kfp.co, z_kfp.co = w_co, x_co, y_co, z_co

        prev_quat = quat

    w.update()
    x.update()
    y.update()
    z.update()


def add_driver_variable_obj_prop(fcurve, name, obj, obj_type, prop_data_path):
    var = fcurve.driver.variables.new()
    var.name = name
    var.type = "SINGLE_PROP"
    var_target = var.targets[0]
    var_target.id_type = obj_type
    var_target.id = obj
    var_target.data_path = prop_data_path
    return var


def setup_camera_for_animation(camera: bpy.types.Camera):
    camera_obj = get_data_obj(camera)
    camera_obj.rotation_mode = "QUATERNION"  # camera rotation track uses rotation_quaternion

    # connect camera_fov track to blender camera
    # NOTE: seems to report a dependency cycle, but works fine, blender bug?
    camera.driver_remove("lens")
    fcurve_lens = camera.driver_add("lens")
    add_driver_variable_obj_prop(fcurve_lens, "fov", camera_obj, "OBJECT", "animation_tracks.camera_fov")
    add_driver_variable_obj_prop(fcurve_lens, "sensor", camera, "CAMERA", "sensor_width")
    fcurve_lens.driver.expression = "(sensor * 0.5) / tan(radians(fov) * 0.5)"
    fcurve_lens.update()


def add_global_anim_uv_drivers(material, x_dot_node, y_dot_node):
    def _add_driver(dot_node, track):
        vec_input = dot_node.inputs[1]
        vec_input.driver_remove("default_value")
        fcurves = vec_input.driver_add("default_value")
        components = ["x", "y", "z"]
        for i in range(3):
            fcurve = fcurves[i]
            comp = components[i]
            add_driver_variable_obj_prop(fcurve, comp, material, "MATERIAL", f"animation_tracks.{track}.{comp}")
            fcurve.driver.expression = comp
            fcurve.update()

    _add_driver(x_dot_node, "uv0")
    _add_driver(y_dot_node, "uv1")


def add_global_anim_uv_nodes(material: bpy.types.Materia):
    # TODO: don't create more nodes if they already exist
    tree = material.node_tree
    nodes = tree.nodes
    base_tex_node = None
    for node in nodes:
        if node.type == "BSDF_PRINCIPLED":
            base_tex_node = node.inputs[0].links[0].from_node
            break

    if base_tex_node is None:
        raise Exception("Could not find base texture node")

    # operation to perform:
    #   vec uv = ...
    #   vec uvw = vec(uv, 1);
    #   uv.x = dot(uvw, globalAnimUV0.xyz);
    #   uv.y = dot(uvw, globalAnimUV1.xyz);
    uv = nodes.new("ShaderNodeUVMap")
    flip_v_subtract = nodes.new("ShaderNodeMath")
    flip_v_subtract.operation = "SUBTRACT"
    flip_v_subtract.inputs[1].default_value = 1.0
    flip_v_multiply = nodes.new("ShaderNodeMath")
    flip_v_multiply.operation = "MULTIPLY"
    flip_v_multiply.inputs[1].default_value = -1.0
    separate_uv = nodes.new("ShaderNodeSeparateXYZ")
    combine_augmented_uv = nodes.new("ShaderNodeCombineXYZ")
    combine_augmented_uv.inputs["Z"].default_value = 1.0
    x_dot = nodes.new("ShaderNodeVectorMath")
    x_dot.operation = "DOT_PRODUCT"
    y_dot = nodes.new("ShaderNodeVectorMath")
    y_dot.operation = "DOT_PRODUCT"
    flip_v_back_subtract = nodes.new("ShaderNodeMath")
    flip_v_back_subtract.operation = "SUBTRACT"
    flip_v_back_subtract.inputs[1].default_value = 1.0
    flip_v_back_multiply = nodes.new("ShaderNodeMath")
    flip_v_back_multiply.operation = "MULTIPLY"
    flip_v_back_multiply.inputs[1].default_value = -1.0
    combine_new_uv = nodes.new("ShaderNodeCombineXYZ")
    combine_new_uv.inputs["Z"].default_value = 0.0

    tree.links.new(separate_uv.inputs["Vector"], uv.outputs["UV"])
    tree.links.new(flip_v_subtract.inputs[0], separate_uv.outputs["Y"])
    tree.links.new(flip_v_multiply.inputs[0], flip_v_subtract.outputs[0])
    tree.links.new(combine_augmented_uv.inputs["X"], separate_uv.outputs["X"])
    tree.links.new(combine_augmented_uv.inputs["Y"], flip_v_multiply.outputs[0])

    tree.links.new(x_dot.inputs[0], combine_augmented_uv.outputs[0])
    tree.links.new(y_dot.inputs[0], combine_augmented_uv.outputs[0])

    tree.links.new(flip_v_back_subtract.inputs[0], y_dot.outputs["Value"])
    tree.links.new(flip_v_back_multiply.inputs[0], flip_v_back_subtract.outputs[0])
    tree.links.new(combine_new_uv.inputs["X"], x_dot.outputs["Value"])
    tree.links.new(combine_new_uv.inputs["Y"], flip_v_back_multiply.outputs[0])

    tree.links.new(base_tex_node.inputs["Vector"], combine_new_uv.outputs[0])

    add_global_anim_uv_drivers(material, x_dot, y_dot)


def setup_material_for_animation(material: bpy.types.Material):
    if material.sollum_type == MaterialType.NONE:
        raise Exception("Material is not a Sollumz material")

    # nothing to do, now the nodes are added when creating the material
    # add_global_anim_uv_nodes(material)


def setup_armature_for_animation(armature: bpy.types.Armature):
    armature_obj = get_data_obj(armature)
    armature_obj.rotation_mode = "QUATERNION"  # root rotation track uses rotation_quaternion


def get_canonical_track_data_path(track: Track, bone_id: int):
    """
    Gets a data path for an animation track independent of the target object.
    It has the form: 'pose.bones["#{bone_id}"].{track_property_name}'
    """
    base = f'pose.bones["#{bone_id}"].'

    if track == Track.BonePosition:
        return f'{base}location'
    elif track == Track.BoneRotation:
        return f'{base}rotation_quaternion'
    elif track == Track.BoneScale:
        return f'{base}scale'
    else:
        return f'{base}animation_tracks_{TrackToPropertyNameMap[track]}'


def track_data_path_to_canonical_form(data_path: str, target_id: bpy.types.ID, target_bone_name_map):
    is_armature = isinstance(target_id, bpy.types.Armature) or target_id is None
    is_camera = isinstance(target_id, bpy.types.Camera) or target_id is None
    is_material = isinstance(target_id, bpy.types.Material) or target_id is None

    if data_path == "delta_location":
        data_path = 'pose.bones["#0"].animation_tracks_mover_location'
    elif data_path == "delta_rotation_quaternion":
        data_path = 'pose.bones["#0"].animation_tracks_mover_rotation'
    elif is_camera and data_path == "location":
        data_path = 'pose.bones["#0"].animation_tracks_camera_location'
    elif is_camera and data_path == "rotation_quaternion":
        data_path = 'pose.bones["#0"].animation_tracks_camera_rotation'
    elif is_camera and data_path.startswith("animation_tracks.camera_"):
        data_path = data_path.replace("animation_tracks.", 'pose.bones["#0"].animation_tracks_')
    elif is_material and data_path.startswith("animation_tracks.uv"):
        data_path = data_path.replace("animation_tracks.", 'pose.bones["#0"].animation_tracks_')
    elif is_armature and data_path.startswith('pose.bones["'):  # bone properties
        data_path_parts = data_path.split('"')
        bone_name = data_path_parts[1]
        if bone_name.startswith("#"):
            pass  # already a bone ID (canonical form)
        else:
            assert target_bone_name_map is not None, "The armature bone-map is required at this point"
            bone_id = target_bone_name_map[bone_name]
            data_path_parts[1] = f"#{bone_id}"
            data_path = '"'.join(data_path_parts)

    return data_path


def track_data_path_to_target_form(data_path: str, target_id: bpy.types.ID, target_bone_map):
    """
    Converts a data path from the canonical form to the target form, data path specific to the target.
    For example, inserting the bone name into the data path with armature targets.
    `data_path` is expected to be in the canonical form.
    """
    if target_id is None:
        return data_path

    is_armature = isinstance(target_id, bpy.types.Armature)
    is_camera = isinstance(target_id, bpy.types.Camera)
    is_material = isinstance(target_id, bpy.types.Material)

    if data_path == 'pose.bones["#0"].animation_tracks_mover_location':
        data_path = "delta_location"
    elif data_path == 'pose.bones["#0"].animation_tracks_mover_rotation':
        data_path = "delta_rotation_quaternion"
    elif is_camera and data_path.startswith('pose.bones["#0"].animation_tracks_camera_'):  # camera properties
        # modify the actual camera object instead of a pose bone
        data_path = data_path.replace('pose.bones["#0"].animation_tracks_', "animation_tracks.")
        if data_path == "animation_tracks.camera_location":
            data_path = "location"  # use the object location property
        elif data_path == "animation_tracks.camera_rotation":
            data_path = "rotation_quaternion"  # use the object rotation property
    elif is_material and data_path.startswith('pose.bones["#0"].animation_tracks_uv'):  # uv properties
        # modify the actual drawable geometry object instead of a pose bone
        data_path = data_path.replace('pose.bones["#0"].animation_tracks_', "animation_tracks.")
    elif is_armature and data_path.startswith('pose.bones["'):  # bone properties
        # insert bone names in data paths
        data_path_parts = data_path.split('"')
        bone_id = data_path_parts[1]
        if bone_id.startswith("#"):
            bone_id = int(bone_id[1:])

        if target_bone_map is not None and bone_id in target_bone_map:
            new_bone_name = target_bone_map[bone_id].name
            data_path_parts[1] = new_bone_name
            data_path = '"'.join(data_path_parts)

    return data_path


def get_id_and_track_from_track_data_path(
        data_path: str, target_id: bpy.types.ID, target_bone_name_map
) -> Tuple[int, Track] | None:
    """Gets the bone ID and track from a data path."""
    canon_data_path = track_data_path_to_canonical_form(data_path, target_id, target_bone_name_map)
    canon_data_path_parts = canon_data_path.split('"')
    if len(canon_data_path_parts) != 3:
        return None

    id = int(canon_data_path_parts[1].removeprefix("#"))

    track_str = canon_data_path_parts[2].removeprefix("].")
    if track_str == "location":
        track = Track.BonePosition
    elif track_str == "rotation_quaternion":
        track = Track.BoneRotation
    elif track_str == "scale":
        track = Track.BoneScale
    elif track_str.startswith("animation_tracks_uv_transforms["):  # special case for UV transforms collection
        track = Track.UVTransforms
    else:
        prop_name = track_str.removeprefix("animation_tracks_")
        track = PropertyNameToTrackMap.get(prop_name, None)
        if track is None:
            return None

    return id, track


def retarget_animation(animation_obj: bpy.types.Object, old_target_id: bpy.types.ID, new_target_id: bpy.types.ID):
    if isinstance(old_target_id, bpy.types.Armature):
        old_bone_map = build_bone_map(get_data_obj(old_target_id))
        old_bone_name_map = build_name_bone_map(get_data_obj(old_target_id))
    else:
        old_bone_map = None
        old_bone_name_map = None

    new_is_armature = isinstance(new_target_id, bpy.types.Armature)
    if new_is_armature:
        new_bone_map = build_bone_map(get_data_obj(new_target_id))
    else:
        new_bone_map = None

    new_is_camera = isinstance(new_target_id, bpy.types.Camera)
    new_is_material = isinstance(new_target_id, bpy.types.Material)

    # bone_id -> [fcurves]
    bone_locations_to_transform = {}
    bone_rotations_to_transform = {}
    camera_rotations_to_transform = {}

    action = animation_obj.animation_properties.action
    for fcurve in action.fcurves:
        # TODO: can we somehow store the track ID in the F-Curve to avoid parsing the data paths?
        data_path = fcurve.data_path

        canon_data_path = track_data_path_to_canonical_form(data_path, old_target_id, old_bone_name_map)

        data_path = track_data_path_to_target_form(canon_data_path, new_target_id, new_bone_map)

        # check if track needs to be transformed
        data_path_parts = canon_data_path.split('"')
        bone_id = data_path_parts[1]
        if bone_id.startswith("#"):
            bone_id = int(bone_id[1:])
        prop_path = data_path_parts[2]
        if prop_path == "].location":
            if bone_id not in bone_locations_to_transform:
                bone_locations_to_transform[bone_id] = [None, None, None]
            bone_locations_to_transform[bone_id][fcurve.array_index] = fcurve
        elif prop_path == "].rotation_quaternion":  # TODO: Handle rotation_euler
            if bone_id not in bone_rotations_to_transform:
                bone_rotations_to_transform[bone_id] = [None, None, None, None]
            bone_rotations_to_transform[bone_id][fcurve.array_index] = fcurve
        elif prop_path == "].animation_tracks_camera_rotation":
            if bone_id not in camera_rotations_to_transform:
                camera_rotations_to_transform[bone_id] = [None, None, None, None]
            camera_rotations_to_transform[bone_id][fcurve.array_index] = fcurve

        # print(f"<{fcurve.data_path}> -> <{data_path}>")
        fcurve.data_path = data_path

    # perform required transformations
    for bone_id, fcurves in bone_locations_to_transform.items():
        old_bone = old_bone_map.get(bone_id, None) if old_bone_map is not None else None
        new_bone = new_bone_map.get(bone_id, None) if new_bone_map is not None else None
        transform_bone_location_space(fcurves, old_bone, new_bone)

    for bone_id, fcurves in bone_rotations_to_transform.items():
        old_bone = old_bone_map.get(bone_id, None) if old_bone_map is not None else None
        new_bone = new_bone_map.get(bone_id, None) if new_bone_map is not None else None
        transform_bone_rotation_quaternion_space(fcurves, old_bone, new_bone)

    for bone_id, fcurves in camera_rotations_to_transform.items():
        old_camera = old_target_id if isinstance(old_target_id, bpy.types.Camera) else None
        new_camera = new_target_id if isinstance(new_target_id, bpy.types.Camera) else None
        transform_camera_rotation_quaternion(fcurves, old_camera, new_camera)

    if new_is_armature:
        setup_armature_for_animation(new_target_id)

    if new_is_camera:
        setup_camera_for_animation(new_target_id)

    if new_is_material:
        setup_material_for_animation(new_target_id)


def get_frame_range_and_count(action: bpy.types.Action) -> Tuple[Vector, int]:
    frame_range = action.frame_range
    frame_count = math.ceil(frame_range[1] - frame_range[0] + 1)
    return frame_range, frame_count


def get_target_from_id(target_id: bpy.types.ID) -> bpy.types.ID:
    """Returns the ID instance where the animation data should be created to play the animation."""
    if target_id is None:
        return None

    if isinstance(target_id, bpy.types.Material):
        # for materials the animation (UV anim) is stored in the material data block itself because
        # there can be multiple materials with a single parent object, so animations would conflict
        return target_id

    # for armatures and cameras the animation is stored in the parent object, because:
    # - armature animations need to access pose bones and delta location/rotation
    # - camera animations need to access the camera location/rotation
    return get_data_obj(target_id)


def is_any_sollumz_animation_obj(obj: bpy.types.Object) -> bool:
    return obj.sollum_type in {SollumType.CLIP_DICTIONARY,
                               SollumType.ANIMATION,
                               SollumType.ANIMATIONS,
                               SollumType.CLIP,
                               SollumType.CLIPS}


def update_uv_clip_hash(clip_obj) -> bool:
    if len(clip_obj.clip_properties.animations) == 0:
        logger.error(f"Clip '{clip_obj.name}' has no animations.")
        return False

    animation_obj = clip_obj.clip_properties.animations[0].animation
    target = animation_obj.animation_properties.get_target()
    if not isinstance(target, bpy.types.Material):
        logger.error(f"Animation target is not a material.")
        return False

    meshes = [obj for obj in bpy.data.meshes if obj.user_of_id(target)]
    if len(meshes) == 0:
        logger.error(f"Material '{target.name}' is not used by any mesh.")
        return False
    elif len(meshes) > 1:
        logger.warning(f"Material is used by more than one mesh. '{meshes[0].name}' will be used.")

    mesh = meshes[0]
    drawable_models = [o for o in bpy.data.objects if o.sollum_type == SollumType.DRAWABLE_MODEL and o.data == mesh]
    if len(drawable_models) == 0:
        logger.error(f"Material '{target.name}' is not used by any drawable model.")
        return False
    elif len(drawable_models) > 1:
        logger.warning(f"Material is used by more than one drawable model. '{drawable_models[0].name}' will be used.")

    drawable_model = drawable_models[0]
    if drawable_model.parent is None:
        logger.error(f"Drawable model '{drawable_model.name}' has no parent.")
        return False

    parent = None
    temp_parent_obj = drawable_model
    while temp_parent_obj.parent:
        temp_parent_obj = temp_parent_obj.parent
        if temp_parent_obj.sollum_type == SollumType.DRAWABLE or temp_parent_obj.sollum_type == SollumType.FRAGMENT :
            parent = temp_parent_obj
        else:
            break

    model_name = parent.name
    material_index = target.shader_properties.index

    clip_hash = jenkhash.Generate(model_name) + (material_index + 1)
    clip_hash_str = f"hash_{clip_hash:08X}"

    clip_obj.clip_properties.hash = clip_hash_str
    return True


def is_uv_animation_supported(material: bpy.types.Material):
    shader = ShaderManager.find_shader(material.shader_properties.filename)
    return shader is not None and shader.is_uv_animation_supported
