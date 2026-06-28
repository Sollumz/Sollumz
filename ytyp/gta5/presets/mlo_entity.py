"""MLO entity preset operators + panel.
Presets shared with map entities.
"""
import bpy

from ....shared.presets import (
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
    make_get_targets_from_collection,
)
from ....ymap_next.gta5.presets.entity import ENTITY_PRESET_CATEGORY
from ...utils import get_selected_entity, get_selected_mlo_entities_collection


class SOLLUMZ_OT_save_mlo_entity_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_mlo_entity_preset"
    bl_label = "Save Entity Preset"
    bl_description = "Save current MLO entity properties as a named preset"
    category = ENTITY_PRESET_CATEGORY
    get_target = get_selected_entity

    @classmethod
    def poll(cls, context):
        if get_selected_entity(context) is None:
            cls.poll_message_set("Select an MLO entity.")
            return False
        return True


class SOLLUMZ_OT_load_mlo_entity_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_mlo_entity_preset"
    bl_label = "Apply Entity Preset"
    bl_description = "Apply a saved entity preset to the active MLO entity"
    category = ENTITY_PRESET_CATEGORY
    get_target = get_selected_entity
    get_targets = make_get_targets_from_collection(get_selected_mlo_entities_collection)

    @classmethod
    def poll(cls, context):
        if get_selected_entity(context) is None:
            cls.poll_message_set("Select an MLO entity.")
            return False
        return True


class SOLLUMZ_OT_delete_mlo_entity_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_mlo_entity_preset"
    bl_label = "Delete Entity Preset"
    bl_description = "Remove a saved entity preset"
    category = ENTITY_PRESET_CATEGORY


class SOLLUMZ_PT_mlo_entity_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Entity Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = ENTITY_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_mlo_entity_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_mlo_entity_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_mlo_entity_preset.bl_idname
