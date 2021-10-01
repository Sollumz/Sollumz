from abc import ABC as AbstractClass, abstractmethod
from xml.etree import ElementTree as ET
import bpy
import bmesh
from bpy.types import Object as BlenderObject, Mesh
from .cwxml import GTAObject, AttributeProperty, ListProperty, VectorProperty, ValueProperty, VerticesProperty, QuaternionProperty, FlagsProperty
from meshhelper import get_total_bbs, get_bound_center, get_children_recursive, get_obj_radius
from mathutils import Vector, Quaternion
from .polygon import Box, Sphere, Capsule, Triangle, Cylinder, PolygonsProperty, PolygonType
from enum import Enum


class BoundType(str, Enum):
    BOX = 'sollumz_bound_box'
    SPHERE = 'sollumz_bound_sphere'
    CAPSULE = 'sollumz_bound_capsule'
    CYLINDER = 'sollumz_bound_cylinder'
    DISC = 'sollumz_bound_disc'
    CLOTH = 'sollumz_bound_cloth'
    GEOMETRY = 'sollumz_bound_geometry'
    GEOMETRYBVH = 'sollumz_bound_geometrybvh'
    COMPOSITE = 'sollumz_bound_composite'


class YBN(GTAObject):
    tag_name = 'BoundsFile'

    def __init__(self):
        super().__init__()
        self.bounds = BoundComposite()
    
    def load_obj(self, obj: BlenderObject):
        self.bounds.load_obj(obj)

        return self
    
    def to_obj(self, name: str) -> BlenderObject:
        obj = self.bounds.to_obj(name)
        bpy.context.collection.objects.link(obj)
        return obj


class Bounds(GTAObject):
    tag_name = 'Bounds'

    def __init__(self):
        super().__init__()
        self.box_min = VectorProperty('BoxMin')
        self.box_max = VectorProperty('BoxMax')
        self.box_center = VectorProperty('BoxCenter')
        self.sphere_center = VectorProperty('SphereCenter')
        self.sphere_radius = ValueProperty('SphereRadius', 0.0)
        self.margin = ValueProperty('Margin', 0)
        self.volume = ValueProperty('Volume', 0)
        self.inertia = VectorProperty('Inertia')
        self.material_index = ValueProperty('MaterialIndex', 0)
        self.material_color_index = ValueProperty('MaterialColourIndex', 0)
        self.procedural_id = ValueProperty('ProceduralId', 0)
        self.room_id = ValueProperty('RoomId', 0)
        self.ped_density = ValueProperty('PedDensity', 0)
        self.unk_flags = ValueProperty('UnkFlags', 0)
        self.poly_flags = ValueProperty('PolyFlags', 0)
        self.unk_type = ValueProperty('UnkType', 0)
    
    def load_obj(self, obj: BlenderObject):
        bbs = get_total_bbs(obj)
        self.box_min = bbs[0]
        self.box_max = bbs[1]
        self.box_center = get_bound_center(obj)
        self.sphere_center = get_bound_center(obj)
        self.sphere_radius = get_obj_radius(obj)
        self.procedural_id = obj.bound_properties.procedural_id
        self.room_id = obj.bound_properties.room_id
        self.ped_density = obj.bound_properties.ped_density
        self.poly_flags = obj.bound_properties.poly_flags

        return self


class BoundComposite(Bounds):
    def __init__(self):
        super().__init__()
        self.type = AttributeProperty('type', 'Composite')
        self.children = BoundListProperty()
    
    def load_obj(self, obj: BlenderObject):
        super().load_obj(obj)

        for child in get_children_recursive(obj):
            if child.sollum_type == BoundType.BOX:
                self.children.append(BoundBox().load_obj(child))
            elif child.sollum_type == BoundType.SPHERE:
                self.children.append(BoundSphere().load_obj(child))
            elif child.sollum_type == BoundType.CAPSULE:
                self.children.append(BoundCapsule().load_obj(child))
            elif child.sollum_type == BoundType.CYLINDER:
                self.children.append(BoundCylinder().load_obj(child))
            elif child.sollum_type == BoundType.DISC:
                self.children.append(BoundDisc().load_obj(child))
            elif child.sollum_type == BoundType.CLOTH:
                self.children.append(BoundCloth().load_obj(child))
            elif child.sollum_type == BoundType.GEOMETRY:
                self.children.append(BoundGeometry().load_obj(child))
            elif child.sollum_type == BoundType.GEOMETRYBVH:
                self.children.append(BoundGeometryBVH().load_obj(child))

        return self

    
    def to_obj(self, name: str) -> BlenderObject:
        obj = bpy.data.objects.new(name, None)
        obj.sollum_type = BoundType.COMPOSITE

        for child in self.children:
            child_obj = child.to_obj()
            if not child_obj:
                continue
            child_obj.parent = obj

        return obj


