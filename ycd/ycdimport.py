import os
import bpy
from mathutils import Vector, Quaternion
from ..cwxml import clipdictionary as ycdxml
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.animationhelper import (
    Track,
    TrackFormat,
    TrackFormatMap,
    get_canonical_track_data_path,
    get_action_duration_frames,
    get_scene_fps
)
from ..tools.utils import color_hash


def create_anim_obj(sollum_type: SollumType) -> bpy.types.Object:
    anim_obj = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    anim_obj.empty_display_size = 0
    anim_obj.sollum_type = sollum_type
    bpy.context.collection.objects.link(anim_obj)
    return anim_obj


ActionData = dict[int, dict[Track, list]]


def insert_action_data(action_data: ActionData, bone_id: int, track: Track, data):
    if bone_id not in action_data:
        action_data[bone_id] = {}

    if track not in action_data[bone_id]:
        action_data[bone_id][track] = []

    action_data[bone_id][track].append(data)


def get_values_from_sequence_data(sequence_data: ycdxml.Animation.SequenceDataList.SequenceData, frame_id: int) -> list:
    channel_values = []

    for i in range(len(sequence_data.channels)):
        while len(channel_values) <= i:
            channel_values.append(None)

        channel = sequence_data.channels[i]

        if channel is not None:
            channel_values[i] = channel.get_value(frame_id, channel_values)

    return channel_values


def get_vector3_from_sequence_data(
    sequence_data: ycdxml.Animation.SequenceDataList.SequenceData,
    frame_id: int
) -> Vector:
    channel_values = get_values_from_sequence_data(sequence_data, frame_id)

    if len(channel_values) == 1:
        location = channel_values[0]
    else:
        location = Vector([
            channel_values[0],
            channel_values[1],
            channel_values[2],
        ])

    return location


def get_quaternion_from_sequence_data(
    sequence_data: ycdxml.Animation.SequenceDataList.SequenceData,
    frame_id: int
) -> Quaternion:
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

    return rotation


def combine_sequences_and_build_action_data(animation: ycdxml.Animation) -> ActionData:
    sequence_frame_limit = animation.sequence_frame_limit

    if len(animation.sequences) <= 1:
        sequence_frame_limit = animation.frame_count + 30

    action_data = {}

    for frame_id in range(0, animation.frame_count):
        sequence_index = int(frame_id / (sequence_frame_limit))
        sequence_frame = frame_id % (sequence_frame_limit)

        if sequence_index >= len(animation.sequences):
            sequence_index = len(animation.sequences) - 1

        sequence = animation.sequences[sequence_index]

        for sequence_data_index, sequence_data in enumerate(sequence.sequence_data):
            bone_data = animation.bone_ids[sequence_data_index]
            bone_id = bone_data.bone_id

            if bone_data is None:
                continue

            track = bone_data.track
            format = bone_data.format
            assert TrackFormatMap[track] == format, f"Track format mismatch: {TrackFormatMap[track]} != {format}"

            if format == TrackFormat.Vector3:
                vec = get_vector3_from_sequence_data(sequence_data, sequence_frame)
                insert_action_data(action_data, bone_id, track, vec)
            elif format == TrackFormat.Quaternion:
                quat = get_quaternion_from_sequence_data(sequence_data, sequence_frame)
                insert_action_data(action_data, bone_id, track, quat)
            elif format == TrackFormat.Float:
                value = get_values_from_sequence_data(sequence_data, sequence_frame)[0]
                insert_action_data(action_data, bone_id, track, value)

    return action_data


