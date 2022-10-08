import bpy

from sollumz_ui import SOLLUMZ_PT_TOOL_PANEL




class SOLLUMZ_PT_YMAP_PANEL(bpy.types.Panel):
    bl_label = "YMAP Tools"
    bl_idname = "SOLLUMZ_PT_YMAP_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname


    def draw_header(self, context):
        self.layout.label(text="", icon="FILE")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("sollumz.importymap")
        row.operator("sollumz.exportymap")