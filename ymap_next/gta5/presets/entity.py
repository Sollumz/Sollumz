"""Entity preset category.
This category is shared between map entities and MLO entities.
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
from ....shared.presets.serializer import dict_to_struct, struct_to_dict
from ...context import active_entities_collection, active_entity

_LOD_LEVEL_TO_MLO = {
    "HD": "sollumz_lodtypes_depth_hd",
    "LOD": "sollumz_lodtypes_depth_lod",
    "SLOD1": "sollumz_lodtypes_depth_slod1",
    "SLOD2": "sollumz_lodtypes_depth_slod2",
    "SLOD3": "sollumz_lodtypes_depth_slod3",
    "SLOD4": "sollumz_lodtypes_depth_slod4",
}
_LOD_LEVEL_TO_MAP = {v: k for k, v in _LOD_LEVEL_TO_MLO.items()}
_LOD_LEVEL_TO_MAP["sollumz_lodtypes_depth_orphanhd"] = "HD"

_PRIORITY_TO_MLO = {
    "REQUIRED": "sollumz_pri_required",
    "OPTIONAL_HIGH": "sollumz_pri_optional_high",
    "OPTIONAL_MEDIUM": "sollumz_pri_optional_medium",
    "OPTIONAL_LOW": "sollumz_pri_optional_low",
}
_PRIORITY_TO_MAP = {v: k for k, v in _PRIORITY_TO_MLO.items()}


def _is_mlo_entity(target):
    from ....ytyp.properties.mlo import MloEntityProperties

    return isinstance(target, MloEntityProperties)


def _entity_capture(target):
    data = struct_to_dict(target)
    if _is_mlo_entity(target):
        # Normalize to canonical form (map enums) so presets can be used in both maps and MLOs.
        if "lod_level" in data:
            data["lod_level"] = _LOD_LEVEL_TO_MAP.get(data["lod_level"], data["lod_level"])
        if "priority_level" in data:
            data["priority_level"] = _PRIORITY_TO_MAP.get(data["priority_level"], data["priority_level"])

        # MLO entities store these values as floats but are actually ints...
        if "ambient_occlusion_multiplier" in data:
            data["ambient_occlusion_multiplier"] = int(data["ambient_occlusion_multiplier"])
        if "artificial_ambient_occlusion" in data:
            data["artificial_ambient_occlusion"] = int(data["artificial_ambient_occlusion"])
        if "tint_value" in data:
            data["tint_value"] = int(data["tint_value"])

    return data


def _entity_apply(target, data, **opts):
    if _is_mlo_entity(target):
        data = dict(data)
        if "lod_level" in data:
            data["lod_level"] = _LOD_LEVEL_TO_MLO.get(data["lod_level"], data["lod_level"])
        if "priority_level" in data:
            data["priority_level"] = _PRIORITY_TO_MLO.get(data["priority_level"], data["priority_level"])
    dict_to_struct(target, data)


def _poll(context):
    if active_entity(context) is None:
        return False, "Select a map entity."
    return True, ""


ENTITY_PRESET_CATEGORY = PresetCategory(
    id="entity",
    label="Entity",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "entity_presets.json",
    get_target=active_entity,
    get_targets=make_get_targets_from_collection(active_entities_collection),
    poll=_poll,
    capture_fn=_entity_capture,
    apply_fn=_entity_apply,
)


register_preset_category(ENTITY_PRESET_CATEGORY)


class SOLLUMZ_OT_save_entity_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_entity_preset"
    bl_label = "Save Entity Preset"
    bl_description = "Save current entity properties as a named preset"
    category = ENTITY_PRESET_CATEGORY


class SOLLUMZ_OT_load_entity_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_entity_preset"
    bl_label = "Apply Entity Preset"
    bl_description = "Apply a saved entity preset to the active entity"
    category = ENTITY_PRESET_CATEGORY


class SOLLUMZ_OT_delete_entity_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_entity_preset"
    bl_label = "Delete Entity Preset"
    bl_description = "Remove a saved entity preset"
    category = ENTITY_PRESET_CATEGORY


class SOLLUMZ_PT_entity_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Entity Presets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"INSTANCED"}

    category = ENTITY_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_entity_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_entity_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_entity_preset.bl_idname
