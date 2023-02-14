import bpy
from ...sollumz_ui import BasicListHelper, FlagsPanel, OrderListHelper, draw_list_with_add_remove
from ..properties.ytyp import ArchetypeType
from ..properties.mlo import EntityProperties
from ..utils import get_selected_archetype, get_selected_entity
from .extensions import ExtensionsListHelper, ExtensionsPanelHelper
from .archetype import SOLLUMZ_PT_ARCHETYPE_PANEL


class SOLLUMZ_UL_ENTITIES_LIST(BasicListHelper, OrderListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITIES_LIST"
    name_prop = "archetype_name"
    orderkey = "archetype_name"
    item_icon = "OBJECT_DATA"


class SOLLUMZ_PT_MLO_ENTITIES_PANEL(bpy.types.Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_MLO_ENTITIES_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname
    bl_order = 5

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        selected_archetype = get_selected_archetype(context)

        list_col = draw_list_with_add_remove(self.layout, "sollumz.createmloentity", "sollumz.deletemloentity",
                                             SOLLUMZ_UL_ENTITIES_LIST.bl_idname, "", selected_archetype, "entities", selected_archetype, "entity_index")
        list_col.operator("sollumz.addobjasmloentity")
        row = layout.row()
        list_col.operator("sollumz.addobjasportalentity")

        layout.separator()

        selected_entity = get_selected_entity(context)
        if selected_entity:
            layout.prop(selected_entity, "linked_object")
            row = layout.row()
            row.prop(selected_entity, "attached_portal_name",
                     text="Attached Portal")
            row.operator("sollumz.setmloentityportal")
            row.operator("sollumz.clearmloentityportal", text="", icon="X")
            row = layout.row()
            row.prop(selected_entity, "attached_room_name",
                     text="Attached Room")
            row.operator("sollumz.setmloentityroom")
            row.operator("sollumz.clearmloentityroom", text="", icon="X")
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


class SOLLUMZ_PT_ENTITY_FLAGS_PANEL(FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ENTITY_FLAGS_PANEL"
    bl_label = "Entity Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITIES_PANEL.bl_idname

    bl_order = 0

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_flags(self, context):
        selected_entity = get_selected_entity(context)
        return selected_entity.flags


class SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST(bpy.types.UIList, ExtensionsListHelper):
    bl_idname = "SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST"


class SOLLUMZ_PT_ENTITY_EXTENSIONS_PANEL(bpy.types.Panel, ExtensionsPanelHelper):
    bl_label = "Entity Extensions"
    bl_idname = "SOLLUMZ_PT_ENTITY_EXTENSIONS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITIES_PANEL.bl_idname

    bl_order = 1

    ADD_OPERATOR_ID = "sollumz.addentityextension"
    DELETE_OPERATOR_ID = "sollumz.deleteentityextension"
    EXTENSIONS_LIST_ID = SOLLUMZ_UL_ENTITY_EXTENSIONS_LIST.bl_idname

    @classmethod
    def get_extensions_container(self, context):
        return get_selected_entity(context)
