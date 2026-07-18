from pathlib import Path

import bpy
from szio.gta5 import (
    AssetFormat,
    AssetTextureDictionary,
    AssetWithDependencies,
    EmbeddedTexture,
    try_load_asset,
)

from ..iecontext import ImportTexturesMode, import_context
from .properties import TextureDictionary


def find_ytd_external_dependencies(asset: AssetTextureDictionary, name: str) -> AssetWithDependencies:
    prefers_xml = import_context().asset_target.format == AssetFormat.CWXML
    if is_hi_txd(name):
        # User selected a +hi.ytd, look for the base .ytd file
        non_hi_txd = try_load_non_hi_txd(name, prefers_xml)
        if non_hi_txd is None:
            # No base .ytd found, import the +hi.ytd as a regular texture dictionary
            return AssetWithDependencies(name, asset, {})

        hi_txd = asset
        name = make_txd_base_name(name)
    else:
        # User selected the base .ytd, optionally look for the +hi.ytd
        non_hi_txd = asset
        hi_txd = try_load_hi_txd(name, prefers_xml)

    return AssetWithDependencies(name, non_hi_txd, {"hi": hi_txd} if hi_txd else {})


def is_hi_txd(name: str) -> bool:
    """Is this a +hi.ytd file?"""
    return name.endswith("+hi")


def make_txd_base_name(name: str) -> str:
    if name.endswith("+hi"):
        name = name[:-3]  # trim '+hi'
    return name


def try_load_non_hi_txd(name: str, prefers_xml: bool) -> AssetTextureDictionary | None:
    return try_load_hd_txd(make_txd_base_name(name), prefers_xml, "")


def try_load_hi_txd(name: str, prefers_xml: bool) -> AssetTextureDictionary | None:
    return try_load_hd_txd(make_txd_base_name(name), prefers_xml, "+hi")


def try_load_hd_txd(name: str, prefers_xml: bool, suffix: str) -> AssetTextureDictionary | None:
    d = import_context().directory
    hd_txd = None

    possible_exts = (".ytd", ".ytd.xml")
    if prefers_xml:
        possible_exts = possible_exts[::-1]

    for ext in possible_exts:
        hd_path = d / f"{name}{suffix}{ext}"
        if hd_path.is_file():
            hd_txd = try_load_asset(hd_path)
            if hd_txd:
                break

    return hd_txd


def import_ytd(asset: AssetWithDependencies, name: str) -> TextureDictionary:
    """Create a Texture Dictionary data-block in the Blender scene from a YTD asset."""
    non_hi_txd = asset.main_asset
    hi_txd = asset.dependencies.get("hi", None)
    hi_textures = hi_txd.textures if hi_txd is not None else {}

    scene = bpy.context.scene
    txd = scene.sz_txds.new_texture_dictionary(name=name)

    extract_embedded_textures(non_hi_txd.textures)
    extract_embedded_textures(hi_textures, dir_suffix="+hi")

    # The base .ytd stores a low-resolution copy of each texture in the +hi.ytd. Only import the
    # high-resolution version; export rebuilds the low-resolution copy by dropping the first mip.
    base_textures = {n: t for n, t in non_hi_txd.textures.items() if n not in hi_textures}

    for tex in sorted((base_textures | hi_textures).values(), key=lambda t: t.name):
        is_hd = tex.name in hi_textures
        img = _create_or_get_image(tex, dir_suffix="+hi" if is_hd else "")
        if is_hd:
            img.sz_is_hd = True
        txd.new_texture(img)
    if txd.textures:
        txd.textures.select(0)

    return txd


def _with_dir_suffix(d: Path | None, suffix: str) -> Path | None:
    return d.with_name(d.name + suffix) if (d is not None and suffix) else d


