# Import for type hinting without circular import
from __future__ import annotations
from typing import Union, TYPE_CHECKING

if TYPE_CHECKING:
    from .properties import CMapDataProperties

import bpy
from ..tools.utils import get_list_item


def get_selected_ymap(context) -> Union[CMapDataProperties, None]:
    scene = context.scene
    return get_list_item(scene.ymaps, scene.ymap_index)

def get_active_element_list(context):
    if context.scene.selected_ymap_element == "sollumz_ymapelement_entity":
        return "entities", "entity_index"
    elif context.scene.selected_ymap_element == "sollumz_ymapelement_modeloccluder":
        return "modeloccluders", "modeloccluder_index"
    elif context.scene.selected_ymap_element == "sollumz_ymapelement_boxoccluder":
        return "boxoccluders", "boxoccluder_index"
    elif context.scene.selected_ymap_element == "sollumz_ymapelement_cargenerator":
        return "cargens", "cargen_index"