import numpy as np
import pytest

from ..ymap_next.occluders.box import (
    recover_box_occluder,
    box_island_is_valid,
    box_occluder_world_geometry,
    box_occluder_local_geometry,
    _unique_positions,
)


def _assert_geometry_equal(a, b, atol=1e-3):
    """Vertex sets equal (order-independent), so the harmless length/width + 90 deg relabel passes."""
    assert a.shape == b.shape
    d = np.linalg.norm(a[:, None, :] - b[None, :, :], axis=2)
    assert d.min(axis=1).max() < atol
    assert d.min(axis=0).max() < atol


def _assert_box_roundtrips(center, size, angle_deg, expect_verts):
    import math

    cos, sin = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    verts, _ = box_occluder_world_geometry(center, size, cos, sin)
    vcount = len(verts)
    assert vcount == expect_verts
    rec = recover_box_occluder(verts)
    assert rec is not None, f"box {size} @ {angle_deg} deg was not recognized"
    rcenter, rsize, rcos, rsin = rec
    rebuilt, _ = box_occluder_world_geometry(rcenter, rsize, rcos, rsin)
    _assert_geometry_equal(verts, rebuilt)
    return rec


@pytest.mark.parametrize("angle", [0, 17, 30, 45, 90, 123, 270])
def test_box_solid_box_roundtrips(angle):
    _assert_box_roundtrips((10.0, 20.0, 5.0), (4.0, 2.0, 3.0), angle, expect_verts=8)


def test_box_square_solid_box_roundtrips():
    _assert_box_roundtrips((0.0, 0.0, 0.0), (2.0, 2.0, 2.0), 30, expect_verts=8)


@pytest.mark.parametrize("angle", [0, 20, 75, 200])
def test_box_horizontal_plane_roundtrips(angle):
    _, rsize, _, _ = _assert_box_roundtrips((3.0, -7.0, 1.0), (4.0, 2.0, 0.0), angle, expect_verts=4)
    assert rsize[2] == 0.0  # height stays zero


@pytest.mark.parametrize("angle", [0, 25, 110])
def test_box_vertical_plane_roundtrips(angle):
    _, rsize, _, _ = _assert_box_roundtrips((1.0, 2.0, 9.0), (5.0, 0.0, 3.0), angle, expect_verts=4)
    assert 0.0 in (rsize[0], rsize[1])  # exactly one horizontal dim is zero
    assert rsize[2] != 0.0


@pytest.mark.parametrize("angle", [0, 25, 110])
def test_length_zero_wall_roundtrips(angle):
    # A Length=0 wall comes back as a Width=0 wall, geometry is preserved.
    _, rsize, _, _ = _assert_box_roundtrips((1.0, 2.0, 9.0), (0.0, 5.0, 3.0), angle, expect_verts=4)
    assert 0.0 in (rsize[0], rsize[1])
    assert rsize[2] != 0.0


def test_box_reject_tilted_plane():
    # Horizontal rectangle tilted 30 deg about X -> normal is neither vertical nor horizontal.
    import math

    base = np.array([[-2, -1, 0], [2, -1, 0], [2, 1, 0], [-2, 1, 0]], dtype=np.float32)
    a = math.radians(30)
    rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]], dtype=np.float32)
    tilted = base @ rx.T + np.array([5.0, 5.0, 5.0], dtype=np.float32)
    assert recover_box_occluder(tilted) is None


def test_box_reject_non_rectangle_quad():
    # A non-right-angle parallelogram (sheared) is not a box occluder.
    quad = np.array([[0, 0, 0], [4, 0, 0], [5, 2, 0], [1, 2, 0]], dtype=np.float32)
    assert recover_box_occluder(quad) is None


def test_box_reject_triangle():
    tri = np.array([[0, 0, 0], [1, 0, 0], [0, 1, 0]], dtype=np.float32)
    assert recover_box_occluder(tri) is None


@pytest.mark.parametrize("size", [(0.0, 0.0, 3.0), (0.0, 0.0, 0.0), (5.0, 0.0, 0.0)])
def test_box_line_and_point_generate_no_geometry(size):
    # >=2 zero dimensions for a line or point
    verts, faces = box_occluder_local_geometry(size)
    assert len(verts) == 0
    assert len(faces) == 0

    verts, faces = box_occluder_world_geometry((0.0, 0.0, 0.0), size, 1.0, 0.0)
    assert len(verts) == 0
    assert len(faces) == 0


