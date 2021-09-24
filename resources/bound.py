from abc import ABC
from .cwxml import XMLElementTree, XMLAttributeProperty, XMLList, XMLVector, XMLValue, XMLVerticesList, XMLQuaternion, XMLFlags
from mathutils import Vector

class Bounds(XMLElementTree, ABC):
    def __init__(self, tag_name: str):
        super().__init__(tag_name)
        self.box_min = XMLVector('BoxMin')
        self.box_max = XMLVector('BoxMax')
        self.box_center = XMLVector('BoxCenter')
        self.sphere_center = XMLVector('SphereCenter')
        self.sphere_radius = XMLValue('SphereRadius', 0.0)
        self.margin = XMLValue('Margin', 0)
        self.volume = XMLValue('Volume', 0)
        self.inertia = XMLVector('Inertia')
        self.material_index = XMLValue('MaterialIndex', 0)
        self.material_color_index = XMLValue('MaterialColourIndex', 0)
        self.procedural_id = XMLValue('ProceduralId', 0)
        self.room_id = XMLValue('RoomId', 0)
        self.ped_density = XMLValue('PedDensity', 0)
        self.unk_flags = XMLValue('UnkFlags', 0)
        self.poly_flags = XMLValue('PolyFlags', 0)
        self.unk_type = XMLValue('UnkType', 0)


class BoundsFile(XMLElementTree):
    def __init__(self, bounds: Bounds):
        super().__init__('BoundsFile')
        self.bounds = bounds


class BoundsComposite(Bounds):
    def __init__(self):
        super().__init__('Bounds')
        self.type = XMLAttributeProperty('type', 'Composite')
        self.children = XMLList('Children', GeometryBVH)


class Poly(XMLElementTree):
    def __init__(self, tag_name: str):
        super().__init__(tag_name)
        self.material_index = XMLAttributeProperty('m', 0)
    

class Triangle(Poly):
    def __init__(self):
        super().__init__('Triangle')
        self.v1 = XMLAttributeProperty('v1', 0)
        self.v2 = XMLAttributeProperty('v2', 0)
        self.v3 = XMLAttributeProperty('v3', 0)
        self.f1 = XMLAttributeProperty('f1', 0)
        self.f2 = XMLAttributeProperty('f2', 0)
        self.f3 = XMLAttributeProperty('f3', 0)


class Sphere(Poly):
    def __init__(self):
        super().__init__('Sphere')
        self.v = XMLAttributeProperty('v', 0)
        self.radius = XMLAttributeProperty('radius', 0.0)


class Capsule(Poly):
    def __init__(self):
        super().__init__('Capsule')
        self.v1 = XMLAttributeProperty('v1', 0)
        self.v2 = XMLAttributeProperty('v2', 0)
        self.radius = XMLAttributeProperty('radius', 0.0)


class Box(Poly):
    def __init__(self):
        super().__init__('Box')
        self.v1 = XMLAttributeProperty('v1', 0)
        self.v2 = XMLAttributeProperty('v2', 0)
        self.v3 = XMLAttributeProperty('v3', 0)
        self.v4 = XMLAttributeProperty('v4', 0)


class Cylinder(Poly):
    def __init__(self):
        super().__init__('Cylinder')
        self.v1 = XMLAttributeProperty('v1', 0)
        self.v2 = XMLAttributeProperty('v2', 0)
        self.radius = XMLAttributeProperty('radius', 0)


class MaterialItem(XMLElementTree):
    def __init__(self):
        super().__init__('Item')
        self.type = XMLValue('Type', 0)
        self.procedural_id = XMLValue('ProceduralId', 0)
        self.room_id = XMLValue('RoomId', 0)
        self.ped_density = XMLValue('PedDensity', 0)
        self.flags = XMLFlags()
        self.material_color_index = XMLValue('MaterialColourIndex', 0)
        self.unk = XMLValue('Unk', 0)


class BoundItem(Bounds):
    def __init__(self):
        super().__init__('Item')
        self.composite_position = XMLVector('CompositePosition')
        self.composite_rotation = XMLQuaternion('CompositeRotation')
        self.composite_scale = XMLVector('CompositeScale', Vector([1, 1, 1]))
        self.composite_flags1 = XMLFlags('CompositeFlags1')
        self.composite_flags2 = XMLFlags('CompositeFlags2')
        self.geometry_center = XMLVector('GeometryCenter')
        self.materials = XMLList('Materials', MaterialItem)
        self.vertices = XMLVerticesList('Vertices')
        self.polygons = XMLList('Polygons', Poly)


class GeometryBVH(BoundItem):
    def __init__(self):
        super().__init__()
        self.type = XMLAttributeProperty('type', 'GeometryBVH')
