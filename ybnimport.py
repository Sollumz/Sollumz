import bpy
import os
import xml.etree.ElementTree as ET
from mathutils import Vector, Matrix, Quaternion
import math 
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from datetime import datetime 
import random 
from math import cos
from math import degrees
from math import radians
from math import sin
from math import sqrt 

from . import collisionmatoperators
from .tools import meshgen as MeshGen

def get_all_vertices(vert_data):
    vertices = [] 
    
    for vert in vert_data.text.split(" " * 5):
        data = vert.split(",")
        
        try:
            x = float(data[0])
            y = float(data[1])
            z = float(data[2])
            
            vertices.append(Vector((x, y, z)))
        except:
            a = 0
    
    return vertices 

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


def set_bound_transform(bounds, obj):
    locationn = bounds.find("CompositePosition")

    location = Vector((float(locationn.attrib["x"]), float(locationn.attrib["y"]), float(locationn.attrib["z"])))
    obj.location = location
    
    rotationn = bounds.find("CompositeRotation")

    rotation = Quaternion((float(rotationn.attrib["w"]), float(rotationn.attrib["x"]), float(rotationn.attrib["y"]), float(rotationn.attrib["z"]))) 
    obj.rotation_euler = rotation.to_euler()
    
    scalen = bounds.find("CompositeScale")

    scale = Vector((float(scalen.attrib["x"]), float(scalen.attrib["y"]), float(scalen.attrib["z"])))
    obj.scale = scale

    return obj

######################## STOLEN FROM GIZZ (edited) ###########################
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

def create_poly_box(polyline, allverts, materials, geocenter):
    
    materialindex = int(polyline.attrib["m"]) 
    idxs = []
    idxs.append(int(polyline.attrib["v1"]))
    idxs.append(int(polyline.attrib["v2"]))
    idxs.append(int(polyline.attrib["v3"]))
    idxs.append(int(polyline.attrib["v4"]))
    verts = []
    for idx in idxs:
        verts.append(allverts[idx])
    
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

    #obj.data.materials.append(material)
    
    #location = center + geocenter 
    
    obj.location                = center#location #boxes dont use geocenter to offset? 
    obj.rotation_euler          = rotation
    obj.scale                   = scale
    obj.sollumtype = "Bound Box"
    
    return obj
#######################################################################

def create_poly_triangle(triangleline, vertices, materials, geocenter):
    
    materialindex = int(triangleline.attrib["m"])
    indicies = []
    indicies.append(int(triangleline.attrib["v1"]))
    indicies.append(int(triangleline.attrib["v2"]))
    indicies.append(int(triangleline.attrib["v3"]))
    #return indicies
    verts = []
    for i in indicies:
        verts.append(vertices[i])
    
    result = []
    
    result.append(indicies)
    result.append(verts)
    result.append(materialindex)
    
    #create mesh
    #mesh = bpy.data.meshes.new("Geometry")
    #mesh.from_pydata(verts, [], [[0, 1, 2]]) 
    
    
    #mat = materials[materialindex]
    #mesh.materials.append(mat)
    
    #obj = bpy.data.objects.new("Triangle", mesh)
    #obj.sollumtype = "Bound Triangle"

    #return obj
    return result
    
def create_poly_sphere(sphereline, vertices, materials, geocenter):
    
    radius = float(sphereline.attrib["radius"])
    location = vertices[int(sphereline.attrib["v"])]
    materialindex = int(sphereline.attrib["m"])
    
    mesh = bpy.data.meshes.new("sphere")
    MeshGen.BoundSphere(mesh, radius)

    mat = materials[materialindex]
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("sphere", mesh)
    obj.sollumtype = "Bound Sphere"
    obj.location = location
    obj.bounds_radius = radius
    
    return obj


