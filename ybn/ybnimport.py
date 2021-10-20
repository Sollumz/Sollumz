import bpy
from .properties import CollisionMatFlags
from Sollumz.resources.bound import *
from Sollumz.sollumz_properties import *
from .collision_materials import create_collision_material_from_index, collisionmats
from Sollumz.sollumz_ui import SOLLUMZ_UI_NAMES
from Sollumz.meshhelper import *
import os, traceback
from mathutils import Matrix

def init_poly_obj(poly, sollum_type, materials):
    name = SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    if poly.material_index < len(materials):
        mesh.materials.append(materials[poly.material_index])

    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = sollum_type.value

    return obj

def poly_to_obj(poly, materials, vertices):
    if type(poly) == Box:
        obj = init_poly_obj(poly, PolygonType.BOX, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]
        v3 = vertices[poly.v3]
        v4 = vertices[poly.v4]

        cf1 = (v1 + v2) / 2
        cf2 = (v3 + v4) / 2
        cf3 = (v1 + v4) / 2
        cf4 = (v2 + v3) / 2
        cf5 = (v1 + v3) / 2
        cf6 = (v2 + v4) / 2

        # caclulate obj center
        center = (cf3 + cf4) / 2

        rightest = get_closest_axis_point(Vector((1, 0, 0)), center, [cf1, cf2, cf3, cf4, cf5, cf6])
        upest    = get_closest_axis_point(Vector((0, 0, 1)), center, [cf1, cf2, cf3, cf4, cf5, cf6])
        right    = (rightest - center).normalized()
        up       = (upest    - center).normalized()
        forward  = Vector.cross(right, up).normalized()

        mat = Matrix.Identity(4)

        mat[0] = (right.x,   right.y,   right.z,   0)
        mat[1] = (up.x,      up.y,      up.z,      0)
        mat[2] = (forward.x, forward.y, forward.z, 0)
        mat[3] = (0,         0,         0,         1)

        mat.normalize()

        rotation = mat.to_quaternion().inverted().normalized().to_euler('XYZ')

        # calculate scale
        seq = [cf1, cf2, cf3, cf4, cf5, cf6]

        _cf1 = get_closest_axis_point(right,    center, seq)
        _cf2 = get_closest_axis_point(-right,   center, seq)
        _cf3 = get_closest_axis_point(-up,      center, seq)
        _cf4 = get_closest_axis_point(up,       center, seq)
        _cf5 = get_closest_axis_point(-forward, center, seq)
        _cf6 = get_closest_axis_point(forward,  center, seq)

        W = (_cf2 - _cf1).length
        L = (_cf3 - _cf4).length
        H = (_cf5 - _cf6).length

        scale = Vector((W, L, H))

        mesh = obj.data
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        bm.to_mesh(mesh)
        bm.free()

        obj.location = center
        obj.rotation_euler = rotation
        obj.scale = scale

        return obj
    elif type(poly) == Sphere:
        sphere = init_poly_obj(poly, PolygonType.SPHERE, materials)
        mesh = sphere.data
        create_sphere(mesh, poly.radius)

        sphere.location = vertices[poly.v]

        return sphere
    elif type(poly) == Capsule:
        capsule = init_poly_obj(poly, PolygonType.CAPSULE, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]
        length = get_distance_of_vectors(v1, v2) + (poly.radius * 2) 
        rot = get_direction_of_vectors(v1, v2)

        create_capsule(capsule, poly.radius, length)
        
        capsule.location = (v1 + v2) / 2     
        capsule.rotation_euler = rot
        
        return capsule
    elif type(poly) == Cylinder:
        cylinder = init_poly_obj(poly, PolygonType.CYLINDER, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]

        length = get_distance_of_vectors(v1, v2)
        rot = get_direction_of_vectors(v1, v2)

        cylinder.data = create_cylinder(cylinder.data, poly.radius, length, False)

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
    mesh = bpy.data.meshes.new(SOLLUMZ_UI_NAMES[PolygonType.TRIANGLE])
    triangle_obj = bpy.data.objects.new(SOLLUMZ_UI_NAMES[PolygonType.TRIANGLE], mesh)
    triangle_obj.sollum_type = PolygonType.TRIANGLE

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
            poly_obj = poly_to_obj(poly, triangle_obj.data.materials, geometry.vertices)
            if poly_obj:
                bpy.context.collection.objects.link(poly_obj)
                poly_obj.parent = obj

    triangle_obj.data.from_pydata(vertices, [], faces)
    bpy.context.collection.objects.link(triangle_obj)
    triangle_obj.parent = obj

    #Apply vertex colors
    mesh = triangle_obj.data
    if(len(geometry.vertex_colors) > 0):
        mesh.vertex_colors.new(name = "Vertex Colors") 
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
    if not (sollum_type == BoundType.COMPOSITE or sollum_type == BoundType.GEOMETRYBVH or sollum_type == BoundType.GEOMETRY):
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        mat_index = bound.material_index
        try:
            mat = create_collision_material_from_index(mat_index)
            mesh.materials.append(mat)
        except IndexError:
            print(f"Warning: Failed to set materials for {name}. Material index {mat_index} does not exist in collisionmats list.")
    else:
        obj = bpy.data.objects.new(name, None)

    obj.empty_display_size = 0
    obj.sollum_type = sollum_type.value

    obj.bound_properties.procedural_id = bound.procedural_id
    obj.bound_properties.room_id = bound.room_id
    obj.bound_properties.ped_density = bound.ped_density
    obj.bound_properties.poly_flags = bound.poly_flags
    obj.bound_properties.inertia = bound.inertia
    obj.bound_properties.margin = bound.margin
    obj.bound_properties.volume = bound.volume

    #assign obj composite flags
    for prop in dir(obj.composite_flags1):
        for f in bound.composite_flags1:
            if f.lower() == prop:
                setattr(obj.composite_flags1, prop, True)  

    for prop in dir(obj.composite_flags2):
        for f in bound.composite_flags2:
            if f.lower() == prop:
                setattr(obj.composite_flags2, prop, True)

    obj.location = bound.composite_position
    obj.rotation_euler = bound.composite_rotation.to_euler()
    obj.scale = Vector([1, 1, 1])

    bpy.context.collection.objects.link(obj)

    return obj

