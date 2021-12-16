import bpy
from .properties import CollisionMatFlags
from ..resources.bound import *
from ..sollumz_properties import *
from .collision_materials import create_collision_material_from_index, collisionmats
from ..sollumz_ui import SOLLUMZ_UI_NAMES
from ..tools.meshhelper import *
from ..tools.utils import *
import os
from mathutils import Matrix


def init_poly_obj(poly, sollum_type, materials):
    name = SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    if poly.material_index < len(materials):
        mesh.materials.append(materials[poly.material_index])

    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = sollum_type.value

    return obj


def make_matrix(v1, v2, v3):
    a = v2-v1
    b = v3-v1

    c = a.cross(b)
    if c.magnitude > 0:
        c = c.normalized()
    else:
        raise BaseException("A B C are colinear")

    b2 = c.cross(a).normalized()
    a2 = a.normalized()
    m = Matrix([a2, b2, c]).transposed()
    m = Matrix.Translation(v1) @ m.to_4x4()

    return m


def poly_to_obj(poly, materials, vertices):
    if type(poly) == Box:
        obj = init_poly_obj(poly, SollumType.BOUND_POLY_BOX, materials)

        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]
        v3 = vertices[poly.v3]
        v4 = vertices[poly.v4]
        center = (v1 + v2 + v3 + v4) * 0.25

        # Get edges from the 4 opposing corners of the box
        a1 = ((v3 + v4) - (v1 + v2)) * 0.5
        v2 = v1 + a1
        v3 = v3 - a1
        v4 = v4 - a1

        minedge = Vector((0.0001, 0.0001, 0.0001))
        edge1 = max(v2 - v1, minedge)
        edge2 = max(v3 - v1, minedge)
        edge3 = max((v4 - v1), minedge)

        # Order edges
        s1 = False
        s2 = False
        s3 = False
        if edge2.length > edge1.length:
            t1 = edge1
            edge1 = edge2
            edge2 = t1
            s1 = True
        if edge3.length > edge1.length:
            t1 = edge1
            edge1 = edge3
            edge3 = t1
            s2 = True
        if edge3.length > edge2.length:
            t1 = edge2
            edge2 = edge3
            edge3 = t1
            s3 = True

        # Ensure all edge vectors are perpendicular to each other
        b1 = edge1.normalized()
        b2 = edge2.normalized()
        b3 = b1.cross(b2).normalized()
        b2 = b1.cross(b3).normalized()
        edge2 = b2 * edge2.dot(b2)
        edge3 = b3 * edge3.dot(b3)

        # Unswap edges
        if s3 == True:
            t1 = edge2
            edge2 = edge3
            edge3 = t1
        if s2 == True:
            t1 = edge1
            edge1 = edge3
            edge3 = t1
        if s1 == True:
            t1 = edge1
            edge1 = edge2
            edge2 = t1

        mat = Matrix()
        mat[0] = edge1.x, edge2.x, edge3.x, center.x
        mat[1] = edge1.y, edge2.y, edge3.y, center.y
        mat[2] = edge1.z, edge2.z, edge3.z, center.z

        create_box(obj.data, size=1)
        obj.matrix_basis = mat

        return obj
    elif type(poly) == Sphere:
        sphere = init_poly_obj(poly, SollumType.BOUND_POLY_SPHERE, materials)
        mesh = sphere.data
        create_sphere(mesh, poly.radius)

        sphere.location = vertices[poly.v]

        return sphere
    elif type(poly) == Capsule:
        capsule = init_poly_obj(poly, SollumType.BOUND_POLY_CAPSULE, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]
        length = (v1 - v2).length + (poly.radius * 2)
        rot = get_direction_of_vectors(v1, v2)

        create_capsule(capsule.data, poly.radius, length / 2)

        capsule.location = (v1 + v2) / 2
        capsule.rotation_euler = rot

        return capsule
    elif type(poly) == Cylinder:
        cylinder = init_poly_obj(
            poly, SollumType.BOUND_POLY_CYLINDER, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]

        length = get_distance_of_vectors(v1, v2)
        rot = get_direction_of_vectors(v1, v2)

        cylinder.data = create_cylinder(
            cylinder.data, poly.radius, length, rot_mat=None)

        cylinder.location = (v1 + v2) / 2
        cylinder.rotation_euler = rot

        return cylinder


