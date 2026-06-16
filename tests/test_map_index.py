"""Tests for ``ymap_next/map_index.py``.

``MAP_INDEX`` is built incrementally on ``bpy.app.timers``, which do not tick
under ``blender --background``. All tests force a deterministic build by
calling :func:`MapSessionIndex.ensure_ready`, which drains the build iterator
synchronously and is the same entry point intended for export.
"""

import bpy
import pytest

from ..ymap_next.map_index import (
    CACHE_NOT_READY,
    MAP_INDEX,
    CacheEntityData,
    CacheObjectData,
    find_cargen_by_collection,
    find_entity_by_object,
    find_entity_by_uuid,
    find_grass_batch_by_object,
)
from ..ymap_next.properties.map import get_maps
from .shared import assert_logs_no_errors


@pytest.fixture(autouse=True)
def _clean_map_index_state():
    """Each test starts with empty maps and an invalidated MAP_INDEX.

    Also tracks Blender objects/collections created during the test and
    removes any new ones in teardown, so tests don't leak data blocks.
    """
    def _reset():
        MAP_INDEX.invalidate()
        maps = get_maps(bpy.context)
        if maps is not None:
            maps.groups.clear()

    objs_before = set(bpy.data.objects.keys())
    colls_before = set(bpy.data.collections.keys())
    meshes_before = set(bpy.data.meshes.keys())

    _reset()

    yield

    _reset()

    for name in list(bpy.data.objects.keys()):
        if name not in objs_before:
            obj = bpy.data.objects.get(name)
            if obj is not None:
                bpy.data.objects.remove(obj, do_unlink=True)
    for name in list(bpy.data.collections.keys()):
        if name not in colls_before:
            coll = bpy.data.collections.get(name)
            if coll is not None:
                bpy.data.collections.remove(coll)
    for name in list(bpy.data.meshes.keys()):
        if name not in meshes_before:
            mesh = bpy.data.meshes.get(name)
            if mesh is not None:
                bpy.data.meshes.remove(mesh)


def _new_group(name: str = "test_group"):
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = name
    return group


def _add_cube(name: str):
    mesh = bpy.data.meshes.new(name + "_mesh")
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _add_collection(name: str):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


@assert_logs_no_errors
def test_is_ready_starts_false():
    assert MAP_INDEX.is_ready is False


@assert_logs_no_errors
def test_ensure_ready_marks_ready():
    _new_group()
    MAP_INDEX.ensure_ready()
    assert MAP_INDEX.is_ready is True


@assert_logs_no_errors
def test_ensure_ready_idempotent():
    _new_group()
    MAP_INDEX.ensure_ready()
    MAP_INDEX.ensure_ready()
    assert MAP_INDEX.is_ready is True
    assert MAP_INDEX.build_progress is None


@assert_logs_no_errors
def test_invalidate_clears_ready_and_caches():
    group = _new_group()
    entity = group.new_entity()
    map_data = group.new_map()
    MAP_INDEX.ensure_ready()
    assert MAP_INDEX.try_get_entity(entity.uuid) is not None
    assert MAP_INDEX.try_get_map_data(map_data.uuid) is not None

    MAP_INDEX.invalidate()

    assert MAP_INDEX.is_ready is False
    assert MAP_INDEX.build_progress is None
    assert MAP_INDEX.try_get_entity(entity.uuid) is None
    assert MAP_INDEX.try_get_map_data(map_data.uuid) is None


@assert_logs_no_errors
def test_build_progress_none_when_idle():
    assert MAP_INDEX.build_progress is None
    _new_group()
    MAP_INDEX.ensure_ready()
    assert MAP_INDEX.build_progress is None


@assert_logs_no_errors
def test_start_build_sets_progress_total():
    group = _new_group()
    group.new_map()
    group.new_entity()
    group.new_entity()
    group.new_grass_batch()
    group.new_cargen()
    group.new_occluder()
    group.new_lod_lights()

    # Drop the lazy-populated cache entries so we exercise start_build cleanly.
    MAP_INDEX.invalidate()

    MAP_INDEX.start_build()
    progress = MAP_INDEX.build_progress
    assert progress is not None
    processed, total = progress
    assert processed == 0
    # 1 map + 2 entities + 1 grass_batch + 1 cargen + 1 occluder + 1 lod_lights
    assert total == 7

    MAP_INDEX.ensure_ready()
    assert MAP_INDEX.build_progress is None
    assert MAP_INDEX.is_ready is True


@assert_logs_no_errors
def test_ensure_ready_finishes_partial_build():
    group = _new_group()
    entity = group.new_entity()
    MAP_INDEX.invalidate()

    MAP_INDEX.start_build()  # creates iterator, registers a timer that never fires
    MAP_INDEX.ensure_ready()  # drains the existing iterator

    assert MAP_INDEX.is_ready is True
    cached = MAP_INDEX.try_get_entity(entity.uuid)
    assert cached is not None
    assert cached.map_group_uuid == group.uuid


