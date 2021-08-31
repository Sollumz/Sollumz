import bpy
import bmesh
import xml.etree.ElementTree as ET
import os
import sys
sys.path.append(os.path.dirname(__file__))
from bpy_extras.io_utils import ImportHelper
from .resources.bound import Bound
from .sollumz_shaders import create_collision_material_from_index
import meshgen
from mathutils import Vector, Matrix, Quaternion
import math 
from math import cos, degrees, radians, sin, sqrt

def get_distance_of_verts(a, b):
    locx = b[0] - a[0]
    locy = b[1] - a[1]
    locz = b[2] - a[2]

    distance = sqrt((locx)**2 + (locy)**2 + (locz)**2) 
    return distance

def get_direction_of_verts(a, b):
    direction  = (a - b).normalized()
    axis_align = Vector((0.0, 0.0, 1.0))

    angle = axis_align.angle(direction)
    axis  = axis_align.cross(direction)

    q = Quaternion(axis, angle)
    
    return q.to_euler('XYZ')

def set_bound_transform(obj, bound):
    location = Vector((bound.composite_position[0], bound.composite_position[1], bound.composite_position[2]))
    rotation = Quaternion((bound.composite_rotation[0], bound.composite_rotation[1], bound.composite_rotation[2]))
    scale = Vector((bound.composite_scale[0], bound.composite_scale[1], bound.composite_scale[2]))

    obj.location = location
    obj.rotation_euler  = rotation.to_euler()
    obj.scale = scale

def bound_poly_cylinder_to_blender(cylinder, vertices, materials):
    radius = cylinder.radius
    v1 = vertices[cylinder.v1]
    v2 = vertices[cylinder.v2]
    length = get_distance_of_verts(v1, v2)    
    rot = get_direction_of_verts(v1, v2)
    materialindex = cylinder.material_index
    
    mesh = bpy.data.meshes.new("cylinder")
    meshgen.bound_cylinder(mesh, radius, length)
    
    mat = materials[materialindex]
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("cylinder", mesh)
    obj.sollum_type = "sollumz_bound_poly_cylinder"
    obj.location = (v1 + v2) / 2     
    obj.rotation_euler = rot

    return obj

def get_closest_axis_point(axis, center, points):

    closest     = None
    closestDist = math.inf

    for p in points:
        
        rel  = (p - center).normalized()
        dist = (rel - axis).length

        if dist < closestDist:
            closest     = p
            closestDist = dist

    return closest

def bound_poly_box_to_blender(box, vertices, materials):
    materialindex = box.material_index
    idxs = []
    idxs.append(box.v1)
    idxs.append(box.v2)
    idxs.append(box.v3)
    idxs.append(box.v4)
    verts = []
    for idx in idxs:
        verts.append(vertices[idx])
    
    p1 = verts[0]
    p2 = verts[1]
    p3 = verts[2]
    p4 = verts[3]

    a, b, c, d = p1, p2, p3, p4

    cf1 = (a + b) / 2
    cf2 = (c + d) / 2
    cf3 = (a + d) / 2
    cf4 = (b + c) / 2
    cf5 = (a + c) / 2
    cf6 = (b + d) / 2

    # caclulate box center
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

    # blender stuff
    mesh = bpy.data.meshes.new("box")
    bm   = bmesh.new()

    bmesh.ops.create_cube(bm, size=1)
    bm.to_mesh(mesh)
    bm.free()
    
    mat = materials[materialindex]
    mesh.materials.append(mat)

    obj = bpy.data.objects.new("box", mesh)

    obj.location                = center#location #boxes dont use geocenter to offset? 
    obj.rotation_euler          = rotation
    obj.scale                   = scale
    obj.sollum_type = "sollumz_bound_poly_box"
    
    return obj

def bound_poly_capsule_to_blender(capsule, vertices, materials):
    materialindex = capsule.material_index
    radius = capsule.radius
    v1 = vertices[capsule.v1]
    v2 = vertices[capsule.v2]
    length = get_distance_of_verts(v1, v2)    
    rot = get_direction_of_verts(v1, v2)
    
    mesh = bpy.data.meshes.new("capsule")
    meshgen.bound_capsule(mesh, radius, length)
    
    mat = materials[materialindex]
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("Capsule", mesh)
    
    obj.location = (v1 + v2) / 2     
    obj.rotation_euler = rot

    obj.sollum_type = "sollumz_bound_poly_capsule"
    
    return obj

