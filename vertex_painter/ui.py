import bpy
from ..sollumz_ui import SOLLUMZ_PT_TOOL_PANEL
from ..tools.blenderhelper import get_addon_preferences


class SOLLUMZ_PT_VERTEX_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Vertex Painter"
    bl_idname = "SOLLUMZ_PT_VERTEX_TOOL_PANELL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname
    bl_order = 1

    @classmethod
    def poll(self, context):
        preferences = get_addon_preferences(bpy.context)
        show_panel = preferences.show_vertex_painter
        return show_panel

    def draw_header(self, context):
        self.layout.label(text="", icon="BRUSH_DATA")

    def draw(self, context):
        layout = self.layout
        settings = context.scene.sollumz_vpaint_settings

        row = layout.row()
        row.prop(context.scene, "vert_paint_color1", text="")
        row.operator(
            "sollumz.paint_vertices").color = context.scene.vert_paint_color1

        row2 = layout.row()
        row2.prop(context.scene, "vert_paint_color2", text="")
        row2.operator(
            "sollumz.paint_vertices").color = context.scene.vert_paint_color2

        row3 = layout.row()
        row3.prop(context.scene, "vert_paint_color3", text="")
        row3.operator(
            "sollumz.paint_vertices").color = context.scene.vert_paint_color3

        preferences = get_addon_preferences(bpy.context)
        extra = preferences.extra_color_swatches
        if extra:
            row4 = layout.row()
            row4.prop(context.scene, "vert_paint_color4", text="")
            row4.operator(
                "sollumz.paint_vertices").color = context.scene.vert_paint_color4

            row5 = layout.row()
            row5.prop(context.scene, "vert_paint_color5", text="")
            row5.operator(
                "sollumz.paint_vertices").color = context.scene.vert_paint_color5

            row6 = layout.row()
            row6.prop(context.scene, "vert_paint_color6", text="")
            row6.operator(
                "sollumz.paint_vertices").color = context.scene.vert_paint_color6

        col = layout.column(align=True)
        row = col.row()
        row.label(text="Active Channels")
        row = col.row(align=True)
        row.prop(settings, 'active_channels', expand=True)
        row = col.row(align=True)

        can_isolate = len(settings.active_channels) == 1
        iso_channel_id = 'R'
        if can_isolate:
            for channel_id in settings.active_channels:
                iso_channel_id = channel_id
                break
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator('sollumz.isolate_channel',
                     text="Isolate Active Channel").src_channel_id = iso_channel_id
        row.enabled = can_isolate
        row = col.row(align=True)
        row.operator("sollumz.apply_isolated")
        col = layout.column(align=True)
        row = col.row(align=True)
        row.operator('sollumz.gradient',
                     text="Linear Gradient").circular_gradient = False
        row10 = col.row(align=True)
        row10.operator('sollumz.gradient',
                       text="Circular Gradient").circular_gradient = True
