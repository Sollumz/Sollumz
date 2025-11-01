"""Additional UI for Vertex Paint mode."""

import bpy
from bl_ui.space_view3d import VIEW3D_MT_paint_vertex
from bpy.props import (
    EnumProperty,
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
from .multiproxy import (
    SOLLUMZ_OT_vertex_paint_multiproxy,
    SOLLUMZ_OT_vertex_paint_multiproxy_exit,
)
from .terrain import (
    SOLLUMZ_OT_vertex_paint_terrain_alpha,
    SOLLUMZ_OT_vertex_paint_terrain_texture,
)
from .transfer import (
    SOLLUMZ_OT_vertex_paint_transfer_channels,
)
from .palette import (
    SOLLUMZ_OT_pick_palette_color,
)
from .utils import (
    Channel,
    ChannelWithNoneEnumItems,
)


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


class SOLLUMZ_PT_vertex_paint_multiproxy(Panel):
    bl_idname = "SOLLUMZ_PT_vertex_paint_multiproxy"
    bl_label = "Multi-Object Vertex Paint"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Vertex Paint"
    bl_context = "vertexpaint"
    bl_order = 2

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        if aobj and aobj.mode == "VERTEX_PAINT" and aobj.type == "MESH":
            proxy_state = aobj.sz_multiproxy_state
            if proxy_state.is_multiproxy:
                layout.operator(SOLLUMZ_OT_vertex_paint_multiproxy_exit.bl_idname, depress=True, icon="TRIA_LEFT")
                col = layout.column(align=True)
                col.scale_y = 0.9
                col.label(text="Objects:")
                for o in proxy_state.objects:
                    n = o.ref.name if o.ref else "< Deleted >"
                    col.label(text=n, icon="DOT")
            else:
                layout.operator(SOLLUMZ_OT_vertex_paint_multiproxy.bl_idname, icon="TRIA_RIGHT")


class SOLLUMZ_PT_vertex_paint_transfer_channels(Panel):
    bl_idname = "SOLLUMZ_PT_vertex_paint_transfer_channels"
    bl_label = "Transfer Channels"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Vertex Paint"
    bl_context = "vertexpaint"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 3

    def draw(self, context):
        layout = self.layout
        wm = context.window_manager

        row = layout.row()
        split = row.split()
        subrow = split.row(align=True)
        subrow.prop(wm, "sz_ui_vertex_paint_transfer_src_attr", text="", icon="GROUP_VCOL")
        subrow = split.row(align=True)
        subrow.scale_x = 100.0
        for dst_ch in Channel:
            prop = f"sz_ui_vertex_paint_transfer_src_for_dst_{dst_ch.name[0].lower()}"
            subrow.prop(wm, prop, text="")

        row = layout.row()
        split = row.split(factor=0.5)
        subrow = split.row(align=True)
        subrow.alignment = "CENTER"
        subrow.label(text="↓")
        subrow = split.row(align=True)
        subrow.alignment = "CENTER"
        subrow.label(text="↓")

        row = layout.row(align=True)
        split = row.split()
        subrow = split.row(align=True)
        subrow.prop(wm, "sz_ui_vertex_paint_transfer_dst_attr", text="", icon="GROUP_VCOL")
        subrow = split.row(align=True)
        subrow.scale_x = 100.0
        for dst_ch in Channel:
            subrow.label(text="")
            subrow.label(text="", icon_value=dst_ch.icon)
            subrow.label(text="")

        op = layout.operator(SOLLUMZ_OT_vertex_paint_transfer_channels.bl_idname, text="Transfer")
        op.src_attribute = wm.sz_ui_vertex_paint_transfer_src_attr
        op.dst_attribute = wm.sz_ui_vertex_paint_transfer_dst_attr
        op.src_for_dst_r = wm.sz_ui_vertex_paint_transfer_src_for_dst_r
        op.src_for_dst_g = wm.sz_ui_vertex_paint_transfer_src_for_dst_g
        op.src_for_dst_b = wm.sz_ui_vertex_paint_transfer_src_for_dst_b
        op.src_for_dst_a = wm.sz_ui_vertex_paint_transfer_src_for_dst_a

    @classmethod
    def register(cls):
        def _attr_enum_items(self, context):
            mesh = context.active_object.data
            active = mesh.color_attributes.active_color_name
            items = tuple(
                (attr.name, f"* {attr.name}", f"{attr.name} (Active)")
                if attr.name == active
                else (attr.name, attr.name, attr.name)
                for i, attr in enumerate(mesh.color_attributes)
            )
            _attr_enum_items._last = items
            return items

        WindowManager.sz_ui_vertex_paint_transfer_src_attr = EnumProperty(
            items=_attr_enum_items, name="Source Attribute", default=0
        )
        WindowManager.sz_ui_vertex_paint_transfer_dst_attr = EnumProperty(
            items=_attr_enum_items, name="Destination Attribute", default=0
        )
        WindowManager.sz_ui_vertex_paint_transfer_src_for_dst_r = EnumProperty(
            items=ChannelWithNoneEnumItems, name="Source Channel for Destination Red Channel", default=0
        )
        WindowManager.sz_ui_vertex_paint_transfer_src_for_dst_g = EnumProperty(
            items=ChannelWithNoneEnumItems, name="Source Channel for Destination Green Channel", default=1
        )
        WindowManager.sz_ui_vertex_paint_transfer_src_for_dst_b = EnumProperty(
            items=ChannelWithNoneEnumItems, name="Source Channel for Destination Blue Channel", default=2
        )
        WindowManager.sz_ui_vertex_paint_transfer_src_for_dst_a = EnumProperty(
            items=ChannelWithNoneEnumItems, name="Source Channel for Destination Alpha Channel", default=3
        )

    @classmethod
    def unregister(cls):
        del WindowManager.sz_ui_vertex_paint_transfer_src_attr
        del WindowManager.sz_ui_vertex_paint_transfer_dst_attr
        del WindowManager.sz_ui_vertex_paint_transfer_src_for_dst_r
        del WindowManager.sz_ui_vertex_paint_transfer_src_for_dst_g
        del WindowManager.sz_ui_vertex_paint_transfer_src_for_dst_b
        del WindowManager.sz_ui_vertex_paint_transfer_src_for_dst_a


class SOLLUMZ_PT_vertex_paint_terrain(Panel):
    bl_idname = "SOLLUMZ_PT_vertex_paint_terrain"
    bl_label = "Terrain Painter"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Vertex Paint"
    bl_context = "vertexpaint"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 4

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

    @classmethod
    def register(cls):
        WindowManager.sz_ui_vertex_paint_terrain_alpha = FloatProperty(name="Alpha", min=-1, max=1)

    @classmethod
    def unregister(cls):
        del WindowManager.sz_ui_vertex_paint_terrain_alpha


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
        col = pie.column()
        if aobj := context.active_object:
            if aobj.sz_multiproxy_state.is_multiproxy:
                col.operator(SOLLUMZ_OT_vertex_paint_multiproxy_exit.bl_idname, depress=True, icon="TRIA_LEFT")
            else:
                col.operator(SOLLUMZ_OT_vertex_paint_multiproxy.bl_idname, icon="TRIA_RIGHT")

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


class SOLLUMZ_PT_palette_picker(Panel):
    bl_idname = "SOLLUMZ_PT_palette_picker"
    bl_label = "Palette Picker"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Vertex Paint"
    bl_context = "vertexpaint"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 5

    def draw_header(self, context):
        self.layout.label(text="", icon="EYEDROPPER")

    def draw(self, context):
        layout = self.layout
        layout.operator(SOLLUMZ_OT_pick_palette_color.bl_idname, text="Pick")


def _draw_vertex_paint_menu(menu, context):
    layout = menu.layout
    layout.separator()
    layout.operator(SOLLUMZ_OT_vertex_paint_gradient.bl_idname, text="Gradient (Linear)").type = "LINEAR"
    layout.operator(SOLLUMZ_OT_vertex_paint_gradient.bl_idname, text="Gradient (Radial)").type = "RADIAL"


_addon_keymaps = []


def register():
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
    VIEW3D_MT_paint_vertex.remove(_draw_vertex_paint_menu)

    for km, kmi in _addon_keymaps:
        km.keymap_items.remove(kmi)
    _addon_keymaps.clear()