def bound_poly_sphere_to_blender(sphere, vertices, materials):
    radius = sphere.radius
    location = vertices[sphere.v]
    materialindex = sphere.material_index
    
    mesh = bpy.data.meshes.new("sphere")
    meshgen.bound_sphere(mesh, radius)

    mat = materials[materialindex]
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("sphere", mesh)
    obj.sollum_type = "sollumz_bound_poly_sphere"
    
    return obj

def bound_poly_triangle_to_blender(triangle):
    obj = bpy.data.objects.new("triangle", None)
    return obj

def bound_geometry_to_blender(geometry):
    name = "Geometry"
    if(geometry.isbvh == True):
        name += "BVH"
    obj = bpy.data.objects.new(name, None)

    materials = []
    for gmat in geometry.materials:
        mat = create_collision_material_from_index(gmat.type)
        mat.sollum_type = "sollumz_gta_collision_material"
        mat.collision_properties.procedural_id = gmat.procedural_id
        mat.collision_properties.room_id = gmat.room_id
        mat.collision_properties.ped_density = gmat.ped_density
        materials.append(mat)

    vertices = []
    indicies = []
    material_idxs = []
    for vert in geometry.vertices:
        vertices.append(Vector((vert[0], vert[1], vert[2])))

    poly_objs = []
    for poly in geometry.polygons:
        if(poly.type == "Triangle"):
            #poly_objs.append(bound_poly_triangle_to_blender(poly)) cant use this TO SLOW
            inds = []
            inds.append(poly.v1)    
            inds.append(poly.v2)
            inds.append(poly.v3)
            indicies.append(inds)
            material_idxs.append(poly.material_index)
        if(poly.type == "Sphere"):
            poly_objs.append(bound_poly_sphere_to_blender(poly, vertices, materials))
        if(poly.type == "Capsule"):
            poly_objs.append(bound_poly_capsule_to_blender(poly, vertices, materials))
        if(poly.type == "Box"):
            poly_objs.append(bound_poly_box_to_blender(poly, vertices, materials))
        if(poly.type == "Cylinder"):
            poly_objs.append(bound_poly_cylinder_to_blender(poly, vertices, materials))

    #create triangle mesh
    mesh = bpy.data.meshes.new("TriangleMesh")
    mesh.from_pydata(vertices, [], indicies)
    
    for mat in materials:
        mesh.materials.append(mat)
    for idx in range(len(mesh.polygons)):
        mesh.polygons[idx].material_index = material_idxs[idx]

    triangle_obj = bpy.data.objects.new("Triangle", mesh)  
    bpy.context.scene.collection.objects.link(triangle_obj)
    triangle_obj.sollum_type = "sollumz_bound_poly_triangle"
    triangle_obj.parent = obj

    for poly in poly_objs:
        bpy.context.scene.collection.objects.link(poly)
        poly.parent = obj
    
    set_bound_transform(obj, geometry)

    obj.location += Vector((geometry.geometry_center[0], geometry.geometry_center[1], geometry.geometry_center[2]))
    obj.sollum_type = "sollumz_bound_" + name.lower()

    return obj

def bound_cloth_to_blender(cloth):
    obj = bpy.data.objects.new("Cloth", None)
    set_bound_transform(obj, cloth)

    material = create_collision_material_from_index(cloth.material_index)
    material.collision_properties.procedural_id = cloth.procedural_id
    material.collision_properties.room_id = cloth.room_id
    material.collision_properties.ped_density = cloth.ped_density
    #mesh.materials.append(material)

    obj.sollum_type = "sollumz_bound_cloth"

    return obj

def bound_disc_to_blender(disc):
    mesh = bpy.data.meshes.new("Disc")
    radius = disc.sphere_radius
    margin = disc.margin

    meshgen.bound_disc(mesh=mesh, radius=radius, length=margin)

    material = create_collision_material_from_index(disc.material_index)
    material.collision_properties.procedural_id = disc.procedural_id
    material.collision_properties.room_id = disc.room_id
    material.collision_properties.ped_density = disc.ped_density
    mesh.materials.append(material)

    obj = bpy.data.objects.new("Disc", mesh)
    set_bound_transform(obj, disc)

    obj.sollum_type = "sollumz_bound_disc"

    return obj

