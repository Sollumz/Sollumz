import bpy
from bpy.types import Object as BlenderObject
from .gameobject import GameObject
from Sollumz.meshhelper import *
from Sollumz.codewalker_xml.codewalker_xml import ElementTree
from Sollumz.codewalker_xml.bound_xml import *
from .polygon import *
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


class YBN(GameObject):
    def __init__(self, data: YBN_XML = None) -> None:
        super().__init__(data or YBN_XML())

    @classmethod
    def from_obj(cls, obj: BlenderObject):
        self = YBN()
        self.data.bounds = BoundComposite.from_obj(obj).data

        return self
    
    def to_obj(self, name: str) -> BlenderObject:
        obj = BoundComposite(self.data.bounds).to_obj(name)
        
        return obj


class Bounds(GameObject):
    def __init__(self, data: Bounds_XML = None) -> None:
        super().__init__(data or Bounds_XML())

    @classmethod
    def from_obj(cls, obj: BlenderObject):
        self = cls()
        bb_min, bb_max = get_bb_extents(obj)
        self.data.box_min = bb_min
        self.data.box_max = bb_max
        self.data.box_center = get_bound_center(obj)
        self.data.sphere_center = get_bound_center(obj)
        self.data.sphere_radius = get_obj_radius(obj)
        self.data.procedural_id = obj.bound_properties.procedural_id
        self.data.room_id = obj.bound_properties.room_id
        self.data.ped_density = obj.bound_properties.ped_density
        self.data.poly_flags = obj.bound_properties.poly_flags

        return self


class BoundComposite(Bounds):
    def __init__(self, data: BoundComposite_XML = None) -> None:
        super().__init__(data=data or BoundComposite_XML())

    @classmethod
    def from_obj(cls, obj: BlenderObject):
        self = super().from_obj(obj)

        for child in get_children_recursive(obj):
            if child.sollum_type == BoundType.BOX:
                self.data.children.append(BoundBox.from_obj(child).data)
            elif child.sollum_type == BoundType.SPHERE:
                self.data.children.append(BoundSphere.from_obj(child).data)
            elif child.sollum_type == BoundType.CAPSULE:
                self.data.children.append(BoundCapsule.from_obj(child).data)
            elif child.sollum_type == BoundType.CYLINDER:
                self.data.children.append(BoundCylinder.from_obj(child).data)
            elif child.sollum_type == BoundType.DISC:
                self.data.children.append(BoundDisc.from_obj(child).data)
            elif child.sollum_type == BoundType.CLOTH:
                self.data.children.append(BoundCloth.from_obj(child).data)
            elif child.sollum_type == BoundType.GEOMETRY:
                self.data.children.append(BoundGeometry.from_obj(child).data)
            elif child.sollum_type == BoundType.GEOMETRYBVH:
                self.data.children.append(BoundGeometryBVH.from_obj(child).data)

        return self

    
    def to_obj(self, name: str) -> BlenderObject:
        obj = bpy.data.objects.new(name, None)
        obj.sollum_type = BoundType.COMPOSITE

        for child in self.data.children:
            child_obj = None

            if child.type == 'Box':
                child_obj = BoundBox(child).to_obj()
            elif child.type == 'Sphere':
                child_obj = BoundSphere(child).to_obj()
            elif child.type == 'Capsule':
                child_obj = BoundCapsule(child).to_obj()
            elif child.type == 'Cylinder':
                child_obj = BoundCylinder(child).to_obj()
            elif child.type == 'Disc':
                child_obj = BoundDisc(child).to_obj()
            elif child.type == 'Cloth':
                child_obj = BoundCloth(child).to_obj()
            elif child.type == 'Geometry':
                child_obj = BoundGeometry(child).to_obj()
            elif child.type == 'GeometryBVH':
                child_obj = BoundGeometryBVH(child).to_obj()
            else:
                continue

            child_obj.parent = obj

        return obj


class BoundItem(Bounds):
    def __init__(self, data: BoundItem_XML) -> None:
        super().__init__(data=data)

    @classmethod
    def from_obj(cls, obj: BlenderObject):
        self = super().from_obj(obj)

        # Get flags from object
        for prop in dir(obj.composite_flags1):
            value = getattr(obj.composite_flags1, prop)
            if value == True:
                self.data.composite_flags1.append(prop.upper())
    
        for prop in dir(obj.composite_flags2):
            value = getattr(obj.composite_flags2, prop)
            if value == True:
                self.data.composite_flags2.append(prop.upper())

        return self


    def to_obj(self) -> BlenderObject:
        mesh = bpy.data.meshes.new(self.sollum_type.value)
        obj = bpy.data.objects.new(self.sollum_type.value, mesh)
        obj.sollum_type = self.sollum_type.value

        obj.bound_properties.procedural_id = int(self.data.procedural_id)
        obj.bound_properties.room_id = int(self.data.room_id)
        obj.bound_properties.ped_density = int(self.data.ped_density)
        obj.bound_properties.ped_density = int(self.data.poly_flags)

        #assign obj composite flags
        for prop in dir(obj.composite_flags1):
            for f in self.data.composite_flags1:
                if f.lower() == prop:
                    setattr(obj.composite_flags1, prop, True)  

        for prop in dir(obj.composite_flags2):
            for f in self.data.composite_flags2:
                if f.lower() == prop:
                    setattr(obj.composite_flags2, prop, True)

        obj.location = self.data.composite_position
        obj.rotation_euler  = self.data.composite_rotation.to_euler()
        obj.scale = self.data.composite_scale

        bpy.context.collection.objects.link(obj)

        return obj


