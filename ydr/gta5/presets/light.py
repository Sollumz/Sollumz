"""
Light preset category.

Captures the dual-target data of a Sollumz light: standard Blender Light
fields (color, energy, spot size, etc.) plus the Sollumz `light_properties`
PointerProperty plus the `time_flags`/`light_flags` totals.
"""

import bpy
from pathlib import Path

from ....shared.presets import (
    PresetCategory,
    register_preset_category,
    struct_to_dict,
    dict_to_struct,
    make_get_targets_from_objects,
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
    PresetPanel,
)
from ....shared.presets import migration
from ....sollumz_properties import SollumType


# Standard Blender Light fields included in the preset. Spot-only fields are
# captured only when the light is a Spot.
_LIGHT_FIELDS_COMMON = (
    "color",
    "energy",
    "cutoff_distance",
    "shadow_soft_size",
    "volume_factor",
    "shadow_buffer_clip_start",
)
_LIGHT_FIELDS_SPOT = ("spot_size", "spot_blend")

# `cone_outer_angle` / `cone_inner_angle` are LightProperties setters that
# forward to `bpy.types.Light.spot_size`, which only exists on SpotLights.
# We already capture `spot_size` directly in the light section, so skip these
# aliases to avoid triggering AttributeError on Point/Capsule applies.
_LIGHT_PROPERTIES_SKIP = ("cone_outer_angle", "cone_inner_angle")


def _to_list(value):
    """Coerce Color/Vector/array-like to a JSON-serializable list."""
    try:
        return [float(c) for c in value]
    except TypeError:
        return value


def _capture(target):
    light = target
    light_section = {}
    for key in _LIGHT_FIELDS_COMMON:
        value = getattr(light, key)
        light_section[key] = _to_list(value) if key == "color" else value
    if light.type == "SPOT":
        for key in _LIGHT_FIELDS_SPOT:
            light_section[key] = getattr(light, key)
    return {
        "light": light_section,
        "time_flags": light.time_flags.total,
        "light_flags": light.light_flags.total,
        "light_properties": struct_to_dict(light.light_properties, skip=_LIGHT_PROPERTIES_SKIP),
    }


def _apply(target, data, **opts):
    light = target

    light_section = data.get("light") or {}
    for key, value in light_section.items():
        # Skip fields not present on this light type (e.g. spot_size on a Point).
        if not hasattr(light, key):
            continue
        try:
            setattr(light, key, value)
        except (TypeError, ValueError):
            pass

    if "time_flags" in data:
        light.time_flags.total = str(data["time_flags"])
    if "light_flags" in data:
        light.light_flags.total = str(data["light_flags"])

    light_props_section = data.get("light_properties")
    if isinstance(light_props_section, dict):
        dict_to_struct(light.light_properties, light_props_section, skip=_LIGHT_PROPERTIES_SKIP)


def _target_from_obj(obj):
    if obj is None or obj.type != "LIGHT":
        return None
    if getattr(obj, "sollum_type", None) != SollumType.LIGHT:
        return None
    return obj.data


def _get_target(context):
    return _target_from_obj(context.active_object)


def _poll(context):
    obj = context.active_object
    if obj is None or obj.type != "LIGHT":
        return False, "Select a Sollumz light."
    if getattr(obj, "sollum_type", None) != SollumType.LIGHT:
        return False, "Selected object is not a Sollumz light."
    return True, ""


LIGHT_PRESET_CATEGORY = PresetCategory(
    id="light",
    label="Light",
    game="gta5",
    bundled_defaults_path=Path(__file__).parent / "light_presets.json",
    blacklist=frozenset(
        {
            "Default",
            "Point: Wall Light 1",
            "Spot: Wall Light 1",
            "Point: Wall Light 2",
            "Spot: Wall Light 2",
            "Spot: Streetlight 1",
        }
    ),
    get_target=_get_target,
    get_targets=make_get_targets_from_objects(_target_from_obj),
    poll=_poll,
    capture_fn=_capture,
    apply_fn=_apply,
)


def _value(elem, tag, default=0.0):
    """Read `<tag value="..."/>` as a float."""
    child = elem.find(tag)
    if child is None:
        return default
    try:
        return float(child.get("value", default))
    except (TypeError, ValueError):
        return default