def bound_cylinder_to_blender(cylinder):
    mesh = bpy.data.meshes.new("Cylinder")
    bm   = bmesh.new()

    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, diameter1=.5, diameter2=.5, depth=1)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
    bm.to_mesh(mesh)
    bm.free()

    material = create_collision_material_from_index(cylinder.material_index)
    material.collision_properties.procedural_id = cylinder.procedural_id
    material.collision_properties.room_id = cylinder.room_id
    material.collision_properties.ped_density = cylinder.ped_density
    mesh.materials.append(material)

    obj = bpy.data.objects.new("Cylinder", mesh)
    set_bound_transform(obj, cylinder)

    obj.sollum_type = "sollumz_bound_cylinder"
    
    return obj

def bound_capsule_to_blender(capsule):
    mesh = bpy.data.meshes.new(name="Capsule")
    meshgen.bound_capsule(mesh, .01, .975)
    obj = bpy.data.objects.new("Capsule", mesh)
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
    bm.to_mesh(mesh)
    bm.free()
    
    material = create_collision_material_from_index(capsule.material_index)
    material.collision_properties.procedural_id = capsule.procedural_id
    material.collision_properties.room_id = capsule.room_id
    material.collision_properties.ped_density = capsule.ped_density
    mesh.materials.append(material)

    set_bound_transform(obj, capsule)
    
    obj.sollum_type = "sollumz_bound_capsule"
    
    return obj

def bound_sphere_to_blender(sphere):
    mesh = bpy.data.meshes.new("Sphere")
    bm   = bmesh.new()

    bmesh.ops.create_uvsphere(bm, u_segments = 16, v_segments = 16, diameter=.5)
    bm.to_mesh(mesh)
    bm.free()
    
    material = create_collision_material_from_index(sphere.material_index)
    material.collision_properties.procedural_id = sphere.procedural_id
    material.collision_properties.room_id = sphere.room_id
    material.collision_properties.ped_density = sphere.ped_density
    mesh.materials.append(material)

    obj = bpy.data.objects.new("Sphere", mesh)
    set_bound_transform(obj, sphere)

    obj.sollum_type = "sollumz_bound_sphere"
    
    return obj

def bound_box_to_blender(box):
    mesh = bpy.data.meshes.new("Box")
    bm   = bmesh.new()

    bmesh.ops.create_cube(bm, size=1)
    bm.to_mesh(mesh)
    bm.free()
    
    material = create_collision_material_from_index(box.material_index)
    material.collision_properties.procedural_id = box.procedural_id
    material.collision_properties.room_id = box.room_id
    material.collision_properties.ped_density = box.ped_density
    ######### materials.flags = box.flags ######### not done
    mesh.materials.append(material)

    obj = bpy.data.objects.new("Box", mesh)
    set_bound_transform(obj, box)

    obj.sollum_type = "sollumz_bound_box"

    return obj

def bound_composite_to_blender(composite, name):
    composite_obj = bpy.data.objects.new(name, None)

    children_objs = []

    for child in composite.children:
        if(child.type == "Box"):
            children_objs.append(bound_box_to_blender(child))
        if(child.type == "Sphere"):
            children_objs.append(bound_sphere_to_blender(child))
        if(child.type == "Capsule"):
            children_objs.append(bound_capsule_to_blender(child))
        if(child.type == "Cylinder"):
            children_objs.append(bound_cylinder_to_blender(child))
        if(child.type == "Disc"):
            children_objs.append(bound_disc_to_blender(child))
        if(child.type == "Cloth"):
            children_objs.append(bound_cloth_to_blender(child))
        if("Geometry" in child.type):
            children_objs.append(bound_geometry_to_blender(child))

    print(children_objs)

    for obj in children_objs:
        bpy.context.collection.objects.link(obj)
        obj.parent = composite_obj
        print(obj.name)
    
    composite_obj.sollum_type = "sollumz_bound_composite"

    bpy.context.collection.objects.link(composite_obj)

    return composite_obj

class ImportYbnXml(bpy.types.Operator, ImportHelper):
    """Imports .ybn.xml file exported from codewalker."""
    bl_idname = "sollumz.importybn" 
    bl_label = "Import ybn.xml"
    filename_ext = ".ybn.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ybn.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def execute(self, context):
        b = Bound()
        b.read_xml(ET.parse(self.filepath).getroot()[0])
        
        bound_composite_to_blender(b, os.path.basename(self.filepath))

        return {'FINISHED'}

def ybn_menu_func_import(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Import .ybn.xml")