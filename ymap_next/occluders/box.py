import numpy as np
from mathutils import Vector
from typing import TypeAlias

# Unit cube corners and quad faces for solid box occluders.
_CUBE_VERTS = np.array(
    [
        [-0.5, -0.5, -0.5],
        [0.5, -0.5, -0.5],
        [0.5, 0.5, -0.5],
        [-0.5, 0.5, -0.5],
        [-0.5, -0.5, 0.5],
        [0.5, -0.5, 0.5],
        [0.5, 0.5, 0.5],
        [-0.5, 0.5, 0.5],
    ],
    dtype=np.float32,
)

_CUBE_FACES = np.array(
    [
        (3, 2, 1, 0),
        (5, 6, 7, 4),
        (1, 5, 4, 0),
        (3, 7, 6, 2),
        (4, 7, 3, 0),
        (2, 6, 5, 1),
    ],
    dtype=np.int32,
)

BoxTransform: TypeAlias = tuple[Vector, Vector, float, float]
"""(center, (length, width, height), cos, sin)"""


def _occluder_tol(extent: float) -> float:
    """Comparison tolerance scaled to an extent."""
    return max(1e-3, extent * 1e-3)


def _unique_positions(verts: np.ndarray, tol: float = 1e-4) -> np.ndarray:
    """Return the distinct spatial positions in `verts`, collapsing near-coincident vertices."""
    keys = np.round(verts / tol).astype(np.int64)
    _, idx = np.unique(keys, axis=0, return_index=True)
    return verts[idx]


def _rectangle_from_4_corners_2d(xy4: np.ndarray, tol: float):
    """Recover ``(length, width, cos, sin)`` from 4 coplanar 2D points iff they form a rectangle,
    else ``None``. ``length``/``width`` are the edge lengths; ``(cos, sin)`` is the first edge's
    direction.
    """
    center = xy4.mean(axis=0)
    local = xy4 - center
    angles = np.arctan2(local[:, 1], local[:, 0])
    corners = local[np.argsort(angles)]  # walk the perimeter in angular order

    e1 = corners[1] - corners[0]
    e2 = corners[2] - corners[1]
    e3 = corners[3] - corners[2]
    e4 = corners[0] - corners[3]

    # Opposite edges antiparallel -> parallelogram.
    if not np.allclose(e1, -e3, atol=tol) or not np.allclose(e2, -e4, atol=tol):
        return None

    length = float(np.linalg.norm(e1))
    width = float(np.linalg.norm(e2))
    if length <= 0.0 or width <= 0.0:
        return None

    # Adjacent edges perpendicular -> rectangle.
    if abs(float(e1 @ e2)) > tol * max(length, width):
        return None

    sin = float(e1[0]) / length
    cos = float(e1[1]) / length
    return length, width, cos, sin


def _split_top_bottom(local: np.ndarray, tol: float, n_each: int) -> tuple[np.ndarray, np.ndarray] | None:
    """Split centered verts `local` into `n_each` upper and `n_each` lower corners that sit
    directly above each other (an upright box's top/bottom faces). Returns the lexsort-aligned
    `(top_xy, bot_xy)` 2D corner arrays, or `None` if the verts don't form that pattern.
    """
    z = local[:, 2]
    top_mask = z > 0.0
    if int(top_mask.sum()) != n_each:
        return None
    bot_mask = ~top_mask
    if not np.all(np.abs(local[top_mask, 2] - z.max()) < tol):
        return None
    if not np.all(np.abs(local[bot_mask, 2] - z.min()) < tol):
        return None
    top_sorted = local[top_mask, :2][np.lexsort(local[top_mask, :2].T)]
    bot_sorted = local[bot_mask, :2][np.lexsort(local[bot_mask, :2].T)]
    if not np.allclose(top_sorted, bot_sorted, atol=tol):  # top corners directly above bottom corners
        return None
    return top_sorted, bot_sorted


def _recover_solid(verts: np.ndarray) -> BoxTransform | None:
    """Recover a solid box from 8 corner positions (returns ``(center, (L, W, H), cos, sin)``)."""
    center = verts.mean(axis=0)
    local = verts - center

    z = local[:, 2]
    height = float(z.max() - z.min())
    if height <= 0.0:
        return None
    tol = _occluder_tol(height)

    split = _split_top_bottom(local, tol, 4)
    if split is None:
        return None
    top_xy, _bot_xy = split

    rect = _rectangle_from_4_corners_2d(top_xy, tol)
    if rect is None:
        return None
    length, width, cos, sin = rect
    return Vector(center), Vector((length, width, height)), cos, sin


def _recover_planar(verts: np.ndarray) -> BoxTransform | None:
    """Recover a flat box from 4 coplanar positions: a horizontal rectangle (`height == 0`) or an
    upright vertical wall (`width == 0`). Tilted/non-rectangular planes return `None` so they stay
    model occluders.
    """
    center = verts.mean(axis=0)
    local = verts - center
    z = local[:, 2]
    zspan = float(z.max() - z.min())
    xy_extent = float(np.linalg.norm(local[:, :2], axis=1).max())
    tol = _occluder_tol(max(zspan, xy_extent))

    # Horizontal rectangle -> height = 0.
    if zspan <= tol:
        rect = _rectangle_from_4_corners_2d(local[:, :2], tol)
        if rect is None:
            return None
        length, width, cos, sin = rect
        return Vector(center), Vector((length, width, 0.0)), cos, sin

    # Vertical wall: 2 verts up, 2 down, with the top pair directly above the bottom pair.
    split = _split_top_bottom(local, tol, 2)
    if split is None:
        return None
    top_xy, _bot_xy = split

    seg = top_xy[1] - top_xy[0]  # horizontal footprint
    horiz_len = float(np.linalg.norm(seg))
    if horiz_len <= tol:  # zero horizontal extent -> a line, not a wall
        return None

    sin = float(seg[0]) / horiz_len
    cos = float(seg[1]) / horiz_len
    return Vector(center), Vector((horiz_len, 0.0, zspan)), cos, sin


