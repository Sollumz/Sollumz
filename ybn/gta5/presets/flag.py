"""
Flag preset category.

Target is a bound Object with two `composite_flags1` / `composite_flags2`
FlagPropertyGroup pointers. JSON format keeps a sparse dict per group so
unset flags don't appear in the file:

    {"composite_flags1": {"map_animal": true, ...}, "composite_flags2": {...}}
"""

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
from ....shared.presets import migration
from ....sollumz_properties import BOUND_TYPES


# Default preset applied when none is otherwise specified (create-bound, etc).
DEFAULT_FLAG_PRESET_NAME = "General (Default)"


def _capture(target):
    obj = target
    flag_names = list(type(obj.composite_flags1).__annotations__.keys())
    return {
        "composite_flags1": {n: True for n in flag_names if getattr(obj.composite_flags1, n)},
        "composite_flags2": {n: True for n in flag_names if getattr(obj.composite_flags2, n)},
    }


def _apply(target, data, **opts):
    obj = target
    flag_names = list(type(obj.composite_flags1).__annotations__.keys())
    f1 = data.get("composite_flags1") or {}
    f2 = data.get("composite_flags2") or {}
    for n in flag_names:
        setattr(obj.composite_flags1, n, bool(f1.get(n, False)))
        setattr(obj.composite_flags2, n, bool(f2.get(n, False)))


def _target_from_obj(obj):
    if obj is None or obj.sollum_type not in BOUND_TYPES:
        return None
    return obj


def _get_target(context):
    return _target_from_obj(context.active_object)


def _poll(context):
    obj = context.active_object
    if obj is None or obj.sollum_type not in BOUND_TYPES:
        return False, "Select a Sollumz bound."
    return True, ""


FLAG_PRESET_CATEGORY = PresetCategory(
    id="flag",
    label="Flag",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "flag_presets.json",
    blacklist=frozenset(
        {
            "General (Default)",
            "General 2",
            "Water surface",
            "Leaves - Bush",
            "Stair plane",
            "Stair mesh",
            "Deep surface",
        }
    ),
    get_target=_get_target,
    get_targets=make_get_targets_from_objects(_target_from_obj),
    poll=_poll,
    capture_fn=_capture,
    apply_fn=_apply,
)


def _convert_legacy_xml(xml_path):
    import xml.etree.ElementTree as ET

    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    presets = []
    for item in root.iterfind(".//Item"):
        name = item.get("name", "")
        if not name:
            continue
        f1 = _read_flag_list(item.find("Flags1"))
        f2 = _read_flag_list(item.find("Flags2"))
        data = {
            "composite_flags1": {n: True for n in f1},
            "composite_flags2": {n: True for n in f2},
        }
        presets.append({"name": name, "data": data})
    return presets


def _read_flag_list(elem):
    if elem is None:
        return []
    # Legacy szio.xml `FlagsProperty` serializes as a comma-separated list of
    # flag names in the element text.
    names = []
    if elem.text:
        for part in elem.text.split(","):
            part = part.strip()
            if part:
                names.append(part)
    return names


register_preset_category(FLAG_PRESET_CATEGORY)
migration.register_legacy_migration(FLAG_PRESET_CATEGORY, _convert_legacy_xml)


class SOLLUMZ_OT_save_flag_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_flag_preset"
    bl_label = "Save Flag Preset"
    bl_description = "Save current bound flags as a named preset"
    category = FLAG_PRESET_CATEGORY


class SOLLUMZ_OT_load_flag_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_flag_preset"
    bl_label = "Apply Flag Preset"
    bl_description = "Apply a saved flag preset to the active bound"
    category = FLAG_PRESET_CATEGORY


class SOLLUMZ_OT_delete_flag_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_flag_preset"
    bl_label = "Delete Flag Preset"
    bl_description = "Remove a saved flag preset"
    category = FLAG_PRESET_CATEGORY


class SOLLUMZ_PT_flag_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Flag Presets"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"INSTANCED"}

    category = FLAG_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_flag_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_flag_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_flag_preset.bl_idname
