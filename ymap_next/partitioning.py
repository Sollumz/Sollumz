"""Classification and spatial partitioning of map items for auto-generated leaf map datas."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from uuid import uuid4

import numpy as np
from bpy.types import Object
from mathutils import Vector

from ..shared.game_assets.asset_info import AssetInfoCache
from ..shared.geometry import KDTreeSplitStrategy, kdtree_build, kdtree_merge_leaves
from .extents import ExtentsAccumulator, entity_world_aabb, resolve_entity_lod_dist
from .properties.map import (
    MapCarGen,
    MapData,
    MapEntity,
    MapGrassBatch,
    MapGroup,
    MapPartitionMode,
    MapTimecycleModifier,
)

# Bucket key for items that stay in the logical (AUTO) map data itself
SELF = "SELF"


@dataclass(slots=True)
class PartitioningSettings:
    long_lod_dist_threshold: float = 150.0
    max_per_chunk: int = 512


def classify_entity(
    entity: MapEntity, settings: PartitioningSettings, map_group: MapGroup, cache: AssetInfoCache
) -> str:
    """Returns the bucket key for where this entity should go during auto-partitioning."""
    if entity.lod_level in ("LOD", "SLOD1", "SLOD2", "SLOD3", "SLOD4"):
        return SELF
    if entity.is_mlo:
        return f"interior_{entity.archetype_name.lower()}"
    if entity.is_critical:
        return "critical"

    entity_lod_dist = resolve_entity_lod_dist(entity, map_group, cache)
    if entity_lod_dist >= settings.long_lod_dist_threshold:
        return "long"

    return "strm"


def classify_cargen(cargen: MapCarGen) -> str:
    return "strm"


def classify_tcm(tcm: MapTimecycleModifier) -> str:
    return SELF


def classify_grass(batch: MapGrassBatch) -> str:
    return "grass"


def generate_leaf_name(parent_name: str, bucket_key: str) -> str:
    """Generate the name for an auto-generated leaf map data."""
    if bucket_key.startswith("interior_"):
        return f"{parent_name}_{bucket_key}_milo_"
    return f"{parent_name}_{bucket_key}"


def spatial_partition_by_position(
    items: list,
    get_position,
    max_per_chunk: int,
) -> list[list]:
    """Split items into spatial groups based on 2D position."""
    if len(items) <= max_per_chunk:
        return [items]

    positions = np.array([get_position(item).xy for item in items], dtype=np.float64)
    tree = kdtree_build(positions, KDTreeSplitStrategy.LONGEST_AXIS, max_per_chunk)
    tree = kdtree_merge_leaves(tree, positions, max_per_chunk)
    return [[items[i] for i in leaf.indices] for leaf in tree.iter_leaves()]


def _get_entity_position(entity: MapEntity) -> Vector:
    obj = entity.linked_object
    if obj is not None:
        return Vector(obj.matrix_world.translation)
    return Vector(entity.position)


def _get_cargen_position(cargen: MapCarGen) -> Vector:
    """Average position of all objects in the cargen's linked collection."""
    coll = cargen.linked_collection
    if coll is not None and coll.objects:
        total = Vector((0, 0, 0))
        for obj in coll.objects:
            total += Vector(obj.location)
        return total / len(coll.objects)
    return Vector((0, 0, 0))


def _collect_items_in_auto_scope(map_group: MapGroup, auto_map_data: MapData):
    """Collect all items assigned to the AUTO map data or its auto-generated children."""
    scope_uuids = {auto_map_data.uuid}
    for m in map_group.maps:
        if m.is_auto_generated and m.parent_uuid == auto_map_data.uuid:
            scope_uuids.add(m.uuid)

    entities = [e for e in map_group.entities if e.map_data_uuid in scope_uuids]
    cargens = [c for c in map_group.cargens if c.map_data_uuid in scope_uuids]
    tcms = [t for t in map_group.timecycle_modifiers if t.map_data_uuid in scope_uuids]
    grass = [g for g in map_group.grass_batches if g.map_data_uuid in scope_uuids]

    return entities, cargens, tcms, grass


