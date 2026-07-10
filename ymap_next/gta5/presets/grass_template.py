"""Grass template preset category for map grass batches.

Captures the per-template settings (lod distances, spawn weight, orient-to-
terrain factor) of the currently active grass template inside the active
grass batch.
"""

from pathlib import Path

import bpy

from ....shared.presets import (
    PresetCategory,
    PresetDeleteOperatorBase,
    PresetLoadOperatorBase,
    PresetPanel,
    PresetSaveOperatorBase,
    make_get_targets_from_collection,
    register_preset_category,
)
from ...context import active_grass_template, active_grass_templates_collection


def _poll(context):
    if active_grass_template(context) is None:
        return False, "Select a grass template."
    return True, ""


GRASS_TEMPLATE_PRESET_CATEGORY = PresetCategory(
    id="grass_template",
    label="Grass Template",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "grass_template_presets.json",
    get_target=active_grass_template,
    get_targets=make_get_targets_from_collection(active_grass_templates_collection),
    poll=_poll,
)


register_preset_category(GRASS_TEMPLATE_PRESET_CATEGORY)


class SOLLUMZ_OT_save_grass_template_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_grass_template_preset"
    bl_label = "Save Grass Template Preset"
    bl_description = "Save current grass template settings as a named preset"
    category = GRASS_TEMPLATE_PRESET_CATEGORY


class SOLLUMZ_OT_load_grass_template_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_grass_template_preset"
    bl_label = "Apply Grass Template Preset"
    bl_description = "Apply a saved grass template preset"
    category = GRASS_TEMPLATE_PRESET_CATEGORY


class SOLLUMZ_OT_delete_grass_template_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_grass_template_preset"
    bl_label = "Delete Grass Template Preset"
    bl_description = "Remove a saved grass template preset"
    category = GRASS_TEMPLATE_PRESET_CATEGORY


class SOLLUMZ_PT_grass_template_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Grass Template Presets"

    category = GRASS_TEMPLATE_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_grass_template_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_grass_template_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_grass_template_preset.bl_idname
