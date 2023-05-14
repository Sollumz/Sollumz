import bpy
from bpy.types import PoseBone
from mathutils import Vector, Matrix, Quaternion

from ..cwxml import clipsdictionary as ycdxml
from ..sollumz_properties import SollumType
from ..tools.jenkhash import Generate
from ..tools.blenderhelper import build_name_bone_map, build_bone_map, get_armature_obj
from ..tools.animationhelper import (
    TrackType,
    ActionType,
    AnimationFlag,
    evaluate_vector,
    evaluate_quaternion,
    evaluate_euler_to_quaternion,
    get_quantum_and_min_val,
    is_ped_bone_tag,
    TrackTypeValueMap,
)


def get_name(item):
    return item.name.split(".")[0]


def ensure_action_track(track_type: TrackType, action_type: ActionType):
    if action_type is ActionType.RootMotion:
        if track_type is TrackType.BonePosition:
            return TrackType.RootMotionPosition
        if track_type is TrackType.BoneRotation:
            return TrackType.RootMotionRotation
    elif action_type is ActionType.Base:
        if track_type is TrackType.UV0:
            return TrackType.UV0
        if track_type is TrackType.UV1:
            return TrackType.UV1

    return track_type


def sequence_items_from_action(action, sequence_items, action_data, action_type, frame_count, animation_type):
    if animation_type == "REGULAR":
        locations_map = {}
        rotations_map = {}
        scales_map = {}
        bones_map = action_data

        p_bone: PoseBone
        for parent_tag, p_bone in bones_map.items():
            pos_vector_path = p_bone.path_from_id("location")
            rot_quaternion_path = p_bone.path_from_id("rotation_quaternion")
            rot_euler_path = p_bone.path_from_id("rotation_euler")
            scale_vector_path = p_bone.path_from_id("scale")

            # Get list of per-frame data for every path

            b_locations = evaluate_vector(
                action.fcurves, pos_vector_path, frame_count)
            b_quaternions = evaluate_quaternion(
                action.fcurves, rot_quaternion_path, frame_count)
            b_euler_quaternions = evaluate_euler_to_quaternion(
                action.fcurves, rot_euler_path, frame_count)
            b_scales = evaluate_vector(
                action.fcurves, scale_vector_path, frame_count)

            # Link them with Bone ID

            if len(b_locations) > 0:
                locations_map[parent_tag] = b_locations

            # Its a bit of a edge case scenario because blender uses either
            # euler or quaternion (I cant really understand why quaternion doesnt update with euler)
            # So we will prefer quaternion over euler for now
            # TODO: Theres also third rotation in blender, angles or something...
            if len(b_quaternions) > 0:
                rotations_map[parent_tag] = b_quaternions
            elif len(b_euler_quaternions) > 0:
                rotations_map[parent_tag] = b_euler_quaternions

            if len(b_scales) > 0:
                scales_map[parent_tag] = b_scales

        # Transform position from local to armature space
        for parent_tag, positions in locations_map.items():
            p_bone = bones_map[parent_tag]
            bone = p_bone.bone

            for frame_id, position in enumerate(positions):
                mat = bone.matrix_local

                if bone.parent is not None:
                    mat = bone.parent.matrix_local.inverted() @ bone.matrix_local

                    mat_decomposed = mat.decompose()

                    bone_location = mat_decomposed[0]
                    bone_rotation = mat_decomposed[1]

                    position.rotate(bone_rotation)

                    diff_location = Vector((
                        (position.x + bone_location.x),
                        (position.y + bone_location.y),
                        (position.z + bone_location.z),
                    ))

                    positions[frame_id] = diff_location

        # Transform rotation from local to armature space
        for parent_tag, quaternions in rotations_map.items():
            p_bone = bones_map[parent_tag]
            bone = p_bone.bone

            prev_quaternion = None
            for quaternion in quaternions:
                if p_bone.parent is not None:
                    pose_rot = Matrix.to_quaternion(bone.matrix)
                    quaternion.rotate(pose_rot)

                if prev_quaternion is not None:
                    # "Flickering bug" fix - killso:
                    # This bug is caused by interpolation algorithm used in GTA
                    # which is not slerp, but straight interpolation of every value
                    # and this leads to incorrect results in cases if dot(this, next) < 0
                    # This is correct "Quaternion Lerp" algorithm:
                    # if (Dot(start, end) >= 0f)
                    # {
                    #   result.X = (1 - amount) * start.X + amount * end.X
                    #   ...
                    # }
                    # else
                    # {
                    #   result.X = (1 - amount) * start.X - amount * end.X
                    #   ...
                    # }
                    # (Statement difference is only substracting instead of adding)
                    # But GTA algorithm doesn't have Dot check,
                    # resulting all values that are not passing this statement to "lag" in game.
                    # (because of incorrect interpolation direction)
                    # So what we do is make all values to pass Dot(start, end) >= 0f statement
                    if Quaternion.dot(prev_quaternion, quaternion) < 0:
                        quaternion *= -1

                prev_quaternion = quaternion
        # WARNING: ANY OPERATION WITH ROTATION WILL CAUSE SIGN CHANGE. PROCEED ANYTHING BEFORE FIX.

        if len(locations_map) > 0:
            sequence_items[ensure_action_track(
                TrackType.BonePosition, action_type)] = locations_map

        if len(rotations_map) > 0:
            sequence_items[ensure_action_track(
                TrackType.BoneRotation, action_type)] = rotations_map

        if len(scales_map) > 0:
            sequence_items[ensure_action_track(
                TrackType.BoneScale, action_type)] = scales_map

    elif animation_type == "UV":
        u_locations_map = {}
        v_locations_map = {}
        uv_mat = action
        uv_nodetree = uv_mat.node_tree
        mat_nodes = uv_nodetree.nodes
        vector_math_node = None

        # Verify if material has required node(Vector Math) to get animation data
        for node in mat_nodes:
            if node.type == 'VECT_MATH':
                vector_math_node = node
                break
        if vector_math_node is None:
            raise Exception(
                "Unable to find Vector Math node in material to get UV animation data!")
        else:
            pos_vector_path = vector_math_node.inputs[1].path_from_id(
                "default_value")
            uv_fcurve = uv_nodetree.animation_data.action.fcurves
            uv_locations = evaluate_vector(
                uv_fcurve, pos_vector_path, frame_count)
            if len(uv_locations) > 0:
                u_channel_loc = []
                v_channel_loc = []
                for vector in uv_locations:
                    u_channel_loc.append(round(vector.x, 4))
                    v_channel_loc.append(-round(vector.y, 4))

                if len(u_channel_loc) > 0:
                    u_locations_map[0] = u_channel_loc

                if len(v_channel_loc) > 0:
                    v_locations_map[0] = v_channel_loc

            if len(u_locations_map) > 0:
                sequence_items[ensure_action_track(
                    TrackType.UV0, action_type)] = u_locations_map

            if len(v_locations_map) > 0:
                sequence_items[ensure_action_track(
                    TrackType.UV1, action_type)] = v_locations_map