def bound_to_obj(bound):
    if bound.type == 'Box':
        box = init_bound_obj(bound, BoundType.BOX)
        create_box_from_extents(box.data, bound.box_min, bound.box_max)
        
        return box
    elif bound.type == 'Sphere':
        sphere = init_bound_obj(bound, BoundType.SPHERE)
        create_sphere(sphere.data, bound.sphere_radius)

        return sphere
    elif bound.type == 'Capsule':
        capsule = init_bound_obj(bound, BoundType.CAPSULE)
        bbmin, bbmax = bound.box_min, bound.box_max
        create_capsule(capsule, bound.sphere_radius, bbmax.z - bbmin.z, True)

        return capsule
    elif bound.type == 'Cylinder':
        cylinder = init_bound_obj(bound, BoundType.CYLINDER)
        bbmin, bbmax = bound.box_min, bound.box_max
        extent = bbmax - bbmin
        length = extent.y
        radius = extent.x * 0.5
        cylinder.scale = Vector([1, 1, 1])
        create_cylinder(cylinder.data, radius, length)

        return cylinder
    elif bound.type == 'Disc':
        disc = init_bound_obj(bound, BoundType.DISC)
        bbmin, bbmax = bound.box_min, bound.box_max
        length = bound.margin * 2
        radius = bound.sphere_radius
        create_disc(disc.data, bound.sphere_radius, length)

        return disc
    elif bound.type == 'Cloth':
        cloth = init_bound_obj(bound, BoundType.CLOTH)
        return cloth
    elif bound.type == 'Geometry':
        geometry = geometry_to_obj(bound, BoundType.GEOMETRY)
        return geometry
    elif bound.type == 'GeometryBVH':
        bvh = geometry_to_obj(bound, BoundType.GEOMETRYBVH)
        return bvh

def composite_to_obj(bounds, name, from_drawable):
    if(from_drawable):
        composite = bounds 
    else:
        composite = bounds.composite
    obj = bpy.data.objects.new(name, None)
    obj.empty_display_size = 0
    obj.sollum_type = BoundType.COMPOSITE

    for child in composite.children:
        child_obj = bound_to_obj(child)
        if child_obj:
            child_obj.parent = obj
    
    bpy.context.collection.objects.link(obj)

    return obj
