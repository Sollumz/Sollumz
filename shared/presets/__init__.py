"""
Unified preset framework.

A preset is a named, JSON-serialized snapshot of a Blender PropertyGroup (or a
small bundle of related PropertyGroups) that the user can save and re-apply.
Categories are self-registered at module import time via
`register_preset_category(...)` so each format can declare its own without the
framework needing to know about it.

Public API:
    PresetCategory                  - base class for a preset category declaration
    register_preset_category        - register a category at module import
    PRESET_CATEGORIES               - read-only view of registered categories
    struct_to_dict / dict_to_struct - generic PropertyGroup <-> dict
    PresetSaveOperatorBase / PresetLoadOperatorBase / PresetDeleteOperatorBase
                                    - operator mix-ins; subclass alongside bpy.types.Operator
    PresetPanel                     - Panel mix-in
"""
from .core import (
    PresetCategory,
    PRESET_CATEGORIES,
    register_preset_category,
)
from .serializer import struct_to_dict, dict_to_struct
from .operators import (
    PresetSaveOperatorBase,
    PresetLoadOperatorBase,
    PresetDeleteOperatorBase,
)
from .ui import PresetPanel
from . import store
from . import migration


def register():
    for category in PRESET_CATEGORIES.values():
        try:
            migration.migrate_if_needed(category)
        except Exception as e:
            print(f"[sollumz.presets] migration for '{category.game}/{category.id}' failed: {e}")

        store.invalidate(category)


def unregister():
    store.clear_all_caches()