@assert_logs_no_errors
def test_build_indexes_entities():
    group = _new_group()
    e1_uuid = group.new_entity().uuid
    e2_uuid = group.new_entity().uuid
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    c1 = MAP_INDEX.try_get_entity(e1_uuid)
    c2 = MAP_INDEX.try_get_entity(e2_uuid)
    assert c1 is not None and c2 is not None
    assert c1.index == 0 and c2.index == 1
    assert c1.map_group_uuid == group.uuid


@assert_logs_no_errors
def test_build_indexes_map_data():
    group = _new_group()
    m1_uuid = group.new_map().uuid
    m2_uuid = group.new_map().uuid
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    c1 = MAP_INDEX.try_get_map_data(m1_uuid)
    c2 = MAP_INDEX.try_get_map_data(m2_uuid)
    assert c1 is not None and c2 is not None
    assert c1.index == 0 and c2.index == 1


@assert_logs_no_errors
def test_build_indexes_grass_batches():
    group = _new_group()
    gb = group.new_grass_batch()
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.try_get_entity(gb.uuid)
    assert cached is not None
    assert cached.map_group_uuid == group.uuid


@assert_logs_no_errors
def test_build_indexes_cargens():
    group = _new_group()
    cg = group.new_cargen()
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.try_get_entity(cg.uuid)
    assert cached is not None


@assert_logs_no_errors
def test_build_indexes_occluders():
    group = _new_group()
    occ = group.new_occluder()
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.try_get_entity(occ.uuid)
    assert cached is not None


@assert_logs_no_errors
def test_build_indexes_lod_lights():
    group = _new_group()
    ll = group.new_lod_lights()
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.try_get_entity(ll.uuid)
    assert cached is not None


@assert_logs_no_errors
def test_find_by_id_entity():
    group = _new_group()
    obj = _add_cube("entity_obj")
    entity = group.new_entity()
    entity.linked_object = obj
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.find_by_id(obj)
    assert cached is not None
    assert cached.data_type == CacheObjectData.ENTITY
    assert cached.data_uuid == entity.uuid
    assert cached.map_group_uuid == group.uuid


@assert_logs_no_errors
def test_find_by_id_grass_batch_data_type():
    group = _new_group()
    obj = _add_cube("grass_obj")
    gb = group.new_grass_batch()
    gb.linked_object = obj
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.find_by_id(obj)
    assert cached is not None
    assert cached.data_type == CacheObjectData.GRASS_BATCH
    assert cached.data_uuid == gb.uuid


@assert_logs_no_errors
def test_find_by_id_cargen_with_linked_collection():
    group = _new_group()
    coll = _add_collection("cargen_coll")
    cg = group.new_cargen()
    cg.linked_collection = coll
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.find_by_id(coll)
    assert cached is not None
    assert cached.data_type == CacheObjectData.CARGEN
    assert cached.data_uuid == cg.uuid


@assert_logs_no_errors
def test_find_by_id_occluder_data_type():
    group = _new_group()
    obj = _add_cube("occluder_obj")
    occ = group.new_occluder()
    occ.linked_object = obj
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.find_by_id(obj)
    assert cached is not None
    assert cached.data_type == CacheObjectData.OCCLUDER
    assert cached.data_uuid == occ.uuid


@assert_logs_no_errors
def test_find_by_id_lod_lights_data_type():
    group = _new_group()
    obj = _add_cube("lod_lights_obj")
    ll = group.new_lod_lights()
    ll.linked_object = obj
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    cached = MAP_INDEX.find_by_id(obj)
    assert cached is not None
    assert cached.data_type == CacheObjectData.LOD_LIGHTS
    assert cached.data_uuid == ll.uuid


@assert_logs_no_errors
def test_id_cache_skips_unlinked_entity():
    group = _new_group()
    linked_obj = _add_cube("linked")
    unrelated_obj = _add_cube("unrelated")

    group.new_entity()  # no linked_object
    linked = group.new_entity()
    linked.linked_object = linked_obj
    MAP_INDEX.invalidate()

    MAP_INDEX.ensure_ready()

    assert MAP_INDEX.find_by_id(linked_obj) is not None
    assert MAP_INDEX.find_by_id(unrelated_obj) is None


@assert_logs_no_errors
def test_store_get_evict_entity():
    group_uuid = b"\x01" * 16
    entity_uuid = b"\x02" * 16

    assert MAP_INDEX.try_get_entity(entity_uuid) is None

    MAP_INDEX.store_entity(group_uuid, entity_uuid, 42)
    cached = MAP_INDEX.try_get_entity(entity_uuid)
    assert cached is not None
    assert cached.map_group_uuid == group_uuid
    assert cached.index == 42

    MAP_INDEX.evict_entity(entity_uuid)
    assert MAP_INDEX.try_get_entity(entity_uuid) is None

    # Evicting a missing key must not raise.
    MAP_INDEX.evict_entity(entity_uuid)


