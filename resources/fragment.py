from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod, abstractstaticmethod
from xml.etree import ElementTree as ET
from .codewalker_xml import *
from .drawable import Drawable
from .bound import BoundsComposite

class YFT:
    
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

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "BoneTransforms", value=value or [])
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
        self.bounds = BoundsComposite()

class TransformItem(TextProperty):
    tag_name = "Item"

    def __init__(self):
        super().__init__()

class TransformsListProperty(ListProperty):
    list_type = TransformItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "Transforms", value=value or [])
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

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "Children", value=value or [])

class GroupItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name")
        self.index = ValueProperty("Index")
        self.parent_index = ValueProperty("ParentIndex")
        self.unk_byte_4c = ValueProperty("UnkByte4C")
        self.unk_byte_4f = ValueProperty("UnkByte4F")
        self.unk_byte_50 = ValueProperty("UnkByte50")
        self.unk_byte_51 = ValueProperty("UnkByte51") #always 255
        self.unk_byte_52 = ValueProperty("UnkByte52")
        self.unk_byte_53 = ValueProperty("UnkByte53")
        self.unk_float_10 = ValueProperty("UnkFloat10")
        self.unk_float_14 = ValueProperty("UnkFloat14")
        self.unk_float_18 = ValueProperty("UnkFloat18")
        self.unk_float_1c = ValueProperty("UnkFloat1C")
        self.unk_float_20 = ValueProperty("UnkFloat20")
        self.unk_float_24 = ValueProperty("UnkFloat24")
        self.unk_float_28 = ValueProperty("UnkFloat28")
        self.unk_float_2c = ValueProperty("UnkFloat2C")
        self.unk_float_30 = ValueProperty("UnkFloat30")
        self.unk_float_34 = ValueProperty("UnkFloat34")
        self.unk_float_38 = ValueProperty("UnkFloat38")
        self.unk_float_3c = ValueProperty("UnkFloat3C")
        self.unk_float_40 = ValueProperty("UnkFloat40")
        self.mass = ValueProperty("Mass")
        self.unk_float_54 = ValueProperty("UnkFloat54")
        self.unk_float_58 = ValueProperty("UnkFloat58")
        self.unk_float_5c = ValueProperty("UnkFloat5C")
        self.unk_float_60 = ValueProperty("UnkFloat60")
        self.unk_float_64 = ValueProperty("UnkFloat64")
        self.unk_float_68 = ValueProperty("UnkFloat68")
        self.unk_float_6c = ValueProperty("UnkFloat6C")
        self.unk_float_70 = ValueProperty("UnkFloat70")
        self.unk_float_74 = ValueProperty("UnkFloat74")
        self.unk_float_78 = ValueProperty("UnkFloat78")
        self.unk_float_a8 = ValueProperty("UnkFloatA8")

class GroupsListProperty(ListProperty):
    list_type = GroupItem 

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "Groups", value=value or [])

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
        self.archetype = ArchetypeProperty()
        self.transforms = TransformsListProperty()
        self.groups = GroupsListProperty()
        self.children = ChildrenListProperty()

class PhysicsProperty(ElementTree):
    tag_name = "Physics"

    def __init__(self):
        super().__init__()
        self.lod1 = LOD1Property()

class WindowItem(ElementTree):
    tag_name = "Window"

    def __init__(self):
        super().__init__()
        self.item_id = ValueProperty("ItemID")
        self.unk_ushort_1 = ValueProperty("UnkUshort1")
        self.unk_ushort_4 = ValueProperty("UnkUshort4")
        self.unk_ushort_5 = ValueProperty("UnkUshort5")
        self.unk_float_1 = ValueProperty("UnkFloat1")
        self.unk_float_2 = ValueProperty("UnkFloat2")
        self.unk_float_3 = ValueProperty("UnkFloat3")
        self.unk_float_5 = ValueProperty("UnkFloat5")
        self.unk_float_6 = ValueProperty("UnkFloat6")
        self.unk_float_7 = ValueProperty("UnkFloat7")
        self.unk_float_9 = ValueProperty("UnkFloat9")
        self.unk_float_10 = ValueProperty("UnkFloat10")
        self.unk_float_11 = ValueProperty("UnkFloat11")
        self.unk_float_13 = ValueProperty("UnkFloat13")
        self.unk_float_14 = ValueProperty("UnkFloat14")
        self.unk_float_15 = ValueProperty("UnkFloat15")
        self.unk_float_16 = ValueProperty("UnkFloat16")
        self.unk_float_17 = ValueProperty("UnkFloat17")
        self.unk_float_18 = ValueProperty("UnkFloat18")
        self.cracks_texture_tiling = ValueProperty("CracksTextureTiling")
        self.shattermap = TextProperty("ShatterMap")
        
class VehicleGlassWindows(ListProperty):
    list_type = WindowItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "VehicleGlassWindows", value=value or [])

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
        self.bones_transforms = BoneTransformsListProperty()
        self.physics = PhysicsProperty()

