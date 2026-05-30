import os

import bpy
from mathutils import Vector

from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.meshhelper import create_box
from .cwxml_navmesh import YNV
from .navmesh_attributes import (
    ADJACENT_NONE,
    NavMeshAttr,
    ensure_navmesh_attributes,
    parse_edges_str,
    parse_flags_str,
)
from .navmesh_material import classify_polygon, get_navmesh_material


# Decimal places kept when welding vertices by position.
_WELD_PRECISION = 5


def polygons_to_obj(name: str, polygons) -> bpy.types.Object:
    verts: list[Vector] = []
    vert_index: dict[tuple[float, float, float], int] = {}
    faces: list[list[int]] = []
    face_mats = []
    face_perpoly = []  # (f0, f1, f2, f3, f4, cx, cy, had_f4) per face
    face_edges = []    # source (area, poly) per face corner
    material_cache: dict = {}

    def _vertex_index(v) -> int:
        co = (float(v[0]), float(v[1]), float(v[2]))
        key = (round(co[0], _WELD_PRECISION),
               round(co[1], _WELD_PRECISION),
               round(co[2], _WELD_PRECISION))
        existing = vert_index.get(key)
        if existing is not None:
            return existing
        idx = len(verts)
        verts.append(Vector(co))
        vert_index[key] = idx
        return idx

    for poly in polygons:
        poly_verts = list(poly.vertices)
        if len(poly_verts) < 3:
            continue

        face_idx = [_vertex_index(v) for v in poly_verts]

        # Skip degenerate faces produced by the position weld.
        if len(set(face_idx)) < len(face_idx):
            continue

        faces.append(face_idx)

        f0, f1, f2, f3, cx, cy, f4, had_f4 = parse_flags_str(poly.flags)
        face_mats.append(get_navmesh_material(classify_polygon(f1, f2), material_cache))
        face_perpoly.append((f0, f1, f2, f3, f4, cx, cy, had_f4))

        edges = parse_edges_str(poly.edges)
        if len(edges) < len(poly_verts):
            edges += [(ADJACENT_NONE, ADJACENT_NONE)] * (len(poly_verts) - len(edges))
        else:
            edges = edges[:len(poly_verts)]
        face_edges.append(edges)

    mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[SollumType.NAVMESH_POLY_MESH])
    mesh.from_pydata(verts, [], faces)
    ensure_navmesh_attributes(mesh)

    flag_attrs = (
        mesh.attributes[NavMeshAttr.POLY_FLAG_0.value].data,
        mesh.attributes[NavMeshAttr.POLY_FLAG_1.value].data,
        mesh.attributes[NavMeshAttr.POLY_FLAG_2.value].data,
        mesh.attributes[NavMeshAttr.POLY_FLAG_3.value].data,
        mesh.attributes[NavMeshAttr.POLY_FLAG_4.value].data,
    )
    cx_data = mesh.attributes[NavMeshAttr.POLY_CENTROID_X.value].data
    cy_data = mesh.attributes[NavMeshAttr.POLY_CENTROID_Y.value].data
    has_f4 = mesh.attributes[NavMeshAttr.POLY_HAS_F4.value].data
    for i, (f0, f1, f2, f3, f4, cx, cy, had_f4) in enumerate(face_perpoly):
        flag_attrs[0][i].value = f0
        flag_attrs[1][i].value = f1
        flag_attrs[2][i].value = f2
        flag_attrs[3][i].value = f3
        flag_attrs[4][i].value = f4
        cx_data[i].value = cx
        cy_data[i].value = cy
        has_f4[i].value = 1 if had_f4 else 0

    # Only boundary edges (one face user) need to carry a cross-cell
    # neighbour reference; internal adjacency is recomputed from topology.
    edge_users: dict[tuple[int, int], list[tuple[int, int]]] = {}
    for face_i, face_verts in enumerate(faces):
        n = len(face_verts)
        for corner_i in range(n):
            v0 = face_verts[corner_i]
            v1 = face_verts[(corner_i + 1) % n]
            edge_users.setdefault((min(v0, v1), max(v0, v1)), []).append(
                (face_i, corner_i)
            )

    area_data = mesh.attributes[NavMeshAttr.EDGE_ADJACENT_AREA.value].data
    poly_data = mesh.attributes[NavMeshAttr.EDGE_ADJACENT_POLY.value].data
    for edge in mesh.edges:
        key = (min(edge.vertices[0], edge.vertices[1]),
               max(edge.vertices[0], edge.vertices[1]))
        users = edge_users.get(key, [])
        if len(users) == 1:
            face_i, corner_i = users[0]
            area, poly_idx = face_edges[face_i][corner_i]
        else:
            area, poly_idx = ADJACENT_NONE, ADJACENT_NONE
        area_data[edge.index].value = area
        poly_data[edge.index].value = poly_idx

    used_materials = []
    for mat in face_mats:
        if mat not in used_materials:
            mesh.materials.append(mat)
            used_materials.append(mat)
    for i, m in enumerate(face_mats):
        mesh.polygons[i].material_index = used_materials.index(m)

    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = SollumType.NAVMESH_POLY_MESH
    return obj


