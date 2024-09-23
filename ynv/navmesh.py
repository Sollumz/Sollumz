from bpy.types import (
    Object,
    Mesh,
    MeshPolygon,
)
import re
from collections.abc import Iterator
from ..sollumz_properties import SollumType
from mathutils import Vector

_NAVMESH_MAP_NAME_REGEX = re.compile(r"^.*\[(\d+)\]\[(\d+)\].*$")

NAVMESH_GRID_SIZE = 100
NAVMESH_GRID_CELL_SIZE = 150.0
NAVMESH_GRID_BOUNDS_MIN = Vector((-6000.0, -6000.0, 0.0))
NAVMESH_GRID_BOUNDS_MIN.freeze()
NAVMESH_GRID_BOUNDS_MAX = \
    NAVMESH_GRID_BOUNDS_MIN + Vector((NAVMESH_GRID_SIZE, NAVMESH_GRID_SIZE, 0.0)) * NAVMESH_GRID_CELL_SIZE
NAVMESH_GRID_BOUNDS_MAX.freeze()

NAVMESH_SECTORS_PER_GRID_CELL = 3

NAVMESH_STANDALONE_CELL_INDEX = 10000

NAVMESH_ADJACENCY_INDEX_NONE = 0x3FFF

NAVMESH_POLY_SMALL_MAX_AREA = 2.0
NAVMESH_POLY_LARGE_MIN_AREA = 40.0


def navmesh_is_valid(obj: Object) -> bool:
    """Gets whether the object is a navmesh."""
    return obj.sollum_type == SollumType.NAVMESH and obj.type == "MESH"


def navmesh_is_map(obj: Object) -> bool:
    """Gets whether the object is a navmesh placed in the map grid. We identify map navmeshes by their name, checking if
    it contains a '[123][456]' identifier.
    """
    return navmesh_is_valid(obj) and _NAVMESH_MAP_NAME_REGEX.match(obj.name)


def navmesh_is_standalone(obj: Object):
    """Gets whether the object is a standalone navmesh, not in the map grid (i.e. vehicle navmeshes)."""
    return navmesh_is_valid(obj) and not navmesh_is_map(obj)


def navmesh_get_grid_cell(obj: Object) -> tuple[int, int]:
    """Gets the cell coordinates of a map navmesh."""
    if not navmesh_is_valid(obj):
        return -1, -1

    match = _NAVMESH_MAP_NAME_REGEX.match(obj.name)
    if not match:
        return -1, -1

    x = int(match.group(1))
    y = int(match.group(2))
    return x // NAVMESH_SECTORS_PER_GRID_CELL, y // NAVMESH_SECTORS_PER_GRID_CELL


def navmesh_grid_get_cell_filename(x: int, y: int) -> str:
    sx = x * NAVMESH_SECTORS_PER_GRID_CELL
    sy = y * NAVMESH_SECTORS_PER_GRID_CELL
    return f"navmesh[{sx}][{sy}]"


def navmesh_grid_get_cell_bounds(x: int, y: int) -> tuple[Vector, Vector]:
    cell_min = NAVMESH_GRID_BOUNDS_MIN + Vector((x, y, 0.0)) * NAVMESH_GRID_CELL_SIZE
    cell_max = cell_min + Vector((NAVMESH_GRID_CELL_SIZE, NAVMESH_GRID_CELL_SIZE, 0.0))
    return cell_min, cell_max


def navmesh_grid_get_cell_index(x: int, y: int) -> int:
    return y * NAVMESH_GRID_SIZE + x


def navmesh_grid_is_cell_valid(x: int, y: int) -> bool:
    return 0 <= x < NAVMESH_GRID_SIZE and 0 <= y < NAVMESH_GRID_SIZE


def navmesh_grid_get_cell_neighbors(x: int, y: int) -> Iterator[tuple[int, int]]:
    if navmesh_grid_is_cell_valid(x - 1, y):
        yield x - 1, y
    if navmesh_grid_is_cell_valid(x, y - 1):
        yield x, y - 1
    if navmesh_grid_is_cell_valid(x + 1, y):
        yield x + 1, y
    if navmesh_grid_is_cell_valid(x, y + 1):
        yield x, y + 1


def _loop_to_half_edge(mesh: Mesh, loop_idx: int) -> tuple[int, int]:
    loop = mesh.loops[loop_idx]
    edge_verts = mesh.edges[loop.edge_index].vertices
    v0, v1 = edge_verts
    if v0 != loop.vertex_index:
        v1, v0 = edge_verts
    assert v0 == loop.vertex_index, \
        f"Degenerate mesh, failed to get half-edge from loop: {v0=}, {v1=}, {loop_idx=}, {loop.vertex_index=}, {loop.edge_index=}"
    return v0, v1


def navmesh_compute_edge_adjacency(mesh: Mesh) -> tuple[dict[tuple[int, int], int], dict[tuple[int, int], int]]:
    half_edge_to_lhs_poly = {}
    half_edge_to_rhs_poly = {}

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            v0, v1 = _loop_to_half_edge(mesh, loop_idx)

            assert (v0, v1) not in half_edge_to_lhs_poly, \
                f"Degenerate mesh, multiple LHS polygons on half-edge ({v0}, {v1}): {half_edge_to_lhs_poly[(v0, v1)]} and {poly.index}"

            half_edge_to_lhs_poly[(v0, v1)] = poly.index

    for poly in mesh.polygons:
        for loop_idx in poly.loop_indices:
            v0, v1 = _loop_to_half_edge(mesh, loop_idx)

            # The RHS poly of this half-edge is the LHS poly of the half-edge going on the opposite direction
            rhs_poly_idx = half_edge_to_lhs_poly.get((v1, v0), None)
            if rhs_poly_idx is not None:
                assert (v0, v1) not in half_edge_to_rhs_poly, \
                    f"Degenerate mesh, multiple RHS polygons on half-edge ({v0}, {v1}): {half_edge_to_rhs_poly[(v0, v1)]} and {rhs_poly_idx}"
                half_edge_to_rhs_poly[(v0, v1)] = rhs_poly_idx

    return half_edge_to_lhs_poly, half_edge_to_rhs_poly


def navmesh_poly_get_adjacent_polys_local(mesh: Mesh, poly_idx: int, edge_adjacendy: tuple[dict[tuple[int, int], int], dict[tuple[int, int], int]]):
    _, half_edge_to_rhs_poly = edge_adjacendy

    adjacent_polys = []
    poly = mesh.polygons[poly_idx]
    for loop_idx in poly.loop_indices:
        v0, v1 = _loop_to_half_edge(mesh, loop_idx)

        adjacent_poly = half_edge_to_rhs_poly.get((v0, v1), None)
        if adjacent_poly is None:
            adjacent_poly = NAVMESH_ADJACENCY_INDEX_NONE

        adjacent_polys.append(adjacent_poly)

    return adjacent_polys


def navmesh_poly_update_flags(mesh: Mesh, poly_idx: int):
    """"""
    from .navmesh_attributes import mesh_get_navmesh_poly_attributes, mesh_set_navmesh_poly_attributes

    poly = mesh.polygons[poly_idx]
    poly_attrs = mesh_get_navmesh_poly_attributes(mesh, poly_idx)

    area = poly.area
    poly_attrs.is_small = area < NAVMESH_POLY_SMALL_MAX_AREA
    poly_attrs.is_large = area > NAVMESH_POLY_LARGE_MIN_AREA

    mesh_set_navmesh_poly_attributes(mesh, poly_idx, poly_attrs)
