import bpy
from bpy.types import (
    Object,
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    PointerProperty,
)
import bmesh
from enum import IntEnum

from ..tools.blenderhelper import remove_number_suffix
from ..sollumz_properties import (
    SOLLUMZ_UI_NAMES,
    SollumType,
    VehicleLightID,
    MIN_VEHICLE_LIGHT_ID,
    MAX_VEHICLE_LIGHT_ID,
    items_from_enums,
    FlagPropertyGroup,
)
from ..ydr.shader_materials import (
    VEHICLE_PREVIEW_NODE_DIRT_COLOR,
    VEHICLE_PREVIEW_NODE_DIRT_LEVEL,
    VEHICLE_PREVIEW_NODE_DIRT_WETNESS,
    VEHICLE_PREVIEW_NODE_BODY_COLOR,
    VEHICLE_PREVIEW_NODE_LIGHT_EMISSIVE_TOGGLE,
)


class FragArchetypeProperties(bpy.types.PropertyGroup):
    max_speed: bpy.props.FloatProperty(name="Max Speed", default=150)
    max_ang_speed: bpy.props.FloatProperty(name="Max Angular Speed", default=6.2831855)
    gravity_factor: bpy.props.FloatProperty(name="Gravity Factor", default=1)
    buoyancy_factor: bpy.props.FloatProperty(name="Buoyancy Factor", default=1)


class LODProperties(bpy.types.PropertyGroup):
    min_move_force: bpy.props.FloatProperty(name="Min Move Force")
    unbroken_cg_offset: bpy.props.FloatVectorProperty(name="Unbroken CG Offset", subtype="XYZ")
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
    # TODO: HAS_CLOTH is needed in some dynamic fragment props with cloth so the cloth stays attached to broken parts,
    #       we might be able to automatically set it on export but I haven't seen a clear pattern yet, sometimes only
    #       the direct parent from the cloth bone has it set, sometimes the whole parent tree.
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


class VehiclePaintLayer(IntEnum):
    CUSTOM = 0
    PRIMARY = 1
    SECONDARY = 2
    PEARLESCENT = 3
    WHEEL = 4
    DEFAULT = 5
    INTERIOR_TRIM = 6
    INTERIOR_DASH = 7

    @property
    def ui_label(self) -> str:
        match self:
            case VehiclePaintLayer.CUSTOM:
                return "Custom - Not Paintable"
            case VehiclePaintLayer.PRIMARY:
                return "Primary"
            case VehiclePaintLayer.SECONDARY:
                return "Secondary"
            case VehiclePaintLayer.PEARLESCENT:
                return "Pearlescent"
            case VehiclePaintLayer.WHEEL:
                return "Wheel"
            case VehiclePaintLayer.DEFAULT:
                return "Default - Not Paintable"
            case VehiclePaintLayer.INTERIOR_TRIM:
                return "Interior Trim"
            case VehiclePaintLayer.INTERIOR_DASH:
                return "Dashboard"
            case _:
                assert False, f"Unknown paint layer {self}"


VehiclePaintLayerEnumItems = tuple((enum.name, enum.ui_label, desc, enum.value) for enum, desc in (
    (VehiclePaintLayer.CUSTOM,
        "Custom - cannot be painted at mod shops. Use 'matDiffuseColor' parameter as paint color"),
    (VehiclePaintLayer.DEFAULT,
        "Default - cannot be painted at mod shops. Use white as paint color, or grey when vehicle is scorched"),
    (VehiclePaintLayer.PRIMARY,
        "Use Primary paint color on this material"),
    (VehiclePaintLayer.SECONDARY,
        "Use Secondary paint color on this material"),
    (VehiclePaintLayer.PEARLESCENT,
        "Use Pearlescent paint color on this material. Note, this does not apply the pearlescent effect, but simply "
        "use the color chosen for pearlescent to paint this material as well"),
    (VehiclePaintLayer.WHEEL,
        "Use Wheel paint color on this material"),
    (VehiclePaintLayer.INTERIOR_TRIM,
        "Use Interior Trim paint color on this material"),
    (VehiclePaintLayer.INTERIOR_DASH,
        "Use Interior Dashboard paint color on this material"),
))