def portals_to_obj(portals) -> bpy.types.Object:
    pobj = bpy.data.objects.new("Portals", None)
    pobj.empty_display_size = 0

    for idx, portal in enumerate(portals):
        from_mesh = bpy.data.meshes.new("from")
        create_box(from_mesh, 0.5)
        from_obj = bpy.data.objects.new("from", from_mesh)
        from_obj.location = portal.position_from

        to_mesh = bpy.data.meshes.new("to")
        create_box(to_mesh, 0.5)
        to_obj = bpy.data.objects.new("to", to_mesh)
        to_obj.location = portal.position_to

        portal_obj = bpy.data.objects.new(
            f"{SOLLUMZ_UI_NAMES[SollumType.NAVMESH_PORTAL]} {idx}", None,
        )
        portal_obj.sollum_type = SollumType.NAVMESH_PORTAL
        portal_obj.empty_display_size = 0
        portal_obj.sz_nav_portal.portal_type = int(portal.type) if portal.type is not None else 0
        portal_obj.sz_nav_portal.angle = float(portal.angle) if portal.angle is not None else 0.0
        portal_obj.sz_nav_portal.poly_from = int(portal.poly_from) if portal.poly_from is not None else 0
        portal_obj.sz_nav_portal.poly_to = int(portal.poly_to) if portal.poly_to is not None else 0

        from_obj.parent = portal_obj
        to_obj.parent = portal_obj
        portal_obj.parent = pobj
        bpy.context.collection.objects.link(from_obj)
        bpy.context.collection.objects.link(to_obj)
        bpy.context.collection.objects.link(portal_obj)

    return pobj


def points_to_obj(points) -> bpy.types.Object:
    pobj = bpy.data.objects.new("Points", None)
    pobj.empty_display_size = 0

    for idx, point in enumerate(points):
        mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[SollumType.NAVMESH_POINT])
        create_box(mesh, 0.5)
        obj = bpy.data.objects.new(
            f"{SOLLUMZ_UI_NAMES[SollumType.NAVMESH_POINT]} {idx}", mesh,
        )
        obj.sollum_type = SollumType.NAVMESH_POINT
        obj.location = point.position
        obj.rotation_euler = (0, 0, float(point.angle) if point.angle is not None else 0.0)
        obj.sz_nav_point.point_type = int(point.type) if point.type is not None else 0
        obj.parent = pobj
        bpy.context.collection.objects.link(obj)

    return pobj


def navmesh_to_obj(navmesh, filepath: str) -> bpy.types.Object:
    name = os.path.basename(filepath.replace(YNV.file_extension, ""))

    root = bpy.data.objects.new(name, None)
    root.sollum_type = SollumType.NAVMESH
    root.empty_display_size = 0
    root.sz_navmesh.area_id = max(0, int(navmesh.area_id)) if navmesh.area_id is not None else 0
    root.sz_navmesh.content_flags = navmesh.content_flags or ""
    if navmesh.bb_min is not None:
        root.sz_navmesh.bb_min = (float(navmesh.bb_min[0]),
                                  float(navmesh.bb_min[1]),
                                  float(navmesh.bb_min[2]))
    if navmesh.bb_max is not None:
        root.sz_navmesh.bb_max = (float(navmesh.bb_max[0]),
                                  float(navmesh.bb_max[1]),
                                  float(navmesh.bb_max[2]))
    bpy.context.collection.objects.link(root)

    poly_obj = polygons_to_obj(name + "_polys", navmesh.polygons)
    poly_obj.parent = root
    bpy.context.collection.objects.link(poly_obj)

    portals_obj = portals_to_obj(navmesh.portals)
    portals_obj.parent = root
    bpy.context.collection.objects.link(portals_obj)

    points_obj = points_to_obj(navmesh.points)
    points_obj.parent = root
    bpy.context.collection.objects.link(points_obj)

    return root


def import_ynv(filepath: str):
    ynv_xml = YNV.from_xml_file(filepath)
    return navmesh_to_obj(ynv_xml, filepath)
