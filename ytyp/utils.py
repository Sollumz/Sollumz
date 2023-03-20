# Import for type hinting without circular import
from __future__ import annotations
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .properties.ytyp import CMapTypesProperties, ArchetypeProperties
    from .properties.mlo import RoomProperties, PortalProperties, MloEntityProperties, TimecycleModifierProperties, EntitySetProperties
    from .properties.extensions import ExtensionProperties

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


def get_selected_entity_set(context) -> Union[EntitySetProperties, None]:
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_entity_set
        
def get_selected_entity_set_entity(context) -> Union[MloEntityProperties, None]:
    entity_set = get_selected_entity_set(context)
    if entity_set:
        entity = entity_set.selected_entity
        if entity:
            return entity
        
def get_selected_entity_set_id(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return str(archetype.selected_entity_set_id + 1)