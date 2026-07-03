"""Computation of map data entities/streaming extents from the items assigned to a container.

Used at export for containers without manual extents, and by the "Calculate Extents" operator.
"""

from collections import defaultdict
from collections.abc import Iterable, Sequence

import bpy
import numpy as np
from bpy.types import Depsgraph
from mathutils import Matrix, Quaternion, Vector

from ..shared.game_assets.asset_info import (
    AssetInfoCache,
    try_get_archetype_info_by_name,
    try_get_asset_metadata_archetype_info,
)
from ..tools.meshhelper import get_combined_bound_box
from .grass import evaluated_grass_batch_instances_from_object
from .grass.geonodes import disable_grass_batch_modifier_preview
from .properties.map import (
    MapCarGen,
    MapEntity,
    MapGrassBatch,
    MapGroup,
    MapLodLights,
    MapOccluder,
    MapTimecycleModifier,
)


def resolve_entity_lod_dist(entity: MapEntity, map_group: MapGroup, cache: AssetInfoCache) -> float:
    """Effective LOD distance used by an entity, matching how the game derives it: a LOD parent's
    `child_lod_dist` overrides; otherwise an unset (`<= 0`) `lod_dist` falls back to the archetype's.
    """
    parent = map_group.find_entity(entity.parent_uuid) if entity.parent_uuid else None
    if parent is not None and parent.child_lod_dist != 0:
        return parent.child_lod_dist

    lod_dist = entity.lod_dist
    if lod_dist <= 0.0:
        archetype_info = try_get_archetype_info_by_name(entity.archetype_name, cache=cache)
        if archetype_info is not None:
            lod_dist = archetype_info.lod_dist
    return lod_dist


def _vec_min(a: Vector, b: Vector) -> Vector:
    return Vector((min(a.x, b.x), min(a.y, b.y), min(a.z, b.z)))


def _vec_max(a: Vector, b: Vector) -> Vector:
    return Vector((max(a.x, b.x), max(a.y, b.y), max(a.z, b.z)))


class ExtentsAccumulator:
    """Unions item world AABBs into entities extents and, with each AABB grown by the item's
    streaming distance, into streaming extents."""

    def __init__(self):
        self._entities_min: Vector | None = None
        self._entities_max: Vector | None = None
        self._streaming_min: Vector | None = None
        self._streaming_max: Vector | None = None

    def add(self, bb_min: Vector, bb_max: Vector, streaming_dist: float = 0.0):
        bb_min = Vector(bb_min)
        bb_max = Vector(bb_max)
        grow = Vector((streaming_dist, streaming_dist, streaming_dist))
        if self._entities_min is None:
            self._entities_min = bb_min
            self._entities_max = bb_max
            self._streaming_min = bb_min - grow
            self._streaming_max = bb_max + grow
        else:
            self._entities_min = _vec_min(self._entities_min, bb_min)
            self._entities_max = _vec_max(self._entities_max, bb_max)
            self._streaming_min = _vec_min(self._streaming_min, bb_min - grow)
            self._streaming_max = _vec_max(self._streaming_max, bb_max + grow)

    @property
    def has_items(self) -> bool:
        return self._entities_min is not None

    @property
    def entities_extents(self) -> tuple[Vector, Vector]:
        assert self.has_items
        return self._entities_min, self._entities_max

    @property
    def streaming_extents(self) -> tuple[Vector, Vector]:
        assert self.has_items
        return self._streaming_min, self._streaming_max


def _transform_aabb(matrix: Matrix, bb_min: Vector, bb_max: Vector) -> tuple[Vector, Vector]:
    """Transform a local AABB into world space (single-AABB version of lod_lights.bake._transform_aabbs)."""
    center_local = (Vector(bb_min) + Vector(bb_max)) * 0.5
    extent_local = (Vector(bb_max) - Vector(bb_min)) * 0.5

    center_world = matrix @ center_local
    m = matrix
    extent_world = Vector(
        (
            abs(m[0][0]) * extent_local.x + abs(m[0][1]) * extent_local.y + abs(m[0][2]) * extent_local.z,
            abs(m[1][0]) * extent_local.x + abs(m[1][1]) * extent_local.y + abs(m[1][2]) * extent_local.z,
            abs(m[2][0]) * extent_local.x + abs(m[2][1]) * extent_local.y + abs(m[2][2]) * extent_local.z,
        )
    )
    return center_world - extent_world, center_world + extent_world