class BoundBox(BoundItem):
    sollum_type = BoundType.BOX

    def __init__(self, data: BoundBox_XML = None) -> None:
        super().__init__(data or BoundBox_XML())


class BoundSphere(BoundItem):
    sollum_type = BoundType.SPHERE

    def __init__(self, data: BoundSphere_XML = None) -> None:
        super().__init__(data or BoundSphere_XML())


class BoundCylinder(BoundItem):
    sollum_type = BoundType.CYLINDER

    def __init__(self, data: BoundCylinder_XML = None) -> None:
        super().__init__(data or BoundCylinder_XML())


class BoundCapsule(BoundItem):
    sollum_type = BoundType.CAPSULE

    def __init__(self, data: BoundCapsule_XML = None) -> None:
        super().__init__(data or BoundCapsule_XML())


class BoundDisc(BoundItem):
    sollum_type = BoundType.DISC

    def __init__(self, data: BoundDisc_XML = None) -> None:
        super().__init__(data or BoundDisc_XML())


class BoundCloth(BoundItem):
    sollum_type = BoundType.CLOTH

    def __init__(self, data: BoundCloth_XML = None) -> None:
        super().__init__(data or BoundCloth_XML())


class BoundGeometry(BoundItem):
    sollum_type = BoundType.GEOMETRY

    def __init__(self, data: BoundGeometry_XML = None) -> None:
        super().__init__(data or BoundGeometry_XML())


class BoundGeometryBVH(BoundItem):
    sollum_type = BoundType.GEOMETRYBVH

    def __init__(self, data: BoundGeometryBVH_XML = None) -> None:
        super().__init__(data or BoundGeometryBVH_XML())
    
    @classmethod
    def from_obj(cls, obj: BlenderObject):
        self: BoundGeometryBVH = super().from_obj(obj)

        self.data.geometry_center = get_bound_center(obj, True)

        mesh = obj.to_mesh()
        mesh.calc_normals_split()
        mesh.calc_loop_triangles()

        for vertex in mesh.vertices:
            self.data.vertices.append(obj.matrix_world @ vertex.co)

        for face in mesh.loop_triangles:
            self.data.polygons.append(Triangle.from_obj(face).data)
        
        for material in mesh.materials:
            if material.sollum_type == "sollumz_gta_collision_material":
                mat_item = MaterialItem_XML()
                mat_item.type = material.collision_properties.collision_index
                mat_item.procedural_id = material.collision_properties.procedural_id
                mat_item.room_id = material.collision_properties.room_id
                mat_item.ped_density = material.collision_properties.ped_density
                mat_item.material_color_index = material.collision_properties.material_color_index
                # TODO: flags
                self.data.materials.append(mat_item)


        # Get child poly bounds
        for child in get_children_recursive(obj):
            if child.sollum_type == PolygonType.BOX:
                self.data.polygons.append(Box.from_obj(child, self.data.vertices).data)
            elif child.sollum_type == PolygonType.SPHERE:
                self.data.polygons.append(Sphere.from_obj(child, self.data.vertices).data)
            elif child.sollum_type == PolygonType.CAPSULE:
                self.data.polygons.append(Capsule.from_obj(child, self.data.vertices).data)
            elif child.sollum_type == PolygonType.CYLINDER:
                self.data.polygons.append(Cylinder.from_obj(child, self.data.vertices).data)

        return self

    
    def to_obj(self) -> BlenderObject:
        obj = super().to_obj()

        for gmat in self.data.materials:
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

        for poly in self.data.polygons:
            if type(poly) == Triangle_XML:
                tri_materials.append(poly.material_index)
                face = []
                v1 = self.data.vertices[poly.v1]
                v2 = self.data.vertices[poly.v2]
                v3 = self.data.vertices[poly.v3]
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
                poly_obj = None
                if type(poly) == Box_XML:
                    poly_obj = Box(poly).to_obj(self.data.vertices, obj.data.materials)
                elif type(poly) == Sphere_XML:
                    poly_obj = Sphere(poly).to_obj(obj.data.materials)
                elif type(poly) == Capsule_XML:
                    poly_obj = Capsule(poly).to_obj(self.data.vertices, obj.data.materials)
                elif type(poly) == Cylinder_XML:
                    poly_obj = Cylinder(poly).to_obj(self.data.vertices, obj.data.materials)
                else:
                    continue

                bpy.context.collection.objects.link(poly_obj)
                poly_obj.parent = obj

        obj.data.from_pydata(vertices, [], faces)

        # Apply triangle materials
        for index, poly in obj.data.polygons.items():
            if tri_materials[index]:
                poly.material_index = tri_materials[index]

        obj.location = self.data.geometry_center

        return obj