import bpy

from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType


class FragArchetypeProperties(bpy.types.PropertyGroup):
    unknown_48: bpy.props.FloatProperty(name="Unknown48", default=1)
    unknown_4c: bpy.props.FloatProperty(
        name="Unknown4c", default=150)
    unknown_50: bpy.props.FloatProperty(
        name="Unknown50", default=6.28)
    unknown_54: bpy.props.FloatProperty(name="Unknown54", default=1)
    inertia_tensor: bpy.props.FloatVectorProperty(
        name="Inertia Tensor")


class LODProperties(bpy.types.PropertyGroup):
    unknown_14: bpy.props.FloatProperty(name="Unknown14")
    unknown_18: bpy.props.FloatProperty(name="Unknown18")
    unknown_1c: bpy.props.FloatProperty(name="Unknown1C")
    position_offset: bpy.props.FloatVectorProperty(name="Position Offset")
    unknown_40: bpy.props.FloatVectorProperty(name="Unknown40")
    unknown_50: bpy.props.FloatVectorProperty(name="Unknown50")
    damping_linear_c: bpy.props.FloatVectorProperty(
        name="Damping Linear C", default=(0.02, 0.02, 0.02))
    damping_linear_v: bpy.props.FloatVectorProperty(
        name="Damping Linear V", default=(0.02, 0.02, 0.02))
    damping_linear_v2: bpy.props.FloatVectorProperty(
        name="Damping Linear V2", default=(0.01, 0.01, 0.01))
    damping_angular_c: bpy.props.FloatVectorProperty(
        name="Damping Angular C", default=(0.02, 0.02, 0.02))
    damping_angular_v: bpy.props.FloatVectorProperty(
        name="Damping Angular V", default=(0.02, 0.02, 0.02))
    damping_angular_v2: bpy.props.FloatVectorProperty(
        name="Damping Angular V2", default=(0.01, 0.01, 0.01))

    archetype_properties: bpy.props.PointerProperty(
        type=FragArchetypeProperties)


class GroupProperties(bpy.types.PropertyGroup):
    glass_window_index: bpy.props.IntProperty(name="Glass Window Index")
    glass_flags: bpy.props.IntProperty(name="Glass Flags")
    strength: bpy.props.FloatProperty(name="Strength", default=100)
    force_transmission_scale_up: bpy.props.FloatProperty(
        name="Force Transmission Scale Up", default=0.25)
    force_transmission_scale_down: bpy.props.FloatProperty(
        name="Force Transmission Scale Down", default=0.25)
    joint_stiffness: bpy.props.FloatProperty(name="Joint Stiffness")
    min_soft_angle_1: bpy.props.FloatProperty(
        name="Min Soft Angle 1", default=-1)
    max_soft_angle_1: bpy.props.FloatProperty(
        name="Max Soft Angle 1", default=1)
    max_soft_angle_2: bpy.props.FloatProperty(
        name="Max Soft Angle 2", default=1)
    max_soft_angle_3: bpy.props.FloatProperty(
        name="Max Soft Angle 3", default=1)
    rotation_speed: bpy.props.FloatProperty(name="Rotation Speed")
    rotation_strength: bpy.props.FloatProperty(name="Restoring Strength")
    restoring_max_torque: bpy.props.FloatProperty(name="Restoring Max Torque")
    latch_strength: bpy.props.FloatProperty(name="Latch Strength")
    min_damage_force: bpy.props.FloatProperty(
        name="Min Damage Force", default=100)
    damage_health: bpy.props.FloatProperty(name="Damage Health", default=1000)
    unk_float_5c: bpy.props.FloatProperty(name="UnkFloat5C")
    unk_float_60: bpy.props.FloatProperty(name="UnkFloat60", default=1)
    unk_float_64: bpy.props.FloatProperty(name="UnkFloat64", default=1)
    unk_float_68: bpy.props.FloatProperty(name="UnkFloat68", default=1)
    unk_float_6c: bpy.props.FloatProperty(name="UnkFloat6C", default=1)
    unk_float_70: bpy.props.FloatProperty(name="UnkFloat70", default=1)
    unk_float_74: bpy.props.FloatProperty(name="UnkFloat74", default=1)
    unk_float_78: bpy.props.FloatProperty(name="UnkFloat78", default=1)
    unk_float_a8: bpy.props.FloatProperty(name="UnkFloatA8", default=1)


