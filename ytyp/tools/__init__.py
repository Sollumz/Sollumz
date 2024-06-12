import bpy
from ..gizmos.extensions import SOLLUMZ_GGT_archetype_extensions
from ..operators.extensions import SOLLUMZ_OT_delete_archetype_extension, SOLLUMZ_OT_duplicate_archetype_extension
from ..utils import get_selected_extension
from ...icons import ICON_GEOM_TOOL


class ArchetypeExtensionTool(bpy.types.WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    bl_idname = "sollumz.archetype_extension"
    bl_label = "Edit Archetype Extensions"
    bl_description = "Edit extensions of the selected archetype"
    bl_icon = ICON_GEOM_TOOL

    bl_widget = SOLLUMZ_GGT_archetype_extensions.bl_idname
    bl_keymap = (
        (SOLLUMZ_OT_delete_archetype_extension.bl_idname,
         {"type": "DEL", "value": "PRESS"}, {"properties": []}),
        (SOLLUMZ_OT_duplicate_archetype_extension.bl_idname,
         {"type": "D", "value": "PRESS", "shift": True}, {"properties": []}),
    )

    def draw_settings(context, layout, tool):
        selected_extension = get_selected_extension(context)
        if selected_extension is not None:
            layout.prop(selected_extension, "extension_type_for_archetypes")
