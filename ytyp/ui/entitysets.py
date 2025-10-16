import bpy
from ..properties.ytyp import ArchetypeType
from ..utils import get_selected_ytyp, get_selected_archetype
from .mlo import MloChildTabPanel
from ...shared.multiselection import (
    MultiSelectUIListMixin,
    multiselect_ui_draw_list,
)
from ..operators import ytyp as ytyp_ops


class SOLLUMZ_UL_ENTITY_SETS_LIST(MultiSelectUIListMixin, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITY_SETS_LIST"
    default_item_icon = "ASSET_MANAGER"
    multiselect_operator = ytyp_ops.SOLLUMZ_OT_archetype_select_mlo_entity_set.bl_idname


class SOLLUMZ_PT_ENTITY_SETS_PANEL(MloChildTabPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ENTITY_SETS_PANEL"
    bl_label = "Entity Sets"

    icon = "ASSET_MANAGER"

    bl_order = 5

    @classmethod
    def poll_tab(cls, context):
        selected_archetype = get_selected_archetype(context)

        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        self.layout.enabled = not get_selected_ytyp(context).archetypes.has_multiple_selection
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        selected_archetype = get_selected_archetype(context)

        multiselect_ui_draw_list(
            self.layout, selected_archetype.entity_sets,
            "sollumz.createentityset", "sollumz.deleteentityset",
            SOLLUMZ_UL_ENTITY_SETS_LIST, SOLLUMZ_MT_entity_sets_list_context_menu,
            "tool_panel"
        )


class SOLLUMZ_MT_entity_sets_list_context_menu(bpy.types.Menu):
    bl_label = "Entity Sets Specials"
    bl_idname = "SOLLUMZ_MT_entity_sets_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(ytyp_ops.SOLLUMZ_OT_archetype_select_all_mlo_entity_set.bl_idname, text="Select All")
        op1 = layout.operator(ytyp_ops.SOLLUMZ_OT_archetype_select_invert_mlo_entity_set.bl_idname, text="Invert")
        if (filter_opts := SOLLUMZ_UL_ENTITY_SETS_LIST.last_filter_options.get("entity_sets_tool_panel", None)):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)
