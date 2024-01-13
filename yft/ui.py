import bpy
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL, SOLLUMZ_PT_MAT_PANEL
from ..ydr.ui import SOLLUMZ_PT_BONE_PANEL
from ..ybn.ui import SOLLUMZ_PT_BOUND_PROPERTIES_PANEL
from ..sollumz_properties import MaterialType, SollumType, BOUND_TYPES
from ..sollumz_helper import find_sollumz_parent
from .properties import (
    GroupProperties, FragmentProperties, VehicleWindowProperties, VehicleLightID,
    GroupFlagBit,
)
from .operators import (
    SOLLUMZ_OT_CREATE_FRAGMENT, SOLLUMZ_OT_CREATE_BONES_AT_OBJECTS, SOLLUMZ_OT_SET_MASS, SOLLUMZ_OT_SET_LIGHT_ID,
    SOLLUMZ_OT_SELECT_LIGHT_ID, SOLLUMZ_OT_COPY_FRAG_BONE_PHYSICS
)

class SOLLUMZ_PT_FRAGMENT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Fragments"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_TOOL_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"
    bl_order = 3

    def draw_header(self, context):
        self.layout.label(text="", icon="MOD_PHYSICS")

    def draw(self, context):
        pass


class SOLLUMZ_PT_FRAGMENT_CREATE_PANEL(bpy.types.Panel):
    bl_label = "Create Fragment Objects"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_CREATE_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_TOOL_PANEL.bl_idname
    bl_order = 1

    def draw_header(self, context):
        self.layout.label(text="", icon="ADD")

    def draw(self, context):
        layout = self.layout
        layout.operator(SOLLUMZ_OT_CREATE_FRAGMENT.bl_idname,
                        icon="MOD_PHYSICS")

        layout.separator()

        row = layout.row()
        row.operator(SOLLUMZ_OT_CREATE_BONES_AT_OBJECTS.bl_idname,
                     icon="BONE_DATA")
        row = layout.row()
        row.prop(context.scene, "create_bones_fragment")
        row.prop(context.scene, "create_bones_parent_to_selected")

        layout.separator()
        layout.label(text="Wheel Instances")
        layout.operator("sollumz.generate_wheel_instances",
                        icon="OUTLINER_OB_GROUP_INSTANCE")


class SOLLUMZ_PT_FRAGMENT_SET_MASS_PANEL(bpy.types.Panel):
    bl_label = "Set Mass"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_SET_MASS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_TOOL_PANEL.bl_idname
    bl_order = 2

    def draw_header(self, context):
        self.layout.label(text="", icon="WORLD")

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator(SOLLUMZ_OT_SET_MASS.bl_idname, icon="WORLD")
        row.prop(context.scene, "set_mass_amount", text="")
        layout.operator("sollumz.calculate_mass", icon="SNAP_VOLUME")


class SOLLUMZ_PT_FRAGMENT_COPY_BONE_PHYSICS_PANEL(bpy.types.Panel):
    bl_label = "Copy Bone Physics"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_COPY_BONE_PHYSICS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_TOOL_PANEL.bl_idname
    bl_order = 4

    def draw_header(self, context):
        self.layout.label(text="", icon="BONE_DATA")

    def draw(self, context):
        layout = self.layout
        row = layout.row(align=True)
        row.operator(SOLLUMZ_OT_COPY_FRAG_BONE_PHYSICS.bl_idname, icon="BONE_DATA")


class SOLLUMZ_PT_LIGHT_ID_PANEL(bpy.types.Panel):
    bl_label = "Vehicle Light IDs"
    bl_idname = "SOLLUMZ_PT_LIGHT_ID_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_TOOL_PANEL.bl_idname
    bl_order = 3

    def draw_header(self, context):
        self.layout.label(text="", icon="OUTLINER_OB_LIGHT")

    def draw(self, context):
        layout = self.layout
        layout.use_property_decorate = False
        layout.use_property_split = True

        row = layout.row(align=True)
        row.operator(SOLLUMZ_OT_SET_LIGHT_ID.bl_idname,
                     icon="OUTLINER_OB_LIGHT")
        row.prop(context.scene, "set_vehicle_light_id", text="")

        if context.scene.set_vehicle_light_id == VehicleLightID.CUSTOM:
            layout.prop(context.scene, "set_custom_vehicle_light_id")
            layout.separator()

        row = layout.row(align=True)

        row.operator(SOLLUMZ_OT_SELECT_LIGHT_ID.bl_idname,
                     icon="GROUP_VERTEX")
        row.prop(context.scene, "select_vehicle_light_id", text="")

        if context.scene.select_vehicle_light_id == VehicleLightID.CUSTOM:
            layout.prop(context.scene, "select_custom_vehicle_light_id")
            layout.separator()

        face_mode = context.scene.tool_settings.mesh_select_mode[2]
        light_id = context.scene.selected_vehicle_light_id

        layout.separator()

        if face_mode:
            if light_id == -1:
                light_id = "N/A"
            layout.label(
                text=f"Selection Light ID: {light_id}")
        else:
            layout.label(
                text="Must be in Edit Mode > Face Selection.", icon="ERROR")


