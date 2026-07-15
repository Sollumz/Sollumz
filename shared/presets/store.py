"""
On-disk and in-process preset storage.

JSON file layout:

    {
        "version": 1,
        "category": "<category id>",
        "presets": [
            {"name": "...", "data": {...}},
            ...
        ]
    }

User presets live at `{config_dir}/presets/{game}/{id}.json`. If that file
does not exist, the category's `bundled_defaults_path` is used as a read-only
fallback (saves still write to the user path, creating it on demand).
"""

import json
import os
from pathlib import Path

from ... import logger

CURRENT_VERSION = 1

_cache = {}  # dict[tuple[str, str], list[dict]]


def _config_presets_dir():
    # Late import: known_paths pulls in bpy
    from ...known_paths import config_directory_path

    return Path(config_directory_path()) / "presets"


def user_preset_path(category):
    return _config_presets_dir() / category.game / "{}.json".format(category.id)


def _read_file(path):
    with path.open("r", encoding="utf-8") as f:
        doc = json.load(f)
    if not isinstance(doc, dict):
        return []
    presets = doc.get("presets")
    if not isinstance(presets, list):
        return []

    return [p for p in presets if isinstance(p, dict) and "name" in p]


def _write_file(path, category, presets):
    path.parent.mkdir(parents=True, exist_ok=True)
    doc = {
        "version": CURRENT_VERSION,
        "game": category.game,
        "category": category.id,
        "presets": presets,
    }
    tmp = path.with_suffix(path.suffix + ".tmp")
    with tmp.open("w", encoding="utf-8") as f:
        json.dump(doc, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _cache_key(category):
    return (category.game, category.id)


def load_presets(category):
    """Return the list of preset dicts for a category. Caches in-process so
    the popover renders without I/O on each draw."""
    key = _cache_key(category)
    cached = _cache.get(key)
    if cached is not None:
        return cached

    user_path = user_preset_path(category)
    presets: list[dict] = []
    if user_path.is_file():
        try:
            presets = _read_file(user_path)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Presets: failed to read {user_path}: {e}")
    elif category.bundled_defaults_path and category.bundled_defaults_path.is_file():
        try:
            presets = _read_file(category.bundled_defaults_path)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(f"Presets: failed to read {category.bundled_defaults_path}: {e}")

    _cache[key] = presets
    return presets


def save_presets(category, presets):
    _write_file(user_preset_path(category), category, presets)
    _cache[_cache_key(category)] = presets


def add_preset(category, name, data):
    """Add or overwrite a preset by name. Returns True on add, False on
    overwrite (caller can decide whether that's an error)."""
    presets = list(load_presets(category))
    for i, p in enumerate(presets):
        if p.get("name") == name:
            presets[i] = {"name": name, "data": data}
            save_presets(category, presets)
            return False
    presets.append({"name": name, "data": data})
    save_presets(category, presets)
    return True


def delete_preset(category, name):
    presets = load_presets(category)
    new = [p for p in presets if p.get("name") != name]
    if len(new) == len(presets):
        return False
    save_presets(category, new)
    return True


def find_preset(category, name):
    for p in load_presets(category):
        if p.get("name") == name:
            return p
    return None


def invalidate(category):
    """Drop the in-process cache for one category. Next read pulls from disk."""
    _cache.pop(_cache_key(category), None)


def clear_all_caches():
    _cache.clear()
