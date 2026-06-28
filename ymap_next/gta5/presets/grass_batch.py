"""Grass batch preset category for map grass batches.

Captures the list of templates of the currently active grass batch.
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
from ...context import active_grass_batch, active_grass_batches_collection


def _poll(context):
    if active_grass_batch(context) is None:
        return False, "Select a grass batch."
    return True, ""


GRASS_BATCH_PRESET_CATEGORY = PresetCategory(
    id="grass_batch",
    label="Grass Batch",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "grass_batch_presets.json",
    get_target=active_grass_batch,
    get_targets=make_get_targets_from_collection(active_grass_batches_collection),
    poll=_poll,
)


register_preset_category(GRASS_BATCH_PRESET_CATEGORY)


class SOLLUMZ_OT_save_grass_batch_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_grass_batch_preset"
    bl_label = "Save Grass Batch Preset"
    bl_description = "Save current grass batch settings as a named preset"
    category = GRASS_BATCH_PRESET_CATEGORY


class SOLLUMZ_OT_load_grass_batch_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_grass_batch_preset"
    bl_label = "Apply Grass Batch Preset"
    bl_description = "Apply a saved grass batch preset"
    category = GRASS_BATCH_PRESET_CATEGORY


class SOLLUMZ_OT_delete_grass_batch_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_grass_batch_preset"
    bl_label = "Delete Grass Batch Preset"
    bl_description = "Remove a saved grass batch preset"
    category = GRASS_BATCH_PRESET_CATEGORY


class SOLLUMZ_PT_grass_batch_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Grass Batch Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = GRASS_BATCH_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_grass_batch_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_grass_batch_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_grass_batch_preset.bl_idname
