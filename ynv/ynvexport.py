import bpy
from bpy.types import (
    Object
)
from mathutils import Vector
import math
from ..shared.math import wrap_angle
from typing import Optional
from ..cwxml.navmesh import (
    NavMesh,
    NavCoverPoint,
    NavLink,
    NavPolygon,
)
from ..sollumz_properties import SollumType
from ..tools.utils import (
    get_max_vector_list,
    get_min_vector_list,
)
from ..tools.blenderhelper import (
    get_evaluated_obj,
)
from .navmesh import (
    navmesh_is_valid,
    navmesh_is_standalone,
    navmesh_is_map,
    navmesh_get_grid_cell,
    navmesh_grid_get_cell_bounds,
    navmesh_grid_get_cell_index,
    navmesh_grid_get_cell_neighbors,
    navmesh_grid_get_cell_filename,
    navmesh_compute_edge_adjacency,
    navmesh_poly_get_adjacent_polys_local,
    NAVMESH_STANDALONE_CELL_INDEX,
    NAVMESH_ADJACENCY_INDEX_NONE,
)
from .navmesh_attributes import NavMeshAttr
from .properties import NavLinkType

from .. import logger


def export_ynv(navmesh_obj: Object, filepath: str) -> bool:
    assert navmesh_is_valid(navmesh_obj)

    navmesh_xml = navmesh_from_object(navmesh_obj)
    if navmesh_xml is not None:
        navmesh_xml.write_xml(filepath)
        return True
    else:
        return False


def navmesh_from_object(navmesh_obj: Object) -> Optional[NavMesh]:
    """Create a ``NavMesh`` cwxml object."""

    is_standalone = navmesh_is_standalone(navmesh_obj)

    bbmin = get_min_vector_list(navmesh_obj.bound_box)
    bbmax = get_max_vector_list(navmesh_obj.bound_box)

    navmesh_xml = NavMesh()
    if is_standalone:
        navmesh_xml.bb_min = bbmin
        navmesh_xml.bb_max = bbmax
        navmesh_xml.bb_size = bbmax - bbmin
        navmesh_xml.area_id = NAVMESH_STANDALONE_CELL_INDEX
    else:
        # neighbors = locate_neighbors_in_scene(navmesh_obj)
        # if neighbors is None:
        #     return None
        cell_x, cell_y = navmesh_get_grid_cell(navmesh_obj)
        cell_min, cell_max = navmesh_grid_get_cell_bounds(cell_x, cell_y)
        cell_min.z = bbmin.z
        cell_max.z = bbmax.z
        navmesh_xml.bb_min = cell_min
        navmesh_xml.bb_max = cell_max
        navmesh_xml.bb_size = cell_max - cell_min
        navmesh_xml.area_id = navmesh_grid_get_cell_index(cell_x, cell_y)

    navmesh_xml.polygons, has_water, is_dlc = polygons_from_object(navmesh_obj)

    links_obj = None
    cover_points_obj = None
    for child_obj in navmesh_obj.children:
        if child_obj.sollum_type == SollumType.NAVMESH_LINK_GROUP:
            links_obj = child_obj
        elif child_obj.sollum_type == SollumType.NAVMESH_COVER_POINT_GROUP:
            cover_points_obj = child_obj

    if links_obj is not None:
        for link_obj in links_obj.children:
            if link_obj.sollum_type != SollumType.NAVMESH_LINK:
                continue

            link_xml = link_from_object(link_obj)
            if link_xml is not None:
                navmesh_xml.links.append(link_xml)

    if cover_points_obj is not None:
        for cover_point_obj in cover_points_obj.children:
            if cover_point_obj.sollum_type != SollumType.NAVMESH_COVER_POINT:
                continue

            navmesh_xml.cover_points.append(cover_point_from_object(cover_point_obj))

    has_links = len(navmesh_xml.links) > 0

    content_flags = ["Polygons"]
    if has_links:
        content_flags.append("Portals")
    if is_standalone:
        content_flags.append("Vehicle")
    if has_water:
        content_flags.append("Unknown8")
    if is_dlc:
        content_flags.append("Unknown16")
    navmesh_xml.content_flags = ", ".join(content_flags)

    return navmesh_xml