def _remove_auto_generated_children(map_group: MapGroup, auto_map_data: MapData):
    """Remove all auto-generated child map datas of the given AUTO map data."""
    indices_to_remove = []
    for i, m in enumerate(map_group.maps):
        if m.is_auto_generated and m.parent_uuid == auto_map_data.uuid:
            indices_to_remove.append(i)

    # Remove in reverse order to preserve indices
    for i in reversed(indices_to_remove):
        map_group.maps.remove(i)


def generate_partitions(map_group: MapGroup, map_data: MapData, settings: PartitioningSettings):
    """Generate or regenerate auto-partitioned leaf map datas for an AUTO map data.

    Collects all items in scope (AUTO parent + existing auto-generated children),
    classifies them into buckets, applies spatial partitioning, then creates new
    auto-generated leaf MapDatas and reassigns items.
    """
    assert map_data.partition_mode == MapPartitionMode.AUTO.name

    # Snapshot before mutating map_group.maps; add()/remove() invalidate existing
    # references into the collection, including map_data itself
    map_data_uuid = map_data.uuid
    map_data_name = map_data.name

    # 1. Collect all items in scope
    entities, cargens, tcms, grass_batches = _collect_items_in_auto_scope(map_group, map_data)

    # 2. Classify items into buckets
    cache = AssetInfoCache()
    buckets: dict[str, list] = defaultdict(list)
    for entity in entities:
        buckets[classify_entity(entity, settings, map_group, cache)].append(entity)
    for cargen in cargens:
        buckets[classify_cargen(cargen)].append(cargen)
    for tcm in tcms:
        buckets[classify_tcm(tcm)].append(tcm)
    for batch in grass_batches:
        buckets[classify_grass(batch)].append(batch)

    # 3. Spatial-partition large buckets into numbered chunks
    numbered_buckets: dict[str, list] = {}
    cargen_assignments: list[tuple[MapCarGen, list[Object], list[str]]] = []
    for key, bucket_items in buckets.items():
        if key == SELF:
            numbered_buckets[SELF] = bucket_items
        elif key == "strm":
            # Entities take priority: they are partitioned into chunks first, then each cargen object is
            # placed into the chunk whose entities extents contain it; leftover objects get their own chunks
            strm_entities = [item for item in bucket_items if isinstance(item, MapEntity)]
            strm_cargens = [item for item in bucket_items if isinstance(item, MapCarGen)]
            entity_chunks = []
            if strm_entities:
                entity_chunks = spatial_partition_by_position(
                    strm_entities, _get_entity_position, settings.max_per_chunk
                )
                for i, chunk in enumerate(entity_chunks):
                    numbered_buckets[f"strm_{i}"] = chunk
            if strm_cargens:
                cargen_assignments = _partition_strm_cargen_objects(
                    strm_cargens, entity_chunks, numbered_buckets, settings, map_group, cache
                )
        elif key == "long":
            chunks = spatial_partition_by_position(bucket_items, _get_entity_position, settings.max_per_chunk)
            for i, chunk in enumerate(chunks):
                numbered_buckets[f"long_{i}"] = chunk
        elif key == "critical":
            chunks = spatial_partition_by_position(bucket_items, _get_entity_position, settings.max_per_chunk)
            for i, chunk in enumerate(chunks):
                numbered_buckets[f"critical_{i}"] = chunk
        elif key == "grass":
            # TODO(ymap): would be useful to split the same grass batch mesh into multiple partitions
            numbered_buckets["grass_0"] = bucket_items
            # chunks = spatial_partition_by_position(bucket_items, _get_grass_position, settings.max_per_chunk)
            # for i, chunk in enumerate(chunks):
            #     numbered_buckets[f"grass_{i}"] = chunk
        elif key.startswith("interior_"):
            numbered_buckets[key] = bucket_items
        else:
            numbered_buckets[f"{key}_0"] = bucket_items

    # 4. Remove stale auto-generated children
    _remove_auto_generated_children(map_group, map_data)

    # 5. Reassign SELF items back to the AUTO parent
    for item in numbered_buckets.pop(SELF, []):
        item.map_data_uuid = map_data_uuid

    # 6. Create new leaf MapDatas and reassign items
    leaf_uuid_by_key: dict[str, bytes] = {}
    for bucket_key, bucket_items in numbered_buckets.items():
        leaf_uuid = uuid4().bytes
        leaf_uuid_by_key[bucket_key] = leaf_uuid
        leaf = map_group.maps.add()
        leaf.uuid = leaf_uuid
        leaf.name = generate_leaf_name(map_data_name, bucket_key)
        leaf.parent_uuid = map_data_uuid
        leaf.is_auto_generated = True
        for item in bucket_items:
            item.map_data_uuid = leaf_uuid

    # 7. Rebuild the partitioned cargens' container slots from their objects' buckets
    for cargen, objs, keys in cargen_assignments:
        cargen.extra_map_datas.clear()
        slot_by_key: dict[str, int] = {}
        for obj, bucket_key in zip(objs, keys):
            obj.sz_cargen_map_data_index = slot_by_key.setdefault(bucket_key, len(slot_by_key))
        slot_keys = list(slot_by_key) or ["strm_0"]  # cargens with no objects stay in the first strm bucket
        cargen.map_data_uuid = leaf_uuid_by_key[slot_keys[0]]
        for bucket_key in slot_keys[1:]:
            cargen.add_extra_map_data(leaf_uuid_by_key[bucket_key])

    map_group.refresh_ui()


