import bpy
from bpy.types import (
    Panel
)
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..sollumz_properties import SollumType
from .navmesh import (
    navmesh_is_valid
)


class SOLLUMZ_PT_NAVMESH_PANEL(Panel):
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


class SOLLUMZ_PT_NAVMESH_POLY_ATTRS_PANEL(bpy.types.Panel):
    bl_label = "Polygon Attributes"
    bl_idname = "SOLLUMZ_PT_NAVMESH_POLY_ATTRS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_NAVMESH_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        navmesh_obj = context.active_object
        mesh = navmesh_obj.data

        selected_poly = mesh.sz_navmesh_selected_poly

        grid = layout.grid_flow(columns=-3)
        grid.prop(selected_poly, "is_small")
        grid.prop(selected_poly, "is_large")
        grid.prop(selected_poly, "is_pavement")
        grid.prop(selected_poly, "is_road")
        grid.prop(selected_poly, "is_near_car_node")
        grid.prop(selected_poly, "is_train_track")
        grid.prop(selected_poly, "is_in_shelter")
        grid.prop(selected_poly, "is_interior")
        grid.prop(selected_poly, "is_too_steep_to_walk_on")
        grid.prop(selected_poly, "is_water")
        grid.prop(selected_poly, "is_shallow_water")
        grid.prop(selected_poly, "is_network_spawn_candidate")
        grid.prop(selected_poly, "is_isolated")
        grid.prop(selected_poly, "lies_along_edge")

        layout.prop(selected_poly, "audio_properties")
        layout.prop(selected_poly, "ped_density", slider=True)

        col = layout.column(align=True, heading="Cover Directions")
        row = col.row(align=True)
        row.prop(selected_poly, "cover_directions", index=3, toggle=True, text="-X -Y")
        row.prop(selected_poly, "cover_directions", index=4, toggle=True, text="-Y")
        row.prop(selected_poly, "cover_directions", index=5, toggle=True, text="+X -Y")
        row = col.row(align=True)
        row.prop(selected_poly, "cover_directions", index=2, toggle=True, text="-X")
        row.label(text="")
        row.prop(selected_poly, "cover_directions", index=6, toggle=True, text="+X")
        row = col.row(align=True)
        row.prop(selected_poly, "cover_directions", index=1, toggle=True, text="-X +Y")
        row.prop(selected_poly, "cover_directions", index=0, toggle=True, text="+Y")
        row.prop(selected_poly, "cover_directions", index=7, toggle=True, text="+X +Y")


class SOLLUMZ_PT_NAVMESH_COVER_POINT_PANEL(Panel):
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
        layout.use_property_split = True
        layout.use_property_decorate = False

        cover_point_obj = context.active_object
        cover_point_props = cover_point_obj.sz_nav_cover_point

        layout.prop(cover_point_props, "cover_type")
        layout.prop(cover_point_props, "disabled")


class SOLLUMZ_PT_NAVMESH_LINK_PANEL(Panel):
    bl_label = "Link Properties"
    bl_idname = "SOLLUMZ_PT_NAVMESH_LINK_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        if aobj is None:
            return True

        if aobj.sollum_type == SollumType.NAVMESH_LINK:
            return True

        if aobj.sollum_type == SollumType.NAVMESH_LINK_TARGET:
            pobj = aobj.parent
            return pobj is not None and pobj.sollum_type == SollumType.NAVMESH_LINK

        return False

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        aobj = context.active_object
        match aobj.sollum_type:
            case SollumType.NAVMESH_LINK:
                link_obj = aobj
            case SollumType.NAVMESH_LINK_TARGET:
                link_obj = aobj.parent
        link_props = link_obj.sz_nav_link
        layout.prop(link_props, "link_type")
        layout.prop(link_props, "heading")
        layout.prop(link_props, "poly_from")
        layout.prop(link_props, "poly_to")


class SOLLUMZ_PT_NAVMESH_TOOL_PANEL(Panel):
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