def create_poly_capsule(capsuleline, vertices, materials, geocenter):
    
    materialindex = int(capsuleline.attrib["m"])
    radius = float(capsuleline.attrib["radius"])
    v1 = vertices[int(capsuleline.attrib["v1"])]
    v2 = vertices[int(capsuleline.attrib["v2"])]
    length = get_distance_of_verts(v1, v2)    
    rot = get_direction_of_verts(v1, v2)
    
    mesh = bpy.data.meshes.new("capsule")
    MeshGen.BoundCapsule(mesh, radius, length)
    
    mesh.materials.append(materials[materialindex])
    
    obj = bpy.data.objects.new("Capsule", mesh)
    
    obj.location = (v1 + v2) / 2     
    obj.rotation_euler = rot

    obj.sollumtype = "Bound Capsule"
    obj.bounds_radius = radius
    obj.bounds_length = length
    
    return obj

def create_poly_cylinder(cylinderline, vertices, materials, geocenter):
    radius = float(cylinderline.attrib["radius"])
    v1 = vertices[int(cylinderline.attrib["v1"])]
    v2 = vertices[int(cylinderline.attrib["v2"])]
    length = get_distance_of_verts(v1, v2)    
    rot = get_direction_of_verts(v1, v2)
    materialindex = int(cylinderline.attrib["m"])
    
    mesh = bpy.data.meshes.new("cylinder")
    MeshGen.BoundCylinder(mesh, radius, length)
    
    mat = materials[materialindex]
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("cylinder", mesh)
    obj.sollumtype = "Bound Cylinder"
    obj.location = (v1 + v2) / 2     
    obj.rotation_euler = rot
    obj.bounds_radius = radius
    obj.bounds_length = length

    return obj

## NOT USED ## at least codewalker doesnt use it?
def create_poly_disc(discline, vertices, materials, geocenter):
    #obj.sollumtype = "Bound Disc"
    return None

def read_box_info(bounds):
    
    mesh = bpy.data.meshes.new("Box")
    bm   = bmesh.new()

    bmesh.ops.create_cube(bm, size=1)
    bm.to_mesh(mesh)
    bm.free()
    
    matindex = bounds.find("MaterialIndex").attrib["value"]
    mat = collisionmatoperators.create_with_index(matindex, bpy.context) 
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("Box", mesh)
    obj.sollumtype = "Bound Box"
    set_bound_transform(bounds, obj)
    
    return obj
    
def read_sphere_info(bounds):
    
    mesh = bpy.data.meshes.new("Sphere")
    bm   = bmesh.new()

    bmesh.ops.create_uvsphere(bm, u_segments = 16, v_segments = 16, diameter=.5)
    bm.to_mesh(mesh)
    bm.free()
    
    matindex = bounds.find("MaterialIndex").attrib["value"]
    mat = collisionmatoperators.create_with_index(matindex, bpy.context) 
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("Sphere", mesh)
    obj.sollumtype = "Bound Sphere"
    set_bound_transform(bounds, obj)
    
    return obj

def read_capsule_info(bounds):
    
    mesh = bpy.data.meshes.new(name="Capsule")
    MeshGen.BoundCapsule(mesh, .01, .975)
    obj = bpy.data.objects.new("Capsule", mesh)
    
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
    bm.to_mesh(mesh)
    bm.free()
    
    matindex = bounds.find("MaterialIndex").attrib["value"]
    mat = collisionmatoperators.create_with_index(matindex, bpy.context) 
    mesh.materials.append(mat)
    
    obj.sollumtype = "Bound Capsule"
    set_bound_transform(bounds, obj)
    
    return obj

def read_cylinder_info(bounds):
    
    mesh = bpy.data.meshes.new("Cylinder")
    bm   = bmesh.new()

    bmesh.ops.create_cone(bm, cap_ends=True, cap_tris=False, segments=12, diameter1=.5, diameter2=.5, depth=1)
    bmesh.ops.rotate(bm, verts=bm.verts, cent=(1.0, 0.0, 0.0), matrix=Matrix.Rotation(math.radians(90.0), 3, 'X'))
    bm.to_mesh(mesh)
    bm.free()
    
    matindex = bounds.find("MaterialIndex").attrib["value"]
    mat = collisionmatoperators.create_with_index(matindex, bpy.context) 
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("Cylinder", mesh)
    obj.sollumtype = "Bound Cylinder"
    set_bound_transform(bounds, obj)
    
    return obj