def _partition_strm_cargen_objects(
    cargens: list[MapCarGen],
    entity_chunks: list[list[MapEntity]],
    numbered_buckets: dict[str, list],
    settings: PartitioningSettings,
    map_group: MapGroup,
    cache: AssetInfoCache,
) -> list[tuple[MapCarGen, list[Object], list[str]]]:
    """Assign each cargen object to a strm bucket.

    Objects within an entity chunk's entities extents (XY) go to that chunk, the one with the nearest
    extents center when several overlap. Objects outside every chunk are spatially partitioned into
    additional strm buckets, registered in `numbered_buckets` without items so their leaf map datas
    still get created.

    Returns `(cargen, objects, bucket key per object)` tuples.
    """
    # XY entities extents per chunk, from the same per-entity AABBs as container extents
    chunk_extents = []
    for chunk in entity_chunks:
        acc = ExtentsAccumulator()
        for entity in chunk:
            bb_min, bb_max, _ = entity_world_aabb(entity, map_group, cache)
            acc.add(bb_min, bb_max)
        chunk_extents.append(acc.entities_extents)

    assignments = []
    leftovers = []  # (object, keys list, index) to patch once the leftover buckets exist
    for cargen in cargens:
        coll = cargen.linked_collection
        objs = list(coll.objects) if coll is not None else []
        keys = []
        for obj in objs:
            pos = obj.matrix_world.translation
            best_i = None
            best_dist = float("inf")
            for i, (bb_min, bb_max) in enumerate(chunk_extents):
                if bb_min.x <= pos.x <= bb_max.x and bb_min.y <= pos.y <= bb_max.y:
                    dist = (pos.xy - ((bb_min + bb_max) * 0.5).xy).length_squared
                    if dist < best_dist:
                        best_dist = dist
                        best_i = i
            keys.append(None if best_i is None else f"strm_{best_i}")
            if best_i is None:
                leftovers.append((obj, keys, len(keys) - 1))
        assignments.append((cargen, objs, keys))

    if leftovers:
        for n, chunk in enumerate(
            spatial_partition_by_position(leftovers, lambda lo: lo[0].matrix_world.translation, settings.max_per_chunk)
        ):
            bucket_key = f"strm_{len(entity_chunks) + n}"
            numbered_buckets[bucket_key] = []
            for _obj, keys, i in chunk:
                keys[i] = bucket_key

    if "strm_0" not in numbered_buckets:
        # No entities and no positioned objects, only empty cargens: keep a single strm bucket for them
        numbered_buckets["strm_0"] = []

    return assignments


