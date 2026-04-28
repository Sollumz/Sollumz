import os
import re
from collections.abc import Iterator

import bpy
from bpy.props import (
    BoolProperty,
    EnumProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Context,
    Image,
    PropertyGroup,
    Scene,
    ShaderNodeTexImage,
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

    managed_by_source: BoolProperty(name="Managed by Source", default=False)


class TextureSlotSelectionAccess(MultiSelectAccess):
    pass


class TextureImageSourceSlot(PropertyGroup):
    image: PointerProperty(type=Image, name="Image")
    use: BoolProperty(name="Use Image")


class TextureImageSourceSlotSelectionAccess(MultiSelectAccess):
    use: MultiSelectProperty()


@define_multiselect_collection("images", {"name": "Images"})
class TextureImageSource(PropertyGroup):
    source_type: EnumProperty(
        name="Source Type",
        items=(("OBJECT", "Object", ""),),
        default="OBJECT",
    )
    images: MultiSelectCollection[TextureImageSourceSlot, TextureImageSourceSlotSelectionAccess]

    def object_name_search(self, context: Context, edit_text: str) -> Iterator[str]:
        for obj in context.scene.objects:
            yield obj.name

    object_name: StringProperty(name="Object", search=object_name_search)
    object_include_children: BoolProperty(name="Include Children", default=True)

    def refresh(self, context: Context):
        existing_images_use_flags = {s.image: s.use for s in self.images}

        self.images.clear()
        for image, default_use in sorted(self.find_images(context), key=lambda t: t[0].name):
            s = self.images.add()
            s.image = image
            s.use = existing_images_use_flags.get(image, default_use)

    def find_images(self, context: Context) -> list[tuple[Image, bool]]:
        match self.source_type:
            case "OBJECT":
                return self._find_images_from_object(context)

        return []

    def _find_images_from_object(self, context: Context) -> list[tuple[Image, bool]]:
        obj = context.scene.objects.get(self.object_name, None)
        if obj is None:
            return []

        from ..sollumz_helper import get_sollumz_materials

        found_images = set()
        images = []
        mat_to_model = {}
        mats = get_sollumz_materials(obj, out_material_to_models=mat_to_model, include_root_obj=True)
        for mat in mats:
            use_mat = self.object_include_children or obj in mat_to_model[mat]
            if not use_mat:
                continue

            nodes = mat.node_tree.nodes
            for node in nodes:
                if isinstance(node, ShaderNodeTexImage) and (img := node.image):
                    default_use = True
                    if node.texture_properties.embedded:
                        default_use = False

                    if img not in found_images:
                        images.append((img, default_use))
                        found_images.add(img)

        return images


class TextureImageSourceSelectionAccess(MultiSelectAccess):
    source_type: MultiSelectProperty()
    object_name: MultiSelectProperty()
    object_include_children: MultiSelectProperty()


@define_multiselect_collection("textures", {"name": "Textures"})
@define_multiselect_collection("sources", {"name": "Sources"})
class TextureDictionary(PropertyGroup):
    name: StringProperty(name="Name", default="")
    textures: MultiSelectCollection[TextureSlot, TextureSlotSelectionAccess]
    sources: MultiSelectCollection[TextureImageSource, TextureImageSourceSelectionAccess]

    def new_texture(self, image: Image | None = None) -> TextureSlot:
        slot = self.textures.add()
        self.textures.select(len(self.textures) - 1)
        if image is not None:
            slot.image = image
        return slot

    def new_source(self) -> TextureImageSource:
        src = self.sources.add()
        self.sources.select(len(self.sources) - 1)
        return src

    def refresh_from_sources(self):
        # TODO(txd): not clear all textures
        self._remove_textures_from_sources()

        images = set(s.image for src in self.sources for s in src.images if s.use)
        images = sorted(images, key=lambda img: img.name)
        for img in images:
            tex = self.textures.add()
            tex.image = img
            tex.managed_by_source = True

        if self.textures:
            self.textures.select(0)

    def _remove_textures_from_sources(self):
        indices_to_remove = [i for i, tex in enumerate(self.textures) if tex.managed_by_source]
        if not indices_to_remove:
            return

        indices_to_remove = sorted(indices_to_remove, reverse=True)
        new_active_index = max(indices_to_remove[-1] - 1, 0)
        for idx in indices_to_remove:
            self.textures.remove(idx)

        if self.textures:
            self.textures.select(min(new_active_index, len(self.textures) - 1))


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
