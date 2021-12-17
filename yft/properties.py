import bpy


class FragmentProperties(bpy.types.PropertyGroup):
    unk_b0: bpy.props.FloatProperty(name="UnknownB0")
    unk_b8: bpy.props.FloatProperty(name="UnknownB8")
    unk_bc: bpy.props.FloatProperty(name="UnknownBC")
    unk_c0: bpy.props.FloatProperty(name="UnknownC0")
    unk_c4: bpy.props.FloatProperty(name="UnknownC4")
    unk_cc: bpy.props.FloatProperty(name="UnknownCC")
    gravity_factor: bpy.props.FloatProperty(name="Gravity Factor")
    buoyancy_factor: bpy.props.FloatProperty(name="Buoyancy Factor")


class LODProperties(bpy.types.PropertyGroup):
    type: bpy.props.IntProperty(name="Type", default=0)
    unknown_14: bpy.props.FloatProperty(name="Unknown14")
    unknown_18: bpy.props.FloatProperty(name="Unknown18")
    unknown_1c: bpy.props.FloatProperty(name="Unknown1C")
    position_offset: bpy.props.FloatVectorProperty(name="Position Offset")
    unknown_40: bpy.props.FloatVectorProperty(name="Unknown40")
    unknown_50: bpy.props.FloatVectorProperty(name="Unknown50")
    damping_linear_c: bpy.props.FloatVectorProperty(name="Damping Linear C")
    damping_linear_v: bpy.props.FloatVectorProperty(name="Damping Linear V")
    damping_linear_v2: bpy.props.FloatVectorProperty(name="Damping Linear V2")
    damping_angular_c: bpy.props.FloatVectorProperty(name="Damping Angular C")
    damping_angular_v: bpy.props.FloatVectorProperty(name="Damping Angular V")
    damping_angular_v2: bpy.props.FloatVectorProperty(
        name="Damping Angular V2")
    # archetype properties
    archetype_name: bpy.props.StringProperty(name="Name")
    archetype_mass: bpy.props.FloatProperty(name="Mass")
    archetype_unknown_48: bpy.props.FloatProperty(name="Unknown48")
    archetype_unknown_4c: bpy.props.FloatProperty(name="Unknown4c")
    archetype_unknown_50: bpy.props.FloatProperty(name="Unknown50")
    archetype_unknown_54: bpy.props.FloatProperty(name="Unknown54")
    archetype_inertia_tensor: bpy.props.FloatVectorProperty(
        name="Inertia Tensor")


class GroupProperties(bpy.types.PropertyGroup):
    glass_window_index: bpy.props.IntProperty(name="Glass Window Index")
    glass_flags: bpy.props.IntProperty(name="Glass Flags")
    strength: bpy.props.FloatProperty(name="Strength")
    force_transmission_scale_up: bpy.props.FloatProperty(
        name="Force Transmission Scale Up")
    force_transmission_scale_down: bpy.props.FloatProperty(
        name="Force Transmission Scale Down")
    joint_stiffness: bpy.props.FloatProperty(name="Joint Stiffness")
    min_soft_angle_1: bpy.props.FloatProperty(name="Min Soft Angle 1")
    max_soft_angle_1: bpy.props.FloatProperty(name="Max Soft Angle 1")
    max_soft_angle_2: bpy.props.FloatProperty(name="Max Soft Angle 2")
    max_soft_angle_3: bpy.props.FloatProperty(name="Max Soft Angle 3")
    rotation_speed: bpy.props.FloatProperty(name="Rotation Speed")
    rotation_strength: bpy.props.FloatProperty(name="Restoring Strength")
    restoring_max_torque: bpy.props.FloatProperty(name="Restoring Max Torque")
    latch_strength: bpy.props.FloatProperty(name="Latch Strength")
    mass: bpy.props.FloatProperty(name="Mass")
    min_damage_force: bpy.props.FloatProperty(name="Min Damage Force")
    damage_health: bpy.props.FloatProperty(name="Damage Health")
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
    bone_tag: bpy.props.IntProperty(name="Bone Tag")
    pristine_mass: bpy.props.FloatProperty(name="Pristine Mass")
    damaged_mass: bpy.props.FloatProperty(name="Damaged Mass")
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
