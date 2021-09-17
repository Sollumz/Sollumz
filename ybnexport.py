import bpy
from bpy_extras.io_utils import ExportHelper
import time, os, sys
sys.path.append(os.path.dirname(__file__))
import meshhelper
from .resources.bound import Bound, Poly

def get_children(myObject): 
    children = [] 
    for ob in bpy.data.objects: 
        if ob.parent == myObject: 
            children.append(ob) 
    return children 

def object_to_bound(obj):
    bound = Bound()
    
    name = obj.sollum_type.split('_')[-1].capitalize()
    isbvh = False

    #checks if bvh and if so fixes name
    if("bvh" in name.lower()):
        isbvh = True
        name = name[:-3]
        name += "BVH" 

    bound.type = name
    bound.procedural_id = obj.bound_properties.procedural_id
    bound.room_id = obj.bound_properties.room_id
    bound.ped_density = obj.bound_properties.ped_density
    bound.poly_flags = obj.bound_properties.poly_flags
    bound.isbvh = isbvh

    children_objs = get_children(obj)

    if("composite" in name.lower()):
        for cobj in children_objs:
            bound.children.append(object_to_bound(cobj))
    elif("geometry" in name.lower()):
        bound.composite_position = [0, 0, 0]
        bound.composite_rotation = [0, 0, 0, 1]#[obj.rotation_euler.to_quaternion()[0], obj.rotation_euler.to_quaternion()[1], obj.rotation_euler.to_quaternion()[2], obj.rotation_euler.to_quaternion()[3]]
        bound.composite_scale = [obj.scale[0], obj.scale[1], obj.scale[2]]
        bound.geometry_center = [obj.location[0], obj.location[1], obj.location[2]]
        
        bbminmax = meshhelper.get_min_max_bounding_box([obj])
        #bbminmax = [obj.bound_box[0], obj.bound_box[6]]
        bound.box_min = [bbminmax[0][0], bbminmax[0][1], bbminmax[0][2]]
        bound.box_max = [bbminmax[1][0], bbminmax[1][1], bbminmax[1][2]]
        
        bb_center = [0, 0, 0]
        bound.box_center = bb_center

        #bbsphere = meshhelper.get_sphere_bb([obj], bbminmax)
        #bound.sphere_center = [bbsphere[0][0], bbsphere[0][1], bbsphere[0][2]]
        #bound.sphere_radius = bbsphere[1]

        for prop in dir(obj.composite_flags1):
            value = getattr(obj.composite_flags1, prop)
            if(value == True):
                bound.composite_flags1.append(prop.upper())
        
        for prop in dir(obj.composite_flags2):
            value = getattr(obj.composite_flags2, prop)
            if(value == True):
                bound.composite_flags2.append(prop.upper())

        vertices = []
        vertex_index = 0

        for child in children_objs:
            poly = Poly()
            if(child.sollum_type == "sollumz_bound_poly_box"):
                poly.type = "Box"
                vertex_index += 4
                poly.v1 = vertex_index - 4
                poly.v2 = vertex_index - 3
                poly.v3 = vertex_index - 2
                poly.v4 = vertex_index - 1
                poly.material_index = 0
                for vert in child.data.vertices:
                    vertices.append(vert.co)
            elif(child.sollum_type == "sollumz_bound_poly_sphere"):
                poly.type = "Sphere"
                vertex_index += 1
                poly.v1 = vertex_index - 1
                poly.material_index = 0
                poly.radius = 0 ######################### GET RADIUS ########################
                vertices.append(child.location)
            elif(child.sollum_type == "sollumz_bound_poly_capsule"):
                poly.type = "Capsule"
                vertex_index += 2
                poly.v1 = vertex_index - 2
                poly.v2 = vertex_index - 1
                poly.material_index = 0
            elif(child.sollum_type == "sollumz_bound_poly_cylinder"):
                poly.type = "Cylinder"
                vertex_index += 2
                poly.v1 = vertex_index - 2
                poly.v2 = vertex_index - 1
                poly.material_index = 0
                bound.geometry_center 
            elif(child.sollum_type == "sollumz_bound_poly_triangle"):
                mesh = child.data
                mesh.calc_loop_triangles() 

                for face in mesh.loop_triangles:
                    vert1 = mesh.vertices[face.vertices[0]].co
                    vert2 = mesh.vertices[face.vertices[1]].co
                    vert3 = mesh.vertices[face.vertices[2]].co
                    vertices.append(vert1)
                    vertices.append(vert2)
                    vertices.append(vert3)
                    vertex_index += 3

                    poly = Poly()
                    poly.type = "Triangle"
                    poly.material_index = 0
                    poly.v1 = vertex_index - 3
                    poly.v2 = vertex_index - 2
                    poly.v3 = vertex_index - 1
                    poly.f1 = 0
                    poly.f2 = 0
                    poly.f3 = 0
                    bound.polygons.append(poly)

                break
            bound.polygons.append(poly)

        bound.vertices = vertices

    elif("box" in name.lower()):
        print("not implemented")
    elif("sphere" in name.lower()):
        print("not implemented")
    elif("capsule" in name.lower()):
        print("not implemented")
    elif("cylinder" in name.lower()):
        print("not implemented")
    elif("disc" in name.lower()):
        print("not implemented")
    elif("cloth" in name.lower()):
        print("not implemented")

    return bound

class ExportYbnXml(bpy.types.Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ybn"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ybn Xml (.ybn.xml)"

    # ExportHelper mixin class uses this
    filename_ext = ".ybn.xml"

    def execute(self, context):

        objects = bpy.context.collection.objects

        if(len(objects) == 0):
            return "No objects in scene for Sollumz export"

        for obj in objects:
                if(obj.sollum_type == "sollumz_bound_composite"):
                    composite = object_to_bound(obj)

                    print("")
                    print("EXPORTING YBN")
                    print("")
                    #for child in composite.children:
                        #print(len(child.vertices))
                        #print(child.__dict__)
                        #for p in child.polygons:
                           #print(p.__dict__)
                    print(composite.composite_flags1)
                    root = composite.write_xml()

        return {'FINISHED'}

def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname, text="Export .ybn.xml")