def locate_neighbors_in_scene(navmesh_obj: Object) -> Optional[dict[tuple[int, int], Object]]:
    cell_to_obj = {navmesh_get_grid_cell(obj): obj for obj in bpy.context.scene.objects if navmesh_is_map(obj)}

    cell_x, cell_y = navmesh_get_grid_cell(navmesh_obj)
    cells = {}
    missing_cells = []
    for ncell_x, ncell_y in navmesh_grid_get_cell_neighbors(cell_x, cell_y):
        ncell = cell_to_obj.get((ncell_x, ncell_y), None)
        if ncell is not None:
            cells[(ncell_x, ncell_y)] = ncell
        else:
            missing_cells.append((ncell_x, ncell_y))

    if len(missing_cells) > 0:
        missing_cells_str = ", ".join(navmesh_grid_get_cell_filename(x, y) for x, y in missing_cells)
        logger.error(
            "Map navmesh export requires neighboring cells. "
            f"The following navmeshes must be imported into the scene: {missing_cells_str}."
        )
        return None
    else:
        return cells


def link_from_object(link_obj: Object) -> Optional[NavLink]:
    assert link_obj.sollum_type == SollumType.NAVMESH_LINK

    link_target_obj = next((c for c in link_obj.children if c.sollum_type == SollumType.NAVMESH_LINK_TARGET), None)
    if link_target_obj is None:
        logger.error(f"Link '{link_obj.name}' has no target object!")
        return None

    link_props = link_obj.sz_nav_link
    link_xml = NavLink()
    link_xml.type = NavLinkType[link_props.link_type].value
    link_xml.angle = wrap_angle(link_props.heading)
    link_xml.position_from = link_obj.location
    link_xml.position_to = link_obj.location + link_target_obj.location
    # TODO: automatically find poly_from/poly_to from position
    link_xml.poly_from = link_props.poly_from
    link_xml.poly_to = link_props.poly_to
    return link_xml


def cover_point_from_object(cover_point_obj: Object) -> NavCoverPoint:
    assert cover_point_obj.sollum_type == SollumType.NAVMESH_COVER_POINT

    cover_point_props = cover_point_obj.sz_nav_cover_point
    # TODO: warn if rotation is not Z-axis aligned
    cover_point_xml = NavCoverPoint()
    cover_point_xml.type = cover_point_props.get_raw_int()
    cover_point_xml.angle = wrap_angle(cover_point_obj.rotation_euler.z - math.pi)
    cover_point_xml.position = Vector(cover_point_obj.location)
    return cover_point_xml