def read_disc_info(bounds):
    mesh = bpy.data.meshes.new("Disc")
    radius = float(bounds.find("SphereRadius").attrib["value"])
    margin = float(bounds.find("Margin").attrib["value"])

    MeshGen.BoundDisc(mesh=mesh, radius=radius, length=margin)

    matindex = bounds.find("MaterialIndex").attrib["value"]
    mat = collisionmatoperators.create_with_index(matindex, bpy.context) 
    mesh.materials.append(mat)
    
    obj = bpy.data.objects.new("Disc", mesh)
    set_bound_transform(bounds, obj)

    obj.sollumtype = "Bound Disc"
    obj.bounds_radius = radius
    obj.bounds_length = margin
    
    return obj

def read_cloth_info(bounds):
    print("ERROR")

def create_materials(emats):
    mats = []
    
    for emat in emats:
        matindex = str(emat.find("Type").attrib["value"])
        mat = collisionmatoperators.create_with_index(matindex, bpy.context) 
        mats.append(mat)
        
    return mats

def read_geometry_info(bounds, bvh=False):

    objectName = "GeometryBVH" if bvh else "Geometry"    

    #read materials
    materials = create_materials(bounds.find("Materials"))   
    
    bobj = bpy.data.objects.new(objectName, None)
    
    geocenter = bounds.find("GeometryCenter")
    geolocation = Vector((float(geocenter.attrib["x"]), float(geocenter.attrib["y"]), float(geocenter.attrib["z"])))
    
    bobj.location = geolocation
    
    vertices = get_all_vertices(bounds.find("Vertices"))  
    
    tindicies = []
    tverts = []
    pmaterialidxs = []
    
    polys = []
    
    for p in bounds.find("Polygons"):
        if(p.tag == "Triangle"):
            result = create_poly_triangle(p, vertices, materials, geolocation)
            
            tindicies.append(result[0])
            #for ind in result[0]:
            #    tindicies.append(ind)
            for vert in result[1]:
                tverts.append(vert)
            pmaterialidxs.append(result[2])
            
            #indicies.append(create_poly_triangle(p, vertices, materials, geolocation))
            #way to slow for the plugin...
            t = None#create_triangle(p, vertices, materials)
            if( t!= None):
                t.parent = bobj
                bpy.context.scene.collection.objects.link(t)
        if(p.tag == "Box"):
            b = create_poly_box(p, vertices, materials, geolocation)
            if(b != None):
                polys.append(b)
                #b.parent = bobj
                bpy.context.scene.collection.objects.link(b)
        if(p.tag == "Sphere"):
            s = create_poly_sphere(p, vertices, materials, geolocation)
            if(s != None):
                polys.append(s)
                #s.parent = bobj
                bpy.context.scene.collection.objects.link(s)
        if(p.tag == "Capsule"):
            c = create_poly_capsule(p, vertices, materials, geolocation)
            if(c != None):
                polys.append(c)
                #c.parent = bobj
                bpy.context.scene.collection.objects.link(c)
        if(p.tag == "Cylinder"):
            c = create_poly_cylinder(p, vertices, materials, geolocation)
            if(c != None):
                polys.append(c)
                #c.parent = bobj
                bpy.context.scene.collection.objects.link(c)
        if(p.tag == "Disc"):
            d = create_poly_disc(p, vertices, materials, geolocation)
            if(d != None):
                polys.append(d)
                #d.parent = bobj
                bpy.context.scene.collection.objects.link(d)
    
    #create triangle mesh
    mesh = bpy.data.meshes.new("Geometry")
    mesh.from_pydata(vertices, [], tindicies)
    #assign triangle materials
    for mat in materials:
        mesh.materials.append(mat)
    
    for idx in range(len(mesh.polygons)):
        mesh.polygons[idx].material_index = pmaterialidxs[idx]
    
    bobj = bpy.data.objects.new(objectName, mesh)  
    set_bound_transform(bounds, bobj)
    bobj.location += geolocation
    for poly in polys:
        poly.parent = bobj
    
    #clean up old verts
    #bobj.select_set(True)
    #bpy.ops.object.mode_set(mode='EDIT')
    #bpy.ops.mesh.select_loose()
    #bpy.ops.mesh.delete(type='VERT')
    
    bobj.sollumtype = "Bound Geometry"
    bobj.bounds_bvh = bvh
    return bobj