class VehicleRenderPreview(bpy.types.PropertyGroup):
    DEFAULT_DIRT_COLOR = (70/255, 60/255, 50/255)
    DEFAULT_BODY_COLOR = (1.0, 1.0, 1.0)

    def _on_each_node_tree(self, callback, callback_context):
        obj = self.id_data
        if not obj:
            return

        materials_visited = set()
        for child_obj in obj.children_recursive:
            if child_obj.type != "MESH":
                continue

            mesh = child_obj.data
            for material in mesh.materials:
                if material is None or material in materials_visited:
                    continue

                materials_visited.add(material)

                node_tree = material.node_tree
                if node_tree is None:
                    continue

                callback(node_tree, callback_context)

    @staticmethod
    def _dirt_level_update_callback():
        def _apply(node_tree, value):
            node = node_tree.nodes.get(VEHICLE_PREVIEW_NODE_DIRT_LEVEL, None)
            if node is None:
                return

            node.outputs[0].default_value = value

        def _update(self, context):
            value = self.dirt_level
            self._on_each_node_tree(_apply, value)

        return _update

    @staticmethod
    def _dirt_wetness_update_callback():
        def _apply(node_tree, value):
            node = node_tree.nodes.get(VEHICLE_PREVIEW_NODE_DIRT_WETNESS, None)
            if node is None:
                return

            node.outputs[0].default_value = value

        def _update(self, context):
            value = self.dirt_wetness
            self._on_each_node_tree(_apply, value)

        return _update

    @staticmethod
    def _dirt_color_update_callback():
        def _apply(node_tree, value):
            node = node_tree.nodes.get(VEHICLE_PREVIEW_NODE_DIRT_COLOR, None)
            if node is None:
                return

            node.inputs[0].default_value = value[0]
            node.inputs[1].default_value = value[1]
            node.inputs[2].default_value = value[2]

        def _update(self, context):
            value = self.dirt_color
            self._on_each_node_tree(_apply, value)

        return _update

    dirt_level: bpy.props.FloatProperty(
        name="Dirt Level",
        min=0.0, max=1.0,
        subtype="FACTOR",
        default=0.0,
        update=_dirt_level_update_callback(),
    )

    dirt_wetness: bpy.props.FloatProperty(
        name="Dirt Wetness",
        min=0.0, max=1.0,
        subtype="FACTOR",
        default=0.0,
        update=_dirt_wetness_update_callback(),
    )

    dirt_color: bpy.props.FloatVectorProperty(
        name="Dirt Color",
        min=0.0, max=1.0,
        size=3, subtype="COLOR",
        default=DEFAULT_DIRT_COLOR,
        update=_dirt_color_update_callback(),
    )

    @staticmethod
    def _define_light_id_property(light_id: int):
        prop_name = f"light_id_{light_id}"
        node_name = VEHICLE_PREVIEW_NODE_LIGHT_EMISSIVE_TOGGLE[light_id]

        def _apply(node_tree, value):
            node = node_tree.nodes.get(node_name, None)
            if node is None:
                return

            node.outputs[0].default_value = value

        def _update(self, context):
            value = 1.0 if self[prop_name] else 0.0

            self._on_each_node_tree(_apply, value)

        VehicleRenderPreview.__annotations__[prop_name] = bpy.props.BoolProperty(
            name=SOLLUMZ_UI_NAMES[VehicleLightID(str(light_id))],
            default=True,
            update=_update,
        )

    @staticmethod
    def _define_body_color_property(paint_layer_id: int):
        prop_name = f"body_color_{paint_layer_id}"
        node_name = VEHICLE_PREVIEW_NODE_BODY_COLOR[paint_layer_id]

        def _apply(node_tree, value):
            node = node_tree.nodes.get(node_name, None)
            if node is None:
                return

            node.inputs[0].default_value = value[0]
            node.inputs[1].default_value = value[1]
            node.inputs[2].default_value = value[2]

        def _update(self, context):
            value = self[prop_name]

            self._on_each_node_tree(_apply, value)

        VehicleRenderPreview.__annotations__[prop_name] = bpy.props.FloatVectorProperty(
            name=VehiclePaintLayer(paint_layer_id).ui_label,
            min=0.0, max=1.0,
            size=3, subtype="COLOR",
            default=VehicleRenderPreview.DEFAULT_BODY_COLOR,
            update=_update,
        )


for light_id in range(MIN_VEHICLE_LIGHT_ID, MAX_VEHICLE_LIGHT_ID+1):
    VehicleRenderPreview._define_light_id_property(light_id)
for paint_layer_id in range(1, 7+1):
    VehicleRenderPreview._define_body_color_property(paint_layer_id)


class ClothTuningFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 11

    wind_feedback: bpy.props.BoolProperty(
        name="Wind Feedback",
        description="Rotate object based on wind direction. See the object 'prop_air_windsock' as an example",
        update=FlagPropertyGroup.update_flag
    )
    flip_indices_order: bpy.props.BoolProperty(
        name="Flip Indices Order",
        description="???",
        update=FlagPropertyGroup.update_flag
    )
    # actually CLOTH_TUNE_IGNORE_DISTURBANCES but that name doesn't make sense given what this flag actually does
    flip_wind: bpy.props.BoolProperty(
        name="Flip Wind",
        description="Invert wind force direction",
        update=FlagPropertyGroup.update_flag
    )
    is_in_interior: bpy.props.BoolProperty(
        name="Is In Interior",
        description="Disable wind force",
        update=FlagPropertyGroup.update_flag
    )
    no_ped_collision: bpy.props.BoolProperty(
        name="No Ped Collision",
        description="Disable cloth interaction with peds",
        update=FlagPropertyGroup.update_flag
    )
    use_distance_threshold: bpy.props.BoolProperty(
        name="Use Distance Threshold",
        description="???. Not compatible with 'Force Vertex Resistance'",
        update=FlagPropertyGroup.update_flag
    )
    clamp_horizontal_force: bpy.props.BoolProperty(
        name="Clamp Horizontal Force",
        description="Ignore forces on the X and Y axes",
        update=FlagPropertyGroup.update_flag
    )
    flip_gravity: bpy.props.BoolProperty(
        name="Flip Gravity",
        description="Invert gravity force direction",
        update=FlagPropertyGroup.update_flag
    )
    activate_on_hit: bpy.props.BoolProperty(
        name="Activate On Hit",
        description="???",
        update=FlagPropertyGroup.update_flag
    )
    force_vertex_resistance: bpy.props.BoolProperty(
        name="Force Vertex Resistance",
        description="???. Not compatible with 'Use Distance Threshold'",
        update=FlagPropertyGroup.update_flag
    )
    update_if_visible: bpy.props.BoolProperty(
        name="Update If Visible",
        description="Only perform cloth simulation when the object is visible",
        update=FlagPropertyGroup.update_flag
    )


class ClothProperties(bpy.types.PropertyGroup):
    def _world_bounds_filter(self, obj: Object) -> bool:
        return obj.sollum_type == SollumType.BOUND_COMPOSITE and obj.parent is None

    world_bounds: PointerProperty(
        type=Object, poll=_world_bounds_filter,
        name="World Bounds",
        description=(
            f"{SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]} the cloth will collide with. These bounds should be "
            "positioned at world coordinates.\n\n"
            f"Only {SOLLUMZ_UI_NAMES[SollumType.BOUND_CAPSULE]} and {SOLLUMZ_UI_NAMES[SollumType.BOUND_PLANE]} "
            "types are supported.\n\n"
            "Cloth simulation does not interact with regular world collisions due to performance optimizations. "
            "Instead, these simplified bounds are used, typically consisting of a single plane behind the cloth to "
            "prevent it from clipping into buildings"
        )
    )

    weight: FloatProperty(name="Weight", default=1.0)
    enable_tuning: BoolProperty(name="Tuning")
    tuning_flags: PointerProperty(type=ClothTuningFlags)
    extra_force: FloatVectorProperty(
        name="Extra Force",
        description="Additional force applied to the cloth",
        subtype="XYZ",
        size=3
    )
    weight_override: FloatProperty(
        name="Weight Override",
        description="If positive, override the cloth mass",
        default=-1.0
    )
    distance_threshold: FloatProperty(
        name="Distance Threshold or Vertex Resistance",
        description=(
            "When the flag 'Use Distance Threshold' is enabled, this is the distance threshold value used. When the "
            "flag 'Force Vertex Resistance' is enabled, this is the vertex resistance value used. Otherwise, has no "
            "effect"
        )
    )
    # Wind feedback-specific properties
    rotation_rate: FloatProperty(
        name="Rotation Rate",
        description="Rate at which to rotate the object towards the wind direction",
        default=3.14159274,
        subtype="ANGLE",
        unit="ROTATION"
    )
    angle_threshold: FloatProperty(
        name="Angle Threshold",
        description="Maximum angle at which to stop rotating the object from the target wind direction",
        default=0.5235988,
        subtype="ANGLE",
        unit="ROTATION"
    )
    pin_vert: IntProperty(
        name="Pin Vertex",
        description=(
            "Index of a pinned vertex of the cloth. Used along with the middle-point of the other two non-pinned "
            "vertices to determine the current cloth direction"
        )
    )
    non_pin_vert0: IntProperty(
        name="Non-Pin Vertex 0",
        description=(
            "Index of a non-pinned vertex of the cloth. Used along with the other two pinned and non-pinned vertices "
            "to determine the current cloth direction"
        )
    )
    non_pin_vert1: IntProperty(
        name="Non-Pin Vertex 1",
        description=(
            "Index of a non-pinned vertex of the cloth. Used along with the other two pinned and non-pinned vertices "
            "to determine the current cloth direction"
        )
    )


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
    unbroken_elasticity: bpy.props.FloatProperty(name="Unbroken Elasticity")
    gravity_factor: bpy.props.FloatProperty(name="Gravity Factor", default=1.0)
    buoyancy_factor: bpy.props.FloatProperty(name="Buoyancy Factor", default=1.0)
    template_asset: bpy.props.EnumProperty(
        name="Physics Template (Peds Only)", items=FragmentTemplateAssetEnumItems,
        default=FragmentTemplateAsset.NONE.name
    )

    lod_properties: bpy.props.PointerProperty(type=LODProperties)

    cloth: bpy.props.PointerProperty(type=ClothProperties)

    vehicle_render_preview: bpy.props.PointerProperty(type=VehicleRenderPreview)


