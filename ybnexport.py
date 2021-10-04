import bpy
from bpy_extras.io_utils import ExportHelper
import os, sys

from Sollumz.sollumz_properties import CollisionFlags
sys.path.append(os.path.dirname(__file__))
from Sollumz.resources.bound import *
from meshhelper import *


def init_poly_bound(poly_bound, obj):
    materials = obj.parent.data.materials.values()
    mat_index = materials.index(obj.active_material)
    poly_bound.material_index = mat_index

    return poly_bound

def polygon_from_object(poly_type, obj, vertices):
    if obj.sollum_type == PolygonType.BOX:
        box = init_poly_bound(Box(), obj)
        indices = []
        bound_box = get_bound_world(obj)
        neighbors = [bound_box[0], bound_box[5], bound_box[2], bound_box[7]]
        for vert in neighbors:
            vertices.append(vert)
            indices.append(len(vertices) - 1)

        box.v1 = indices[0]
        box.v2 = indices[1]
        box.v3 = indices[2]
        box.v4 = indices[3]

        return box
    elif obj.sollum_type == PolygonType.SPHERE:
        sphere = init_poly_bound(Sphere(), obj)
        vertices.append(obj.location)
        sphere.v = len(vertices) - 1
        sphere.radius = get_obj_radius(obj)
        
        return sphere
    elif obj.sollum_type == PolygonType.CAPSULE:
        capsule = init_poly_bound(Capsule(), obj)
        # Same method for getting verts as cylinder
        cylinder = polygon_from_object(PolygonType.CYLINDER, obj, vertices)

        capsule.v1 = cylinder.data.v1
        capsule.v2 = cylinder.data.v2
        capsule.radius = cylinder.data.radius
        
        return cylinder
    elif obj.sollum_type == PolygonType.CYLINDER:
        cylinder = init_poly_bound(Cylinder(), obj)
        bound_box = get_bound_world(obj)
        # Get bound height
        height = get_distance_of_vectors(bound_box[0], bound_box[1])
        distance = Vector((0, 0, height / 2))
        center = get_bound_center(obj)
        radius = get_distance_of_vectors(bound_box[1], bound_box[2]) / 2
        v1 = center - distance
        v2 = center + distance
        vertices.append(v1)
        vertices.append(v2)

        cylinder.v1 = len(vertices) - 2
        cylinder.v2 = len(vertices) - 1

        cylinder.radius = radius

        return cylinder

def triangle_from_face(face):
    triangle = Triangle()
    triangle.material_index = face.material_index

    triangle.v1 = face.vertices[0]
    triangle.v2 = face.vertices[1]
    triangle.v3 = face.vertices[2]

    return triangle


def geometry_from_object(obj, sollum_type=BoundType.GEOMETRYBVH):
    geometry = None

    if sollum_type == BoundType.GEOMETRYBVH:
        geometry = BoundGeometryBVH()
    elif sollum_type == BoundType.GEOMETRY:
        geometry = BoundGeometry()
    else:
        return ValueError('Invalid argument for geometry sollum_type!')

    geometry = init_bound_item(geometry, obj)
    geometry.geometry_center = get_bound_center(obj, True)

    mesh = obj.to_mesh()
    mesh.calc_normals_split()
    mesh.calc_loop_triangles()

    for vertex in mesh.vertices:
        geometry.vertices.append(obj.matrix_world @ vertex.co)

    for face in mesh.loop_triangles:
        geometry.polygons.append(triangle_from_face(face))
    
    for material in mesh.materials:
        if material.sollum_type == "sollumz_gta_collision_material":
            mat_item = MaterialItem()
            mat_item.type = material.collision_properties.collision_index
            mat_item.procedural_id = material.collision_properties.procedural_id
            mat_item.room_id = material.collision_properties.room_id
            mat_item.ped_density = material.collision_properties.ped_density
            mat_item.material_color_index = material.collision_properties.material_color_index
            
            # Assign flags
            for flag_name in CollisionFlags.__annotations__.keys():
                flag_exists = getattr(material.collision_properties, flag_name)
                if flag_exists == True:
                    mat_item.flags.append(f"FLAG_{flag_name.upper()}")
            geometry.materials.append(mat_item)


    # Get child poly bounds
    for child in get_children_recursive(obj):
        geometry.polygons.append(polygon_from_object(obj.sollum_type, child, geometry.vertices))
    
    return geometry

def init_bound_item(bound_item, obj):
    init_bound(bound_item, obj)
    # Get flags from object
    for prop in dir(obj.composite_flags1):
        value = getattr(obj.composite_flags1, prop)
        if value == True:
            bound_item.composite_flags1.append(prop.upper())

    for prop in dir(obj.composite_flags2):
        value = getattr(obj.composite_flags2, prop)
        if value == True:
            bound_item.composite_flags2.append(prop.upper())

    return bound_item

def init_bound(bound, obj):
    bb_min, bb_max = get_bb_extents(obj)
    bound.box_min = bb_min
    bound.box_max = bb_max
    bound.box_center = get_bound_center(obj)
    bound.sphere_center = get_bound_center(obj)
    bound.sphere_radius = get_obj_radius(obj)
    bound.procedural_id = obj.bound_properties.procedural_id
    bound.room_id = obj.bound_properties.room_id
    bound.ped_density = obj.bound_properties.ped_density
    bound.poly_flags = obj.bound_properties.poly_flags

    return bound

def bound_from_object(obj):
    if obj.sollum_type == BoundType.BOX:
        raise NotImplementedError
    elif obj.sollum_type == BoundType.SPHERE:
        raise NotImplementedError
    elif obj.sollum_type == BoundType.CAPSULE:
        raise NotImplementedError
    elif obj.sollum_type == BoundType.CYLINDER:
        raise NotImplementedError
    elif obj.sollum_type == BoundType.DISC:
        raise NotImplementedError
    elif obj.sollum_type == BoundType.CLOTH:
        raise NotImplementedError
    elif obj.sollum_type == BoundType.GEOMETRY:
        return geometry_from_object(obj, BoundType.GEOMETRY)
    elif obj.sollum_type == BoundType.GEOMETRYBVH:
        return geometry_from_object(obj)

def ybn_from_object(obj):
    ybn = YBN()
    init_bound(ybn.bounds, obj)

    for child in get_children_recursive(obj):
        bound = bound_from_object(child)
        if bound:
            ybn.bounds.children.append(bound)
    
    return ybn
    
    

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

        print('Exporting')
        for obj in objects:
            if(obj.sollum_type == "sollumz_bound_composite"):
                ybn_from_object(obj).write_xml(self.filepath)

        return {'FINISHED'}

def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname, text="Export .ybn.xml")