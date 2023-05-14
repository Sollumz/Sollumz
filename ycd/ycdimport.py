import os
import bpy
from mathutils import Vector, Quaternion, Matrix
from ..cwxml.clipsdictionary import YCD
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.blenderhelper import build_bone_map, get_armature_obj
from ..tools.animationhelper import is_ped_bone_tag
from ..tools.utils import list_index_exists
from ..sollumz_preferences import get_import_settings
from .. import logger


def create_anim_obj(type):
    anim_obj = bpy.data.objects.new(SOLLUMZ_UI_NAMES[type], None)
    anim_obj.empty_display_size = 0
    anim_obj.sollum_type = type
    bpy.context.collection.objects.link(anim_obj)

    return anim_obj


def insert_action_data(actions_data, type, track, bone_name, data):
    if type not in actions_data:
        actions_data[type] = {}

    if track not in actions_data[type]:
        actions_data[type][track] = {}

    if bone_name not in actions_data[type][track]:
        actions_data[type][track][bone_name] = []

    actions_data[type][track][bone_name].append(data)


def get_values_from_sequence_data(sequence_data, frame_id):
    channel_values = []

    for i in range(len(sequence_data.channels)):
        while len(channel_values) <= i:
            channel_values.append(None)

        channel = sequence_data.channels[i]

        if channel is not None:
            channel_values[i] = channel.get_value(frame_id, channel_values)

    return channel_values


def get_location_from_sequence_data(sequence_data, frame_id, p_bone, is_convert_local_to_pose):
    channel_values = get_values_from_sequence_data(sequence_data, frame_id)

    if len(channel_values) == 1:
        location = channel_values[0]
    else:
        location = Vector([
            channel_values[0],
            channel_values[1],
            channel_values[2],
        ])

    if not is_convert_local_to_pose:
        return location

    mat = p_bone.bone.matrix_local

    if p_bone.bone.parent is not None:
        mat = p_bone.bone.parent.matrix_local.inverted() @ p_bone.bone.matrix_local

    mat_decomposed = mat.decompose()

    bone_location = mat_decomposed[0]
    bone_rotation = mat_decomposed[1]

    diff_location = Vector((
        (location.x - bone_location.x),
        (location.y - bone_location.y),
        (location.z - bone_location.z),
    ))

    diff_location.rotate(bone_rotation.inverted())

    return diff_location


def get_quaternion_from_sequence_data(sequence_data, frame_id, p_bone, is_convert_local_to_pose):
    channel_values = get_values_from_sequence_data(sequence_data, frame_id)

    if len(channel_values) == 1:
        rotation = channel_values[0]
    else:
        if len(sequence_data.channels) <= 4:
            for channel in sequence_data.channels:
                if channel.type == "CachedQuaternion1" or channel.type == "CachedQuaternion2":
                    cached_value = channel.get_value(frame_id, channel_values)

                    if channel.quat_index == 0:
                        channel_values = [
                            cached_value, channel_values[0], channel_values[1], channel_values[2]]
                    elif channel.quat_index == 1:
                        channel_values = [
                            channel_values[0], cached_value, channel_values[1], channel_values[2]]
                    elif channel.quat_index == 2:
                        channel_values = [
                            channel_values[0], channel_values[1], cached_value, channel_values[2]]
                    elif channel.quat_index == 3:
                        channel_values = [
                            channel_values[0], channel_values[1], channel_values[2], cached_value]

            if channel.type == "CachedQuaternion2":
                rotation = Quaternion(
                    (channel_values[0], channel_values[1], channel_values[2], channel_values[3]))
            else:
                rotation = Quaternion(
                    (channel_values[3], channel_values[0], channel_values[1], channel_values[2]))
        else:
            rotation = Quaternion(
                (channel_values[3], channel_values[0], channel_values[1], channel_values[2]))

    if is_convert_local_to_pose == True:
        if p_bone.parent is not None:
            pose_rot = Matrix.to_quaternion(p_bone.bone.matrix)
            return pose_rot.rotation_difference(rotation)

        return rotation
    else:
        return rotation