class ChildProperties(bpy.types.PropertyGroup):
    mass: bpy.props.FloatProperty(name="Mass", min=0)
    damaged: bpy.props.BoolProperty(name="Damaged")


class VehicleWindowProperties(bpy.types.PropertyGroup):
    unk_float_17: bpy.props.FloatProperty(name="Unk Float 17")
    unk_float_18: bpy.props.FloatProperty(name="Unk Float 18")
    cracks_texture_tiling: bpy.props.FloatProperty(
        name="Cracks Texture Tiling")


class FragmentProperties(bpy.types.PropertyGroup):
    unk_b0: bpy.props.FloatProperty(name="UnknownB0")
    unk_b8: bpy.props.FloatProperty(name="UnknownB8")
    unk_bc: bpy.props.FloatProperty(name="UnknownBC")
    unk_c0: bpy.props.FloatProperty(name="UnknownC0", default=65280)
    unk_c4: bpy.props.FloatProperty(name="UnknownC4")
    unk_cc: bpy.props.FloatProperty(name="UnknownCC")
    gravity_factor: bpy.props.FloatProperty(name="Gravity Factor")
    buoyancy_factor: bpy.props.FloatProperty(name="Buoyancy Factor")

    lod_properties: bpy.props.PointerProperty(type=LODProperties)


def register():
    bpy.types.Object.fragment_properties = bpy.props.PointerProperty(
        type=FragmentProperties)
    bpy.types.Object.child_properties = bpy.props.PointerProperty(
        type=ChildProperties)
    bpy.types.Object.vehicle_window_properties = bpy.props.PointerProperty(
        type=VehicleWindowProperties)
    bpy.types.Object.sollumz_is_physics_child_mesh = bpy.props.BoolProperty(
        name="Is Physics Child", description="Whether or not this fragment mesh is a physics child. Usually wheels meshes are physics children")

    bpy.types.Object.glass_thickness = bpy.props.FloatProperty(
        name="Thickness", default=0.1)

    bpy.types.Scene.create_fragment_type = bpy.props.EnumProperty(
        items=[
            (SollumType.FRAGMENT.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGMENT], "Create a fragment object"),
            (SollumType.FRAGLOD.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGLOD], "Create a fragment LOD object"),
            (SollumType.FRAGGROUP.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGGROUP], "Create a fragment group object"),
            (SollumType.FRAGCHILD.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGCHILD], "Create a fragment child object"),
        ],
        name="Type",
        default=SollumType.FRAGMENT.value
    )

    bpy.types.Bone.group_properties = bpy.props.PointerProperty(
        type=GroupProperties)
    bpy.types.Bone.sollumz_use_physics = bpy.props.BoolProperty(
        name="Use Physics", description="Whether or not to use physics for this fragment bone")

    bpy.types.Scene.create_bones_fragment = bpy.props.PointerProperty(type=bpy.types.Object,
                                                                      name="Fragment", description="The Fragment to add the bones to")
    bpy.types.Scene.create_bones_parent_to_selected = bpy.props.BoolProperty(
        name="Parent to selected bone", description="Parent all bones to the currently selected bone")
    bpy.types.Scene.set_mass_amount = bpy.props.FloatProperty(
        name="Mass", description="Mass", min=0)


def unregister():
    del bpy.types.Object.fragment_properties
    del bpy.types.Object.child_properties
    del bpy.types.Object.vehicle_window_properties
    del bpy.types.Object.sollumz_is_physics_child_mesh

    del bpy.types.Bone.group_properties
    del bpy.types.Bone.sollumz_use_physics

    del bpy.types.Scene.create_bones_fragment
    del bpy.types.Scene.create_bones_parent_to_selected
    del bpy.types.Scene.set_mass_amount
