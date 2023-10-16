import os
import bpy
from mathutils import Vector, Quaternion
from ..cwxml import clipdictionary as ycdxml
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.animationhelper import Track, TrackFormat, TrackFormatMap, get_canonical_track_data_path
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


def apply_action_data_to_action(action_data: ActionData, action: bpy.types.Action, frame_count: int):
    frames_ids = [*range(frame_count)]

    for bone_id, bones_data in action_data.items():
        group_item = action.groups.new(f"#{bone_id}")
        for track, frames_data in bones_data.items():
            format = TrackFormatMap[track]
            data_path = get_canonical_track_data_path(track, bone_id)
            if format == TrackFormat.Vector3:
                vec_tracks_x = list(map(lambda vec: vec.x, frames_data))
                vec_tracks_y = list(map(lambda vec: vec.y, frames_data))
                vec_tracks_z = list(map(lambda vec: vec.z, frames_data))

                vec_curve_x = action.fcurves.new(data_path=data_path, index=0)
                vec_curve_y = action.fcurves.new(data_path=data_path, index=1)
                vec_curve_z = action.fcurves.new(data_path=data_path, index=2)

                vec_curve_x.group = group_item
                vec_curve_y.group = group_item
                vec_curve_z.group = group_item

                vec_curve_x.keyframe_points.add(len(frames_data))
                vec_curve_y.keyframe_points.add(len(frames_data))
                vec_curve_z.keyframe_points.add(len(frames_data))

                vec_curve_x.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, vec_tracks_x) for x in co])
                vec_curve_y.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, vec_tracks_y) for x in co])
                vec_curve_z.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, vec_tracks_z) for x in co])

                vec_curve_x.update()
                vec_curve_y.update()
                vec_curve_z.update()
            elif format == TrackFormat.Quaternion:
                quat_tracks_x = list(map(lambda rotation: rotation.x, frames_data))
                quat_tracks_y = list(map(lambda rotation: rotation.y, frames_data))
                quat_tracks_z = list(map(lambda rotation: rotation.z, frames_data))
                quat_tracks_w = list(map(lambda rotation: rotation.w, frames_data))

                quat_curve_w = action.fcurves.new(data_path=data_path, index=0)
                quat_curve_x = action.fcurves.new(data_path=data_path, index=1)
                quat_curve_y = action.fcurves.new(data_path=data_path, index=2)
                quat_curve_z = action.fcurves.new(data_path=data_path, index=3)

                quat_curve_w.group = group_item
                quat_curve_x.group = group_item
                quat_curve_y.group = group_item
                quat_curve_z.group = group_item

                quat_curve_w.keyframe_points.add(len(frames_data))
                quat_curve_x.keyframe_points.add(len(frames_data))
                quat_curve_y.keyframe_points.add(len(frames_data))
                quat_curve_z.keyframe_points.add(len(frames_data))

                quat_curve_w.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, quat_tracks_w) for x in co])
                quat_curve_x.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, quat_tracks_x) for x in co])
                quat_curve_y.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, quat_tracks_y) for x in co])
                quat_curve_z.keyframe_points.foreach_set(
                    "co", [x for co in zip(frames_ids, quat_tracks_z) for x in co])

                quat_curve_w.update()
                quat_curve_x.update()
                quat_curve_y.update()
                quat_curve_z.update()
            elif format == TrackFormat.Float:
                value_curve = action.fcurves.new(data_path=data_path)
                value_curve.group = group_item

                value_curve.keyframe_points.add(len(frames_data))
                value_curve.keyframe_points.foreach_set("co", [x for co in zip(frames_ids, frames_data) for x in co])

                value_curve.update()


def action_data_to_action(action_name: str, action_data, frame_count: int) -> bpy.types.Action:
    action = bpy.data.actions.new(f"{action_name}_action")
    apply_action_data_to_action(action_data, action, frame_count)
    return action


def animation_to_obj(animation: ycdxml.Animation) -> bpy.types.Object:
    animation_obj = create_anim_obj(SollumType.ANIMATION)

    animation_obj.name = animation.hash
    animation_obj.animation_properties.hash = animation.hash
    animation_obj.animation_properties.frame_count = animation.frame_count

    action_data = combine_sequences_and_build_action_data(animation)
    animation_obj.animation_properties.action = action_data_to_action(animation.hash, action_data,
                                                                      animation.frame_count)

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

    if clip.type == "Animation":
        animation_data = animations_map[clip.animation_hash]

        clip_obj.clip_properties.duration = clip.end_time - clip.start_time

        clip_animation = clip_obj.clip_properties.animations.add()
        clip_animation.animation = animations_obj_map[clip.animation_hash]
        clip_animation.start_frame = int((clip.start_time / animation_data.duration) * animation_data.frame_count)
        clip_animation.end_frame = int((clip.end_time / animation_data.duration) * animation_data.frame_count)
    elif clip.type == "AnimationList":
        clip_obj.clip_properties.duration = clip.duration

        for animation in clip.animations:
            animation_data = animations_map[animation.animation_hash]

            clip_animation = clip_obj.clip_properties.animations.add()
            clip_animation.animation = animations_obj_map[animation.animation_hash]
            clip_animation.start_frame = int(
                (animation.start_time / animation_data.duration) * animation_data.frame_count)
            clip_animation.end_frame = int((animation.end_time / animation_data.duration) * animation_data.frame_count)

    def _init_attribute(attr, xml_attr):
        attr.name = xml_attr.name_hash
        attr.type = xml_attr.type
        if attr.type == "Float":
            attr.value_float = xml_attr.value
        elif attr.type == "Int":
            attr.value_int = xml_attr.value
        elif attr.type == "Bool":
            attr.value_bool = xml_attr.value
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


def clip_dictionary_to_obj(clip_dictionary: ycdxml.ClipDictionary, name: str):
    _, clips_obj, animations_obj = create_clip_dictionary_template(name)

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


def import_ycd(filepath: str):
    ycd_xml = ycdxml.YCD.from_xml_file(filepath)

    clip_dictionary_to_obj(
        ycd_xml,
        os.path.basename(filepath.replace(ycdxml.YCD.file_extension, ""))
    )
