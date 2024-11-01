import bpy
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ...sollumz_ui import FlagsPanel
from .ymap import YmapToolChildPanel
from ..utils import get_selected_ymap, get_active_element

class SOLLUMZ_PT_ELEMENT_TABS_PANEL(YmapToolChildPanel, TabbedPanelHelper, bpy.types.Panel):
    bl_label = "YMAP Content"
    bl_idname = "SOLLUMZ_PT_ELEMENT_TABS_PANEL"
    bl_options = {"HIDE_HEADER"}

    default_tab = "SOLLUMZ_PT_ELEMENT_PANEL"

    bl_order = 2

    @classmethod
    def poll(cls, context):
        selected_ymap = get_selected_ymap(context)
        if selected_ymap:
            return max(len(selected_ymap.entities), len(selected_ymap.cargens),
                       len(selected_ymap.modeloccluders), len(selected_ymap.boxoccluders)) > 0

    def draw_before(self, context: bpy.types.Context):
        self.layout.separator()


class ElementChildTabPanel(TabPanel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_ELEMENT_TABS_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_ELEMENT_TABS_PANEL.bl_category

    parent_tab_panel = SOLLUMZ_PT_ELEMENT_TABS_PANEL


class ElementChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ELEMENT_TABS_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_ELEMENT_TABS_PANEL.bl_category


class SOLLUMZ_PT_ELEMENT_PANEL(ElementChildTabPanel, bpy.types.Panel):
    bl_label = "Definition"
    bl_idname = "SOLLUMZ_PT_ELEMENT_PANEL"

    icon = "SEQ_STRIP_META"

    bl_order = 0

    def draw(self, context):
        aobj = get_active_element("item", context)
        list_name, index = get_active_element("list", context)
        layout = self.layout
        grid = layout.grid_flow(columns=2, even_columns=True, even_rows=True)
        grid.use_property_split = True
        boxedgrid = grid.box()
        if list_name == "entities":
            boxedgrid.label(text="Entity Definition")
            boxedgrid.prop(aobj, "flags")
            boxedgrid.prop(aobj, "guid")
            boxedgrid.prop(aobj, "parent_index")
            boxedgrid.prop(aobj, "lod_dist")
            boxedgrid.prop(aobj, "child_lod_dist")
            boxedgrid.prop(aobj, "num_children")
            boxedgrid.prop(aobj, "ambient_occlusion_multiplier")
            boxedgrid.prop(aobj, "artificial_ambient_occlusion")
            boxedgrid.prop(aobj, "tint_value")
            boxedgrid.prop(aobj, "lod_level")
            boxedgrid.prop(aobj, "priority_level")
        elif list_name == "cargens":
            boxedgrid.label(text="Car Generator Definition")
            boxedgrid.prop(aobj, 'car_model')
            boxedgrid.prop(aobj, 'flags')
            boxedgrid.prop(aobj, 'pop_group')
            boxedgrid.prop(aobj, 'perpendicular_length')
            boxedgrid.prop(aobj, 'body_color_remap_1')
            boxedgrid.prop(aobj, 'body_color_remap_2')
            boxedgrid.prop(aobj, 'body_color_remap_3')
            boxedgrid.prop(aobj, 'body_color_remap_4')
            boxedgrid.prop(aobj, 'livery')
        elif list_name == "modeloccluders":
            boxedgrid.label(text="Model Occluder Definition")
            boxedgrid.prop(aobj, 'flags')
        elif list_name == "boxoccluders":
            boxedgrid.label(text="Box Occluder Definition")


class SOLLUMZ_PT_FLAGS_PANEL(ElementChildTabPanel, bpy.types.Panel):
    bl_label = "Flags"
    bl_idname = "SOLLUMZ_PT_FLAGS_PANEL"

    icon = "BOOKMARKS"

    bl_order = 1

    def draw(self, context):
        layout = self.layout
        layout.label(text="PLACEHOLDER")

#class SOLLUMZ_PT_ELEMENT_FLAGS_PANEL(ElementChildTabPanel, FlagsPanel, bpy.types.Panel):
#    bl_label = "Flags"
#    bl_idname = "SOLLUMZ_PT_ELEMENT_FLAGS_PANEL"
#    icon = "BOOKMARKS"
#
#    bl_order = 1
#
#    def get_flags(self, context):
#        selected_element = get_active_element("item", context)
#        return selected_element.flags