def mat_to_obj(gmat):
    mat = create_collision_material_from_index(gmat.type)
    mat.sollum_type = MaterialType.COLLISION
    mat.collision_properties.procedural_id = gmat.procedural_id
    mat.collision_properties.room_id = gmat.room_id
    mat.collision_properties.ped_density = gmat.ped_density
    mat.collision_properties.material_color_index = gmat.material_color_index

    # Assign flags
    for flag_name in CollisionMatFlags.__annotations__.keys():
        if f"FLAG_{flag_name.upper()}" in gmat.flags:
            setattr(mat.collision_flags, flag_name, True)

    return mat


def geometry_to_obj(geometry, sollum_type):
    obj = init_bound_obj(geometry, sollum_type)
    mesh = bpy.data.meshes.new(
        SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_TRIANGLE])
    triangle_obj = bpy.data.objects.new(
        SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_TRIANGLE], mesh)
    triangle_obj.sollum_type = SollumType.BOUND_POLY_TRIANGLE

    for gmat in geometry.materials:
        triangle_obj.data.materials.append(mat_to_obj(gmat))

    vertices = []
    faces = []
    tri_materials = []

    for poly in geometry.polygons:
        if type(poly) == Triangle:
            tri_materials.append(poly.material_index)
            face = []
            v1 = geometry.vertices[poly.v1]
            v2 = geometry.vertices[poly.v2]
            v3 = geometry.vertices[poly.v3]
            if not v1 in vertices:
                vertices.append(v1)
                face.append(len(vertices) - 1)
            else:
                face.append(vertices.index(v1))
            if not v2 in vertices:
                vertices.append(v2)
                face.append(len(vertices) - 1)
            else:
                face.append(vertices.index(v2))
            if not v3 in vertices:
                vertices.append(v3)
                face.append(len(vertices) - 1)
            else:
                face.append(vertices.index(v3))
            faces.append(face)
        else:
            poly_obj = poly_to_obj(
                poly, triangle_obj.data.materials, geometry.vertices)
            if poly_obj:
                bpy.context.collection.objects.link(poly_obj)
                poly_obj.parent = obj

    triangle_obj.data.from_pydata(vertices, [], faces)
    bpy.context.collection.objects.link(triangle_obj)
    triangle_obj.parent = obj

    # Apply vertex colors
    mesh = triangle_obj.data
    if(len(geometry.vertex_colors) > 0):
        mesh.vertex_colors.new(name="Vertex Colors")
        color_layer = mesh.vertex_colors[0]
        for i in range(len(color_layer.data)):
            rgba = geometry.vertex_colors[mesh.loops[i].vertex_index]
            r = rgba[0] / 255
            g = rgba[1] / 255
            b = rgba[2] / 255
            a = rgba[3] / 255
            color_layer.data[i].color = [r, g, b, a]

    # Apply triangle materials
    for index, poly in triangle_obj.data.polygons.items():
        if tri_materials[index]:
            poly.material_index = tri_materials[index]

    obj.location += geometry.geometry_center

    return obj


