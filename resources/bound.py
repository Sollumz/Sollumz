from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod, abstractstaticmethod
from xml.etree import ElementTree as ET
from .codewalker_xml import *
from enum import Enum

class YBN:
    
    @staticmethod
    def from_xml_file(filepath):
        return BoundFile.from_xml_file(filepath)

    @staticmethod
    def write_xml(bound_file, filepath):
        return bound_file.write_xml(filepath)

class BoundFile(ElementTree):
    tag_name = "BoundsFile"

    def __init__(self):
        super().__init__()
        self.composite = BoundsComposite()

class Bounds(ElementTree, AbstractClass):
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

class BoundsComposite(Bounds):
    def __init__(self):
        super().__init__()
        self.type = AttributeProperty('type', 'Composite')
        self.children = BoundListProperty()

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

class BoundBox(BoundItem):
    type = 'Box'

class BoundSphere(BoundItem):
    type = 'Sphere'

class BoundCapsule(BoundItem):
    type = 'Capsule'

class BoundCylinder(BoundItem):
    type = 'Cylinder'

class BoundDisc(BoundItem):
    type = 'Disc'

class BoundCloth(BoundItem):
    type = 'Cloth'

class BoundGeometryBVH(BoundItem):
    type = 'GeometryBVH'

    def __init__(self):
        super().__init__()
        self.geometry_center = VectorProperty('GeometryCenter')
        self.materials = MaterialsListProperty() 
        self.vertices = VerticesProperty('Vertices')
        self.vertex_colors = VertexColorProperty("VertexColours")
        self.polygons = PolygonsProperty()

class BoundGeometry(BoundGeometryBVH):
    type = 'Geometry'

    def __init__(self):
        super().__init__()
        # Placeholder: Currently not implemented by CodeWalker
        self.octants = PolygonsProperty('Octants')

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

class MaterialItem(ElementTree):
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

class VertexColorProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str = 'VertexColours', value = None):
        super().__init__(tag_name, value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = VertexColorProperty(element.tag, [])
        text = element.text.strip().split('\n')
        if len(text) > 0:
            for line in text:
                colors = line.strip().split(',')
                if not len(colors) == 4:
                    return VertexColorProperty.read_value_error(element)

                new.value.append([int(colors[0]), int(colors[1]), int(colors[2]), int(colors[3])])
        
        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.text = '\n'
        
        if(len(self.value) == 0):
            return None 
        
        for color in self.value:
            for index, component in enumerate(color):
                element.text += str(int(component * 255))
                if index < len(color) - 1:
                    element.text += ', '
            element.text += '\n'
        
        return element

class Polygon(ElementTree, AbstractClass):
    def __init__(self):
        super().__init__()
        self.material_index = AttributeProperty('m', 0)

class PolygonsProperty(ListProperty):
    list_type = Polygon

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Polygons', value=value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = PolygonsProperty()    

        for child in element.iter():
            if child.tag == 'Box':
                new.value.append(Box.from_xml(child))
            elif child.tag == 'Sphere':
                new.value.append(Sphere.from_xml(child))
            elif child.tag == 'Capsule':
                new.value.append(Capsule.from_xml(child))
            elif child.tag == 'Cylinder':
                new.value.append(Cylinder.from_xml(child))
            elif child.tag == 'Triangle':
                new.value.append(Triangle.from_xml(child))

        return new

class Triangle(Polygon):
    tag_name = 'Triangle'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 0)
        self.v3 = AttributeProperty('v3', 0)
        self.f1 = AttributeProperty('f1', 0)
        self.f2 = AttributeProperty('f2', 0)
        self.f3 = AttributeProperty('f3', 0)

class Sphere(Polygon):
    tag_name = 'Sphere'

    def __init__(self):
        super().__init__()
        self.v = AttributeProperty('v', 0)
        self.radius = AttributeProperty('radius', 0)

class Capsule(Polygon):
    tag_name = 'Capsule'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 1)
        self.radius = AttributeProperty('radius', 0)

class Box(Polygon):
    tag_name = 'Box'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 1)
        self.v3 = AttributeProperty('v3', 2)
        self.v4 = AttributeProperty('v4', 3)

class Cylinder(Polygon):
    tag_name = 'Cylinder'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 1)
        self.radius = AttributeProperty('radius', 0)