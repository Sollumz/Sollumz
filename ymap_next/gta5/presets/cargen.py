"""Car generator preset category for map cargens."""

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
from ...context import active_cargen, active_cargens_collection

# Per-instance / display fields skipped from templating.
_SKIP_FIELDS = (
    "name",
    "ui_label",
    "linked_collection",
    "uuid",
    "uuid_str",
    "map_group_uuid",
    "map_data_uuid",
    "map_data_name",
)


def _poll(context):
    if active_cargen(context) is None:
        return False, "Select a car generator."
    return True, ""


CARGEN_PRESET_CATEGORY = PresetCategory(
    id="cargen",
    label="Car Generator",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "cargen_presets.json",
    skip=_SKIP_FIELDS,
    get_target=active_cargen,
    get_targets=make_get_targets_from_collection(active_cargens_collection),
    poll=_poll,
)


register_preset_category(CARGEN_PRESET_CATEGORY)


class SOLLUMZ_OT_save_cargen_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_cargen_preset"
    bl_label = "Save Car Generator Preset"
    bl_description = "Save current car generator properties as a named preset"
    category = CARGEN_PRESET_CATEGORY


class SOLLUMZ_OT_load_cargen_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_cargen_preset"
    bl_label = "Apply Car Generator Preset"
    bl_description = "Apply a saved car generator preset"
    category = CARGEN_PRESET_CATEGORY


class SOLLUMZ_OT_delete_cargen_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_cargen_preset"
    bl_label = "Delete Car Generator Preset"
    bl_description = "Remove a saved car generator preset"
    category = CARGEN_PRESET_CATEGORY


class SOLLUMZ_PT_cargen_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Car Generator Presets"

    category = CARGEN_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_cargen_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_cargen_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_cargen_preset.bl_idname
