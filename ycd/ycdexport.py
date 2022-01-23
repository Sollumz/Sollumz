from msilib import sequence
from operator import contains
import bl_keymap_utils
import bpy
from bpy.types import PoseBone, FCurve, Action
from mathutils import Vector, Quaternion, Euler
from ..resources.clipsdictionary import *
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import build_name_bone_map, build_bone_map, get_armature_obj
from ..tools.animationhelper import evaluate_euler_to_quaternion, evaluate_quaternion, evaluate_vector, is_ped_bone_tag, rotate_preserve_sign, get_quantum_and_min_val
from ..tools.utils import list_index_exists

def get_name(item):
    return item.name.split('.')[0]


def get_track_id(type, action_type, with_unk0=False):
    track = -1
    unk0 = -1

    # TODO: Move to enum

    if type == 'location':
        unk0 = 0

        if action_type == 'base':
            track = 0
        elif action_type == 'root_motion':
            track = 5
    elif type == 'rotation_quaternion' or type == 'rotation_euler':
        unk0 = 1

        if action_type == 'base':
            track = 1
        elif action_type == 'root_motion':
            track = 6
    elif type == 'scale':
        unk0 = 0

        if action_type == 'base':
            track = 2

    if with_unk0:
        return track, unk0

    return track


def fill_bone_ids_from_action(action, bone_groups, bones_name_map, action_type):
    bones_list_map = {}

    for fcurve in action.fcurves.values():
        bone_name, type = fcurve.data_path.replace('pose.bones["', '').replace('"]', '').split('.')

        if bone_name not in bones_name_map:
            continue

        if '%s-%s' % (bone_name, type) not in bones_list_map:
            bones_list_map['%s-%s' % (bone_name, type)] = True

            track, unk0 = get_track_id(type, action_type, True)

            if track == -1:
                continue

            bone_id = Animation.BoneIdListProperty.BoneId()

            bone_id.bone_id = bones_name_map[bone_name]
            bone_id.track = track
            bone_id.unk0 = unk0

            if track not in bone_groups:
                bone_groups[track] = []

            bone_groups[track].append(bone_id)


def sequence_items_from_action(action: Action, sequence_items, bones_map, action_type, frame_count, is_ped_animation):
    locations = {}
    rotations = {}
    scales = {}
    
    p_bone: PoseBone
    for bone_id, p_bone in bones_map.items():
        pos_vector_path = p_bone.path_from_id('location')
        rot_quaternion_path = p_bone.path_from_id('rotation_quaternion')
        rot_euler_path = p_bone.path_from_id('rotation_euler')
        scale_vector_path = p_bone.path_from_id('scale')

        # Get list of per-frame data for every path

        b_locations = evaluate_vector(action.fcurves, pos_vector_path, frame_count)
        b_quaternions = evaluate_quaternion(action.fcurves, rot_quaternion_path, frame_count)
        b_euler_quaternions = evaluate_euler_to_quaternion(action.fcurves, rot_euler_path, frame_count)
        b_scales = evaluate_vector(action.fcurves, scale_vector_path, frame_count)
        
        # Link them with Bone ID

        if len(b_locations) > 0:
            locations[bone_id] = b_locations

        # Its a bit of a edge case scenario because blender uses either
        # euler or quaternion (I cant really understand why quaternion doesnt update with euler)
        # So we will prefer quaternion over euler for now
        if len(b_quaternions) > 0:
            rotations[bone_id] = b_quaternions
        elif len(b_euler_quaternions) > 0:
            rotations[bone_id] = b_euler_quaternions

        if len(b_scales) > 0:
            scales[bone_id] = b_scales

    if not is_ped_animation:
        for bone_id, positions in locations.items():
            p_bone = bones_map[bone_id]
            bone = p_bone.bone

            for frame_id, position in enumerate(positions):
                mat = bone.matrix_local

                if (bone.parent != None):
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

    for bone_id, quaternions in rotations.items():
        p_bone = bones_map[bone_id]
        bone = p_bone.bone

        for quaternion in quaternions:
            # 'Flickering bug' fix - killso:
            # This bug is caused by interpolation algorithm used in GTA
            # which is not Slerp, they directly interpolate Quaternion
            # values without taking actual rotation into account. 
            # (probably for optimization purposes)
            # So in usual scenario Q and -Q would represent the same
            # rotation but with different signs and Slerp will work just fine,
            # but in gta it will interpolate XYZW values and it will lead to
            # interpolating in 'different direction'.
            # Another problem here, is that mathutils functions like
            # rotate or any other that affect quaternion mess up the signs,
            # so i've made special functions for that, which check
            # quaternion direction before and after operation
            # and in case if it doesn't match - flip signs
            if p_bone.parent is not None:
                pose_rot = Matrix.to_quaternion(bone.matrix)
                rotate_preserve_sign(quaternion, pose_rot)

    if len(locations) > 0:
        sequence_items[get_track_id('location', action_type)] = locations

    if len(rotations) > 0:
        sequence_items[get_track_id('rotation_quaternion', action_type)] = rotations

    if len(scales) > 0:
        sequence_items[get_track_id('scale', action_type)] = scales


