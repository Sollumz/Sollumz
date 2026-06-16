import bpy
import json
from pathlib import Path
from szio import VPath
from szio.gta5 import (
    AssetMapTypes,
    ArchetypeType,
    ArchetypeAssetType,
    try_load_asset,
)
from szio.jenkhash import name_to_hash
from ..shared.game_assets.game_files import GameFiles

CMD_ID = "sz_create_asset_library"


def import_props_from_ytyp(directory: Path, typ_file: Path, catalog_id: str, cached_file_index_path: Path | None):
    typ: AssetMapTypes = try_load_asset(typ_file)
    archetypes = typ.archetypes
    archetypes_by_hash = {name_to_hash(a.name): a for a in archetypes}

    # Build a lookup of (filename hash, extensions) -> path for all files in directory
    if cached_file_index_path is not None and cached_file_index_path.is_file():
        import pickle
        with cached_file_index_path.open("rb") as fp:
            file_index = pickle.load(fp)
    else:
        file_index = GameFiles(directory).read_asset_filelist()
        file_index = GameFiles.index_by_name_hash(file_index)
    # file_index = {}
    # for f in directory.rglob("*"):
    #     if not f.is_file():
    #         continue
    #
    #     exts = tuple(f.suffixes)
    #     # pathlib's stem only removes the last extension
    #     stem = f.name[: -sum(map(len, exts))] if exts else f.name
    #     stem_hash = name_to_hash(stem)
    #     file_index[(stem_hash, exts)] = f

    def _file_index_lookup(filename_hash: int, ext: str) -> VPath | None:
        p = (file_index.get((ext,), {}) or file_index.get((ext, ".xml"), {})).get(filename_hash, None)
        return VPath(p[-1]) if p else None

    files = []
    def _add_file_to_import(filepath: VPath):
        if filepath is None or not filepath.is_file():
            print(f"not found {filepath}")
        else:
            files.append({"name": str(Path(str(filepath)).relative_to(directory))})

    found_dwd = set()
    found_txd = set()
    for arch in archetypes:
        if arch.type == ArchetypeType.MLO:
            continue

        asset_ext = None
        asset_filename_hash = name_to_hash(arch.asset_name)
        match arch.asset_type:
            case ArchetypeAssetType.DRAWABLE:
                asset_ext = ".ydr"
            case ArchetypeAssetType.FRAGMENT:
                asset_ext = ".yft"
            case ArchetypeAssetType.DRAWABLE_DICTIONARY:
                asset_filename_hash = name_to_hash(arch.drawable_dictionary)
                asset_ext = ".ydd"
                if asset_filename_hash in found_dwd:
                    continue
                found_dwd.add(asset_filename_hash)
            case _:
                print(f"Unsupported asset type '{arch.asset_type.name}'")
                continue

        if arch.texture_dictionary:
            txd_hash = name_to_hash(arch.texture_dictionary)
            if txd_hash not in found_txd:
                txd_filepath = _file_index_lookup(txd_hash, ".ytd")
                _add_file_to_import(txd_filepath)
                found_txd.add(txd_hash)

        asset_filepath = _file_index_lookup(asset_filename_hash, asset_ext)
        _add_file_to_import(asset_filepath)

    bpy.ops.sollumz.import_assets(
        directory=str(directory.absolute()),
        files=files,
        use_custom_settings=True,
        import_as_asset=True,
        textures_mode="PACK",
    )

    objs_to_remove = []
    for obj in bpy.data.objects:
        asset_data = obj.asset_data
        if asset_data:
            asset_data.catalog_id = catalog_id
            arch = archetypes_by_hash.get(name_to_hash(obj.name))
            if arch is None:
                # A .ydd can be used by multiple .ytyps, so we may have imported
                # models that are not all defined in the current .ytyp. Delete them
                objs_to_remove.append(obj)
                continue

            if obj.name.startswith("hash_") and not arch.name.startswith("hash_"):
                # The .ytyp may have the solved name
                obj.name = arch.name.lower()

            arch_info = json.dumps(
                {
                    "ytyp": typ.name,
                    "type": arch.type.name,
                    "lod_dist": arch.lod_dist,
                    "bb_min": tuple(arch.bb_min),
                    "bb_max": tuple(arch.bb_max),
                    "num_extensions": len(arch.extensions) if arch.extensions else 0,
                },
                separators=(",", ":"),
                indent=None,
            )

            asset_data["sz_asset_archetype_info"] = arch_info
            obj["sz_asset_archetype_info"] = arch_info
            obj.data["sz_asset_archetype_info"] = arch_info

    bpy.data.batch_remove(objs_to_remove)