def apply_action_data_to_action(action_data: ActionData, action: bpy.types.Action, frame_count: int, duration_secs: float):
    # Scale frame IDs to match the animation duration specified in the XML in Blender
    # -1 because the anim finishes when it reaches the last frame
    unscaled_duration_secs = (frame_count - 1) / get_scene_fps()
    scale_factor = duration_secs / unscaled_duration_secs
    scaled_frame_ids = [frame_id * scale_factor for frame_id in range(frame_count)]

    def _interleave_frame_ids(track_data: list[float]) -> list[float]:
        """Converts [data0, data1, ..., dataN] to [frameId0, data0, frameId1, data1, ..., frameIdN, dataN]"""
        assert len(track_data) == len(scaled_frame_ids)
        return [value for co in zip(scaled_frame_ids, track_data) for value in co]

    if bpy.app.version >= (5, 0, 0):
        from bpy_extras import anim_utils

        action_idtype = "OBJECT"
        if (uv_bone_data := action_data.get(0, {})) and (Track.UV0 in uv_bone_data or Track.UV1 in uv_bone_data):
            action_idtype = "MATERIAL"
        action_slot = action.slots.new(action_idtype, "Slot")
        channelbag = anim_utils.action_ensure_channelbag_for_slot(action, action_slot)
        def _new_fcurve(data_path: str, index: int, group: str):
            return channelbag.fcurves.new(data_path, index=index, group_name=group)
    else:
        def _new_fcurve(data_path: str, index: int, group: str):
            return action.fcurves.new(data_path, index=index, action_group=group)

    for bone_id, bones_data in action_data.items():
        group_name = f"#{bone_id}"

        for track, frames_data in bones_data.items():
            track_format = TrackFormatMap[track]
            data_path = get_canonical_track_data_path(track, bone_id)
            if track_format == TrackFormat.Vector3:
                vec_tracks_x = list(map(lambda vec: vec.x, frames_data))
                vec_tracks_y = list(map(lambda vec: vec.y, frames_data))
                vec_tracks_z = list(map(lambda vec: vec.z, frames_data))

                vec_curve_x = _new_fcurve(data_path, 0, group_name)
                vec_curve_y = _new_fcurve(data_path, 1, group_name)
                vec_curve_z = _new_fcurve(data_path, 2, group_name)

                vec_curve_x.keyframe_points.add(len(frames_data))
                vec_curve_y.keyframe_points.add(len(frames_data))
                vec_curve_z.keyframe_points.add(len(frames_data))

                vec_curve_x.keyframe_points.foreach_set("co", _interleave_frame_ids(vec_tracks_x))
                vec_curve_y.keyframe_points.foreach_set("co", _interleave_frame_ids(vec_tracks_y))
                vec_curve_z.keyframe_points.foreach_set("co", _interleave_frame_ids(vec_tracks_z))

                vec_curve_x.update()
                vec_curve_y.update()
                vec_curve_z.update()
            elif track_format == TrackFormat.Quaternion:
                quat_tracks_x = list(map(lambda rotation: rotation.x, frames_data))
                quat_tracks_y = list(map(lambda rotation: rotation.y, frames_data))
                quat_tracks_z = list(map(lambda rotation: rotation.z, frames_data))
                quat_tracks_w = list(map(lambda rotation: rotation.w, frames_data))

                quat_curve_w = _new_fcurve(data_path, 0, group_name)
                quat_curve_x = _new_fcurve(data_path, 1, group_name)
                quat_curve_y = _new_fcurve(data_path, 2, group_name)
                quat_curve_z = _new_fcurve(data_path, 3, group_name)

                quat_curve_w.keyframe_points.add(len(frames_data))
                quat_curve_x.keyframe_points.add(len(frames_data))
                quat_curve_y.keyframe_points.add(len(frames_data))
                quat_curve_z.keyframe_points.add(len(frames_data))

                quat_curve_w.keyframe_points.foreach_set("co", _interleave_frame_ids(quat_tracks_w))
                quat_curve_x.keyframe_points.foreach_set("co", _interleave_frame_ids(quat_tracks_x))
                quat_curve_y.keyframe_points.foreach_set("co", _interleave_frame_ids(quat_tracks_y))
                quat_curve_z.keyframe_points.foreach_set("co", _interleave_frame_ids(quat_tracks_z))

                quat_curve_w.update()
                quat_curve_x.update()
                quat_curve_y.update()
                quat_curve_z.update()
            elif track_format == TrackFormat.Float:
                value_curve = _new_fcurve(data_path, 0, group_name)

                value_curve.keyframe_points.add(len(frames_data))
                value_curve.keyframe_points.foreach_set("co", _interleave_frame_ids(frames_data))

                value_curve.update()


def action_data_to_action(action_name: str, action_data, frame_count: int, duration_secs: float) -> bpy.types.Action:
    action = bpy.data.actions.new(f"{action_name}_action")
    apply_action_data_to_action(action_data, action, frame_count, duration_secs)
    return action


def animation_to_obj(animation: ycdxml.Animation) -> bpy.types.Object:
    animation_obj = create_anim_obj(SollumType.ANIMATION)

    animation_obj.name = animation.hash
    animation_obj.animation_properties.hash = animation.hash

    action_data = combine_sequences_and_build_action_data(animation)
    animation_obj.animation_properties.action = action_data_to_action(animation.hash, action_data,
                                                                      animation.frame_count, animation.duration)

    return animation_obj


