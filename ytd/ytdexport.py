from pathlib import Path
from typing import Optional

import bpy
from bpy.types import Image, Scene
from szio.dds import DdsFile
from szio.gta5 import AssetTextureDictionary, EmbeddedTexture
from szio.types import DataSource

from .. import logger
from ..iecontext import ExportBundle, export_context
from .properties import TextureDictionary


def export_ytd(txd: TextureDictionary | None) -> ExportBundle:
    embedded_tex = []
    hi_embedded_tex = []
    asset, hi_asset = create_txd_asset(txd, out_embedded_textures=embedded_tex, out_embedded_textures_hi=hi_embedded_tex) if txd is not None else (None, None)
    return export_context().make_bundle(
        asset,
        ("+hi", hi_asset),
        extra_files=[t.data for t in embedded_tex],
        secondary_extra_files=[("+hi", [t.data for t in hi_embedded_tex])],
    )


def create_txd_asset(
    txd: TextureDictionary,
    out_embedded_textures: list[EmbeddedTexture] | None = None,
    out_embedded_textures_hi: list[EmbeddedTexture] | None = None,
) -> tuple[AssetTextureDictionary, AssetTextureDictionary | None]:
    textures: dict[str, EmbeddedTexture] = {}
    hi_textures: dict[str, EmbeddedTexture] = {}

    txd.refresh_from_sources(bpy.context)

    for slot in txd.textures:
        img = slot.image
        if img is None:
            continue

        texture_name = slot.name
        if not texture_name or texture_name in textures:
            continue

        texture, hi_texture = split_embedded_texture(img, texture_name)
        textures[texture_name] = texture
        if hi_texture is not None:
            hi_textures[texture_name] = hi_texture

    if out_embedded_textures is not None:
        out_embedded_textures.extend(textures.values())

    if out_embedded_textures_hi is not None and hi_textures:
        out_embedded_textures_hi.extend(hi_textures.values())

    return AssetTextureDictionary(textures=textures), AssetTextureDictionary(textures=hi_textures) if hi_textures else None


def split_embedded_texture(img: Image, texture_name: str) -> tuple[EmbeddedTexture, EmbeddedTexture | None]:
    """Extracts the DDS data of `img` and, if flagged as HD, splits it into a lower-resolution
    copy with the first mip level dropped and the original full-resolution copy.

    Returns `(texture, hi_texture)`. `texture` is the one to embed in the regular asset (possibly downsized);
    `hi_texture` is the full-resolution copy for the '+hi' texture dictionary counterpart, or `None` when
    `img` is not flagged as HD.
    """
    texture_data = extract_texture_dds_data_source(img, texture_name)
    width, height = img.size

    if not img.sz_is_hd:
        return EmbeddedTexture(texture_name, width, height, texture_data), None

    hi_texture = EmbeddedTexture(texture_name, width, height, texture_data)
    if (lo_texture_data := _drop_first_mip(img, texture_data)) is not None:
        texture_data = lo_texture_data
        width = max(1, width // 2)
        height = max(1, height // 2)

    return EmbeddedTexture(texture_name, width, height, texture_data), hi_texture


def _drop_first_mip(img: Image, texture_data: DataSource | None) -> DataSource | None:
    """DDS data of `texture_data` with the top mip level removed, for the lower-resolution variant
    of an HD texture. Returns None when there is no data or the mip cannot be dropped, in which case
    the full-resolution data should be kept.
    """
    if texture_data is None:
        return None
    try:
        dds = DdsFile.from_buffer(bytearray(texture_data.read_bytes()))
        return DataSource.create(dds.drop_mip(), texture_data.name)
    except (ValueError, OSError) as e:
        logger.warning(f"Cannot drop first mip of HD texture '{img.name}', keeping full resolution: {e}")
        return None


def extract_texture_dds_data_source(img: Image, texture_name: str) -> DataSource | None:
    texture_name_dds = f"{texture_name}.dds"
    texture_data = None
    packed = img.packed_file
    if packed and (packed_data := packed.data):
        # Embed packed data
        if not packed_data.startswith(b"DDS "):
            logger.warning(
                f"Embedded texture '{img.name}' packed data is not in DDS format. Please, convert it to a DDS file."
            )
        else:
            texture_data = DataSource.create(packed_data, texture_name_dds)
    else:
        # Embed external file
        texture_path = Path(bpy.path.abspath(img.filepath))
        if not texture_path.is_file():
            logger.warning(
                f"Embedded texture '{img.name}' file does not exist and the image is not packed. "
                f"File path: {texture_path}"
            )
        elif texture_path.suffix != ".dds":
            logger.warning(
                f"Embedded texture '{img.name}' is not in DDS format. Please, convert it to a DDS file."
                f"File path: {texture_path}"
            )
        else:
            texture_data = DataSource.create(texture_path, texture_name_dds)

    return texture_data
