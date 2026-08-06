import os
import re
from collections.abc import Iterator

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Context,
    Image,
    Object,
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


def get_texture_name(image: Image | None) -> str:
    if image:
        return os.path.splitext(bpy.path.basename(image.filepath))[0].lower()
    return ""


class TextureSlot(PropertyGroup):
    image: PointerProperty(type=Image, name="Image")

    def get_name(self) -> str:
        return get_texture_name(self.image)

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
        items=(
            ("OBJECT", "Object", "", "OBJECT_DATA", 0),
            ("COLLECTION", "Collection", "", "OUTLINER_COLLECTION", 1),
        ),
        default="OBJECT",
    )
    images: MultiSelectCollection[TextureImageSourceSlot, TextureImageSourceSlotSelectionAccess]

    def object_name_search(self, context: Context, _edit_text: str) -> Iterator[str]:
        for obj in context.scene.objects:
            yield obj.name

    object_name: StringProperty(name="Object", search=object_name_search)
    object_include_children: BoolProperty(name="Include Children", default=True)

    def collection_name_search(self, _context: Context, _edit_text: str) -> Iterator[str]:
        for coll in bpy.data.collections:
            yield coll.name

    collection_name: StringProperty(name="Collection", search=collection_name_search)
    collection_include_children: BoolProperty(name="Include Children", default=True)

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
            case "COLLECTION":
                return self._find_images_from_collection()

        return []

    def _find_images_from_object(self, context: Context) -> list[tuple[Image, bool]]:
        obj = context.scene.objects.get(self.object_name, None)
        if obj is None:
            return []

        found_images = set()
        images = []
        self._add_images_from_object(obj, self.object_include_children, found_images, images)
        return images

    def _find_images_from_collection(self) -> list[tuple[Image, bool]]:
        coll = bpy.data.collections.get(self.collection_name, None)
        if coll is None:
            return []

        found_images = set()
        images = []
        objects = coll.all_objects if self.collection_include_children else coll.objects
        for obj in objects:
            self._add_images_from_object(obj, True, found_images, images)
        return images

    def _add_images_from_object(
        self, obj: Object, include_children: bool, found_images: set[Image], images: list[tuple[Image, bool]]
    ):
        from ..sollumz_helper import get_sollumz_materials

        mat_to_model = {}
        mats = get_sollumz_materials(obj, out_material_to_models=mat_to_model, include_root_obj=True)
        for mat in mats:
            use_mat = include_children or obj in mat_to_model[mat]
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


class TextureImageSourceSelectionAccess(MultiSelectAccess):
    source_type: MultiSelectProperty()
    object_name: MultiSelectProperty()
    object_include_children: MultiSelectProperty()
    collection_name: MultiSelectProperty()
    collection_include_children: MultiSelectProperty()


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

    def refresh_from_sources(self, context: Context):
        for src in self.sources:
            src.refresh(context)

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


class GtxdNode(PropertyGroup):

    def get_name(self) -> str:
        return self.get("name_", "")

    def set_name(self, new_name: str):
        old_name = self.get("name_", "")
        new_name = new_name.strip()
        self["name_"] = new_name

        gtxd = get_gtxd_for_node(self.id_data, self)
        if gtxd is not None and old_name and new_name and old_name.lower() != new_name.lower():
            for node in gtxd.nodes:
                if node.parent.strip().lower() == old_name.lower():
                    node["parent_"] = new_name

        if gtxd is not None:
            refresh_gtxd_ui(gtxd)

    def search_names(self, context: Context, edit_text: str) -> Iterator[str]:
        for txd in context.scene.sz_txds.texture_dictionaries:
            if txd.name:
                yield txd.name

    name: StringProperty(name="Name", get=get_name, set=set_name, search=search_names)

    def get_parent(self) -> str:
        return self.get("parent_", "")

    def set_parent(self, new_parent: str):
        self["parent_"] = new_parent.strip()
        if gtxd := get_gtxd_for_node(self.id_data, self):
            refresh_gtxd_ui(gtxd)

    def search_parents(self, context: Context, edit_text: str) -> Iterator[str]:
        gtxd = get_gtxd_for_node(context.scene, self)
        if gtxd is None:
            return
        pointer = self.as_pointer()
        for node in get_gtxd_ui_order(gtxd):
            if node.as_pointer() != pointer:
                yield node.ui_label

    parent: StringProperty(
        name="Parent",
        description="Texture dictionary this one inherits the textures from. Leave empty to place it at the root",
        get=get_parent,
        set=set_parent,
        search=search_parents,
    )

    ui_tree_depth: IntProperty(min=0)
    ui_tree_sort_id: IntProperty()
    ui_is_orphan: BoolProperty(default=False)

    def get_ui_label(self) -> str:
        return self.name or "Set name..."

    def set_ui_label(self, s: str):
        s = s.strip()
        self.name = "" if s == "Set name..." else s

    ui_label: StringProperty(get=get_ui_label, set=set_ui_label)


class Gtxd(PropertyGroup):
    name: StringProperty(name="Name", default="gtxd")
    nodes: CollectionProperty(type=GtxdNode, name="Texture Dictionaries")
    node_index: IntProperty(name="Texture Dictionary")
def get_selected_gtxd(context: Context) -> Gtxd | None:
    gtxds = context.scene.sz_gtxds
    index = context.scene.sz_gtxd_index
    return gtxds[index] if 0 <= index < len(gtxds) else None
def get_gtxd_for_node(scene: Scene, target: GtxdNode) -> Gtxd | None:
    pointer = target.as_pointer()
    for gtxd in scene.sz_gtxds:
        if any(node.as_pointer() == pointer for node in gtxd.nodes):
            return gtxd
    return None
def get_gtxd_ui_order(gtxd: Gtxd) -> list[GtxdNode]:
    ordered = list(gtxd.nodes)
    for node in gtxd.nodes:
        ordered[node.ui_tree_sort_id] = node
    return ordered
def refresh_gtxd_ui(gtxd: Gtxd):
    nodes = gtxd.nodes

    children = {}
    roots = []
    names = {n.name.strip().lower() for n in nodes if n.name.strip()}
    for node in nodes:
        node.ui_is_orphan = False
        parent = node.parent.strip().lower()
        if not parent:
            roots.append(node)
        elif parent in names:
            children.setdefault(parent, []).append(node)
        else:
            node.ui_is_orphan = True
            roots.append(node)

    sort_id = -1
    visited = set()

    def _add_to_ui(node, depth):
        nonlocal sort_id
        sort_id += 1
        node.ui_tree_sort_id = sort_id
        node.ui_tree_depth = depth
        visited.add(node.as_pointer())

        for child in children.get(node.name.strip().lower(), []):
            if child.as_pointer() not in visited:
                _add_to_ui(child, depth + 1)

    for root in roots:
        _add_to_ui(root, 0)

    for node in nodes:
        if node.as_pointer() not in visited:
            sort_id += 1
            node.ui_tree_sort_id = sort_id
            node.ui_tree_depth = 0
            node.ui_is_orphan = bool(node.parent.strip())


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
    Scene.sz_gtxds = CollectionProperty(type=Gtxd, name="GTXDs")
    Scene.sz_gtxd_index = IntProperty(name="GTXD")

    Image.sz_is_hd = BoolProperty(
        name="HD",
        description=(
            "Export the full-resolution texture to a separate '+hi' texture dictionary. The base texture "
            "dictionary gets a half-resolution copy with the first mip level dropped"
        ),
        default=False,
    )


def unregister():
    del Scene.sz_txds
    del Scene.sz_gtxds
    del Scene.sz_gtxd_index
    del Image.sz_is_hd
