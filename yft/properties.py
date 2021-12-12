import bpy


class FragmentProperties(bpy.types.PropertyGroup):
    unk_b0: bpy.props.FloatProperty(name="UnknownB0")
    unk_b8: bpy.props.FloatProperty(name="UnknownB8")
    unk_bc: bpy.props.FloatProperty(name="UnknownBC")
    unk_c0: bpy.props.FloatProperty(name="UnknownC0")
    unk_c4: bpy.props.FloatProperty(name="UnknownC4")
    unk_cc: bpy.props.FloatProperty(name="UnknownCC")
    unk_d0: bpy.props.FloatProperty(name="UnknownD0")
    unk_d4: bpy.props.FloatProperty(name="UnknownD4")


# blender doesn't support pointer properties to custom property groups?
'''class ArchetypeProperties(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    mass: bpy.props.FloatProperty(name="Mass")
    mass_inv: bpy.props.FloatProperty(name="MassInv")
    unknown_48: bpy.props.FloatProperty(name="Unknown48")
    unknown_4c: bpy.props.FloatProperty(name="Unknown4c")
    unknown_50: bpy.props.FloatProperty(name="Unknown50")
    unknown_54: bpy.props.FloatProperty(name="Unknown54")
    inertia_tensor: bpy.props.FloatVectorProperty(name="InertiaTensor")
    inertia_tensor_inv: bpy.props.FloatVectorProperty(name="InertiaTensorInv")
    bound: bpy.props.PointerProperty(type=bpy.types.Object)'''


class LODProperties(bpy.types.PropertyGroup):
    type: bpy.props.IntProperty(name="Type", default=0)
    unk_14: bpy.props.FloatProperty(name="Unknown14")
    unk_18: bpy.props.FloatProperty(name="Unknown18")
    unk_1c: bpy.props.FloatProperty(name="Unknown1C")
    unk_30: bpy.props.FloatVectorProperty(name="Unknown30")
    unk_40: bpy.props.FloatVectorProperty(name="Unknown40")
    unk_50: bpy.props.FloatVectorProperty(name="Unknown50")
    unk_60: bpy.props.FloatVectorProperty(name="Unknown60")
    unk_70: bpy.props.FloatVectorProperty(name="Unknown70")
    unk_80: bpy.props.FloatVectorProperty(name="Unknown80")
    unk_90: bpy.props.FloatVectorProperty(name="Unknown90")
    unk_a0: bpy.props.FloatVectorProperty(name="UnknownA0")
    unk_b0: bpy.props.FloatVectorProperty(name="UnknownB0")
    name: bpy.props.StringProperty(name="Name")
    mass: bpy.props.FloatProperty(name="Mass")
    mass_inv: bpy.props.FloatProperty(name="MassInv")
    unknown_48: bpy.props.FloatProperty(name="Unknown48")
    unknown_4c: bpy.props.FloatProperty(name="Unknown4c")
    unknown_50: bpy.props.FloatProperty(name="Unknown50")
    unknown_54: bpy.props.FloatProperty(name="Unknown54")
    inertia_tensor: bpy.props.FloatVectorProperty(name="InertiaTensor")
    inertia_tensor_inv: bpy.props.FloatVectorProperty(name="InertiaTensorInv")
    # archetype_properties = bpy.props.PointerProperty(type=ArchetypeProperties)


class GroupProperties(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    parent_index: bpy.props.IntProperty(default=0)
    unk_byte_4c: bpy.props.IntProperty(name="UnkByte4C")
    unk_byte_4f: bpy.props.IntProperty(name="UnkByte4F")
    unk_byte_50: bpy.props.IntProperty(name="UnkByte50")
    unk_byte_51: bpy.props.IntProperty(name="UnkByte51")
    unk_byte_52: bpy.props.IntProperty(name="UnkByte52")
    unk_byte_53: bpy.props.IntProperty(name="UnkByte53")
    unk_float_10: bpy.props.FloatProperty(name="UnkFloat10")
    unk_float_14: bpy.props.FloatProperty(name="UnkFloat14")
    unk_float_18: bpy.props.FloatProperty(name="UnkFloat18")
    unk_float_1c: bpy.props.FloatProperty(name="UnkFloat1C")
    unk_float_20: bpy.props.FloatProperty(name="UnkFloat20")
    unk_float_24: bpy.props.FloatProperty(name="UnkFloat24")
    unk_float_28: bpy.props.FloatProperty(name="UnkFloat28")
    unk_float_2c: bpy.props.FloatProperty(name="UnkFloat2C")
    unk_float_30: bpy.props.FloatProperty(name="UnkFloat30")
    unk_float_34: bpy.props.FloatProperty(name="UnkFloat34")
    unk_float_38: bpy.props.FloatProperty(name="UnkFloat38")
    unk_float_3c: bpy.props.FloatProperty(name="UnkFloat3C")
    unk_float_40: bpy.props.FloatProperty(name="UnkFloat40")
    mass: bpy.props.FloatProperty(name="Mass")
    unk_float_54: bpy.props.FloatProperty(name="UnkFloat54")
    unk_float_58: bpy.props.FloatProperty(name="UnkFloat58")
    unk_float_5c: bpy.props.FloatProperty(name="UnkFloat5C")
    unk_float_60: bpy.props.FloatProperty(name="UnkFloat60")
    unk_float_64: bpy.props.FloatProperty(name="UnkFloat64")
    unk_float_68: bpy.props.FloatProperty(name="UnkFloat68")
    unk_float_6c: bpy.props.FloatProperty(name="UnkFloat6C")
    unk_float_70: bpy.props.FloatProperty(name="UnkFloat70")
    unk_float_74: bpy.props.FloatProperty(name="UnkFloat74")
    unk_float_78: bpy.props.FloatProperty(name="UnkFloat78")
    unk_float_a8: bpy.props.FloatProperty(name="UnkFloatA8")


class ChildProperties(bpy.types.PropertyGroup):
    bone_tag: bpy.props.IntProperty(name="BoneTag")
    mass_1: bpy.props.FloatProperty(name="Mass1")
    mass_2: bpy.props.FloatProperty(name="Mass2")
    unk_vec: bpy.props.FloatVectorProperty(name="UnkVec")
    inertia_tensor: bpy.props.FloatVectorProperty(name="InertiaTensor", size=4)
    #bone: bpy.props.PointerProperty(type=bpy.types.Bone)
    # group_index: bpy.props.IntProperty(name="EventSet") ???


def register():
    bpy.types.Object.fragment_properties = bpy.props.PointerProperty(
        type=FragmentProperties)
    bpy.types.Object.lod_properties = bpy.props.PointerProperty(
        type=LODProperties)
    bpy.types.Object.group_properties = bpy.props.PointerProperty(
        type=GroupProperties
    )
    bpy.types.Object.child_properties = bpy.props.PointerProperty(
        type=ChildProperties)


def unregister():
    bpy.types.Object.fragment_properties
    bpy.types.Object.lod_properties
    bpy.types.Object.group_properties
    bpy.types.Object.child_properties