def get_light_id_of_selection(self):
    face_mode = bpy.context.scene.tool_settings.mesh_select_mode[2]

    if not face_mode or bpy.context.mode != "EDIT_MESH":
        return -1

    mesh_objs = bpy.context.objects_in_mode_unique_data[:]
    if not mesh_objs:
        return -1

    light_id = -1

    for obj in mesh_objs:
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        try:
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
        finally:
            # Make sure the bmesh is freed after each loop iteration. It can crash
            # while the user edits the mesh otherwise.
            bm.free()

    return light_id


def _get_mat_paint_layer(self: bpy.types.Material) -> int:
    """Get material paint layer (i.e Primary, Secondary) based on the value of matDiffuseColor."""
    paint_layer_int = VehiclePaintLayer.CUSTOM.value
    if self.node_tree is None:
        return paint_layer_int

    matDiffuseColor = self.node_tree.nodes.get("matDiffuseColor", None)
    if matDiffuseColor is None:
        return paint_layer_int

    x = matDiffuseColor.get("X")
    if x != 2.0:
        return paint_layer_int

    y = matDiffuseColor.get("Y")
    z = matDiffuseColor.get("Z")

    if y != z:
        return paint_layer_int

    for paint_layer in VehiclePaintLayer:
        if y == paint_layer.value:
            paint_layer_int = paint_layer.value
            break

    return paint_layer_int


def _set_mat_paint_layer(self: bpy.types.Material, value_int: int):
    """Set matDiffuseColor value from paint layer selection."""

    if self.node_tree is None or not 0 <= value_int <= 7:
        return

    matDiffuseColor = self.node_tree.nodes.get("matDiffuseColor", None)
    if matDiffuseColor is None:
        return

    if value_int == 0:
        matDiffuseColor.set_vec3((1.0, 1.0, 1.0))
        return

    matDiffuseColor.set("X", 2.0)
    matDiffuseColor.set("Y", float(value_int))
    matDiffuseColor.set("Z", float(value_int))


def _update_mat_paint_name(mat: bpy.types.Material):
    """Update material name to have [PAINT_LAYER] extension at the end."""
    def _get_paint_layer_name(_paint_layer: VehiclePaintLayer):
        if _paint_layer == VehiclePaintLayer.CUSTOM or _paint_layer == VehiclePaintLayer.DEFAULT:
            return ""
        return f"[{_paint_layer.ui_label.upper()}]"

    new_name_ext = _get_paint_layer_name(VehiclePaintLayer[mat.sz_paint_layer])
    mat_base_name = remove_number_suffix(mat.name).strip()

    # Replace existing extension
    for paint_layer in VehiclePaintLayer:
        name_ext = _get_paint_layer_name(paint_layer)
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

    bpy.types.Material.sz_paint_layer = bpy.props.EnumProperty(
        name="Paint Layer",
        items=VehiclePaintLayerEnumItems,
        default=VehiclePaintLayer.CUSTOM.value,
        get=_get_mat_paint_layer,
        set=_set_mat_paint_layer,
        update=lambda self, context: _update_mat_paint_name(self),
    )


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
    del bpy.types.Material.sz_paint_layer
