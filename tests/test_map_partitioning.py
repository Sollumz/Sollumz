from pathlib import Path
from xml.etree import ElementTree as ET

import bpy

from ..ymap_next.ymapexport import export_ymap
from ..ymap_next.properties.map import get_maps, MapPartitionMode
from ..ymap_next.partitioning import (
    generate_partitions,
    collapse_to_auto,
    convert_to_manual,
    auto_assign_unassigned,
    PartitioningSettings,
)
from ..iecontext import export_context_scope, ExportContext, ExportSettings
from .shared import (
    assert_logs_no_errors,
    is_tmp_dir_available,
    SOLLUMZ_TEST_ASSETS_DIR,
)
from .shared import (
    tmp_path as tmp_path_with_subdir,
)


YMAP_ASSETS_DIR = SOLLUMZ_TEST_ASSETS_DIR / "cwxml" / "ymap"


def _import_ymaps(*filenames: str):
    bpy.ops.sollumz.import_ymap(
        directory=str(YMAP_ASSETS_DIR) + "/",
        files=[{"name": f} for f in filenames],
    )


def _export_map_group(map_group, output_dir: Path):
    from szio.gta5 import AssetFormat, AssetVersion, AssetTarget

    settings = ExportSettings(targets=(AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8),))
    with export_context_scope(ExportContext(map_group.name.lower(), settings)):
        bundles = export_ymap(map_group)

    assert bundles, "Export produced no bundles"
    for b in bundles:
        assert b.is_valid(), "Export bundle is not valid"
        b.save(output_dir, settings.targets)
    return bundles


def _last_map_group():
    maps = get_maps()
    assert maps is not None and len(maps.groups) > 0
    return maps.groups[len(maps.groups) - 1]


def _parse_xml(path: Path) -> ET.Element:
    tree = ET.ElementTree()
    tree.parse(str(path))
    return tree.getroot()


