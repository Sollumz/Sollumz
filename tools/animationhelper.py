from sys import float_info
from mathutils import Quaternion

ped_bone_tags = [
    11816,
    57597,
    23553,
    24816,
    24817,
    24818,
    58866,
    64016,
    64017,
    58867,
    64096,
    64097,
    58868,
    64112,
    64113,
    58869,
    64064,
    64065,
    58870,
    64080,
    64081,
    26610,
    4089,
    4090,
    26611,
    4169,
    4170,
    26612,
    4185,
    26613,
    4137,
    4138,
    26614,
    4153,
    4154,
]

def is_ped_bone_tag(bone_tag):
    return bone_tag in ped_bone_tags

def rotate_preserve_sign(quaternion, by):
    quaternion_orig = quaternion.copy()
    Quaternion.rotate(quaternion, by)

    if Quaternion.dot(quaternion, quaternion_orig) < 0:
        quaternion *= -1

def rotation_difference_preserve_sign(quat_left, quat_right):
    diff = quat_left.rotation_difference(quat_right)

    if Quaternion.dot(diff, quat_right) < 0:
        diff *= -1

    return diff

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
