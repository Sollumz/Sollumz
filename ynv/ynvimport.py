from ..tools.meshhelper import create_box
from ..cwxml.navmesh import YNV
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
import os
import bpy
from ..tools.blenderhelper import find_bsdf_and_material_output


def points_to_obj(points):
    pobj = bpy.data.objects.new("Points", None)
    pobj.empty_display_size = 0

    for idx, point in enumerate(points):
        mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[SollumType.NAVMESH_POINT])
        obj = bpy.data.objects.new(
            SOLLUMZ_UI_NAMES[SollumType.NAVMESH_POINT] + " " + str(idx), mesh)
        obj.sollum_type = SollumType.NAVMESH_POINT
        obj.parent = pobj

        # properties
        create_box(mesh, 0.5)
        obj.location = point.position
        obj.rotation_euler = (0, 0, point.angle)
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
        obj = bpy.data.objects.new(
            SOLLUMZ_UI_NAMES[SollumType.NAVMESH_PORTAL] + " " + str(idx), tomesh)
        obj.sollum_type = SollumType.NAVMESH_PORTAL
        fromobj.parent = obj
        toobj.parent = obj
        obj.parent = pobj
        bpy.context.collection.objects.link(fromobj)
        bpy.context.collection.objects.link(toobj)
        bpy.context.collection.objects.link(obj)

    return pobj


def get_material(flags, material_cache):
    if flags in material_cache:
        return material_cache[flags]

    mat = bpy.data.materials.new(flags)
    if bpy.app.version < (5, 0, 0):
        mat.use_nodes = True
    r, g, b = 0.0, 0.0, 0.0

    sp = flags.split(" ")
    flags_list = []
    for part in sp:
        flags_list.append(int(part))

    flags0 = flags_list[0]
    if flags0 & 1 > 0:
        r += 0.01             # SmallPoly
    if flags0 & 2 > 0:
        r += 0.01             # LargePoly
    if flags0 & 4 > 0:
        g += 0.25             # IsPavement
    if flags0 & 8 > 0:
        g += 0.02             # IsUnderground
    if flags0 & 64 > 0:
        r += 0.25             # Unused1
    if flags0 & 128 > 0:
        b += 0.25             # Unused2

    flags1 = flags_list[1]
    if flags1 & 64 > 0:
        b += 0.1              # AudioProperties1
    if flags1 & 512 > 0:
        g += 0.1              # AudioProperties2
    if flags1 & 1024 > 0:
        b += 0.03             # AudioProperties3
    if flags1 & 4096 > 0:
        g += 0.75             # AudioProperties4
    if flags1 & 8192 > 0:
        b += 0.75             # Unused3
    if flags1 & 16384 > 0:
        r += 0.2              # NearCarNode
    if flags1 & 32768 > 0:
        b += 0.2              # IsInterior
    if flags1 & 65536 > 0:
        g = 0.2               # IsIsolated

    bsdf, _ = find_bsdf_and_material_output(mat)
    bsdf.inputs[0].default_value = (r, g, b, 0.75)

    # Cache the material before returning it
    material_cache[flags] = mat
    return mat


def polygons_to_obj(polygons):
    material_cache = {}
    mats = []
    vertices = {}
    verts = []
    indices = []
    face = []
    for poly in polygons:
        mats.append(get_material(poly.flags, material_cache))
        maxtcount = len(poly.vertices)
        for vert in poly.vertices:
            vertex = id(vert)
            if vertex in vertices:
                idx = vertices[vertex]
            else:
                idx = len(vertices)
                vertices[vertex] = idx
                verts.append(vert)
            face.append(idx)
            if len(face) == maxtcount:
                indices.append(face)
                face = []

    mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[SollumType.NAVMESH_POLY_MESH])
    mesh.from_pydata(verts, [], indices)
    obj = bpy.data.objects.new(
        SOLLUMZ_UI_NAMES[SollumType.NAVMESH_POLY_MESH], mesh)
    obj.sollum_type = SollumType.NAVMESH_POLY_MESH

    # Ensure materials are unique in the mesh
    used_materials = []
    for mat in mats:
        if mat not in used_materials:
            mesh.materials.append(mat)
            used_materials.append(mat)

    for idx, poly in enumerate(mesh.polygons):
        poly.material_index = used_materials.index(mats[idx])

    return obj


def navmesh_to_obj(navmesh, filepath):
    name = os.path.basename(filepath.replace(YNV.file_extension, ""))
    nobj = bpy.data.objects.new(name, None)
    nobj.sollum_type = SollumType.NAVMESH
    nobj.empty_display_size = 0
    bpy.context.collection.objects.link(nobj)

    nmobj = polygons_to_obj(navmesh.polygons)
    nmobj.parent = nobj
    bpy.context.collection.objects.link(nmobj)

    npobj = portals_to_obj(navmesh.portals)
    npobj.parent = nobj
    bpy.context.collection.objects.link(npobj)

    npobj = points_to_obj(navmesh.points)
    npobj.parent = nobj
    bpy.context.collection.objects.link(npobj)


def import_ynv(filepath):
    ynv_xml = YNV.from_xml_file(filepath)
    navmesh_to_obj(ynv_xml, filepath)