def build_values_channel(values, uniq_values, indirect_percentage=0.1):
    values_len_percentage = len(uniq_values) / len(values)

    if len(uniq_values) == 1:
        channel = ChannelsListProperty.StaticFloat()

        channel.value = uniq_values[0]
    elif values_len_percentage <= indirect_percentage:
        channel = ChannelsListProperty.IndirectQuantizeFloat()

        min_value, quantum = get_quantum_and_min_val(uniq_values)

        channel.values = uniq_values
        channel.offset = min_value
        channel.quantum = quantum

        for value in values:
            channel.frames.append(uniq_values.index(value))
    else:
        channel = ChannelsListProperty.QuantizeFloat()

        min_value, quantum = get_quantum_and_min_val(values)

        channel.values = values
        channel.offset = min_value
        channel.quantum = quantum

    return channel


def sequence_item_from_frames_data(track, frames_data):
    sequence_data = Animation.SequenceDataListProperty.SequenceData()

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
            channel = ChannelsListProperty.StaticVector3()
            channel.value = frames_data[0]

            sequence_data.channels.append(channel)
        else:
            sequence_data.channels.append(build_values_channel(values_x, uniq_x))
            sequence_data.channels.append(build_values_channel(values_y, uniq_y))
            sequence_data.channels.append(build_values_channel(values_z, uniq_z))
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
            channel = ChannelsListProperty.StaticQuaternion()
            channel.value = frames_data[0]

            sequence_data.channels.append(channel)
        else:
            sequence_data.channels.append(build_values_channel(values_x, uniq_x))
            sequence_data.channels.append(build_values_channel(values_y, uniq_y))
            sequence_data.channels.append(build_values_channel(values_z, uniq_z))
            sequence_data.channels.append(build_values_channel(values_w, uniq_w))

    return sequence_data


def animation_from_object(animation_obj, bones_name_map, bones_map, is_ped_animation):
    animation = Animation()

    animation_properties = animation_obj.animation_properties

    animation.hash = animation_properties.hash
    animation.frame_count = animation_properties.frame_count
    animation.sequence_frame_limit = animation_properties.frame_count + 30
    animation.duration = animation_properties.frame_count / bpy.context.scene.render.fps

    animation.unknown10 = 0
    animation.unknown1C = ''

    bone_groups = {}
    sequence_items = {}

    # TODO: Get it from sequence_items_from_action data
    if animation_properties.base_action:
        fill_bone_ids_from_action(animation_properties.base_action, bone_groups, bones_name_map, 'base')

    if animation_properties.root_motion_location_action:
        fill_bone_ids_from_action(animation_properties.root_motion_location_action, bone_groups, bones_name_map, 'root_motion')

    # if animation_properties.root_motion_rotation_action:
    #     bone_ids_from_action(animation_properties.root_motion_rotation_action, bone_groups, bones_name_map, 'root_motion')

    for track, bones in sorted(bone_groups.items()):
        for bone_id in sorted(bones, key=lambda bone_id: bone_id.bone_id):
            animation.bone_ids.append(bone_id)

        if track == 5 or track == 6:
            animation.unknown10 = 16

    action: Action
    action_type: str
    if animation_properties.base_action:
        action = animation_properties.base_action
        action_type = 'base'

    if animation_properties.root_motion_location_action:
        action = animation_properties.root_motion_location_action
        action_type = 'root_motion'

    if action is not None:
        sequence_items_from_action(
            action, sequence_items, bones_map, action_type, animation_properties.frame_count, is_ped_animation)

    # if animation_properties.root_motion_rotation_action:
    #     sequence_items_from_action(animation_properties.root_motion_rotation_action, sequence_items, bones_name_map,
    #                                bones_map, 'root_motion', animation_properties.frame_count, is_ped_animation)

    sequence = Animation.SequenceListProperty.Sequence()

    sequence.frame_count = animation_properties.frame_count
    sequence.hash = 'hash_' + hex(0)[2:].zfill(8)

    for track, bones_data in sorted(sequence_items.items()):
        for bone_id, frames_data in sorted(bones_data.items()):
            sequence_data = sequence_item_from_frames_data(track, frames_data)

            sequence.sequence_data.append(sequence_data)

    animation.sequences.append(sequence)

    return animation


