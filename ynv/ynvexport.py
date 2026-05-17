"""Export a NAVMESH hierarchy to a CodeWalker .ynv.xml file.

Vertices are shared between polygons after import (welded by position),
so Blender's edge-to-face map finds the neighbour for every internal
edge — the 3ds Max ofio plugin's ``reverse_edge_poly`` trick.

Boundary edges (no neighbour inside the current mesh) fall into one of
three buckets:

1. **The neighbour cell is loaded in the scene** (multi-cell export).
   Look the edge up by its two vertex positions in the sibling's
   boundary-edge index — if a match exists, emit
   ``(sibling_area_id, sibling_poly_idx)`` with the *current* polygon
   index. Otherwise the sibling polygon was deleted → emit
   ``ADJACENT_NONE``.

2. **The neighbour cell is NOT loaded.** Keep whatever the EDGE
   attribute stored at import — we have no way to know if the index in
   that file is still valid, so trust it verbatim.

3. **The stored attribute points back at OUR own area_id** (the
   neighbour was once inside this same mesh and got deleted since
   import — the topology recompute above already found no face on the
   other side). Emit ``ADJACENT_NONE``; writing the stale index would
   crash the game.
"""
from typing import Optional

from mathutils import Vector

from .. import logger
from ..sollumz_properties import SollumType
from .cwxml_navmesh import (
    NavPoint,
    NavPolygon,
    NavPortal,
    Navmesh,
    YNV,
)
from .navmesh_attributes import (
    ADJACENT_NONE,
    NavMeshAttr,
    format_edges_str,
    format_flags_str,
    has_navmesh_attributes,
)


# Boundary edges are matched across cells by rounding vertex coordinates
# to this many decimal places before comparing. 3 decimals = 1mm; well
# below CodeWalker's own coordinate precision so two cells that share a
# physical edge end up with the same key.
_EDGE_POS_EPS = 3


def _find_polymesh(navmesh_obj):
    for child in navmesh_obj.children:
        if child.sollum_type == SollumType.NAVMESH_POLY_MESH and child.type == "MESH":
            return child
    return None


def _find_group_with_children_of_type(navmesh_obj, sollum_type):
    for child in navmesh_obj.children:
        for grandchild in child.children:
            if grandchild.sollum_type == sollum_type:
                return child
    return None


def _round_pos(v) -> tuple:
    return (round(float(v[0]), _EDGE_POS_EPS),
            round(float(v[1]), _EDGE_POS_EPS),
            round(float(v[2]), _EDGE_POS_EPS))


def build_edge_positional_index(mesh) -> dict[tuple, int]:
    """Index every **boundary** edge by its rounded XYZ-pair → polygon index.

    Internal edges (shared by two faces of this mesh) are skipped because
    a cross-cell neighbour can only touch one of our faces by definition.
    Skipping them also rules out false matches where an internal edge of
    a sibling happens to coincide in space with our boundary edge.
    """
    edge_users: dict[tuple[int, int], list[int]] = {}
    for face in mesh.polygons:
        n = len(face.vertices)
        for i in range(n):
            v0 = face.vertices[i]
            v1 = face.vertices[(i + 1) % n]
            edge_users.setdefault((min(v0, v1), max(v0, v1)), []).append(face.index)

    pos_index: dict[tuple, int] = {}
    verts = mesh.vertices
    for face in mesh.polygons:
        n = len(face.vertices)
        for i in range(n):
            v0 = face.vertices[i]
            v1 = face.vertices[(i + 1) % n]
            key = (min(v0, v1), max(v0, v1))
            if len(edge_users.get(key, [])) > 1:
                continue
            p0 = _round_pos(verts[v0].co)
            p1 = _round_pos(verts[v1].co)
            pos_key = (p0, p1) if p0 < p1 else (p1, p0)
            pos_index[pos_key] = face.index
    return pos_index


