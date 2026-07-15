"""Bone fragment physics preset category."""

import bpy
from pathlib import Path

from ....shared.presets import (
    PresetCategory,
    register_preset_category,
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
)
from ....sollumz_properties import SollumType


def _is_fragment(context):
    obj = context.active_object
    return obj is not None and obj.sollum_type == SollumType.FRAGMENT


def _get_target(context):
    bone = context.active_bone
    if bone is None or not _is_fragment(context):
        return None
    return bone.group_properties


def _get_targets(context):
    """All selected bones' group properties. In pose mode this is every selected
    pose bone, otherwise it falls back to the active bone (there doesn't seem to
    be a way to get all bones selected in the outliner while in object mode).
    """
    if not _is_fragment(context):
        return []

    pose_bones = context.selected_pose_bones
    if pose_bones:
        bones = [pb.bone for pb in pose_bones]
    else:
        active = context.active_bone
        bones = [active] if active is not None else []

    seen = set()
    out = []
    for bone in bones:
        props = bone.group_properties
        key = id(props)
        if key in seen:
            continue
        seen.add(key)
        out.append(props)
    return out


def _poll(context):
    if _get_target(context) is None:
        return False, "Select a bone on a Sollumz fragment armature."
    return True, ""


BONE_FRAGMENT_PHYSICS_PRESET_CATEGORY = PresetCategory(
    id="bone_fragment_physics",
    label="Bone Physics",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "bone_fragment_physics_presets.json",
    get_target=_get_target,
    get_targets=_get_targets,
    poll=_poll,
)


register_preset_category(BONE_FRAGMENT_PHYSICS_PRESET_CATEGORY)


class SOLLUMZ_OT_save_bone_fragment_physics_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_bone_fragment_physics_preset"
    bl_label = "Save Bone Physics Preset"
    bl_description = "Save current bone group physics properties as a named preset"
    category = BONE_FRAGMENT_PHYSICS_PRESET_CATEGORY


class SOLLUMZ_OT_load_bone_fragment_physics_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_bone_fragment_physics_preset"
    bl_label = "Apply Bone Physics Preset"
    bl_description = "Apply a saved bone physics preset to the active bone"
    category = BONE_FRAGMENT_PHYSICS_PRESET_CATEGORY


class SOLLUMZ_OT_delete_bone_fragment_physics_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_bone_fragment_physics_preset"
    bl_label = "Delete Bone Physics Preset"
    bl_description = "Remove a saved bone physics preset"
    category = BONE_FRAGMENT_PHYSICS_PRESET_CATEGORY


class SOLLUMZ_PT_bone_fragment_physics_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Bone Physics Presets"

    category = BONE_FRAGMENT_PHYSICS_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_bone_fragment_physics_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_bone_fragment_physics_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_bone_fragment_physics_preset.bl_idname
