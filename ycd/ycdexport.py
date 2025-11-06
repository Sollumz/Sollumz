import bpy
from mathutils import Vector, Quaternion
import math
import struct
from typing import Optional
from ..cwxml import clipdictionary as ycdxml
from ..sollumz_properties import SollumType
from ..tools import jenkhash
from ..tools.blenderhelper import build_name_bone_map, build_bone_map
from ..tools.animationhelper import (
    Track,
    TrackFormat,
    TrackFormatMap,
    AnimationFlag,
    get_quantum_and_min_val,
    get_id_and_track_from_track_data_path,
    calculate_bone_space_transform_matrix,
    get_target_from_id,
    get_action_duration_frames,
    get_action_duration_secs,
    get_action_export_frame_count,
    action_fcurves,
)
from .properties import ClipAttribute, ClipTag, calculate_final_uv_transform_matrix

from .. import logger


def parse_uv_transform_data_path(data_path: str) -> tuple[int, str]:
    # data_path = '...uv_transforms[123].property'

    # trim up to 'uv_transforms'
    data_path = data_path[data_path.index("uv_transforms") + len("uv_transforms"):]

    # extract transform index
    index_start = data_path.index("[") + 1
    index_end = data_path.index("]", index_start)
    index = int(data_path[index_start:index_end])

    # extract property name
    prop_start = data_path.index(".", index_end) + 1
    prop = data_path[prop_start:]

    return index, prop


TrackFramesData = list[Vector] | list[Quaternion] | list[float]
SequenceItems = dict[int, dict[Track, TrackFramesData]]