def collapse_to_auto(map_group: MapGroup, map_data: MapData):
    """Merge items from manual leaf children back into the parent, switch to AUTO mode.

    Only collapses leaf map datas (those with no children of their own).
    """
    map_data_uuid = map_data.uuid

    leaf_uuids = set()
    parent_uuids = {m.parent_uuid for m in map_group.maps if m.parent_uuid}

    for m in map_group.maps:
        if m.parent_uuid == map_data_uuid and m.uuid not in parent_uuids:
            leaf_uuids.add(m.uuid)

    # Move items from leaf children to parent
    for entity in map_group.entities:
        if entity.map_data_uuid in leaf_uuids:
            entity.map_data_uuid = map_data_uuid
    for cargen in map_group.cargens:
        if cargen.map_data_uuid in leaf_uuids:
            cargen.map_data_uuid = map_data_uuid
        # Extra slots collapse to the parent too; objects keep their slot indices (duplicate slots
        # referencing the same container are fine, export merges them)
        for ref in cargen.extra_map_datas:
            if ref.map_data_uuid in leaf_uuids:
                ref.map_data_uuid = map_data_uuid
    for tcm in map_group.timecycle_modifiers:
        if tcm.map_data_uuid in leaf_uuids:
            tcm.map_data_uuid = map_data_uuid
    for batch in map_group.grass_batches:
        if batch.map_data_uuid in leaf_uuids:
            batch.map_data_uuid = map_data_uuid

    # Set mode before removing leaves; maps.remove() invalidates the map_data reference
    map_data.partition_mode = MapPartitionMode.AUTO.name

    # Remove the leaf map datas
    indices_to_remove = [i for i, m in enumerate(map_group.maps) if m.uuid in leaf_uuids]
    for i in reversed(indices_to_remove):
        map_group.maps.remove(i)

    map_group.refresh_ui()


def convert_to_manual(map_group: MapGroup, map_data: MapData):
    """Convert an AUTO map data to manual mode.

    The auto-generated leaves remain in the tree with their items. Clears
    is_auto_generated on the leaves so they become regular manual map datas.
    """
    map_data.partition_mode = MapPartitionMode.NONE.name
    for m in map_group.maps:
        if m.is_auto_generated and m.parent_uuid == map_data.uuid:
            m.is_auto_generated = False


def auto_assign_unassigned(map_group: MapGroup):
    """Assign items without a map_data_uuid to the nearest existing leaf map data by extents."""
    # Find leaf map datas (those that are not parents of any other map data). Locked containers
    # are excluded: their entity list is frozen because non-imported .ymap files reference their
    # exported indices, and an unassigned entity earlier in the entities collection order would
    # land mid-list and shift them.
    parent_uuids = {m.parent_uuid for m in map_group.maps if m.parent_uuid}
    leaf_maps = [m for m in map_group.maps if m.uuid not in parent_uuids and not m.incomplete_lod_hierarchy_lock]

    if not leaf_maps:
        return

    def _find_nearest(pos: Vector) -> MapData:
        best = leaf_maps[0]
        best_dist = float("inf")
        for m in leaf_maps:
            center = (m.entities_extents_min + m.entities_extents_max) * 0.5
            dist = (pos - center).length_squared
            if dist < best_dist:
                best_dist = dist
                best = m
        return best

    for entity in map_group.entities:
        if not entity.map_data_uuid:
            pos = _get_entity_position(entity)
            entity.map_data_uuid = _find_nearest(pos).uuid

    for cargen in map_group.cargens:
        if not cargen.map_data_uuid:
            pos = _get_cargen_position(cargen)
            cargen.map_data_uuid = _find_nearest(pos).uuid

    for tcm in map_group.timecycle_modifiers:
        if not tcm.map_data_uuid:
            tcm.map_data_uuid = _find_nearest(tcm.location).uuid

    # for batch in map_group.grass_batches:
    #     if not batch.map_data_uuid:
    #         pos = _get_grass_position(batch)
    #         batch.map_data_uuid = _find_nearest(pos).uuid
