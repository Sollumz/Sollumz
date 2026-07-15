from bpy.types import Panel, WorkSpaceTool

from ...icons import ICON_GEOM_TOOL
from ...sollumz_preferences import get_theme_settings
from .lod_hierarchy import LOD_LEVEL_VIS_PROPS
from .lod_hierarchy_interact import SOLLUMZ_OT_map_lod_overlay_interact, SOLLUMZ_OT_map_lod_overlay_unlink


def _draw_display_settings(layout, wm):
    theme = get_theme_settings()
    col = layout.column()

    def toggle_with_setting(toggle_prop, text, setting_prop, setting_text):
        split = col.split(factor=0.4)
        split.prop(wm, toggle_prop, text=text)
        sub = split.row()
        sub.active = getattr(wm, toggle_prop)
        sub.prop(theme, setting_prop, text=setting_text)

    toggle_with_setting("sz_ui_map_lod_overlay_show_lines", "Lines", "map_lod_overlay_line_alpha", "Alpha")
    toggle_with_setting("sz_ui_map_lod_overlay_show_outlines", "Outlines", "map_lod_overlay_outline_alpha", "Alpha")

    layout.separator()

    split = layout.split(factor=0.4)
    col = split.column(align=True)
    col.alignment = "RIGHT"
    col.label(text="Markers")
    col = split.column(align=True)
    col.prop(theme, "map_lod_overlay_marker_size", text="Size")
    col.prop(theme, "map_lod_overlay_marker_alpha", text="Alpha")


class SOLLUMZ_PT_map_lod_overlay_display(Panel):
    """Display settings popover for the Map LOD Hierarchy tool header."""

    bl_idname = "SOLLUMZ_PT_map_lod_overlay_display"
    bl_label = "Display"
    bl_space_type = "PROPERTIES"
    bl_region_type = "HEADER"
    bl_ui_units_x = 14

    def draw(self, context):
        _draw_display_settings(self.layout, context.window_manager)


class MapLodHierarchyTool(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    bl_idname = "sollumz.map_lod_hierarchy"
    bl_label = "Map LOD Hierarchy"
    bl_description = "Display and edit LOD hierarchy connections between map entities"
    bl_icon = ICON_GEOM_TOOL

    bl_keymap = (
        (
            SOLLUMZ_OT_map_lod_overlay_interact.bl_idname,
            {"type": "LEFTMOUSE", "value": "PRESS"},
            None,
        ),
        (
            SOLLUMZ_OT_map_lod_overlay_interact.bl_idname,
            {"type": "LEFTMOUSE", "value": "PRESS", "ctrl": True},
            {"properties": [("toggle", True)]},
        ),
        (
            SOLLUMZ_OT_map_lod_overlay_unlink.bl_idname,
            {"type": "U", "value": "PRESS"},
            None,
        ),
    )

    def draw_settings(context, layout, tool):
        wm = context.window_manager

        if context.region.type == "TOOL_HEADER":
            # Compact: level visibility toggles inline, everything else in the popover
            row = layout.row(align=True)
            row.label(text="Show Levels:")
            for prop_name in LOD_LEVEL_VIS_PROPS.values():
                row.prop(wm, prop_name, toggle=True)

            layout.popover(panel=SOLLUMZ_PT_map_lod_overlay_display.bl_idname, text="Display")
        else:
            # Expanded: sidebar Tool tab and Properties editor have vertical room.
            layout.use_property_split = False
            col = layout.column(align=True)
            col.label(text="Show Levels")
            grid = col.grid_flow(row_major=True, columns=2, even_columns=True, align=True)
            for prop_name in LOD_LEVEL_VIS_PROPS.values():
                grid.prop(wm, prop_name, toggle=True)

            layout.separator()
            layout.label(text="Display")
            _draw_display_settings(layout, wm)
