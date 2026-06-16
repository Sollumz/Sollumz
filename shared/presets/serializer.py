"""
PropertyGroup <-> dict serialization for presets.

Walks `__annotations__` recursively. Vectors/Colors become plain lists. Nested
PropertyGroups become nested dicts. CollectionProperty becomes a list of
dicts.

A class can opt out of the default annotation walk by declaring a class-level
`__sz_preset_capture__` tuple of field names, only those are captured/applied.
"""

from typing import Iterable
from bpy.types import bpy_struct, bpy_prop_array, bpy_prop_collection
from mathutils import Vector, Color, Euler, Quaternion, Matrix


# mathutils types that FloatVectorProperty returns when a `subtype` is set
# (e.g. COLOR -> Color, DIRECTION -> Vector). JSON has no native representation
# for these, so we coerce to plain lists.
_MATHUTILS_VECTOR_TYPES = (Vector, Color, Euler, Quaternion)


def _whitelist(struct: bpy_struct) -> tuple | None:
    return getattr(type(struct), "__sz_preset_capture__", None)


def _iter_keys(struct: bpy_struct) -> Iterable[str]:
    whitelist = _whitelist(struct)
    if whitelist is not None:
        return whitelist
    return type(struct).__annotations__.keys()


def struct_to_dict(struct: bpy_struct, skip: Iterable[str] | None = None) -> dict:
    """Capture a PropertyGroup as a JSON-friendly dict. Strings stay plain
    strings, arrays/Vectors/Colors become lists, nested PropertyGroups become
    nested dicts. `skip` names are omitted."""
    skip_set = set(skip) if skip else set()

    def _convert(key: str):
        prop = getattr(struct, key)
        if isinstance(prop, str):
            return prop
        if isinstance(prop, bpy_prop_array):
            return list(prop)
        if isinstance(prop, _MATHUTILS_VECTOR_TYPES):
            return list(prop)
        if isinstance(prop, Matrix):
            return [list(row) for row in prop]
        if isinstance(prop, bpy_prop_collection):
            return [struct_to_dict(item) for item in prop]
        if isinstance(prop, bpy_struct):
            return struct_to_dict(prop)
        return prop

    return {key: _convert(key) for key in _iter_keys(struct) if key not in skip_set}


def dict_to_struct(struct: bpy_struct, data: dict, skip: Iterable[str] | None = None):
    """Apply a JSON-friendly dict back onto a PropertyGroup.

    Fields not present in `data` are left at their current value (so a partial
    preset only touches the keys it specifies). Missing target attributes are
    silently skipped. `skip` names are never written.
    """
    skip_set = set(skip) if skip else set()

    for key in _iter_keys(struct):
        if key in skip_set:
            continue
        if key not in data:
            continue
        value = data[key]
        try:
            prop = getattr(struct, key)
        except AttributeError:
            continue
        if isinstance(prop, bpy_prop_collection):
            if isinstance(value, list):
                prop.clear()
                for item in value:
                    entry = prop.add()
                    if isinstance(item, dict):
                        dict_to_struct(entry, item)
        elif isinstance(prop, bpy_struct):
            if isinstance(value, dict):
                dict_to_struct(prop, value)
        else:
            try:
                setattr(struct, key, value)
            except (TypeError, AttributeError, ValueError):
                pass
