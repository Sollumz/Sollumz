import bpy
from ...tabbed_panels import TabPanel, TabbedPanelHelper
from ...sollumz_ui import BasicListHelper, OrderListHelper, FlagsPanel, draw_list_with_add_remove
from ..properties.ytyp import ArchetypeType
from ..utils import get_selected_archetype, get_selected_entity_set, get_selected_entity_set_entity
from .mlo import SOLLUMZ_PT_MLO_PANEL
from ..properties.mlo import EntityProperties
from .extensions import ExtensionsListHelper, ExtensionsPanelHelper


class SOLLUMZ_UL_ENTITY_SETS_LIST(BasicListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITY_SETS_LIST"
    item_icon = "ASSET_MANAGER"


class SOLLUMZ_UL_ES_ENTITIES_LIST(BasicListHelper, OrderListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ES_ENTITIES_LIST"
    name_prop = "archetype_name"
    orderkey = "archetype_name"
    item_icon = "OBJECT_DATA"


class SOLLUMZ_PT_ENTITY_SETS_PANEL(TabPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ENTITY_SETS_PANEL"
    bl_label = "Entity Sets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_MLO_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_MLO_PANEL
    icon = "ASSET_MANAGER"

    bl_order = 5

    @classmethod
    def poll_tab(cls, context):
        selected_archetype = get_selected_archetype(context)

        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        selected_archetype = get_selected_archetype(context)
        selected_entity_set = get_selected_entity_set(context)
        selected_entity_set_entity = get_selected_entity_set_entity(context)

        layout.label(text="Entity Sets")
        draw_list_with_add_remove(self.layout, "sollumz.createentityset", "sollumz.deleteentityset",
                                  SOLLUMZ_UL_ENTITY_SETS_LIST.bl_idname, "", selected_archetype, "entity_sets", selected_archetype, "entity_set_index")
        if not selected_entity_set:
            return

        layout.separator()
        layout.label(text="Entity Set Entities")
        list_col = draw_list_with_add_remove(self.layout, "sollumz.create_entityset_entity", "sollumz.delete_entityset_entity",
                                             SOLLUMZ_UL_ES_ENTITIES_LIST.bl_idname, "", selected_entity_set, "entities", selected_entity_set, "entity_set_entity_index")
        
        if not selected_entity_set_entity:
            return

        list_col.separator()

        row = list_col.row(align=True)
        row.operator("sollumz.addobjas_entity_set_entity", icon="OUTLINER_OB_MESH")
        row.prop(context.scene, "sollumz_add_entity_entityset_room", text="", icon="CUBE")
        list_col.operator("sollumz.setobj_entity_set_entitytransforms",
                          icon="OUTLINER_DATA_EMPTY")
        
        layout.separator()


class SOLLUMZ_PT_ES_ENTITY_TAB_PANEL(TabbedPanelHelper, bpy.types.Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_ES_ENTITY_TAB_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_ENTITY_SETS_PANEL.bl_idname

    default_tab = "SOLLUMZ_PT_ES_ENTITY_PANEL"

    bl_order = 6

    @classmethod
    def poll(cls, context):
        return get_selected_entity_set_entity(context) is not None


class SOLLUMZ_PT_ES_ENTITY_PANEL(TabPanel, bpy.types.Panel):
    bl_label = "Entity"
    bl_idname = "SOLLUMZ_PT_ES_ENTITY_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ES_ENTITY_TAB_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_ES_ENTITY_TAB_PANEL
    icon = "OBJECT_DATA"

    bl_order = 0

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        selected_entity = get_selected_entity_set_entity(context)

        layout.prop(selected_entity, "linked_object")

        layout.separator()

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


class SOLLUMZ_UL_ES_ENTITY_EXTENSIONS_LIST(bpy.types.UIList, ExtensionsListHelper):
    bl_idname = "SOLLUMZ_UL_ES_ENTITY_EXTENSIONS_LIST"


class SOLLUMZ_PT_ES_ENTITY_EXTENSIONS_PANEL(TabPanel, ExtensionsPanelHelper, bpy.types.Panel):
    bl_label = "Entity Extensions"
    bl_idname = "SOLLUMZ_PT_ES_ENTITY_EXTENSIONS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ES_ENTITY_TAB_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_ES_ENTITY_TAB_PANEL
    icon = "CON_TRACKTO"

    bl_order = 1

    ADD_OPERATOR_ID = "sollumz.addentityextension"
    DELETE_OPERATOR_ID = "sollumz.deleteentityextension"
    EXTENSIONS_LIST_ID = SOLLUMZ_UL_ES_ENTITY_EXTENSIONS_LIST.bl_idname

    @classmethod
    def get_extensions_container(self, context):
        return get_selected_entity_set_entity(context)


class SOLLUMZ_PT_ES_ENTITY_FLAGS_PANEL(TabPanel, FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ES_ENTITY_FLAGS_PANEL"
    bl_label = "Entity Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ES_ENTITY_TAB_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_ES_ENTITY_TAB_PANEL
    icon = "BOOKMARKS"

    bl_order = 2

    def get_flags(self, context):
        selected_entity = get_selected_entity_set_entity(context)
        return selected_entity.flags
