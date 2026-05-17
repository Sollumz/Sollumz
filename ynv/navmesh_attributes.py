"""Per-polygon and per-edge mesh attributes — the single source of truth for
every flag byte.

The polygon's material is just a visual grouping (one material per category)
that lets the user select all polygons of a given kind via the standard
"Select by Material" workflow. The exporter never reads flags off a material
— it always reads them from these attributes.
"""
from enum import Enum

from bpy.types import Mesh


class NavMeshAttr(str, Enum):
    POLY_FLAG_0 = ".navmesh.poly_flag0"
    POLY_FLAG_1 = ".navmesh.poly_flag1"
    POLY_FLAG_2 = ".navmesh.poly_flag2"
    POLY_FLAG_3 = ".navmesh.poly_flag3"
    POLY_FLAG_4 = ".navmesh.poly_flag4"
    POLY_CENTROID_X = ".navmesh.poly_centroid_x"
    POLY_CENTROID_Y = ".navmesh.poly_centroid_y"
    POLY_HAS_F4 = ".navmesh.poly_has_f4"
    EDGE_ADJACENT_AREA = ".navmesh.edge_adjacent_area"
    EDGE_ADJACENT_POLY = ".navmesh.edge_adjacent_poly"

    @property
    def domain(self) -> str:
        return "EDGE" if self.name.startswith("EDGE") else "FACE"


# A 14-bit value of all 1s means "no neighbour" in the CodeWalker format.
ADJACENT_NONE = 16383


# Named (bit_index, label) pairs for each flag byte — used by the UI.
FLAG0_BITS: list[tuple[int, str]] = [
    (0, "Avoid Unk0"),
    (1, "Avoid Unk1"),
    (2, "Is Footpath"),
    (3, "Is Underground"),
    (6, "Is Steep Slope"),
    (7, "Is Water"),
]
FLAG1_BITS: list[tuple[int, str]] = [
    (0, "Underground Unk0"),
    (1, "Underground Unk1"),
    (2, "Underground Unk2"),
    (3, "Underground Unk3"),
    (5, "Has Path Node"),
    (6, "Is Interior"),
    (7, "Interaction Unk"),
]
FLAG2_BITS: list[tuple[int, str]] = [
    (0, "Is Flat Ground"),
    (1, "Is Road"),
    (2, "Is Cell Edge"),
    (3, "Is Train Track"),
    (4, "Is Shallow Water"),
    (5, "Footpath Unk1"),
    (6, "Footpath Unk2"),
    (7, "Footpath Mall"),
]
FLAG3_BITS: list[tuple[int, str]] = [
    (0, "Slope South"),
    (1, "Slope SE"),
    (2, "Slope East"),
    (3, "Slope NE"),
    (4, "Slope North"),
    (5, "Slope NW"),
    (6, "Slope West"),
    (7, "Slope SW"),
]


def ensure_navmesh_attributes(mesh: Mesh) -> None:
    for attr in NavMeshAttr:
        if attr.value not in mesh.attributes:
            mesh.attributes.new(attr.value, "INT", attr.domain)


def has_navmesh_attributes(mesh: Mesh) -> bool:
    return all(attr.value in mesh.attributes for attr in NavMeshAttr)


def parse_flags_str(flags_str: str) -> tuple[int, int, int, int, int, int, int, bool]:
    """Parse ``<Flags>`` text into (f0, f1, f2, f3, cx, cy, f4, had_f4)."""
    nums = [int(p) for p in (flags_str or "").split() if p]
    had_f4 = len(nums) >= 7
    while len(nums) < 7:
        nums.append(0)
    f0, f1, f2, f3, cx, cy, f4 = nums[:7]
    return f0, f1, f2, f3, cx, cy, f4, had_f4


def format_flags_str(f0: int, f1: int, f2: int, f3: int,
                     cx: int, cy: int, f4: int, include_f4: bool) -> str:
    base = f"{f0 & 0xFF} {f1 & 0xFF} {f2 & 0xFF} {f3 & 0xFF} {cx & 0xFF} {cy & 0xFF}"
    if include_f4:
        return base + f" {f4 & 0xFF}"
    return base


def parse_edges_str(edges_str: str) -> list[tuple[int, int]]:
    result = []
    for line in (edges_str or "").strip().split("\n"):
        first = line.strip().split(",", 1)[0].strip()
        if ":" not in first:
            continue
        area_s, poly_s = first.split(":", 1)
        try:
            result.append((int(area_s), int(poly_s)))
        except ValueError:
            continue
    return result


def format_edges_str(edges: list[tuple[int, int]]) -> str:
    return "\n".join(f"{a}:{p}, {a}:{p}" for a, p in edges)
