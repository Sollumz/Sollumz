"""Timecycle modifier preset category for map timecycle modifiers."""

from pathlib import Path

import bpy

from ....shared.presets import (
    PresetCategory,
    PresetDeleteOperatorBase,
    PresetLoadOperatorBase,
    PresetPanel,
    PresetSaveOperatorBase,
    register_preset_category,
)
from ...context import active_tcm


def _poll(context):
    if active_tcm(context) is None:
        return False, "Select a timecycle modifier."
    return True, ""


TIMECYCLE_MODIFIER_PRESET_CATEGORY = PresetCategory(
    id="timecycle_modifier",
    label="Timecycle Modifier",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "timecycle_modifier_presets.json",
    get_target=active_tcm,
    poll=_poll,
)


register_preset_category(TIMECYCLE_MODIFIER_PRESET_CATEGORY)


class SOLLUMZ_OT_save_timecycle_modifier_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_timecycle_modifier_preset"
    bl_label = "Save Timecycle Modifier Preset"
    bl_description = "Save current timecycle modifier properties as a named preset"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY


class SOLLUMZ_OT_load_timecycle_modifier_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_timecycle_modifier_preset"
    bl_label = "Apply Timecycle Modifier Preset"
    bl_description = "Apply a saved timecycle modifier preset"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY


class SOLLUMZ_OT_delete_timecycle_modifier_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_timecycle_modifier_preset"
    bl_label = "Delete Timecycle Modifier Preset"
    bl_description = "Remove a saved timecycle modifier preset"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY


class SOLLUMZ_PT_timecycle_modifier_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Timecycle Modifier Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_timecycle_modifier_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_timecycle_modifier_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_timecycle_modifier_preset.bl_idname