def _get_text(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    if child is None:
        return ""
    return child.text or ""


def _get_value(el: ET.Element, tag: str) -> str:
    child = el.find(tag)
    if child is None:
        return ""
    return child.attrib.get("value", "")


def _find_map(group, uuid):
    """Find a map data by UUID. Needed because Blender CollectionProperty invalidates
    element references when new items are added."""
    for m in group.maps:
        if m.uuid == uuid:
            return m
    return None


def _make_map_group_with_mixed_entities():
    """Create a map group programmatically with LOD, HD, OrphanHD, MLO, and critical entities.

    Returns the group and the UUID of the logical AUTO map data (not a direct reference,
    because Blender CollectionProperty invalidates references when items are added).
    """
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = "test_auto_partition"

    logical = group.new_map()
    logical.name = "test_sector"
    logical.partition_mode = MapPartitionMode.AUTO.name
    logical_uuid = logical.uuid

    # LOD entity (should stay in logical map)
    lod = group.new_entity()
    lod.archetype_name = "test_lod_model"
    lod.lod_level = "LOD"
    lod.lod_dist = 500
    lod.child_lod_dist = 100
    lod.position = (100, 100, 50)
    lod.map_data_uuid = logical_uuid
    lod_uuid = lod.uuid

    # HD entity (should go into _strm_)
    hd1 = group.new_entity()
    hd1.archetype_name = "test_hd_building_a"
    hd1.lod_level = "HD"
    hd1.lod_dist = 80
    hd1.position = (90, 90, 50)
    hd1.parent_uuid = lod_uuid
    hd1.map_data_uuid = logical_uuid

    # HD entity (should go into _strm_)
    hd2 = group.new_entity()
    hd2.archetype_name = "test_hd_building_b"
    hd2.lod_level = "HD"
    hd2.lod_dist = 80
    hd2.position = (110, 110, 50)
    hd2.parent_uuid = lod_uuid
    hd2.map_data_uuid = logical_uuid

    # HD entity with high lodDist (should go into _long_)
    far = group.new_entity()
    far.archetype_name = "test_hd_far_tree"
    far.lod_level = "HD"
    far.lod_dist = 300
    far.position = (200, 200, 50)
    far.map_data_uuid = logical_uuid

    # OrphanHD with low lodDist (should go into _strm_)
    orphan_near = group.new_entity()
    orphan_near.archetype_name = "test_orphan_near"
    orphan_near.lod_level = "HD"
    orphan_near.lod_dist = 50
    orphan_near.position = (150, 150, 50)
    orphan_near.map_data_uuid = logical_uuid

    # Critical entity (should go into _critical_)
    crit = group.new_entity()
    crit.archetype_name = "test_critical_pole"
    crit.lod_level = "HD"
    crit.lod_dist = 100
    crit.is_critical = True
    crit.position = (300, 300, 50)
    crit.map_data_uuid = logical_uuid

    # MLO entity (should go into _interior_)
    mlo = group.new_entity()
    mlo.archetype_name = "v_test_shop"
    mlo.lod_level = "HD"
    mlo.lod_dist = 60
    mlo.is_mlo = True
    mlo.position = (400, 400, 50)
    mlo.map_data_uuid = logical_uuid

    return group, logical_uuid


@assert_logs_no_errors
def test_auto_partition_generates_leaves():
    """AUTO partitioning creates the correct leaf map datas and reassigns items."""
    group, logical_uuid = _make_map_group_with_mixed_entities()

    logical = _find_map(group, logical_uuid)
    generate_partitions(group, logical, PartitioningSettings(max_per_chunk=128))

    # Re-lookup after generate_partitions (collection may have been reallocated)
    children = [m for m in group.maps if m.parent_uuid == logical_uuid and m.is_auto_generated]
    child_names = {m.name for m in children}

    # Should have strm, long, critical, and interior leaves
    assert any("strm" in n for n in child_names), f"Missing _strm_ leaf in {child_names}"
    assert any("long" in n for n in child_names), f"Missing _long_ leaf in {child_names}"
    assert any("critical" in n for n in child_names), f"Missing _critical_ leaf in {child_names}"
    assert any("interior" in n for n in child_names), f"Missing _interior_ leaf in {child_names}"

    # LOD entity should still be in the logical map
    lod_entities = [e for e in group.entities if e.lod_level == "LOD"]
    assert len(lod_entities) == 1
    assert lod_entities[0].map_data_uuid == logical_uuid

    # HD entities with low lodDist should be in strm leaves
    strm_maps = {m.uuid for m in children if "strm" in m.name}
    hd_strm = [e for e in group.entities if e.archetype_name.startswith("test_hd_building")]
    for e in hd_strm:
        assert e.map_data_uuid in strm_maps, f"{e.archetype_name} not in strm"

    # OrphanHD with low lodDist should also be in strm
    orphan_near = [e for e in group.entities if e.archetype_name == "test_orphan_near"]
    assert len(orphan_near) == 1
    assert orphan_near[0].map_data_uuid in strm_maps

    # High lodDist entity should be in long
    long_maps = {m.uuid for m in children if "long" in m.name}
    far = [e for e in group.entities if e.archetype_name == "test_hd_far_tree"]
    assert len(far) == 1
    assert far[0].map_data_uuid in long_maps

    # Critical entity should be in critical
    crit_maps = {m.uuid for m in children if "critical" in m.name}
    crit = [e for e in group.entities if e.archetype_name == "test_critical_pole"]
    assert len(crit) == 1
    assert crit[0].map_data_uuid in crit_maps

    # MLO entity should be in interior
    interior_maps = {m.uuid for m in children if "interior" in m.name}
    mlo = [e for e in group.entities if e.archetype_name == "v_test_shop"]
    assert len(mlo) == 1
    assert mlo[0].map_data_uuid in interior_maps

    # Interior leaf name should contain archetype
    interior_leaf = [m for m in children if "interior" in m.name][0]
    assert "v_test_shop" in interior_leaf.name


@assert_logs_no_errors
def test_auto_partition_regenerate():
    """Regenerating partitions redistributes new items correctly."""
    group, logical_uuid = _make_map_group_with_mixed_entities()

    logical = _find_map(group, logical_uuid)
    generate_partitions(group, logical, PartitioningSettings(max_per_chunk=128))
    children_before = [m for m in group.maps if m.parent_uuid == logical_uuid and m.is_auto_generated]
    num_children_before = len(children_before)
    assert num_children_before > 0

    # Add a new HD entity to the logical parent (simulating user adding an entity)
    new_entity = group.new_entity()
    new_entity.archetype_name = "test_new_hd_prop"
    new_entity.lod_level = "HD"
    new_entity.lod_dist = 80
    new_entity.position = (95, 95, 50)
    new_entity.map_data_uuid = logical_uuid

    # Regenerate (re-lookup logical since collection may have been reallocated)
    logical = _find_map(group, logical_uuid)
    generate_partitions(group, logical, PartitioningSettings(max_per_chunk=128))

    # New entity should now be in a strm leaf
    strm_maps = {m.uuid for m in group.maps if m.is_auto_generated and "strm" in m.name}
    new_entities = [e for e in group.entities if e.archetype_name == "test_new_hd_prop"]
    assert len(new_entities) == 1
    assert new_entities[0].map_data_uuid in strm_maps, "New entity was not distributed to strm leaf"

    # All entities still accounted for
    total_entities = len(group.entities)
    assert total_entities == 8  # 7 original + 1 new


@assert_logs_no_errors
def test_collapse_to_auto_and_regenerate():
    """Collapse manual children into parent, switch to AUTO, regenerate."""
    group, logical_uuid = _make_map_group_with_mixed_entities()
    logical = _find_map(group, logical_uuid)
    logical.partition_mode = MapPartitionMode.NONE.name  # Start in manual mode

    settings = PartitioningSettings(max_per_chunk=128)

    # Create some manual child maps and assign entities to them
    child1 = group.new_map()
    child1.name = "test_sector_strm_0"
    child1.parent_uuid = logical_uuid
    child1_uuid = child1.uuid

    child2 = group.new_map()
    child2.name = "test_sector_long_0"
    child2.parent_uuid = logical_uuid
    child2_uuid = child2.uuid

    # Move some entities to child maps
    for e in group.entities:
        if e.lod_level == "HD" and e.lod_dist < settings.long_lod_dist_threshold and not e.is_critical and not e.is_mlo:
            e.map_data_uuid = child1_uuid
        elif e.lod_dist >= settings.long_lod_dist_threshold:
            e.map_data_uuid = child2_uuid

    # Collapse to auto (re-lookup logical since new_map may have invalidated it)
    logical = _find_map(group, logical_uuid)
    collapse_to_auto(group, logical)

    # Re-lookup after collapse (maps collection modified)
    logical = _find_map(group, logical_uuid)
    assert logical.partition_mode == MapPartitionMode.AUTO.name

    # Manual children should be removed
    remaining_children = [m for m in group.maps if m.parent_uuid == logical_uuid]
    assert len(remaining_children) == 0, "Manual children should have been removed"

    # Regenerate
    logical = _find_map(group, logical_uuid)
    generate_partitions(group, logical, settings)
    auto_children = [m for m in group.maps if m.parent_uuid == logical_uuid and m.is_auto_generated]
    assert len(auto_children) > 0, "Regeneration should create auto-generated children"


@assert_logs_no_errors
def test_convert_to_manual():
    """Converting AUTO to manual keeps leaves but clears is_auto_generated."""
    group, logical_uuid = _make_map_group_with_mixed_entities()

    logical = _find_map(group, logical_uuid)
    generate_partitions(group, logical, PartitioningSettings(max_per_chunk=128))
    children = [m for m in group.maps if m.parent_uuid == logical_uuid and m.is_auto_generated]
    assert len(children) > 0

    logical = _find_map(group, logical_uuid)
    convert_to_manual(group, logical)

    logical = _find_map(group, logical_uuid)
    assert logical.partition_mode == MapPartitionMode.NONE.name
    # Children should still exist but no longer be auto-generated
    for m in group.maps:
        if m.parent_uuid == logical_uuid:
            assert not m.is_auto_generated, f"{m.name} should not be auto-generated after convert"


@assert_logs_no_errors
def test_auto_assign_unassigned():
    """Unassigned items get assigned to the nearest leaf map data."""
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = "test_auto_assign"

    root = group.new_map()
    root.name = "test_root"

    # Two leaf map datas at different locations
    leaf_a = group.new_map()
    leaf_a.name = "test_leaf_a"
    leaf_a.parent_uuid = root.uuid
    leaf_a.entities_extents_min = (0, 0, 0)
    leaf_a.entities_extents_max = (100, 100, 100)

    leaf_b = group.new_map()
    leaf_b.name = "test_leaf_b"
    leaf_b.parent_uuid = root.uuid
    leaf_b.entities_extents_min = (900, 900, 0)
    leaf_b.entities_extents_max = (1000, 1000, 100)

    # Entity near leaf_a (unassigned)
    e1 = group.new_entity()
    e1.archetype_name = "near_a"
    e1.position = (50, 50, 50)
    e1.lod_level = "HD"
    # map_data_uuid left empty

    # Entity near leaf_b (unassigned)
    e2 = group.new_entity()
    e2.archetype_name = "near_b"
    e2.position = (950, 950, 50)
    e2.lod_level = "HD"
    # map_data_uuid left empty

    auto_assign_unassigned(group)

    assert e1.map_data_uuid == leaf_a.uuid, "Entity near A should be assigned to leaf_a"
    assert e2.map_data_uuid == leaf_b.uuid, "Entity near B should be assigned to leaf_b"


@assert_logs_no_errors
def test_strm_partitioning_splits_into_multiple_chunks():
    """A large strm bucket is spatially partitioned into multiple count-capped strm leaves."""
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = "test_strm_split"

    logical = group.new_map()
    logical.name = "test_sector"
    logical.partition_mode = MapPartitionMode.AUTO.name
    logical_uuid = logical.uuid

    max_per_chunk = 64
    side = 16                       # 16 x 16 = 256 entities
    num_entities = side * side
    spacing = 50.0

    # Spread entities across a 2D grid so the KD-tree actually splits them spatially.
    for i in range(num_entities):
        e = group.new_entity()
        e.archetype_name = f"test_hd_prop_{i}"
        e.lod_level = "HD"
        e.lod_dist = 80.0           # > 0 (no archetype lookup) and < 150 (long threshold) -> "strm"
        e.position = ((i % side) * spacing, (i // side) * spacing, 0.0)
        e.map_data_uuid = logical_uuid

    # Re-lookup logical: adding to a CollectionProperty can reallocate references.
    logical = _find_map(group, logical_uuid)
    generate_partitions(group, logical, PartitioningSettings(max_per_chunk=max_per_chunk))

    children = [m for m in group.maps if m.parent_uuid == logical_uuid and m.is_auto_generated]
    strm_leaves = [m for m in children if "strm" in m.name]

    # 1. Multiple strm buckets were created.
    assert len(strm_leaves) >= 2, \
        f"Expected multiple strm leaves, got {len(strm_leaves)}: {[m.name for m in strm_leaves]}"

    # Group entities by their assigned strm leaf.
    strm_leaf_uuids = {m.uuid for m in strm_leaves}
    per_leaf = {}
    for e in group.entities:
        if e.map_data_uuid in strm_leaf_uuids:
            per_leaf.setdefault(e.map_data_uuid, []).append(e)

    # 2. Completeness: every created entity routed to exactly one strm leaf (no loss/dupes).
    total = sum(len(v) for v in per_leaf.values())
    assert total == num_entities, f"Expected {num_entities} entities across strm leaves, got {total}"

    # 3. Each strm leaf respects the cap.
    for ents in per_leaf.values():
        assert len(ents) <= max_per_chunk, \
            f"strm leaf has {len(ents)} entities, exceeds cap {max_per_chunk}"

    # 4. Leaf names are unique (strm_0, strm_1, ...).
    names = [m.name for m in strm_leaves]
    assert len(set(names)) == len(names), f"Duplicate strm leaf names: {names}"

    # 5. Spatial coherence: leaves cover roughly disjoint regions, so the summed area of the
    #    per-leaf bounding boxes stays close to the global bbox area. A non-spatial (random)
    #    assignment would instead make each leaf span the whole map, summing to ~N_leaves * global.
    def _bbox_area(pts):
        xs = [p[0] for p in pts]
        ys = [p[1] for p in pts]
        return (max(xs) - min(xs)) * (max(ys) - min(ys))

    all_pts = [(e.position[0], e.position[1]) for v in per_leaf.values() for e in v]
    global_area = _bbox_area(all_pts)
    summed = sum(_bbox_area([(e.position[0], e.position[1]) for e in ents]) for ents in per_leaf.values())
    assert summed <= global_area * 2.0, \
        f"strm leaves not spatially coherent: summed leaf area {summed:.0f} vs global {global_area:.0f}"


if is_tmp_dir_available():
    def tmp_path(file_name: str) -> Path:
        return tmp_path_with_subdir(file_name, "ymap_partition")

    @assert_logs_no_errors
    def test_import_export_roundtrip():
        """Import stub ymaps, export, verify output matches originals (stable parent_index)."""
        _import_ymaps(
            "test_partition_lod.ymap.xml",
            "test_partition_strm.ymap.xml",
            "test_partition_long.ymap.xml",
        )

        map_group = _last_map_group()
        assert len(map_group.maps) == 3
        # All should be NONE (manual)
        for m in map_group.maps:
            assert m.partition_mode == MapPartitionMode.NONE.name
        # A complete import must not lock any container
        assert not any(m.incomplete_lod_hierarchy_lock for m in map_group.maps)

        out_dir = tmp_path("roundtrip")
        out_dir.mkdir(parents=True, exist_ok=True)
        _export_map_group(map_group, out_dir)

        # Verify each file matches original
        for name in ("test_partition_lod", "test_partition_strm", "test_partition_long"):
            exported = out_dir / f"{name}.ymap.xml"
            assert exported.exists(), f"Expected exported file: {exported}"
            orig = _parse_xml(YMAP_ASSETS_DIR / f"{name}.ymap.xml")
            exp = _parse_xml(exported)

            # Check map-level fields
            assert _get_text(exp, "name") == _get_text(orig, "name"), f"{name}: name mismatch"
            assert _get_text(exp, "parent") == _get_text(orig, "parent"), f"{name}: parent mismatch"

            # Check entity count
            orig_entities = orig.findall("./entities/Item")
            exp_entities = exp.findall("./entities/Item")
            assert len(exp_entities) == len(orig_entities), \
                f"{name}: entity count {len(exp_entities)} != {len(orig_entities)}"

            # Check parentIndex stability
            for i, (oe, ee) in enumerate(zip(orig_entities, exp_entities)):
                assert _get_value(ee, "parentIndex") == _get_value(oe, "parentIndex"), \
                    f"{name} entity #{i}: parentIndex mismatch"
                assert _get_text(ee, "archetypeName") == _get_text(oe, "archetypeName"), \
                    f"{name} entity #{i}: archetypeName mismatch"

    @assert_logs_no_errors
    def test_cross_map_parent_index():
        """HD entities in child map with LOD parent in parent map get correct parent_index and flags."""
        _import_ymaps(
            "test_partition_lod.ymap.xml",
            "test_partition_strm.ymap.xml",
            "test_partition_long.ymap.xml",
        )

        map_group = _last_map_group()

        out_dir = tmp_path("cross_map")
        out_dir.mkdir(parents=True, exist_ok=True)
        _export_map_group(map_group, out_dir)

        # Check the strm file - its entities should have LOD_IN_PARENT_MAP flag
        strm_xml = _parse_xml(out_dir / "test_partition_strm.ymap.xml")
        strm_entities = strm_xml.findall("./entities/Item")

        for i, entity in enumerate(strm_entities):
            parent_index = int(_get_value(entity, "parentIndex"))
            flags = int(_get_value(entity, "flags"))
            lod_in_parent_map = flags & (1 << 3)  # EntityFlags.LOD_IN_PARENT_MAP

            assert parent_index >= 0, f"strm entity #{i} should have valid parentIndex"
            assert lod_in_parent_map != 0, f"strm entity #{i} should have LOD_IN_PARENT_MAP flag"

    @assert_logs_no_errors
    def test_auto_partition_export():
        """Create AUTO map group, generate partitions, export, verify leaf files."""
        group, logical_uuid = _make_map_group_with_mixed_entities()

        logical = _find_map(group, logical_uuid)
        generate_partitions(group, logical, PartitioningSettings(max_per_chunk=128))

        out_dir = tmp_path("auto_export")
        out_dir.mkdir(parents=True, exist_ok=True)
        bundles = _export_map_group(group, out_dir)

        # Check that leaf files were exported
        exported_names = {b.asset_name for b in bundles}
        assert any("strm" in n for n in exported_names), f"Missing _strm_ export in {exported_names}"
        assert any("long" in n for n in exported_names), f"Missing _long_ export in {exported_names}"
        assert any("critical" in n for n in exported_names), f"Missing _critical_ export in {exported_names}"
        assert any("interior" in n for n in exported_names), f"Missing _interior_ export in {exported_names}"

        # The logical map itself should be exported too (with LOD entity)
        logical_xml_path = out_dir / "test_sector.ymap.xml"
        assert logical_xml_path.exists(), "Logical map data should be exported"
        logical_xml = _parse_xml(logical_xml_path)
        logical_entities = logical_xml.findall("./entities/Item")
        assert len(logical_entities) == 1, "Logical map should contain only the LOD entity"
        assert _get_text(logical_entities[0], "lodLevel") == "LODTYPES_DEPTH_LOD"

        # Check critical leaf has HAS_ENTITIES_CRITICAL content flag (bit 9 = 512)
        crit_files = [p for p in out_dir.iterdir() if "critical" in p.name and p.suffix == ".xml"]
        assert len(crit_files) > 0
        crit_xml = _parse_xml(crit_files[0])
        content_flags = int(_get_value(crit_xml, "contentFlags"))
        assert content_flags & 512, "Critical leaf should have HAS_ENTITIES_CRITICAL flag"

    @assert_logs_no_errors
    def test_auto_partition_export_without_explicit_generate():
        """Exporting an AUTO map with pending items generates partitions automatically."""
        group, logical_uuid = _make_map_group_with_mixed_entities()

        out_dir = tmp_path("auto_export_implicit")
        out_dir.mkdir(parents=True, exist_ok=True)
        bundles = _export_map_group(group, out_dir)

        exported_names = {b.asset_name for b in bundles}
        assert any("strm" in n for n in exported_names), f"Missing _strm_ export in {exported_names}"
        assert any("long" in n for n in exported_names), f"Missing _long_ export in {exported_names}"
        assert any("critical" in n for n in exported_names), f"Missing _critical_ export in {exported_names}"
        assert any("interior" in n for n in exported_names), f"Missing _interior_ export in {exported_names}"

        # Leaves should exist in the document and reference the logical parent
        children = [m for m in group.maps if m.parent_uuid == logical_uuid and m.is_auto_generated]
        assert children, "Export should have generated auto-partitioned leaves"
        for m in children:
            assert m.name.startswith("test_sector"), f"Leaf {m.name!r} not named after its parent"

    @assert_logs_no_errors
    def test_import_edit_export():
        """Import manual maps, add new entity, auto-assign, export, verify."""
        _import_ymaps(
            "test_partition_lod.ymap.xml",
            "test_partition_strm.ymap.xml",
            "test_partition_long.ymap.xml",
        )

        map_group = _last_map_group()

        # Add a new unassigned entity near the strm entities
        new_entity = map_group.new_entity()
        new_entity.archetype_name = "test_new_addition"
        new_entity.lod_level = "HD"
        new_entity.lod_dist = 80
        new_entity.position = (100, 100, 50)
        # map_data_uuid left empty

        auto_assign_unassigned(map_group)
        assert new_entity.map_data_uuid, "New entity should have been assigned a map data"

        # Export should succeed
        out_dir = tmp_path("import_edit")
        out_dir.mkdir(parents=True, exist_ok=True)
        _export_map_group(map_group, out_dir)

        # The new entity should appear in one of the exported files
        found = False
        for xml_file in out_dir.glob("*.ymap.xml"):
            root = _parse_xml(xml_file)
            for entity in root.findall("./entities/Item"):
                if _get_text(entity, "archetypeName") == "test_new_addition":
                    found = True
                    break
            if found:
                break
        assert found, "New entity should appear in exported files"