class BoundItem(Bounds, AbstractClass):
    tag_name = 'Item'

    @property
    @abstractmethod
    def type(self) -> str:
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.type = AttributeProperty('type', self.type)
        self.composite_position = VectorProperty('CompositePosition')
        self.composite_rotation = QuaternionProperty('CompositeRotation')
        self.composite_scale = VectorProperty('CompositeScale', Vector([1, 1, 1]))
        self.composite_flags1 = FlagsProperty('CompositeFlags1')
        self.composite_flags2 = FlagsProperty('CompositeFlags2')
    
    def load_obj(self, obj: BlenderObject):
        super().load_obj(obj)

        # Get flags from object
        for prop in dir(obj.composite_flags1):
            value = getattr(obj.composite_flags1, prop)
            if value == True:
                self.composite_flags1.append(prop.upper())
    
        for prop in dir(obj.composite_flags2):
            value = getattr(obj.composite_flags2, prop)
            if value == True:
                self.composite_flags2.append(prop.upper())

        return self
    
    # @property
    # @abstractmethod
    # def sollum_type(self):
    #     raise NotImplementedError

    # @abstractmethod
    def to_obj(self) -> BlenderObject:
        if self.sollum_type:
            obj = bpy.data.objects.new(self.sollum_type.value, None)
            obj.sollum_type = self.sollum_type.value

            obj.bound_properties.procedural_id = int(self.procedural_id)
            obj.bound_properties.room_id = int(self.room_id)
            obj.bound_properties.ped_density = int(self.ped_density)
            obj.bound_properties.ped_density = int(self.poly_flags)

            #assign obj composite flags
            for prop in dir(obj.composite_flags1):
                for f in self.composite_flags1:
                    if f.lower() == prop:
                        setattr(obj.composite_flags1, prop, True)  

            for prop in dir(obj.composite_flags2):
                for f in self.composite_flags2:
                    if f.lower() == prop:
                        setattr(obj.composite_flags2, prop, True)

            obj.location = self.composite_position
            obj.rotation_euler  = self.composite_rotation.to_euler()
            obj.scale = self.composite_scale

            bpy.context.collection.objects.link(obj)
            return obj


class BoundBox(BoundItem):
    type = 'Box'
    sollum_type = BoundType.BOX

    def __init__(self):
        super().__init__()


class BoundSphere(BoundItem):
    type = 'Sphere'
    sollum_type = BoundType.SPHERE

    def __init__(self):
        super().__init__()



# TODO
class BoundCapsule(BoundItem):
    type = 'Capsule'
    sollum_type = BoundType.CAPSULE

    def __init__(self):
        super().__init__()



class BoundCylinder(BoundItem):
    type = 'Cylinder'
    sollum_type = BoundType.CYLINDER

    def __init__(self):
        super().__init__()


# TODO
class BoundDisc(BoundItem):
    type = 'Disc'
    sollum_type = BoundType.DISC

    def __init__(self):
        super().__init__()
    

# TODO
class BoundCloth(BoundItem):
    type = 'Cloth'
    sollum_type = BoundType.CLOTH

    def __init__(self):
        super().__init__()


# TODO
class BoundGeometry(BoundItem):
    type = 'Geometry'
    sollum_type = BoundType.GEOMETRY

    def __init__(self):
        super().__init__()


