import bpy
import bmesh

from ..tools.blenderhelper import remove_number_suffix
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType, VehicleLightID, VehiclePaintLayer, items_from_enums


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

    window_mat: bpy.props.PointerProperty(
        type=bpy.types.Material, name="Window Material", description="The material of the window mesh (usually a vehglass shader)")
    is_veh_window: bpy.props.BoolProperty(
        name="Is Glass Window")


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
    unk_c4: bpy.props.FloatProperty(name="UnknownC4", default=1.0)
    unk_cc: bpy.props.FloatProperty(name="UnknownCC")
    gravity_factor: bpy.props.FloatProperty(name="Gravity Factor", default=1.0)
    buoyancy_factor: bpy.props.FloatProperty(
        name="Buoyancy Factor", default=1.0)

    lod_properties: bpy.props.PointerProperty(type=LODProperties)


def get_light_id_of_selection(self):
    face_mode = bpy.context.scene.tool_settings.mesh_select_mode[2]

    if not face_mode or bpy.context.mode != "EDIT_MESH":
        return -1

    selected_mesh_objs = [
        obj for obj in bpy.context.selected_objects if obj.type == "MESH"]

    if not selected_mesh_objs:
        return -1

    light_id = -1

    for obj in selected_mesh_objs:
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        if not bm.loops.layers.color:
            continue

        color_layer = bm.loops.layers.color[0]

        for face in bm.faces:
            if not face.select:
                continue

            for loop in face.loops:
                loop_light_id = int(loop[color_layer][3] * 255)

                if light_id != -1 and loop_light_id != light_id:
                    return -1
                elif loop_light_id != light_id and light_id == -1:
                    light_id = loop_light_id

    return light_id


PAINT_LAYER_VALUES = {
    VehiclePaintLayer.NOT_PAINTABLE: 0,
    VehiclePaintLayer.PRIMARY: 1,
    VehiclePaintLayer.SECONDARY: 2,
    VehiclePaintLayer.WHEEL: 4,
    VehiclePaintLayer.INTERIOR_TRIM: 6,
    VehiclePaintLayer.INTERIOR_DASH: 7,
}


def update_mat_paint_name(mat: bpy.types.Material):
    """Update material name to have [PAINT_LAYER] extension at the end."""
    def get_paint_layer_name(_paint_layer: VehiclePaintLayer):
        if _paint_layer == VehiclePaintLayer.NOT_PAINTABLE:
            return ""
        return f"[{SOLLUMZ_UI_NAMES[_paint_layer].upper()}]"

    new_name_ext = get_paint_layer_name(mat.sollumz_paint_layer)
    mat_base_name = remove_number_suffix(mat.name).strip()

    # Replace existing extension
    for paint_layer in VehiclePaintLayer:
        name_ext = get_paint_layer_name(paint_layer)
        if name_ext in mat_base_name:
            mat_base_name = mat_base_name.replace(name_ext, "").strip()

    if new_name_ext:
        mat.name = f"{mat_base_name} {new_name_ext}"
    else:
        mat.name = mat_base_name


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

    bpy.types.Scene.set_vehicle_light_id = bpy.props.EnumProperty(items=items_from_enums(
        VehicleLightID, exclude=VehicleLightID.NONE), name="Vehicle Light ID", description="Determines which action causes the emissive shader to activate (this is stored in the alpha channel of the vertex colors)")
    bpy.types.Scene.select_vehicle_light_id = bpy.props.EnumProperty(items=items_from_enums(
        VehicleLightID, exclude=VehicleLightID.NONE), name="Vehicle Light ID", description="Determines which action causes the emissive shader to activate (this is stored in the alpha channel of the vertex colors)")
    bpy.types.Scene.set_custom_vehicle_light_id = bpy.props.IntProperty(
        name="Custom")
    bpy.types.Scene.select_custom_vehicle_light_id = bpy.props.IntProperty(
        name="Custom")
    bpy.types.Scene.selected_vehicle_light_id = bpy.props.IntProperty(
        name="Light ID", get=get_light_id_of_selection)

    bpy.types.Material.sollumz_paint_layer = bpy.props.EnumProperty(
        items=(
            (VehiclePaintLayer.NOT_PAINTABLE.value, SOLLUMZ_UI_NAMES[VehiclePaintLayer.NOT_PAINTABLE],
             "Material cannot be painted at mod shops"),
            (VehiclePaintLayer.PRIMARY.value, SOLLUMZ_UI_NAMES[VehiclePaintLayer.PRIMARY],
             "Primary paint color will use this material"),
            (VehiclePaintLayer.SECONDARY.value, SOLLUMZ_UI_NAMES[VehiclePaintLayer.SECONDARY],
             "Secondary paint color will use this material"),
            (VehiclePaintLayer.WHEEL.value, SOLLUMZ_UI_NAMES[VehiclePaintLayer.WHEEL],
             "Wheel color will use this material"),
            (VehiclePaintLayer.INTERIOR_TRIM.value, SOLLUMZ_UI_NAMES[VehiclePaintLayer.INTERIOR_TRIM],
             "Interior trim color will use this material"),
            (VehiclePaintLayer.INTERIOR_DASH.value, SOLLUMZ_UI_NAMES[VehiclePaintLayer.INTERIOR_DASH],
             "Interior dash color will use this material"),
        ),
        name="Paint Layer", default=VehiclePaintLayer.NOT_PAINTABLE, update=lambda mat, context: update_mat_paint_name(mat))


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
    del bpy.types.Scene.set_vehicle_light_id
    del bpy.types.Scene.select_vehicle_light_id
    del bpy.types.Scene.set_custom_vehicle_light_id
    del bpy.types.Scene.select_custom_vehicle_light_id
    del bpy.types.Scene.selected_vehicle_light_id
    del bpy.types.Material.sollumz_paint_layer
