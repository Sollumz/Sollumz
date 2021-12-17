import bpy

from ..sollumz_properties import ArchetypeType, EntityProperties
from .properties import *
from ..sollumz_ui import FlagsPanel, OrderListHelper, TimeFlagsPanel


class SOLLUMZ_UL_YTYP_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_YTYP_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon="PRESET")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="PRESET")


class SOLLUMZ_PT_YTYP_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Archetype Definition"
    bl_idname = "SOLLUMZ_PT_YTYP_TOOL_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_category = "Sollumz Tools"

    def draw_header(self, context):
        self.layout.label(text="", icon="OBJECT_DATA")

    def draw(self, context):
        layout = self.layout
        layout.label(text="YTYPS")
        layout.template_list(
            SOLLUMZ_UL_YTYP_LIST.bl_idname, "", context.scene, "ytyps", context.scene, "ytyp_index"
        )
        row = layout.row()
        row.operator("sollumz.createytyp")
        row.operator("sollumz.deleteytyp")
        row = layout.row()
        row.operator("sollumz.importytyp")
        row.operator("sollumz.exportytyp")


class SOLLUMZ_UL_ARCHETYPE_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ARCHETYPE_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon="SEQ_STRIP_META")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="SEQ_STRIP_META")


class SOLLUMZ_PT_YTYP_PANEL(bpy.types.Panel):
    bl_label = "YTYP"
    bl_idname = "SOLLUMZ_PT_YTYP_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_YTYP_TOOL_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return get_selected_ytyp(context) is not None

    def draw(self, context):
        layout = self.layout
        selected_ytyp = get_selected_ytyp(context)
        layout.prop(selected_ytyp, "name")
        layout.label(text="Archetypes:")
        layout.template_list(SOLLUMZ_UL_ARCHETYPE_LIST.bl_idname, "",
                             selected_ytyp, "archetypes", selected_ytyp, "archetype_index")
        row = layout.row()
        row.operator("sollumz.createarchetype")
        row.operator("sollumz.deletearchetype")
        layout.separator()
        row = layout.row()
        row.operator("sollumz.createarchetypefromselected")
        row.prop(context.scene, "create_archetype_type", text="")


class SOLLUMZ_UL_ROOM_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ROOM_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon="CUBE")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="CUBE")


class SOLLUMZ_UL_PORTAL_LIST(OrderListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_PORTAL_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        name = f"{index}: {item.name}"
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=name, icon="OUTLINER_OB_LIGHTPROBE")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=name, emboss=False, icon="OUTLINER_OB_LIGHTPROBE")


class SOLLUMZ_UL_TIMECYCLE_MODIFIER_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_TIMECYCLE_MODIFIER_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon="TIME")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="TIME")


class SOLLUMZ_UL_ENTITIES_LIST(OrderListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ENTITIES_LIST"
    orderkey = "archetype_name"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        name = f"{item.archetype_name if len(item.archetype_name) > 0 else 'Unknown'}"
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=name, icon="OBJECT_DATA")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=name, emboss=False, icon="OBJECT_DATA")


class SOLLUMZ_PT_ARCHETYPE_PANEL(bpy.types.Panel):
    bl_label = "Archetype"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_YTYP_PANEL.bl_idname

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        selected_archetype = get_selected_archetype(context)
        layout.prop(selected_archetype, "type")
        layout.prop(selected_archetype, "name")
        layout.prop(selected_archetype, "special_attribute")
        layout.prop(selected_archetype, "texture_dictionary")
        layout.prop(selected_archetype, "clip_dictionary")
        layout.prop(selected_archetype, "drawable_dictionary")
        layout.prop(selected_archetype, "physics_dictionary")
        layout.prop(selected_archetype, "asset_type")
        layout.prop(selected_archetype, "asset_name")
        layout.prop(selected_archetype, "asset", text="Linked Object")