def polygons_from_object(navmesh_obj: Object) -> tuple[list[NavPolygon], bool]:
    assert navmesh_is_valid(navmesh_obj)

    cell_x, cell_y = navmesh_get_grid_cell(navmesh_obj)
    if cell_x < 0 or cell_y < 0:
        cell_index = NAVMESH_STANDALONE_CELL_INDEX
    else:
        # TODO: error if there are vertices outside cell bounds for map navmeshes
        cell_index = navmesh_grid_get_cell_index(cell_x, cell_y)

    polygons_xml = []
    has_water = False
    is_dlc = False
    navmesh_obj_eval = get_evaluated_obj(navmesh_obj)
    mesh = navmesh_obj_eval.to_mesh()
    # Disabled, manually stored in attributes for now
    # mesh_edge_adjacency = navmesh_compute_edge_adjacency(mesh)

    mesh_verts = mesh.vertices
    poly_data0 = mesh.attributes[NavMeshAttr.POLY_DATA_0].data  # TODO: validate that attrs exist
    poly_data1 = mesh.attributes[NavMeshAttr.POLY_DATA_1].data
    poly_data2 = mesh.attributes[NavMeshAttr.POLY_DATA_2].data
    edge_data0 = mesh.attributes[NavMeshAttr.EDGE_DATA_0].data
    edge_data1 = mesh.attributes[NavMeshAttr.EDGE_DATA_1].data
    edge_adjacent_poly = mesh.attributes[NavMeshAttr.EDGE_ADJACENT_POLY].data
    for poly in mesh.polygons:
        poly_verts = [mesh_verts[v].co for v in poly.vertices]

        poly_min = get_min_vector_list(poly_verts)
        poly_max = get_max_vector_list(poly_verts)
        POLY_BBOX_RESOLUTION = 0.25
        poly_min_lowres = Vector(map(int, poly_min / POLY_BBOX_RESOLUTION)) * POLY_BBOX_RESOLUTION
        poly_max_lowres = Vector(map(int, poly_max / POLY_BBOX_RESOLUTION)) * POLY_BBOX_RESOLUTION
        poly_size_lowres = poly_max_lowres - poly_min_lowres

        centroid = poly.center
        compressed_centroid_x = (
            int((centroid.x - poly_min_lowres.x) / poly_size_lowres.x * 256)
            if poly_size_lowres.x != 0.0 else 0
        )
        compressed_centroid_y = (
            int((centroid.y - poly_min_lowres.y) / poly_size_lowres.y * 256)
            if poly_size_lowres.y != 0.0 else 0
        )
        compressed_centroid_x = min(max(compressed_centroid_x, 0), 255)
        compressed_centroid_y = min(max(compressed_centroid_y, 0), 255)

        # adjacent_polys = navmesh_poly_get_adjacent_polys_local(mesh, poly.index, mesh_edge_adjacency)
        # adjacent_polys_with_cell_index = [
        #    (NAVMESH_ADJACENCY_INDEX_NONE, NAVMESH_ADJACENCY_INDEX_NONE)
        #    if poly_idx == NAVMESH_ADJACENCY_INDEX_NONE else (cell_index, poly_idx)
        #    for poly_idx in adjacent_polys
        # ]
        # Not calculating edge adjacency, get it from the attribute
        assert len(poly.edge_keys) == len(poly.vertices)
        edge_flags = []
        adjacent_polys_with_cell_index = []
        for v in poly.vertices:  # Currently every vertex has its own edge, so there should same number of vertices and edges
            edata0 = edge_data0[v].value
            edata00 = edata0 & 0xFFFF
            edata01 = (edata0 >> 16) & 0xFFFF
            edata1 = edge_data1[v].value
            edata10 = edata1 & 0xFFFF
            edata11 = (edata1 >> 16) & 0xFFFF
            eadj_poly = edge_adjacent_poly[v].value
            edge_flags.append((edata00, edata01, edata10, edata11))
            adjacent_polys_with_cell_index.append((eadj_poly & 0xFFFF, (eadj_poly >> 16) & 0xFFFF))

        data0 = poly_data0[poly.index].value
        data1 = poly_data1[poly.index].value
        data2 = poly_data2[poly.index].value
        flag0 = data0 & 0xFF
        flag1 = (data0 >> 8) & 0xFF
        flag2 = data1 & 0xFF
        flag3 = (data1 >> 8) & 0xFF
        flag4 = data2 & 1  # is zero area dlc stitch poly

        if (flag0 & 128) != 0:
            has_water = True

        if (flag4 & 1) != 0:
            is_dlc = True

        if (flag4 & 1) != 0 and len(poly_verts) == 3:
            # Remove the extra vertex that was added to DLC stitch poly so they could form a polygon in the blender mesh
            poly_verts.pop()
            adjacent_polys_with_cell_index.pop()
            edge_flags.pop()

        poly_xml = NavPolygon()
        poly_xml.vertices = poly_verts
        poly_xml.edges = "\n".join(map(lambda e: f"{e[0]}:{e[1]}, {e[0]}:{e[1]}", adjacent_polys_with_cell_index))
        poly_xml.edges_flags = "\n".join(map(lambda e: f"{e[0]}:{e[1]}, {e[2]}:{e[3]}", edge_flags))
        poly_xml.flags = f"{flag0} {flag1} {flag2} {flag3} {compressed_centroid_x} {compressed_centroid_y} {flag4}"
        polygons_xml.append(poly_xml)

    navmesh_obj_eval.to_mesh_clear()

    return polygons_xml, has_water, is_dlc
