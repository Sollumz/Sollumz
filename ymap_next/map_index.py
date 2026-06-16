import functools
import time
from collections.abc import Iterator
from typing import TYPE_CHECKING

import bpy
from bpy.types import (
    ID,
    Collection,
    Object,
)

from ..tools.blenderhelper import tag_redraw

if TYPE_CHECKING:
    from .properties.map import (
        MapCarGen,
        MapEntity,
        MapGrassBatch,
        MapGroup,
    )


class CacheObjectData:
    __slots__ = ("map_group_uuid", "data_type", "data_uuid")

    ENTITY = 1
    CARGEN = 2
    GRASS_BATCH = 3
    OCCLUDER = 4
    LOD_LIGHTS = 5

    def __init__(self, map_group_uuid: bytes, data_type: int, data_uuid: bytes):
        self.map_group_uuid = map_group_uuid
        self.data_type = data_type
        self.data_uuid = data_uuid


class CacheEntityData:
    __slots__ = ("map_group_uuid", "index")

    def __init__(self, map_group_uuid: bytes, index: int):
        self.map_group_uuid = map_group_uuid
        self.index = index


_BUILD_TICK_TIME_BUDGET = 0.020  # 20ms per tick
_BUILD_TICK_TIME_CHECK_INTERVAL = 500  # check deadline every N entries

if bpy.app.version >= (4, 1, 0):

    def _session_uid(id: ID) -> int:
        return id.session_uid

else:  # 4.0

    def _session_uid(id: ID) -> int:
        # Not really the same semantics but should be close enough for our use-case. Hopefully we will drop 4.0 support soon
        return id.as_pointer()