def build_values_channel(values, uniq_values, indirect_percentage=0.1):
    values_len_percentage = len(uniq_values) / len(values)

    if len(uniq_values) == 1:
        channel = ycdxml.ChannelsList.StaticFloat()

        channel.value = uniq_values[0]
    elif values_len_percentage <= indirect_percentage:
        channel = ycdxml.ChannelsList.IndirectQuantizeFloat()

        min_value, quantum = get_quantum_and_min_val(uniq_values)

        channel.values = uniq_values
        channel.offset = min_value
        channel.quantum = quantum

        for value in values:
            channel.frames.append(uniq_values.index(value))
    else:
        channel = ycdxml.ChannelsList.QuantizeFloat()

        min_value, quantum = get_quantum_and_min_val(values)

        channel.values = values
        channel.offset = min_value
        channel.quantum = quantum

    return channel


def sequence_item_from_frames_data(track, frames_data):
    sequence_data = ycdxml.Animation.SequenceDataList.SequenceData()

    # TODO: Would be good to put this in enum

    # Location, Scale, RootMotion Position
    if track == 0 or track == 2 or track == 5:
        values_x = []
        values_y = []
        values_z = []

        for vector in frames_data:
            values_x.append(vector.x)
            values_y.append(vector.y)
            values_z.append(vector.z)

        uniq_x = list(set(values_x))
        len_uniq_x = len(uniq_x)

        uniq_y = list(set(values_y))
        len_uniq_y = len(uniq_y)

        uniq_z = list(set(values_z))
        len_uniq_z = len(uniq_z)

        if len_uniq_x == 1 and len_uniq_y == 1 and len_uniq_z == 1:
            channel = ycdxml.ChannelsList.StaticVector3()
            channel.value = frames_data[0]

            sequence_data.channels.append(channel)
        else:
            sequence_data.channels.append(
                build_values_channel(values_x, uniq_x))
            sequence_data.channels.append(
                build_values_channel(values_y, uniq_y))
            sequence_data.channels.append(
                build_values_channel(values_z, uniq_z))
    # Rotation, RootMotion Rotation
    elif track == 1 or track == 6:
        values_x = []
        values_y = []
        values_z = []
        values_w = []

        for vector in frames_data:
            values_x.append(vector.x)
            values_y.append(vector.y)
            values_z.append(vector.z)
            values_w.append(vector.w)

        uniq_x = list(set(values_x))
        len_uniq_x = len(uniq_x)

        uniq_y = list(set(values_y))
        len_uniq_y = len(uniq_y)

        uniq_z = list(set(values_z))
        len_uniq_z = len(uniq_z)

        uniq_w = list(set(values_w))
        len_uniq_w = len(uniq_w)

        if len_uniq_x == 1 and len_uniq_y == 1 and len_uniq_z == 1 and len_uniq_w == 1:
            channel = ycdxml.ChannelsList.StaticQuaternion()
            channel.value = frames_data[0]

            sequence_data.channels.append(channel)
        else:
            sequence_data.channels.append(
                build_values_channel(values_x, uniq_x))
            sequence_data.channels.append(
                build_values_channel(values_y, uniq_y))
            sequence_data.channels.append(
                build_values_channel(values_z, uniq_z))
            sequence_data.channels.append(
                build_values_channel(values_w, uniq_w))

    # UV0/U or UV1/V
    elif track == 17 or track == 18:
        len_uniq_uv = len(frames_data)

        if len_uniq_uv == 1:
            channel = ycdxml.ChannelsList.StaticVector3()
            channel.value = frames_data[0]

            sequence_data.channels.append(channel)
        else:
            channel1 = ycdxml.ChannelsList.StaticFloat()
            channel2 = ycdxml.ChannelsList.StaticFloat()
            if track == 17:
                channel1.value = 1
                channel2.value = 0
            elif track == 18:
                channel1.value = 0
                channel2.value = 1
            sequence_data.channels.append(channel1)
            sequence_data.channels.append(channel2)
            # Main channel item which contains frame data
            sequence_data.channels.append(
                build_values_channel(frames_data, list(set(frames_data))))

    return sequence_data


