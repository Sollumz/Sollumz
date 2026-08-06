from uuid import uuid4

import bpy
from numpy.testing import assert_allclose

from ..iecontext import ExportContext, ExportSettings, export_context_scope
from ..ymap_next.partitioning import PartitioningSettings, collapse_to_auto, generate_partitions
from ..ymap_next.properties.map import MapCarGen, MapPartitionMode, get_maps
from ..ymap_next.ymapexport import export_ymap
from .shared import assert_logs_no_errors


def _make_group_with_maps(name: str, num_maps: int = 2):
    """Create a map group with containers named `<name>_a`, `<name>_b`, ... Returns the group and the
    container UUIDs.
    """
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = name

    map_uuids = []
    for i in range(num_maps):
        md = group.new_map()
        md.name = f"{name}_{chr(ord('a') + i)}"
        map_uuids.append(md.uuid)
    return group, map_uuids


def _add_cargen(group, primary_uuid, extra_uuids=(), *, object_positions=(), object_slots=()):
    cargen = group.new_cargen()
    cargen.model = "adder"
    cargen.map_data_uuid = primary_uuid
    for extra_uuid in extra_uuids:
        cargen.add_extra_map_data(extra_uuid)

    coll = bpy.data.collections.new(f"{group.name}.cargen")
    bpy.context.scene.collection.children.link(coll)
    cargen.linked_collection = coll

    mesh = MapCarGen.get_cargen_mesh()

    for i, pos in enumerate(object_positions):
        obj = bpy.data.objects.new(f"{group.name}.cargen.{i}", mesh)
        obj.location = pos
        if i < len(object_slots):
            obj.sz_cargen_map_data_index = object_slots[i]
        coll.objects.link(obj)

    bpy.context.view_layer.update()
    return cargen


@assert_logs_no_errors
def test_resolve_map_data_uuids_falls_back_to_primary():
    group, (a_uuid, b_uuid) = _make_group_with_maps("test_mc_resolve")
    cargen = _add_cargen(group, a_uuid, [b_uuid, uuid4().bytes, b""])

    assert cargen.raw_slot_uuids()[:2] == [a_uuid, b_uuid]
    # Dangling and empty extras resolve to the primary
    assert cargen.resolve_map_data_uuids(group) == [a_uuid, b_uuid, a_uuid, a_uuid]


@assert_logs_no_errors
def test_quick_add_no_duplicate_slots():
    group, (a_uuid, b_uuid) = _make_group_with_maps("test_mc_quick_add")
    cargen = _add_cargen(group, a_uuid)

    cargen.new_map_data_name = "test_mc_quick_add_b"
    cargen.new_map_data_name = "test_mc_quick_add_b"  # already an extra slot
    cargen.new_map_data_name = "test_mc_quick_add_a"  # already the primary
    cargen.new_map_data_name = "does_not_exist"

    assert [ref.map_data_uuid for ref in cargen.extra_map_datas] == [b_uuid]


@assert_logs_no_errors
def test_remove_slot_remaps_cargen_object_indices():
    group, uuids = _make_group_with_maps("test_mc_remove", 3)
    _add_cargen(
        group,
        uuids[0],
        uuids[1:],
        object_positions=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0), (2.0, 0.0, 0.0)),
        object_slots=(0, 1, 2),
    )

    bpy.ops.sollumz.map_cargen_remove_extra_map_data(index=0)  # removes slot 1

    cargen = group.cargens.active_item
    assert [ref.map_data_uuid for ref in cargen.extra_map_datas] == [uuids[2]]
    coll = cargen.linked_collection
    slots = [coll.objects[f"test_mc_remove.cargen.{i}"].sz_cargen_map_data_index for i in range(3)]
    # Slot 1 falls back to the primary, slot 2 shifts down to keep referencing the same container
    assert slots == [0, 0, 1]


@assert_logs_no_errors
def test_remove_slot_redirects_to_surviving_duplicate():
    group, (a_uuid, b_uuid) = _make_group_with_maps("test_mc_dup_remove")
    # Duplicate slots referencing the same container: [a, b, b]
    _add_cargen(
        group,
        a_uuid,
        [b_uuid, b_uuid],
        object_positions=((0.0, 0.0, 0.0), (1.0, 0.0, 0.0)),
        object_slots=(1, 2),
    )

    bpy.ops.sollumz.map_cargen_remove_extra_map_data(index=0)  # removes slot 1, slot 2 references b too

    # Both objects still reference container b through the surviving slot, not the primary
    cargen = group.cargens.active_item
    coll = cargen.linked_collection
    slots = [coll.objects[f"test_mc_dup_remove.cargen.{i}"].sz_cargen_map_data_index for i in range(2)]
    assert slots == [1, 1]
    assert cargen.resolve_map_data_uuids(group) == [a_uuid, b_uuid]


