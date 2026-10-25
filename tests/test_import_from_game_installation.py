"""Tests for importing game assets from the game installation: finding the files of the archetypes of the game asset
library, importing them from the Asset Browser, and replacing the library objects linked to map entities with them."""

import io
import json
import os
from pathlib import Path
from types import SimpleNamespace

import bpy
import pytest
from mathutils import Vector
from szio import VPath
from szio.jenkhash import name_to_hash

from ..shared.game_assets import game_files
from ..shared.game_assets.asset_info import ASSET_KEY_ARCHETYPE_INFO
from ..shared.game_assets.game_files import (
    GameFiles,
    clear_game_file_index_cache,
    find_game_asset_files,
    get_game_file_index,
)
from ..shared.game_assets.operators import SOLLUMZ_OT_import_library_asset_from_game_installation
from ..sollumz_helper import duplicate_object_with_children
from ..sollumz_preferences import get_addon_preferences, get_game_directory, save_game_directory
from ..shared.multiselection import SelectMode
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_empty_object, remove_number_suffix
from ..ymap_next.context import active_group
from ..ymap_next.properties.map import get_maps
from .shared import asset_path, log_capture, requires_szio_native
from .test_import_export import DEFAULT_EXPORT_SETTINGS

ASSET_NAME = "model_with_simple_bounds"
YTYP_NAME = "test_props"
DLC_NAME = "testdlc"
ASSET_PATH_IN_GAME = f"update/x64/dlcpacks/{DLC_NAME}/dlc.rpf/models/{ASSET_NAME}.ydr"
TXD_PATH_IN_GAME = "x64test.rpf/textures/txd.ytd"

DWD_NAME = "dwd_props"
DWD_ASSET_NAMES = ("dwd_prop_a", "dwd_prop_b")
DWD_YTYP_NAME = "test_dwd_props"


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


def _build_ydd(out_dir: Path) -> bytes:
    """A drawable dictionary with a drawable for each of `DWD_ASSET_NAMES`, copies of a test model."""
    bpy.ops.wm.read_homefile()
    ydr_path = asset_path("gen8", f"{ASSET_NAME}.ydr")
    assert bpy.ops.sollumz.import_assets(directory=str(ydr_path.parent), files=[{"name": ydr_path.name}]) == {
        "FINISHED"
    }
    drawable = bpy.data.objects[ASSET_NAME]
    dictionary = create_empty_object(SollumType.DRAWABLE_DICTIONARY, DWD_NAME)
    for name, obj in zip(DWD_ASSET_NAMES, (drawable, duplicate_object_with_children(drawable))):
        obj.name = name
        obj.parent = dictionary

    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    dictionary.select_set(True)
    out_dir.mkdir()
    res = bpy.ops.sollumz.export_assets(
        directory=str(out_dir),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS | {"target_formats": {"NATIVE"}, "target_versions": {"GEN8"}},
    )
    assert res == {"FINISHED"}
    return (out_dir / f"{DWD_NAME}.ydd").read_bytes()


@pytest.fixture()
def dwd_game_dir(tmp_path, monkeypatch):
    """A fake game installation directory with a drawable dictionary used by the archetypes `DWD_ASSET_NAMES`."""
    yield from _fake_game_dir(
        tmp_path,
        monkeypatch,
        {
            "x64test.rpf": {
                f"models/{DWD_NAME}.ydd": _build_ydd(tmp_path / "ydd"),
                f"maps/{DWD_YTYP_NAME}.ytyp.xml": _ytyp_xml(
                    DWD_YTYP_NAME,
                    *(_archetype_xml(n, "DRAWABLEDICTIONARY", drawable_dictionary=DWD_NAME) for n in DWD_ASSET_NAMES),
                ),
            }
        },
    )


def _drawables() -> list[bpy.types.Object]:
    return [o for o in bpy.data.objects if o.sollum_type == SollumType.DRAWABLE]


def _drawable_dictionaries() -> list[bpy.types.Object]:
    return [o for o in bpy.data.objects if o.sollum_type == SollumType.DRAWABLE_DICTIONARY]


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


