from bpy.types import WorkSpaceTool

from ...icons import ICON_GEOM_TOOL
from .lod_hierarchy import LOD_LEVEL_VIS_PROPS
from .lod_hierarchy_interact import SOLLUMZ_OT_map_lod_overlay_interact, SOLLUMZ_OT_map_lod_overlay_unlink


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

        # LOD level visibility toggles
        row = layout.row(align=True)
        row.label(text="Show Levels:")
        for prop_name in LOD_LEVEL_VIS_PROPS.values():
            row.prop(wm, prop_name, toggle=True)

        # Display options
        row = layout.row(align=True)

        def toggle_with_sub(toggle_prop, sub_prop):
            row.prop(wm, toggle_prop)
            if getattr(wm, toggle_prop):
                subrow = row.row()
                subrow.separator(factor=2.0)
                subrow.prop(wm, sub_prop)

        toggle_with_sub("sz_ui_map_lod_overlay_show_lines", "sz_ui_map_lod_overlay_line_alpha")
        toggle_with_sub("sz_ui_map_lod_overlay_show_labels", "sz_ui_map_lod_overlay_label_mode")
        row.prop(wm, "sz_ui_map_lod_overlay_show_lod_dist")
        toggle_with_sub("sz_ui_map_lod_overlay_show_outlines", "sz_ui_map_lod_overlay_outline_alpha")

        layout.prop(wm, "sz_ui_map_lod_overlay_marker_size")
        layout.prop(wm, "sz_ui_map_lod_overlay_marker_alpha")