def _export_group_assets(group) -> dict:
    """Export the group and return the szio AssetMapData per container name."""
    from szio.gta5 import AssetFormat, AssetTarget, AssetVersion

    settings = ExportSettings(targets=(AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8),))
    with export_context_scope(ExportContext(group.name.lower(), settings)):
        bundles = export_ymap(group)

    assert bundles, "Export produced no bundles"
    for b in bundles:
        assert b.is_valid(), "Export bundle is not valid"
    return {b.asset_name: b.main_asset for b in bundles}


@assert_logs_no_errors
def test_export_splits_cargen_objects_across_containers():
    group, (a_uuid, b_uuid) = _make_group_with_maps("test_mc_export_split")
    _add_cargen(
        group,
        a_uuid,
        [b_uuid],
        object_positions=((1.0, 2.0, 3.0), (10.0, 20.0, 30.0)),
        object_slots=(0, 1),
    )

    assets = _export_group_assets(group)
    (cg_a,) = assets["test_mc_export_split_a"].car_generators
    (cg_b,) = assets["test_mc_export_split_b"].car_generators
    assert tuple(cg_a.position) == (1.0, 2.0, 3.0)
    assert tuple(cg_b.position) == (10.0, 20.0, 30.0)


@assert_logs_no_errors
def test_export_invalid_slots_fall_back_to_primary():
    group, (a_uuid, _b_uuid) = _make_group_with_maps("test_mc_export_invalid")
    # One object on an out-of-range slot, one on a dangling extra
    _add_cargen(
        group,
        a_uuid,
        [uuid4().bytes],
        object_positions=((0.0, 0.0, 0.0), (5.0, 0.0, 0.0)),
        object_slots=(5, 1),
    )

    assets = _export_group_assets(group)
    assert len(assets["test_mc_export_invalid_a"].car_generators) == 2
    assert not assets["test_mc_export_invalid_b"].car_generators


@assert_logs_no_errors
def test_export_duplicate_slots_export_once():
    group, (a_uuid, _b_uuid) = _make_group_with_maps("test_mc_export_dup")
    # The extra references the same container as the primary; each object exports exactly once
    _add_cargen(
        group,
        a_uuid,
        [a_uuid],
        object_positions=((0.0, 0.0, 0.0), (5.0, 0.0, 0.0)),
        object_slots=(0, 1),
    )

    assets = _export_group_assets(group)
    assert len(assets["test_mc_export_dup_a"].car_generators) == 2
    assert not assets["test_mc_export_dup_b"].car_generators


@assert_logs_no_errors
def test_export_extents_cover_only_assigned_objects():
    group, (a_uuid, b_uuid) = _make_group_with_maps("test_mc_export_extents")
    cargen = _add_cargen(
        group,
        a_uuid,
        [b_uuid],
        object_positions=((0.0, 0.0, 0.0), (100.0, 0.0, 0.0)),
        object_slots=(0, 1),
    )
    half = tuple(cargen.linked_collection.objects["test_mc_export_extents.cargen.0"].dimensions / 2)

    _export_group_assets(group)

    # Extents are recalculated during export; each container covers only the objects assigned to it
    map_a = group.find_map(a_uuid)
    assert_allclose(tuple(map_a.entities_extents_min), (-half[0], -half[1], -half[2]), atol=1e-5)
    assert_allclose(tuple(map_a.entities_extents_max), half, atol=1e-5)
    map_b = group.find_map(b_uuid)
    assert_allclose(tuple(map_b.entities_extents_min), (100.0 - half[0], -half[1], -half[2]), atol=1e-5)
    assert_allclose(tuple(map_b.entities_extents_max), (100.0 + half[0], half[1], half[2]), atol=1e-5)


def _add_strm_entity(group, map_uuid, pos):
    e = group.new_entity()
    e.archetype_name = "test_strm_building"
    e.lod_level = "HD"
    e.lod_dist = 80
    e.position = pos
    e.map_data_uuid = map_uuid


