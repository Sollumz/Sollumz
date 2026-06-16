"""Archetype preset category."""
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
from ...utils import get_selected_archetype


def _poll(context):
    if get_selected_archetype(context) is None:
        return False, "Select an archetype."
    return True, ""


ARCHETYPE_PRESET_CATEGORY = PresetCategory(
    id="archetype",
    label="Archetype",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "archetype_presets.json",
    get_target=get_selected_archetype,
    poll=_poll,
)


register_preset_category(ARCHETYPE_PRESET_CATEGORY)


class SOLLUMZ_OT_save_archetype_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_archetype_preset"
    bl_label = "Save Archetype Preset"
    bl_description = "Save current archetype properties as a named preset"
    category = ARCHETYPE_PRESET_CATEGORY


class SOLLUMZ_OT_load_archetype_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_archetype_preset"
    bl_label = "Apply Archetype Preset"
    bl_description = "Apply a saved archetype preset to the active archetype"
    category = ARCHETYPE_PRESET_CATEGORY


class SOLLUMZ_OT_delete_archetype_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_archetype_preset"
    bl_label = "Delete Archetype Preset"
    bl_description = "Remove a saved archetype preset"
    category = ARCHETYPE_PRESET_CATEGORY


class SOLLUMZ_PT_archetype_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Archetype Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = ARCHETYPE_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_archetype_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_archetype_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_archetype_preset.bl_idname
