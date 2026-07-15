"""
Legacy XML -> JSON migration.

Each category with a legacy XML format registers a converter at module import
time. The legacy XML always lives at `{config_dir}/{category_id}_presets.xml`
(the historical filename convention, GTA5-only — XML was never multi-game).
On first load, if no user JSON exists yet and the legacy XML does, the
converter runs and the XML is renamed to `*.xml.bak` so the migration is
idempotent. The new JSON is written into the per-game subdir
`{config_dir}/presets/{game}/{id}.json` via `store.save_presets`.

Converters live with the category that owns them so this module has no hard
dependency on any format module.
"""

import os
from pathlib import Path

from . import store

from ... import logger

_converters = {}  # dict[tuple[str, str], callable]


def register_legacy_migration(category, converter):
    """Register a `(legacy_xml_path: Path) -> list[dict]` converter for a
    category. Call at module import time alongside `register_preset_category`.
    """
    _converters[(category.game, category.id)] = converter


def _legacy_xml_path(category):
    from ...known_paths import config_directory_path

    return Path(config_directory_path()) / "{}_presets.xml".format(category.id)


def migrate_if_needed(category):
    """If the user has no JSON for this category but does have legacy XML,
    convert and rename. Returns the migrated JSON path, or None if nothing
    was done. Errors are caught and logged so a bad XML doesn't break addon
    load."""
    converter = _converters.get((category.game, category.id))
    if converter is None:
        return None

    xml_path = _legacy_xml_path(category)
    if not xml_path.exists():
        return None

    user_json = store.user_preset_path(category)
    if user_json.exists():
        return None  # already migrated

    try:
        presets = converter(xml_path)
    except Exception as e:
        logger.error(f"Presets: legacy XML conversion for '{category.game}/{category.id}' failed: {e}")
        return None

    store.save_presets(category, presets)

    bak = xml_path.with_suffix(xml_path.suffix + ".bak")
    try:
        if bak.exists():
            bak.unlink()
        os.replace(str(xml_path), str(bak))
    except OSError as e:
        logger.error(f"Presets: could not rename legacy XML to .bak: {e}")

    logger.info(
        f"Presets: migrated {len(presets)} '{category.game}/{category.id}' preset(s) from {xml_path}"
    )
    return user_json