def import_interiors_from_ytyp(typ_file: Path, catalog_id: str):
    from ..ytyp.properties.ytyp import CMapTypesProperties, ArchetypeType

    typ_dir = typ_file.parent.absolute()
    bpy.ops.sollumz.import_assets(
        directory=str(typ_dir),
        files=[{"name": str(typ_file.absolute().relative_to(typ_dir))}],
        use_custom_settings=True,
        ytyp_mlo_instance_entities=True,
    )

    scene = bpy.context.scene
    map_types: CMapTypesProperties = scene.ytyps[0]
    for arch in map_types.archetypes:
        if arch.type != ArchetypeType.MLO:
            continue

        arch_info = json.dumps(
            {
                "ytyp": map_types.name,
                "type": "MLO",
                "lod_dist": arch.lod_dist,
                "bb_min": tuple(arch.bb_min),
                "bb_max": tuple(arch.bb_max),
                "num_extensions": len(arch.extensions) if arch.extensions else 0,
            },
            separators=(",", ":"),
            indent=None,
        )

        mlo_collection: bpy.types.Collection = bpy.data.collections[arch.name]
        mlo_collection.asset_mark()
        mlo_collection.asset_generate_preview()
        asset_data = mlo_collection.asset_data
        asset_data.catalog_id = catalog_id
        asset_data["sz_asset_archetype_info"] = arch_info
        mlo_collection["sz_asset_archetype_info"] = arch_info

        # Create an object instancing the collection so the game assets library code doesn't have to deal with both
        # objects and colections, and just use objects always
        mlo_collection_instance_obj = bpy.data.objects.new(arch.name, None)
        mlo_collection_instance_obj.instance_type = "COLLECTION"
        mlo_collection_instance_obj.instance_collection = mlo_collection
        bpy.context.collection.objects.link(mlo_collection_instance_obj)
        mlo_collection_instance_obj.asset_mark()
        mlo_collection_instance_obj.asset_generate_preview()
        asset_data = mlo_collection_instance_obj.asset_data
        asset_data.catalog_id = catalog_id
        asset_data["sz_asset_archetype_info"] = arch_info
        mlo_collection_instance_obj["sz_asset_archetype_info"] = arch_info


def create_library_from_ytyp(
    directory: Path, typ_file: Path, out_library_file: Path, catalog_id: str, interiors_only: bool, cached_file_index_path: Path | None
):
    bpy.ops.wm.read_homefile(use_factory_startup=True, use_empty=True)

    if interiors_only:
        import_interiors_from_ytyp(typ_file, catalog_id)
    else:
        import_props_from_ytyp(directory, typ_file, catalog_id, cached_file_index_path)

    for scene in bpy.data.scenes:
        scene.sz_txds.texture_dictionaries.clear()

    bpy.data.orphans_purge(do_recursive=True)

    bpy.ops.wm.save_mainfile(filepath=str(out_library_file.absolute()), compress=True)


def main(argv: list[str]) -> int:
    import sys
    import os
    from argparse import ArgumentParser

    parser = ArgumentParser(
        prog=os.path.basename(sys.argv[0]) + " --command " + CMD_ID,
        description="Create asset library.",
    )
    parser.add_argument(
        "-d",
        "--directory",
        type=Path,
        help="Base directory to search assets in.",
        required=True,
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Input .ytyp file.",
        required=True,
    )
    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help="Output .blend file.",
        required=True,
    )
    parser.add_argument(
        "-c",
        "--catalog",
        type=str,
        help="Catalog UUID assigned to assets.",
        required=True,
    )
    parser.add_argument(
        "--interiors",
        action="store_true",
        help="Create asset library of interiors (MLOs) instead of props.",
    )
    parser.add_argument(
        "-f",
        "--file-index",
        type=Path,
    )
    args = parser.parse_args(argv)

    create_library_from_ytyp(args.directory, args.input, args.output, args.catalog, args.interiors, args.file_index)

    return 0


CMD = (CMD_ID, main)
