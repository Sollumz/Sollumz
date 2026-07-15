"""Tests for the on-disk / in-process preset storage.

All tests use the throwaway ``tmp_category`` and the autouse ``preset_config_dir``
redirect, so nothing touches the real config directory.
"""

import json

from ...shared.presets import store
from ...shared.presets.core import PresetCategory
from ..shared import log_capture


def _write_user_file(category, doc_text):
    path = store.user_preset_path(category)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(doc_text, encoding="utf-8")
    return path


def test_user_preset_path(preset_config_dir, tmp_category):
    expected = preset_config_dir / "presets" / tmp_category.game / "{}.json".format(tmp_category.id)
    assert store.user_preset_path(tmp_category) == expected


def test_load_empty_when_no_files(tmp_category):
    assert store.load_presets(tmp_category) == []


def test_add_preset_new_then_overwrite(tmp_category):
    assert store.add_preset(tmp_category, "A", {"v": 1}) is True
    assert store.add_preset(tmp_category, "B", {"v": 2}) is True
    # Overwriting an existing name returns False and replaces the data in place.
    assert store.add_preset(tmp_category, "A", {"v": 99}) is False
    presets = store.load_presets(tmp_category)
    assert [p["name"] for p in presets] == ["A", "B"]
    assert store.find_preset(tmp_category, "A")["data"] == {"v": 99}


def test_delete_preset(tmp_category):
    store.add_preset(tmp_category, "A", {})
    store.add_preset(tmp_category, "B", {})
    assert store.delete_preset(tmp_category, "A") is True
    assert [p["name"] for p in store.load_presets(tmp_category)] == ["B"]
    # Deleting an absent preset is a no-op returning False.
    assert store.delete_preset(tmp_category, "missing") is False


def test_find_preset(tmp_category):
    store.add_preset(tmp_category, "A", {"v": 1})
    assert store.find_preset(tmp_category, "A") == {"name": "A", "data": {"v": 1}}
    assert store.find_preset(tmp_category, "nope") is None


def test_cache_used_until_invalidated(tmp_category):
    store.add_preset(tmp_category, "A", {})
    path = store.user_preset_path(tmp_category)
    # Mutate the file on disk behind the cache's back.
    doc = json.loads(path.read_text(encoding="utf-8"))
    doc["presets"].append({"name": "Sneaky", "data": {}})
    path.write_text(json.dumps(doc), encoding="utf-8")
    # The cached value still reflects the pre-mutation state.
    assert [p["name"] for p in store.load_presets(tmp_category)] == ["A"]
    store.invalidate(tmp_category)
    # A fresh read picks up the on-disk change.
    assert [p["name"] for p in store.load_presets(tmp_category)] == ["A", "Sneaky"]


def test_save_writes_versioned_doc(tmp_category):
    store.save_presets(tmp_category, [{"name": "A", "data": {}}])
    path = store.user_preset_path(tmp_category)
    doc = json.loads(path.read_text(encoding="utf-8"))
    assert doc["version"] == store.CURRENT_VERSION
    assert doc["game"] == tmp_category.game
    assert doc["category"] == tmp_category.id
    assert doc["presets"] == [{"name": "A", "data": {}}]
    # The atomic write leaves no temp file behind.
    assert not path.with_suffix(path.suffix + ".tmp").exists()


def test_bundled_fallback(preset_config_dir, tmp_path):
    bundled = tmp_path / "bundled.json"
    bundled.write_text(
        json.dumps(
            {
                "version": 1,
                "game": "testgame",
                "category": "bundledcat",
                "presets": [{"name": "Bundled", "data": {}}],
            }
        ),
        encoding="utf-8",
    )
    cat = PresetCategory(id="bundledcat", label="Bundled", game="testgame", bundled_defaults_path=bundled)

    # No user file yet -> the bundled defaults are used.
    assert [p["name"] for p in store.load_presets(cat)] == ["Bundled"]
    # After a save, the user file takes precedence over the bundled defaults.
    store.save_presets(cat, [{"name": "User", "data": {}}])
    store.invalidate(cat)
    assert [p["name"] for p in store.load_presets(cat)] == ["User"]


def test_malformed_json_returns_empty_and_logs(tmp_category):
    _write_user_file(tmp_category, "{ this is not valid json")
    with log_capture() as logs:
        result = store.load_presets(tmp_category)
    assert result == []
    assert logs.has_errors


def test_non_dict_doc_returns_empty(tmp_category):
    _write_user_file(tmp_category, json.dumps([1, 2, 3]))
    assert store.load_presets(tmp_category) == []


def test_presets_not_a_list_returns_empty(tmp_category):
    _write_user_file(tmp_category, json.dumps({"presets": "nope"}))
    assert store.load_presets(tmp_category) == []


def test_items_without_name_filtered(tmp_category):
    _write_user_file(
        tmp_category,
        json.dumps(
            {
                "presets": [
                    {"name": "Good", "data": {}},
                    {"data": {}},  # no name -> filtered out
                    "not-a-dict",  # not a dict -> filtered out
                ]
            }
        ),
    )
    assert [p["name"] for p in store.load_presets(tmp_category)] == ["Good"]


def test_clear_all_caches(tmp_category):
    store.add_preset(tmp_category, "A", {})
    assert store._cache  # populated by the save
    store.clear_all_caches()
    assert store._cache == {}