def combine_sequences_and_convert_to_groups(animation, armature, is_ped_animation):
    bone_map = build_bone_map(armature)

    sequence_frame_limit = animation.sequence_frame_limit

    if len(animation.sequences) <= 1:
        sequence_frame_limit = animation.frame_count + 30

    actions_data = {}

    for frame_id in range(0, animation.frame_count):
        sequence_index = int(frame_id / (sequence_frame_limit))
        sequence_frame = frame_id % (sequence_frame_limit)

        if sequence_index >= len(animation.sequences):
            sequence_index = len(animation.sequences) - 1

        sequence = animation.sequences[sequence_index]

        for sequence_data_index, sequence_data in enumerate(sequence.sequence_data):
            bone_data = animation.bone_ids[sequence_data_index]

            if bone_data is None or bone_data.bone_id not in bone_map:
                continue

            p_bone = bone_map[bone_data.bone_id]

            bone_name = p_bone.name

            if bone_data.track == 0:
                location = get_location_from_sequence_data(
                    sequence_data, sequence_frame, p_bone, True)
                insert_action_data(actions_data, "base",
                                   bone_data.track, bone_name, location)
            elif bone_data.track == 1:
                rotation = get_quaternion_from_sequence_data(
                    sequence_data, sequence_frame, p_bone, True)
                insert_action_data(actions_data, "base",
                                   bone_data.track, bone_name, rotation)
            elif bone_data.track == 2:
                scale = get_location_from_sequence_data(
                    sequence_data, sequence_frame, p_bone, False)
                insert_action_data(actions_data, "base",
                                   bone_data.track, bone_name, scale)
            elif bone_data.track == 5:
                location = get_location_from_sequence_data(
                    sequence_data, sequence_frame, p_bone, True)
                insert_action_data(
                    actions_data, "root_motion_location", bone_data.track, bone_name, location)
            elif bone_data.track == 6:
                rotation = get_quaternion_from_sequence_data(
                    sequence_data, sequence_frame, p_bone, False)
                insert_action_data(
                    actions_data, "root_motion_rotation", bone_data.track, bone_name, rotation)

    for type in actions_data:
        for track in actions_data[type]:
            if track == 1:
                bones_data = actions_data[type][track]

                if "SKEL_L_Thigh" in bones_data:
                    bones_data["RB_L_ThighRoll"] = list(
                        bones_data["SKEL_L_Thigh"])

                if "SKEL_R_Thigh" in bones_data:
                    bones_data["RB_R_ThighRoll"] = list(
                        bones_data["SKEL_R_Thigh"])

    return actions_data


