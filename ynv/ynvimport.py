import bpy
from bpy.types import (
    Object,
    Mesh
)
import os
import math
from ..shared.math import wrap_angle
import numpy as np
from ..cwxml.navmesh import (
    YNV,
    NavCoverPoint,
    NavLink,
    NavPolygon,
)
from ..sollumz_properties import SollumType
from .navmesh_attributes import NavMeshAttr, mesh_add_navmesh_attribute
from .properties import NavLinkType
from typing import Sequence


def cover_points_to_obj(points: Sequence[NavCoverPoint]) -> Object:
    pobj = bpy.data.objects.new("Cover Points", None)
    pobj.sollum_type = SollumType.NAVMESH_COVER_POINT_GROUP
    pobj.empty_display_size = 0

    for idx, point in enumerate(points):
        obj = bpy.data.objects.new(f"Cover Point {idx}", None)
        obj.sollum_type = SollumType.NAVMESH_COVER_POINT
        obj.parent = pobj
        obj.empty_display_size = 0.5
        obj.empty_display_type = "CONE"
        obj.location = point.position
        # flip rotation so the cone display is more intuitive
        obj.rotation_euler = (0, 0, wrap_angle(math.pi + point.angle))
        obj.lock_rotation = (True, True, False)
        obj.sz_nav_cover_point.set_raw_int(point.type)
        bpy.context.collection.objects.link(obj)

    return pobj


def links_to_obj(links: Sequence[NavLink]) -> Object:
    pobj = bpy.data.objects.new("Links", None)
    pobj.sollum_type = SollumType.NAVMESH_LINK_GROUP
    pobj.empty_display_size = 0

    for idx, link in enumerate(links):
        from_obj = bpy.data.objects.new(f"Link {idx}", None)
        from_obj.sollum_type = SollumType.NAVMESH_LINK
        from_obj.parent = pobj
        from_obj.empty_display_size = 0.65
        from_obj.empty_display_type = "SPHERE"
        from_obj.location = link.position_from
        from_obj.sz_nav_link.link_type = NavLinkType(link.type).name
        from_obj.sz_nav_link.heading = link.angle
        from_obj.sz_nav_link.poly_from = link.poly_from
        from_obj.sz_nav_link.poly_to = link.poly_to

        to_obj = bpy.data.objects.new(f"Link {idx}.target", None)
        to_obj.sollum_type = SollumType.NAVMESH_LINK_TARGET
        to_obj.parent = from_obj
        to_obj.empty_display_size = 0.45
        to_obj.empty_display_type = "SPHERE"
        to_obj.location = link.position_to - link.position_from

        bpy.context.collection.objects.link(from_obj)
        bpy.context.collection.objects.link(to_obj)

    return pobj


def polygons_to_mesh(name: str, polygons: Sequence[NavPolygon]) -> Mesh:
    vert_to_idx = {}
    vertices = []
    faces = []
    poly_data_attrs = (NavMeshAttr.POLY_DATA_0, NavMeshAttr.POLY_DATA_1)
    poly_data = np.empty((len(polygons), len(poly_data_attrs)), dtype=np.uint16)
    for poly_index, poly in enumerate(polygons):
        face_indices = []
        num_new_vertices = 0
        prev_idx = None
        for vert in poly.vertices:
            vert.freeze()
            idx = vert_to_idx.get(vert, None)
            if prev_idx is not None and idx == prev_idx:
                # In some cases there are edges with the same vertex as start and end, skip them.
                continue

            if idx is None:
                idx = len(vertices)
                vert_to_idx[vert] = idx
                vertices.append(vert)
                num_new_vertices += 1

            face_indices.append(idx)
            prev_idx = idx

        if len(set(face_indices)) <= 2:
            # Skip faces with the less than 3 different vertices.
            # Blender polygons require at least 3 vertices, but navmeshes often have polygons with
            # only 2 vertices (e.g. the zero-area stich polys for DLCs). These should be computed
            # again on export if needed.

            # Roll-back changes in the vertices array
            if num_new_vertices > 0:
                for _ in range(num_new_vertices):
                    new_vert = vertices.pop(-1)
                    del vert_to_idx[new_vert]

            continue

        poly_index_in_mesh = len(faces)
        faces.append(face_indices)

        flags = tuple(map(int, poly.flags.split(" ")))[:4]
        poly_data[poly_index_in_mesh, :] = flags[0] | (flags[1] << 8), flags[2] | (flags[3] << 8)

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)

    for i, attr in enumerate(poly_data_attrs):
        mesh_add_navmesh_attribute(mesh, attr)
        mesh.attributes[attr].data.foreach_set("value", poly_data[:len(faces), i].ravel())

    return mesh


def navmesh_to_obj(navmesh, filepath):
    name = os.path.basename(filepath.replace(YNV.file_extension, ""))
    mesh = polygons_to_mesh(name, navmesh.polygons)
    mesh_obj = bpy.data.objects.new(name, mesh)
    mesh_obj.sollum_type = SollumType.NAVMESH
    mesh_obj.empty_display_size = 0
    bpy.context.collection.objects.link(mesh_obj)

    links_obj = links_to_obj(navmesh.links)
    links_obj.parent = mesh_obj
    bpy.context.collection.objects.link(links_obj)

    cover_points_obj = cover_points_to_obj(navmesh.cover_points)
    cover_points_obj.parent = mesh_obj
    bpy.context.collection.objects.link(cover_points_obj)


def import_ynv(filepath):
    ynv_xml = YNV.from_xml_file(filepath)
    navmesh_to_obj(ynv_xml, filepath)