class SOLLUMZ_PT_MLO_FLAGS_PANEL(FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_MLO_FLAGS_PANEL"
    bl_label = "MLO Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname

    @classmethod
    def poll(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.type == ArchetypeType.MLO

    def get_flags(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.mlo_flags


class SOLLUMZ_PT_YTYP_TIME_FLAGS_PANEL(TimeFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_YTYP_TIME_FLAGS_PANEL"
    bl_label = "Time Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname
    select_operator = "sollumz.ytyp_time_flags_select_range"
    clear_operator = "sollumz.ytyp_time_flags_clear"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def get_flags(self, context):
        return get_selected_archetype(context).time_flags


class SOLLUMZ_PT_ARCHETYPE_FLAGS_PANEL(FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_FLAGS_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname

    def get_flags(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.flags


class SOLLUMZ_PT_ROOM_PANEL(bpy.types.Panel):
    bl_label = "Rooms"
    bl_idname = "SOLLUMZ_PT_ROOM_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname
    bl_order = 0

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)

        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        selected_archetype = get_selected_archetype(context)

        layout.template_list(SOLLUMZ_UL_ROOM_LIST.bl_idname, "",
                             selected_archetype, "rooms", selected_archetype, "room_index")
        row = layout.row()
        row.operator("sollumz.createroom")
        row.operator("sollumz.deleteroom")
        row = layout.row()
        row.operator("sollumz.createlimboroom")
        row = layout.row()
        row.use_property_split = False
        row.prop(context.scene, "show_room_gizmo")
        if not selected_archetype.asset:
            layout.label(
                text="Gizmo will not appear when no object is linked.", icon="ERROR")
            layout.separator()
        layout.separator()

        selected_room = get_selected_room(context)
        if selected_room:
            for prop_name in RoomProperties.__annotations__:
                if prop_name in ["flags", "id"]:
                    continue
                layout.prop(selected_room, prop_name)
            layout.separator()
            layout.operator("sollumz.setroomboundsfromselection")


class SOLLUMZ_PT_ROOM_FLAGS_PANEL(FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ROOM_FLAGS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ROOM_PANEL.bl_idname

    @classmethod
    def poll(self, context):
        return get_selected_room(context) is not None

    def get_flags(self, context):
        selected_room = get_selected_room(context)
        return selected_room.flags


class SOLLUMZ_PT_PORTAL_PANEL(bpy.types.Panel):
    bl_label = "Portals"
    bl_idname = "SOLLUMZ_PT_PORTAL_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname
    bl_order = 1

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        selected_archetype = get_selected_archetype(context)

        layout.template_list(SOLLUMZ_UL_PORTAL_LIST.bl_idname, "",
                             selected_archetype, "portals", selected_archetype, "portal_index")
        row = layout.row()
        row.operator("sollumz.createportal")
        row.operator("sollumz.deleteportal")
        row = layout.row()
        row.operator("sollumz.createportalfromselection")
        row = layout.row()
        row.use_property_split = False
        row.prop(context.scene, "show_portal_gizmo")
        if not selected_archetype.asset:
            layout.label(
                text="Gizmo will not appear when no object is linked.", icon="ERROR")
            layout.separator()

        layout.separator()

        selected_portal = get_selected_portal(context)
        if selected_portal:
            for prop_name in PortalProperties.__annotations__:
                if prop_name in ["room_from_index", "room_to_index", "name", "room_from_id", "room_to_id", "flags", "id"]:
                    continue
                row = layout.row()
                row.prop(selected_portal, prop_name)
                if prop_name == "room_from_name":
                    row.operator("sollumz.setportalroomfrom")
                elif prop_name == "room_to_name":
                    row.operator("sollumz.setportalroomto")


class SOLLUMZ_PT_PORTAL_FLAGS_PANEL(FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_PORTAL_FLAGS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_PORTAL_PANEL.bl_idname

    @classmethod
    def poll(self, context):
        return get_selected_portal(context) is not None

    def get_flags(self, context):
        selected_portal = get_selected_portal(context)
        return selected_portal.flags


class SOLLUMZ_PT_MLO_ENTITIES_PANEL(bpy.types.Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_MLO_ENTITIES_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname
    bl_order = 2

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        selected_archetype = get_selected_archetype(context)

        layout.template_list(SOLLUMZ_UL_ENTITIES_LIST.bl_idname, "",
                             selected_archetype, "entities", selected_archetype, "entity_index")
        row = layout.row()
        row.operator("sollumz.createmloentity")
        row.operator("sollumz.deletemloentity")
        row = layout.row()
        row.operator("sollumz.addobjasmloentity")

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
                for prop_name in UnlinkedEntityProperties.__annotations__:
                    if prop_name == "linked_object":
                        continue
                    layout.prop(selected_entity, prop_name)
                layout.separator()
            for prop_name in EntityProperties.__annotations__:
                if prop_name == "flags":
                    continue
                layout.prop(selected_entity, prop_name)


class SOLLUMZ_PT_ENTITY_FLAGS_PANEL(FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ENTITY_FLAGS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_MLO_ENTITIES_PANEL.bl_idname

    @classmethod
    def poll(self, context):
        return get_selected_entity(context) is not None

    def get_flags(self, context):
        selected_entity = get_selected_entity(context)
        return selected_entity.flags


class SOLLUMZ_PT_TIMECYCLE_MODIFIER_PANEL(bpy.types.Panel):
    bl_label = "Timecycle Modifiers"
    bl_idname = "SOLLUMZ_PT_TIMECYCLE_MODIFIER_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname
    bl_order = 3

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)

        return selected_archetype.type == ArchetypeType.MLO

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        selected_archetype = get_selected_archetype(context)

        layout.template_list(SOLLUMZ_UL_TIMECYCLE_MODIFIER_LIST.bl_idname, "",
                             selected_archetype, "timecycle_modifiers", selected_archetype, "tcm_index")
        row = layout.row()
        row.operator("sollumz.createtimecyclemodifier")
        row.operator("sollumz.deletetimecyclemodifier")

        layout.separator()

        selected_tcm = get_selected_tcm(context)
        if selected_tcm:
            for prop_name in TimecycleModifierProperties.__annotations__:
                layout.prop(selected_tcm, prop_name)