def read_composite_info(name, bounds):
    
    cobj = bpy.data.objects.new(name + "_col", None)
        
    if(cobj == None):
        return #log error 
    
    children = []
    
    #read children 
    for child in bounds.find("Children"):
        
        childtype = child.attrib["type"]
        
        if(childtype == "GeometryBVH"):
            children.append(read_geometry_info(child, True))
        if(childtype == "Geometry"):
            children.append(read_geometry_info(child, False))
        if(childtype == "Box"):
            children.append(read_box_info(child))
        if(childtype == "Sphere"):
            children.append(read_sphere_info(child))
        if(childtype == "Capsule"):
            children.append(read_capsule_info(child))
        if(childtype == "Cylinder"):
            children.append(read_cylinder_info(child))
        if(childtype == "Disc"):
            children.append(read_disc_info(child))
        if(childtype == "Cloth"):
            print()
            #children.append(read_cloth_info(child))
    
    for child in children:
        bpy.context.scene.collection.objects.link(child)   
        child.parent = cobj 
        
    cobj.sollumtype = "Bound Composite"

    return cobj
    
def read_bounds(name, bounds):
    
    type = bounds.attrib["type"]
    
    #bobjs = []
    
    if(type == "Composite"):
        return read_composite_info(name, bounds)
        #bobjs.append(read_composite_info(name, bounds))
    else:
        print("ERROR UNKNOWN BOUND TYPE OF : " + type)
        return None
        
    """ not needed since all R* bounds have a composite as the root of all objects
    if(type == "Box"):
        read_box_info(bounds)
    if(type == "Sphere"):
        bobjs.append(read_sphere_info(child))
    if(type == "Capsule"):
        bobjs.append(read_capsule_info(child))
    if(type == "Cylinder"):
        bobjs.append(read_cylinder_info(child))
    if(type == "Disc"):
        print()
        #bobjs.append(read_disc_info(child))
    if(type == "Cloth"):
        print()
        #bobjs.append(read_cloth_info(child))
    """
    
    #return bobjs

def read_ybn_xml(context, filepath, root):
    
    filename = os.path.basename(filepath[:-8]) 
    
    bound_node = root.find("Bounds") 
    bound_obj = read_bounds(filename, bound_node)
    
    return bound_obj
    
class ImportYbnXml(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ybn"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ybn"

    # ImportHelper mixin class uses this
    filename_ext = ".ybn.xml"

    def execute(self, context):
        tree = ET.parse(self.filepath)
        root = tree.getroot() 
        
        bound_obj = read_ybn_xml(context, self.filepath, root)
        
        if(bound_obj != None):
            context.scene.collection.objects.link(bound_obj)
        else:
            self.report("Error importing ybn located at: " + self.filepath)
            
        return {'FINISHED'}
    
# Only needed if you want to add into a dynamic menu
def menu_func_import_ybn(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Ybn (.ybn.xml)")

def register():
    bpy.utils.register_class(ImportYbnXml)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ybn)

def unregister():
    bpy.utils.unregister_class(ImportYbnXml)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ybn)