class MapSessionIndex:
    """Session-scoped identity map over the YMAP data model.

    Two kinds of keys are tracked:

    * UUID -> `(group_uuid, index)` for entities and map datas.
    * `ID.session_uid` -> `CacheObjectData` for reverse lookups from a selected Blender `Object` / `Collection` back to
      the owning `MapEntity` / `MapCarGen` / `MapGrassBatch` / `MapOccluder` / `MapLodLights`.

    All caches are built incrementally in the background via `bpy.app.timers`.  Lookups never block, they return `None`
    when the cache hasn't indexed the requested item yet.  Callers can check `is_ready` to distinguish "not found" from
    "not yet indexed".

    The UUID->index cache self-corrects on stale hits (see `MapGroup.find_entity`).

    The entire cache is wiped on `load_post` (new session) and the session_uid keys are only meaningful within a single
    Blender session.
    """

    def __init__(self):
        # UUID → (group_uuid, index). Populated by background build + lazily by find_entity/find_map fallback scans
        self._entity_cache: dict[bytes, CacheEntityData] = {}
        self._map_data_cache: dict[bytes, CacheEntityData] = {}

        # session_uid → CacheObjectData. Populated by background build only.
        self._id_cache: dict[int, CacheObjectData] = {}

        # Background build state
        self._build_iter: Iterator | None = None
        self._ready: bool = False
        self._build_progress: int = 0
        self._build_total: int = 0
        self._fingerprint: int = 0

    @property
    def is_ready(self) -> bool:
        """``True`` after the background build has completed at least once since the last invalidation."""
        return self._ready

    @property
    def build_progress(self) -> tuple[int, int] | None:
        """Returns ``(processed, total)`` during a build, or ``None`` if not building."""
        if self._build_iter is None:
            return None
        return (self._build_progress, self._build_total)

    def invalidate(self):
        """Clear all caches and cancel any in-progress build."""
        self._entity_cache.clear()
        self._map_data_cache.clear()
        self._id_cache.clear()
        self._build_iter = None
        self._ready = False

    def invalidate_and_rebuild(self):
        self.invalidate()
        self.start_build()

    def start_build(self):
        """Begin building all caches in the background via timer."""
        if self._build_iter is not None:
            return
        self._build_total = self._count_build_items()
        self._build_progress = 0
        self._build_iter = self._iter_build()
        bpy.app.timers.register(self._build_tick, first_interval=0.0, persistent=True)

    def _count_build_items(self) -> int:
        from .properties.map import get_maps

        maps = get_maps()
        if maps is None:
            return 0
        total = 0
        for group in maps.groups:
            total += len(group.maps) + len(group.entities) + len(group.grass_batches)
            total += len(group.cargens) + len(group.occluders) + len(group.lod_lights)
        return total

    def _structural_fingerprint(self) -> int:
        """O(groups) hash of collection sizes. Changes only when items are added/removed."""
        from .properties.map import get_maps

        maps = get_maps()
        if maps is None:
            return 0
        parts = []
        for group in maps.groups:
            parts.append(
                (
                    group.uuid,
                    len(group.maps),
                    len(group.entities),
                    len(group.cargens),
                    len(group.grass_batches),
                    len(group.occluders),
                    len(group.lod_lights),
                )
            )
        return hash((len(parts), *parts))

    def ensure_ready(self):
        """Finish the build synchronously.  Use only for operations that need definitive answers (export)."""
        if self._build_iter is None and not self._ready:
            self._build_iter = self._iter_build()
        if self._build_iter is not None:
            self._drain_build()

    # Background build internals

    def _drain_build(self):
        for entry in self._build_iter:
            self._apply_build_entry(entry)
        self._build_iter = None
        self._ready = True
        self._fingerprint = self._structural_fingerprint()

    def _iter_build(self):
        """Yield ``(group_uuid, index, item_uuid, session_uid, data_type)`` for every indexed item."""
        from .properties.map import get_maps

        maps = get_maps()
        if maps is None:
            return
        for group in maps.groups:
            guuid = group.uuid
            for i, m in enumerate(group.maps):
                yield guuid, i, m.uuid, None, None
            for i, entity in enumerate(group.entities):
                linked = entity.linked_object
                uid = _session_uid(linked) if linked is not None else None
                yield guuid, i, entity.uuid, uid, CacheObjectData.ENTITY
            for i, gb in enumerate(group.grass_batches):
                linked = gb.linked_object
                uid = _session_uid(linked) if linked is not None else None
                yield guuid, i, gb.uuid, uid, CacheObjectData.GRASS_BATCH
            for i, cg in enumerate(group.cargens):
                linked = cg.linked_collection
                uid = _session_uid(linked) if linked is not None else None
                yield guuid, i, cg.uuid, uid, CacheObjectData.CARGEN
            for i, occ in enumerate(group.occluders):
                linked = occ.linked_object
                uid = _session_uid(linked) if linked is not None else None
                yield guuid, i, occ.uuid, uid, CacheObjectData.OCCLUDER
            for i, ll in enumerate(group.lod_lights):
                linked = ll.linked_object
                uid = _session_uid(linked) if linked is not None else None
                yield guuid, i, ll.uuid, uid, CacheObjectData.LOD_LIGHTS

    def _build_tick(self) -> float | None:
        build_iter = self._build_iter
        if build_iter is None:
            return None

        deadline = time.monotonic() + _BUILD_TICK_TIME_BUDGET
        count = 0
        while True:
            entry = next(build_iter, None)
            if entry is None:
                self._build_progress += count
                self._build_iter = None
                self._ready = True
                self._fingerprint = self._structural_fingerprint()
                tag_redraw(bpy.context, space_type="PROPERTIES", region_type="WINDOW")
                return None
            self._apply_build_entry(entry)
            count += 1
            if count % _BUILD_TICK_TIME_CHECK_INTERVAL == 0 and time.monotonic() >= deadline:
                break

        self._build_progress += count
        tag_redraw(bpy.context, space_type="PROPERTIES", region_type="WINDOW")
        return 0.0

    def _apply_build_entry(self, entry):
        guuid, index, item_uuid, session_uid, data_type = entry
        if data_type is None:
            # map_data entry (no linked id)
            self._map_data_cache[item_uuid] = CacheEntityData(guuid, index)
        else:
            self._entity_cache[item_uuid] = CacheEntityData(guuid, index)
            if session_uid is not None:
                self._id_cache[session_uid] = CacheObjectData(guuid, data_type, item_uuid)

    # UUID → index lookups

    def store_entity(self, map_group_uuid: bytes, entity_uuid: bytes, entity_index: int):
        self._entity_cache[entity_uuid] = CacheEntityData(map_group_uuid, entity_index)

    def try_get_entity(self, entity_uuid: bytes) -> CacheEntityData | None:
        return self._entity_cache.get(entity_uuid)

    def evict_entity(self, entity_uuid: bytes):
        self._entity_cache.pop(entity_uuid, None)

    def store_map_data(self, map_group_uuid: bytes, map_data_uuid: bytes, map_data_index: int):
        self._map_data_cache[map_data_uuid] = CacheEntityData(map_group_uuid, map_data_index)

    def try_get_map_data(self, map_data_uuid: bytes) -> CacheEntityData | None:
        return self._map_data_cache.get(map_data_uuid)

    def evict_map_data(self, map_data_uuid: bytes):
        self._map_data_cache.pop(map_data_uuid, None)

    # ID → item lookups

    def find_by_id(self, id_data: ID) -> CacheObjectData | None:
        return self._id_cache.get(_session_uid(id_data))

    def store_id(self, id_data: ID, data: CacheObjectData):
        self._id_cache[_session_uid(id_data)] = data


