from abc import ABC as AbstractClass
from mathutils import Matrix
from xml.etree import ElementTree as ET
from .element import (
    AttributeProperty,
    ElementTree,
    ElementProperty,
    ListProperty,
    MatrixProperty,
    Matrix33Property,
    Vector4Property,
    TextProperty,
    ValueProperty,
    VectorProperty
)
from .drawable import Drawable, Lights, VertexLayoutList
from .bound import BoundComposite


class YFT:

    file_extension = ".yft.xml"

    @staticmethod
    def from_xml_file(filepath):
        return Fragment.from_xml_file(filepath)

    @staticmethod
    def write_xml(fragment, filepath):
        return fragment.write_xml(filepath)


class BoneTransform(MatrixProperty):
    tag_name = "Item"

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name, value or Matrix())


class BoneTransformsList(ListProperty):
    list_type = BoneTransform
    tag_name = "BoneTransforms"

    def __init__(self, tag_name=None):
        super().__init__(tag_name or BoneTransformsList.tag_name)
        self.unk = AttributeProperty("unk", 1)


class Archetype(ElementTree):
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
        self.bounds = BoundComposite()


class Archetype2(Archetype):
    tag_name = "Archetype2"


class Transform(MatrixProperty):
    tag_name = "Item"

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name, value or Matrix())


class TransformsList(ListProperty):
    list_type = Transform
    tag_name = "Transforms"

    def __init__(self, tag_name=None):
        super().__init__(tag_name or TransformsList.tag_name)


