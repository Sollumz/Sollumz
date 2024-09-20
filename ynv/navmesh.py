from bpy.types import (
    Object
)
import re
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


def navmesh_grid_get_cell_bounds(x: int, y: int) -> tuple[Vector, Vector]:
    cell_min = NAVMESH_GRID_BOUNDS_MIN + Vector((x, y, 0.0)) * NAVMESH_GRID_CELL_SIZE
    cell_max = cell_min + Vector((NAVMESH_GRID_CELL_SIZE, NAVMESH_GRID_CELL_SIZE, 0.0))
    return cell_min, cell_max
