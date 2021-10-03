import os
import bpy
from bpy_extras.io_utils import ImportHelper
from Sollumz.resources.bound import *

def init_poly_obj(poly, sollum_type, materials):
    mesh = bpy.data.meshes.new(sollum_type.value)
    if poly.material_index < len(materials):
        mesh.materials.append(materials[poly.material_index])

    obj = bpy.data.objects.new(sollum_type.value, mesh)
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
        bound_sphere(mesh, poly.radius)

        return sphere
    elif type(poly) == Capsule:
        capsule = init_poly_obj(poly, PolygonType.CAPSULE, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]
        length = get_distance_of_vectors(v1, v2)    
        rot = get_direction_of_vectors(v1, v2)
        
        mesh = capsule.data
        bound_capsule(mesh, poly.radius, length)
        
        capsule.location = (v1 + v2) / 2     
        capsule.rotation_euler = rot
        
        return capsule
    elif type(poly) == Cylinder:
        cylinder = init_poly_obj(poly, PolygonType.CYLINDER, materials)
        v1 = vertices[poly.v1]
        v2 = vertices[poly.v2]

        length = get_distance_of_vectors(v1, v2)
        rot = get_direction_of_vectors(v1, v2)

        cylinder.data = bound_cylinder(cylinder.data, poly.radius, length)

        cylinder.location = (v1 + v2) / 2
        cylinder.rotation_euler = rot

        return cylinder

def bvh_to_obj(bvh):
    obj = init_bound_obj(bvh, BoundType.GEOMETRYBVH)
    for gmat in bvh.materials:
        mat = create_collision_material_from_index(gmat.type)
        mat.sollum_type = "sollumz_gta_collision_material"
        mat.collision_properties.procedural_id = gmat.procedural_id
        mat.collision_properties.room_id = gmat.room_id
        mat.collision_properties.ped_density = gmat.ped_density
        mat.collision_properties.material_color_index = gmat.material_color_index
        
        #assign flags 
        for prop in dir(mat.collision_properties):
            for f in gmat.flags:
                if(f[5:].lower() == prop):
                    setattr(mat.collision_properties, prop, True)

        obj.data.materials.append(mat)

    vertices = []
    faces = []
    tri_materials = []

    for poly in bvh.polygons:
        if type(poly) == Triangle:
            tri_materials.append(poly.material_index)
            face = []
            v1 = bvh.vertices[poly.v1]
            v2 = bvh.vertices[poly.v2]
            v3 = bvh.vertices[poly.v3]
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
            poly_obj = poly_to_obj(poly, obj.data.materials, bvh.vertices)
            if poly_obj:
                bpy.context.collection.objects.link(poly_obj)
                poly_obj.parent = obj

    obj.data.from_pydata(vertices, [], faces)

    # Apply triangle materials
    for index, poly in obj.data.polygons.items():
        if tri_materials[index]:
            poly.material_index = tri_materials[index]

    obj.location = bvh.geometry_center

    return obj

def init_bound_obj(bound, sollum_type):
    mesh = bpy.data.meshes.new(sollum_type.value)
    obj = bpy.data.objects.new(sollum_type.value, mesh)
    obj.sollum_type = sollum_type.value

    obj.bound_properties.procedural_id = int(bound.procedural_id)
    obj.bound_properties.room_id = int(bound.room_id)
    obj.bound_properties.ped_density = int(bound.ped_density)
    obj.bound_properties.ped_density = int(bound.poly_flags)

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
    obj.rotation_euler  = bound.composite_rotation.to_euler()
    obj.scale = bound.composite_scale

    bpy.context.collection.objects.link(obj)

    return obj

def bound_to_obj(bound):
    if bound.type == 'Box':
        obj = init_bound_obj(bound, BoundType.BOX)
        return obj
    elif bound.type == 'Sphere':
        sphere = init_bound_obj(bound, BoundType.SPHERE)
        return sphere
    elif bound.type == 'Capsule':
        capsule = init_bound_obj(bound, BoundType.CAPSULE)
        return capsule
    elif bound.type == 'Cylinder':
        cylinder = init_bound_obj(bound, BoundType.CYLINDER)
        return cylinder
    elif bound.type == 'Disc':
        disc = init_bound_obj(bound, BoundType.DISC)
        return disc
    elif bound.type == 'Cloth':
        cloth = init_bound_obj(bound, BoundType.CLOTH)
        return cloth
    elif bound.type == 'Geometry':
        geometry = init_bound_obj(bound, BoundType.GEOMETRY)
        return geometry
    elif bound.type == 'GeometryBVH':
        bvh = bvh_to_obj(bound)
        return bvh

def composite_to_obj(composite, name):
    obj = bpy.data.objects.new(name, None)
    obj.sollum_type = BoundType.COMPOSITE

    for child in composite.children:
        child_obj = bound_to_obj(child)
        if child_obj:
            child_obj.parent = obj

    return obj

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
        
        ybn_xml = YBN.from_xml_file(self.filepath)
        ybn_obj = composite_to_obj(ybn_xml.bounds, os.path.basename(self.filepath))
        bpy.context.collection.objects.link(ybn_obj)

        return {'FINISHED'}

def ybn_menu_func_import(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Import .ybn.xml")
