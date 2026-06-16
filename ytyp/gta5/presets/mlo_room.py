"""MLO rooms preset category."""
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
from ...utils import get_selected_room


def _poll(context):
    if get_selected_room(context) is None:
        return False, "Select a room."
    return True, ""


MLO_ROOM_PRESET_CATEGORY = PresetCategory(
    id="mlo_room",
    label="Room",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "mlo_room_presets.json",
    get_target=get_selected_room,
    poll=_poll,
)


register_preset_category(MLO_ROOM_PRESET_CATEGORY)


class SOLLUMZ_OT_save_mlo_room_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_mlo_room_preset"
    bl_label = "Save Room Preset"
    bl_description = "Save current room properties as a named preset"
    category = MLO_ROOM_PRESET_CATEGORY


class SOLLUMZ_OT_load_mlo_room_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_mlo_room_preset"
    bl_label = "Apply Room Preset"
    bl_description = "Apply a saved room preset to the active room"
    category = MLO_ROOM_PRESET_CATEGORY


class SOLLUMZ_OT_delete_mlo_room_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_mlo_room_preset"
    bl_label = "Delete Room Preset"
    bl_description = "Remove a saved room preset"
    category = MLO_ROOM_PRESET_CATEGORY


class SOLLUMZ_PT_mlo_room_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Room Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = MLO_ROOM_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_mlo_room_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_mlo_room_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_mlo_room_preset.bl_idname
