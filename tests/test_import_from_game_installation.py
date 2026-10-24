"""Tests for importing game assets from the game installation: finding the files of the archetypes of the game asset
library and importing them from the Asset Browser."""

import io
import json
import os
from pathlib import Path
from types import SimpleNamespace

import bpy
import pytest
from szio import VPath

from ..shared.game_assets import game_files
from ..shared.game_assets.asset_info import ASSET_KEY_ARCHETYPE_INFO
from ..shared.game_assets.game_files import (
    GameFiles,
    clear_game_file_index_cache,
    find_game_asset_files,
    get_game_file_index,
)
from ..shared.game_assets.operators import SOLLUMZ_OT_import_library_asset_from_game_installation
from ..sollumz_preferences import get_addon_preferences, get_game_directory, save_game_directory
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import remove_number_suffix
from .shared import asset_path, log_capture, requires_szio_native

ASSET_NAME = "model_with_simple_bounds"
YTYP_NAME = "test_props"
DLC_NAME = "testdlc"
ASSET_PATH_IN_GAME = f"update/x64/dlcpacks/{DLC_NAME}/dlc.rpf/models/{ASSET_NAME}.ydr"
TXD_PATH_IN_GAME = "x64test.rpf/textures/txd.ytd"



def _archetype_xml(name: str, asset_type: str, texture_dictionary: str = "", drawable_dictionary: str = "") -> str:
    return f"""  <Item type="CBaseArchetypeDef">
   <lodDist value="100" />
   <flags value="0" />
   <specialAttribute value="0" />
   <bbMin x="-1" y="-1" z="-1" />
   <bbMax x="1" y="1" z="1" />
   <bsCentre x="0" y="0" z="0" />
   <bsRadius value="1.7" />
   <hdTextureDist value="5" />
   <name>{name}</name>
   <textureDictionary>{texture_dictionary}</textureDictionary>
   <clipDictionary />
   <drawableDictionary>{drawable_dictionary}</drawableDictionary>
   <physicsDictionary />
   <assetType>ASSET_TYPE_{asset_type}</assetType>
   <assetName>{name}</assetName>
   <extensions />
  </Item>
"""


def _ytyp_xml(name: str, *archetypes: str) -> bytes:
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<CMapTypes>
 <extensions />
 <archetypes>
{"".join(archetypes)} </archetypes>
 <name>{name}</name>
 <dependencies />
 <compositeEntityTypes itemType="CCompositeEntityType" />
</CMapTypes>
""".encode()


DLCLIST_XML = f"""<?xml version="1.0" encoding="UTF-8"?>
<SMandatoryPacksData>
 <Paths>
  <Item>platform:/dlcpacks/{DLC_NAME}/</Item>
 </Paths>
