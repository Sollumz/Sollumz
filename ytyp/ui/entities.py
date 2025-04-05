import bpy
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ..properties.ytyp import ArchetypeType, MloEntitySelectionAccess
from ..properties.mlo import EntityProperties, MloEntityProperties
from ..utils import get_selected_ytyp, get_selected_archetype, get_selected_entity
from .extensions import ExtensionsListHelper, ExtensionsPanelHelper
from .mlo import MloChildTabPanel
from ...shared.multiselection import (
    MultiSelectCollection,
    MultiSelectUIListMixin,
    multiselect_ui_draw_list,
    MultiSelectUIFlagsPanel,
)
from ..operators import ytyp as ytyp_ops


def entities_filter_items(
    entities: MultiSelectCollection[MloEntityProperties,  MloEntitySelectionAccess],
    filter_name: str,
    use_filter_sort_reverse: bool,
    use_filter_sort_alpha: bool,
) -> tuple[list[int], list[int]]:
    from ...shared.multiselection import _default_filter_items, _BITFLAG_FILTER_ITEM
    filter_flags, filter_order = _default_filter_items(
        entities,
        filter_name,
        use_filter_sort_reverse,
        use_filter_sort_alpha,
        name_prop="archetype_name"
    )

    # After the initial name filtering, remove all entities that are filtered out
    for i, entity in enumerate(entities):
        if not entity.is_filtered():
            if not filter_flags:
                # Empty list is equivalent to all items visible
                filter_flags = [_BITFLAG_FILTER_ITEM] * len(entities)

            filter_flags[i] &= ~_BITFLAG_FILTER_ITEM


    return filter_flags, filter_order