class SOLLUMZ_PT_FRAGMENT_PANEL(bpy.types.Panel):
    bl_label = "Fragment"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.FRAGMENT

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object

        for prop in FragmentProperties.__annotations__:
            if prop == "lod_properties":
                continue
            # skip flags because these don't look like they should be user-editable
            if prop == "flags":
                continue

            self.layout.prop(obj.fragment_properties, prop)


class SOLLUMZ_PT_PHYS_LODS_PANEL(bpy.types.Panel):
    bl_label = "Physics LOD Properties"
    bl_idname = "SOLLUMZ_PT_PHYS_LODS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.view_layer.objects.active
        lod_props = obj.fragment_properties.lod_properties

        for prop in lod_props.__annotations__:
            if prop == "archetype_properties":
                continue
            layout.prop(lod_props, prop)


class SOLLUMZ_PT_FRAG_ARCHETYPE_PANEL(bpy.types.Panel):
    bl_label = "Archetype Properties"
    bl_idname = "SOLLUMZ_PT_FRAG_ARCHETYPE_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.view_layer.objects.active
        arch_props = obj.fragment_properties.lod_properties.archetype_properties

        for prop in arch_props.__annotations__:
            layout.prop(arch_props, prop)


class SOLLUMZ_PT_BONE_PHYSICS_PANEL(bpy.types.Panel):
    bl_label = "Fragment Physics"
    bl_idname = "SOLLUMZ_PT_BONE_PHYSICS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BONE_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_object.sollum_type == SollumType.FRAGMENT

    def draw_header(self, context):
        bone = context.active_bone
        self.layout.prop(bone, "sollumz_use_physics", text="")

    def draw(self, context):
        bone = context.active_bone
        props = bone.group_properties

        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.active = bone.sollumz_use_physics

        col = layout.column(heading="Flags")
        col.prop(props, "flags", index=GroupFlagBit.DISAPPEAR_WHEN_DEAD, text="Disappear When Dead")
        col.prop(props, "flags", index=GroupFlagBit.DAMAGE_WHEN_BROKEN, text="Damage When Broken")
        col.prop(props, "flags", index=GroupFlagBit.DOESNT_AFFECT_VEHICLES, text="Doesn't Affect Vehicles")
        col.prop(props, "flags", index=GroupFlagBit.DOESNT_PUSH_VEHICLES_DOWN, text="Doesn't Push Vehicles Down")
        col.prop(props, "flags", index=GroupFlagBit.HAS_CLOTH, text="Has Cloth")

        col = layout.column(heading="Breakable Glass")
        row = col.row(align=True)
        row.prop(props, "flags", index=GroupFlagBit.USE_GLASS_WINDOW, text="")
        sub = row.row(align=True)
        sub.active = props.flags[GroupFlagBit.USE_GLASS_WINDOW]
        sub.prop(props, "glass_type", text="")

        col = layout.column()
        for prop in GroupProperties.__annotations__:
            if prop in {"flags", "glass_type"}:
                continue

            col.prop(props, prop)


class SOLLUMZ_PT_PHYSICS_CHILD_PANEL(bpy.types.Panel):
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_PHYSICS_CHILD_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BOUND_PROPERTIES_PANEL.bl_idname

    bl_order = 2

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj is not None and aobj.sollum_type != SollumType.BOUND_COMPOSITE and aobj.sollum_type in BOUND_TYPES and find_sollumz_parent(aobj)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        aobj = context.active_object

        child_props = aobj.child_properties

        layout.prop(child_props, "mass")


class SOLLUMZ_PT_VEH_WINDOW_PANEL(bpy.types.Panel):
    bl_label = "Vehicle Window"
    bl_idname = "SOLLUMZ_PT_VEHICLE_WINDOW_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_PHYSICS_CHILD_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj and aobj.sollum_type == SollumType.BOUND_GEOMETRY

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object
        child_props = obj.child_properties

        layout.prop(child_props, "is_veh_window")

        if not child_props.is_veh_window:
            return

        layout.separator()

        layout.prop(child_props, "window_mat")

        for prop in VehicleWindowProperties.__annotations__:
            self.layout.prop(obj.vehicle_window_properties, prop)


class SOLLUMZ_PT_FRAGMENT_GEOMETRY_PANEL(bpy.types.Panel):
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_GEOMETRY_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        if aobj is None or aobj.sollum_type != SollumType.DRAWABLE_MODEL:
            return False

        return find_sollumz_parent(aobj, parent_type=SollumType.FRAGMENT) is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(context.active_object,
                    "sollumz_is_physics_child_mesh", text="Is Wheel Mesh")


class SOLLUMZ_PT_FRAGMENT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Fragment"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_MAT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname
    bl_order = 4

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        if aobj is None or aobj.sollum_type != SollumType.DRAWABLE_MODEL:
            return False

        has_frag_parent = find_sollumz_parent(
            aobj, parent_type=SollumType.FRAGMENT) is not None
        mat = aobj.active_material

        return mat is not None and mat.sollum_type == MaterialType.SHADER and has_frag_parent

    def draw(self, context):
        layout = self.layout
        mat = context.active_object.active_material

        has_mat_diffuse_color = any(
            "matDiffuseColor" in n.name for n in mat.node_tree.nodes)
        row = layout.row()
        row.enabled = has_mat_diffuse_color
        row.prop(mat, "sollumz_paint_layer")
        if not has_mat_diffuse_color:
            layout.label(
                text="Not a paint shader. Shader must have a matDiffuseColor parameter.", icon="ERROR")
