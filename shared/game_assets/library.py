import sqlite3
from collections.abc import Iterator
from pathlib import Path

import bpy
from bpy.types import (
    BlendData,
)
from mathutils import Euler, Vector
from szio.gta5 import (
    ArchetypeType,
    AssetMapTypes,
    try_load_asset,
)

from ... import logger
from ...known_paths import data_directory_path
from ...shared.process_pool import ProcessPool
from ...sollumz_preferences import get_addon_preferences
from ...tools import jenkhash
from ...tools.blenderhelper import tag_redraw
from .catalog import CatalogDefinitionFile


def asset_cache_path() -> Path:
    path = Path(data_directory_path()) / "_assets.cache"
    path.parent.mkdir(parents=True, exist_ok=True)
    return path


def _configured_shared_directories() -> list[Path]:
    prefs = get_addon_preferences(bpy.context)
    out = []
    for d in prefs.shared_assets_directories:
        if not d.path:
            continue
        out.append(Path(bpy.path.abspath(d.path)))
    return out


def find_library_blends_with_objects(con, object_names: list[str]) -> dict[str | None, list[str]]:
    """Given a list of object names, return a dict mapping blend_file -> [objects].
    Lookup is performed by hash so it is case-insensitive and handles `hash_XXXXXXXX` references. The returned
    object names are the actual names stored in the .blend files.
    Objects not found in the cache are grouped under None, using the caller's original name strings.
    """
    import itertools

    def batched(iterable, n):
        it = iter(iterable)
        while chunk := list(itertools.islice(it, n)):
            yield chunk

    CHUNK_SIZE = 32766

    hash_to_input: dict[int, str] = {jenkhash.name_to_hash(name): name for name in object_names}

    groups: dict[str | None, list[str]] = {}
    found_hashes: set[int] = set()

    for chunk in batched(list(hash_to_input.keys()), CHUNK_SIZE):
        placeholders = ",".join("?" * len(chunk))
        rows = con.execute(
            f"SELECT blend_file, object_name, name_hash FROM object_locations WHERE name_hash IN ({placeholders})",
            chunk,
        ).fetchall()
        for blend_file, obj_name, name_hash in rows:
            groups.setdefault(blend_file, []).append(obj_name)
            found_hashes.add(name_hash)

    missing = [name for h, name in hash_to_input.items() if h not in found_hashes]
    if missing:
        groups[None] = missing

    return groups


def batch_create_objects_from_library(
    object_transforms: dict[str, list[tuple[int, Vector, Euler, Vector]]], object_linked_cb
) -> tuple[int, int]:
    """Instance archetypes from the shared asset library as library overrides.

    For each archetype referenced in ``object_transforms``, links the matching object from the library and creates one
    Blender *library override* per requested transform, linking each override into the current scene's root collection.
    Overrides are used so that per-instance transforms are editable without touching the library data-block.

    object_transforms: Mapping of archetype name to a list of ``(id, location, rotation, scale)`` tuples, one tuple per
        instance to create. ``id`` is an opaque caller-supplied identifier that is handed back to ``object_linked_cb``
        so the caller can associate each override with its source.
    object_linked_cb: Callable ``(obj: Object, id: int) -> None`` invoked once per created override, with the override
        object and its matching ``id``.

    Returns `(num_linked, num_missing)`, counts of successfully instanced and not-found-in-library archetypes.
    """
    object_names = list(object_transforms.keys())
    res = link_objects_from_library(object_names)
    if res is None:
        return 0, len(object_names)

    datas, num_missing = res

    # Key transforms by hash so lookups match the cache's hash-based
    # lookup (handles case differences and `hash_XXXXXXXX` references).
    transforms_by_hash: dict[int, list[tuple[int, Vector, Euler, Vector]]] = {
        jenkhash.name_to_hash(name): t_list for name, t_list in object_transforms.items()
    }

    num_linked = 0
    for data in datas:
        scene = bpy.context.scene
        for obj in data.objects:
            if obj is None:
                continue
            per_instance_transforms = transforms_by_hash.get(jenkhash.name_to_hash(obj.name), None)
            if not per_instance_transforms:
                continue

            for obj_id, loc, rot, scl in per_instance_transforms:
                obj_override = obj.override_create()
                obj_override.location = loc
                obj_override.rotation_euler = rot
                obj_override.scale = scl
                scene.collection.objects.link(obj_override)
                object_linked_cb(obj_override, obj_id)
                num_linked += 1

    return num_linked, num_missing