def _add_library_asset_objects(
    library_dir: Path, name: str, num_objects: int, append: bool = False, ytyp: str = YTYP_NAME
) -> list[bpy.types.Object]:
    """Create a game asset library .blend with an object for the archetype `name`, and return objects of it added to
    the scene: library overrides, like the objects linked from the asset library to entities, or appended copies, like
    the objects dropped from the Asset Browser with the Append or Pack import methods."""
    obj = bpy.data.objects.new(name, bpy.data.meshes.new(name))
    obj[ASSET_KEY_ARCHETYPE_INFO] = json.dumps({"ytyp": ytyp, "type": "BASE"})
    # A new file each time, a library already linked cannot be written again
    library_path = library_dir / f"_assets.{ytyp}.{len(bpy.data.libraries)}.blend"
    bpy.data.libraries.write(str(library_path), {obj})
    bpy.data.objects.remove(obj)

    with bpy.data.libraries.load(str(library_path), link=not append) as (_, data_dst):
        data_dst.objects = [name]

    objs = []
    for _ in range(num_objects):
        if append:
            new_obj = data_dst.objects[0] if not objs else data_dst.objects[0].copy()
        else:
            new_obj = data_dst.objects[0].override_create()
        bpy.context.scene.collection.objects.link(new_obj)
        objs.append(new_obj)
    return objs


@requires_szio_native
def test_map_import_entity_objects_from_game_installation(game_dir, tmp_path, prefs_temp_file):
    bpy.ops.wm.read_homefile()
    library_objs = _add_library_asset_objects(tmp_path, ASSET_NAME, num_objects=2)
    locations = [Vector((1.0, 2.0, 3.0)), Vector((-4.0, 5.0, 0.0))]
    group = get_maps(bpy.context, create_if_missing=True).new_group()
    for library_obj, location in zip(library_objs, locations):
        library_obj.location = location
        entity = group.new_entity()
        entity.archetype_name = ASSET_NAME
        entity.linked_object = library_obj
    group.entities.select(0)
    group.entities.select(1, SelectMode.EXTEND)
    # Only the second library object is selected and active
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    library_objs[1].select_set(True)
    view_layer = bpy.context.view_layer
    view_layer.objects.active = library_objs[1]
    assert set(bpy.context.selected_objects) == {library_objs[1]}

    result = bpy.ops.sollumz.map_import_entity_objects_from_game_installation(directory=str(game_dir))

    assert result == {"FINISHED"}
    objs = [e.linked_object for e in active_group(bpy.context).entities]
    # The imported model replaces the first library object, and a copy of it the second one
    assert objs[0] is not None and objs[1] is not None and objs[0] != objs[1]
    # The first keeps the archetype name, without suffix, now that the library objects with that name are removed
    assert objs[0].name == ASSET_NAME
    for obj, location in zip(objs, locations):
        assert obj.sollum_type == SollumType.DRAWABLE
        assert remove_number_suffix(obj.name) == ASSET_NAME
        assert obj.location == location
        # Full import, with collisions
        assert any(c.sollum_type == SollumType.BOUND_BOX for c in obj.children_recursive)
        assert obj.name in bpy.context.scene.collection.objects
    # The library objects are removed
    assert not any(o.override_library is not None for o in bpy.data.objects)
    # The selection is kept, with the new object in place of the library object
    assert set(bpy.context.selected_objects) == {objs[1]}
    assert view_layer.objects.active == objs[1]