def _polygons_from_mesh(
    mesh,
    area_id: int,
    sibling_indices: Optional[dict[int, dict[tuple, int]]] = None,
) -> list[NavPolygon]:
    if not has_navmesh_attributes(mesh):
        raise ValueError(
            "Navmesh polygon mesh is missing the .navmesh.* attribute layers — "
            "re-import the source .ynv.xml so they get created."
        )

    f0_data = mesh.attributes[NavMeshAttr.POLY_FLAG_0.value].data
    f1_data = mesh.attributes[NavMeshAttr.POLY_FLAG_1.value].data
    f2_data = mesh.attributes[NavMeshAttr.POLY_FLAG_2.value].data
    f3_data = mesh.attributes[NavMeshAttr.POLY_FLAG_3.value].data
    f4_data = mesh.attributes[NavMeshAttr.POLY_FLAG_4.value].data
    cx_data = mesh.attributes[NavMeshAttr.POLY_CENTROID_X.value].data
    cy_data = mesh.attributes[NavMeshAttr.POLY_CENTROID_Y.value].data
    has_f4 = mesh.attributes[NavMeshAttr.POLY_HAS_F4.value].data
    area_data = mesh.attributes[NavMeshAttr.EDGE_ADJACENT_AREA.value].data
    poly_data = mesh.attributes[NavMeshAttr.EDGE_ADJACENT_POLY.value].data

    edge_index_by_pair: dict[tuple[int, int], int] = {}
    for edge in mesh.edges:
        v0, v1 = edge.vertices[0], edge.vertices[1]
        edge_index_by_pair[(min(v0, v1), max(v0, v1))] = edge.index

    edge_to_faces: dict[tuple[int, int], list[int]] = {}
    for face in mesh.polygons:
        n = len(face.vertices)
        for i in range(n):
            v0 = face.vertices[i]
            v1 = face.vertices[(i + 1) % n]
            edge_to_faces.setdefault((min(v0, v1), max(v0, v1)), []).append(face.index)

    out: list[NavPolygon] = []
    for face in mesh.polygons:
        if len(face.vertices) < 3:
            continue

        verts = [Vector(mesh.vertices[v].co) for v in face.vertices]
        f0 = f0_data[face.index].value & 0xFF
        f1 = f1_data[face.index].value & 0xFF
        f2 = f2_data[face.index].value & 0xFF
        f3 = f3_data[face.index].value & 0xFF
        f4 = f4_data[face.index].value & 0xFF
        cx = cx_data[face.index].value & 0xFF
        cy = cy_data[face.index].value & 0xFF
        include_f4 = bool(has_f4[face.index].value)

        edge_list = []
        n = len(face.vertices)
        for i in range(n):
            v0 = face.vertices[i]
            v1 = face.vertices[(i + 1) % n]
            key = (min(v0, v1), max(v0, v1))

            # Internal edge inside this mesh.
            other = [f for f in edge_to_faces.get(key, ()) if f != face.index]
            if other:
                edge_list.append((area_id & 0xFFFF, other[0] & 0xFFFF))
                continue

            edge_idx = edge_index_by_pair.get(key)
            if edge_idx is None:
                edge_list.append((ADJACENT_NONE, ADJACENT_NONE))
                continue

            stored_area = area_data[edge_idx].value & 0xFFFF
            stored_poly = poly_data[edge_idx].value & 0xFFFF

            # Stored neighbour was in OUR own area → it was internal and
            # has been deleted since import. No safe value to write.
            if stored_area == area_id:
                edge_list.append((ADJACENT_NONE, ADJACENT_NONE))
                continue

            # Sibling cell is loaded → trust positional matching for the
            # current (possibly renumbered) polygon index.
            if (sibling_indices
                    and stored_area != ADJACENT_NONE
                    and stored_area in sibling_indices):
                p0 = _round_pos(mesh.vertices[v0].co)
                p1 = _round_pos(mesh.vertices[v1].co)
                pos_key = (p0, p1) if p0 < p1 else (p1, p0)
                new_idx = sibling_indices[stored_area].get(pos_key)
                if new_idx is not None:
                    edge_list.append((stored_area, new_idx & 0xFFFF))
                else:
                    # Sibling cell is loaded but its boundary edge is gone
                    # — its polygon was deleted. Emit "no neighbour".
                    edge_list.append((ADJACENT_NONE, ADJACENT_NONE))
                continue

            # Sibling cell not loaded — keep stored value verbatim.
            edge_list.append((stored_area, stored_poly))

        poly_xml = NavPolygon()
        poly_xml.vertices = verts
        poly_xml.flags = format_flags_str(f0, f1, f2, f3, cx, cy, f4, include_f4=include_f4)
        poly_xml.edges = format_edges_str(edge_list)
        out.append(poly_xml)

    return out