MAP_INDEX = MapSessionIndex()


CACHE_NOT_READY = object()


def find_entity_by_object(obj: Object) -> "tuple[MapGroup, MapEntity] | object | None":
    """Find the MapGroup and MapEntity linked to the given Blender Object."""
    from .properties.map import get_maps

    cache = MAP_INDEX.find_by_id(obj)
    if cache is None or cache.data_type != CacheObjectData.ENTITY:
        return None if MAP_INDEX.is_ready else CACHE_NOT_READY
    maps = get_maps()
    if maps is None:
        return None
    group = maps.find_group(cache.map_group_uuid)
    if group is None:
        return None
    entity = group.find_entity(cache.data_uuid)
    if entity is None or entity.linked_object != obj:
        return None
    return (group, entity)


def find_entity_by_uuid(entity_uuid: bytes) -> "tuple[MapGroup, MapEntity] | object | None":
    from .properties.map import get_maps

    cache = MAP_INDEX.try_get_entity(entity_uuid)
    if cache is None:
        return None if MAP_INDEX.is_ready else CACHE_NOT_READY
    maps = get_maps()
    if maps is None:
        return None
    group = maps.find_group(cache.map_group_uuid)
    if group is None:
        return None
    entity = group.find_entity(entity_uuid)
    if entity is None:
        return None
    return (group, entity)


def find_grass_batch_by_object(obj: Object) -> "tuple[MapGroup, MapGrassBatch] | object | None":
    """Find the MapGroup and MapGrassBatch linked to the given Blender Object."""
    from .properties.map import get_maps

    cache = MAP_INDEX.find_by_id(obj)
    if cache is None or cache.data_type != CacheObjectData.GRASS_BATCH:
        return None if MAP_INDEX.is_ready else CACHE_NOT_READY
    maps = get_maps()
    if maps is None:
        return None
    group = maps.find_group(cache.map_group_uuid)
    if group is None:
        return None
    gb = group.find_grass_batch(cache.data_uuid)
    if gb is None or gb.linked_object != obj:
        return None
    return (group, gb)


def find_cargen_by_collection(collection: Collection) -> "tuple[MapGroup, MapCarGen] | object | None":
    """Find the MapGroup and MapCarGen linked to the given Blender Collection."""
    from .properties.map import get_maps

    cache = MAP_INDEX.find_by_id(collection)
    if cache is None or cache.data_type != CacheObjectData.CARGEN:
        return None if MAP_INDEX.is_ready else CACHE_NOT_READY
    maps = get_maps()
    if maps is None:
        return None
    group = maps.find_group(cache.map_group_uuid)
    if group is None:
        return None
    cg = group.find_cargen(cache.data_uuid)
    if cg is None or cg.linked_collection != collection:
        return None
    return (group, cg)


@bpy.app.handlers.persistent
def _on_undo_redo(_scene):
    if MAP_INDEX.is_ready and MAP_INDEX._structural_fingerprint() == MAP_INDEX._fingerprint:
        return
    MAP_INDEX.invalidate_and_rebuild()


@bpy.app.handlers.persistent
def _on_load_post(_file_path):
    MAP_INDEX.invalidate_and_rebuild()


def _on_init():
    MAP_INDEX.invalidate_and_rebuild()


def register():
    bpy.app.handlers.undo_post.append(_on_undo_redo)
    bpy.app.handlers.redo_post.append(_on_undo_redo)
    bpy.app.handlers.load_post.append(_on_load_post)

    bpy.app.timers.register(_on_init, first_interval=0.0)


def unregister():
    bpy.app.handlers.load_post.remove(_on_load_post)
    bpy.app.handlers.redo_post.remove(_on_undo_redo)
    bpy.app.handlers.undo_post.remove(_on_undo_redo)
