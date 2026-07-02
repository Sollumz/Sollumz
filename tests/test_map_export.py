from pathlib import Path
from xml.etree import ElementTree as ET

import bpy
from numpy.testing import assert_allclose

from ..ymap_next.ymapexport import export_ymap
from ..ymap_next.properties.map import get_maps
from ..iecontext import export_context_scope, ExportContext, ExportSettings
from .shared import (
    assert_logs_no_errors,
    log_capture,
    SOLLUMZ_TEST_ASSETS_DIR,
)


YMAP_ASSETS_DIR = SOLLUMZ_TEST_ASSETS_DIR / "cwxml" / "ymap"


def _import_ymaps(*filenames: str):
    """Import ymap files via the operator, all at once so they link correctly."""
    bpy.ops.sollumz.import_ymap(
        directory=str(YMAP_ASSETS_DIR) + "/",
        files=[{"name": f} for f in filenames],
    )


def _export_last_map_group(output_dir: Path):
    """Export the most recently created map group to output_dir."""
    from szio.gta5 import AssetFormat, AssetVersion, AssetTarget

    maps = get_maps()
    assert maps is not None and len(maps.groups) > 0, "No map groups found after import"

    # The last group is the most recently imported one
    map_group = maps.groups[len(maps.groups) - 1]

    settings = ExportSettings(targets=(AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8),))
    with export_context_scope(ExportContext(map_group.name.lower(), settings)):
        bundles = export_ymap(map_group)

    assert bundles, "Export produced no bundles"
    for b in bundles:
        assert b.is_valid(), "Export bundle is not valid"
        b.save(output_dir, settings.targets)


def _last_map_group():
    """Return the most recently created map group (the one from the latest import)."""
    maps = get_maps()
    assert maps is not None and len(maps.groups) > 0, "No map groups found after import"
    return maps.groups[len(maps.groups) - 1]


def _parse_xml(path: Path) -> ET.Element:
    tree = ET.ElementTree()
    tree.parse(str(path))
    return tree.getroot()


def _get_text(el: ET.Element, tag: str) -> str:
    """Get text content of a child element, or empty string."""
    child = el.find(tag)
    if child is None:
        return ""
    return child.text or ""


def _get_value(el: ET.Element, tag: str) -> str:
    """Get the 'value' attribute of a child element."""
    child = el.find(tag)
    if child is None:
        return ""
    return child.attrib.get("value", "")


def _get_vector(el: ET.Element, tag: str) -> tuple[float, float, float]:
    """Get x,y,z attributes from a vector element."""
    child = el.find(tag)
    assert child is not None, f"Missing element: {tag}"
    return (
        float(child.attrib.get("x", "0")),
        float(child.attrib.get("y", "0")),
        float(child.attrib.get("z", "0")),
    )


def _get_vector4(el: ET.Element, tag: str) -> tuple[float, float, float, float]:
    """Get x,y,z,w attributes from a quaternion/vector4 element."""
    child = el.find(tag)
    assert child is not None, f"Missing element: {tag}"
    return (
        float(child.attrib.get("x", "0")),
        float(child.attrib.get("y", "0")),
        float(child.attrib.get("z", "0")),
        float(child.attrib.get("w", "0")),
    )


