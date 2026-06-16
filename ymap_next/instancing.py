from collections import defaultdict

import bpy
from mathutils import Euler, Quaternion, Vector
from szio.gta5 import (
    Entity,
    EntityMloInstance,
)
from .properties.map import (
    MapEntity,
    MapGroup,
)
from ..tools.blenderhelper import remove_number_suffix
from .. import logger
from typing import Callable, TypeAlias

InstancingBatch: TypeAlias = dict[str, list[tuple[int, Vector, Euler, Vector]]]


def batch_add_map_entity(entities_to_instance: InstancingBatch, entity_idx: int, entity: MapEntity | Entity):
    if isinstance(entity, Entity):  # szio Entity
        is_mlo = isinstance(entity, EntityMloInstance)
        entities_to_instance[entity.archetype_name].append(
            (
                entity_idx,
                entity.position,
                (entity.rotation if is_mlo else entity.rotation.inverted()).to_euler(),
                Vector((entity.scale_xy, entity.scale_xy, entity.scale_z)),
            )
        )
    else:  # MapEntity property group
        entities_to_instance[entity.archetype_name].append(
            (
                entity_idx,
                entity.position,
                entity.rotation.to_euler(),
                Vector((entity.scale_xy, entity.scale_xy, entity.scale_z)),
            )
        )


def batch_instance_map_entities(
    map_group: MapGroup,
    entities_to_instance: InstancingBatch,
):
    from ..shared.game_assets.library import batch_create_objects_from_library

    # Cache entities collection into a list for O(1) lookups. Collection properties are
    # a linked-list internally so each index lookup is O(N).
    entities_list = list(map_group.entities)

    def _link_obj(obj, entity_idx: int):
        entities_list[entity_idx].linked_object = obj

    num_linked, num_missing = batch_create_objects_from_library(entities_to_instance, _link_obj)

    if num_missing > 0:
        logger.info(f"Game asset linking: {num_linked} entities linked, {num_missing} assets not found in library")
    elif num_linked > 0:
        logger.info(f"Game asset linking: {num_linked} entities linked")

    return num_linked, num_missing


def instance_map_entities(
    map_group: MapGroup,
    entity_filter: Callable[[MapEntity], bool] | None = None,
) -> tuple[int, int, int]:
    """Instance all entities of `map_group` that are not already linked to an object.

    If `entity_filter` is given, only entities for which it returns `True` are considered; excluded
    entities are ignored entirely (not counted as skipped).

    Returns `(num_linked, num_missing, num_skipped)`: instances created, archetypes not found in the asset
    library, and entities skipped because they already had a linked object.
    """
    batch = defaultdict(list)
    num_skipped = 0
    for entity_idx, entity in enumerate(map_group.entities):
        if entity_filter is not None and not entity_filter(entity):
            continue

        if entity.linked_object is not None:
            num_skipped += 1
            continue

        batch_add_map_entity(batch, entity_idx, entity)

    num_linked, num_missing = batch_instance_map_entities(map_group, batch)
    # TODO(ymap_next): organize instanced objects in collections?
    return num_linked, num_missing, num_skipped


def uninstance_map_entities(
    map_group: MapGroup,
    entity_filter: Callable[[MapEntity], bool] | None = None,
) -> int:
    """Remove the linked object of every instanced entity in `map_group`, saving each object's transform
    back into the entity data first. If `entity_filter` is given, only entities for which it returns `True`
    are considered. Returns the number of objects removed.
    """
    objs_to_remove = []
    for entity in map_group.entities:
        if entity_filter is not None and not entity_filter(entity):
            continue

        obj = entity.linked_object
        if obj is None:
            continue

        # Save archetype and transforms from linked object
        entity.archetype_name = remove_number_suffix(obj.name).lower()

        transform = obj.matrix_world
        location, rotation, scale = transform.decompose()
        entity.position = location
        entity.rotation = rotation
        entity.scale_xy = scale.x
        entity.scale_z = scale.z

        entity.linked_object = None
        objs_to_remove.append(obj)

    bpy.data.batch_remove(objs_to_remove)
    return len(objs_to_remove)