def animation_from_object(animation_obj, bones_name_map, bones_map, is_ped_animation, animation_type):
    animation = ycdxml.Animation()

    animation_properties = animation_obj.animation_properties
    frame_count = animation_properties.frame_count

    animation.hash = animation_properties.hash
    animation.frame_count = frame_count
    animation.sequence_frame_limit = frame_count + 30
    animation.duration = (frame_count - 1) / bpy.context.scene.render.fps
    animation.unknown10 = AnimationFlag.Default

    # This value must be unique (Looks like its used internally for animation caching)
    animation.unknown1C = "hash_" + \
        hex(Generate(animation_properties.hash) + 1)[2:].zfill(8)

    sequence_items = {}
    if animation_type == "REGULAR":
        if animation_properties.base_action:
            action = animation_properties.base_action
            action_type = ActionType.Base
            sequence_items_from_action(
                action, sequence_items, bones_map, action_type, frame_count, animation_type)

        if animation_properties.root_motion_location_action:
            action = animation_properties.root_motion_location_action
            action_type = ActionType.RootMotion

            animation.unknown10 |= AnimationFlag.RootMotion
            sequence_items_from_action(
                action, sequence_items, bones_map, action_type, frame_count, animation_type)

        # TODO: Figure out root motion rotation
        # if animation_properties.root_motion_rotation_action:
            # action = animation_properties.root_motion_rotation_action
            # action_type = ActionType.RootMotion

            # animation.unknown10 |= AnimationFlag.RootMotion
            # sequence_items_from_action(
            #     action, sequence_items, bones_map, action_type, frames_count, animation_type)
    elif animation_type == "UV":
        action_material = animation_obj.uv_anim_materials.material
        action_type = ActionType.Base
        sequence_items_from_action(
            action_material, sequence_items, animation_obj, action_type, frame_count, animation_type)

    sequence = ycdxml.Animation.SequenceList.Sequence()
    sequence.frame_count = frame_count
    sequence.hash = "hash_" + hex(0)[2:].zfill(8)

    for track, bones_data in sorted(sequence_items.items()):
        for bone_id, frames_data in sorted(bones_data.items()):
            sequence_data = sequence_item_from_frames_data(track, frames_data)

            seq_bone_id = ycdxml.Animation.BoneIdList.BoneId()
            seq_bone_id.bone_id = bone_id
            seq_bone_id.track = track.value
            seq_bone_id.unk0 = TrackTypeValueMap[track].value
            animation.bone_ids.append(seq_bone_id)

            sequence.sequence_data.append(sequence_data)

    animation.sequences.append(sequence)

    # Get int value from enum, a bit junky...
    animation.unknown10 = animation.unknown10.value

    return animation