def sequence_items_from_action(
        action: bpy.types.Action,
        target_id: bpy.types.ID
) -> SequenceItems:
    action_frame_range = action.frame_range
    export_frame_count = get_action_export_frame_count(action)
    def _export_frame_to_action_frame(frame_index: int) -> float:
        export_last_frame_index = export_frame_count - 1
        return action_frame_range[0] + (frame_index / export_last_frame_index) * (action_frame_range[1] - action_frame_range[0])

    target = get_target_from_id(target_id)
    target_is_armature = isinstance(target_id, bpy.types.Armature)
    target_is_camera = isinstance(target_id, bpy.types.Camera)
    if target_is_armature:
        bone_name_map = build_name_bone_map(target)
        bone_map = build_bone_map(target)
    else:
        bone_name_map = None
        bone_map = None

    uv_transforms_fcurves = {}

    sequence_items: SequenceItems = {}
    for fcurve in action_fcurves(action):
        data_path = fcurve.data_path
        bone_id_track_pair = get_id_and_track_from_track_data_path(data_path, target_id, bone_name_map)
        if bone_id_track_pair is None:
            logger.warning(f"Channel '{data_path}' in action '{action.name}' is unsupported, skipping...")
            continue

        bone_id, track = bone_id_track_pair
        if track == Track.UVTransforms:
            if bone_id not in uv_transforms_fcurves:
                uv_transforms_fcurves[bone_id] = []
            uv_transforms_fcurves[bone_id].append(fcurve)
            continue  # UV transforms are handled later

        comp_index = fcurve.array_index
        track_format = TrackFormatMap[track]

        if bone_id not in sequence_items:
            sequence_items[bone_id] = {}

        bone_sequences = sequence_items[bone_id]

        if track not in bone_sequences:
            if track_format == TrackFormat.Vector3:
                # TODO: defaults should be kept in-sync with the properties defaults in AnimationTracks, refactor this
                #  once we add more defaults to avoid duplication
                if track == Track.UV0:
                    default_vec = (1.0, 0.0, 0.0)
                elif track == Track.UV1:
                    default_vec = (0.0, 1.0, 0.0)
                else:
                    default_vec = (0.0, 0.0, 0.0)
                bone_sequences[track] = [Vector(default_vec) for _ in range(export_frame_count)]
            elif track_format == TrackFormat.Quaternion:
                bone_sequences[track] = [Quaternion((1.0, 0.0, 0.0, 0.0)) for _ in range(export_frame_count)]
            elif track_format == TrackFormat.Float:
                bone_sequences[track] = [0.0] * export_frame_count

        track_sequence = bone_sequences[track]
        for frame_id in range(export_frame_count):
            value = fcurve.evaluate(_export_frame_to_action_frame(frame_id))
            if track_format == TrackFormat.Float:
                track_sequence[frame_id] = value
            else:
                track_sequence[frame_id][comp_index] = value

    if target_is_armature:
        # transform bones from pose space to local space
        for bone_id, bone_sequences in sequence_items.items():
            transform_mat = calculate_bone_space_transform_matrix(bone_map.get(bone_id, None), None)

            if Track.BonePosition in bone_sequences:
                vecs = bone_sequences[Track.BonePosition]
                for i in range(export_frame_count):
                    vecs[i] = transform_mat @ vecs[i]

            if Track.BoneRotation in bone_sequences:
                quats = bone_sequences[Track.BoneRotation]
                for i in range(export_frame_count):
                    quats[i].rotate(transform_mat)

    if target_is_camera:
        # see animationhelper.transform_camera_rotation_quaternion
        angle_delta = math.radians(-90.0)
        x_axis = Vector((1.0, 0.0, 0.0))
        for bone_id, bone_sequences in sequence_items.items():
            if Track.CameraRotation in bone_sequences:
                quats = bone_sequences[Track.CameraRotation]
                for i in range(export_frame_count):
                    x_axis_local = quats[i] @ x_axis
                    quats[i].rotate(Quaternion(x_axis_local, angle_delta))

    if target_id is not None and len(uv_transforms_fcurves) > 0:
        # copy the UV transforms defined by the user to apply f-curves on them without modifying the original ones
        uv_transforms = target.export_uv_transforms
        uv_transforms.clear()
        for uv_transform in target.animation_tracks.uv_transforms:
            uv_transform_copy = uv_transforms.add()
            uv_transform_copy.update_uv_transform_matrix_on_change = False
            uv_transform_copy.copy_from(uv_transform)

        for bone_id, fcurves in uv_transforms_fcurves.items():
            if bone_id not in sequence_items:
                sequence_items[bone_id] = {}

            bone_sequences = sequence_items[bone_id]

            # compute uv0/uv1 from uv_transform
            bone_sequences[Track.UV0] = [Vector((0.0, 0.0, 0.0)) for _ in range(export_frame_count)]
            bone_sequences[Track.UV1] = [Vector((0.0, 0.0, 0.0)) for _ in range(export_frame_count)]
            uv0_sequence = bone_sequences[Track.UV0]
            uv1_sequence = bone_sequences[Track.UV1]
            for frame_id in range(export_frame_count):
                # apply f-curves to UV transforms
                for fcurve in fcurves:
                    value = fcurve.evaluate(_export_frame_to_action_frame(frame_id))
                    transform_index, prop_name = parse_uv_transform_data_path(fcurve.data_path)

                    prop = getattr(uv_transforms[transform_index], prop_name)
                    if isinstance(prop, float):
                        setattr(uv_transforms[transform_index], prop_name, value)
                    else:  # Vector
                        comp_index = fcurve.array_index
                        prop[comp_index] = value

                mat = calculate_final_uv_transform_matrix(uv_transforms)
                uv0_sequence[frame_id][0] = mat[0][0]
                uv0_sequence[frame_id][1] = mat[0][1]
                uv0_sequence[frame_id][2] = mat[0][2]
                uv1_sequence[frame_id][0] = mat[1][0]
                uv1_sequence[frame_id][1] = mat[1][1]
                uv1_sequence[frame_id][2] = mat[1][2]

        uv_transforms.clear()

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
    quaternion_tracks = list(map(lambda kvp: kvp[0],
                                 filter(lambda kvp: kvp[1] == TrackFormat.Quaternion,
                                        TrackFormatMap.items())))
    for bone_id, bone_sequences in sequence_items.items():
        for track in quaternion_tracks:
            quats = bone_sequences.get(track, None)
            if quats is None:
                continue

            for i in range(1, export_frame_count):
                if quats[i - 1].dot(quats[i]) < 0:
                    quats[i] *= -1
    # WARNING: ANY OPERATION WITH ROTATION WILL CAUSE SIGN CHANGE. PROCEED ANYTHING BEFORE FIX.

    return sequence_items


def build_values_channel(
    values: list[float],
    uniq_values: list[float],
    indirect_percentage: float = 0.1
) -> ycdxml.ChannelsList.Channel:
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

    # TODO: decide when RawFloat is needed (quantizefloat may compress values too much)
    # else:
    #     channel = ycdxml.ChannelsList.RawFloat()
    #     channel.values = values

    return channel


def sequence_data_from_frames_data(
    track: Track,
    frames_data: TrackFramesData
) -> ycdxml.Animation.SequenceDataList.SequenceData:
    sequence_data = ycdxml.Animation.SequenceDataList.SequenceData()

    track_format = TrackFormatMap[track]

    if track_format == TrackFormat.Vector3:
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
    elif track_format == TrackFormat.Quaternion:
        values_x = []
        values_y = []
        values_z = []
        values_w = []

        for quat in frames_data:
            values_x.append(quat.x)
            values_y.append(quat.y)
            values_z.append(quat.z)
            values_w.append(quat.w)

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
    elif track_format == TrackFormat.Float:
        values = frames_data
        uniq = list(set(values))
        sequence_data.channels.append(build_values_channel(values, uniq))

    return sequence_data