class PhysicsChild(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.group_index = ValueProperty("GroupIndex")
        self.bone_tag = ValueProperty("BoneTag")
        self.pristine_mass = ValueProperty("PristineMass")
        self.damaged_mass = ValueProperty("DamagedMass")
        self.unk_float = ValueProperty("UnkFloat")
        self.unk_vec = Vector4Property("UnkVec")
        self.inertia_tensor = Vector4Property("InertiaTensor")
        self.drawable = Drawable()


class ChildrenList(ListProperty):
    list_type = PhysicsChild
    tag_name = "Children"


class PhysicsGroup(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name")
        self.parent_index = ValueProperty("ParentIndex")
        self.glass_window_index = ValueProperty("GlassWindowIndex")
        self.glass_flags = ValueProperty("GlassFlags")
        self.strength = ValueProperty("Strength")
        self.force_transmission_scale_up = ValueProperty(
            "ForceTransmissionScaleUp")
        self.force_transmission_scale_down = ValueProperty(
            "ForceTransmissionScaleDown")
        self.joint_stiffness = ValueProperty("JointStiffness")
        self.min_soft_angle_1 = ValueProperty("MinSoftAngle1")
        self.max_soft_angle_1 = ValueProperty("MaxSoftAngle1")
        self.max_soft_angle_2 = ValueProperty("MaxSoftAngle2")
        self.max_soft_angle_3 = ValueProperty("MaxSoftAngle3")
        self.rotation_speed = ValueProperty("RotationSpeed")
        self.rotation_strength = ValueProperty("RotationStrength")
        self.restoring_strength = ValueProperty("RestoringStrength")
        self.restoring_max_torque = ValueProperty("RestoringMaxTorque")
        self.latch_strength = ValueProperty("LatchStrength")
        self.mass = ValueProperty("Mass")
        self.min_damage_force = ValueProperty("MinDamageForce")
        self.damage_health = ValueProperty("DamageHealth")
        self.unk_float_5c = ValueProperty("UnkFloat5C")
        self.unk_float_60 = ValueProperty("UnkFloat60")
        self.unk_float_64 = ValueProperty("UnkFloat64")
        self.unk_float_68 = ValueProperty("UnkFloat68")
        self.unk_float_6c = ValueProperty("UnkFloat6C")
        self.unk_float_70 = ValueProperty("UnkFloat70")
        self.unk_float_74 = ValueProperty("UnkFloat74")
        self.unk_float_78 = ValueProperty("UnkFloat78")
        self.unk_float_a8 = ValueProperty("UnkFloatA8")


class GroupsList(ListProperty):
    list_type = PhysicsGroup
    tag_name = "Groups"


class PhysicsLOD(ElementTree):
    tag_name = "LOD"

    def __init__(self, tag_name="LOD"):
        super().__init__()
        self.tag_name = tag_name
        self.unknown_14 = ValueProperty("Unknown14")
        self.unknown_18 = ValueProperty("Unknown18")
        self.unknown_1c = ValueProperty("Unknown1C")
        self.position_offset = VectorProperty("PositionOffset")
        self.unknown_40 = VectorProperty("Unknown40")
        self.unknown_50 = VectorProperty("Unknown50")
        self.damping_linear_c = VectorProperty("DampingLinearC")
        self.damping_linear_v = VectorProperty("DampingLinearV")
        self.damping_linear_v2 = VectorProperty("DampingLinearV2")
        self.damping_angular_c = VectorProperty("DampingAngularC")
        self.damping_angular_v = VectorProperty("DampingAngularV")
        self.damping_angular_v2 = VectorProperty("DampingAngularV2")
        self.archetype = Archetype()
        self.archetype2 = Archetype2()
        self.transforms = TransformsList()
        self.groups = GroupsList()
        self.children = ChildrenList()


class Physics(ElementTree):
    tag_name = "Physics"

    def __init__(self):
        super().__init__()
        self.lod1 = PhysicsLOD("LOD1")
        self.lod2 = PhysicsLOD("LOD2")
        self.lod3 = PhysicsLOD("LOD3")


class ShatterMapProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str = "ShatterMap", value=None):
        super().__init__(tag_name, value or "")

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        rows = []
        if element.text:
            txt = element.text.strip().split("\n")
            for row in txt:
                rows.append(row.strip())
        new.value = rows
        return new

    def to_xml(self):
        if not self.value:
            return None

        element = ET.Element(self.tag_name)
        text = []
        for row in self.value:
            text.append("".join(row))
        element.text = "\n".join(text)
        return element


class Window(ElementTree):
    tag_name = "Window"

    def __init__(self):
        super().__init__()
        self.item_id = ValueProperty("ItemID")
        self.unk_ushort_1 = ValueProperty("UnkUshort1")
        self.unk_ushort_4 = ValueProperty("UnkUshort4")
        self.unk_ushort_5 = ValueProperty("UnkUshort5")
        self.projection_matrix = MatrixProperty("Projection")
        self.unk_float_17 = ValueProperty("UnkFloat17")
        self.unk_float_18 = ValueProperty("UnkFloat18")
        self.cracks_texture_tiling = ValueProperty("CracksTextureTiling")
        self.shattermap = ShatterMapProperty("ShatterMap")

    @property
    def width(self):
        return len(self.shattermap[0]) if self.height > 0 else 0

    @property
    def height(self):
        return len(self.shattermap) if self.shattermap else 0


class VehicleGlassWindows(ListProperty):
    list_type = Window
    tag_name = "VehicleGlassWindows"


class GlassWindow(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.flags = ValueProperty("Flags")
        self.projection_matrix = Matrix33Property("Projection")
        self.unk_float_13 = ValueProperty("UnkFloat13")
        self.unk_float_14 = ValueProperty("UnkFloat14")
        self.unk_float_15 = ValueProperty("UnkFloat15")
        self.unk_float_16 = ValueProperty("UnkFloat16")
        self.thickness = ValueProperty("Thickness")
        self.unk_float_18 = ValueProperty("UnkFloat18")
        self.unk_float_19 = ValueProperty("UnkFloat19")
        self.tangent = VectorProperty("Tangent")
        self.layout = VertexLayoutList()


class GlassWindows(ListProperty):
    list_type = GlassWindow
    tag_name = "GlassWindows"


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
        self.gravity_factor = ValueProperty("GravityFactor")
        self.buoyancy_factor = ValueProperty("BuoyancyFactor")
        self.drawable = Drawable()
        self.bones_transforms = BoneTransformsList()
        self.physics = Physics()
        self.glass_windows = GlassWindows()
        self.lights = Lights()
        self.vehicle_glass_windows = VehicleGlassWindows()

    def get_lods_by_id(self):
        return {1: self.physics.lod1, 2: self.physics.lod2, 3: self.physics.lod3}