def _assert_ymap_entities_match(original_path: Path, exported_path: Path, *, rtol: float = 1e-5):
    """Assert that exported YMAP XML entities match the original."""
    orig = _parse_xml(original_path)
    export = _parse_xml(exported_path)

    # Map-level fields
    assert _get_text(export, "name") == _get_text(orig, "name"), "name mismatch"
    assert _get_text(export, "parent") == _get_text(orig, "parent"), "parent mismatch"
    assert _get_value(export, "flags") == _get_value(orig, "flags"), "flags mismatch"
    assert _get_value(export, "contentFlags") == _get_value(orig, "contentFlags"), "contentFlags mismatch"

    # Extents
    assert_allclose(
        _get_vector(export, "streamingExtentsMin"),
        _get_vector(orig, "streamingExtentsMin"),
        rtol=rtol,
        err_msg="streamingExtentsMin mismatch",
    )
    assert_allclose(
        _get_vector(export, "streamingExtentsMax"),
        _get_vector(orig, "streamingExtentsMax"),
        rtol=rtol,
        err_msg="streamingExtentsMax mismatch",
    )
    assert_allclose(
        _get_vector(export, "entitiesExtentsMin"),
        _get_vector(orig, "entitiesExtentsMin"),
        rtol=rtol,
        err_msg="entitiesExtentsMin mismatch",
    )
    assert_allclose(
        _get_vector(export, "entitiesExtentsMax"),
        _get_vector(orig, "entitiesExtentsMax"),
        rtol=rtol,
        err_msg="entitiesExtentsMax mismatch",
    )

    # Entities
    orig_entities = orig.findall("./entities/Item")
    export_entities = export.findall("./entities/Item")
    assert len(export_entities) == len(orig_entities), (
        f"Entity count mismatch: expected {len(orig_entities)}, got {len(export_entities)}"
    )

    for i, (orig_e, export_e) in enumerate(zip(orig_entities, export_entities)):
        prefix = f"Entity #{i}"

        assert _get_text(export_e, "archetypeName") == _get_text(orig_e, "archetypeName"), (
            f"{prefix}: archetypeName mismatch"
        )
        assert _get_value(export_e, "flags") == _get_value(orig_e, "flags"), f"{prefix}: flags mismatch"
        # GUID comparison skipped: stored as FloatProperty, precision loss expected for large values
        assert _get_value(export_e, "parentIndex") == _get_value(orig_e, "parentIndex"), (
            f"{prefix}: parentIndex mismatch"
        )
        assert _get_value(export_e, "lodDist") == _get_value(orig_e, "lodDist"), f"{prefix}: lodDist mismatch"
        assert _get_value(export_e, "childLodDist") == _get_value(orig_e, "childLodDist"), (
            f"{prefix}: childLodDist mismatch"
        )
        assert _get_text(export_e, "lodLevel") == _get_text(orig_e, "lodLevel"), f"{prefix}: lodLevel mismatch"
        assert _get_value(export_e, "numChildren") == _get_value(orig_e, "numChildren"), (
            f"{prefix}: numChildren mismatch"
        )
        assert _get_text(export_e, "priorityLevel") == _get_text(orig_e, "priorityLevel"), (
            f"{prefix}: priorityLevel mismatch"
        )
        assert _get_value(export_e, "ambientOcclusionMultiplier") == _get_value(orig_e, "ambientOcclusionMultiplier"), (
            f"{prefix}: ambientOcclusionMultiplier mismatch"
        )
        assert _get_value(export_e, "artificialAmbientOcclusion") == _get_value(orig_e, "artificialAmbientOcclusion"), (
            f"{prefix}: artificialAmbientOcclusion mismatch"
        )
        assert _get_value(export_e, "tintValue") == _get_value(orig_e, "tintValue"), f"{prefix}: tintValue mismatch"

        assert_allclose(
            _get_vector(export_e, "position"),
            _get_vector(orig_e, "position"),
            rtol=rtol,
            err_msg=f"{prefix}: position mismatch",
        )
        assert_allclose(
            _get_vector4(export_e, "rotation"),
            _get_vector4(orig_e, "rotation"),
            rtol=rtol,
            err_msg=f"{prefix}: rotation mismatch",
        )

        # MLO-specific fields
        orig_type = orig_e.attrib.get("type", "CEntityDef")
        export_type = export_e.attrib.get("type", "CEntityDef")
        assert export_type == orig_type, f"{prefix}: type mismatch ({export_type} != {orig_type})"

        if orig_type == "CMloInstanceDef":
            assert _get_value(export_e, "groupId") == _get_value(orig_e, "groupId"), f"{prefix}: groupId mismatch"
            assert _get_value(export_e, "floorId") == _get_value(orig_e, "floorId"), f"{prefix}: floorId mismatch"
            assert _get_value(export_e, "numExitPortals") == _get_value(orig_e, "numExitPortals"), (
                f"{prefix}: numExitPortals mismatch"
            )
            assert _get_value(export_e, "MLOInstflags") == _get_value(orig_e, "MLOInstflags"), (
                f"{prefix}: MLOInstflags mismatch"
            )


def _assert_ymap_hierarchy_preserved(original_path: Path, exported_path: Path):
    """Assert a locked (incomplete-hierarchy) re-export preserves the LOD hierarchy values and the
    map parent reference exactly as imported.

    Map-level ``flags``/``contentFlags`` are recomputed on export by design (a subset re-export may
    lose e.g. the ``IS_PARENT`` flag), so they are intentionally NOT compared here.
    """
    orig = _parse_xml(original_path)
    export = _parse_xml(exported_path)

    assert _get_text(export, "name") == _get_text(orig, "name"), "name mismatch"
    assert _get_text(export, "parent") == _get_text(orig, "parent"), "parent mismatch"

    orig_entities = orig.findall("./entities/Item")
    export_entities = export.findall("./entities/Item")
    assert len(export_entities) == len(orig_entities), (
        f"Entity count mismatch: expected {len(orig_entities)}, got {len(export_entities)}"
    )

    for i, (orig_e, export_e) in enumerate(zip(orig_entities, export_entities)):
        prefix = f"Entity #{i}"
        assert _get_text(export_e, "archetypeName") == _get_text(orig_e, "archetypeName"), (
            f"{prefix}: archetypeName mismatch"
        )
        # Entity flags carry LOD_IN_PARENT_MAP, which must be preserved verbatim under the lock
        assert _get_value(export_e, "flags") == _get_value(orig_e, "flags"), f"{prefix}: flags mismatch"
        assert _get_value(export_e, "parentIndex") == _get_value(orig_e, "parentIndex"), (
            f"{prefix}: parentIndex mismatch"
        )
        assert _get_value(export_e, "numChildren") == _get_value(orig_e, "numChildren"), (
            f"{prefix}: numChildren mismatch"
        )
        assert _get_text(export_e, "lodLevel") == _get_text(orig_e, "lodLevel"), f"{prefix}: lodLevel mismatch"


