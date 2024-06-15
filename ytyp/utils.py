# Import for type hinting without circular import
from __future__ import annotations
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .properties.ytyp import CMapTypesProperties, ArchetypeProperties
    from .properties.mlo import RoomProperties, PortalProperties, MloEntityProperties, TimecycleModifierProperties, EntitySetProperties
    from .properties.extensions import ExtensionProperties

import bpy
from ..tools.utils import get_list_item


def get_selected_ytyp(context) -> Union[CMapTypesProperties, None]:
    scene = context.scene
    return get_list_item(scene.ytyps, scene.ytyp_index)


def get_selected_archetype(context) -> Union[ArchetypeProperties, None]:
    ytyp = get_selected_ytyp(context)
    if ytyp:
        return ytyp.selected_archetype


def get_selected_room(context) -> Union[RoomProperties, None]:
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_room


def get_selected_portal(context) -> Union[PortalProperties, None]:
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_portal


def get_selected_entity(context) -> Union[MloEntityProperties, None]:
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_entity


def get_selected_tcm(context) -> Union[TimecycleModifierProperties, None]:
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_tcm


def get_selected_extension(context) -> Union[ExtensionProperties, None]:
    archetype = get_selected_archetype(context)
    if archetype:
        return archetype.selected_extension


def get_selected_entity_extension(context) -> Union[ExtensionProperties, None]:
    entity = get_selected_entity(context)
    if entity:
        return entity.selected_extension


def get_selected_entity_set(context) -> Union[EntitySetProperties, None]:
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_entity_set


def get_selected_entity_set_id(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return str(archetype.selected_entity_set_id + 1)


def validate_dynamic_enum(data_block: bpy.types.ID, prop_name: str, enum_collection: bpy.types.bpy_prop_collection):
    """Hack to esnure the EnumProperty ``data_block.prop_name`` has a valid enum value."""
    ids = {str(item.id) for item in enum_collection}
    current_value = getattr(data_block, prop_name)

    if current_value in ids:
        return

    setattr(data_block, prop_name, "-1")


def validate_dynamic_enums(collection: bpy.types.bpy_prop_collection, prop_name: str, enum_collection: bpy.types.bpy_prop_collection):
    """Hack to ensure the EnumProperty ``data_block.prop_name`` for all items in ``collection`` has a valid enum value."""
    for item in collection:
        validate_dynamic_enum(item, prop_name, enum_collection)
