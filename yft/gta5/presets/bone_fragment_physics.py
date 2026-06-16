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


def _get_target(context):
    bone = getattr(context, "active_bone", None)
    obj = context.active_object
    if bone is None or obj is None:
        return None
    if obj.sollum_type != SollumType.FRAGMENT:
        return None
    return bone.group_properties


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
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"INSTANCED"}

    category = BONE_FRAGMENT_PHYSICS_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_bone_fragment_physics_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_bone_fragment_physics_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_bone_fragment_physics_preset.bl_idname
