import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator
from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment, tostring
from xml.dom import minidom
from mathutils import Vector
import os 
import sys 
import shutil
import ntpath
from datetime import datetime 
from .ydrexport import get_obj_children, get_bbs, get_sphere_bb, prettify

def append_bbs(obj, node):
#    children = get_obj_children(obj)
    bbminmax = get_bbs([obj])

    bbmin_node = Element("BoxMin")
    bbmin_node.set("x", str(bbminmax[0][0]))
    bbmin_node.set("y", str(bbminmax[0][1]))
    bbmin_node.set("z", str(bbminmax[0][2]))
    node.append(bbmin_node)
    
    bbmax_node = Element("BoxMax")
    bbmax_node.set("x", str(bbminmax[1][0]))
    bbmax_node.set("y", str(bbminmax[1][1]))
    bbmax_node.set("z", str(bbminmax[1][2]))
    node.append(bbmax_node)

    # TODO
    loc = obj.matrix_world.to_translation()
    pos_node = Element("CompositePosition")
    pos_node.set("x", str(loc.x))
    pos_node.set("y", str(loc.y))
    pos_node.set("z", str(loc.z))
    node.append(pos_node)

    # TODO
    loc = obj.matrix_world.to_translation()
    rot_node = Element("CompositeRotation")
    rot_node.set("x", str(0))
    rot_node.set("y", str(0))
    rot_node.set("z", str(0))
    rot_node.set("w", str(1))
    node.append(rot_node)

    # TODO
    loc = obj.matrix_world.to_translation()
    scale_node = Element("CompositeScale")
    scale_node.set("x", str(1))
    scale_node.set("y", str(1))
    scale_node.set("z", str(1))
    node.append(scale_node)

    # TODO
    bbmax_node = Element("BoxCenter")
    bbmax_node.set("x", str(0))
    bbmax_node.set("y", str(0))
    bbmax_node.set("z", str(0))
    node.append(bbmax_node)

def append_junk(obj, node):
    # TODO
    inertia_node = Element("Inertia")
    inertia_node.set("x", "1")
    inertia_node.set("y", "1")
    inertia_node.set("z", "1")
    node.append(inertia_node)

    # TODO
    geomcenter_node = Element("GeometryCenter")
    geomcenter_node.set("x", "0")
    geomcenter_node.set("y", "0")
    geomcenter_node.set("z", "0")
    node.append(geomcenter_node)

    # TODO
    matind_node = Element("MaterialIndex")
    matind_node.set("value", "0")
    node.append(matind_node)

    # TODO
    matcolind_node = Element("MaterialColourIndex")
    matcolind_node.set("value", "0")
    node.append(matcolind_node)

    # TODO
    procid_node = Element("ProceduralID")
    procid_node.set("value", "0")
    node.append(procid_node)

    # TODO
    roomid_node = Element("RoomID")
    roomid_node.set("value", "0")
    node.append(roomid_node)

    # TODO
    peddensity_node = Element("PedPensity")
    peddensity_node.set("value", "0")
    node.append(peddensity_node)

    # TODO
    unkflags_node = Element("UnkFlags")
    unkflags_node.set("value", "0")
    node.append(unkflags_node)

    # TODO
    polyflags_node = Element("PolyFlags")
    polyflags_node.set("value", "0")
    node.append(polyflags_node)

    # TODO
    unktype_node = Element("UnkType")
    unktype_node.set("value", "2")
    node.append(unktype_node)

def write_bound_disc(obj):

    node = Element("Item")
    node.set("type", "Disc")

    append_bbs(obj, node)
    append_junk(obj, node)

    length = obj.bounds_length
    radius = obj.bounds_radius

    margin_node = Element("Margin")
    margin_node.set("value", str(length))
    node.append(margin_node)

    bsc_node = Element("SphereCenter")
    bsc_node.set("x", str(0))
    bsc_node.set("y", str(0))
    bsc_node.set("z", str(0))
    node.append(bsc_node)
    
    bsr_node = Element("SphereRadius")
    bsr_node.set("value", str(radius))
    node.append(bsr_node)

    return node

def write_bound_geometry_disc(obj, vertex_index):
    return None, None, None

def write_bound_geometry_sphere(obj, vertex_index):
    return None, None, None

def write_bound_geometry_cylinder(obj, vertex_index):
    return None, None, None

def write_bound_geometry_box(obj, vertex_index):
    return None, None, None

def write_bound_geometry_capsule(obj, vertex_index):
    verts = []
    polys = []
    mats = []

    length = obj.bounds_length
    radius = obj.bounds_radius

    loc = obj.matrix_world.to_translation()
    verts.append(loc-Vector((0,0,length/2)))
    verts.append(loc+Vector((0,0,length/2)))

    capsule_node = Element("Capsule")
    capsule_node.set("m", "0")
    capsule_node.set("v1", str(vertex_index))
    capsule_node.set("v2", str(vertex_index+1))
    capsule_node.set("radius", str(radius))

    polys.append(capsule_node)

    return verts, polys, mats

def write_bound_geometry_geometry(obj, vertex_index):
    
    verts = []
    polys = []
    mats = []

    mesh = obj.data
    mesh.calc_loop_triangles()

    for tri in mesh.loop_triangles:
        tri_vert1 = mesh.vertices[tri.vertices[0]].co
        tri_vert2 = mesh.vertices[tri.vertices[1]].co
        tri_vert3 = mesh.vertices[tri.vertices[2]].co
        verts.append(tri_vert1)
        verts.append(tri_vert2)
        verts.append(tri_vert3)
        vertex_index += 3

        triangle_node = Element("Triangle")
        triangle_node.set("m", "0")
        triangle_node.set("v1", str(vertex_index-3))
        triangle_node.set("v2", str(vertex_index-2))
        triangle_node.set("v3", str(vertex_index-1))
        triangle_node.set("f0", str(0))
        triangle_node.set("f1", str(0))
        triangle_node.set("f2", str(0))
        polys.append(triangle_node)

    return verts, polys, mats

