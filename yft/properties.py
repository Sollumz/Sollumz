import bpy
import bmesh
from enum import IntEnum

from ..tools.blenderhelper import remove_number_suffix
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType, VehicleLightID, VehiclePaintLayer, items_from_enums


class FragArchetypeProperties(bpy.types.PropertyGroup):
    max_speed: bpy.props.FloatProperty(name="Max Speed", default=150)
    max_ang_speed: bpy.props.FloatProperty(name="Max Angular Speed", default=6.2831855)
    gravity_factor: bpy.props.FloatProperty(name="Gravity Factor", default=1)
    buoyancy_factor: bpy.props.FloatProperty(name="Buoyancy Factor", default=1)
    inertia_tensor: bpy.props.FloatVectorProperty(name="Inertia Tensor")


class LODProperties(bpy.types.PropertyGroup):
    smallest_ang_inertia: bpy.props.FloatProperty(name="Smallest Angular Inertia")
    largest_ang_inertia: bpy.props.FloatProperty(name="Largest Angular Inertia")
    min_move_force: bpy.props.FloatProperty(name="Min Move Force")
    position_offset: bpy.props.FloatVectorProperty(name="Position Offset")
    original_root_cg_offset: bpy.props.FloatVectorProperty(name="Original Root CG Offset")
    unbroken_cg_offset: bpy.props.FloatVectorProperty(name="Unbroken CG Offset")
    damping_linear_c: bpy.props.FloatVectorProperty(name="Damping Linear C", default=(0.02, 0.02, 0.02))
    damping_linear_v: bpy.props.FloatVectorProperty(name="Damping Linear V", default=(0.02, 0.02, 0.02))
    damping_linear_v2: bpy.props.FloatVectorProperty(name="Damping Linear V2", default=(0.01, 0.01, 0.01))
    damping_angular_c: bpy.props.FloatVectorProperty(name="Damping Angular C", default=(0.02, 0.02, 0.02))
    damping_angular_v: bpy.props.FloatVectorProperty(name="Damping Angular V", default=(0.02, 0.02, 0.02))
    damping_angular_v2: bpy.props.FloatVectorProperty(name="Damping Angular V2", default=(0.01, 0.01, 0.01))

    archetype_properties: bpy.props.PointerProperty(type=FragArchetypeProperties)


GlassTypes = (
    ("Pane", "Pane", "Pane", 0),
    ("Security", "Security", "Security", 1),
    ("Pane_Weak", "Pane Weak", "Pane Weak", 2),
)


def get_glass_type_index(glass_type_enum: str) -> int:
    for enum_name, _, _, index in GlassTypes:
        if glass_type_enum == enum_name:
            return index
    return -1


class GroupFlagBit(IntEnum):
    DISAPPEAR_WHEN_DEAD = 0
    USE_GLASS_WINDOW = 1
    DAMAGE_WHEN_BROKEN = 2
    DOESNT_AFFECT_VEHICLES = 3
    DOESNT_PUSH_VEHICLES_DOWN = 4
    HAS_CLOTH = 5