def apply_action_data_to_action(action_data, action, frame_count):
    frames_ids = [*range(frame_count)]

    for track_id, bones_data in action_data.items():
        type = None

        if track_id == 0 or track_id == 5:
            type = "location"
        elif track_id == 1 or track_id == 6:
            type = "rotation"
        elif track_id == 2:
            type = "scale"

        for bone_name, frames_data in bones_data.items():
            group_item = action.groups.new('%s-%s' % (bone_name, track_id))

            if type == "location":
                data_path_loc = 'pose.bones["%s"].location' % bone_name

                location_tracks_x = list(
                    map(lambda location: location.x, frames_data))
                location_tracks_y = list(
                    map(lambda location: location.y, frames_data))
                location_tracks_z = list(
                    map(lambda location: location.z, frames_data))

                pos_curve_x = action.fcurves.new(
                    data_path=data_path_loc, index=0)
                pos_curve_y = action.fcurves.new(
                    data_path=data_path_loc, index=1)
                pos_curve_z = action.fcurves.new(
                    data_path=data_path_loc, index=2)

                pos_curve_x.group = group_item
                pos_curve_y.group = group_item
                pos_curve_z.group = group_item

                pos_curve_x.keyframe_points.add(len(frames_data))
                pos_curve_y.keyframe_points.add(len(frames_data))
                pos_curve_z.keyframe_points.add(len(frames_data))

                pos_curve_x.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, location_tracks_x) for x in co])
                pos_curve_y.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, location_tracks_y) for x in co])
                pos_curve_z.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, location_tracks_z) for x in co])

                pos_curve_x.update()
                pos_curve_y.update()
                pos_curve_z.update()
            elif type == "scale":
                data_path_loc = 'pose.bones["%s"].scale' % bone_name

                scale_tracks_x = list(
                    map(lambda location: location.x, frames_data))
                scale_tracks_y = list(
                    map(lambda location: location.y, frames_data))
                scale_tracks_z = list(
                    map(lambda location: location.z, frames_data))

                pos_curve_x = action.fcurves.new(
                    data_path=data_path_loc, index=0)
                pos_curve_y = action.fcurves.new(
                    data_path=data_path_loc, index=1)
                pos_curve_z = action.fcurves.new(
                    data_path=data_path_loc, index=2)

                pos_curve_x.group = group_item
                pos_curve_y.group = group_item
                pos_curve_z.group = group_item

                pos_curve_x.keyframe_points.add(len(frames_data))
                pos_curve_y.keyframe_points.add(len(frames_data))
                pos_curve_z.keyframe_points.add(len(frames_data))

                pos_curve_x.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, scale_tracks_x) for x in co])
                pos_curve_y.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, scale_tracks_y) for x in co])
                pos_curve_z.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, scale_tracks_z) for x in co])

                pos_curve_x.update()
                pos_curve_y.update()
                pos_curve_z.update()
            elif type == "rotation":
                data_path_rot = 'pose.bones["%s"].rotation_quaternion' % bone_name

                rotation_tracks_x = list(
                    map(lambda rotation: rotation.x, frames_data))
                rotation_tracks_y = list(
                    map(lambda rotation: rotation.y, frames_data))
                rotation_tracks_z = list(
                    map(lambda rotation: rotation.z, frames_data))
                rotation_tracks_w = list(
                    map(lambda rotation: rotation.w, frames_data))

                rot_curve_w = action.fcurves.new(
                    data_path=data_path_rot, index=0)
                rot_curve_x = action.fcurves.new(
                    data_path=data_path_rot, index=1)
                rot_curve_y = action.fcurves.new(
                    data_path=data_path_rot, index=2)
                rot_curve_z = action.fcurves.new(
                    data_path=data_path_rot, index=3)

                rot_curve_w.group = group_item
                rot_curve_x.group = group_item
                rot_curve_y.group = group_item
                rot_curve_z.group = group_item

                rot_curve_w.keyframe_points.add(len(frames_data))
                rot_curve_x.keyframe_points.add(len(frames_data))
                rot_curve_y.keyframe_points.add(len(frames_data))
                rot_curve_z.keyframe_points.add(len(frames_data))

                rot_curve_w.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, rotation_tracks_w) for x in co])
                rot_curve_x.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, rotation_tracks_x) for x in co])
                rot_curve_y.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, rotation_tracks_y) for x in co])
                rot_curve_z.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, rotation_tracks_z) for x in co])

                rot_curve_w.update()
                rot_curve_x.update()
                rot_curve_y.update()
                rot_curve_z.update()


def actions_data_to_actions(action_name, actions_data, armature, frame_count):
    actions = {}

    for action_type in actions_data:
        action = bpy.data.actions.new(f"{action_name}_{action_type}")

        apply_action_data_to_action(
            actions_data[action_type], action, frame_count)

        actions[action_type] = action

    return actions


def animation_to_obj(animation, armature, is_ped_animation):
    animation_obj = create_anim_obj(SollumType.ANIMATION)

    animation_obj.name = animation.hash
    animation_obj.animation_properties.hash = animation.hash
    animation_obj.animation_properties.frame_count = animation.frame_count

    actions_data = combine_sequences_and_convert_to_groups(
        animation, armature, is_ped_animation)
    actions = actions_data_to_actions(
        animation.hash, actions_data, armature, animation.frame_count)

    if "base" in actions:
        animation_obj.animation_properties.base_action = actions["base"]

    if "root_motion_location" in actions:
        animation_obj.animation_properties.root_motion_location_action = actions[
            "root_motion_location"]

    if "root_motion_rotation" in actions:
        animation_obj.animation_properties.root_motion_rotation_action = actions[
            "root_motion_rotation"]

    return animation_obj