def write_bound_geometry_item(obj, vertex_index):
    if(obj.sollumtype == "Bound Disc"): return write_bound_geometry_disc(obj, vertex_index)
    if(obj.sollumtype == "Bound Sphere"): return write_bound_geometry_sphere(obj, vertex_index)
    if(obj.sollumtype == "Bound Cylinder"): return write_bound_geometry_cylinder(obj, vertex_index)
    if(obj.sollumtype == "Bound Box"): return write_bound_geometry_box(obj, vertex_index)
    if(obj.sollumtype == "Bound Capsule"): return write_bound_geometry_capsule(obj, vertex_index)
    if(obj.sollumtype == "Bound Geometry"): return write_bound_geometry_geometry(obj, vertex_index)

    return None

def write_bound_geometry(obj):
    bvh = obj.bounds_bvh

    node = Element("Item")
    node.set("type", "GeometryBVH" if bvh else "Geometry")

    append_bbs(obj, node)
    append_junk(obj, node)
    
    vertices_node = Element("Vertices")
    node.append(vertices_node)

    polygons_node = Element("Polygons")
    node.append(polygons_node)

    materials_node = Element("Materials")
    node.append(materials_node)

    vertices, polygons, materials = write_bound_geometry_geometry(obj, 0)
    vertex_index = len(vertices)

    children = get_obj_children(obj)

    for c in children:
        verts, polys, mats = write_bound_geometry_item(c, vertex_index)
        
        if verts is not None:
            vertex_index += len(verts)
            vertices += verts
            polygons += polys
            materials += mats
            #children_node.append(child_node)

    vertices_text = '\n'.join(map(lambda v: "     {0}, {1}, {2}".format(v.x, v.y, v.z), vertices))
    vertices_node.text = vertices_text

    for p in polygons:
        polygons_node.append(p)

    #TODO: materials

    return node

def write_bound_sphere(obj):
    # TODO
    return None

def write_bound_cylinder(obj):
    # TODO
    return None

def write_bound_box(obj):
    # TODO
    return None

def write_bound_capsule(obj):
    # TODO
    return None

def write_bound_item(obj):
    if(obj.sollumtype == "Bound Disc"): return write_bound_disc(obj)
    if(obj.sollumtype == "Bound Sphere"): return write_bound_sphere(obj)
    if(obj.sollumtype == "Bound Cylinder"): return write_bound_cylinder(obj)
    if(obj.sollumtype == "Bound Box"): return write_bound_box(obj)
    if(obj.sollumtype == "Bound Capsule"): return write_bound_capsule(obj)
    if(obj.sollumtype == "Bound Geometry"): return write_bound_geometry(obj)

    return None

def write_bound_composite(obj):
    
    children = get_obj_children(obj)
    bbminmax = get_bbs(children)
    bbsphere = get_sphere_bb(children, bbminmax)
    
    bound_node = Element("Bounds")
    bound_node.set("type", "Composite")

    append_bbs(obj, bound_node)
    append_junk(obj, bound_node)

    bsc_node = Element("SphereCenter")
    bsc_node.set("x", str(bbsphere[0][0]))
    bsc_node.set("y", str(bbsphere[0][1]))
    bsc_node.set("z", str(bbsphere[0][2]))
    bound_node.append(bsc_node)
    
    bsr_node = Element("SphereRadius")
    bsr_node.set("value", str(bbsphere[1]))
    bound_node.append(bsr_node)

    # TODO
    margin_node = Element("Margin")
    margin_node.set("value", "0")
    bound_node.append(margin_node)

    # TODO
    volume_node = Element("Volume")
    volume_node.set("value", "0")
    bound_node.append(volume_node)

    children_node = Element("Children")
    bound_node.append(children_node)

    for c in children:
        child_node = write_bound_item(c)
        if child_node is not None:
            children_node.append(child_node)
    
    return bound_node
    
def write_ybn_xml(context, filepath):
    
    root = None

    objects = bpy.context.scene.collection.objects

    if(len(objects) == 0):
        return "No objects in scene for Sollumz export"

    root = Element("BoundsFile")
    
    for obj in objects:
            if(obj.sollumtype == "Bound Composite"):
                xml_node = write_bound_composite(obj)
                root.append(xml_node)

    print("*** Complete ***")
    
    xmlstr = prettify(root)
    with open(filepath, "w") as f:
        f.write(xmlstr)
        return "Sollumz Drawable was succesfully exported to " + filepath
            
class ExportYBN(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ybn"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ybn Xml (.ybn.xml)"

    # ExportHelper mixin class uses this
    filename_ext = ".ybn.xml"

    def execute(self, context):
        start = datetime.now    ()
        
        #try:
        result = write_ybn_xml(context, self.filepath)
        self.report({'INFO'}, result)
        
        #except Exception:
        #    self.report({"ERROR"}, str(Exception) )
            
        finished = datetime.now()
        difference = (finished - start).total_seconds()
        print("Exporting : " + self.filepath)
        print("Export Time:")
        print("start time: " + str(start))
        print("end time: " + str(finished))
        print("difference: " + str(difference) + " seconds")
        return {'FINISHED'}

# Only needed if you want to add into a dynamic menu
def menu_func_export(self, context):
    self.layout.operator(ExportYBN.bl_idname, text="Ybn Xml Export (.ybn.xml)")

def register():
    bpy.utils.register_class(ExportYBN)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.utils.unregister_class(ExportYBN)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