def link_objects_from_library(object_names: list[str]) -> tuple[list[BlendData], int] | None:
    prefs = get_addon_preferences(bpy.context)
    if not prefs.shared_assets_directories:
        return None

    db_path = asset_cache_path()

    if not db_path.exists():
        logger.warning(
            f"Asset cache not found at '{db_path}'. "
            f"Run 'Build Asset Library' or 'Rebuild Asset Cache' first. "
            f"Skipping game asset linking."
        )
        return None

    con = sqlite3.connect(db_path)
    try:
        results = find_library_blends_with_objects(con, object_names)
    except sqlite3.OperationalError as e:
        logger.warning(f"Asset cache is corrupted or has wrong schema: {e}. Skipping game asset linking.")
        return None
    finally:
        con.close()

    num_missing = 0
    datas = []
    for blend_file, names in results.items():
        if blend_file is None:
            # logger.info(f"Missing: {names=}")
            num_missing += len(names)
            continue

        blend_filepath = Path(blend_file)
        if not blend_filepath.exists():
            logger.warning(f"Asset library file not found: '{blend_filepath}'. Skipping {len(names)} objects.")
            num_missing += len(names)
            continue

        with bpy.data.libraries.load(
            str(blend_filepath),
            link=True,
            relative=False,
            assets_only=True,
        ) as (data_src, data_dst):
            data_dst.objects = names

        datas.append(data_dst)

    return datas, num_missing


