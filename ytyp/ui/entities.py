import bpy
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ...sollumz_ui import BasicListHelper, FlagsPanel, OrderListHelper, draw_list_with_add_remove
from ..properties.ytyp import ArchetypeType
from ..properties.mlo import EntityProperties
from ..utils import get_selected_archetype, get_selected_entity
from .extensions import ExtensionsListHelper, ExtensionsPanelHelper
from .mlo import SOLLUMZ_PT_MLO_PANEL


class SOLLUMZ_UL_ENTITIES_LIST(BasicListHelper, OrderListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITIES_LIST"
    name_prop = "archetype_name"
    orderkey = "archetype_name"
    item_icon = "OBJECT_DATA"


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

        list_col = draw_list_with_add_remove(self.layout, "sollumz.createmloentity", "sollumz.deletemloentity",
                                             SOLLUMZ_UL_ENTITIES_LIST.bl_idname, "", selected_archetype, "entities", selected_archetype, "entity_index")
        list_col.separator()
        row = list_col.row(align=True)
        row.operator("sollumz.addobjasentity", icon="OUTLINER_OB_MESH")
        row.prop(context.scene, "sollumz_add_entity_portal",
                 text="", icon="OUTLINER_OB_LIGHTPROBE")
        row.prop(context.scene, "sollumz_add_entity_room", text="", icon="CUBE")
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

        row = layout.row(align=True)
        row.prop(selected_entity, "attached_entity_set_room_id")
        row.operator("sollumz.search_entitysets_rooms", text="", icon="VIEWZOOM")
        
        

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