def clip_to_obj(clip, animations_map, animations_obj_map):
    clip_obj = create_anim_obj(SollumType.CLIP)

    clip_obj.name = clip.hash
    clip_obj.clip_properties.hash = clip.hash
    clip_obj.clip_properties.name = clip.name
    clip_obj.clip_properties.animations.clear()

    if clip.type == "Animation":
        animation_data = animations_map[clip.animation_hash]

        clip_obj.clip_properties.duration = clip.end_time - clip.start_time

        clip_animation = clip_obj.clip_properties.animations.add()
        clip_animation.animation = animations_obj_map[clip.animation_hash]
        clip_animation.start_frame = int(
            (clip.start_time / animation_data.duration) * animation_data.frame_count)
        clip_animation.end_frame = int(
            (clip.end_time / animation_data.duration) * animation_data.frame_count)
    elif clip.type == "AnimationList":
        clip_obj.clip_properties.duration = clip.duration

        for animation in clip.animations:
            animation_data = animations_map[animation.animation_hash]

            clip_animation = clip_obj.clip_properties.animations.add()
            clip_animation.animation = animations_obj_map[animation.animation_hash]
            clip_animation.start_frame = int(
                (animation.start_time / animation_data.duration) * animation_data.frame_count)
            clip_animation.end_frame = int(
                (animation.end_time / animation_data.duration) * animation_data.frame_count)

    return clip_obj


def create_clip_dictionary_template(name, obj, anim_type):
    clip_dictionary_obj = create_anim_obj(SollumType.CLIP_DICTIONARY)
    clips_obj = create_anim_obj(SollumType.CLIPS)
    animations_obj = create_anim_obj(SollumType.ANIMATIONS)

    clip_dictionary_obj.name = name

    clips_obj.parent = clip_dictionary_obj
    animations_obj.parent = clip_dictionary_obj

    if anim_type == "REGULAR":
        clip_dictionary_obj.clip_dict_properties.armature = obj.data
    elif anim_type == "UV":
        if len(obj.data.materials) < 1:
            raise Exception("Error cannot find any materials to animate")
        else:
            clip_dictionary_obj.clip_dict_properties.uv_obj = obj
    else:
        raise Exception("Selected animation type not implemented!")

    return clip_dictionary_obj, clips_obj, animations_obj


def clip_dictionary_to_obj(clip_dictionary, name, armature, armature_obj):
    animation_type = bpy.context.scene.create_animation_type
    _, clips_obj, animations_obj = create_clip_dictionary_template(
        name, armature_obj, animation_type)

    is_ped_animation = False

    for p_bone in armature_obj.pose.bones:
        if is_ped_bone_tag(p_bone.bone.bone_properties.tag):
            is_ped_animation = True
            break

    animations_map = {}
    animations_obj_map = {}

    for animation in clip_dictionary.animations:
        animations_map[animation.hash] = animation

        animation_obj = animation_to_obj(
            animation, armature_obj, is_ped_animation)
        animation_obj.parent = animations_obj

        animations_obj_map[animation.hash] = animation_obj

    for clip in clip_dictionary.clips:
        clip.name = clip.name.replace("pack:/", "")
        clip_obj = clip_to_obj(clip, animations_map, animations_obj_map)
        clip_obj.parent = clips_obj


def import_ycd(filepath):
    import_settings = get_import_settings()

    if import_settings.selected_armature == -1 or not list_index_exists(bpy.data.armatures, import_settings.selected_armature):
        logger.warning("Selected target skeleton not found.")
        return

    armature = bpy.data.armatures[import_settings.selected_armature]
    armature_obj = get_armature_obj(armature)

    ycr_xml = YCD.from_xml_file(filepath)

    animation_type = bpy.context.scene.create_animation_type
    if animation_type == "UV":
        logger.warning(
            "UV import is not supported. Change the animation type under Animation Tools panel")
        return

    clip_dictionary_to_obj(
        ycr_xml,
        os.path.basename(
            filepath.replace(YCD.file_extension, "")
        ),
        armature,
        armature_obj
    )
