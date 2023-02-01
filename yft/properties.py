import bpy

from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType


class FragmentProperties(bpy.types.PropertyGroup):
    unk_b0: bpy.props.FloatProperty(name="UnknownB0")
    unk_b8: bpy.props.FloatProperty(name="UnknownB8")
    unk_bc: bpy.props.FloatProperty(name="UnknownBC")
    unk_c0: bpy.props.FloatProperty(name="UnknownC0", default=65280)
    unk_c4: bpy.props.FloatProperty(name="UnknownC4")
    unk_cc: bpy.props.FloatProperty(name="UnknownCC")
    gravity_factor: bpy.props.FloatProperty(name="Gravity Factor")
    buoyancy_factor: bpy.props.FloatProperty(name="Buoyancy Factor")


class LODProperties(bpy.types.PropertyGroup):
    def get_name(self) -> str:
        return f"LOD{self.number}"

    number: bpy.props.IntProperty(name="Number", default=1)

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
    # archetype properties
    archetype_name: bpy.props.StringProperty(name="Name")
    archetype_mass: bpy.props.FloatProperty(name="Mass")
    archetype_unknown_48: bpy.props.FloatProperty(name="Unknown48", default=1)
    archetype_unknown_4c: bpy.props.FloatProperty(
        name="Unknown4c", default=150)
    archetype_unknown_50: bpy.props.FloatProperty(
        name="Unknown50", default=6.28)
    archetype_unknown_54: bpy.props.FloatProperty(name="Unknown54", default=1)
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
    mass: bpy.props.FloatProperty(name="Mass", min=0)
    damaged: bpy.props.BoolProperty(name="Damaged")


class VehicleWindowProperties(bpy.types.PropertyGroup):
    unk_float_17: bpy.props.FloatProperty(name="Unk Float 17")
    unk_float_18: bpy.props.FloatProperty(name="Unk Float 18")
    cracks_texture_tiling: bpy.props.FloatProperty(
        name="Cracks Texture Tiling")


def register():
    bpy.types.Object.fragment_properties = bpy.props.PointerProperty(
        type=FragmentProperties)
    bpy.types.Object.child_properties = bpy.props.PointerProperty(
        type=ChildProperties)
    bpy.types.Object.vehicle_window_properties = bpy.props.PointerProperty(
        type=VehicleWindowProperties)
    bpy.types.Object.is_physics_child_mesh = bpy.props.BoolProperty(
        name="Is Physics Child", description="Whether or not this fragment mesh is a physics child. Usually wheels meshes are physics children.")

    bpy.types.Object.sollumz_fragment_lods = bpy.props.CollectionProperty(
        type=LODProperties)
    bpy.types.Object.sollumz_active_frag_lod_index = bpy.props.IntProperty(
        min=0)

    bpy.types.Object.glass_thickness = bpy.props.FloatProperty(
        name="Thickness", default=0.1)

    bpy.types.Scene.create_fragment_type = bpy.props.EnumProperty(
        items=[
            (SollumType.FRAGMENT.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGMENT], "Create a fragment object."),
            (SollumType.FRAGLOD.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGLOD], "Create a fragment LOD object."),
            (SollumType.FRAGGROUP.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGGROUP], "Create a fragment group object."),
            (SollumType.FRAGCHILD.value,
             SOLLUMZ_UI_NAMES[SollumType.FRAGCHILD], "Create a fragment child object."),
        ],
        name="Type",
        default=SollumType.FRAGMENT.value
    )

    bpy.types.Bone.group_properties = bpy.props.PointerProperty(
        type=GroupProperties)
    bpy.types.Bone.sollumz_use_physics = bpy.props.BoolProperty(
        name="Use Physics", description="Whether or not to use physics for this fragment bone")


def unregister():
    del bpy.types.Object.fragment_properties
    del bpy.types.Object.child_properties
    del bpy.types.Object.vehicle_window_properties
    del bpy.types.Object.is_physics_child_mesh
    del bpy.types.Object.sollumz_fragment_lods
    del bpy.types.Object.sollumz_active_frag_lod_index

    del bpy.types.Bone.group_properties
    del bpy.types.Bone.sollumz_use_physics
