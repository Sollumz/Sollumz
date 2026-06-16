import bpy
from bpy.types import PropertyGroup, Scene
from bpy.props import EnumProperty, PointerProperty

from .map import MapLodLevelEnumItems


class MapEntityFilterProperties(PropertyGroup):
    """Filter state for the map entities UI list. Read by ``MapEntity.is_filtered``."""

    filter_type: EnumProperty(name="Filter By", items=(
        ("all", "All", "Show all entities"),
        ("lod_level", "LOD Level", "Show only entities with the selected LOD level"),
        ("kind", "Kind", "Show only entities of the selected kind"),
    ))
    lod_level: EnumProperty(items=MapLodLevelEnumItems, name="LOD Level")
    kind: EnumProperty(name="Kind", items=(
        ("regular", "Regular", "Regular (non-MLO) entities"),
        ("mlo", "MLO", "MLO instance entities"),
        ("orphan_hd", "Orphan HD", "Orphan HD entities (HD with no LOD parent)"),
    ))


def get_map_entity_filter(context) -> MapEntityFilterProperties:
    return context.scene.sz_map_entity_filter


def register():
    Scene.sz_map_entity_filter = PointerProperty(type=MapEntityFilterProperties)


def unregister():
    del Scene.sz_map_entity_filter
