from ..tools.utils import get_list_item


def get_selected_ytyp(context):
    scene = context.scene
    return get_list_item(scene.ytyps, scene.ytyp_index)


def get_selected_archetype(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        return ytyp.selected_archetype


def get_selected_room(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_room


def get_selected_portal(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_portal


def get_selected_entity(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_entity


def get_selected_tcm(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_tcm