def clip_from_object(clip_obj):
    clip_properties = clip_obj.clip_properties

    is_single_animation = len(clip_properties.animations) == 1

    if is_single_animation:
        clip = ClipsListProperty.ClipAnimation()
        clip_animation_property = clip_properties.animations[0]
        animation_properties = clip_animation_property.animation.animation_properties

        animation_duration = animation_properties.frame_count / bpy.context.scene.render.fps

        clip.animation_hash = animation_properties.hash
        clip.start_time = (clip_animation_property.start_frame / animation_properties.frame_count) * animation_duration
        clip.end_time = (clip_animation_property.end_frame / animation_properties.frame_count) * animation_duration

        clip_animation_duration = clip.end_time - clip.start_time
        clip.rate = clip_animation_duration / clip_properties.duration
    else:
        clip = ClipsListProperty.ClipAnimationList()
        clip.duration = clip_properties.duration

        for clip_animation_property in clip_properties.animations:
            clip_animation = ClipAnimationsListProperty.ClipAnimation()

            animation_properties = clip_animation_property.animation.animation_properties

            animation_duration = animation_properties.frame_count / bpy.context.scene.render.fps

            clip_animation.animation_hash = animation_properties.hash
            clip_animation.start_time = (clip_animation_property.start_frame / animation_properties.frame_count) * animation_duration
            clip_animation.end_time = (clip_animation_property.end_frame / animation_properties.frame_count) * animation_duration

            clip_animation_duration = clip_animation.end_time - clip_animation.start_time
            clip_animation.rate = clip_animation_duration / clip_properties.duration

            clip.animations.append(clip_animation)

    clip.hash = clip_properties.hash
    clip.name = clip_properties.name
    clip.unknown30 = 0

    return clip


def clip_dictionary_from_object(exportop, obj, exportpath, export_settings=None):
    clip_dictionary = ClipsDictionary()

    armature = obj.clip_dict_properties.armature
    armature_obj = get_armature_obj(armature)

    bones_name_map = build_name_bone_map(armature_obj)
    bones_map = build_bone_map(armature_obj)

    is_ped_animation = False

    for p_bone in armature_obj.pose.bones:
        if is_ped_bone_tag(p_bone.bone.bone_properties.tag):
            is_ped_animation = True
            break

    animations_obj = None
    clips_obj = None

    for child_obj in obj.children:
        if child_obj.sollum_type == SollumType.ANIMATIONS:
            animations_obj = child_obj
        elif child_obj.sollum_type == SollumType.CLIPS:
            clips_obj = child_obj

    for animation_obj in animations_obj.children:
        animation = animation_from_object(animation_obj, bones_name_map, bones_map, is_ped_animation)

        clip_dictionary.animations.append(animation)

    for clip_obj in clips_obj.children:
        clip = clip_from_object(clip_obj)

        clip_dictionary.clips.append(clip)

    return clip_dictionary


def export_ycd(exportop, obj, filepath, export_settings):
    clip_dictionary_from_object(exportop, obj, filepath, export_settings).write_xml(filepath)
