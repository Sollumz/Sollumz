from pathlib import Path
from typing import Optional

import bpy
from bpy.types import Image, Scene

from szio.gta5 import AssetTextureDictionary, EmbeddedTexture
from szio.types import DataSource

from ..iecontext import ExportBundle, export_context
from .. import logger
from .properties import TextureDictionary


def export_ytd(txd: TextureDictionary) -> ExportBundle:
    embedded_tex = []
    asset = create_txd_asset(txd, out_embedded_textures=embedded_tex) if txd is not None else None
    return export_context().make_bundle(asset, extra_files=[t.data for t in embedded_tex])


def create_txd_asset(
    txd: TextureDictionary, out_embedded_textures: list[EmbeddedTexture] | None = None
) -> AssetTextureDictionary:
    textures: dict[str, EmbeddedTexture] = {}

    for slot in txd.textures:
        img = slot.image
        if img is None:
            continue

        texture_name = slot.name
        if not texture_name or texture_name in textures:
            continue

        texture_data = extract_texture_dds_data_source(img, texture_name)
        width, height = img.size
        textures[texture_name] = EmbeddedTexture(texture_name, width, height, texture_data)

    if out_embedded_textures is not None:
        out_embedded_textures.extend(textures.values())

    return AssetTextureDictionary(textures=textures)


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