def _entity_world_aabb(entity: MapEntity, map_group: MapGroup, cache: AssetInfoCache) -> tuple[Vector, Vector, float]:
    """Return the entity's world AABB and its streaming distance (the AABB grown by it is the entity's
    streaming extents contribution).

    AABB sources, in priority order: archetype bounding box from asset metadata, combined bound box of
    the linked object's meshes, point at the entity position.
    """
    obj = entity.linked_object
    if obj is not None:
        world_matrix = obj.matrix_world
    else:
        # The stored rotation is already in Blender space, no inversion needed
        world_matrix = Matrix.LocRotScale(
            Vector(entity.position),
            Quaternion(entity.rotation),
            Vector((entity.scale_xy, entity.scale_xy, entity.scale_z)),
        )

    archetype_info = (
        try_get_asset_metadata_archetype_info(obj, cache=cache)
        if obj is not None
        else try_get_archetype_info_by_name(entity.archetype_name, cache=cache)
    )
    if archetype_info is not None and archetype_info.bb_min != archetype_info.bb_max:
        bb_min, bb_max = _transform_aabb(world_matrix, archetype_info.bb_min, archetype_info.bb_max)
    elif obj is not None and any(c.type == "MESH" for c in (obj, *obj.children_recursive)):
        bb_min, bb_max = get_combined_bound_box(obj, use_world=True)
    else:
        pos = world_matrix.translation
        bb_min, bb_max = Vector(pos), Vector(pos)

    streaming_dist = resolve_entity_lod_dist(entity, map_group, cache)
    return bb_min, bb_max, max(streaming_dist, 0.0)


def _add_grass_batch(acc: ExtentsAccumulator, batch: MapGrassBatch, depsgraph: Depsgraph):
    obj = batch.linked_object
    if obj is None or obj.data is None:
        return

    positions = evaluated_grass_batch_instances_from_object(obj, depsgraph)[0]
    if len(positions) == 0:
        return

    lod_dist = max((t.lod_dist for t in batch.templates), default=0)
    acc.add(Vector(positions.min(axis=0)), Vector(positions.max(axis=0)), float(lod_dist))


def _add_occluder(acc: ExtentsAccumulator, occl: MapOccluder, depsgraph: Depsgraph):
    obj = occl.linked_object
    if obj is None or obj.data is None:
        return

    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    try:
        num_verts = len(mesh_eval.vertices)
        if num_verts == 0:
            return

        local_co = np.empty((num_verts, 3), dtype=np.float32)
        mesh_eval.vertices.foreach_get("co", local_co.ravel())
        mw = np.array(obj.matrix_world, dtype=np.float32)
        world_co = local_co @ mw[:3, :3].T + mw[:3, 3]
        acc.add(Vector(world_co.min(axis=0)), Vector(world_co.max(axis=0)))
    finally:
        obj_eval.to_mesh_clear()


def _lod_lights_world_positions(ll: MapLodLights) -> np.ndarray | None:
    obj = ll.linked_object
    if obj is None or obj.data is None:
        return None

    mesh = obj.data
    num_verts = len(mesh.vertices)
    if num_verts == 0:
        return None

    local_co = np.empty((num_verts, 3), dtype=np.float32)
    mesh.vertices.foreach_get("co", local_co.ravel())
    mw = np.array(obj.matrix_world, dtype=np.float32)
    return local_co @ mw[:3, :3].T + mw[:3, 3]


def _lod_lights_visibility_range(map_group: MapGroup, ll: MapLodLights, distant: bool) -> float:
    props = map_group.lod_lights_bake_props
    prefix = "distant_visibility_range_" if distant else "visibility_range_"
    return getattr(props, prefix + ll.category.lower())


