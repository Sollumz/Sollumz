import bpy
from typing import Optional
from mathutils import Matrix
from szio.gta5 import Skeleton, SkelBone, SkelBoneFlags, SkelBoneRotationLimit, SkelBoneTranslationLimit

def create_drawable_skel(armature_obj: bpy.types.Object, skeleton: Skeleton):
    bpy.context.view_layer.objects.active = armature_obj
    bones = skeleton.bones

    # Need to go into edit mode to modify edit bones
    bpy.ops.object.mode_set(mode="EDIT")

    bone_names = []
    for b in bones:
        blender_name = add_bone(armature_obj.data, b)
        bone_names.append(blender_name)

    bpy.ops.object.mode_set(mode="OBJECT")

    for b, blender_name in zip(bones, bone_names):
        set_bone_properties(armature_obj.data, b, blender_name)
        add_bone_constraints(armature_obj, b, blender_name)

    return armature_obj


def add_bone(armature: bpy.types.Armature, bone: SkelBone) -> str:
    edit_bone = armature.edit_bones.new(bone.name)
    if bone.parent_index != -1:
        edit_bone.parent = armature.edit_bones[bone.parent_index]

    # https://github.com/LendoK/Blender_GTA_V_model_importer/blob/master/importer.py
    mat_rot = bone.rotation.to_matrix().to_4x4()
    mat_loc = Matrix.Translation(bone.position)
    mat_sca = Matrix.Scale(1, 4, bone.scale)

    edit_bone.head = (0, 0, 0)
    edit_bone.tail = (0, 0.05, 0)
    edit_bone.matrix = mat_loc @ mat_rot @ mat_sca

    if edit_bone.parent is not None:
        edit_bone.matrix = edit_bone.parent.matrix @ edit_bone.matrix
    
    return edit_bone.name


def set_bone_properties(armature: bpy.types.Armature, bone: SkelBone, blender_name: str):
    bl_bone = armature.bones[blender_name]
    bl_bone.bone_properties.tag = bone.tag

    # Store original name if it was changed (e.g. truncated)
    if blender_name != bone.name:
        bl_bone.bone_properties.original_name = bone.name

    for _flag in bone.flags:
        # LimitRotation and Unk0 have their special meanings, can be deduced if needed when exporting
        if _flag & (SkelBoneFlags.HAS_ROTATE_LIMITS | SkelBoneFlags.HAS_CHILD):
            continue

        # flags still use the CW names for backwards compatibility
        from szio.gta5.cwxml.adapters.drawable import CW_BONE_FLAGS_INVERSE_MAP
        flag = bl_bone.bone_properties.flags.add()
        flag.name = CW_BONE_FLAGS_INVERSE_MAP[_flag]


def add_bone_constraints(armature_obj: bpy.types.Object, bone: SkelBone, blender_name: str):
    pose_bone = armature_obj.pose.bones[blender_name]

    if bone.translation_limit:
        add_bone_constraint_translation_limit(pose_bone, bone.translation_limit)

    if bone.rotation_limit:
        add_bone_constraint_rotation_limit(pose_bone, bone.rotation_limit)


def add_bone_constraint_rotation_limit(pose_bone: bpy.types.PoseBone, limit: SkelBoneRotationLimit) -> bpy.types.LimitRotationConstraint:
    constraint = pose_bone.constraints.new("LIMIT_ROTATION")
    constraint.owner_space = "LOCAL"
    constraint.use_limit_x = True
    constraint.use_limit_y = True
    constraint.use_limit_z = True
    constraint.max_x = limit.max.x
    constraint.max_y = limit.max.y
    constraint.max_z = limit.max.z
    constraint.min_x = limit.min.x
    constraint.min_y = limit.min.y
    constraint.min_z = limit.min.z
    return constraint


def add_bone_constraint_translation_limit(pose_bone: bpy.types.PoseBone, limit: SkelBoneTranslationLimit) -> bpy.types.LimitLocationConstraint:
    constraint = pose_bone.constraints.new("LIMIT_LOCATION")
    constraint.owner_space = "LOCAL"
    constraint.use_min_x = True
    constraint.use_min_y = True
    constraint.use_min_z = True
    constraint.use_max_x = True
    constraint.use_max_y = True
    constraint.use_max_z = True
    constraint.max_x = limit.max.x
    constraint.max_y = limit.max.y
    constraint.max_z = limit.max.z
    constraint.min_x = limit.min.x
    constraint.min_y = limit.min.y
    constraint.min_z = limit.min.z
    return constraint