def build_library(
    source_directory: Path, output_directory: Path, game_catalog: str, num_subprocesses: int, typ_pattern: str | None = None, report_progress_cb=None
) -> Iterator[float]:
    """Build a Blender asset library from the .ytyp and asset files found in `source_directory` recursively. For each
    .ytyp, a separate .blend library file is created.
    Implemented as an iterator so it is divided in units of work where each can be executed without blocking for too
    long. Yields the delay until next unit of work should be executed.
    Main work is done by Blender subprocesses, importing assets to the corresponding .blend.
    """
    from .game_files import GameFiles

    catalog_filepath = output_directory / "blender_assets.cats.txt"
    if not catalog_filepath.exists():
        catalog_filepath.touch()

    catalog_def = CatalogDefinitionFile([])
    catalog_def.parse(catalog_filepath)
    catalog_def.get_or_add_catalog(game_catalog)

    catalog_dir = source_directory.name

    cmds = []
    interior_cmds = []

    gf = GameFiles(source_directory)
    file_index = gf.read_asset_filelist([(".ytyp",), (".ydr",), (".yft",), (".ydd",), (".ytd",), (".ytyp.xml",), (".ydr.xml",), (".yft.xml",), (".ydd.xml",), (".ytd.xml",)])
    file_index_by_hash = GameFiles.index_by_name_hash(file_index)
    from itertools import chain
    import tempfile
    import pickle
    import re

    typ_pattern = re.compile(typ_pattern) if typ_pattern else None

    with tempfile.NamedTemporaryFile(delete=False) as file_index_by_hash_cache_file:
        pickle.dump(file_index_by_hash, file_index_by_hash_cache_file, protocol=pickle.HIGHEST_PROTOCOL)
        file_index_by_hash_cache_file.close()

        if gf.is_game_installation():
            # game directory
            skip_typs = (
                # bad .ytyps
                "x64h.rpf/levels/gta5/interiors/v_int_14.rpf/v_int_14.ytyp",
                "x64e.rpf/levels/generic/icons.rpf/icons.ytyp",

                # we don't really support composite entities
                "x64f.rpf/levels/gta5/destruction/exterior/des_heli_scrapyard.rpf/des_heli_scrapyard.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_apartmentblock.rpf/des_apartmentblock.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_aquaduct.rpf/des_aquaduct.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_canister.rpf/des_canister.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_farmhouse.rpf/des_farmhouse.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_gassign.rpf/des_gassign.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_gasstation.rpf/des_gasstation.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_heli_billboard.rpf/des_heli_billboard.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_heli_biotech.rpf/des_heli_biotech.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_heli_highway.rpf/des_heli_highway.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_heli_mansion.rpf/des_heli_mansion.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_jetsteal.rpf/des_jetsteal.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_methtrailer.rpf/des_methtrailer.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_protree.rpf/des_protree.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_scaffolding.rpf/des_scaffolding.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_setpiece.rpf/des_setpiece.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_setpiece2.rpf/des_setpiece2.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_shipsink.rpf/des_shipsink.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_stilthouse.rpf/des_stilthouse.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_tankercrash.rpf/des_tankercrash.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_tankerexplosion.rpf/des_tankerexplosion.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_trailerparka.rpf/des_trailerparka.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_trailerparkb.rpf/des_trailerparkb.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_trailerparkc.rpf/des_trailerparkc.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_trailerparkd.rpf/des_trailerparkd.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_trailerparke.rpf/des_trailerparke.ytyp",
                "x64f.rpf/levels/gta5/destruction/exterior/des_traincrash.rpf/des_traincrash.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_coroner_window.rpf/des_coroner_window.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_fib_ceiling.rpf/des_fib_ceiling.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_fib_door.rpf/des_fib_door.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_fib_floor.rpf/des_fib_floor.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_fib_glass.rpf/des_fib_glass.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_fibstairs.rpf/des_fibstairs.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_finale_tunnel.rpf/des_finale_tunnel.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_finale_vault.rpf/des_finale_vault.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_frenchdoors.rpf/des_frenchdoors.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_hosp_ceil.rpf/des_hosp_ceil.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_hosp_ceil2.rpf/des_hosp_ceil2.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_hospitaldoors.rpf/des_hospitaldoors.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_jewel_cab.rpf/des_jewel_cab.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_jewel_cab2.rpf/des_jewel_cab2.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_jewel_cab3.rpf/des_jewel_cab3.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_jewel_cab4.rpf/des_jewel_cab4.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_ranchsafe.rpf/des_ranchsafe.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_server.rpf/des_server.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_showroom.rpf/des_showroom.ytyp",
                "x64f.rpf/levels/gta5/destruction/interior/des_tvsmash.rpf/des_tvsmash.ytyp",
            )

            for typ_file_name, typ_file_paths in chain(file_index.get((".ytyp",), {}).items(), file_index.get((".ytyp", ".xml"), {}).items()):
                typ_file_path = typ_file_paths[-1]  # pick most recent .ytyp

                if any(typ_file_path.endswith(skip_typ) for skip_typ in skip_typs):
                    continue

                typ_name = typ_file_name.split(".", maxsplit=1)[0]

                if typ_pattern is not None and not typ_pattern.search(typ_name):
                    continue

                try:
                    typ: AssetMapTypes | None = try_load_asset(typ_file_path)
                except Exception:
                    typ = None

                if typ is None:
                    continue

                catalog_path = f"{game_catalog}/{catalog_dir}/{typ_name}" if catalog_dir else f"{game_catalog}/{typ_name}"
                cat = catalog_def.get_or_add_catalog(catalog_path)
                library_file = output_directory / f"_assets.{typ_name}.blend"

                cmds.append(
                    [
                        bpy.app.binary_path,
                        "-c",
                        "sz_create_asset_library",
                        "-d",
                        str(source_directory.absolute()),
                        "-i",
                        str(typ_file_path),
                        "-o",
                        str(library_file.absolute()),
                        "-c",
                        str(cat.uuid),
                        "-f",
                        file_index_by_hash_cache_file.name,
                    ]
                )

                has_mlo = any(a.type == ArchetypeType.MLO for a in typ.archetypes)
                if has_mlo:
                    interior_library_file = output_directory / f"_assets.{typ_name}.interiors.blend"
                    interior_cmds.append(
                        [
                            bpy.app.binary_path,
                            "-c",
                            "sz_create_asset_library",
                            "-d",
                            str(source_directory.absolute()),
                            "-i",
                            str(typ_file_path),
                            "-o",
                            str(interior_library_file.absolute()),
                            "-c",
                            str(cat.uuid),
                            "-f",
                            file_index_by_hash_cache_file.name,
                            "--interiors",
                        ]
                    )
        else:
            # external directory
            ext_ytyp = [".ytyp"]
            ext_ytyp_xml = [".ytyp", ".xml"]
            for typ_file in source_directory.glob("**/*.ytyp*"):
                ext = typ_file.suffixes
                if ext != ext_ytyp and ext != ext_ytyp_xml:
                    continue

                typ_name = typ_file.name.split(".", maxsplit=1)[0]

                if typ_pattern is not None and not typ_pattern.search(typ_name):
                    continue

                typ: AssetMapTypes | None = try_load_asset(typ_file)
                if typ is None:
                    continue

                catalog_path = f"{game_catalog}/{catalog_dir}/{typ_name}" if catalog_dir else f"{game_catalog}/{typ_name}"
                cat = catalog_def.get_or_add_catalog(catalog_path)
                library_file = output_directory / f"_assets.{typ_name}.blend"

                cmds.append(
                    [
                        bpy.app.binary_path,
                        "-c",
                        "sz_create_asset_library",
                        "-d",
                        str(source_directory.absolute()),
                        "-i",
                        str(typ_file.absolute()),
                        "-o",
                        str(library_file.absolute()),
                        "-c",
                        str(cat.uuid),
                        "-f",
                        file_index_by_hash_cache_file.name,
                    ]
                )

                has_mlo = any(a.type == ArchetypeType.MLO for a in typ.archetypes)
                if has_mlo:
                    interior_library_file = output_directory / f"_assets.{typ_name}.interiors.blend"
                    interior_cmds.append(
                        [
                            bpy.app.binary_path,
                            "-c",
                            "sz_create_asset_library",
                            "-d",
                            str(source_directory.absolute()),
                            "-i",
                            str(typ_file.absolute()),
                            "-o",
                            str(interior_library_file.absolute()),
                            "-c",
                            str(cat.uuid),
                            "-f",
                            file_index_by_hash_cache_file.name,
                            "--interiors",
                        ]
                    )

        if not cmds:
            logger.warning(f"No .ytyp files found in '{source_directory}'")
            yield 0.01
            return

        total = len(cmds) + len(interior_cmds)

        catalog_def.save(catalog_filepath)
        if report_progress_cb:
            report_progress_cb(0, total)
        proc_pool = ProcessPool(cmds, max_parallel=num_subprocesses)
        while proc_pool.update():
            if report_progress_cb:
                report_progress_cb(proc_pool.num_completed, total)
            # redraw progress bar
            tag_redraw(bpy.context, space_type="VIEW_3D", region_type="UI")
            yield 1.0

        if report_progress_cb:
            report_progress_cb(proc_pool.num_completed, total)
        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="UI")
        yield 0.05
        build_library_cache(_configured_shared_directories())

        if interior_cmds:
            # Process interiors after so they can use assets imported to the library
            interior_proc_pool = ProcessPool(interior_cmds, max_parallel=num_subprocesses)
            while interior_proc_pool.update():
                if report_progress_cb:
                    report_progress_cb(proc_pool.num_completed + interior_proc_pool.num_completed, total)
                # redraw progress bar
                tag_redraw(bpy.context, space_type="VIEW_3D", region_type="UI")
                yield 1.0

            yield 0.05
            build_library_cache(_configured_shared_directories())

        if report_progress_cb:
            report_progress_cb(None, None)
        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="UI")
        yield 0.01


