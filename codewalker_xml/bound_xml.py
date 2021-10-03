from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod, abstractstaticmethod
from xml.etree import ElementTree as ET
from .codewalker_xml import *
from Sollumz.meshhelper import *
from mathutils import Vector
from .polygon_xml import PolygonsProperty
from Sollumz.sollumz_shaders import create_collision_material_from_index


class YBN_XML(ElementTree):
    tag_name = 'BoundsFile'

    def __init__(self) -> None:
        super().__init__()
        self.bounds = BoundComposite_XML()


class Bounds_XML(ElementTree, AbstractClass):
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


class BoundComposite_XML(Bounds_XML):
    def __init__(self):
        super().__init__()
        self.type = AttributeProperty('type', 'Composite')
        self.children = BoundListProperty()


class BoundItem_XML(Bounds_XML, AbstractClass):
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


class BoundBox_XML(BoundItem_XML):
    type = 'Box'


class BoundSphere_XML(BoundItem_XML):
    type = 'Sphere'


class BoundCapsule_XML(BoundItem_XML):
    type = 'Capsule'


class BoundCylinder_XML(BoundItem_XML):
    type = 'Cylinder'


class BoundDisc_XML(BoundItem_XML):
    type = 'Disc'
    

class BoundCloth_XML(BoundItem_XML):
    type = 'Cloth'


class BoundGeometry_XML(BoundItem_XML):
    type = 'Geometry'


class BoundGeometryBVH_XML(BoundItem_XML):
    type = 'GeometryBVH'

    def __init__(self):
        super().__init__()
        self.geometry_center = VectorProperty('GeometryCenter')
        self.materials = MaterialsListProperty()
        self.vertices = VerticesProperty('Vertices')
        self.polygons = PolygonsProperty()


class BoundListProperty(ListProperty):
    list_type = BoundItem_XML

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Children', value=value or [])
    
    @staticmethod
    def from_xml(element: ET.Element):
        new = BoundListProperty()

        for child in element.iter():
            if 'type' in child.attrib:
                bound_type = child.get('type')
                if bound_type == 'Box':
                    new.value.append(BoundBox_XML.from_xml(child))
                elif bound_type == 'Sphere':
                    new.value.append(BoundSphere_XML.from_xml(child))
                elif bound_type == 'Capsule':
                    new.value.append(BoundCapsule_XML.from_xml(child))
                elif bound_type == 'Cylinder':
                    new.value.append(BoundCylinder_XML.from_xml(child))
                elif bound_type == 'Disc':
                    new.value.append(BoundDisc_XML.from_xml(child))
                elif bound_type == 'Cloth':
                    new.value.append(BoundCloth_XML.from_xml(child))
                elif bound_type == 'Geometry':
                    new.value.append(BoundGeometry_XML.from_xml(child))
                elif bound_type == 'GeometryBVH':
                    new.value.append(BoundGeometryBVH_XML.from_xml(child))

        return new


class MaterialItem_XML(ElementTree):
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
    list_type = MaterialItem_XML

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Materials', value=value or [])