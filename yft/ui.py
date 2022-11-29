import bpy
from .operators import SOLLUMZ_OT_create_fragment
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..sollumz_properties import SollumType


def draw_veh_window_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGVEHICLEWINDOW:
        for prop in obj.vehicle_window_properties.__annotations__:
            self.layout.prop(obj.vehicle_window_properties, prop)


def draw_child_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGCHILD:
        for prop in obj.child_properties.__annotations__:
            self.layout.prop(obj.child_properties, prop)


def draw_group_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGGROUP:
        layout = self.layout
        layout.prop(obj, "name")
        for prop in obj.group_properties.__annotations__:
            layout.prop(obj.group_properties, prop)


def draw_lod_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGLOD:
        layout = self.layout
        for prop in obj.lod_properties.__annotations__:
            if "archetype" in prop:
                break
            layout.prop(obj.lod_properties, prop)
        layout.separator()
        layout.label(text="Archetype Properties")
        for prop in obj.lod_properties.__annotations__:
            if not "archetype" in prop:
                continue
            layout.prop(obj.lod_properties, prop)


def draw_fragment_properties(self, context):
    obj = context.active_object
    if obj.sollum_type == SollumType.FRAGMENT:
        for prop in obj.fragment_properties.__annotations__:
            self.layout.prop(obj.fragment_properties, prop)

class SOLLUMZ_PT_FRAGMENT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Fragment Tools"
    bl_idname = "SOLLUMZ_PT_FRAGMENT_TOOL_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"
    bl_order = 6

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="PACKAGE")

    def draw(self, context):
        pass


class SOLLUMZ_PT_CREATE_FRAGMENT_PANEL(bpy.types.Panel):
    bl_label = "Create Fragment Objects"
    bl_idname = "SOLLUMZ_PT_CREATE_FRAGMENT_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_FRAGMENT_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        self.layout.label(text="", icon="CUBE")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_fragment.bl_idname)
        row.prop(context.scene, "create_fragment_type")
        grid = layout.grid_flow(columns=3, even_columns=True, even_rows=True)
        grid.prop(context.scene, "use_mesh_name")
        grid.prop(context.scene, "create_center_to_selection")
        grid.prop(context.scene, "auto_create_embedded_col")

def register():
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_fragment_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_lod_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_group_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_child_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_veh_window_properties)


def unregister():
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_fragment_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_lod_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_group_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_child_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_veh_window_properties)
