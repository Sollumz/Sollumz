import bpy
from ...tabbed_panels import TabPanel
from ...sollumz_ui import BasicListHelper, draw_list_with_add_remove
from ..properties.ytyp import ArchetypeType
from ..utils import get_selected_ytyp, get_selected_archetype
from .mlo import MloChildTabPanel


class SOLLUMZ_UL_ENTITY_SETS_LIST(BasicListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITY_SETS_LIST"
    item_icon = "ASSET_MANAGER"


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

        layout.label(text="Entity Sets")
        draw_list_with_add_remove(self.layout, "sollumz.createentityset", "sollumz.deleteentityset",
                                  SOLLUMZ_UL_ENTITY_SETS_LIST.bl_idname, "", selected_archetype, "entity_sets", selected_archetype, "entity_set_index")
