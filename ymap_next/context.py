from ..shared.multiselection import MultiSelectCollection
from ..ytyp.properties.extensions import ExtensionProperties
from .properties.map import (
    MapCarGen,
    MapCarGenSelectionAccess,
    MapData,
    MapEntity,
    MapGrassBatch,
    MapGrassTemplate,
    MapGroup,
    MapTimecycleModifier,
    get_maps,
)


def active_group(context) -> MapGroup | None:
    maps = get_maps(context)
    if maps and (g := maps.groups):
        return g.active_item
    return None


def active_map(context) -> MapData | None:
    group = active_group(context)
    if group and (m := group.maps):
        return m.active_item
    return None


def active_entity(context) -> MapEntity | None:
    group = active_group(context)
    if group and (e := group.entities):
        return e.active_item
    return None


def active_entity_extension(context) -> ExtensionProperties | None:
    entity = active_entity(context)
    if entity:
        return entity.selected_extension
    return None


def active_entity_from_active_object(context) -> tuple[MapGroup, MapEntity] | object | None:
    from .map_index import find_entity_by_object

    aobj = context.active_object
    return find_entity_by_object(aobj)


def active_cargens_collection(context) -> MultiSelectCollection[MapCarGen, MapCarGenSelectionAccess] | None:
    group = active_group(context)
    if group and (c := group.cargens):
        return c
    return None


def active_cargen(context) -> MapCarGen | None:
    group = active_group(context)
    if group and (c := group.cargens):
        return c.active_item
    return None


def active_cargen_from_active_object(context) -> tuple[MapGroup, MapCarGen] | object | None:
    from .map_index import find_cargen_by_collection

    aobj = context.active_object

    result = None
    for coll in aobj.users_collection:
        result = find_cargen_by_collection(coll)
        if result is not None:
            break

    return result


def active_grass_batch(context) -> MapGrassBatch | None:
    group = active_group(context)
    if group and (b := group.grass_batches):
        return b.active_item
    return None


def active_grass_template(context) -> MapGrassTemplate | None:
    batch = active_grass_batch(context)
    if batch and (t := batch.templates):
        return t.active_item
    return None


def active_tcm(context) -> MapTimecycleModifier | None:
    group = active_group(context)
    if group and (t := group.timecycle_modifiers):
        return t.active_item
    return None