class BoundGeometryBVH(BoundItem):
    type = 'GeometryBVH'
    sollum_type = BoundType.GEOMETRYBVH

    def __init__(self):
        super().__init__()
        self.geometry_center = VectorProperty('GeometryCenter')
        self.materials = MaterialsListProperty()
        self.vertices = VerticesProperty('Vertices')
        self.polygons = PolygonsProperty()
    
    def load_obj(self, obj: BlenderObject):
        super().load_obj(obj)

        mesh = obj.to_mesh()
        mesh.calc_normals_split()
        mesh.calc_loop_triangles()

        # Get vertices from object
        for face in mesh.loop_triangles:
            for face_vert in face.vertices:
                vertex = obj.matrix_world @ mesh.vertices[face_vert].co
                self.vertices.append(vertex)
            self.polygons.append(Triangle().load_obj(face))

        # Get child poly bounds
        for child in get_children_recursive(obj):
            if child.sollum_type == PolygonType.BOX:
                self.polygons.append(Box().load_obj(child))
            elif child.sollum_type == PolygonType.SPHERE:
                self.polygons.append(Sphere().load_obj(child))
            elif child.sollum_type == PolygonType.CAPSULE:
                self.polygons.append(Capsule().load_obj(child))
            elif child.sollum_type == PolygonType.CYLINDER:
                self.polygons.append(Cylinder().load_obj(child))
        
        return self
    
    def to_obj(self) -> BlenderObject:
        obj = super().to_obj()

        # materials = []
        # for gmat in self.materials:
        #     mat = create_collision_material_from_index(gmat.type)
        #     mat.sollum_type = "sollumz_gta_collision_material"
        #     mat.collision_properties.procedural_id = gmat.procedural_id
        #     mat.collision_properties.room_id = gmat.room_id
        #     mat.collision_properties.ped_density = gmat.ped_density
        #     mat.collision_properties.material_color_index = gmat.material_color_index
            
        #     #assign flags 
        #     for prop in dir(mat.collision_properties):
        #         for f in gmat.flags:
        #             if(f[5:].lower() == prop):
        #                 setattr(mat.collision_properties, prop, True)

        #     materials.append(mat)

        allvertices = []
        tvertices = []
        tindicies = []
        material_idxs = []
        for vert in self.vertices:
            allvertices.append(Vector((vert[0], vert[1], vert[2])))

        poly_objs = []
        tidx = 0
        for poly in self.polygons:
            if(poly.type == "Triangle"):
                #poly_objs.append(bound_poly_triangle_to_blender(poly)) cant use this TO SLOW
                tidx += 3
                inds = []
                inds.append(tidx - 3)    
                inds.append(tidx - 2)    
                inds.append(tidx - 1)    
                tvertices.append(allvertices[poly.v1])
                tvertices.append(allvertices[poly.v2])
                tvertices.append(allvertices[poly.v3])
                tindicies.append(inds)
                material_idxs.append(poly.material_index)

        #create triangle mesh
        if(len(tvertices) != 0):
            mesh = bpy.data.meshes.new("TriangleMesh")
            mesh.from_pydata(tvertices, [], tindicies)
            
            # for mat in materials:
            #     mesh.materials.append(mat)
            for idx in range(len(mesh.polygons)):
                mesh.polygons[idx].material_index = material_idxs[idx]

            triangle_obj = bpy.data.objects.new("Triangle", mesh)  
            bpy.context.collection.objects.link(triangle_obj)
            triangle_obj.sollum_type = "sollumz_bound_poly_triangle"
            triangle_obj.parent = obj

        for poly in poly_objs:
            bpy.context.collection.objects.link(poly)
            poly.parent = obj

        obj.location += Vector((self.geometry_center[0], self.geometry_center[1], self.geometry_center[2]))

        return obj


class BoundListProperty(ListProperty):
    list_type = BoundItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Children', value=value or [])
    
    @staticmethod
    def from_xml(element: ET.Element):
        new = BoundListProperty()

        for child in element.iter():
            if 'type' in child.attrib:
                bound_type = child.get('type')
                if bound_type == 'Box':
                    new.value.append(BoundBox.from_xml(child))
                elif bound_type == 'Sphere':
                    new.value.append(BoundSphere.from_xml(child))
                elif bound_type == 'Capsule':
                    new.value.append(BoundCapsule.from_xml(child))
                elif bound_type == 'Cylinder':
                    new.value.append(BoundCylinder.from_xml(child))
                elif bound_type == 'Disc':
                    new.value.append(BoundDisc.from_xml(child))
                elif bound_type == 'Cloth':
                    new.value.append(BoundCloth.from_xml(child))
                elif bound_type == 'Geometry':
                    new.value.append(BoundGeometry.from_xml(child))
                elif bound_type == 'GeometryBVH':
                    new.value.append(BoundGeometryBVH.from_xml(child))

        return new


class MaterialItem(GTAObject):
    tag_name = 'Item'

    def __init__(self):
        super().__init__()
        self.type = ValueProperty('Type', 0)
        self.procedural_id = ValueProperty('ProceduralId', 0)
        self.room_id = ValueProperty('RoomId', 0)
        self.ped_density = ValueProperty('PedDensity', 0)
        self.flags = FlagsProperty()
        self.material_color_index = ValueProperty('MaterialColourIndex', 0)
        self.unk = ValueProperty('Unk', 0)


class MaterialsListProperty(ListProperty):
    list_type = MaterialItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Materials', value=value or [])