def _vec_elem(elem, tag):
    """Read `<tag x="..." y="..." z="..."/>` as [x, y, z]."""
    child = elem.find(tag)
    if child is None:
        return [0.0, 0.0, 0.0]
    try:
        return [float(child.get("x", 0)), float(child.get("y", 0)), float(child.get("z", 0))]
    except (TypeError, ValueError):
        return [0.0, 0.0, 0.0]


def _text(elem, tag, default=""):
    child = elem.find(tag)
    if child is None or child.text is None:
        return default
    return child.text.strip()


def _convert_legacy_xml(xml_path):
    import xml.etree.ElementTree as ET

    tree = ET.parse(str(xml_path))
    root = tree.getroot()
    presets = []
    for item in root.iterfind(".//Item"):
        data = {
            "light": {
                "color": _vec_elem(item, "Color"),
                "energy": _value(item, "Energy"),
                "cutoff_distance": _value(item, "CutoffDistance"),
                "shadow_soft_size": _value(item, "ShadowSoftSize"),
                "volume_factor": _value(item, "VolumeFactor"),
                "shadow_buffer_clip_start": _value(item, "ShadowBufferClipStart"),
                "spot_size": _value(item, "SpotSize"),
                "spot_blend": _value(item, "SpotBlend"),
            },
            "time_flags": str(int(_value(item, "TimeFlags", 0))),
            "light_flags": str(int(_value(item, "Flags", 0))),
            "light_properties": {
                "projected_texture_hash": _text(item, "ProjectedTextureHash"),
                "flashiness": _text(item, "Flashiness"),
                "volume_size_scale": _value(item, "VolumeSizeScale"),
                "volume_outer_color": _vec_elem(item, "VolumeOuterColor"),
                "volume_outer_intensity": _value(item, "VolumeOuterIntensity"),
                "volume_outer_exponent": _value(item, "VolumeOuterExponent"),
                "light_fade_distance": _value(item, "LightFadeDistance"),
                "shadow_fade_distance": _value(item, "ShadowFadeDistance"),
                "specular_fade_distance": _value(item, "SpecularFadeDistance"),
                "volumetric_fade_distance": _value(item, "VolumetricFadeDistance"),
                "culling_plane_normal": _vec_elem(item, "CullingPlaneNormal"),
                "culling_plane_offset": _value(item, "CullingPlaneOffset"),
                "corona_size": _value(item, "CoronaSize"),
                "corona_intensity": _value(item, "CoronaIntensity"),
                "corona_z_bias": _value(item, "CoronaZBias"),
                "shadow_blur": _value(item, "ShadowBlur"),
                "extent": _vec_elem(item, "Extent"),
            },
        }
        name = item.get("name", "")
        if name:
            presets.append({"name": name, "data": data})
    return presets


register_preset_category(LIGHT_PRESET_CATEGORY)
migration.register_legacy_migration(LIGHT_PRESET_CATEGORY, _convert_legacy_xml)


class SOLLUMZ_OT_save_light_preset(PresetSaveOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.save_light_preset"
    bl_label = "Save Light Preset"
    bl_description = "Save current light settings as a named preset"
    category = LIGHT_PRESET_CATEGORY


class SOLLUMZ_OT_load_light_preset(PresetLoadOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.load_light_preset"
    bl_label = "Apply Light Preset"
    bl_description = "Apply a saved light preset to the active light"
    category = LIGHT_PRESET_CATEGORY


class SOLLUMZ_OT_delete_light_preset(PresetDeleteOperatorBase, bpy.types.Operator):
    bl_idname = "sollumz.delete_light_preset"
    bl_label = "Delete Light Preset"
    bl_description = "Remove a saved light preset"
    category = LIGHT_PRESET_CATEGORY


class SOLLUMZ_PT_light_presets(PresetPanel, bpy.types.Panel):
    bl_label = "Light Presets"

    category = LIGHT_PRESET_CATEGORY
    save_operator = SOLLUMZ_OT_save_light_preset.bl_idname
    load_operator = SOLLUMZ_OT_load_light_preset.bl_idname
    delete_operator = SOLLUMZ_OT_delete_light_preset.bl_idname