def _assert_ymap_cargens_match(original_path: Path, exported_path: Path, *, rtol: float = 1e-4):
    """Assert that exported YMAP XML car generators match the original."""
    orig = _parse_xml(original_path)
    export = _parse_xml(exported_path)

    orig_cargens = orig.findall("./carGenerators/Item")
    export_cargens = export.findall("./carGenerators/Item")
    assert len(export_cargens) == len(orig_cargens), (
        f"CarGen count mismatch: expected {len(orig_cargens)}, got {len(export_cargens)}"
    )

    for i, (orig_g, export_g) in enumerate(zip(orig_cargens, export_cargens)):
        prefix = f"CarGen #{i}"

        assert_allclose(
            _get_vector(export_g, "position"),
            _get_vector(orig_g, "position"),
            rtol=rtol,
            err_msg=f"{prefix}: position mismatch",
        )

        assert_allclose(
            float(_get_value(export_g, "orientX")),
            float(_get_value(orig_g, "orientX")),
            rtol=rtol,
            err_msg=f"{prefix}: orientX mismatch",
        )
        assert_allclose(
            float(_get_value(export_g, "orientY")),
            float(_get_value(orig_g, "orientY")),
            rtol=rtol,
            err_msg=f"{prefix}: orientY mismatch",
        )
        assert_allclose(
            float(_get_value(export_g, "perpendicularLength")),
            float(_get_value(orig_g, "perpendicularLength")),
            rtol=rtol,
            err_msg=f"{prefix}: perpendicularLength mismatch",
        )

        assert _get_text(export_g, "carModel") == _get_text(orig_g, "carModel"), f"{prefix}: carModel mismatch"
        assert _get_value(export_g, "livery") == _get_value(orig_g, "livery"), f"{prefix}: livery mismatch"
        assert int(_get_value(export_g, "flags")) == int(_get_value(orig_g, "flags")), (
            f"{prefix}: flags mismatch (covers both flag bits 0-16 and creation_rule packed in bits 28-31)"
        )
        assert (_get_text(export_g, "popGroup") or "") == (_get_text(orig_g, "popGroup") or ""), (
            f"{prefix}: popGroup mismatch"
        )
        for n in (1, 2, 3, 4):
            tag = f"bodyColorRemap{n}"
            assert _get_value(export_g, tag) == _get_value(orig_g, tag), f"{prefix}: {tag} mismatch"


def _assert_ymap_tcms_match(original_path: Path, exported_path: Path, *, rtol: float = 1e-5):
    """Assert that exported YMAP XML timecycle modifiers match the original."""
    orig = _parse_xml(original_path)
    export = _parse_xml(exported_path)

    orig_tcms = orig.findall("./timeCycleModifiers/Item")
    export_tcms = export.findall("./timeCycleModifiers/Item")
    assert len(export_tcms) == len(orig_tcms), f"TCM count mismatch: expected {len(orig_tcms)}, got {len(export_tcms)}"

    for i, (orig_t, export_t) in enumerate(zip(orig_tcms, export_tcms)):
        prefix = f"TCM #{i}"

        assert _get_text(export_t, "name") == _get_text(orig_t, "name"), f"{prefix}: name mismatch"
        assert_allclose(
            _get_vector(export_t, "minExtents"),
            _get_vector(orig_t, "minExtents"),
            rtol=rtol,
            err_msg=f"{prefix}: minExtents mismatch",
        )
        assert_allclose(
            _get_vector(export_t, "maxExtents"),
            _get_vector(orig_t, "maxExtents"),
            rtol=rtol,
            err_msg=f"{prefix}: maxExtents mismatch",
        )
        assert _get_value(export_t, "percentage") == _get_value(orig_t, "percentage"), f"{prefix}: percentage mismatch"
        assert _get_value(export_t, "range") == _get_value(orig_t, "range"), f"{prefix}: range mismatch"
        assert _get_value(export_t, "startHour") == _get_value(orig_t, "startHour"), f"{prefix}: startHour mismatch"
        assert _get_value(export_t, "endHour") == _get_value(orig_t, "endHour"), f"{prefix}: endHour mismatch"


@assert_logs_no_errors
def test_ymap_export_orphan_hd(tmp_path: Path):
    """Import single ORPHANHD entity map, export, verify XML matches."""
    _import_ymaps("test_orphan_hd.ymap.xml")

    _export_last_map_group(tmp_path)

    exported = tmp_path / "test_orphan_hd.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    _assert_ymap_entities_match(
        YMAP_ASSETS_DIR / "test_orphan_hd.ymap.xml",
        exported,
    )


