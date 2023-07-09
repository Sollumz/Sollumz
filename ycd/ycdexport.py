import bpy
from mathutils import Vector, Matrix, Quaternion

from ..cwxml import clipsdictionary as ycdxml
from ..sollumz_properties import SollumType
from ..tools.jenkhash import Generate
from ..tools.blenderhelper import build_name_bone_map, build_bone_map, get_data_obj
from ..tools.animationhelper import (
    Track,
    TrackFormat,
    TrackFormatMap,
    AnimationFlag,
    evaluate_vector,
    evaluate_quaternion,
    evaluate_euler_to_quaternion,
    get_quantum_and_min_val,
    get_id_and_track_from_track_data_path,
)


def sequence_items_from_action(action: bpy.types.Action, target_id: bpy.types.ID, frame_count: int):
    if isinstance(target_id, bpy.types.Armature):
        bone_name_map = build_name_bone_map(get_data_obj(target_id))
    else:
        bone_name_map = None

    sequence_items = {}
    for fcurve in action.fcurves:
        data_path = fcurve.data_path
        bone_id, track = get_id_and_track_from_track_data_path(data_path, target_id, bone_name_map)
        comp_index = fcurve.array_index
        format = TrackFormatMap[track]

        if bone_id not in sequence_items:
            sequence_items[bone_id] = {}

        bone_sequences = sequence_items[bone_id]

        if track not in bone_sequences:
            if format == TrackFormat.Vector3:
                # TODO: defaults should be kept in-sync with the properties defaults in AnimationTracks, refactor this
                #  once we add more defaults to avoid duplication
                if track == Track.UV0:
                    default_vec = (1.0, 0.0, 0.0)
                elif track == Track.UV1:
                    default_vec = (0.0, 1.0, 0.0)
                else:
                    default_vec = (0.0, 0.0, 0.0)
                bone_sequences[track] = [Vector(default_vec) for _ in range(0, frame_count)]
            elif format == TrackFormat.Quaternion:
                bone_sequences[track] = [Quaternion((1.0, 0.0, 0.0, 0.0)) for _ in range(0, frame_count)]
            elif format == TrackFormat.Float:
                bone_sequences[track] = [0.0] * frame_count

        track_sequence = bone_sequences[track]
        for frame_id in range(0, frame_count):
            value = fcurve.evaluate(frame_id)
            if format == TrackFormat.Float:
                track_sequence[frame_id] = value
            else:
                track_sequence[frame_id][comp_index] = value

    # TODO: transform bone space and camera rotation

    return sequence_items

    if animation_type == "REGULAR":
        locations_map = {}
        rotations_map = {}
        scales_map = {}
        bones_map = action_data

        p_bone: bpy.types.PoseBone
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
                Track.BonePosition, action_type)] = locations_map

        if len(rotations_map) > 0:
            sequence_items[ensure_action_track(
                Track.BoneRotation, action_type)] = rotations_map

        if len(scales_map) > 0:
            sequence_items[ensure_action_track(
                Track.BoneScale, action_type)] = scales_map

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
                    Track.UV0, action_type)] = u_locations_map

            if len(v_locations_map) > 0:
                sequence_items[ensure_action_track(
                    Track.UV1, action_type)] = v_locations_map


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


def sequence_data_from_frames_data(track, frames_data):
    sequence_data = ycdxml.Animation.SequenceDataList.SequenceData()

    format = TrackFormatMap[track]

    if format == TrackFormat.Vector3:
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
            sequence_data.channels.append(build_values_channel(values_x, uniq_x))
            sequence_data.channels.append(build_values_channel(values_y, uniq_y))
            sequence_data.channels.append(build_values_channel(values_z, uniq_z))
    elif format == TrackFormat.Quaternion:
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
            sequence_data.channels.append(build_values_channel(values_x, uniq_x))
            sequence_data.channels.append(build_values_channel(values_y, uniq_y))
            sequence_data.channels.append(build_values_channel(values_z, uniq_z))
            sequence_data.channels.append(build_values_channel(values_w, uniq_w))
    elif format == TrackFormat.Float:
        values = frames_data

        uniq = list(set(values))
        len_uniq = len(uniq)

        if len_uniq == 1:
            channel = ycdxml.ChannelsList.StaticVector3()
            channel.value = frames_data[0]

            sequence_data.channels.append(channel)
        else:
            sequence_data.channels.append(build_values_channel(values, uniq))

    return sequence_data


def animation_from_object(animation_obj):
    animation = ycdxml.Animation()

    animation_properties = animation_obj.animation_properties
    frame_count = animation_properties.frame_count

    animation.hash = animation_properties.hash
    animation.frame_count = frame_count
    animation.sequence_frame_limit = frame_count + 30
    animation.duration = (frame_count - 1) / bpy.context.scene.render.fps
    animation.unknown10 = AnimationFlag.Default

    # signature: this value must be unique (used internally for animation caching)
    # TODO: CW should calculate this on import with the proper hash function
    animation.unknown1C = "hash_" + hex(Generate(animation_properties.hash) + 1)[2:].zfill(8)

    action = animation_properties.action
    target_id = animation_properties.target_id
    sequence_items = sequence_items_from_action(action, target_id, frame_count)

    sequence = ycdxml.Animation.SequenceList.Sequence()
    sequence.frame_count = frame_count
    sequence.hash = "hash_" + hex(0)[2:].zfill(8)

    for bone_id, bones_data in sorted(sequence_items.items()):
        for track, frames_data in sorted(bones_data.items()):
            if track == Track.MoverPosition or track == Track.MoverRotation:
                animation.unknown10 |= AnimationFlag.RootMotion

            sequence_data = sequence_data_from_frames_data(track, frames_data)

            seq_bone_id = ycdxml.Animation.BoneIdList.BoneId()
            seq_bone_id.bone_id = bone_id
            seq_bone_id.track = track.value
            seq_bone_id.format = TrackFormatMap[track].value
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
        clip.start_time = (clip_animation_property.start_frame / animation_properties.frame_count) * animation_duration
        clip.end_time = (clip_animation_property.end_frame / animation_properties.frame_count) * animation_duration

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

    # TODO: add tags

    return clip


def clip_dictionary_from_object(obj):
    clip_dictionary = ycdxml.ClipsDictionary()

    animations_obj = None
    clips_obj = None

    for child_obj in obj.children:
        if child_obj.sollum_type == SollumType.ANIMATIONS:
            animations_obj = child_obj
        elif child_obj.sollum_type == SollumType.CLIPS:
            clips_obj = child_obj

    for animation_obj in animations_obj.children:
        animation = animation_from_object(animation_obj)

        clip_dictionary.animations.append(animation)

    for clip_obj in clips_obj.children:
        clip = clip_from_object(clip_obj)

        clip_dictionary.clips.append(clip)

    return clip_dictionary


def export_ycd(obj, filepath):
    clip_dictionary_from_object(obj).write_xml(filepath)
