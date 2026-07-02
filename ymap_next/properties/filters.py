from collections.abc import Iterator
import bpy
from bpy.types import (
    PropertyGroup,
    Scene,
    Context,
)
from bpy.props import (
    EnumProperty,
    PointerProperty,
    StringProperty,
)

from .map import MapLodLevelEnumItems
from ..context import active_group


class MapEntityFilterProperties(PropertyGroup):
    """Filter state for the map entities UI list. Read by ``MapEntity.is_filtered``."""

    filter_type: EnumProperty(
        name="Filter By",
        items=(
            ("all", "All", "Show all entities"),
            ("lod_level", "LOD Level", "Show only entities with the selected LOD level"),
            ("kind", "Kind", "Show only entities of the selected kind"),
            ("container", "Container", "Show only entities assigned to the selected container"),
        ),
    )
    lod_level: EnumProperty(items=MapLodLevelEnumItems, name="LOD Level")
    kind: EnumProperty(
        name="Kind",
        items=(
            ("regular", "Regular", "Regular (non-MLO) entities"),
            ("mlo", "MLO", "MLO instance entities"),
            ("orphan_hd", "Orphan HD", "Orphan HD entities (HD with no LOD parent)"),
        ),
    )

    def _search_containers(self, context: Context, _edit_text: str) -> Iterator[str]:
        group = active_group(context)
        if group:
            for m in sorted(group.maps, key=lambda m: m.ui_tree_sort_id):
                yield m.ui_label

    def _on_container_update(self, context: Context):
        name = self.container_name
        name_stripped = self.container_name.strip()
        if name != name_stripped:
            self.container_name = name_stripped

    container_name: StringProperty(
        name="Container",
        search=_search_containers,
        update=_on_container_update,
    )


def get_map_entity_filter(context) -> MapEntityFilterProperties:
    return context.scene.sz_map_entity_filter


def register():
    Scene.sz_map_entity_filter = PointerProperty(type=MapEntityFilterProperties)


def unregister():
    del Scene.sz_map_entity_filter
