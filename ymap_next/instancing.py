from collections import defaultdict
from typing import Callable, TypeAlias

import bpy
from mathutils import Euler, Quaternion, Vector
from szio import jenkhash
from szio.gta5 import (
    Entity,
    EntityMloInstance,
)

from .. import logger
from ..sollumz_helper import duplicate_object_with_children
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import remove_number_suffix
from .properties.map import (
    MapEntity,
    MapGroup,
)


# TODO(ymap/ytyp): re-use InstancingBatch in MLO import code
class InstancingBatch:
    __slots__ = ("instances", "_objects_snapshot", "_objects_snapshot_by_hash", "_objects_in_scene_snapshopt")

    def __init__(self):
        self.instances: dict[str, list[tuple[int, Vector, Euler, Vector]]] = {}

        self._objects_snapshot = {o.name: o for o in bpy.data.objects}  # cache objects to avoid many O(n) lookups
        self._objects_snapshot_by_hash = {jenkhash.name_to_hash(name): o for name, o in self._objects_snapshot.items()}
        self._objects_in_scene_snapshopt = {o.name for o in bpy.context.scene.objects}

    def add_map_entity(self, entity_idx: int, entity: MapEntity | Entity):
        if isinstance(entity, Entity):  # szio Entity
            is_mlo = isinstance(entity, EntityMloInstance)
            self.instances.setdefault(entity.archetype_name, []).append(
                (
                    entity_idx,
                    entity.position,
                    (entity.rotation if is_mlo else entity.rotation.inverted()).to_euler(),
                    Vector((entity.scale_xy, entity.scale_xy, entity.scale_z)),
                )
            )
        else:  # MapEntity property group
            self.instances.setdefault(entity.archetype_name, []).append(
                (
                    entity_idx,
                    entity.position,
                    entity.rotation.to_euler(),
                    Vector((entity.scale_xy, entity.scale_xy, entity.scale_z)),
                )
            )

    def instance_from_library(self, object_instanced_cb, userpref_instance_entities: bool):
        from ..shared.game_assets.library import batch_create_objects_from_library

        if userpref_instance_entities:
            num_instanced, num_missing = batch_create_objects_from_library(self.instances, object_instanced_cb)
        else:
            num_instanced, num_missing = 0, len(self.instances)
        return num_instanced, num_missing

    def instance_from_current_blend(self, object_instanced_cb, userpref_instance_entities: bool):
        origin = Vector((0.0, 0.0, 0.0))
        origin.freeze()

        num_missing = 0
        num_instanced = 0

        remaining_instances = {}
        for archetype_name, per_instance_transforms in self.instances.items():
            obj = self._objects_snapshot.get(archetype_name, None) or self._objects_snapshot_by_hash.get(
                jenkhash.name_to_hash(archetype_name), None
            )

            if obj is None:
                num_missing += 1
                remaining_instances[archetype_name] = per_instance_transforms
                continue

            in_scene = obj.name in self._objects_in_scene_snapshopt

            for obj_id, loc, rot, scl in per_instance_transforms:
                obj_already_used = obj.location != origin
                do_instance = (
                    # Since it isn't in the current scene, we have to duplicate the object always
                    (not in_scene)
                    or
                    # If found in the scene and user wants to instance entities, only instance it if it is no longer at the origin,
                    # meaning it was already placed elsewhere in the MLO/map or the user moved it away.
                    # This is to support the workflow of importing all models and then importing the MLO ytyp/ymap with instancing
                    # enabled, without duplicating every entity.
                    (userpref_instance_entities and obj_already_used)
                )

                if do_instance:
                    obj_inst = duplicate_object_with_children(obj)
                else:
                    if obj_already_used:
                        # Without instancing, this object can only be used once
                        continue

                    obj_inst = obj

                obj_inst.location = loc
                obj_inst.rotation_euler = rot
                obj_inst.scale = scl
                object_instanced_cb(obj_inst, obj_id)
                num_instanced += 1

        self.instances = remaining_instances
        return num_instanced, num_missing


def batch_add_map_entity(entities_to_instance: InstancingBatch, entity_idx: int, entity: MapEntity | Entity):
    entities_to_instance.add_map_entity(entity_idx, entity)


def batch_instance_map_entities(
    map_group: MapGroup,
    entities_to_instance: InstancingBatch,
    userpref_instance_entities: bool = True,
):
    from ..ydr.shader_materials import apply_tint_preview_index

    # Cache entities collection into a list for O(1) lookups. Collection properties are
    # a linked-list internally so each index lookup is O(N).
    entities_list = list(map_group.entities)

    def _link_obj(obj, entity_idx: int):
        e = entities_list[entity_idx]
        e.linked_object = obj

        tint_value = e.tint_value
        if tint_value != 0:
            apply_tint_preview_index(obj, tint_value)

    num_instanced_from_blend, _ = entities_to_instance.instance_from_current_blend(
        _link_obj, userpref_instance_entities
    )
    num_instanced_from_lib, num_missing = entities_to_instance.instance_from_library(
        _link_obj, userpref_instance_entities
    )

    num_instanced = num_instanced_from_blend + num_instanced_from_lib

    if num_missing > 0:
        logger.info(
            f"{num_instanced} entities instanced ({num_instanced_from_blend} from current .blend, {num_instanced_from_lib} from library), {num_missing} assets not found in library or current .blend file"
        )
    elif num_instanced > 0:
        logger.info(
            f"{num_instanced} entities instanced ({num_instanced_from_blend} from current .blend, {num_instanced_from_lib} from library)"
        )

    return num_instanced, num_missing


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
    batch = InstancingBatch()
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

        if obj.sollum_type in {SollumType.DRAWABLE, SollumType.FRAGMENT}:
            # If any of these, it is probably a custom model from the user, don't delete it
            # Objects from asset libraries normally end up with drawable model type
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
