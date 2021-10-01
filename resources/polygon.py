from xml.etree import ElementTree as ET
from abc import ABC as AbstractClass
from bpy.types import Object as BlenderObject
from .cwxml import GTAObject, AttributeProperty, ListProperty
from meshhelper import get_obj_radius
from enum import Enum


class PolygonType(str, Enum):
    BOX = 'sollumz_bound_poly_box'
    SPHERE = 'sollumz_bound__poly_sphere'
    CAPSULE = 'sollumz_bound_poly_capsule'
    CYLINDER = 'sollumz_bound_poly_cylinder'
    TRIANGLE = 'sollumz_bound_poly_triangle'


class Polygon(GTAObject, AbstractClass):
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
    
    
    def load_obj(self, obj: BlenderObject):
        index = obj.index * 3
        self.v1 = index
        self.v2 = index + 1
        self.v3 = index + 2

        return self
    

class Sphere(Polygon):
    tag_name = 'Sphere'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        # TODO GET RADIUS
        self.radius = AttributeProperty('radius', 0)
    
    def load_obj(self, obj: BlenderObject):
        self.radius = get_obj_radius(obj)
        
        return self
    

class Capsule(Polygon):
    tag_name = 'Capsule'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 1)
        self.radius = AttributeProperty('radius', 0)
    
    def load_obj(self, obj: BlenderObject):
        self.radius = get_obj_radius(obj)
        
        return self


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
    
    def load_obj(self, obj: BlenderObject):
        self.radius = get_obj_radius(obj)

        return self