def _create_or_get_image(tex: EmbeddedTexture, dir_suffix: str = "") -> bpy.types.Image:
    ctx = import_context()
    textures_dir = _with_dir_suffix(ctx.textures_extract_directory or ctx.textures_import_directory, dir_suffix)

    tex_name = tex.name
    tex_name_dds = f"{tex_name}.dds"

    pack = ctx.settings.textures_mode == ImportTexturesMode.PACK
    img = None
    if pack and tex.data:
        # If pack mode and we have embedded texture data, load it into a packed image directly
        with tex.data.open() as src:
            tex_dds = src.read()

        img = bpy.data.images.new(name=tex_name_dds, width=1, height=1)
        img.source = "FILE"
        img.filepath = f"//{tex_name_dds}"
        img.pack(data=tex_dds, data_len=len(tex_dds))

    if not img and textures_dir and textures_dir.is_dir():
        # Try to load texture from file
        if texture_path := lookup_texture_file(tex_name, textures_dir, use_shared_textures_directories=False):
            img = bpy.data.images.load(str(texture_path), check_existing=True)
            if pack:
                img.pack()

    if not img:
        # Check for existing texture image
        img = bpy.data.images.get(tex_name, None) or bpy.data.images.get(tex_name_dds, None)

    if not img:
        # Create placeholder image if still not found
        img = bpy.data.images.new(name=tex_name, width=512, height=512)

    return img


def lookup_texture_file(
    texture_name: str, textures_directory: Path | None, use_shared_textures_directories: bool = False
) -> Path | None:
    """Searches for a DDS file with the given ``texture_name``.
    The search order is as follows:
      1. Check if file exists in ``textures_directory``.
      2. Check the shared textures directories defined by the user in the add-on preferences.
        2.1. These are searched in the priority order set by the user.
        2.2. The user can also set whether the search is recursive or not.
      3. If not found, returns ``None``.
    """
    texture_filename = f"{texture_name}.dds"

    def _lookup_in_directory(directory: Path, recursive: bool) -> Path | None:
        if not directory.is_dir():
            return None

        if recursive:
            # NOTE: rglob returns files in arbitrary order. We are just taking whatever is the first one it returns.
            #       Maybe we should enforce some kind of sort (i.e. alphabetical), but really only makes sense to have
            #       a single texture with this the name in the directory tree.
            texture_path = next(directory.rglob(texture_filename), None)
        else:
            texture_path = directory.joinpath(texture_filename)

        return texture_path if texture_path is not None and texture_path.is_file() else None

    # First, check the textures directory next to the model we imported
    found_texture_path = textures_directory and _lookup_in_directory(textures_directory, False)
    if found_texture_path is not None:
        return found_texture_path

    if use_shared_textures_directories:
        # Texture not found, search the shared textures directories listed in preferences
        from ..sollumz_preferences import get_addon_preferences

        prefs = get_addon_preferences(bpy.context)
        for d in prefs.shared_textures_directories:
            found_texture_path = _lookup_in_directory(Path(d.path), d.recursive)
            if found_texture_path is not None:
                return found_texture_path

    # Texture still not found
    return None


def extract_embedded_textures(embedded_textures: dict[str, EmbeddedTexture], dir_suffix: str = ""):
    import shutil

    if not embedded_textures:
        return

    ctx = import_context()
    if ctx.settings.textures_mode == ImportTexturesMode.PACK:
        return

    textures = [t.data for t in embedded_textures.values() if t.data is not None]
    if not textures and ctx.settings.textures_mode == ImportTexturesMode.CUSTOM_DIR:
        # If no embedded textures data (e.g. importing CWXML), try to lookup external texture files in import directory
        # so we can copy them to the user custom directory
        textures_import_dir = _with_dir_suffix(ctx.textures_import_directory, dir_suffix)
        if textures_import_dir.is_dir():
            from szio.types import DataSource

            textures = [
                DataSource.create(p)
                for t in embedded_textures.values()
                if (p := textures_import_dir / f"{t.name}.dds").is_file()
            ]

    if not textures:
        return

    textures_extract_dir = _with_dir_suffix(ctx.textures_extract_directory, dir_suffix)
    if textures_extract_dir is None:
        return

    textures_extract_dir.mkdir(parents=True, exist_ok=True)
    for tex_data in textures:
        tex_file = textures_extract_dir / tex_data.name
        if tex_file.exists():
            # Don't overwrite existing files
            continue

        with tex_data.open() as src, tex_file.open("wb") as dst:
            shutil.copyfileobj(src, dst)