@assert_logs_no_errors
def test_ymap_export_hd_lod_pair(tmp_path: Path):
    """Import HD+LOD pair, export, verify both XMLs match."""
    _import_ymaps("test_hd_lod_pair.ymap.xml", "test_hd_lod_pair_lod.ymap.xml")

    _export_last_map_group(tmp_path)

    for name in ("test_hd_lod_pair.ymap.xml", "test_hd_lod_pair_lod.ymap.xml"):
        exported = tmp_path / name
        assert exported.exists(), f"Expected exported file: {exported}"
        _assert_ymap_entities_match(
            YMAP_ASSETS_DIR / name,
            exported,
        )


@assert_logs_no_errors
def test_ymap_export_mlo_instance(tmp_path: Path):
    """Import MLO instance + parent, export, verify CMloInstanceDef fields."""
    _import_ymaps("test_mlo.ymap.xml", "test_mlo_parent.ymap.xml")

    _export_last_map_group(tmp_path)

    for name in ("test_mlo.ymap.xml", "test_mlo_parent.ymap.xml"):
        exported = tmp_path / name
        assert exported.exists(), f"Expected exported file: {exported}"
        _assert_ymap_entities_match(
            YMAP_ASSETS_DIR / name,
            exported,
        )


@assert_logs_no_errors
def test_ymap_export_cargens(tmp_path: Path):
    """Import map with cargens, export, verify cargen fields."""
    _import_ymaps("test_cargens.ymap.xml")

    _export_last_map_group(tmp_path)

    exported = tmp_path / "test_cargens.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    _assert_ymap_cargens_match(
        YMAP_ASSETS_DIR / "test_cargens.ymap.xml",
        exported,
    )


@assert_logs_no_errors
def test_ymap_export_tcm(tmp_path: Path):
    """Import map with TCM, export, verify TCM fields."""
    _import_ymaps("test_tcm.ymap.xml")

    _export_last_map_group(tmp_path)

    exported = tmp_path / "test_tcm.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    _assert_ymap_tcms_match(
        YMAP_ASSETS_DIR / "test_tcm.ymap.xml",
        exported,
    )


def _make_map_group_for_extents(name: str):
    """Create a map group with one container and two data-only entities with known positions/lod_dists.

    Returns the group and the container UUID (not a direct reference, because Blender
    CollectionProperty invalidates references when items are added).
    """
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = name

    md = group.new_map()
    md.name = name
    md_uuid = md.uuid

    e1 = group.new_entity()
    e1.archetype_name = "test_box_a"
    e1.lod_level = "HD"
    e1.position = (0.0, 0.0, 0.0)
    e1.lod_dist = 10.0
    e1.map_data_uuid = md_uuid

    e2 = group.new_entity()
    e2.archetype_name = "test_box_b"
    e2.lod_level = "HD"
    e2.position = (100.0, 40.0, 20.0)
    e2.lod_dist = 50.0
    e2.map_data_uuid = md_uuid

    return group, md_uuid


def _find_map(group, uuid):
    for m in group.maps:
        if m.uuid == uuid:
            return m
    return None


@assert_logs_no_errors
def test_ymap_export_computed_extents(tmp_path: Path):
    """Extents of hand-built maps are computed at export and written back to the map data."""
    group, md_uuid = _make_map_group_for_extents("test_computed_extents")

    _export_last_map_group(tmp_path)

    exported = tmp_path / "test_computed_extents.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    xml = _parse_xml(exported)

    # Data-only entities contribute a point AABB at their position, grown by lod_dist for streaming
    expected_entities = ((0.0, 0.0, 0.0), (100.0, 40.0, 20.0))
    expected_streaming = ((-10.0, -10.0, -30.0), (150.0, 90.0, 70.0))
    assert_allclose(_get_vector(xml, "entitiesExtentsMin"), expected_entities[0], atol=1e-5)
    assert_allclose(_get_vector(xml, "entitiesExtentsMax"), expected_entities[1], atol=1e-5)
    assert_allclose(_get_vector(xml, "streamingExtentsMin"), expected_streaming[0], atol=1e-5)
    assert_allclose(_get_vector(xml, "streamingExtentsMax"), expected_streaming[1], atol=1e-5)

    # The computed extents are written back to the map data properties
    md = _find_map(group, md_uuid)
    assert not md.extents_manual
    assert_allclose(tuple(md.entities_extents_min), expected_entities[0], atol=1e-5)
    assert_allclose(tuple(md.entities_extents_max), expected_entities[1], atol=1e-5)
    assert_allclose(tuple(md.streaming_extents_min), expected_streaming[0], atol=1e-5)
    assert_allclose(tuple(md.streaming_extents_max), expected_streaming[1], atol=1e-5)


@assert_logs_no_errors
def test_ymap_update_maps_extents():
    """update_maps_extents (the Calculate Extents operator path) stores computed extents on the containers."""
    from ..ymap_next.extents import update_maps_extents

    group, md_uuid = _make_map_group_for_extents("test_update_extents")

    md = _find_map(group, md_uuid)
    md.extents_manual = True  # update_maps_extents recalculates regardless of the manual flag

    num_updated = update_maps_extents(group, [md_uuid])
    assert num_updated == 1

    md = _find_map(group, md_uuid)
    assert_allclose(tuple(md.entities_extents_min), (0.0, 0.0, 0.0), atol=1e-5)
    assert_allclose(tuple(md.entities_extents_max), (100.0, 40.0, 20.0), atol=1e-5)
    assert_allclose(tuple(md.streaming_extents_min), (-10.0, -10.0, -30.0), atol=1e-5)
    assert_allclose(tuple(md.streaming_extents_max), (150.0, 90.0, 70.0), atol=1e-5)