def clip_to_obj(
    clip: ycdxml.Clip,
    animations_map: dict[str, ycdxml.Animation],
    animations_obj_map: dict[str, bpy.types.Object]
) -> bpy.types.Object:
    clip_obj = create_anim_obj(SollumType.CLIP)

    clip_obj.name = clip.hash
    clip_obj.clip_properties.hash = clip.hash
    clip_obj.clip_properties.name = clip.name
    clip_obj.clip_properties.animations.clear()

    if clip.type == ycdxml.ClipType.ANIMATION:
        animation_data = animations_map[clip.animation_hash]
        animation_obj = animations_obj_map[clip.animation_hash]
        duration_secs = animation_data.duration
        duration_frames = get_action_duration_frames(animation_obj.animation_properties.action)

        clip_obj.clip_properties.duration = (clip.end_time - clip.start_time) / clip.rate

        clip_animation = clip_obj.clip_properties.animations.add()
        clip_animation.animation = animation_obj
        clip_animation.start_frame = (clip.start_time / duration_secs) * duration_frames
        clip_animation.end_frame = (clip.end_time / duration_secs) * duration_frames
    elif clip.type == ycdxml.ClipType.ANIMATION_LIST:
        clip_obj.clip_properties.duration = clip.duration

        for animation in clip.animations:
            animation_data = animations_map[animation.animation_hash]
            animation_obj = animations_obj_map[animation.animation_hash]
            duration_secs = animation_data.duration
            duration_frames = get_action_duration_frames(animation_obj.animation_properties.action)

            clip_animation = clip_obj.clip_properties.animations.add()
            clip_animation.animation = animation_obj
            clip_animation.start_frame = (animation.start_time / duration_secs) * duration_frames
            clip_animation.end_frame = (animation.end_time / duration_secs) * duration_frames

             # NOTE: we can ignore animation.rate because all anims in the list play in parallel,
             # so `(animation.end_time - animation.start_time) / animation.rate` should equal `clip.duration`,
             # which we already set in the clip_properties

    def _init_attribute(attr, xml_attr):
        attr.name = xml_attr.name_hash
        attr.type = xml_attr.type
        if attr.type == "Float":
            attr.value_float = xml_attr.value
        elif attr.type == "Int":
            attr.value_int = xml_attr.value
        elif attr.type == "Bool":
            attr.value_bool = xml_attr.value != 0
        elif attr.type == "Vector3":
            attr.value_vec3 = xml_attr.value
        elif attr.type == "Vector4":
            attr.value_vec4 = xml_attr.value
        elif attr.type == "String" or attr.type == "HashString":
            attr.value_string = xml_attr.value

    clip_obj.clip_properties.tags.clear()
    for tag in clip.tags:
        clip_tag = clip_obj.clip_properties.tags.add()
        clip_tag.name = tag.name_hash
        clip_tag.ui_timeline_color = color_hash(clip_tag.name)
        clip_tag.start_phase = tag.start_phase
        clip_tag.end_phase = tag.end_phase
        for attr in tag.attributes:
            clip_tag_attr = clip_tag.attributes.add()
            _init_attribute(clip_tag_attr, attr)

    clip_obj.clip_properties.properties.clear()
    for prop in clip.properties:
        clip_prop = clip_obj.clip_properties.properties.add()
        clip_prop.name = prop.name_hash
        for attr in prop.attributes:
            clip_prop_attr = clip_prop.attributes.add()
            _init_attribute(clip_prop_attr, attr)

    return clip_obj


def create_clip_dictionary_template(name: str) -> tuple[bpy.types.Object, bpy.types.Object, bpy.types.Object]:
    clip_dictionary_obj = create_anim_obj(SollumType.CLIP_DICTIONARY)
    clips_obj = create_anim_obj(SollumType.CLIPS)
    animations_obj = create_anim_obj(SollumType.ANIMATIONS)

    clip_dictionary_obj.name = name

    clips_obj.parent = clip_dictionary_obj
    animations_obj.parent = clip_dictionary_obj

    return clip_dictionary_obj, clips_obj, animations_obj


def clip_dictionary_to_obj(clip_dictionary: ycdxml.ClipDictionary, name: str) -> bpy.types.Object:
    clip_dict_obj, clips_obj, animations_obj = create_clip_dictionary_template(name)

    animations_map = {}
    animations_obj_map = {}

    for animation in clip_dictionary.animations:
        animations_map[animation.hash] = animation

        animation_obj = animation_to_obj(animation)
        animation_obj.parent = animations_obj

        animations_obj_map[animation.hash] = animation_obj

    for clip in clip_dictionary.clips:
        clip.name = clip.name.replace("pack:/", "")
        clip_obj = clip_to_obj(clip, animations_map, animations_obj_map)
        clip_obj.parent = clips_obj

    return clip_dict_obj


def import_ycd(filepath: str) -> bpy.types.Object:
    ycd_xml = ycdxml.YCD.from_xml_file(filepath)

    return clip_dictionary_to_obj(
        ycd_xml,
        os.path.basename(filepath.replace(ycdxml.YCD.file_extension, ""))
    )