def animation_from_object(animation_obj: bpy.types.Object) -> Optional[ycdxml.Animation]:
    animation_properties = animation_obj.animation_properties
    action = animation_properties.action
    export_frame_count = get_action_export_frame_count(action)
    if export_frame_count == 0:
        logger.error(f"Action '{action.name}' has no keyframes. Used by animation '{animation_obj.name}'. Cannot export empty action.")
        return None

    animation = ycdxml.Animation()
    animation.hash = animation_properties.hash
    animation.frame_count = export_frame_count
    animation.sequence_frame_limit = export_frame_count + 30
    animation.duration = get_action_duration_secs(action)
    animation.unknown10 = AnimationFlag.Default

    # signature: this value must be unique (used internally for animation caching)
    # TODO: CW should calculate this on import with the proper hash function
    animation.unknown1C = f"hash_{jenkhash.Generate(animation_properties.hash) + 1:08X}"

    target_id = animation_properties.target_id
    sequence_items = sequence_items_from_action(action, target_id)

    sequence = ycdxml.Animation.SequenceList.Sequence()
    sequence.frame_count = export_frame_count
    sequence.hash = "hash_00000000"  # TODO: calculate signature

    sequence_datas = [(bone_id, track, frames_data)
                      for bone_id, bones_data in sequence_items.items()
                      for track, frames_data in bones_data.items()]
    sequence_datas.sort(key=lambda x: x[0] | (x[1].value << 16))
    for bone_id, track, frames_data in sequence_datas:
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


def clip_attribute_to_xml(attr: ClipAttribute) -> ycdxml.AttributesList.Attribute:
    if attr.type == "Float":
        xml_attr = ycdxml.AttributesList.FloatAttribute()
        xml_attr.value = attr.value_float
    elif attr.type == "Int":
        xml_attr = ycdxml.AttributesList.IntAttribute()
        xml_attr.value = attr.value_int
    elif attr.type == "Bool":
        xml_attr = ycdxml.AttributesList.BoolAttribute()
        xml_attr.value = 1 if attr.value_bool else 0
    elif attr.type == "Vector3":
        xml_attr = ycdxml.AttributesList.Vector3Attribute()
        xml_attr.value = Vector(attr.value_vec3)
    elif attr.type == "Vector4":
        xml_attr = ycdxml.AttributesList.Vector4Attribute()
        xml_attr.value = Vector(attr.value_vec4)
    elif attr.type == "String":
        xml_attr = ycdxml.AttributesList.StringAttribute()
        xml_attr.value = attr.value_string
    elif attr.type == "HashString":
        xml_attr = ycdxml.AttributesList.HashStringAttribute()
        xml_attr.value = attr.value_string
    else:
        assert False, f"Unknown attribute type: {attr.type}"
    xml_attr.name_hash = attr.name
    return xml_attr


def clip_attribute_calc_signature(attr: ClipAttribute) -> int:
    signature = jenkhash.name_to_hash(attr.name)
    if attr.type == "Float":
        signature = jenkhash.GenerateData(struct.pack("f", attr.value_float), seed=signature)
    elif attr.type == "Int":
        signature = jenkhash.GenerateData(struct.pack("i", attr.value_int), seed=signature)
    elif attr.type == "Bool":
        signature = jenkhash.GenerateData(struct.pack("?", attr.value_bool), seed=signature)
    elif attr.type == "Vector3":
        vec3 = attr.value_vec3
        signature = jenkhash.GenerateData(struct.pack("3f", vec3[0], vec3[1], vec3[2]), seed=signature)
    elif attr.type == "Vector4":
        vec4 = attr.value_vec4
        signature = jenkhash.GenerateData(struct.pack("4f", vec4[0], vec4[1], vec4[2], vec4[3]), seed=signature)
    elif attr.type == "String":
        signature = jenkhash.Generate(attr.value_string, seed=signature)
    elif attr.type == "HashString":
        signature = jenkhash.name_to_hash(attr.value_string)
    else:
        assert False, f"Unknown attribute type: {attr.type}"

    return signature


# TODO: these calc_signature functions try to reproduce the original
#  calculations but currently do not match the expected results, investigate.
#  Should be good enough for now
def clip_property_calc_signature(prop: ClipAttribute) -> int:
    signature = jenkhash.name_to_hash(prop.name)
    for attr in prop.attributes:
        attr_signature = clip_attribute_calc_signature(attr)
        signature = jenkhash.GenerateData(struct.pack("I", attr_signature), seed=signature)

    return signature