@assert_logs_no_errors
def test_ymap_export_manual_extents_preserved(tmp_path: Path):
    """Containers with manual extents export the stored values as-is."""
    group, md_uuid = _make_map_group_for_extents("test_manual_extents")

    md = _find_map(group, md_uuid)
    md.extents_manual = True
    md.entities_extents_min = (1.0, 2.0, 3.0)
    md.entities_extents_max = (4.0, 5.0, 6.0)
    md.streaming_extents_min = (-7.0, -8.0, -9.0)
    md.streaming_extents_max = (10.0, 11.0, 12.0)

    _export_last_map_group(tmp_path)

    exported = tmp_path / "test_manual_extents.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    xml = _parse_xml(exported)

    assert_allclose(_get_vector(xml, "entitiesExtentsMin"), (1.0, 2.0, 3.0), atol=1e-5)
    assert_allclose(_get_vector(xml, "entitiesExtentsMax"), (4.0, 5.0, 6.0), atol=1e-5)
    assert_allclose(_get_vector(xml, "streamingExtentsMin"), (-7.0, -8.0, -9.0), atol=1e-5)
    assert_allclose(_get_vector(xml, "streamingExtentsMax"), (10.0, 11.0, 12.0), atol=1e-5)


def _box_occluder_key(item: ET.Element):
    """Identity that is stable across a roundtrip: center is preserved exactly, length/width may swap
    (a box is rotationally ambiguous), height is preserved exactly."""

    def g(tag: str) -> int:
        return int(_get_value(item, tag))

    return (g("iCenterX"), g("iCenterY"), g("iCenterZ"), tuple(sorted((g("iLength"), g("iWidth")))), g("iHeight"))


def _box_occluder_keys(path: Path) -> list:
    return [_box_occluder_key(item) for item in _parse_xml(path).findall("./boxOccluders/Item")]


def _make_occluder_group(name: str, verts, faces):
    """Create a map group with a single occluder object built from the given mesh data."""
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = name
    md = group.new_map()
    md.name = name
    md_uuid = md.uuid

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    bpy.context.scene.collection.objects.link(obj)

    occl = group.new_occluder()
    occl.name = name
    occl.map_data_uuid = md_uuid
    occl.linked_object = obj
    return group


def test_ymap_export_box_occluders(tmp_path: Path):
    """Import box occluders (solid + degenerate planes/walls + a line), export, verify they survive.

    The asset has 7 boxes; the Length=0 & Width=0 line occluder is dropped on import (with a
    warning), the other 6 must round-trip as box occluders (not degrade to model occluders).
    """
    with log_capture() as logs:
        _import_ymaps("test_occluders.ymap.xml")

    assert not logs.errors, "Importing occluders must not log errors"
    assert any("degenerate line" in w for w in logs.warnings), "Expected a warning about the dropped line occluder"

    with log_capture() as export_logs:
        _export_last_map_group(tmp_path)
    assert not export_logs.errors, "Exporting occluders must not log errors"

    exported = tmp_path / "test_occluders.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    root = _parse_xml(exported)

    assert root.findall("./occludeModels/Item") == [], "No box occluder should degrade to a model occluder"

    original = _box_occluder_keys(YMAP_ASSETS_DIR / "test_occluders.ymap.xml")
    surviving = [k for k in original if k[3] != (0, 0)]  # drop the line (both horizontal dims zero)
    assert sorted(_box_occluder_keys(exported)) == sorted(surviving)


@assert_logs_no_errors
def test_ymap_flat_plane_exports_as_box_occluder(tmp_path: Path):
    """A flat rectangular plane that fits the box-occluder constraints exports as a box occluder."""
    import math

    angle = math.radians(20.0)
    cos, sin = math.cos(angle), math.sin(angle)
    # 4 x 2 horizontal rectangle rotated about Z, centered at (10, 20, 5).
    base = ((-2.0, -1.0), (2.0, -1.0), (2.0, 1.0), (-2.0, 1.0))
    verts = [(10.0 + bx * cos - by * sin, 20.0 + bx * sin + by * cos, 5.0) for bx, by in base]
    _make_occluder_group("test_plane_occluder", verts, [(0, 1, 2, 3)])

    _export_last_map_group(tmp_path)

    root = _parse_xml(tmp_path / "test_plane_occluder.ymap.xml")
    boxes = root.findall("./boxOccluders/Item")
    assert len(boxes) == 1, f"Expected the plane to export as 1 box occluder, got {len(boxes)}"
    assert root.findall("./occludeModels/Item") == [], "A box-shaped plane must not become a model occluder"
    assert int(_get_value(boxes[0], "iHeight")) == 0, "A horizontal plane is a height-0 box occluder"
    assert int(_get_value(boxes[0], "iLength")) > 0
    assert int(_get_value(boxes[0], "iWidth")) > 0


