from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod, abstractstaticmethod
from xml.etree import ElementTree as ET
from .codewalker_xml import *
from .drawable import Drawable

class YDD:
    
    @staticmethod
    def from_xml_file(filepath):
        return Fragment.from_xml_file(filepath)

    @staticmethod
    def write_xml(fragment, filepath):
        return fragment.write_xml(filepath)

class BoneTransformItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()

class BoneTransformsListProperty(ListProperty):
    list_type = BoneTransformItem

    def __init__(self):
        super().__init__()
        self.unk = AttributeProperty("unk", 0)

class LOD1Property(ElementTree):
    tag_name = "LOD1"

    def __init__(self):
        super().__init__()
        self.unknown_14 = ValueProperty("Unknown14")
        self.unknown_18 = ValueProperty("Unknown18")
        self.unknown_1c = ValueProperty("Unknown1C")
        self.unknown_30 = VectorProperty("Unknown30")
        self.unknown_40 = VectorProperty("Unknown40")
        self.unknown_50 = VectorProperty("Unknown50")
        self.unknown_60 = VectorProperty("Unknown60")
        self.unknown_70 = VectorProperty("Unknown70")
        self.unknown_80 = VectorProperty("Unknown80")
        self.unknown_90 = VectorProperty("Unknown90")
        self.unknown_a0 = VectorProperty("UnknownA0")
        self.unknown_b0 = VectorProperty("UnknownB0")

class PhysicsProperty(ElementTree):
    tag_name = "Physics"

    def __init__(self):
        super().__init__()
        self.lod1 = LOD1Property("LOD1")

class Fragment(ElementTree, AbstractClass):
    tag_name = "Fragment"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name")
        self.bounding_sphere_center = VectorProperty("BoundingSphereCenter")
        self.bounding_sphere_radius = ValueProperty("BoundingSphereRadius")
        self.unknown_b0 = ValueProperty("UnknownB0")
        self.unknown_b8 = ValueProperty("UnknownB8")
        self.unknown_bc = ValueProperty("UnknownBC")
        self.unknown_c0 = ValueProperty("UnknownC0")
        self.unknown_c4 = ValueProperty("UnknownC4")
        self.unknown_cc = ValueProperty("UnknownCC")
        self.unknown_d0 = ValueProperty("UnknownD0")
        self.unknown_d4 = ValueProperty("UnknownD4")
        self.drawable = Drawable()
        self.bones_transforms = BoneTransformsListProperty("BoneTransforms")
        self.physics = PhysicsProperty("Physics")