def init_bound_obj(bound, sollum_type):
    obj = None
    name = SOLLUMZ_UI_NAMES[sollum_type]
    if not (sollum_type == SollumType.BOUND_COMPOSITE or sollum_type == SollumType.BOUND_GEOMETRYBVH or sollum_type == SollumType.BOUND_GEOMETRY):
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        mat_index = bound.material_index
        try:
            mat = create_collision_material_from_index(mat_index)
            mesh.materials.append(mat)
        except IndexError:
            print(
                f"Warning: Failed to set materials for {name}. Material index {mat_index} does not exist in collisionmats list.")
    else:
        obj = bpy.data.objects.new(name, None)

    obj.empty_display_size = 0
    obj.sollum_type = sollum_type.value

    obj.bound_properties.procedural_id = bound.procedural_id
    obj.bound_properties.room_id = bound.room_id
    obj.bound_properties.ped_density = bound.ped_density
    obj.bound_properties.poly_flags = bound.poly_flags
    obj.bound_properties.inertia = bound.inertia
    obj.bound_properties.unk_flags = bound.unk_flags
    obj.bound_properties.unk_type = bound.unk_type
    obj.margin = bound.margin
    obj.bound_properties.volume = bound.volume

    # assign obj composite flags
    for prop in dir(obj.composite_flags1):
        for f in bound.composite_flags1:
            if f.lower() == prop:
                setattr(obj.composite_flags1, prop, True)

    for prop in dir(obj.composite_flags2):
        for f in bound.composite_flags2:
            if f.lower() == prop:
                setattr(obj.composite_flags2, prop, True)

    mat = bound.composite_rotation.to_matrix().to_4x4()
    # Set scale
    mat[0][0] = bound.composite_scale.x
    mat[1][1] = bound.composite_scale.y
    mat[2][2] = bound.composite_scale.z
    # Set position
    mat[0][3] = bound.composite_position.x
    mat[1][3] = bound.composite_position.y
    mat[2][3] = bound.composite_position.z

    obj.matrix_world = mat

    bpy.context.collection.objects.link(obj)

    return obj


def bound_to_obj(bound):
    if bound.type == 'Box':
        box = init_bound_obj(bound, SollumType.BOUND_BOX)
        box.bound_dimensions = bound.box_max

        return box
    elif bound.type == 'Sphere':
        sphere = init_bound_obj(bound, SollumType.BOUND_SPHERE)
        sphere.bound_radius = bound.sphere_radius
        # create_sphere(sphere.data, bound.sphere_radius)

        return sphere
    elif bound.type == 'Capsule':
        capsule = init_bound_obj(bound, SollumType.BOUND_CAPSULE)
        bbmin, bbmax = bound.box_min, bound.box_max
        capsule.bound_length = bbmax.z - bbmin.z
        capsule.bound_radius = bound.sphere_radius
        # create_capsule(capsule, bound.sphere_radius, bbmax.z - bbmin.z, True)

        return capsule
    elif bound.type == 'Cylinder':
        cylinder = init_bound_obj(bound, SollumType.BOUND_CYLINDER)
        bbmin, bbmax = bound.box_min, bound.box_max
        extent = bbmax - bbmin
        cylinder.bound_length = extent.y
        cylinder.bound_radius = extent.x * 0.5
        # create_cylinder(cylinder.data, radius, length)

        return cylinder
    elif bound.type == 'Disc':
        disc = init_bound_obj(bound, SollumType.BOUND_DISC)
        bbmin, bbmax = bound.box_min, bound.box_max
        disc.bound_radius = bound.sphere_radius
        create_disc(disc.data, bound.sphere_radius, bound.margin * 2)
        # Cant assign to dimensions directly according to docs
        # disc.dimensions = length, disc.dimensions.y, disc.dimensions.z

        return disc
    elif bound.type == 'Cloth':
        cloth = init_bound_obj(bound, SollumType.BOUND_CLOTH)
        return cloth
    elif bound.type == 'Geometry':
        geometry = geometry_to_obj(bound, SollumType.BOUND_GEOMETRY)
        return geometry
    elif bound.type == 'GeometryBVH':
        bvh = geometry_to_obj(bound, SollumType.BOUND_GEOMETRYBVH)
        return bvh


def composite_to_obj(bounds, name, from_drawable=False):
    if(from_drawable):
        composite = bounds
    else:
        composite = bounds.composite

    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = 0
    obj.sollum_type = SollumType.BOUND_COMPOSITE

    for idx, child in enumerate(composite.children):
        child_obj = bound_to_obj(child)
        child_obj.creation_index = idx
        if child_obj:
            child_obj.parent = obj

    bpy.context.collection.objects.link(obj)

    return obj


def import_ybn(filepath):
    ybn_xml = YBN.from_xml_file(filepath)
    composite_to_obj(ybn_xml, os.path.basename(
        filepath.replace(YBN.file_extension, '')))