@assert_logs_no_errors
def test_ymap_tilted_plane_exports_as_model_occluder(tmp_path: Path):
    """A tilted plane cannot be a box occluder (boxes are upright) and stays a model occluder."""
    import math

    angle = math.radians(30.0)
    cos, sin = math.cos(angle), math.sin(angle)
    # Horizontal rectangle tilted about X -> its normal is neither vertical nor horizontal.
    base = ((-2.0, -1.0), (2.0, -1.0), (2.0, 1.0), (-2.0, 1.0))
    verts = [(30.0 + bx, 30.0 + by * cos, 10.0 + by * sin) for bx, by in base]
    _make_occluder_group("test_tilted_occluder", verts, [(0, 1, 2, 3)])

    _export_last_map_group(tmp_path)

    root = _parse_xml(tmp_path / "test_tilted_occluder.ymap.xml")
    assert root.findall("./boxOccluders/Item") == [], "A tilted plane must not become a box occluder"
    assert len(root.findall("./occludeModels/Item")) == 1, "A tilted plane should export as one model occluder"


def test_ymap_box_shaped_model_stays_model_occluder(tmp_path: Path):
    """A model occluder whose corners happen to form cubes but whose faces don't (open shells) must
    not degrade to box occluders. The asset has 6 real boxes + 1 model that splits into 3 box-shaped
    (8-corner) but topologically-open islands, only the corner positions match a box, not the faces."""
    with log_capture() as logs:
        _import_ymaps("test_occluders_box_shaped_models.ymap.xml")
    assert not logs.errors, "Importing occluders must not log errors"

    with log_capture() as export_logs:
        _export_last_map_group(tmp_path)
    assert not export_logs.errors, "Exporting occluders must not log errors"

    root = _parse_xml(tmp_path / "test_occluders_box_shaped_models.ymap.xml")

    # The box-shaped model islands must survive as a model occluder, not be re-emitted as boxes.
    assert len(root.findall("./occludeModels/Item")) >= 1, "Box-shaped model occluders must stay models"

    # The 6 genuine box occluders must still round-trip as boxes (and nothing extra from the model).
    exported_boxes = _box_occluder_keys(tmp_path / "test_occluders_box_shaped_models.ymap.xml")
    original_boxes = _box_occluder_keys(YMAP_ASSETS_DIR / "test_occluders_box_shaped_models.ymap.xml")
    assert len(exported_boxes) == len(original_boxes), "The genuine box occluders must be preserved"
    assert sorted(exported_boxes) == sorted(original_boxes)


# Incomplete LOD hierarchy
#
# These tests import a subset of a related .ymap set (missing parent and/or child maps, or an
# out-of-range parent index). The affected map data containers must be locked
# (MapData.incomplete_lod_hierarchy_lock) and their LOD hierarchy values preserved as-is on
# re-export, while complete containers in the same group stay unlocked and editable.


def _find_group_map(group, name: str):
    for m in group.maps:
        if m.name == name:
            return m
    raise AssertionError(f"Map data '{name}' not found in group '{group.name}'")


def _find_group_entity(group, archetype_name: str):
    for e in group.entities:
        if e.archetype_name == archetype_name:
            return e
    raise AssertionError(f"Entity '{archetype_name}' not found in group '{group.name}'")


def test_ymap_export_incomplete_missing_parent(tmp_path: Path):
    """Importing an HD map without its parent LOD map locks the container and preserves the hierarchy."""
    # test_partition_strm references <parent>test_partition_lod</parent>, which is not imported.
    with log_capture() as logs:
        _import_ymaps("test_partition_strm.ymap.xml")

    assert logs.warnings, "Expected warnings about the incomplete LOD hierarchy"
    assert not logs.errors, "Importing an incomplete hierarchy must not log errors"

    group = _last_map_group()
    assert group.maps[0].incomplete_lod_hierarchy_lock, "Container with a missing parent map should be locked"
    assert all(e.num_children_missing == 0 for e in group.entities), "HD entities have no missing children"

    _export_last_map_group(tmp_path)

    exported = tmp_path / "test_partition_strm.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    # The original <parent> string and all entity hierarchy values (incl. LOD_IN_PARENT_MAP and the
    # parent indices into the missing LOD map) must round-trip verbatim.
    _assert_ymap_hierarchy_preserved(YMAP_ASSETS_DIR / "test_partition_strm.ymap.xml", exported)


