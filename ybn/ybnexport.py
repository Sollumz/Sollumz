import bpy
import traceback
from .properties import CollisionMatFlags
from Sollumz.resources.bound import *
from Sollumz.meshhelper import *
from Sollumz.sollumz_properties import BoundType, PolygonType, MaterialType
from Sollumz.sollumz_operators import SollumzExportHelper

class NoGeometryError(Exception):
    message = 'Sollumz Geometry has no geometry!'

def init_poly_bound(poly_bound, obj, materials):
    # materials = obj.parent.data.materials.values()
    mat_index = 0
    try:
        mat_index = materials.index(obj.active_material)
    except:
        add_material(obj.active_material, materials)
        mat_index = len(materials) - 1
    poly_bound.material_index = mat_index

    return poly_bound

def add_material(material, materials):
    if material and material.sollum_type == MaterialType.COLLISION:
        mat_item = MaterialItem()
        mat_item.type = material.collision_properties.collision_index
        mat_item.procedural_id = material.collision_properties.procedural_id
        mat_item.room_id = material.collision_properties.room_id
        mat_item.ped_density = material.collision_properties.ped_density
        mat_item.material_color_index = material.collision_properties.material_color_index
        
        # Assign flags
        for flag_name in CollisionMatFlags.__annotations__.keys():
            # flag_exists = getattr(material.collision_flags, flag_name)
            if flag_name in material.collision_flags:
                mat_item.flags.append(f"FLAG_{flag_name.upper()}")

        materials.append(mat_item)

def polygon_from_object(obj, vertices, materials, geom_center):
    world_pos = obj.matrix_world.to_translation()
    if obj.sollum_type == PolygonType.BOX:
        box = init_poly_bound(Box(), obj, materials)
        indices = []
        bound_box = get_bound_world(obj)

        corners = [bound_box[0], bound_box[5], bound_box[2], bound_box[7]]
        for vert in corners:
            vertices.append(vert - geom_center)
            indices.append(len(vertices) - 1)

        box.v1 = indices[0]
        box.v2 = indices[1]
        box.v3 = indices[2]
        box.v4 = indices[3]

        return box
    elif obj.sollum_type == PolygonType.SPHERE:
        sphere = init_poly_bound(Sphere(), obj, materials)
        vertices.append(world_pos - geom_center)
        sphere.v = len(vertices) - 1
        bound_box = get_bound_world(obj)

        radius = get_distance_of_vectors(bound_box[1], bound_box[2]) / 2

        sphere.radius = radius
        
        return sphere
    elif obj.sollum_type == PolygonType.CYLINDER or obj.sollum_type == PolygonType.CAPSULE:
        bound = None
        if obj.sollum_type == PolygonType.CYLINDER:
            bound = init_poly_bound(Cylinder(), obj, materials)
        elif obj.sollum_type == PolygonType.CAPSULE:
            bound = init_poly_bound(Capsule(), obj, materials)

        bound_box = get_bound_world(obj)

        # Get bound height
        height = get_distance_of_vectors(bound_box[0], bound_box[1])
        radius = get_distance_of_vectors(bound_box[1], bound_box[2]) / 2

        if obj.sollum_type == PolygonType.CAPSULE:
            height = height - (radius * 2)

        vertical = Vector((0, 0, height / 2))
        vertical.rotate(obj.matrix_world.to_euler('XYZ')) 
        
        v1 = world_pos - vertical
        v2 = world_pos + vertical


        vertices.append(v1 - geom_center)
        vertices.append(v2 - geom_center)

        bound.v1 = len(vertices) - 2
        bound.v2 = len(vertices) - 1

        bound.radius = radius

        return bound

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
    geometry.geometry_center = obj.location
    geometry.composite_position = Vector()

    # Ensure object has geometry
    found = False

    # Get child poly bounds
    for child in get_children_recursive(obj):
        if child.sollum_type == PolygonType.TRIANGLE:
            found = True
            mesh = child.to_mesh()
            mesh.calc_normals_split()
            mesh.calc_loop_triangles()

            for material in mesh.materials:
                add_material(material, geometry.materials)

            for vertex in mesh.vertices:
                geometry.vertices.append((child.matrix_world @ vertex.co) - geometry.geometry_center)

            for face in mesh.loop_triangles:
                geometry.polygons.append(triangle_from_face(face))
            

    for child in get_children_recursive(obj):
        poly = polygon_from_object(child, geometry.vertices, geometry.materials, geometry.geometry_center)
        if poly:
            found = True
            geometry.polygons.append(poly)
    
    if not found:
        raise NoGeometryError()

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
    
    bound_item.composite_position = obj.location
    bound_item.composite_rotation = obj.rotation_euler.to_quaternion().normalized()
    bound_item.composite_scale = Vector([1, 1, 1])

    return bound_item

def init_bound(bound, obj):
    bb_min, bb_max = get_bb_extents(obj)
    bound.box_min = bb_min
    bound.box_max = bb_max
    center = get_bound_center(obj)
    bound.box_center = center
    bound.sphere_center = center
    bound.sphere_radius = get_obj_radius(obj)
    bound.procedural_id = obj.bound_properties.procedural_id
    bound.room_id = obj.bound_properties.room_id
    bound.ped_density = obj.bound_properties.ped_density
    bound.poly_flags = obj.bound_properties.poly_flags

    return bound

def bound_from_object(obj):
    if obj.sollum_type == BoundType.BOX:
        return init_bound_item(BoundBox(), obj)
    elif obj.sollum_type == BoundType.SPHERE:
        return init_bound_item(BoundSphere(), obj)
    elif obj.sollum_type == BoundType.CYLINDER:
        return init_bound_item(BoundCylinder(), obj)
    elif obj.sollum_type == BoundType.CAPSULE:
        return init_bound_item(BoundCapsule(), obj)
    elif obj.sollum_type == BoundType.DISC:
        return init_bound_item(BoundDisc(), obj)
    elif obj.sollum_type == BoundType.CLOTH:
        return init_bound_item(BoundCloth(), obj)
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

class ExportYbnXml(bpy.types.Operator, SollumzExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ybn" 
    bl_label = "Export Ybn Xml (.ybn.xml)"
    
    filename_ext = '.ybn.xml'

    def execute(self, context):

        objects = bpy.context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == BoundType.COMPOSITE and obj.enable_export:
                    found = True
                    try:
                        ybn_from_object(obj).write_xml(self.get_filepath(obj))
                        self.report({'INFO'}, 'YBN Successfully exported.')
                    except NoGeometryError:
                        self.report({'WARNING'}, f'{obj.name} was not exported: {NoGeometryError.message}')
                    except:
                        self.report({'ERROR'}, traceback.format_exc())
        
        if not found:
            self.report({'INFO'}, "No bound object types in scene for Sollumz export")

        return {'FINISHED'}
    

def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname, text="Export .ybn.xml")

def register():
    bpy.types.TOPBAR_MT_file_export.append(ybn_menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(ybn_menu_func_export)