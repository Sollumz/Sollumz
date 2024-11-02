import bpy

from ...sollumz_ui import BasicListHelper, draw_list_with_add_remove, draw_simple_list
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ..utils import get_selected_ymap, get_active_element


class SOLLUMZ_UL_YMAP_LIST(BasicListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_YMAP_LIST"
    item_icon = "PRESET"


class SOLLUMZ_UL_ELEMENT_LIST(BasicListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ELEMENT_LIST"
    item_icon = "PRESET"


class SOLLUMZ_PT_YMAP_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Map Data"
    bl_idname = "SOLLUMZ_PT_YMAP_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 5

    def draw_header(self, context):
        self.layout.label(text="", icon="OBJECT_ORIGIN")

    def draw(self, context):
        ...

class YmapToolChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_YMAP_TOOL_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_YMAP_TOOL_PANEL.bl_category


class SOLLUMZ_PT_YMAP_LIST_PANEL(YmapToolChildPanel, bpy.types.Panel):
    bl_label = "YMAPS"
    bl_idname = "SOLLUMZ_PT_YMAP_LIST_PANEL"
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        list_col, _ = draw_list_with_add_remove(self.layout, "sollumz.createymap", "sollumz.deleteymap",
                                                SOLLUMZ_UL_YMAP_LIST.bl_idname, "", context.scene, "ymaps", context.scene, "ymap_index", rows=3)
        row = list_col.row()
        row.operator("sollumz.importymap", icon="IMPORT")
        row.operator("sollumz.exportymap", icon="EXPORT")


class SOLLUMZ_PT_YMAP_CONTENT_PANEL(YmapToolChildPanel, bpy.types.Panel):
    bl_label = "Content"
    bl_idname = "SOLLUMZ_PT_YMAP_CONTENT_PANEL"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return get_selected_ymap(context) is not None

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "selected_ymap_element")
        list_name, index = get_active_element("list", context)
        selected_ymap = get_selected_ymap(context)
        if (list_name in ["modeloccluders", "boxoccluders"] and len(selected_ymap.entities) > 0) or \
        (list_name == "entities" and max(len(selected_ymap.modeloccluders), len(selected_ymap.boxoccluders)) > 0):
            layout.label(text="Can't have Entities and Occluders")
            
        else:
            list_col = draw_simple_list(
                self.layout, SOLLUMZ_UL_ELEMENT_LIST.bl_idname, "", get_selected_ymap(context), list_name, get_selected_ymap(context), index, rows=3)
            
            row = list_col.row()
            row.operator("sollumz.addelement", icon="ADD")
            row.operator("sollumz.delelement", icon="REMOVE")
