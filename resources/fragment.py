from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod, abstractstaticmethod
from xml.etree import ElementTree as ET
from .codewalker_xml import *
from .drawable import Drawable
from .bound import YBN

class YDD:
    
    @staticmethod
    def from_xml_file(filepath):
        return Fragment.from_xml_file(filepath)

    @staticmethod
    def write_xml(fragment, filepath):
        return fragment.write_xml(filepath)

class BoneTransformItem(TextProperty):
    tag_name = "Item"

    def __init__(self):
        super().__init__()

class BoneTransformsListProperty(ListProperty):
    list_type = BoneTransformItem

    def __init__(self):
        super().__init__()
        self.unk = AttributeProperty("unk", 0)

class ArchetypeProperty(ElementTree):
    tag_name = "Archetype"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name")
        self.mass = ValueProperty("Mass")
        self.mass_inv = ValueProperty("MassInv")
        self.unknown_48 = ValueProperty("Unknown48")
        self.unknown_4c = ValueProperty("Unknown4C")
        self.unknown_50 = ValueProperty("Unknown50")
        self.unknown_54 = ValueProperty("Unknown54")
        self.inertia_tensor = VectorProperty("InertiaTensor")
        self.inertia_tensor_inv = VectorProperty("InertiaTensorInv")
        self.bounds = YBN()

class TransformItem(TextProperty):
    tag_name = "Item"

    def __init__(self):
        super().__init__()

class TransformsListProperty(ListProperty):
    list_type = BoneTransformItem

    def __init__(self):
        super().__init__()
        self.unk = AttributeProperty("unk", 0)

class ChildrenItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.group_index = ValueProperty("GroupIndex")
        self.bone_tag = ValueProperty("BoneTag")
        self.mass_1 = ValueProperty("Mass1")
        self.mass_2 = ValueProperty("Mass2")
        self.unk_float = ValueProperty("UnkFloat")
        self.unk_vec = VectorProperty("UnkVec")
        self.inertia_tensor = QuaternionProperty("InertiaTensor")
        #self.event_set = None # ?????????? FIND
        self.drawable = Drawable()

class ChildrenListProperty(ListProperty):
    list_type = ChildrenItem

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name, value=value)

class GroupsProperty(ElementTree):
    tag_name = "Groups"

    def __init__(self):
        super().__init__()
        self.children = ChildrenListProperty("Children")

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
        self.archetype = ArchetypeProperty("Archetype")
        self.transforms = TransformsListProperty("Transforms")

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

