"""MLO timecycle modifier preset operators + panel.
Presets shared with map timecycle modifiers.
"""
import bpy

from ....shared.presets import (
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
    make_get_targets_from_collection,
)
from ....ymap_next.gta5.presets.timecycle_modifier import TIMECYCLE_MODIFIER_PRESET_CATEGORY
from ...utils import get_selected_tcm, get_selected_tcms_collection


class SOLLUMZ_OT_save_mlo_timecycle_modifier_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_mlo_timecycle_modifier_preset"
    bl_label = "Save Timecycle Modifier Preset"
    bl_description = "Save current timecycle modifier properties as a named preset"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY
    get_target = get_selected_tcm

    @classmethod
    def poll(cls, context):
        if get_selected_tcm(context) is None:
            cls.poll_message_set("Select a timecycle modifier.")
            return False
        return True


class SOLLUMZ_OT_load_mlo_timecycle_modifier_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_mlo_timecycle_modifier_preset"
    bl_label = "Apply Timecycle Modifier Preset"
    bl_description = "Apply a saved timecycle modifier preset"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY
    get_target = get_selected_tcm
    get_targets = make_get_targets_from_collection(get_selected_tcms_collection)

    @classmethod
    def poll(cls, context):
        if get_selected_tcm(context) is None:
            cls.poll_message_set("Select a timecycle modifier.")
            return False
        return True


class SOLLUMZ_OT_delete_mlo_timecycle_modifier_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_mlo_timecycle_modifier_preset"
    bl_label = "Delete Timecycle Modifier Preset"
    bl_description = "Remove a saved timecycle modifier preset"
    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY


class SOLLUMZ_PT_mlo_timecycle_modifier_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Timecycle Modifier Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = TIMECYCLE_MODIFIER_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_mlo_timecycle_modifier_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_mlo_timecycle_modifier_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_mlo_timecycle_modifier_preset.bl_idname
