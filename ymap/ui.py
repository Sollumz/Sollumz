import bpy

from ..sollumz_ui import SOLLUMZ_PT_TOOL_PANEL


class SOLLUMZ_UL_YMAP_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_YMAP_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon="PRESET")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="PRESET")


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
        layout.label(text="YMAPS")
        layout.template_list(
            SOLLUMZ_UL_YMAP_LIST.bl_idname, "", context.scene, "ymaps", context.scene, "ymaps_index"
        )
        row = layout.row()
        row.operator("sollumz.createymap")
        row.operator("sollumz.deleteymap")
        row = layout.row()
        row.operator("sollumz.importymap")
        row.operator("sollumz.exportymap")