def test_ymap_export_incomplete_missing_children(tmp_path: Path):
    """Importing a LOD map without its HD children locks the container and preserves numChildren."""
    # test_partition_lod entities expect 3 and 1 children; none are imported -> count mismatch.
    with log_capture() as logs:
        _import_ymaps("test_partition_lod.ymap.xml")

    assert logs.warnings, "Expected warnings about the incomplete LOD hierarchy"
    assert not logs.errors, "Importing an incomplete hierarchy must not log errors"

    group = _last_map_group()
    assert group.maps[0].incomplete_lod_hierarchy_lock, "Container with missing children should be locked"
    # No children were imported, so all expected children are missing.
    assert _find_group_entity(group, "test_sector_lod_a").num_children_missing == 3
    assert _find_group_entity(group, "test_sector_lod_b").num_children_missing == 1

    _export_last_map_group(tmp_path)

    exported = tmp_path / "test_partition_lod.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    _assert_ymap_hierarchy_preserved(YMAP_ASSETS_DIR / "test_partition_lod.ymap.xml", exported)


def test_ymap_export_incomplete_bad_parent_index(tmp_path: Path):
    """A map with an out-of-range parentIndex locks the container and preserves the value as-is."""
    with log_capture() as logs:
        _import_ymaps("test_partial_bad_parent_index.ymap.xml")

    assert logs.warnings, "Expected warnings about the incomplete LOD hierarchy"
    assert not logs.errors, "Importing an incomplete hierarchy must not log errors"

    group = _last_map_group()
    assert group.maps[0].incomplete_lod_hierarchy_lock, (
        "Container with an out-of-range parent index should be locked"
    )

    _export_last_map_group(tmp_path)

    exported = tmp_path / "test_partial_bad_parent_index.ymap.xml"
    assert exported.exists(), f"Expected exported file: {exported}"
    # parentIndex stays 5 and the HD entity is NOT coerced to ORPHANHD (parentIndex != -1).
    _assert_ymap_hierarchy_preserved(YMAP_ASSETS_DIR / "test_partial_bad_parent_index.ymap.xml", exported)


@assert_logs_no_errors
def test_ymap_export_complete_hierarchy_not_locked(tmp_path: Path):
    """Regression: a COMPLETE import stays unlocked and recomputes the hierarchy identically."""
    _import_ymaps("test_hd_lod_pair.ymap.xml", "test_hd_lod_pair_lod.ymap.xml")

    group = _last_map_group()
    assert not any(m.incomplete_lod_hierarchy_lock for m in group.maps), "A complete hierarchy must NOT be locked"

    _export_last_map_group(tmp_path)

    for name in ("test_hd_lod_pair.ymap.xml", "test_hd_lod_pair_lod.ymap.xml"):
        exported = tmp_path / name
        assert exported.exists(), f"Expected exported file: {exported}"
        _assert_ymap_entities_match(YMAP_ASSETS_DIR / name, exported)


# Partial subtree imports: test_partition_lod is the root (test_sector_lod_a expects 3 children,
# test_sector_lod_b expects 1), test_partition_strm holds 2 children of lod_a + the child of lod_b,
# test_partition_long holds lod_a's 3rd child. Importing lod+strm WITHOUT long must lock only the
# lod container (one child missing) while the fully-resolved strm container stays editable.


def _import_partial_subtree():
    with log_capture() as logs:
        _import_ymaps("test_partition_lod.ymap.xml", "test_partition_strm.ymap.xml")

    assert logs.warnings, "Expected warnings about the incomplete LOD hierarchy"
    assert not logs.errors, "Importing an incomplete hierarchy must not log errors"

    group = _last_map_group()
    lod_map = _find_group_map(group, "test_partition_lod")
    strm_map = _find_group_map(group, "test_partition_strm")
    assert lod_map.incomplete_lod_hierarchy_lock, "Root container with a missing child map should be locked"
    assert not strm_map.incomplete_lod_hierarchy_lock, "Fully resolved subtree container must NOT be locked"
    return group


def test_ymap_export_incomplete_partial_subtree(tmp_path: Path):
    """Only the container with missing children locks; an unedited re-export matches the originals."""
    group = _import_partial_subtree()

    lod_a = _find_group_entity(group, "test_sector_lod_a")
    lod_b = _find_group_entity(group, "test_sector_lod_b")
    assert lod_a.num_children_missing == 1, "One of lod_a's 3 children lives in the non-imported map"
    assert lod_b.num_children_missing == 0, "lod_b's child was imported"
    for name in ("test_hd_building_a", "test_hd_building_b", "test_hd_building_c"):
        assert _find_group_entity(group, name).parent_uuid, f"{name} should have a resolved parent"

    _export_last_map_group(tmp_path)

    for name in ("test_partition_lod.ymap.xml", "test_partition_strm.ymap.xml"):
        exported = tmp_path / name
        assert exported.exists(), f"Expected exported file: {exported}"
        # lod: numChildren reconstructed as found (via parent_uuid) + missing; strm: parentIndex
        # and LOD_IN_PARENT_MAP recomputed to the original values.
        _assert_ymap_hierarchy_preserved(YMAP_ASSETS_DIR / name, exported)
        _assert_ymap_entities_match(YMAP_ASSETS_DIR / name, exported)


