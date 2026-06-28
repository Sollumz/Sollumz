"""Collision material preset category."""

import bpy
from pathlib import Path

from ....shared.presets import (
    PresetCategory,
    register_preset_category,
    make_get_targets_from_objects,
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
)
from ....sollumz_properties import MaterialType


def _capture(target):
    mat = target
    props = mat.collision_properties
    flags = mat.collision_flags
    prop_names = ("procedural_id", "ped_density")
    flag_names = list(type(flags).__annotations__.keys())
    return {
        "props": {n: getattr(props, n) for n in prop_names},
        "flags": {n: True for n in flag_names if getattr(flags, n)},
    }


def _apply(target, data, **opts):
    mat = target
    props = mat.collision_properties
    flags = mat.collision_flags
    prop_names = ("procedural_id", "ped_density")
    flag_names = list(type(flags).__annotations__.keys())
    data_props = data.get("props") or {}
    data_flags = data.get("flags") or {}
    for n in prop_names:
        if n in data_props:
            setattr(props, n, data_props[n])
    for n in flag_names:
        setattr(flags, n, bool(data_flags.get(n, False)))


def _target_from_obj(obj):
    if obj is None:
        return None
    mat = obj.active_material
    if mat is None or mat.sollum_type != MaterialType.COLLISION:
        return None
    return mat


def _get_target(context):
    return _target_from_obj(context.active_object)


def _poll(context):
    obj = context.active_object
    if obj is None:
        return False, "Select an object with a Sollumz collision material."
    mat = obj.active_material
    if mat is None or mat.sollum_type != MaterialType.COLLISION:
        return False, "Active material is not a Sollumz collision material."
    return True, ""


COLLISION_MATERIAL_PRESET_CATEGORY = PresetCategory(
    id="collision_material",
    label="Collision Material",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "collision_material_presets.json",
    get_target=_get_target,
    get_targets=make_get_targets_from_objects(_target_from_obj),
    poll=_poll,
    capture_fn=_capture,
    apply_fn=_apply,
)

register_preset_category(COLLISION_MATERIAL_PRESET_CATEGORY)


class SOLLUMZ_OT_save_collision_material_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_collision_material_preset"
    bl_label = "Save Collision Material"
    bl_description = "Save current material collision properties as a named preset"
    category = COLLISION_MATERIAL_PRESET_CATEGORY


class SOLLUMZ_OT_load_collision_material_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_collision_material_preset"
    bl_label = "Apply Collision Material"
    bl_description = "Apply a saved collision material preset to the active material"
    category = COLLISION_MATERIAL_PRESET_CATEGORY


class SOLLUMZ_OT_delete_collision_material_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_collision_material_preset"
    bl_label = "Delete Collision Material"
    bl_description = "Remove a saved collision material preset"
    category = COLLISION_MATERIAL_PRESET_CATEGORY


class SOLLUMZ_PT_collision_material_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Collision Material Presets"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"INSTANCED"}

    category = COLLISION_MATERIAL_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_collision_material_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_collision_material_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_collision_material_preset.bl_idname
