"""
PresetCategory registry.

Categories self-register at module import time. The registry is a plain
dictionary keyed by `(game, id)`; readers should treat it as read-only via
`PRESET_CATEGORIES.values()`.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Any

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

    get_target: Callable[[Any], Any] = lambda context: None
    """Returns the PropertyGroup (or other object) to capture from / apply
    onto. Receives `context`."""

    poll: Callable[[Any], tuple] = lambda context: (True, "")
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