</SMandatoryPacksData>
""".encode()


def _build_rpf(entries: dict[str, bytes]) -> bytes:
    from pymateria.rpf7 import PackFile, PackFileEntryFile

    pf = PackFile.create()
    for path, data in entries.items():
        pf.add_entry(PackFileEntryFile.create(pf, path, data), False)
    buf = io.BytesIO()
    PackFile.export_rpf(pf, buf)
    return buf.getvalue()


def _fake_game_dir(tmp_path: Path, monkeypatch, rpfs: dict[str, dict[str, bytes]]):
    """A fake game installation directory with the RPF archives `rpfs`, mapping their path to the files inside."""
    from szio.vfs import clear_archive_cache

    # Save the game file indices next to the test files instead of the user data directory
    monkeypatch.setattr(game_files, "_game_file_index_cache_directory", lambda: tmp_path / "game_files.cache")

    game_dir = tmp_path / "game"
    game_dir.mkdir()
    (game_dir / "GTA5.exe").touch()
    for rpf_path, entries in rpfs.items():
        rpf_path = game_dir / rpf_path
        rpf_path.parent.mkdir(parents=True, exist_ok=True)
        rpf_path.write_bytes(_build_rpf(entries))

    clear_game_file_index_cache()
    yield game_dir
    clear_game_file_index_cache()
    clear_archive_cache()


@pytest.fixture()
def game_dir(tmp_path, monkeypatch):
    """A fake game installation directory with a drawable test asset, in CWXML and binary in the base game and
    overridden by a DLC, which also has its HD texture dictionary."""
    ydr = asset_path("gen8", f"{ASSET_NAME}.ydr").read_bytes()
    txd = asset_path("gen8", "txd.ytd").read_bytes()
    yield from _fake_game_dir(
        tmp_path,
        monkeypatch,
        {
            "x64test.rpf": {
                f"models/{ASSET_NAME}.ydr": ydr,
                f"models/{ASSET_NAME}.ydr.xml": asset_path("cwxml", f"{ASSET_NAME}.ydr.xml").read_bytes(),
                "textures/txd.ytd": txd,
                f"maps/{YTYP_NAME}.ytyp.xml": _ytyp_xml(
                    YTYP_NAME, _archetype_xml(ASSET_NAME, "DRAWABLE", texture_dictionary="txd")
                ),
            },
            "update/update.rpf": {"common/data/dlclist.xml": DLCLIST_XML},
            f"update/x64/dlcpacks/{DLC_NAME}/dlc.rpf": {
                f"models/{ASSET_NAME}.ydr": ydr,
                f"models/{ASSET_NAME}+hidr.ytd": txd,
            },
        },
    )


def _drawables() -> list[bpy.types.Object]:
    return [o for o in bpy.data.objects if o.sollum_type == SollumType.DRAWABLE]


@requires_szio_native
def test_find_game_asset_files(game_dir):
    with log_capture() as logs:
        files = find_game_asset_files(game_dir, ASSET_NAME, YTYP_NAME)

    logs.assert_no_warnings_or_errors()
    assert files is not None
    # The binary file is preferred over its CWXML variant, and the DLC file over the base game one
    assert files.asset == VPath(game_dir) / ASSET_PATH_IN_GAME
    assert files.txd == VPath(game_dir) / TXD_PATH_IN_GAME

    # Unknown .ytyp or archetype
    with log_capture() as logs:
        assert find_game_asset_files(game_dir, ASSET_NAME, "missing_props") is None
        assert find_game_asset_files(game_dir, "missing_prop", YTYP_NAME) is None

    assert any("Could not find 'missing_props.ytyp'" in w for w in logs.warnings)
    assert any("Could not find archetype 'missing_prop'" in w for w in logs.warnings)


@requires_szio_native
def test_game_file_index_saved_to_disk(game_dir, monkeypatch):
    scans = []
    original_read_asset_filelist = GameFiles.read_asset_filelist

    def _read_asset_filelist(self, *args, **kwargs):
        scans.append(self.root)
        return original_read_asset_filelist(self, *args, **kwargs)

    monkeypatch.setattr(GameFiles, "read_asset_filelist", _read_asset_filelist)

    index = get_game_file_index(game_dir)
    assert len(scans) == 1

    # In the next session, it is loaded from disk without scanning the game files again
    clear_game_file_index_cache()
    assert get_game_file_index(game_dir) == index
    assert len(scans) == 1

    # Changing a game archive rebuilds it
    rpf = game_dir / "x64test.rpf"
    st = rpf.stat()
    os.utime(rpf, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000_000))
    clear_game_file_index_cache()
    assert get_game_file_index(game_dir) == index
    assert len(scans) == 2


class _FakeCollection(list):
    def add(self) -> SimpleNamespace:
        item = SimpleNamespace()
        self.append(item)
        return item


class _FakeImportLibraryAssetOperator:
    """Stand-in for the operator instance, so `invoke` and `execute` can run without the Asset Browser."""

    invoke = SOLLUMZ_OT_import_library_asset_from_game_installation.invoke
    execute = SOLLUMZ_OT_import_library_asset_from_game_installation.execute

    def __init__(self, directory: str = "", assets: list[dict] = ()):
        self.directory = directory
        self.assets = _FakeCollection(SimpleNamespace(**a) for a in assets)
        self.reports = []

    def report(self, level: set[str], msg: str):
        self.reports.append((next(iter(level)), msg))

    def assert_no_errors(self):
        assert not any(level == "ERROR" for level, _ in self.reports)


def _fake_asset_browser_context(selected_assets: list[SimpleNamespace]) -> tuple[SimpleNamespace, list]:
    fileselect_calls = []
    context = SimpleNamespace(
        preferences=bpy.context.preferences,
        window=None,
        asset=None,
        selected_assets=selected_assets,
        window_manager=SimpleNamespace(fileselect_add=fileselect_calls.append),
    )
    return context, fileselect_calls


def _fake_asset(metadata: dict[str, str] | None = None, id_type: str = "OBJECT", name: str = "prop_a"):
    """Stand-in for `bpy.types.AssetRepresentation`, which cannot be created from Python."""
    return SimpleNamespace(name=name, id_type=id_type, metadata=metadata or {})


def _metadata(**archetype_info) -> dict[str, str]:
    return {ASSET_KEY_ARCHETYPE_INFO: json.dumps(archetype_info)}


def _test_asset_item(asset_name: str = ASSET_NAME) -> dict:
    return {"asset_name": asset_name, "ytyp_name": YTYP_NAME, "is_interior": False}


@requires_szio_native
def test_import_library_assets_from_game_installation(context, game_dir, monkeypatch, prefs_temp_file):
    from ..ytd import ytdimport

    loaded_hd_txds = {}
    original_try_load_hd_txd = ytdimport.try_load_hd_txd

    def _try_load_hd_txd(name, prefers_xml, suffix):
        hd_txd = original_try_load_hd_txd(name, prefers_xml, suffix)
        loaded_hd_txds[f"{name}{suffix}"] = hd_txd
        return hd_txd

    monkeypatch.setattr(ytdimport, "try_load_hd_txd", _try_load_hd_txd)
    bpy.ops.wm.read_homefile()
    get_addon_preferences().game_directory = ""

    op = _FakeImportLibraryAssetOperator(
        str(game_dir),
        [
            # Number suffix and case are ignored when looking up the archetype
            _test_asset_item(ASSET_NAME.upper() + ".001"),
            _test_asset_item(),
            {"asset_name": "v_int_1", "ytyp_name": "v_int_1", "is_interior": True},
        ],
    )
    result = op.execute(context)

    assert result == {"FINISHED"}
    op.assert_no_errors()
    assert any(level == "WARNING" and "interiors" in msg for level, msg in op.reports)
    # The asset selected twice is imported once, with all its data
    (drawable,) = _drawables()
    assert remove_number_suffix(drawable.name) == ASSET_NAME
    assert any(o.sollum_type == SollumType.DRAWABLE_MODEL for o in drawable.children_recursive)
    assert any(o.sollum_type == SollumType.BOUND_BOX for o in drawable.children_recursive)
    # The model and the texture dictionary are in different archives, imported together from their common directory.
    # The HD texture dictionary next to the model is still found.
    assert [t.name for t in context.scene.sz_txds.texture_dictionaries] == ["txd"]
    assert loaded_hd_txds[f"{ASSET_NAME}+hidr"] is not None
    # The selected game directory is saved so the user is not asked again
    assert get_game_directory() == game_dir

    # Importing again doesn't import the texture dictionary already in the scene
    op = _FakeImportLibraryAssetOperator(str(game_dir), [_test_asset_item()])
    assert op.execute(context) == {"FINISHED"}
    op.assert_no_errors()
    assert len(_drawables()) == 2
    assert [t.name for t in context.scene.sz_txds.texture_dictionaries] == ["txd"]


@requires_szio_native
def test_import_library_assets_from_game_installation_game_directory(context, game_dir, tmp_path, prefs_temp_file):
    bpy.ops.wm.read_homefile()
    get_addon_preferences().game_directory = ""
    asset_browser, fileselect_calls = _fake_asset_browser_context(
        [
            _fake_asset(_metadata(ytyp=YTYP_NAME, type="BASE"), name=ASSET_NAME),
            # MLOs are saved as collections
            _fake_asset(_metadata(ytyp="v_int_1", type="MLO"), id_type="COLLECTION", name="v_int_1"),
            # Not game assets: no or malformed archetype metadata, or not an object or collection
            _fake_asset(),
            _fake_asset({ASSET_KEY_ARCHETYPE_INFO: "{not json"}),
            _fake_asset(_metadata(ytyp=YTYP_NAME, type="BASE"), id_type="MATERIAL"),
        ]
    )

    # Without a saved game directory, the file browser is opened to select it, with the selected game assets copied
    # before, they are no longer in the context after it closes
    op = _FakeImportLibraryAssetOperator()
    assert op.invoke(asset_browser, None) == {"RUNNING_MODAL"}
    assert fileselect_calls == [op]
    assert [(a.asset_name, a.ytyp_name, a.is_interior) for a in op.assets] == [
        (ASSET_NAME, YTYP_NAME, False),
        ("v_int_1", "v_int_1", True),
    ]

    # A selected directory that is not a game installation is rejected and not saved
    op.directory = str(tmp_path)
    assert op.execute(context) == {"CANCELLED"}
    assert any(level == "ERROR" and "not a GTA V installation" in msg for level, msg in op.reports)
    assert get_addon_preferences().game_directory == ""

    # With a saved game directory, the import runs without asking for it
    save_game_directory(game_dir)
    op = _FakeImportLibraryAssetOperator()
    assert op.invoke(asset_browser, None) == {"FINISHED"}
    op.assert_no_errors()
    assert len(fileselect_calls) == 1
    assert Path(op.directory) == game_dir
    assert len(_drawables()) == 1
