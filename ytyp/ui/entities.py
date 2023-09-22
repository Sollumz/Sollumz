import bpy
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ...sollumz_ui import BasicListHelper, FlagsPanel, FilterListHelper, draw_list_with_add_remove
from ..properties.ytyp import ArchetypeType
from ..properties.mlo import EntityProperties, MloEntityProperties
from ..utils import get_selected_archetype, get_selected_entity
from .extensions import ExtensionsListHelper, ExtensionsPanelHelper
from .mlo import SOLLUMZ_PT_MLO_PANEL


class SOLLUMZ_UL_ENTITIES_LIST(BasicListHelper, FilterListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITIES_LIST"
    name_prop = "archetype_name"
    order_by_name_key = "archetype_name"
    item_icon = "OBJECT_DATA"

    def filter_item(self, item: MloEntityProperties):
        scene = bpy.context.scene
        filter_type = scene.sollumz_entity_filter_type

        if filter_type == "all":
            return True

        if filter_type == "room":
            return scene.sollumz_entity_filter_room == item.attached_room_id
        elif filter_type == "portal":
            return scene.sollumz_entity_filter_portal == item.attached_portal_id
        elif filter_type == "entity_set":
            in_entity_set = scene.sollumz_entity_filter_entity_set == item.attached_entity_set_id
            in_room = scene.sollumz_entity_filter_entity_set_room == item.attached_room_id

            if scene.sollumz_do_entity_filter_entity_set_room:
                return in_entity_set and in_room

            return in_entity_set

        return True


class SOLLUMZ_PT_MLO_ENTITY_LIST_PANEL(TabPanel, bpy.types.Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_MLO_ENTITY_LIST_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_MLO_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_MLO_PANEL
    icon = "OUTLINER"

    bl_order = 2

    @classmethod
    def poll_tab(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = False
        layout.use_property_decorate = False
        selected_archetype = get_selected_archetype(context)

        list_col, _ = draw_list_with_add_remove(self.layout, "sollumz.createmloentity", "sollumz.deletemloentity",
                                                SOLLUMZ_UL_ENTITIES_LIST.bl_idname, "", selected_archetype, "entities", selected_archetype, "entity_index")

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


class SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL(TabbedPanelHelper, bpy.types.Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITY_LIST_PANEL.bl_idname

    default_tab = "SOLLUMZ_PT_MLO_ENTITY_PANEL"

    bl_order = 3

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None


class SOLLUMZ_PT_MLO_ENTITY_PANEL(TabPanel, bpy.types.Panel):
    bl_label = "Entity"
    bl_idname = "SOLLUMZ_PT_MLO_ENTITY_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL
    icon = "OBJECT_DATA"

    bl_order = 0

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        selected_archetype = get_selected_archetype(context)
        selected_entity = get_selected_entity(context)

        layout.prop(selected_entity, "linked_object")

        layout.separator()

        row = layout.row(align=True)
        row.prop(selected_entity, "attached_portal_id")
        row.operator("sollumz.search_entity_portals", text="", icon="VIEWZOOM")

        row = layout.row(align=True)
        row.prop(selected_entity, "attached_room_id")
        row.operator("sollumz.search_entity_rooms", text="", icon="VIEWZOOM")

        row = layout.row(align=True)
        row.prop(selected_entity, "attached_entity_set_id")
        row.operator("sollumz.search_entityset", text="", icon="VIEWZOOM")

        layout.separator()

        if not selected_entity.linked_object:
            layout.prop(selected_entity, "position")
            layout.prop(selected_entity, "rotation")
            layout.prop(selected_entity, "scale_xy")
            layout.prop(selected_entity, "scale_z")
            layout.separator()

        for prop_name in EntityProperties.__annotations__:
            if prop_name == "flags":
                continue
            layout.prop(selected_entity, prop_name)


class SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST(bpy.types.UIList, ExtensionsListHelper):
    bl_idname = "SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST"


class SOLLUMZ_PT_ENTITY_EXTENSIONS_PANEL(TabPanel, ExtensionsPanelHelper, bpy.types.Panel):
    bl_label = "Entity Extensions"
    bl_idname = "SOLLUMZ_PT_ENTITY_EXTENSIONS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL
    icon = "CON_TRACKTO"

    bl_order = 1

    ADD_OPERATOR_ID = "sollumz.addentityextension"
    DELETE_OPERATOR_ID = "sollumz.deleteentityextension"
    DUPLICATE_OPERATOR_ID = "sollumz.duplicateentityextension"
    EXTENSIONS_LIST_ID = SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST.bl_idname

    @classmethod
    def get_extensions_container(self, context):
        return get_selected_entity(context)


class SOLLUMZ_PT_ENTITY_FLAGS_PANEL(TabPanel, FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ENTITY_FLAGS_PANEL"
    bl_label = "Entity Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_MLO_ENTITY_TAB_PANEL
    icon = "BOOKMARKS"

    bl_order = 2

    def get_flags(self, context):
        selected_entity = get_selected_entity(context)
        return selected_entity.flags
