import bpy
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..ydr.ui import SOLLUMZ_PT_BONE_PANEL
from ..sollumz_properties import SollumType, BOUND_TYPES, SOLLUMZ_UI_NAMES
from ..sollumz_helper import find_sollumz_parent
from ..ydr.properties import DrawableProperties
from .properties import GroupProperties, FragmentProperties, VehicleWindowProperties
from .operators import SOLLUMZ_OT_CREATE_FRAGMENT, SOLLUMZ_OT_CREATE_BONES_AT_OBJECTS, SOLLUMZ_OT_SET_MASS


class SOLLUMZ_PT_FRAGMENT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Fragment Tools"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_TOOL_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"
    bl_order = 6

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

            self.layout.prop(obj.fragment_properties, prop)


class SOLLUMZ_PT_VEH_WINDOW_PANEL(bpy.types.Panel):
    bl_label = "Vehicle Window"
    bl_idname = "SOLLUMZ_PT_VEHICLE_WINDOW_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.sollum_type == SollumType.FRAGVEHICLEWINDOW

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object

        for prop in VehicleWindowProperties.__annotations__:
            self.layout.prop(obj.vehicle_window_properties, prop)


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
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_BONE_PHYSICS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    bl_options = {"HIDE_HEADER", "DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BONE_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_object.sollum_type == SollumType.FRAGMENT

    def draw(self, context):
        layout = self.layout

        bone = context.active_bone
        layout.separator()
        layout.label(text="Fragment")
        layout.prop(bone, "sollumz_use_physics")


class SOLLUMZ_PT_BONE_PHYSICS_SUBPANEL(bpy.types.Panel):
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_BONE_PHYSICS_SUBPANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "bone"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BONE_PHYSICS_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_bone.sollumz_use_physics == True

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        bone = context.active_bone

        for prop in GroupProperties.__annotations__:
            if prop == "mass":
                continue

            layout.prop(bone.group_properties, prop)


class SOLLUMZ_PT_PHYSICS_CHILD_PANEL(bpy.types.Panel):
    bl_label = "Physics"
    bl_idname = "SOLLUMZ_PT_PHYSICS_CHILD_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

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

        parent = find_sollumz_parent(aobj)

        if parent is None or parent.sollum_type != SollumType.DRAWABLE:
            return False

        return parent.parent is not None and parent.parent.sollum_type == SollumType.FRAGMENT

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(context.active_object, "sollumz_is_physics_child_mesh")