def test_box_horizontal_plane_with_subtol_noise():
    import math

    verts, _ = box_occluder_world_geometry((0.0, 0.0, 0.0), (6.0, 4.0, 0.0), math.cos(0.3), math.sin(0.3))
    verts = verts.copy()
    verts[:, 2] += np.array([1e-5, -1e-5, 1e-5, -1e-5], dtype=np.float32)  # well under occluder_tol
    rec = recover_box_occluder(verts)
    assert rec is not None
    assert rec[1][2] == 0.0  # recovered as a flat (height 0) box


def test_unique_positions_collapses_coincident():
    verts = np.array([[0, 0, 0], [0, 0, 0], [1, 0, 0], [1, 0, 0]], dtype=np.float32)
    assert len(_unique_positions(verts)) == 2


def _triangulate_quads(quads, diagonal=0):
    """Split each quad ``(a, b, c, d)`` into two triangles along a diagonal."""
    tris = []
    for q in quads:
        a, b, c, d = (int(x) for x in q)
        if diagonal == 0:
            tris += [(a, b, c), (a, c, d)]  # diagonal a-c
        else:
            tris += [(a, b, d), (b, c, d)]  # diagonal b-d
    return np.array(tris, dtype=np.int32)


def _box_island(center, size, angle_deg):
    import math

    cos, sin = math.cos(math.radians(angle_deg)), math.sin(math.radians(angle_deg))
    verts, quads = box_occluder_world_geometry(center, size, cos, sin)
    box = recover_box_occluder(verts)
    assert box is not None
    return verts, quads, box


@pytest.mark.parametrize("diagonal", [0, 1])
def test_box_island_valid_solid_box(diagonal):
    verts, quads, box = _box_island((10.0, 20.0, 5.0), (4.0, 2.0, 3.0), 30)
    assert box_island_is_valid(verts, _triangulate_quads(quads, diagonal), box)


@pytest.mark.parametrize("diagonal", [0, 1])
def test_box_island_valid_flat_plane(diagonal):
    verts, quads, box = _box_island((3.0, -7.0, 1.0), (4.0, 2.0, 0.0), 20)
    assert box_island_is_valid(verts, _triangulate_quads(quads, diagonal), box)


@pytest.mark.parametrize("diagonal", [0, 1])
def test_box_island_valid_vertical_wall(diagonal):
    verts, quads, box = _box_island((1.0, 2.0, 9.0), (5.0, 0.0, 3.0), 25)
    assert box_island_is_valid(verts, _triangulate_quads(quads, diagonal), box)


def test_box_island_reject_side_split():
    # 8 perfect cuboid corners, but one face is split along a side (b-c) instead of a diagonal: the two
    # triangles overlap on half the face and leave the other half uncovered -> not a box surface.
    verts, quads, box = _box_island((10.0, 20.0, 5.0), (4.0, 2.0, 3.0), 30)
    tris = []
    for i, q in enumerate(quads):
        a, b, c, d = (int(x) for x in q)
        tris += [(a, b, c), (b, c, d)] if i == 0 else [(a, b, c), (a, c, d)]
    assert recover_box_occluder(verts) is not None  # positions still pass the loose check
    assert not box_island_is_valid(verts, np.array(tris, dtype=np.int32), box)


def test_box_island_reject_open_box():
    # An open shell: one face has no triangles. Corner positions still form a cuboid.
    verts, quads, box = _box_island((10.0, 20.0, 5.0), (4.0, 2.0, 3.0), 30)
    tris = _triangulate_quads(quads[1:])  # drop one face
    assert not box_island_is_valid(verts, tris, box)


def test_box_island_reject_interior_triangle():
    # One face's split is replaced by triangles that cut across the cube interior (each mixes the
    # bottom z=- corners with the far +++ corner 6), so they belong to no single face.
    verts, quads, box = _box_island((10.0, 20.0, 5.0), (4.0, 2.0, 3.0), 30)
    tris = [(0, 1, 6), (0, 6, 3)]  # both span the interior, on no cube face
    for q in quads[1:]:
        a, b, c, d = (int(x) for x in q)
        tris += [(a, b, c), (a, c, d)]
    assert not box_island_is_valid(verts, np.array(tris, dtype=np.int32), box)


def test_box_island_reject_plane_side_split():
    # A flat rectangle whose two triangles share a side instead of the diagonal.
    verts, quads, box = _box_island((3.0, -7.0, 1.0), (4.0, 2.0, 0.0), 20)
    a, b, c, d = (int(x) for x in quads[0])
    tris = np.array([(a, b, c), (b, c, d)], dtype=np.int32)
    assert not box_island_is_valid(verts, tris, box)
