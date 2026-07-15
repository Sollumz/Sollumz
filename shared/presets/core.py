"""
PresetCategory registry.

Categories self-register at module import time. The registry is a plain
dictionary keyed by `(game, id)`; readers should treat it as read-only via
`PRESET_CATEGORIES.values()`.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any, Iterable
from bpy.types import (
    Context,
    Object,
)

from ..multiselection import MultiSelectCollection

from .serializer import struct_to_dict, dict_to_struct


@dataclass
class PresetCategory:
    id: str
    """Stable id used in file names and operator args. Snake_case. Unique
    within a game, but the same id may be reused across games (e.g. both
    GTA5 and RDR2 can define a `flag` category)."""

    label: str
    """Human-readable name shown in UI (popover header, error messages)."""

    game: str
    """Short game id this category targets (e.g. `gta5`). Doubles as the
    subdirectory name under `{config_dir}/presets/` where its JSON lives."""

    bundled_defaults_path: Path | None = None
    """Optional path to a JSON file shipped with the addon, loaded when the
    user has no presets of their own for this category yet."""

    blacklist: frozenset = frozenset()
    """Preset names that cannot be deleted (typically the bundled defaults)."""

    skip: tuple = ()
    """Field names to omit from generic capture/apply (e.g. transform fields
    on a positional entity)."""

    get_target: Callable[[Context], Any] = lambda context: None
    """Returns the PropertyGroup (or other object) to capture from / apply
    onto. Receives `context`."""

    get_targets: Callable[[Context], Iterable] | None = None
    """Returns the active + selected targets to apply onto. Receives `context`.
    Used by load to apply a preset to every selected target. When None, load
    falls back to the single `get_target`. Save never uses this."""

    poll: Callable[[Context], tuple] = lambda context: (True, "")
    """Returns (ok, reason). When `ok` is False, save/load are disabled and
    the popover shows the reason."""

    capture_fn: Callable | None = None
    """Override for `capture()`. If None, the default uses struct_to_dict on
    get_target(context)."""

    apply_fn: Callable | None = None
    """Override for `apply()`. Receives (target, data, **opts). If None, the
    default uses dict_to_struct on get_target(context)."""

    def capture(self, target):
        if self.capture_fn is not None:
            return self.capture_fn(target)
        return struct_to_dict(target, skip=self.skip)

    def apply(self, target, data, **opts):
        if self.apply_fn is not None:
            return self.apply_fn(target, data, **opts)
        dict_to_struct(target, data, skip=self.skip)

    def iter_targets(
        self,
        context: Context,
        *,
        get_target_override: Callable[[Context], Any] | None = None,
        get_targets_override: Callable[[Context], Iterable] | None = None,
    ) -> list:
        """Resolve the targets to apply a preset onto."""
        getter_multi = get_targets_override or self.get_targets
        if getter_multi is not None:
            return [t for t in getter_multi(context) if t is not None]
        getter = get_target_override or self.get_target
        target = getter(context)
        return [target] if target is not None else []


PRESET_CATEGORIES: dict[tuple[str, str], PresetCategory] = {}


def register_preset_category(category: PresetCategory):
    """Register a preset category. Call at module import time (top-level)
    so the registry is populated before `shared.presets.register()` runs.
    Raises ValueError if (game, id) is already taken."""
    key = (category.game, category.id)
    if key in PRESET_CATEGORIES:
        existing = PRESET_CATEGORIES[key]
        if existing is category:
            return  # idempotent
        raise ValueError(f"preset category '{category.game}/{category.id}' is already registered")
    PRESET_CATEGORIES[key] = category


def make_get_targets_from_objects(transform: Callable[[Object], object | None]) -> Callable[[Context], list]:
    """Build a `get_targets` for object-based categories.

    `transform(obj)` maps an Object to its target (or `None` to skip it).

    The active object and every selected object are mapped through it, with
    `None`s dropped and duplicates removed (selected objects can share an active
    material / light data, which should only be applied to once).
    """

    def _get_targets(context: Context) -> list:
        objs = list(context.selected_objects)
        active = context.active_object
        if active is not None and active not in objs:
            objs.append(active)

        seen = set()
        out = []
        for obj in objs:
            target = transform(obj)
            if target is None:
                continue
            key = id(target)
            if key in seen:
                continue
            seen.add(key)
            out.append(target)
        return out

    return _get_targets


def make_get_targets_from_collection(
    get_collection: Callable[[Context], MultiSelectCollection | None],
    transform: Callable[[object], object | None] = lambda item: item,
) -> Callable[[Context], list]:
    """Build a `get_targets` for `MultiSelectCollection`-based categories.

    `get_collection(context)` returns the collection whose selected items are the
    targets (or `None` when unavailable).

    `transform(item)` maps each selected item to its target (or `None` to skip it).
    """

    def _get_targets(context: Context) -> list:
        coll = get_collection(context)
        if coll is None:
            return []
        out = []
        for item in coll.iter_selected_items():
            target = transform(item)
            if target is not None:
                out.append(target)
        return out

    return _get_targets
