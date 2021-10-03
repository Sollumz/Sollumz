import bpy
import bmesh
from xml.etree import ElementTree as ET
from abc import ABC as AbstractClass
from bpy.types import Object as BlenderObject
from .codewalker_xml import ElementTree, AttributeProperty, ListProperty
from Sollumz.meshhelper import *
from mathutils import Vector, Matrix
from enum import Enum


class Polygon_XML(ElementTree, AbstractClass):
    def __init__(self):
        super().__init__()
        self.material_index = AttributeProperty('m', 0)


class PolygonsProperty(ListProperty):
    list_type = Polygon_XML

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Polygons', value=value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = PolygonsProperty()    

        for child in element.iter():
            if child.tag == 'Box':
                new.value.append(Box_XML.from_xml(child))
            elif child.tag == 'Sphere':
                new.value.append(Sphere_XML.from_xml(child))
            elif child.tag == 'Capsule':
                new.value.append(Capsule_XML.from_xml(child))
            elif child.tag == 'Cylinder':
                new.value.append(Cylinder_XML.from_xml(child))
            elif child.tag == 'Triangle':
                new.value.append(Triangle_XML.from_xml(child))

        return new


class Triangle_XML(Polygon_XML):
    tag_name = 'Triangle'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 0)
        self.v3 = AttributeProperty('v3', 0)
        self.f1 = AttributeProperty('f1', 0)
        self.f2 = AttributeProperty('f2', 0)
        self.f3 = AttributeProperty('f3', 0)
    

class Sphere_XML(Polygon_XML):
    tag_name = 'Sphere'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.radius = AttributeProperty('radius', 0)

    

class Capsule_XML(Polygon_XML):
    tag_name = 'Capsule'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 1)
        self.radius = AttributeProperty('radius', 0)


class Box_XML(Polygon_XML):
    tag_name = 'Box'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 1)
        self.v3 = AttributeProperty('v3', 2)
        self.v4 = AttributeProperty('v4', 3)



class Cylinder_XML(Polygon_XML):
    tag_name = 'Cylinder'

    def __init__(self):
        super().__init__()
        self.v1 = AttributeProperty('v1', 0)
        self.v2 = AttributeProperty('v2', 1)
        self.radius = AttributeProperty('radius', 0)