def _portal_from_obj(portal_obj) -> NavPortal:
    props = portal_obj.sz_nav_portal
    from_child = next((c for c in portal_obj.children if c.name.startswith("from")), None)
    to_child = next((c for c in portal_obj.children if c.name.startswith("to")), None)
    pos_from = Vector(from_child.matrix_world.translation) if from_child else Vector(portal_obj.location)
    pos_to = Vector(to_child.matrix_world.translation) if to_child else Vector(portal_obj.location)

    p = NavPortal()
    p.type = int(props.portal_type)
    p.angle = float(props.angle)
    p.position_from = pos_from
    p.position_to = pos_to
    p.poly_from = int(props.poly_from) & 0xFFFF
    p.poly_to = int(props.poly_to) & 0xFFFF
    return p


def _point_from_obj(point_obj) -> NavPoint:
    p = NavPoint()
    p.type = int(point_obj.sz_nav_point.point_type)
    p.angle = float(point_obj.rotation_euler.z)
    p.position = Vector(point_obj.matrix_world.translation)
    return p


def navmesh_from_object(
    navmesh_obj,
    sibling_indices: Optional[dict[int, dict[tuple, int]]] = None,
) -> Optional[Navmesh]:
    if navmesh_obj.sollum_type != SollumType.NAVMESH:
        logger.error(f"'{navmesh_obj.name}' is not a NAVMESH root object.")
        return None

    polymesh = _find_polymesh(navmesh_obj)
    if polymesh is None:
        logger.error(f"'{navmesh_obj.name}' has no NAVMESH_POLY_MESH child.")
        return None

    props = navmesh_obj.sz_navmesh
    area_id = int(props.area_id)

    nav = Navmesh()
    nav.area_id = area_id
    nav.content_flags = props.content_flags or "Polygons"
    bb_min = Vector(props.bb_min)
    bb_max = Vector(props.bb_max)
    nav.bb_min = bb_min
    nav.bb_max = bb_max
    nav.bb_size = bb_max - bb_min

    nav.polygons = _polygons_from_mesh(polymesh.data, area_id, sibling_indices)
    poly_count = len(nav.polygons)

    portals_group = _find_group_with_children_of_type(navmesh_obj, SollumType.NAVMESH_PORTAL)
    if portals_group is not None:
        dropped_portals = 0
        for child in portals_group.children:
            if child.sollum_type != SollumType.NAVMESH_PORTAL:
                continue
            portal = _portal_from_obj(child)
            if portal.poly_from >= poly_count or portal.poly_to >= poly_count:
                dropped_portals += 1
                continue
            nav.portals.append(portal)
        if dropped_portals:
            logger.info(
                f"Dropped {dropped_portals} portal(s) referencing deleted polygons."
            )

    points_group = _find_group_with_children_of_type(navmesh_obj, SollumType.NAVMESH_POINT)
    if points_group is not None:
        for child in points_group.children:
            if child.sollum_type == SollumType.NAVMESH_POINT:
                nav.points.append(_point_from_obj(child))

    return nav


def export_ynv(
    navmesh_obj,
    filepath: str,
    sibling_indices: Optional[dict[int, dict[tuple, int]]] = None,
) -> bool:
    nav = navmesh_from_object(navmesh_obj, sibling_indices=sibling_indices)
    if nav is None:
        return False
    YNV.write_xml(nav, filepath)
    return True
