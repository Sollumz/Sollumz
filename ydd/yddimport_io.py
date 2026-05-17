import bpy
from bpy.types import (
    Object
)
from typing import Optional
from pathlib import Path
from szio.gta5 import (
    AssetFormat,
    AssetWithDependencies,
    AssetDrawableDictionary,
    AssetFragment,
    AssetClothDictionary,
    try_load_asset,
    Skeleton,
    jenkhash,
)
from ..ydr.ydrimport_io import create_drawable, create_drawable_skel
from ..ydr.cloth_char_io import (
    cloth_char_import_mesh,
    cloth_char_import_bounds,
)
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_empty_object, create_blender_object
from ..iecontext import import_context
from .. import logger


def find_ydd_external_dependencies(asset: AssetDrawableDictionary, name: str) -> AssetWithDependencies | None:
    prefers_xml = asset.ASSET_FORMAT == AssetFormat.CWXML
    deps = {}
    if import_context().settings.import_external_skeleton:
        # TODO: if multiple .yft, match by name and show a popup to allow the user to select the correct one
        skel_yft = try_load_external_skeleton()

        if skel_yft is not None:
            d = skel_yft.drawable
            if d is not None and d.skeleton is not None:
                deps["external_skel"] = skel_yft

    cloth_dictionary = try_load_cloth_dictionary(name, prefers_xml)
    if cloth_dictionary is not None:
        deps["cloth"] = cloth_dictionary

    return AssetWithDependencies(name, asset, deps)


def try_load_cloth_dictionary(name: str, prefers_xml: bool) -> AssetClothDictionary | None:
    d = import_context().directory
    cloth_dictionary = None

    possible_exts = (".yld", ".yld.xml")
    if prefers_xml:
        possible_exts = possible_exts[::-1]

    for ext in possible_exts:
        cloth_dictionary_path = d / f"{name}{ext}"
        if cloth_dictionary_path.is_file():
            cloth_dictionary = try_load_asset(cloth_dictionary_path)
            if cloth_dictionary:
                break

    return cloth_dictionary


def try_load_external_skeleton() -> Optional[AssetFragment]:
    """Read first yft at ydd_filepath into a Fragment"""
    directory = import_context().directory

    yft_filepath = get_first_yft_path(directory)

    if yft_filepath is None:
        logger.warning(f"Could not find external skeleton yft in directory '{directory}'.")
        return None

    yft = try_load_asset(yft_filepath)
    if yft is None:
        logger.warning(f"Could not load external skeleton yft '{yft_filepath}'.")
        return None

    logger.info(f"Using '{yft_filepath}' as external skeleton...")
    return yft


def get_first_yft_path(directory: Path) -> Optional[Path]:
    for file in directory.iterdir():
        if file.is_file() and ((name := file.name).endswith(".yft") or name.endswith(".yft.xml")):
            return file

    return None


def import_ydd(asset: AssetWithDependencies, name: str) -> Object | list[Object]:
    dwd = asset.main_asset
    skel_frag = asset.dependencies.get("external_skel", None)
    cloth_dictionary = asset.dependencies.get("cloth", None)

    return create_drawable_dictionary(dwd, name, cloth_dictionary, skel_frag)


def create_drawable_dictionary(
    dwd: AssetDrawableDictionary,
    name: str,
    cloth_dictionary: AssetClothDictionary | None,
    external_skel_frag: AssetFragment | None
) -> Object | list[Object]:
    import_as_asset = import_context().settings.import_as_asset

    if import_as_asset:
        dict_obj = None
        dict_assets = []
    else:
        if external_skel_frag is not None:
            dict_obj = create_armature_parent(name, external_skel_frag)
        else:
            dict_obj = create_empty_object(SollumType.DRAWABLE_DICTIONARY, name)

    dwd_skel = find_first_skeleton(dwd)

    cloths = cloth_dictionary.cloths if cloth_dictionary else {}
    cloths = {jenkhash.name_to_hash(k): v for k, v in cloths.items()}

    for name, drawable in dwd.drawables.items():
        skeleton = drawable.skeleton

        external_armature = None
        external_skeleton = None
        if external_skel_frag is not None:
            if skeleton is None or not skeleton.bones:
                external_skeleton = external_skel_frag.drawable.skeleton
                external_armature = dict_obj
        else:
            if (skeleton is None or not skeleton.bones) and dwd_skel is not None:
                external_skeleton = dwd_skel

        drawable_obj = create_drawable(
            drawable,
            name=name,
            external_armature=external_armature,
            external_skeleton=external_skeleton
        )
        drawable_obj.parent = dict_obj
        if import_as_asset:
            from ..ydr.ydrimport import convert_object_to_asset
            drawable_obj_asset = convert_object_to_asset(name, drawable_obj)
            dict_assets.append(drawable_obj_asset)

        if not import_as_asset and cloths and (cloth := cloths.get(jenkhash.name_to_hash(name), None)):
            cloth_obj = cloth_char_import_mesh(cloth, drawable_obj, external_armature or drawable_obj)
            cloth_obj.parent = drawable_obj
            bounds_obj = cloth_char_import_bounds(cloth, external_armature or drawable_obj)
            bounds_obj.parent = cloth_obj

    return dict_assets if import_as_asset else dict_obj


def create_armature_parent(name: str, skel: AssetFragment) -> Object:
    armature = bpy.data.armatures.new(f"{name}.skel")
    dict_obj = create_blender_object(SollumType.DRAWABLE_DICTIONARY, name, armature)
    create_drawable_skel(dict_obj, skel.drawable.skeleton)
    return dict_obj


def find_first_skeleton(dwd: AssetDrawableDictionary) -> Optional[Skeleton]:
    """Find first skeleton in a drawable dictionary"""
    for drawable in dwd.drawables.values():
        skeleton = drawable.skeleton
        if skeleton is not None and skeleton.bones:
            return skeleton

    return None