def test_ymap_export_incomplete_partial_subtree_edit_unlocked(tmp_path: Path):
    """Deleting an entity in the unlocked subtree updates the locked parent's exported numChildren."""
    group = _import_partial_subtree()

    building_b_idx = next(i for i, e in enumerate(group.entities) if e.archetype_name == "test_hd_building_b")
    group.entities.remove(building_b_idx)
    from ..ymap_next.map_index import MAP_INDEX

    MAP_INDEX.invalidate_and_rebuild()

    _export_last_map_group(tmp_path)

    lod_root = _parse_xml(tmp_path / "test_partition_lod.ymap.xml")
    lod_entities = lod_root.findall("./entities/Item")
    assert len(lod_entities) == 2, "The locked container's entity list must be unchanged"
    assert _get_value(lod_entities[0], "numChildren") == "2", "lod_a: 1 found child + 1 missing child"
    assert _get_value(lod_entities[0], "parentIndex") == "-1"
    assert _get_value(lod_entities[1], "numChildren") == "1", "lod_b: 1 found child"

    strm_root = _parse_xml(tmp_path / "test_partition_strm.ymap.xml")
    strm_entities = strm_root.findall("./entities/Item")
    assert [_get_text(e, "archetypeName") for e in strm_entities] == ["test_hd_building_a", "test_hd_building_c"]
    assert _get_value(strm_entities[0], "parentIndex") == "0"
    assert _get_value(strm_entities[1], "parentIndex") == "1"


def test_ymap_export_incomplete_partial_subtree_reparent(tmp_path: Path):
    """Reparenting an unlocked entity onto a locked container's entity updates both parents' counts."""
    group = _import_partial_subtree()

    lod_a = _find_group_entity(group, "test_sector_lod_a")
    building_c = _find_group_entity(group, "test_hd_building_c")
    group.set_entity_parent(building_c, lod_a.uuid)
    assert building_c.parent_uuid == lod_a.uuid, "Reparenting an entity in an unlocked container must work"

    _export_last_map_group(tmp_path)

    lod_root = _parse_xml(tmp_path / "test_partition_lod.ymap.xml")
    lod_entities = lod_root.findall("./entities/Item")
    assert _get_value(lod_entities[0], "numChildren") == "4", "lod_a: 3 found children + 1 missing child"
    assert _get_value(lod_entities[1], "numChildren") == "0", "lod_b: its child was reparented away"

    strm_root = _parse_xml(tmp_path / "test_partition_strm.ymap.xml")
    strm_entities = strm_root.findall("./entities/Item")
    assert [_get_value(e, "parentIndex") for e in strm_entities] == ["0", "0", "0"]


def test_ymap_incomplete_locked_container_edits_blocked():
    """Edits that would break a locked container's frozen entity list must be no-ops."""
    group = _import_partial_subtree()

    lod_map = _find_group_map(group, "test_partition_lod")
    lod_a = _find_group_entity(group, "test_sector_lod_a")
    lod_b = _find_group_entity(group, "test_sector_lod_b")
    building_a = _find_group_entity(group, "test_hd_building_a")

    # Reparenting an entity in a locked container is a no-op
    group.set_entity_parent(lod_a, lod_b.uuid)
    assert not lod_a.parent_uuid
    # ...also through the parent_name property setter (bypasses set_entity_parent)
    lod_a.parent_name = "test_sector_lod_b"
    assert not lod_a.parent_uuid

    # Moving an entity into or out of a locked container is a no-op
    strm_map_uuid = building_a.map_data_uuid
    building_a.map_data_name = "test_partition_lod"
    assert building_a.map_data_uuid == strm_map_uuid, "Cannot move an entity INTO a locked container"
    lod_map_uuid = lod_a.map_data_uuid
    lod_a.map_data_name = "test_partition_strm"
    assert lod_a.map_data_uuid == lod_map_uuid, "Cannot move an entity OUT of a locked container"

    # Re-linking a locked container to another parent is a no-op
    lod_map.parent_name = "test_partition_strm"
    assert not lod_map.parent_uuid


def test_ymap_incomplete_unlock_recomputes_but_keeps_missing_children(tmp_path: Path):
    """Unlocking a container re-enables editing; missing children count is lost and not included in numChildren."""
    group = _import_partial_subtree()

    lod_map = _find_group_map(group, "test_partition_lod")
    lod_map.incomplete_lod_hierarchy_lock = False

    _export_last_map_group(tmp_path)

    lod_root = _parse_xml(tmp_path / "test_partition_lod.ymap.xml")
    lod_entities = lod_root.findall("./entities/Item")
    assert _get_value(lod_entities[0], "numChildren") == "2", "lod_a: 2 found children, lost the 1 missing child"
    assert _get_value(lod_entities[1], "numChildren") == "1"

    # Editing the previously locked container's entities is possible again
    lod_a = _find_group_entity(group, "test_sector_lod_a")
    lod_b = _find_group_entity(group, "test_sector_lod_b")
    group.set_entity_parent(lod_a, lod_b.uuid)
    assert lod_a.parent_uuid == lod_b.uuid