def recover_box_occluder(verts: np.ndarray) -> BoxTransform | None:
    """Recover `(center, (length, width, height), cos, sin)` from a mesh island's vertices iff they
    form a Z-rotated cuboid (8 positions) or a flat plane (4 positions), else `None`.
    """
    uniq = _unique_positions(verts)
    n = len(uniq)
    if n == 8:
        return _recover_solid(uniq)
    if n == 4:
        return _recover_planar(uniq)
    return None


def box_island_is_valid(verts: np.ndarray, tris: np.ndarray, box: BoxTransform) -> bool:
    """True iff the mesh island triangles `tris` fill the surface of the recovered `box`, i.e. its faces
    connect like a box, not just its corner positions line up.

    `recover_box_occluder` only inspects positions, so 8 corners that happen to form a cuboid pass
    even when the triangles between them don't form the box's 6 faces (an open shell, a missing face,
    a cross-cut triangulation). This connectivity check rejects those so they stay model occluders.

    Algorithm:
      1. Build the recovered box's reference corners and quad faces.
      2. Match each mesh island vertex to the corner it sits on. Every corner must match exactly one vertex.
      3. Relabel each triangle by its corners and assign it to the one quad that contains them.
      4. Accept only if every quad is split into exactly two triangles meeting along a diagonal.
    """
    center, size, cos, sin = box
    ref_corners, ref_quads = box_occluder_world_geometry(center, size, cos, sin)

    if len(verts) != len(ref_corners):
        return False

    # Mesh each island vertex with its nearest reference corner
    corner_distances = np.linalg.norm(verts[:, None, :] - ref_corners[None, :, :], axis=2)
    nearest_corner = corner_distances.argmin(axis=1)
    if len(np.unique(nearest_corner)) != len(ref_corners):
        return False

    # Describe each quad face by its set of corners and its two diagonals.
    # ref_quads are ordered, so corners (q0, q2) and (q1, q3) are the diagonals.
    quad_corner_sets = [frozenset(int(c) for c in q) for q in ref_quads]
    quad_diagonals = [(frozenset((int(q[0]), int(q[2]))), frozenset((int(q[1]), int(q[3])))) for q in ref_quads]
    quad_triangles = [[] for _ in ref_quads]

    # Assign every triangle to the single quad face whose corners contain it.
    for tri in tris:
        tri_corners = frozenset(int(nearest_corner[i]) for i in tri)
        if len(tri_corners) != 3:
            return False
        owner_quads = [qi for qi, corner_set in enumerate(quad_corner_sets) if tri_corners <= corner_set]
        if len(owner_quads) != 1:  # spans the box interior / belongs to no single face
            return False
        quad_triangles[owner_quads[0]].append(tri_corners)

    # Every quad must be split into exactly two triangles meeting along a diagonal (not a side).
    for quad_idx, face_triangles in enumerate(quad_triangles):
        if len(face_triangles) != 2:
            return False
        shared_corners = face_triangles[0] & face_triangles[1]
        if shared_corners not in quad_diagonals[quad_idx]:
            return False

    return True


def box_occluder_local_geometry(size) -> tuple[np.ndarray, np.ndarray]:
    """Local (pre-rotation/translation) mesh geometry for a box occluder of the given `size`."""
    size = np.array(size, dtype=np.float32)
    x, y, z = size
    x_zero, y_zero, z_zero = x == 0.0, y == 0.0, z == 0.0
    n_zero = int(x_zero) + int(y_zero) + int(z_zero)

    if n_zero == 0:
        return _CUBE_VERTS * size, _CUBE_FACES

    if n_zero == 1:
        hx, hy, hz = size * 0.5
        if z_zero:  # height == 0 -> XY quad
            verts = np.array([[-hx, -hy, 0], [hx, -hy, 0], [hx, hy, 0], [-hx, hy, 0]], dtype=np.float32)
        elif y_zero:  # width == 0 -> XZ quad
            verts = np.array([[-hx, 0, -hz], [hx, 0, -hz], [hx, 0, hz], [-hx, 0, hz]], dtype=np.float32)
        else:  # length == 0 -> YZ quad
            verts = np.array([[0, -hy, -hz], [0, hy, -hz], [0, hy, hz], [0, -hy, hz]], dtype=np.float32)
        return verts, np.array([(0, 1, 2, 3)], dtype=np.int32)

    # >= 2 zero dimensions: box degenerated into a line or point which occludes nothing. Drop it, don't build any geometry
    return np.empty((0, 3), dtype=np.float32), np.empty((0, 4), dtype=np.int32)


def box_occluder_world_geometry(center, size, cos: float, sin: float) -> tuple[np.ndarray, np.ndarray]:
    verts, quads = box_occluder_local_geometry(size)
    if len(verts) == 0:
        return verts, quads

    # Transform to world coordinates
    rot = np.array([[sin, -cos, 0], [cos, sin, 0], [0, 0, 1]], dtype=np.float32)
    verts = verts @ rot.T + np.array(center, dtype=np.float32)

    return verts, quads
