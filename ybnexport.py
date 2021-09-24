import bpy
from bpy_extras.io_utils import ExportHelper
import os, sys
sys.path.append(os.path.dirname(__file__))
from meshhelper import get_total_bbs, get_bound_center, get_children_recursive
from .resources.bound import Bounds, BoundsComposite, GeometryBVH, BoundsFile, Triangle

def init_bounds(bounds: Bounds, obj):
    bounds.procedural_id = obj.bound_properties.procedural_id
    bounds.room_id = obj.bound_properties.room_id
    bounds.ped_density = obj.bound_properties.ped_density
    bounds.poly_flags = obj.bound_properties.poly_flags

    bbs = get_total_bbs(obj)
    bounds.box_min = bbs[0]
    bounds.box_max = bbs[1]
    bounds.box_center = get_bound_center(obj)

def object_to_composite(obj) -> BoundsComposite:
    bounds = BoundsComposite()
    init_bounds(bounds, obj)

    for child in get_children_recursive(obj):
        bounds.children.append(object_to_bound(child))
    
    return BoundsFile(bounds)


def object_to_bound(obj) -> GeometryBVH:
    bound = GeometryBVH()
    init_bounds(bound, obj)

    for prop in dir(obj.composite_flags1):
        value = getattr(obj.composite_flags1, prop)
        if value == True:
            bound.composite_flags1.append(prop.upper())
    
    for prop in dir(obj.composite_flags2):
        value = getattr(obj.composite_flags2, prop)
        if value == True:
            bound.composite_flags2.append(prop.upper())

    vertex_index = 0

    if obj.sollum_type == "sollumz_bound_geometrybvh":
        mesh = obj.to_mesh()
        mesh.calc_normals_split()
        mesh.calc_loop_triangles()

        for face in mesh.loop_triangles:
            for face_vert in face.vertices:
                vertex = obj.matrix_world @ mesh.vertices[face_vert].co
                bound.vertices.append(vertex)

            vertex_index += 3

            triangle = Triangle()
            triangle.material_index = 0
            triangle.v1 = vertex_index - 3
            triangle.v2 = vertex_index - 2
            triangle.v3 = vertex_index - 1
            bound.polygons.append(triangle)

        bound.polygons.append(triangle)

    return bound

class ExportYbnXml(bpy.types.Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ybn"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ybn Xml (.ybn.xml)"

    # ExportHelper mixin class uses this
    filename_ext = ".ybn.xml"
    check_extension = False

    def execute(self, context):

        objects = bpy.context.collection.objects

        if(len(objects) == 0):
            return "No objects in scene for Sollumz export"

        for obj in objects:
            if(obj.sollum_type == "sollumz_bound_composite"):
                composite = object_to_composite(obj)

                print("")
                print("EXPORTING YBN")
                print("")
                #for child in composite.children:
                    #print(len(child.vertices))
                    #print(child.__dict__)
                    #for p in child.polygons:
                        #print(p.__dict__)
                # print(composite.composite_flags1)
                composite.write_xml(self.filepath)

        return {'FINISHED'}

def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname, text="Export .ybn.xml")