@requires_szio_native
@pytest.mark.parametrize("append", (False, True))
def test_import_objects_from_game_installation(game_dir, tmp_path, prefs_temp_file, append):
    bpy.ops.wm.read_homefile()
    library_objs = _add_library_asset_objects(tmp_path, ASSET_NAME, num_objects=2, append=append)
    library_names = {obj.name for obj in library_objs}
    # Only the first library object is linked to an entity
    group = get_maps(bpy.context, create_if_missing=True).new_group()
    entity = group.new_entity()
    entity.archetype_name = ASSET_NAME
    entity.linked_object = library_objs[0]

    # An object without archetype metadata is not a game asset object, even if a .ytyp in the scene has its archetype
    scene_ytyp = bpy.context.scene.ytyps.add()
    scene_ytyp.name = "scene_props"
    scene_ytyp.new_archetype().name = "scene_prop"
    other_obj = bpy.data.objects.new("scene_prop", None)
    bpy.context.scene.collection.objects.link(other_obj)
    for obj in bpy.context.selected_objects:
        obj.select_set(False)
    other_obj.select_set(True)
    bpy.context.view_layer.objects.active = other_obj
    assert not bpy.ops.sollumz.import_objects_from_game_installation.poll()

    # Selected along with the library objects, it is ignored
    for obj in library_objs:
        obj.select_set(True)
    bpy.context.view_layer.objects.active = library_objs[0]
    result = bpy.ops.sollumz.import_objects_from_game_installation(directory=str(game_dir))

    assert result == {"FINISHED"}
    new_objs = set(bpy.context.selected_objects) - {other_obj}
    assert len(new_objs) == 2
    assert all(obj.sollum_type == SollumType.DRAWABLE for obj in new_objs)
    # The entity is linked to the object that replaces its library object
    entity = active_group(bpy.context).entities[0]
    assert entity.linked_object in new_objs
    assert bpy.context.view_layer.objects.active == entity.linked_object
    # The library objects are removed
    assert not any(o.override_library is not None for o in bpy.data.objects)
    assert not any(o.name in library_names for o in bpy.data.objects if o not in new_objs and o.library is None)


@requires_szio_native
def test_map_import_entity_objects_from_drawable_dictionary(dwd_game_dir, tmp_path, prefs_temp_file):
    bpy.ops.wm.read_homefile()
    get_maps(bpy.context, create_if_missing=True).new_group()
    prop_a, prop_b = DWD_ASSET_NAMES

    def _import_entity_objects(*names: str, location: Vector = Vector()) -> list[bpy.types.Object]:
        """Add an entity linked to a library object at `location` for each archetype, and replace the library objects
        of these entities with their models. Returns the new linked objects."""
        group = active_group(bpy.context)
        first_index = len(group.entities)
        for name in names:
            library_obj = _add_library_asset_objects(tmp_path, name, num_objects=1, ytyp=DWD_YTYP_NAME)[0]
            library_obj.location = location
            entity = group.new_entity()
            entity.archetype_name = name
            entity.linked_object = library_obj
        group.entities.select(first_index)
        group.entities.select(len(group.entities) - 1, SelectMode.EXTEND)

        result = bpy.ops.sollumz.map_import_entity_objects_from_game_installation(directory=str(dwd_game_dir))

        assert result == {"FINISHED"}
        return [e.linked_object for e in active_group(bpy.context).entities][first_index:]

    # The whole drawable dictionary is imported, and the entity is linked to its drawable, which stays in it
    (obj_a,) = _import_entity_objects(prop_a, location=Vector((1.0, 2.0, 3.0)))
    (dictionary,) = _drawable_dictionaries()
    assert obj_a.parent == dictionary
    assert len(dictionary.children) == len(DWD_ASSET_NAMES)
    # Binary drawable dictionaries only have the hashes of the drawable names
    assert name_to_hash(remove_number_suffix(obj_a.name)) == name_to_hash(prop_a)
    bpy.context.view_layer.update()
    assert obj_a.matrix_world.translation == Vector((1.0, 2.0, 3.0))

    # The drawable of the dictionary not linked to any entity is used, instead of importing the dictionary again
    (obj_b,) = _import_entity_objects(prop_b)
    assert obj_b.parent == dictionary
    assert len(_drawable_dictionaries()) == 1

    # Both drawables are used now, so the dictionary is imported again, once for both archetypes
    obj_a2, obj_b2 = _import_entity_objects(prop_a, prop_b)
    assert len(_drawable_dictionaries()) == 2
    assert obj_a2.parent is not None and obj_a2.parent == obj_b2.parent and obj_a2.parent != dictionary
