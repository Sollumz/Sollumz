import os
import re

import bpy
from bpy.props import (
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Image,
    PropertyGroup,
    Scene,
)

from ..shared.multiselection import (
    MultiSelectAccess,
    MultiSelectCollection,
    MultiSelectProperty,
    define_multiselect_collection,
)

_TRAILING_BLENDER_SUFFIX_RE = re.compile(r"\.\d{3}$")


def _derive_texture_name(image: Image | None) -> str:
    if image:
        return os.path.splitext(bpy.path.basename(image.filepath))[0]
    return ""


class TextureSlot(PropertyGroup):
    image: PointerProperty(type=Image, name="Image")

    def get_name(self) -> str:
        return _derive_texture_name(self.image)

    name: StringProperty(name="Name", get=get_name)


class TextureSlotSelectionAccess(MultiSelectAccess):
    pass


@define_multiselect_collection("textures", {"name": "Textures"})
class TextureDictionary(PropertyGroup):
    name: StringProperty(name="Name", default="")
    textures: MultiSelectCollection[TextureSlot, TextureSlotSelectionAccess]

    def new_texture(self, image: Image | None = None) -> TextureSlot:
        slot = self.textures.add()
        self.textures.select(len(self.textures) - 1)
        if image is not None:
            slot.image = image
        return slot


class TextureDictionarySelectionAccess(MultiSelectAccess):
    name: MultiSelectProperty()


@define_multiselect_collection("texture_dictionaries", {"name": "Texture Dictionaries"})
class TextureDictionaries(PropertyGroup):
    texture_dictionaries: MultiSelectCollection[TextureDictionary, TextureDictionarySelectionAccess]

    def new_texture_dictionary(self, name: str | None = None) -> TextureDictionary:
        txd = self.texture_dictionaries.add()
        index = len(self.texture_dictionaries) - 1
        self.texture_dictionaries.select(index)
        if name:
            txd.name = name
        else:
            txd.name = f"TXD.{index + 1}"
        return txd


def register():
    Scene.sz_txds = PointerProperty(
        type=TextureDictionaries,
        name="Texture Dictionaries",
    )


def unregister():
    del Scene.sz_txds
