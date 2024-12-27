from abc import ABC as AbstractClass, abstractmethod
from typing import Union, Type
from xml.etree import ElementTree as ET
from .element import (
    AttributeProperty,
    ElementProperty,
    ElementTree,
    ListProperty,
    QuaternionProperty,
    StringValueProperty,
    TextProperty,
    TextListProperty,
    ValueProperty,
    VectorProperty,
    TextPropertyRequired,
    ListPropertyRequired,
    ElementProperty,
    Vector4Property,
)


class IPL:

    file_extension = ".ipl.xml"

    @staticmethod
    def from_xml_file(filepath):
        return IplData.from_xml_file(filepath)


class Entity(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.archetype_name = TextProperty("archetypeName")
        self.position = VectorProperty("position")
        self.rotation = QuaternionProperty("rotation")
        self.scale = VectorProperty("scale")
        self.lod_dist = ValueProperty("lodDist", 0)
        self.lod_level = TextProperty("lodLevel")


class EntityList(ListPropertyRequired):
    list_type = Entity
    tag_name = "entities"


class IplData(ElementTree, AbstractClass):
    tag_name = "IplData"

    def __init__(self):
        super().__init__()
        self.name = TextPropertyRequired("name")
        self.parent = TextPropertyRequired("parent")
        self.entities = EntityList()
