import bpy
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..sollumz_properties import SollumType
from .navmesh import (
    navmesh_is_valid
)


class SOLLUMZ_PT_NAVMESH_PANEL(bpy.types.Panel):
    bl_label = "Navigation Mesh Properties"
    bl_idname = "SOLLUMZ_PT_NAVMESH_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and navmesh_is_valid(context.active_object)

    def draw(self, context):
        pass


class SOLLUMZ_PT_NAVMESH_COVER_POINT_PANEL(bpy.types.Panel):
    bl_label = "Cover Point Properties"
    bl_idname = "SOLLUMZ_PT_NAVMESH_COVER_POINT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.NAVMESH_COVER_POINT

    def draw(self, context):
        layout = self.layout

        cover_point_obj = context.active_object
        cover_point_props = cover_point_obj.sz_nav_cover_point

        layout.prop(cover_point_props, "point_type")


class SOLLUMZ_PT_NAVMESH_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Navigation Mesh"
    bl_idname = "SOLLUMZ_PT_NAVMESH_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 7

    def draw_header(self, context):
        self.layout.label(text="", icon="TRACKING")

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager
        layout.prop(wm, "sz_ui_nav_view_bounds")


def register():
    pass


def unregister():
    pass