def calc_map_data_extents(
    map_group: MapGroup,
    depsgraph: Depsgraph,
    *,
    entities: Sequence[MapEntity] = (),
    cargens: Sequence[MapCarGen] = (),
    tcms: Sequence[MapTimecycleModifier] = (),
    grass_batches: Sequence[MapGrassBatch] = (),
    occluders: Sequence[MapOccluder] = (),
    lod_lights: Sequence[MapLodLights] = (),
    distant_lod_lights: Sequence[MapLodLights] = (),
    asset_info_cache: AssetInfoCache | None = None,
) -> tuple[tuple[Vector, Vector], tuple[Vector, Vector]] | None:
    """Compute ``(entities_extents, streaming_extents)`` of a single map data container from the items assigned to it."""
    cache = asset_info_cache if asset_info_cache is not None else AssetInfoCache()
    acc = ExtentsAccumulator()

    for entity in entities:
        bb_min, bb_max, streaming_dist = _entity_world_aabb(entity, map_group, cache)
        acc.add(bb_min, bb_max, streaming_dist)

    for cargen in cargens:
        coll = cargen.linked_collection
        if coll is None:
            continue
        for obj in coll.objects:
            pos = obj.matrix_world.translation
            half = Vector(obj.dimensions) / 2
            acc.add(pos - half, pos + half)

    for tcm in tcms:
        tcm_min, tcm_max = tcm.extents
        acc.add(tcm_min, tcm_max)

    for batch in grass_batches:
        _add_grass_batch(acc, batch, depsgraph)

    for occl in occluders:
        _add_occluder(acc, occl, depsgraph)

    for ll in lod_lights:
        positions = _lod_lights_world_positions(ll)
        if positions is not None:
            vis_range = _lod_lights_visibility_range(map_group, ll, distant=False)
            acc.add(Vector(positions.min(axis=0)), Vector(positions.max(axis=0)), vis_range)

    for ll in distant_lod_lights:
        positions = _lod_lights_world_positions(ll)
        if positions is not None:
            vis_range = _lod_lights_visibility_range(map_group, ll, distant=True)
            acc.add(Vector(positions.min(axis=0)), Vector(positions.max(axis=0)), vis_range)

    if not acc.has_items:
        return None

    return acc.entities_extents, acc.streaming_extents


def update_maps_extents(map_group: MapGroup, map_uuids: Iterable[bytes]) -> int:
    """Recalculate and store extents of the given containers, regardless of their manual-extents flag.

    Returns the number of containers whose extents were updated (containers without items are skipped).
    """
    uuids = set(map_uuids)

    entities_by_map: dict[bytes, list[MapEntity]] = defaultdict(list)
    for entity in map_group.entities:
        if entity.map_data_uuid in uuids:
            entities_by_map[entity.map_data_uuid].append(entity)

    cargens_by_map: dict[bytes, list[MapCarGen]] = defaultdict(list)
    for cargen in map_group.cargens:
        if cargen.map_data_uuid in uuids:
            cargens_by_map[cargen.map_data_uuid].append(cargen)

    tcms_by_map: dict[bytes, list[MapTimecycleModifier]] = defaultdict(list)
    for tcm in map_group.timecycle_modifiers:
        if tcm.map_data_uuid in uuids:
            tcms_by_map[tcm.map_data_uuid].append(tcm)

    grass_by_map: dict[bytes, list[MapGrassBatch]] = defaultdict(list)
    for batch in map_group.grass_batches:
        if batch.map_data_uuid in uuids:
            grass_by_map[batch.map_data_uuid].append(batch)

            if obj := batch.linked_object:
                disable_grass_batch_modifier_preview(obj, batch)

    occl_by_map: dict[bytes, list[MapOccluder]] = defaultdict(list)
    for occl in map_group.occluders:
        if occl.map_data_uuid in uuids:
            occl_by_map[occl.map_data_uuid].append(occl)

    lls_by_map: dict[bytes, list[MapLodLights]] = defaultdict(list)
    distant_lls_by_parent: dict[bytes, list[MapLodLights]] = defaultdict(list)
    for ll in map_group.lod_lights:
        if not ll.map_data_uuid:
            continue
        if ll.map_data_uuid in uuids:
            lls_by_map[ll.map_data_uuid].append(ll)
        child_map = map_group.find_map(ll.map_data_uuid)
        if child_map is not None and child_map.parent_uuid in uuids:
            distant_lls_by_parent[child_map.parent_uuid].append(ll)

    # Fetch the depsgraph after disabling grass previews so the evaluated meshes are up to date
    depsgraph = bpy.context.evaluated_depsgraph_get()
    asset_info_cache = AssetInfoCache()

    num_updated = 0
    for map_uuid in uuids:
        map_data = map_group.find_map(map_uuid)
        if map_data is None:
            continue

        extents = calc_map_data_extents(
            map_group,
            depsgraph,
            entities=entities_by_map[map_uuid],
            cargens=cargens_by_map[map_uuid],
            tcms=tcms_by_map[map_uuid],
            grass_batches=grass_by_map[map_uuid],
            occluders=occl_by_map[map_uuid],
            lod_lights=lls_by_map[map_uuid],
            distant_lod_lights=distant_lls_by_parent[map_uuid],
            asset_info_cache=asset_info_cache,
        )
        if extents is None:
            continue

        map_data.entities_extents, map_data.streaming_extents = extents
        num_updated += 1

    return num_updated
