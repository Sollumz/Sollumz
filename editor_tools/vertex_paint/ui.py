"""Additional UI for Vertex Paint mode."""

import bpy
from bl_ui.space_view3d import VIEW3D_MT_paint_vertex
from bpy.props import (
    FloatProperty,
)
from bpy.types import (
    Menu,
    Panel,
    WindowManager,
)

from .gradient import SOLLUMZ_OT_vertex_paint_gradient
from .isolate import (
    SOLLUMZ_OT_vertex_paint_isolate_toggle_channel,
    isolate_get_state,
)
from .terrain import (
    SOLLUMZ_OT_vertex_paint_terrain_alpha,
    SOLLUMZ_OT_vertex_paint_terrain_texture,
)
from .utils import Channel


class SOLLUMZ_PT_vertex_paint_isolate_channels(Panel):
    bl_idname = "SOLLUMZ_PT_vertex_paint_isolate_channels"
    bl_label = "Isolate Channels"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Vertex Paint"
    bl_context = "vertexpaint"
    bl_order = 1

    def draw(self, context):
        layout = self.layout

        isolated_channels = isolate_get_state(context).channels
        row = layout.row(align=True)
        row.alignment = "CENTER"
        row.scale_x = 100.0  # increase scale to expand buttons with only icons
        for ch in Channel:
            row.operator(
                SOLLUMZ_OT_vertex_paint_isolate_toggle_channel.bl_idname,
                text="",
                icon_value=ch.icon,
                depress=ch in isolated_channels,
            ).channel = ch.value


class SOLLUMZ_PT_vertex_paint_terrain(Panel):
    bl_idname = "SOLLUMZ_PT_vertex_paint_terrain"
    bl_label = "Terrain Painter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Vertex Paint"
    bl_context = "vertexpaint"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 2

    def draw_header(self, context):
        self.layout.label(text="", icon="IMAGE")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(SOLLUMZ_OT_vertex_paint_terrain_texture.bl_idname, text="Paint Texture 1").texture = 1
        row.operator(SOLLUMZ_OT_vertex_paint_terrain_texture.bl_idname, text="Paint Texture 2").texture = 2
        row = layout.row()
        row.operator(SOLLUMZ_OT_vertex_paint_terrain_texture.bl_idname, text="Paint Texture 3").texture = 3
        row.operator(SOLLUMZ_OT_vertex_paint_terrain_texture.bl_idname, text="Paint Texture 4").texture = 4
        row = layout.row(align=True)
        alpha = context.window_manager.sz_ui_vertex_paint_terrain_alpha
        row.operator(SOLLUMZ_OT_vertex_paint_terrain_alpha.bl_idname).alpha = alpha
        row.prop(context.window_manager, "sz_ui_vertex_paint_terrain_alpha")


class SOLLUMZ_MT_vertex_painter_pie_menu(Menu):
    bl_idname = "SOLLUMZ_MT_vertex_painter_pie_menu"
    bl_label = "Sollumz Vertex Painter"

    @classmethod
    def poll(cls, context):
        return context.mode == "PAINT_VERTEX"

    def draw(self, context):
        layout = self.layout

        pie = layout.menu_pie()

        # Left
        pie.column()

        # Right
        col = pie.column()
        row = col.row(align=True)
        row.alignment = "CENTER"
        row.label(text="Terrain")
        subcol = col.column(align=True)
        subcol.scale_x = 1.0
        subcol.scale_y = 1.6
        subcol.operator(SOLLUMZ_OT_vertex_paint_terrain_texture.bl_idname, text="Texture 1").texture = 1
        subcol.operator(SOLLUMZ_OT_vertex_paint_terrain_texture.bl_idname, text="Texture 2").texture = 2
        subcol.operator(SOLLUMZ_OT_vertex_paint_terrain_texture.bl_idname, text="Texture 3").texture = 3
        subcol.operator(SOLLUMZ_OT_vertex_paint_terrain_texture.bl_idname, text="Texture 4").texture = 4

        # Bottom
        pie.column()

        # Top
        isolated_channels = isolate_get_state(context).channels
        col = pie.column()
        row = col.row(align=True)
        row.alignment = "CENTER"
        row.label(text="Isolate")
        row = col.row(align=True)
        row.scale_x = 1.6
        row.scale_y = 2.0
        row.alignment = "CENTER"
        for ch in Channel:
            row.operator(
                SOLLUMZ_OT_vertex_paint_isolate_toggle_channel.bl_idname,
                text="",
                icon_value=ch.icon,
                depress=ch in isolated_channels,
            ).channel = ch.value


def _draw_vertex_paint_menu(menu, context):
    layout = menu.layout
    layout.separator()
    layout.operator(SOLLUMZ_OT_vertex_paint_gradient.bl_idname, text="Gradient (Linear)").type = "LINEAR"
    layout.operator(SOLLUMZ_OT_vertex_paint_gradient.bl_idname, text="Gradient (Radial)").type = "RADIAL"


_addon_keymaps = []


def register():
    WindowManager.sz_ui_vertex_paint_terrain_alpha = FloatProperty(name="Alpha", min=-1, max=1)

    VIEW3D_MT_paint_vertex.append(_draw_vertex_paint_menu)

    # Keybinding for vertex paint pie menu
    wm = bpy.context.window_manager
    kc = wm.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name="3D View", space_type="VIEW_3D")
        kmi = km.keymap_items.new("wm.call_menu_pie", type="T", value="PRESS", shift=True)
        kmi.properties.name = SOLLUMZ_MT_vertex_painter_pie_menu.bl_idname

        _addon_keymaps.append((km, kmi))


def unregister():
    del WindowManager.sz_ui_vertex_paint_terrain_alpha

    VIEW3D_MT_paint_vertex.remove(_draw_vertex_paint_menu)

    for km, kmi in _addon_keymaps:
        km.keymap_items.remove(kmi)
    _addon_keymaps.clear()
