"""Tests for the preferences .ini load/save (sollumz_preferences).

The autouse ``prefs_temp_file`` fixture redirects the preferences file into an isolated temp
directory and restores the in-memory preferences after each test, so nothing touches (or leaks into)
the developer's real Sollumz preferences.
"""

import pytest

from .. import sollumz_preferences as prefs_mod
from .shared import log_capture


@pytest.fixture(autouse=True)
def prefs_temp_file(tmp_path, monkeypatch):
    """Redirect preferences to an isolated temp .ini and restore the real preferences afterwards.

    `_save_preferences` / `_load_preferences` resolve the file through the module-global `prefs_file_path` (imported by
    name at module load), so the patch must be applied on `sollumz_preferences` itself, not on `known_paths`.
    """
    ini_path = tmp_path / "sollumz_prefs.ini"
    monkeypatch.setattr(prefs_mod, "prefs_file_path", lambda: str(ini_path))

    prefs = prefs_mod.get_addon_preferences()
    # Snapshot the real preferences so any mutation a test makes is rolled back afterwards.
    snapshot = prefs_mod._get_bpy_struct_as_dict(prefs)
    try:
        yield ini_path
    finally:
        prefs_mod._update_bpy_struct_from_dict(prefs, snapshot, eval_strings=True)


def test_round_trip(prefs_temp_file):
    """Scalars, nested settings groups, theme colors and collections survive save -> load."""
    prefs = prefs_mod.get_addon_preferences()

    prefs.use_text_name_as_mat_name = False             # bool scalar
    prefs.default_flags_portal = 42                      # int scalar
    prefs.import_settings.split_by_group = False         # nested PointerProperty group
    prefs.import_settings.import_as_asset = True
    prefs.theme.mlo_gizmo_room = (0.1, 0.2, 0.3, 0.4)    # FloatVectorProperty
    prefs.shared_textures_directories.clear()
    d = prefs.shared_textures_directories.add()
    d.path = "C:\\textures"
    d.recursive = False
    prefs.name_table_paths.clear()
    nt = prefs.name_table_paths.add()
    nt.path = "C:\\names.txt"

    prefs_mod._save_preferences()
    saved_ini = prefs_temp_file.read_text(encoding="utf-8")

    # Mutate to different in-memory values. These auto-save and overwrite the temp .ini, so put the
    # saved snapshot back on disk before loading.
    prefs.use_text_name_as_mat_name = True
    prefs.default_flags_portal = 0
    prefs.import_settings.split_by_group = True
    prefs.import_settings.import_as_asset = False
    prefs.theme.mlo_gizmo_room = (1.0, 1.0, 1.0, 1.0)
    prefs.shared_textures_directories.clear()
    prefs.name_table_paths.clear()
    prefs_temp_file.write_text(saved_ini, encoding="utf-8")

    prefs_mod._load_preferences()

    assert prefs.use_text_name_as_mat_name is False
    assert prefs.default_flags_portal == 42
    assert prefs.import_settings.split_by_group is False
    assert prefs.import_settings.import_as_asset is True
    assert tuple(prefs.theme.mlo_gizmo_room) == pytest.approx((0.1, 0.2, 0.3, 0.4), abs=1e-4)
    assert [(d.path, d.recursive) for d in prefs.shared_textures_directories] == [("C:\\textures", False)]
    assert [nt.path for nt in prefs.name_table_paths] == ["C:\\names.txt"]


def test_corrupt_ini_falls_back_and_backs_up(prefs_temp_file):
    """A malformed .ini must not raise out of load; it is backed up and defaults are kept."""
    prefs_temp_file.write_text("not a valid ini line\n[unterminated", encoding="utf-8")

    with log_capture() as logs:
        prefs_mod._load_preferences()   # must NOT raise

    assert logs.has_errors
    bak_path = prefs_temp_file.parent / (prefs_temp_file.name + ".bak")
    assert bak_path.exists()
    assert not prefs_temp_file.exists()


def test_schema_drift_keeps_overlapping_fields(prefs_temp_file):
    """Collection entries with the wrong field count load best-effort instead of being dropped.

    ``SzSharedTexturesDirectory`` has two fields ``(path, recursive)``. An entry with too few values
    keeps its overlapping field and defaults the rest; an entry with too many ignores the extras.
    Neither is dropped, and each mismatch logs a warning.
    """
    prefs = prefs_mod.get_addon_preferences()
    prefs_temp_file.write_text(
        "[main]\n"
        "shared_textures_directories = [('short_only',), ('p2', False, 'extra_ignored')]\n",
        encoding="utf-8",
    )

    with log_capture() as logs:
        prefs_mod._load_preferences()

    dirs = [(d.path, d.recursive) for d in prefs.shared_textures_directories]
    assert dirs == [("short_only", True), ("p2", False)]   # 'recursive' default is True
    logs.assert_warning(match="SzSharedTexturesDirectory", num=2)


def test_save_is_atomic_no_tmp_left(prefs_temp_file):
    """The atomic write leaves the real file in place and no leftover temp file."""
    prefs_mod._save_preferences()

    assert prefs_temp_file.exists()
    assert not (prefs_temp_file.parent / (prefs_temp_file.name + ".tmp")).exists()
