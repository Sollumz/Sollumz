import bpy
from .operators import SOLLUMZ_OT_ADD_FRAG_LOD, SOLLUMZ_OT_REMOVE_FRAG_LOD
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..ydr.ui import SOLLUMZ_PT_BONE_PANEL
from ..sollumz_properties import SollumType, BOUND_TYPES
from ..sollumz_helper import find_fragment_parent
from .properties import GroupProperties, FragmentProperties, VehicleWindowProperties


class SOLLUMZ_PT_FRAGMENT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Fragment Tools"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_TOOL_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"
    bl_order = 6

    def draw_header(self, context):
        self.layout.label(text="", icon="PACKAGE")

    def draw(self, context):
        pass


class SOLLUMZ_UL_PHYS_LODS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_PHYS_LODS_LIST"

    def draw_item(
        self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text=item.get_name(), icon="NODE_COMPOSITING")


class SOLLUMZ_UL_PHYS_CHILDREN_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_PHYSICS_CHILDREN_LIST"

    def draw_item(
        self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index
    ):
        layout.label(text=f"Child {index + 1}", icon="CON_CHILDOF")


class SOLLUMZ_PT_FRAGMENT_PANEL(bpy.types.Panel):
    bl_label = "Fragment"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.sollum_type == SollumType.FRAGMENT

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object

        for prop in FragmentProperties.__annotations__:
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
    bl_label = "Physics LODs"
    bl_idname = "SOLLUMZ_PT_PHYS_LODS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        active_obj = context.view_layer.objects.active
        if active_obj is None or active_obj.sollum_type != SollumType.FRAGMENT:
            return False

        return len(active_obj.sollumz_fragment_lods) >= 0

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.view_layer.objects.active
        frag_lods = obj.sollumz_fragment_lods

        row = layout.row()
        row.template_list(
            SOLLUMZ_UL_PHYS_LODS_LIST.bl_idname, "", obj, "sollumz_fragment_lods", obj, "sollumz_active_frag_lod_index"
        )

        col = row.column()
        col.operator(SOLLUMZ_OT_ADD_FRAG_LOD.bl_idname, text="", icon="ADD")
        col.operator(SOLLUMZ_OT_REMOVE_FRAG_LOD.bl_idname,
                     text="", icon="REMOVE")

        layout.separator()

        active_lod_index = obj.sollumz_active_frag_lod_index

        if active_lod_index >= len(frag_lods):
            return

        active_lod = frag_lods[active_lod_index]

        layout.prop(active_lod, "number", text="LOD Number")
        layout.separator()

        for prop in active_lod.__annotations__:
            if "archetype" in prop:
                break

            if prop == "number":
                continue

            layout.prop(active_lod, prop)

        layout.separator()

        layout.label(text="Archetype Properties")

        for prop in active_lod.__annotations__:
            if not "archetype" in prop:
                continue

            layout.prop(active_lod, prop)


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

        # Display mass first and separated from other properties
        # since it is most important
        layout.prop(bone.group_properties, "mass")
        layout.separator()

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
        return aobj is not None and aobj.sollum_type in BOUND_TYPES and find_fragment_parent(aobj)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        aobj = context.active_object

        child_props = aobj.child_properties

        layout.prop(child_props, "mass")
        layout.prop(child_props, "Damaged")


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
        return aobj is not None and aobj.sollum_type == SollumType.FRAG_GEOM

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        layout.prop(context.active_object, "is_physics_child_mesh")
