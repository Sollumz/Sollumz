import bpy
from bpy.types import (
    Object
)
from mathutils import Vector
import math
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
    navmesh_get_grid_cell,
    navmesh_grid_get_cell_bounds,
    navmesh_grid_get_cell_index,
    navmesh_compute_edge_adjacency,
    navmesh_poly_get_adjacent_polys_local,
    NAVMESH_STANDALONE_CELL_INDEX,
    NAVMESH_ADJACENCY_INDEX_NONE,
)
from .navmesh_attributes import NavMeshAttr

from .. import logger


def export_ynv(navmesh_obj: Object, filepath: str) -> bool:
    assert navmesh_is_valid(navmesh_obj)

    navmesh_from_object(navmesh_obj).write_xml(filepath)
    return True


def navmesh_from_object(navmesh_obj: Object) -> NavMesh:
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
        cell_x, cell_y = navmesh_get_grid_cell(navmesh_obj)
        cell_min, cell_max = navmesh_grid_get_cell_bounds(cell_x, cell_y)
        cell_min.z = bbmin.z
        cell_max.z = bbmax.z
        navmesh_xml.bb_min = cell_min
        navmesh_xml.bb_max = cell_max
        navmesh_xml.bb_size = cell_max - cell_min
        navmesh_xml.area_id = navmesh_grid_get_cell_index(cell_x, cell_y)

    navmesh_xml.polygons = polygons_from_object(navmesh_obj, navmesh_xml.area_id)

    links_obj = None
    cover_points_obj = None
    for child_obj in navmesh_obj.children:
        if child_obj.sollum_type == SollumType.NAVMESH_LINK_GROUP:
            links_obj = child_obj
        elif child_obj.sollum_type == SollumType.NAVMESH_COVER_POINT_GROUP:
            cover_points_obj = child_obj

    # TODO: navmesh links
    # if links_obj is not None:
    #     for link_obj in links_obj.children:
    #         if link_obj.sollum_type != SollumType.NAVMESH_LINK:
    #             continue
    #
    #         navmesh_xml.links.append(link_from_object(link_obj))

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
    # if has_water:
    #     content_flags.append("Unknown8")
    # if is_dlc:
    #     content_flags.append("Unknown16")
    navmesh_xml.content_flags = ", ".join(content_flags)

    return navmesh_xml


def link_from_object(link_obj: Object) -> NavLink:
    assert link_obj.sollum_type == SollumType.NAVMESH_LINK

    # TODO: link_from_object
    link_xml = NavLink()
    return link_xml


def cover_point_from_object(cover_point_obj: Object) -> NavCoverPoint:
    assert cover_point_obj.sollum_type == SollumType.NAVMESH_COVER_POINT

    cover_point_props = cover_point_obj.sz_nav_cover_point
    # TODO: warn if rotation is not Z-axis aligned
    cover_point_xml = NavCoverPoint()
    cover_point_xml.type = cover_point_props.get_raw_int()
    cover_point_xml.angle = cover_point_obj.rotation_euler.z - math.pi  # TODO: wrap to [0..2pi] range
    cover_point_xml.position = Vector(cover_point_obj.location)
    return cover_point_xml


def polygons_from_object(navmesh_obj: Object, local_cell_index: int) -> list[NavPolygon]:
    assert navmesh_is_valid(navmesh_obj)

    # TODO: error if there are vertices outside cell bounds for map navmeshes

    polygons_xml = []
    navmesh_obj_eval = get_evaluated_obj(navmesh_obj)
    mesh = navmesh_obj_eval.to_mesh()
    mesh_edge_adjacency = navmesh_compute_edge_adjacency(mesh)

    mesh_verts = mesh.vertices
    flags0 = mesh.attributes[NavMeshAttr.FLAG_0].data  # TODO: validate that attrs exist
    flags1 = mesh.attributes[NavMeshAttr.FLAG_1].data
    flags2 = mesh.attributes[NavMeshAttr.FLAG_2].data
    flags3 = mesh.attributes[NavMeshAttr.FLAG_3].data
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

        flag0 = min(max(flags0[poly.index].value, 0), 255)
        flag1 = min(max(flags1[poly.index].value, 0), 255)
        flag2 = min(max(flags2[poly.index].value, 0), 255)
        flag3 = min(max(flags3[poly.index].value, 0), 255)

        poly_xml = NavPolygon()
        poly_xml.vertices = poly_verts

        adjacent_polys = navmesh_poly_get_adjacent_polys_local(mesh, poly, mesh_edge_adjacency)
        adjacent_polys_with_cell_index = [
            (NAVMESH_ADJACENCY_INDEX_NONE, NAVMESH_ADJACENCY_INDEX_NONE)
            if poly_idx == NAVMESH_ADJACENCY_INDEX_NONE else (local_cell_index, poly_idx)
            for poly_idx in adjacent_polys
        ]

        poly_xml.edges = "\n".join(map(lambda e: f"{e[0]}:{e[1]}, {e[0]}:{e[1]}", adjacent_polys_with_cell_index))
        poly_xml.flags = f"{flag0} {flag1} {flag2} {flag3} {compressed_centroid_x} {compressed_centroid_y}"

        polygons_xml.append(poly_xml)

    navmesh_obj_eval.to_mesh_clear()

    return polygons_xml