def build_library_cache(directories: list[Path]):
    """Rebuild the unified `_assets.cache` SQLite lookup DB at `asset_cache_path()`.
    Walks every .blend under each directory and inserts one row per asset-marked object,
    keyed by `jenkhash(object_name)`, so later lookups by `link_objects_from_library`
    are case-insensitive and don't need to open every file. `blend_file` rows store absolute paths
    so a single cache can serve multiple configured shared asset directories.
    """
    db_path = asset_cache_path()

    con = sqlite3.connect(db_path)
    try:
        con.execute("DROP TABLE IF EXISTS object_locations")
        con.execute("""
            CREATE TABLE object_locations (
                name_hash   INTEGER PRIMARY KEY,
                object_name TEXT    NOT NULL,
                blend_file  TEXT    NOT NULL
            )
        """)
        con.commit()

        for directory in directories:
            pattern = "**/*.blend"
            for blend_file in directory.glob(pattern):
                with bpy.data.libraries.load(
                    str(blend_file.absolute()),
                    link=True,
                    relative=False,
                    assets_only=True,
                ) as (
                    data_src,
                    data_dst,
                ):
                    abs_blend_file = str(blend_file.absolute())
                    con.executemany(
                        "INSERT OR REPLACE INTO object_locations (name_hash, object_name, blend_file) VALUES (?, ?, ?)",
                        [(jenkhash.name_to_hash(name), name, abs_blend_file) for name in data_src.objects],
                    )

        con.commit()
    finally:
        con.close()
