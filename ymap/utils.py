# Import for type hinting without circular import
from __future__ import annotations
from typing import Union, TYPE_CHECKING
from ..tools.utils import get_list_item

if TYPE_CHECKING:
    from .properties import CMapDataProperties


def get_selected_ymap(context) -> Union[CMapDataProperties, None]:
    scene = context.scene
    return get_list_item(scene.ymaps, scene.ymap_index)


def get_active_element(type, context):
    selected_ymap = get_selected_ymap(context)
    element_mapping = {
        "sollumz_element_entity": ("entities", "entity_index"),
        "sollumz_element_modeloccluder": ("modeloccluders", "modeloccluder_index"),
        "sollumz_element_boxoccluder": ("boxoccluders", "boxoccluder_index"),
        "sollumz_element_cargenerator": ("cargens", "cargen_index")}

    selected = element_mapping.get(context.scene.selected_ymap_element)
    if type == "list":
        return selected
    elif type == "item":
        if selected[0] == "entities":
            return get_list_item(selected_ymap.entities, selected_ymap.entity_index)
        if selected[0] == "modeloccluders":
            return get_list_item(selected_ymap.modeloccluders, selected_ymap.modeloccluder_index)
        if selected[0] == "boxoccluders":
            return get_list_item(selected_ymap.boxoccluders, selected_ymap.boxoccluder_index)
        if selected[0] == "cargens":
            return get_list_item(selected_ymap.cargens, selected_ymap.cargen_index)