@assert_logs_no_errors
def test_store_get_evict_map_data():
    group_uuid = b"\x03" * 16
    map_uuid = b"\x04" * 16

    assert MAP_INDEX.try_get_map_data(map_uuid) is None

    MAP_INDEX.store_map_data(group_uuid, map_uuid, 7)
    cached = MAP_INDEX.try_get_map_data(map_uuid)
    assert cached is not None
    assert cached.map_group_uuid == group_uuid
    assert cached.index == 7

    MAP_INDEX.evict_map_data(map_uuid)
    assert MAP_INDEX.try_get_map_data(map_uuid) is None
    MAP_INDEX.evict_map_data(map_uuid)


@assert_logs_no_errors
def test_store_id_round_trip():
    obj = _add_cube("store_id_obj")
    data = CacheObjectData(b"\x05" * 16, CacheObjectData.ENTITY, b"\x06" * 16)

    assert MAP_INDEX.find_by_id(obj) is None

    MAP_INDEX.store_id(obj, data)

    cached = MAP_INDEX.find_by_id(obj)
    assert cached is data


@assert_logs_no_errors
def test_find_entity_by_uuid():
    group = _new_group()
    entity_uuid = group.new_entity().uuid
    # Drop the lazy-populated cache entry so the lookup goes through the build.
    MAP_INDEX.invalidate()
    MAP_INDEX.ensure_ready()

    result = find_entity_by_uuid(entity_uuid)
    assert result is not None and result is not CACHE_NOT_READY
    found_group, found_entity = result
    assert found_group.uuid == group.uuid
    assert found_entity.uuid == entity_uuid


@assert_logs_no_errors
def test_find_entity_by_uuid_returns_cache_not_ready_sentinel():
    # No entity exists and the cache has never been built. Lookup of an
    # unknown UUID must return the CACHE_NOT_READY sentinel, not None.
    _new_group()
    assert MAP_INDEX.is_ready is False
    assert find_entity_by_uuid(b"\xff" * 16) is CACHE_NOT_READY


@assert_logs_no_errors
def test_find_entity_by_uuid_returns_none_when_missing():
    _new_group()
    MAP_INDEX.ensure_ready()
    assert MAP_INDEX.is_ready is True
    assert find_entity_by_uuid(b"\xff" * 16) is None


@assert_logs_no_errors
def test_find_entity_by_object():
    group = _new_group()
    obj = _add_cube("find_entity_obj")
    entity = group.new_entity()
    entity.linked_object = obj
    MAP_INDEX.invalidate()
    MAP_INDEX.ensure_ready()

    result = find_entity_by_object(obj)
    assert result is not None and result is not CACHE_NOT_READY
    found_group, found_entity = result
    assert found_group.uuid == group.uuid
    assert found_entity.uuid == entity.uuid


@assert_logs_no_errors
def test_find_entity_by_object_returns_none_when_linked_object_swapped():
    group = _new_group()
    original = _add_cube("original_obj")
    replacement = _add_cube("replacement_obj")
    entity = group.new_entity()
    entity.linked_object = original
    MAP_INDEX.invalidate()
    MAP_INDEX.ensure_ready()

    # Reassign linked_object without rebuilding the cache. The reverse
    # lookup must reject the stale hit (linked_object != obj guard in
    # find_entity_by_object).
    entity.linked_object = replacement

    assert find_entity_by_object(original) is None


@assert_logs_no_errors
def test_find_grass_batch_by_object():
    group = _new_group()
    obj = _add_cube("gb_obj")
    gb = group.new_grass_batch()
    gb.linked_object = obj
    MAP_INDEX.invalidate()
    MAP_INDEX.ensure_ready()

    result = find_grass_batch_by_object(obj)
    assert result is not None and result is not CACHE_NOT_READY
    found_group, found_gb = result
    assert found_group.uuid == group.uuid
    assert found_gb.uuid == gb.uuid


@assert_logs_no_errors
def test_find_cargen_by_collection():
    group = _new_group()
    coll = _add_collection("cg_coll")
    cg = group.new_cargen()
    cg.linked_collection = coll
    MAP_INDEX.invalidate()
    MAP_INDEX.ensure_ready()

    result = find_cargen_by_collection(coll)
    assert result is not None and result is not CACHE_NOT_READY
    found_group, found_cg = result
    assert found_group.uuid == group.uuid
    assert found_cg.uuid == cg.uuid


@assert_logs_no_errors
def test_fingerprint_changes_after_adding_entity():
    group = _new_group()
    group.new_entity()
    before = MAP_INDEX._structural_fingerprint()

    group.new_entity()
    after = MAP_INDEX._structural_fingerprint()

    assert before != after
