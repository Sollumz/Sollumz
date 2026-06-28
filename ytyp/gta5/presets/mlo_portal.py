"""MLO portal preset category."""
import bpy
from pathlib import Path

from ....shared.presets import (
    PresetCategory,
    register_preset_category,
    make_get_targets_from_collection,
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
)
from ...utils import get_selected_portal, get_selected_portals_collection


def _poll(context):
    if get_selected_portal(context) is None:
        return False, "Select a portal."
    return True, ""


MLO_PORTAL_PRESET_CATEGORY = PresetCategory(
    id="mlo_portal",
    label="Portal",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "mlo_portal_presets.json",
    get_target=get_selected_portal,
    get_targets=make_get_targets_from_collection(get_selected_portals_collection),
    poll=_poll,
)


register_preset_category(MLO_PORTAL_PRESET_CATEGORY)


class SOLLUMZ_OT_save_mlo_portal_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_mlo_portal_preset"
    bl_label = "Save Portal Preset"
    bl_description = "Save current portal properties as a named preset"
    category = MLO_PORTAL_PRESET_CATEGORY


class SOLLUMZ_OT_load_mlo_portal_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_mlo_portal_preset"
    bl_label = "Apply Portal Preset"
    bl_description = "Apply a saved portal preset to the active portal"
    category = MLO_PORTAL_PRESET_CATEGORY


class SOLLUMZ_OT_delete_mlo_portal_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_mlo_portal_preset"
    bl_label = "Delete Portal Preset"
    bl_description = "Remove a saved portal preset"
    category = MLO_PORTAL_PRESET_CATEGORY


class SOLLUMZ_PT_mlo_portal_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Portal Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = MLO_PORTAL_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_mlo_portal_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_mlo_portal_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_mlo_portal_preset.bl_idname