def clip_tag_calc_signature(tag: ClipTag) -> int:
    import zlib

    signature = jenkhash.name_to_hash(tag.name)
    for attr in tag.attributes:
        attr_signature = clip_attribute_calc_signature(attr)
        signature = jenkhash.GenerateData(struct.pack("I", attr_signature), seed=signature)

    signature = zlib.crc32(struct.pack("f", tag.start_phase), jenkhash.name_to_hash(tag.name) ^ signature)
    signature = zlib.crc32(struct.pack("f", tag.end_phase), signature)
    return signature


def clip_from_object(clip_obj: bpy.types.Object) -> ycdxml.Clip:
    clip_properties = clip_obj.clip_properties

    is_single_animation = len(clip_properties.animations) == 1

    if is_single_animation:
        xml_clip = ycdxml.ClipsList.ClipAnimation()
        clip_animation_property = clip_properties.animations[0]
        animation_properties = clip_animation_property.animation.animation_properties
        duration_frames = get_action_duration_frames(animation_properties.action)
        duration_secs = get_action_duration_secs(animation_properties.action)

        xml_clip.animation_hash = animation_properties.hash
        xml_clip.start_time = (clip_animation_property.start_frame / duration_frames) * duration_secs
        xml_clip.end_time = (clip_animation_property.end_frame / duration_frames) * duration_secs

        clip_animation_duration = xml_clip.end_time - xml_clip.start_time
        xml_clip.rate =  clip_animation_duration / clip_properties.duration
    else:
        xml_clip = ycdxml.ClipsList.ClipAnimationList()
        xml_clip.duration = clip_properties.duration

        for clip_animation_property in clip_properties.animations:
            clip_animation = ycdxml.ClipAnimationsList.ClipAnimation()

            animation_properties = clip_animation_property.animation.animation_properties
            duration_frames = get_action_duration_frames(animation_properties.action)
            duration_secs = get_action_duration_secs(animation_properties.action)

            clip_animation.animation_hash = animation_properties.hash
            clip_animation.start_time = (clip_animation_property.start_frame / duration_frames) * duration_secs
            clip_animation.end_time = (clip_animation_property.end_frame / duration_frames) * duration_secs

            clip_animation_duration = clip_animation.end_time - clip_animation.start_time
            clip_animation.rate = clip_animation_duration / clip_properties.duration

            xml_clip.animations.append(clip_animation)

    xml_clip.hash = clip_properties.hash
    xml_clip.name = "pack:/" + clip_properties.name
    xml_clip.unknown30 = 0

    for tag in clip_properties.tags:
        xml_tag = ycdxml.Clip.TagList.Tag()
        xml_tag.name_hash = tag.name
        xml_tag.unk_hash = f"hash_{clip_tag_calc_signature(tag):08X}"
        xml_tag.start_phase = tag.start_phase
        xml_tag.end_phase = tag.end_phase
        for attr in tag.attributes:
            xml_tag.attributes.append(clip_attribute_to_xml(attr))
        xml_clip.tags.append(xml_tag)
    xml_clip.tags.sort(key=lambda t: t.start_phase)

    for prop in clip_properties.properties:
        xml_prop = ycdxml.Property()
        xml_prop.name_hash = prop.name
        xml_prop.unk_hash = f"hash_{clip_property_calc_signature(prop):08X}"
        for attr in prop.attributes:
            xml_prop.attributes.append(clip_attribute_to_xml(attr))
        xml_clip.properties.append(xml_prop)

    return xml_clip


def clip_dictionary_from_object(obj: bpy.types.Object) -> Optional[ycdxml.ClipDictionary]:
    clip_dictionary = ycdxml.ClipDictionary()

    animations_obj = None
    clips_obj = None

    for child_obj in obj.children:
        if child_obj.sollum_type == SollumType.ANIMATIONS:
            animations_obj = child_obj
        elif child_obj.sollum_type == SollumType.CLIPS:
            clips_obj = child_obj

    any_animation_export_failed = False
    for animation_obj in animations_obj.children:
        animation = animation_from_object(animation_obj)
        if animation is None:
            any_animation_export_failed = True
            continue

        clip_dictionary.animations.append(animation)

    if any_animation_export_failed:
        # If any animation had some error, it's not safe to continue exporting the clips
        return None

    for clip_obj in clips_obj.children:
        clip = clip_from_object(clip_obj)

        clip_dictionary.clips.append(clip)

    return clip_dictionary


def export_ycd(obj: bpy.types.Object, filepath: str) -> bool:
    clip_dict = clip_dictionary_from_object(obj)
    if clip_dict is None:
        return False

    clip_dict.write_xml(filepath)
    return True
