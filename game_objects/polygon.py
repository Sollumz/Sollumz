import bpy
import bmesh
from xml.etree import ElementTree as ET
from abc import ABC as AbstractClass
from bpy.types import MeshLoopTriangle, Object as BlenderObject
from .gameobject import GameObject
from Sollumz.codewalker_xml.polygon_xml import *
from Sollumz.meshhelper import *
from mathutils import Vector, Matrix
from enum import Enum


class PolygonType(str, Enum):
    BOX = 'sollumz_bound_poly_box'
    SPHERE = 'sollumz_bound__poly_sphere'
    CAPSULE = 'sollumz_bound_poly_capsule'
    CYLINDER = 'sollumz_bound_poly_cylinder'
    TRIANGLE = 'sollumz_bound_poly_triangle'


class Polygon(GameObject, AbstractClass):
    def __init__(self, data: Polygon_XML) -> None:
        super().__init__(data)
    
    @classmethod
    def from_obj(cls, obj: BlenderObject):
        self: Polygon_XML = cls()
        materials = obj.parent.data.materials.values()
        mat_index = materials.index(obj.active_material)
        self.data.material_index = mat_index

        return self

    def to_obj(self, materials) -> BlenderObject:
        mesh = bpy.data.meshes.new(self.sollum_type.value)
        if self.data.material_index < len(materials):
            mesh.materials.append(materials[self.data.material_index])

        obj = bpy.data.objects.new(self.sollum_type.value, mesh)
        obj.sollum_type = self.sollum_type.value

        return obj


class Triangle(Polygon):
    sollum_type = PolygonType.TRIANGLE

    def __init__(self, data: Triangle_XML = None) -> None:
        super().__init__(data or Triangle_XML())
    
    @classmethod
    def from_obj(cls, obj: MeshLoopTriangle):
        self = Triangle()
        self.data.material_index = obj.material_index

        self.data.v1 = obj.vertices[0]
        self.data.v2 = obj.vertices[1]
        self.data.v3 = obj.vertices[2]

        return self
    

class Sphere(Polygon):
    sollum_type = PolygonType.SPHERE

    def __init__(self, data: Sphere_XML = None) -> None:
        super().__init__(data or Sphere_XML())
    
    @classmethod
    def from_obj(cls, obj: BlenderObject, vertices):
        self = super().from_obj(obj)
        vertices.append(obj.location)
        self.data.v = len(vertices) - 1
        self.data.radius = get_obj_radius(obj)
        
        return self
    
    def to_obj(self, materials):
        obj = super().to_obj(materials)
        mesh = obj.data
        bound_sphere(mesh, self.data.radius)

    

class Capsule(Polygon):
    sollum_type = PolygonType.CAPSULE

    def __init__(self, data: Capsule_XML = None) -> None:
        super().__init__(data or Capsule_XML())
    
    @classmethod
    def from_obj(cls, obj: BlenderObject, vertices):
        self = super().from_obj(obj)
        cylinder = Cylinder().from_obj(obj, vertices)

        self.data.v1 = cylinder.data.v1
        self.data.v2 = cylinder.data.v2
        self.data.radius = cylinder.data.radius
        
        return self
    
    def to_obj(self, vertices, materials) -> BlenderObject:
        obj = super().to_obj(materials)

        v1 = vertices[self.data.v1]
        v2 = vertices[self.data.v2]
        length = get_distance_of_vectors(v1, v2)    
        rot = get_direction_of_vectors(v1, v2)
        
        mesh = obj.data
        bound_capsule(mesh, self.data.radius, length)
        
        obj.location = (v1 + v2) / 2     
        obj.rotation_euler = rot
        
        return obj


class Box(Polygon):
    sollum_type = PolygonType.BOX

    def __init__(self, data: Box_XML = None) -> None:
        super().__init__(data or Box_XML())
    
    @classmethod
    def from_obj(cls, obj: BlenderObject, vertices: list):
        self = super().from_obj(obj)

        indices = []
        bound_box = get_bound_world(obj)
        neighbors = [bound_box[0], bound_box[5], bound_box[2], bound_box[7]]
        for vert in neighbors:
            vertices.append(vert)
            indices.append(len(vertices) - 1)

        self.data.v1 = indices[0]
        self.data.v2 = indices[1]
        self.data.v3 = indices[2]
        self.data.v4 = indices[3]

        return self

    def to_obj(self, vertices, materials) -> BlenderObject:
        obj = super().to_obj(materials)
        v1 = vertices[self.data.v1]
        v2 = vertices[self.data.v2]
        v3 = vertices[self.data.v3]
        v4 = vertices[self.data.v4]

        cf1 = (v1 + v2) / 2
        cf2 = (v3 + v4) / 2
        cf3 = (v1 + v4) / 2
        cf4 = (v2 + v3) / 2
        cf5 = (v1 + v3) / 2
        cf6 = (v2 + v4) / 2

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

        mesh = obj.data
        bm = bmesh.new()
        bmesh.ops.create_cube(bm, size=1)
        bm.to_mesh(mesh)
        bm.free()

        obj.location = center
        obj.rotation_euler = rotation
        obj.scale = scale

        return obj



class Cylinder(Polygon):
    sollum_type = PolygonType.CYLINDER

    def __init__(self, data: Cylinder_XML = None) -> None:
        super().__init__(data or Cylinder_XML())
    
    @classmethod
    def from_obj(cls, obj: BlenderObject, vertices):
        self = super().from_obj(obj)
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

        self.data.v1 = len(vertices) - 2
        self.data.v2 = len(vertices) - 1

        self.data.radius = radius

        return self
    
    def to_obj(self, vertices, materials) -> BlenderObject:
        obj = super().to_obj(materials)
        v1 = vertices[self.data.v1]
        v2 = vertices[self.data.v2]

        length = get_distance_of_vectors(v1, v2)
        rot = get_direction_of_vectors(v1, v2)

        obj.data = bound_cylinder(obj.data, self.data.radius, length)

        obj.location = (v1 + v2) / 2
        obj.rotation_euler = rot

        return obj