class SOLLUMZ_UL_ENTITIES_LIST(MultiSelectUIListMixin, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITIES_LIST"
    name_prop = "archetype_name"
    # order_by_name_key = "archetype_name"
    default_item_icon = "OBJECT_DATA"
    multiselect_operator = ytyp_ops.SOLLUMZ_OT_archetype_select_mlo_entity.bl_idname

    def filter_items(self, context, data, propname):
        multiselect_collection_name = propname[:-1]  # remove '_' suffix
        collection: MultiSelectCollection = getattr(data, multiselect_collection_name)
        return entities_filter_items(collection, self.filter_name, self.use_filter_sort_reverse, self.use_filter_sort_alpha)


class SOLLUMZ_PT_MLO_ENTITY_LIST_PANEL(MloChildTabPanel, bpy.types.Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_MLO_ENTITY_LIST_PANEL"

    icon = "OUTLINER"

    bl_order = 2

    @classmethod
    def poll_tab(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        self.layout.enabled = not get_selected_ytyp(context).archetypes.has_multiple_selection
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        selected_archetype = get_selected_archetype(context)

        list_col, _ = multiselect_ui_draw_list(
            self.layout, selected_archetype.entities,
            "sollumz.createmloentity", "sollumz.deletemloentity",
            SOLLUMZ_UL_ENTITIES_LIST, SOLLUMZ_MT_entities_list_context_menu,
            "tool_panel"
        )

        filter_type = context.scene.sollumz_entity_filter_type

        row = list_col.row()
        col = row.column()
        col_row = col.row()
        col_row.label(text="Filter By", icon="FILTER")
        col_row.prop(context.scene, "sollumz_entity_filter_type", text="")

        if filter_type == "room":
            row.prop(context.scene, "sollumz_entity_filter_room", text="")
        elif filter_type == "portal":
            row.prop(context.scene, "sollumz_entity_filter_portal", text="")
        elif filter_type == "entity_set":
            col = row.column()
            col.prop(context.scene, "sollumz_entity_filter_entity_set", text="")
            col.separator()
            row = col.row()
            row.prop(context.scene, "sollumz_do_entity_filter_entity_set_room")
            row.separator()
            col = row.column()
            col.enabled = context.scene.sollumz_do_entity_filter_entity_set_room
            col.prop(context.scene,
                     "sollumz_entity_filter_entity_set_room", text="")
            list_col.separator()

        list_col.separator(factor=2)
        row = list_col.row(align=True)
        row.operator("sollumz.addobjasentity", icon="OUTLINER_OB_MESH")

        list_col.operator("sollumz.setobjentitytransforms",
                          icon="OUTLINER_DATA_EMPTY")

        layout.separator()


class SOLLUMZ_MT_entities_list_context_menu(bpy.types.Menu):
    bl_label = "Entities Specials"
    bl_idname = "SOLLUMZ_MT_entities_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op = layout.operator(ytyp_ops.SOLLUMZ_OT_archetype_select_all_mlo_entity.bl_idname, text="Select All")
        if (filter_opts := SOLLUMZ_UL_ENTITIES_LIST.last_filter_options.get("entities_tool_panel", None)):
            filter_opts.apply_to_operator(op)


class SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL(TabbedPanelHelper, bpy.types.Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITY_LIST_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_MLO_ENTITY_LIST_PANEL.bl_category

    default_tab = "SOLLUMZ_PT_MLO_ENTITY_PANEL"

    bl_order = 3

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        self.layout.enabled = not get_selected_ytyp(context).archetypes.has_multiple_selection
        super().draw(context)


class MloEntityChildTabPanel(TabPanel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL.bl_category

    parent_tab_panel = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL


class SOLLUMZ_PT_MLO_ENTITY_PANEL(MloEntityChildTabPanel, bpy.types.Panel):
    bl_label = "Entity"
    bl_idname = "SOLLUMZ_PT_MLO_ENTITY_PANEL"

    icon = "OBJECT_DATA"

    bl_order = 0

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        self.layout.enabled = not get_selected_ytyp(context).archetypes.has_multiple_selection
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        selected_archetype = get_selected_archetype(context)
        has_multiple_selection = selected_archetype.entities.has_multiple_selection
        selection = selected_archetype.entities.selection
        active = selected_archetype.entities.active_item

        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "linked_object")

        layout.separator()

        row = layout.row(align=True)
        row.prop(selection, "attached_portal_id")
        row.operator("sollumz.search_entity_portals", text="", icon="VIEWZOOM")

        row = layout.row(align=True)
        row.prop(selection, "attached_room_id")
        row.operator("sollumz.search_entity_rooms", text="", icon="VIEWZOOM")

        row = layout.row(align=True)
        row.prop(selection, "attached_entity_set_id")
        row.operator("sollumz.search_entityset", text="", icon="VIEWZOOM")

        layout.separator()

        if not active.linked_object:
            col = layout.column()
            col.enabled = not has_multiple_selection
            col.prop(active, "position")
            col.prop(active, "rotation")
            col.prop(active, "scale_xy")
            col.prop(active, "scale_z")
            layout.separator()

        for prop_name in EntityProperties.__annotations__:
            if prop_name == "flags":
                continue
            layout.prop(selection, prop_name)


class SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST(ExtensionsListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST"


class SOLLUMZ_PT_ENTITY_EXTENSIONS_PANEL(MloEntityChildTabPanel, ExtensionsPanelHelper, bpy.types.Panel):
    bl_label = "Entity Extensions"
    bl_idname = "SOLLUMZ_PT_ENTITY_EXTENSIONS_PANEL"

    icon = "CON_TRACKTO"

    bl_order = 1

    ADD_OPERATOR_ID = "sollumz.addentityextension"
    DELETE_OPERATOR_ID = "sollumz.deleteentityextension"
    DUPLICATE_OPERATOR_ID = "sollumz.duplicateentityextension"
    EXTENSIONS_LIST_ID = SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST.bl_idname

    @classmethod
    def get_extensions_container(self, context):
        return get_selected_entity(context)

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        ytyp = get_selected_ytyp(context)
        self.layout.enabled = not ytyp.archetypes.has_multiple_selection and not ytyp.archetypes.active_item.entities.has_multiple_selection
        super().draw(context)


class SOLLUMZ_PT_ENTITY_FLAGS_PANEL(MloEntityChildTabPanel, MultiSelectUIFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ENTITY_FLAGS_PANEL"
    bl_label = "Entity Flags"

    icon = "BOOKMARKS"

    bl_order = 2

    def get_flags_active(self, context):
        selected_entity = get_selected_entity(context)
        return selected_entity.flags

    def get_flags_selection(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.entities.selection.flags

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        ytyp = get_selected_ytyp(context)
        self.layout.enabled = not ytyp.archetypes.has_multiple_selection
        super().draw(context)