@assert_logs_no_errors
def test_partition_assigns_cargen_objects_to_entity_chunks():
    group, (parent_uuid,) = _make_group_with_maps("test_mc_part_chunks", 1)
    group.find_map(parent_uuid).partition_mode = MapPartitionMode.AUTO.name

    # Two entity clusters far apart; max_per_chunk=4 forces one strm chunk per cluster
    for x in (0.0, 500.0):
        for dx, dy in ((0, 0), (10, 0), (0, 10), (10, 10)):
            _add_strm_entity(group, parent_uuid, (x + dx, dy, 0.0))

    cargen = _add_cargen(group, parent_uuid, object_positions=((5.0, 5.0, 0.0), (505.0, 5.0, 0.0)))

    generate_partitions(group, group.find_map(parent_uuid), PartitioningSettings(max_per_chunk=4))

    # One object per cluster: the cargen spans both strm leaves, each object in its cluster's leaf
    uuids = cargen.resolve_map_data_uuids(group)
    assert len(uuids) == 2 and len(set(uuids)) == 2
    coll = cargen.linked_collection
    obj0_uuid = uuids[coll.objects["test_mc_part_chunks.cargen.0"].sz_cargen_map_data_index]
    obj1_uuid = uuids[coll.objects["test_mc_part_chunks.cargen.1"].sz_cargen_map_data_index]
    entities_by_pos = {tuple(e.position): e for e in group.entities}
    assert obj0_uuid == entities_by_pos[(0.0, 0.0, 0.0)].map_data_uuid
    assert obj1_uuid == entities_by_pos[(500.0, 0.0, 0.0)].map_data_uuid
    assert cargen.map_data_uuid == obj0_uuid  # slot 0 (primary) comes from the first object
    for uuid in uuids:
        m = group.find_map(uuid)
        assert m.is_auto_generated and m.parent_uuid == parent_uuid and "_strm_" in m.name


@assert_logs_no_errors
def test_partition_objects_outside_entity_extents_get_own_bucket():
    group, (parent_uuid,) = _make_group_with_maps("test_mc_part_outside", 1)
    group.find_map(parent_uuid).partition_mode = MapPartitionMode.AUTO.name

    # Single entity cluster covering (0,0)..(10,10) -> one strm chunk
    for dx, dy in ((0, 0), (10, 0), (0, 10), (10, 10)):
        _add_strm_entity(group, parent_uuid, (dx, dy, 0.0))

    cargen = _add_cargen(
        group,
        parent_uuid,
        object_positions=((5.0, 5.0, 0.0), (1000.0, 0.0, 0.0), (1010.0, 0.0, 0.0)),
    )

    generate_partitions(group, group.find_map(parent_uuid), PartitioningSettings(max_per_chunk=4))

    # The two objects outside the entity extents share their own strm bucket
    uuids = cargen.resolve_map_data_uuids(group)
    names = [group.find_map(u).name for u in uuids]
    assert names == ["test_mc_part_outside_a_strm_0", "test_mc_part_outside_a_strm_1"]
    coll = cargen.linked_collection
    slots = [coll.objects[f"test_mc_part_outside.cargen.{i}"].sz_cargen_map_data_index for i in range(3)]
    assert slots == [0, 1, 1]

    # Regenerating rebuilds the slots from scratch: same shape, no accumulated extras or stale leaves
    generate_partitions(group, group.find_map(parent_uuid), PartitioningSettings(max_per_chunk=4))

    assert len(group.maps) == 3  # parent + 2 strm leaves
    assert len(cargen.extra_map_datas) == 1
    assert [group.find_map(u).name for u in cargen.resolve_map_data_uuids(group)] == names
    slots = [coll.objects[f"test_mc_part_outside.cargen.{i}"].sz_cargen_map_data_index for i in range(3)]
    assert slots == [0, 1, 1]


@assert_logs_no_errors
def test_collapse_to_auto_remaps_cargen_extras():
    group, (parent_uuid, leaf_a_uuid, leaf_b_uuid) = _make_group_with_maps("test_mc_collapse", 3)
    group.find_map(leaf_a_uuid).parent_uuid = parent_uuid
    group.find_map(leaf_b_uuid).parent_uuid = parent_uuid
    cargen = _add_cargen(
        group,
        leaf_a_uuid,
        [leaf_b_uuid],
        object_positions=((0.0, 0.0, 0.0), (5.0, 0.0, 0.0)),
        object_slots=(0, 1),
    )

    collapse_to_auto(group, group.find_map(parent_uuid))

    # Primary and extra both collapse to the parent; objects keep their slot indices
    assert cargen.map_data_uuid == parent_uuid
    assert [ref.map_data_uuid for ref in cargen.extra_map_datas] == [parent_uuid]
    assert cargen.resolve_map_data_uuids(group) == [parent_uuid, parent_uuid]
