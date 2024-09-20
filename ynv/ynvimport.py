import bpy
from bpy.types import (
    Object,
    Mesh
)
import os
import math
import numpy as np
from ..tools.meshhelper import create_box
from ..cwxml.navmesh import YNV, NavCoverPoint, NavPolygon
from ..sollumz_properties import SollumType
from .navmesh_attributes import NavMeshAttr, mesh_add_navmesh_attribute
from typing import Sequence


def cover_points_to_obj(points: Sequence[NavCoverPoint]) -> Object:
    pobj = bpy.data.objects.new("Cover Points", None)
    pobj.empty_display_size = 0

    for idx, point in enumerate(points):
        obj = bpy.data.objects.new(f"Cover Point {idx}", None)
        obj.sollum_type = SollumType.NAVMESH_COVER_POINT
        obj.parent = pobj
        obj.empty_display_size = 0.5
        obj.empty_display_type = "CONE"
        obj.location = point.position
        obj.rotation_euler = (0, 0, math.pi + point.angle)  # flip rotation so the cone display is more intuitive
        obj.lock_rotation = (True, True, False)
        obj.sz_nav_cover_point.point_type = point.type
        bpy.context.collection.objects.link(obj)

    return pobj


def portals_to_obj(portals):
    pobj = bpy.data.objects.new("Portals", None)
    pobj.empty_display_size = 0

    for idx, portal in enumerate(portals):
        frommesh = bpy.data.meshes.new("from")
        create_box(frommesh, 0.5)
        fromobj = bpy.data.objects.new("from", frommesh)
        fromobj.location = portal.position_from
        tomesh = bpy.data.meshes.new("to")
        create_box(tomesh, 0.5)
        toobj = bpy.data.objects.new("to", tomesh)
        toobj.location = portal.position_to
        obj = bpy.data.objects.new(f"Portal {idx}", None)
        obj.sollum_type = SollumType.NAVMESH_PORTAL
        fromobj.parent = obj
        toobj.parent = obj
        obj.parent = pobj
        bpy.context.collection.objects.link(fromobj)
        bpy.context.collection.objects.link(toobj)
        bpy.context.collection.objects.link(obj)

    return pobj


def polygons_to_mesh(name: str, polygons: Sequence[NavPolygon]) -> Mesh:
    vert_to_idx = {}
    vertices = []
    faces = []
    flag_values = np.empty((len(polygons), len(NavMeshAttr)), dtype=np.int32)
    for poly_index, poly in enumerate(polygons):
        face_indices = []
        for vert in poly.vertices:
            vert.freeze()
            idx = vert_to_idx.get(vert, None)
            if idx is None:
                idx = len(vertices)
                vert_to_idx[vert] = idx
                vertices.append(vert)
            face_indices.append(idx)

        faces.append(face_indices)

        flags = tuple(map(int, poly.flags.split(" ")))[:4]
        flag_values[poly_index, :] = flags

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices, [], faces)

    for i, attr in enumerate(NavMeshAttr):
        mesh_add_navmesh_attribute(mesh, attr)
        mesh.attributes[attr].data.foreach_set("value", flag_values[:, i].ravel())

    return mesh


def navmesh_to_obj(navmesh, filepath):
    name = os.path.basename(filepath.replace(YNV.file_extension, ""))
    mesh = polygons_to_mesh(name, navmesh.polygons)
    mesh_obj = bpy.data.objects.new(name, mesh)
    mesh_obj.sollum_type = SollumType.NAVMESH
    mesh_obj.empty_display_size = 0
    bpy.context.collection.objects.link(mesh_obj)

    portals_obj = portals_to_obj(navmesh.portals)
    portals_obj.parent = mesh_obj
    bpy.context.collection.objects.link(portals_obj)

    cover_points_obj = cover_points_to_obj(navmesh.cover_points)
    cover_points_obj.parent = mesh_obj
    bpy.context.collection.objects.link(cover_points_obj)


def import_ynv(filepath):
    ynv_xml = YNV.from_xml_file(filepath)
    navmesh_to_obj(ynv_xml, filepath)