def clip_from_object(clip_obj):
    clip_properties = clip_obj.clip_properties

    is_single_animation = len(clip_properties.animations) == 1

    if is_single_animation:
        clip = ycdxml.ClipsList.ClipAnimation()
        clip_animation_property = clip_properties.animations[0]
        animation_properties = clip_animation_property.animation.animation_properties

        animation_duration = animation_properties.frame_count / bpy.context.scene.render.fps

        clip.animation_hash = animation_properties.hash
        clip.start_time = (clip_animation_property.start_frame /
                           animation_properties.frame_count) * animation_duration
        clip.end_time = (clip_animation_property.end_frame /
                         animation_properties.frame_count) * animation_duration

        clip_animation_duration = clip.end_time - clip.start_time
        clip.rate = clip_animation_duration / clip_properties.duration
    else:
        clip = ycdxml.ClipsList.ClipAnimationList()
        clip.duration = clip_properties.duration

        for clip_animation_property in clip_properties.animations:
            clip_animation = ycdxml.ClipAnimationsList.ClipAnimation()

            animation_properties = clip_animation_property.animation.animation_properties

            animation_duration = animation_properties.frame_count / bpy.context.scene.render.fps

            clip_animation.animation_hash = animation_properties.hash
            clip_animation.start_time = (
                clip_animation_property.start_frame / animation_properties.frame_count) * animation_duration
            clip_animation.end_time = (
                clip_animation_property.end_frame / animation_properties.frame_count) * animation_duration

            clip_animation_duration = clip_animation.end_time - clip_animation.start_time
            clip_animation.rate = clip_animation_duration / clip_properties.duration

            clip.animations.append(clip_animation)

    clip.hash = clip_properties.hash
    clip.name = "pack:/" + clip_properties.name
    clip.unknown30 = 0

    return clip


def clip_dictionary_from_object(obj):
    clip_dictionary = ycdxml.ClipsDictionary()

    armature = obj.clip_dict_properties.armature
    uv_prop = obj.clip_dict_properties.uv_obj

    if armature is not None and uv_prop is None:
        animation_type = "REGULAR"
        armature_obj = get_armature_obj(armature)
    elif armature is None and uv_prop is not None:
        animation_type = "UV"

    if animation_type is None:
        raise Exception("Invalid/unknown clip dictionary type")
    elif animation_type == "REGULAR":
        bones_name_map = build_name_bone_map(armature_obj)
        bones_map = build_bone_map(armature_obj)

        is_ped_animation = False

        for p_bone in armature_obj.pose.bones:
            if is_ped_bone_tag(p_bone.bone.bone_properties.tag):
                is_ped_animation = True
                break
    elif animation_type == "UV":
        bones_name_map = None
        bones_map = None
        is_ped_animation = False

    animations_obj = None
    clips_obj = None

    for child_obj in obj.children:
        if child_obj.sollum_type == SollumType.ANIMATIONS:
            animations_obj = child_obj
        elif child_obj.sollum_type == SollumType.CLIPS:
            clips_obj = child_obj

    for animation_obj in animations_obj.children:
        animation = animation_from_object(
            animation_obj, bones_name_map, bones_map, is_ped_animation, animation_type)

        clip_dictionary.animations.append(animation)

    for clip_obj in clips_obj.children:
        clip = clip_from_object(clip_obj)

        clip_dictionary.clips.append(clip)

    return clip_dictionary


def export_ycd(obj, filepath):
    clip_dictionary_from_object(obj).write_xml(filepath)