class GroupProperties(bpy.types.PropertyGroup):
    flags: bpy.props.BoolVectorProperty(name="Flags", size=len(GroupFlagBit))
    glass_type: bpy.props.EnumProperty(name="Glass Type", items=GlassTypes)
    strength: bpy.props.FloatProperty(name="Strength", default=100)
    force_transmission_scale_up: bpy.props.FloatProperty(name="Force Transmission Scale Up", default=0.25)
    force_transmission_scale_down: bpy.props.FloatProperty(name="Force Transmission Scale Down", default=0.25)
    joint_stiffness: bpy.props.FloatProperty(name="Joint Stiffness")
    min_soft_angle_1: bpy.props.FloatProperty(name="Min Soft Angle 1", default=-1)
    max_soft_angle_1: bpy.props.FloatProperty(name="Max Soft Angle 1", default=1)
    max_soft_angle_2: bpy.props.FloatProperty(name="Max Soft Angle 2", default=1)
    max_soft_angle_3: bpy.props.FloatProperty(name="Max Soft Angle 3", default=1)
    rotation_speed: bpy.props.FloatProperty(name="Rotation Speed")
    rotation_strength: bpy.props.FloatProperty(name="Rotation Strength")
    restoring_strength: bpy.props.FloatProperty(name="Restoring Strength")
    restoring_max_torque: bpy.props.FloatProperty(name="Restoring Max Torque")
    latch_strength: bpy.props.FloatProperty(name="Latch Strength")
    min_damage_force: bpy.props.FloatProperty(name="Min Damage Force", default=100)
    damage_health: bpy.props.FloatProperty(name="Damage Health", default=1000)
    weapon_health: bpy.props.FloatProperty(name="Weapon Health")
    weapon_scale: bpy.props.FloatProperty(name="Weapon Scale", default=1)
    vehicle_scale: bpy.props.FloatProperty(name="Vehicle Scale", default=1)
    ped_scale: bpy.props.FloatProperty(name="Ped Scale", default=1)
    ragdoll_scale: bpy.props.FloatProperty(name="Ragdoll Scale", default=1)
    explosion_scale: bpy.props.FloatProperty(name="Explosion Scale", default=1)
    object_scale: bpy.props.FloatProperty(name="Object Scale", default=1)
    ped_inv_mass_scale: bpy.props.FloatProperty(name="Ped Inverse Mass Scale", default=1)
    melee_scale: bpy.props.FloatProperty(name="Melee Scale", default=1)


class ChildProperties(bpy.types.PropertyGroup):
    mass: bpy.props.FloatProperty(name="Mass", min=0)
    damaged: bpy.props.BoolProperty(name="Damaged")

    window_mat: bpy.props.PointerProperty(
        type=bpy.types.Material, name="Window Material", description="The material of the window mesh (usually a vehglass shader)")
    is_veh_window: bpy.props.BoolProperty(
        name="Is Glass Window")


class VehicleWindowProperties(bpy.types.PropertyGroup):
    data_min: bpy.props.FloatProperty(name="Data Min")
    data_max: bpy.props.FloatProperty(name="Data Max")
    cracks_texture_tiling: bpy.props.FloatProperty(name="Cracks Texture Tiling", default=1.5)


class FragmentTemplateAsset(IntEnum):
    NONE = 0xFF
    FRED = 0
    WILMA = 1
    FRED_LARGE = 2
    WILMA_LARGE = 3
    ALIEN = 4


FragmentTemplateAssetEnumItems = tuple((enum.name, label, desc, enum.value) for enum, label, desc in (
    (FragmentTemplateAsset.NONE, "None", "Use physics defined in this fragment"),
    (FragmentTemplateAsset.FRED, "Fred", "Use 'z_z_fred' physics"),
    (FragmentTemplateAsset.WILMA, "Wilma", "Use 'z_z_wilma' physics"),
    (FragmentTemplateAsset.FRED_LARGE, "Fred (Large)", "Use 'z_z_fred_large' physics"),
    (FragmentTemplateAsset.WILMA_LARGE, "Wilma (Large)", "Use 'z_z_wilma_large' physics"),
    (FragmentTemplateAsset.ALIEN, "Alien", "Use 'z_z_alien' physics"),
))


class FragmentProperties(bpy.types.PropertyGroup):
    flags: bpy.props.IntProperty(name="Flags", default=1)  # TODO: rage::fragType::m_Flags
    unbroken_elasticity: bpy.props.FloatProperty(name="Unbroken Elasticity")
    gravity_factor: bpy.props.FloatProperty(name="Gravity Factor", default=1.0)
    buoyancy_factor: bpy.props.FloatProperty(name="Buoyancy Factor", default=1.0)
    template_asset: bpy.props.EnumProperty(
        name="Physics Template (Peds Only)", items=FragmentTemplateAssetEnumItems,
        default=FragmentTemplateAsset.NONE.name
    )

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
