import bpy
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ..properties.ytyp import ArchetypeType
from ..properties.mlo import RoomProperties
from ..utils import get_selected_archetype, get_selected_room, get_selected_portal, get_selected_ytyp
from .archetype import ArchetypeChildPanel
from ...shared.multiselection import (
    MultiSelectUIListMixin,
    multiselect_ui_draw_list,
    MultiSelectUIFlagsPanel,
)
from ..operators import ytyp as ytyp_ops


class SOLLUMZ_PT_MLO_PANEL(ArchetypeChildPanel, TabbedPanelHelper, bpy.types.Panel):
    bl_label = "MLO"
    bl_idname = "SOLLUMZ_PT_MLO_PANEL"
    bl_options = {"HIDE_HEADER"}

    default_tab = "SOLLUMZ_PT_ROOM_PANEL"

    bl_order = 3

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype is not None and selected_archetype.type == ArchetypeType.MLO

    def draw_before(self, context: bpy.types.Context):
        self.layout.label(text="MLO")


class MloChildTabPanel(TabPanel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_MLO_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_MLO_PANEL.bl_category

    parent_tab_panel = SOLLUMZ_PT_MLO_PANEL


class SOLLUMZ_UL_ROOM_LIST(MultiSelectUIListMixin, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ROOM_LIST"
    default_item_icon = "CUBE"
    multiselect_operator = ytyp_ops.SOLLUMZ_OT_archetype_select_mlo_room.bl_idname


class SOLLUMZ_PT_ROOM_PANEL(MloChildTabPanel, bpy.types.Panel):
    bl_label = "Rooms"
    bl_idname = "SOLLUMZ_PT_ROOM_PANEL"

    icon = "CUBE"

    bl_order = 0

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

        list_col, _ = multiselect_ui_draw_list(
            self.layout, selected_archetype.rooms,
            "sollumz.createroom", "sollumz.deleteroom",
            SOLLUMZ_UL_ROOM_LIST, SOLLUMZ_MT_rooms_list_context_menu,
            "tool_panel"
        )

        list_col.operator("sollumz.createlimboroom")

        row = layout.row()
        row.use_property_split = False
        row.prop(context.scene, "show_room_gizmo")

        if not selected_archetype.asset and context.scene.show_room_gizmo:
            row = layout.row()
            row.alert = True
            row.label(
                text="Gizmo will not appear when no object is linked.")

        if len(selected_archetype.rooms) == 0:
            return

        # has_multiple_selection = selected_archetype.rooms.has_multiple_selection
        selection = selected_archetype.rooms.selection
        # active = selected_archetype.rooms.active_item

        layout.separator()
        for prop_name in RoomProperties.__annotations__:
            if prop_name in ["flags", "id", "uuid"]:
                continue
            layout.prop(selection.owner, getattr(selection.propnames, prop_name))

        list_col.operator(
            "sollumz.setroomboundsfromselection", icon="GROUP_VERTEX")


class SOLLUMZ_MT_rooms_list_context_menu(bpy.types.Menu):
    bl_label = "Rooms Specials"
    bl_idname = "SOLLUMZ_MT_rooms_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op = layout.operator(ytyp_ops.SOLLUMZ_OT_archetype_select_all_mlo_room.bl_idname, text="Select All")
        if (filter_opts := SOLLUMZ_UL_ROOM_LIST.last_filter_options.get("rooms_tool_panel", None)):
            filter_opts.apply_to_operator(op)


class SOLLUMZ_PT_ROOM_FLAGS_PANEL(MultiSelectUIFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ROOM_FLAGS_PANEL"
    bl_label = "Room Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ROOM_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_ROOM_PANEL.bl_category

    @classmethod
    def poll(cls, context):
        return get_selected_room(context) is not None

    def get_flags_active(self, context):
        selected_room = get_selected_room(context)
        return selected_room.flags

    def get_flags_selection(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.rooms.selection.flags

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        ytyp = get_selected_ytyp(context)
        self.layout.enabled = not ytyp.archetypes.has_multiple_selection
        super().draw(context)


class SOLLUMZ_UL_PORTAL_LIST(MultiSelectUIListMixin, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_PORTAL_LIST"
    default_item_icon = "OUTLINER_OB_LIGHTPROBE"
    name_editable = False
    multiselect_operator = ytyp_ops.SOLLUMZ_OT_archetype_select_mlo_portal.bl_idname

    def filter_items(self, context, data, propname):
        # NOTE: for some unknown reason, the Blender default filter by name does not work with this list. As soon as
        # you type something, all portals disappear. Even though, it works just fine in other lists like rooms or
        # entity sets...
        # So just override the filter but with our implementation of the default filter...
        multiselect_collection_name = propname[:-1]  # remove '_' suffix
        collection = getattr(data, multiselect_collection_name)
        from ...shared.multiselection import _default_filter_items
        return _default_filter_items(collection, self.filter_name, self.use_filter_sort_reverse, self.use_filter_sort_alpha)


class SOLLUMZ_PT_PORTAL_PANEL(MloChildTabPanel, bpy.types.Panel):
    bl_label = "Portals"
    bl_idname = "SOLLUMZ_PT_PORTAL_PANEL"

    icon = "OUTLINER_OB_LIGHTPROBE"

    bl_order = 1

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

        list_col, _ = multiselect_ui_draw_list(
            self.layout, selected_archetype.portals,
            "sollumz.createportal", "sollumz.deleteportal",
            SOLLUMZ_UL_PORTAL_LIST, SOLLUMZ_MT_portals_list_context_menu,
            "tool_panel"
        )

        row = list_col.row()
        row.operator("sollumz.createportalfromselection",
                     text="Create From Vertices", icon="GROUP_VERTEX")
        row.prop(context.scene, "sollumz_add_portal_room_from",
                 icon="CUBE", text="")

        row.label(text="", icon="FORWARD")

        row.prop(context.scene, "sollumz_add_portal_room_to",
                 icon="CUBE", text="")

        list_col.separator(factor=2)

        row = list_col.row(align=True)
        row.operator("sollumz.updateportalfromselection",
                     text="Update From Vertices", icon="GROUP_VERTEX")
        row.operator("sollumz.flipportal",
                     text="Flip Direction", icon="LOOP_FORWARDS")

        row = layout.row()
        row.use_property_split = False
        row.prop(context.scene, "show_portal_gizmo")

        if not selected_archetype.asset and context.scene.show_portal_gizmo:
            row = layout.row()
            row.alert = True
            row.label(text="Gizmo will not appear when no object is linked.")

        if len(selected_archetype.portals) == 0:
            return

        # has_multiple_selection = selected_archetype.portals.has_multiple_selection
        selection = selected_archetype.portals.selection
        # active = selected_archetype.portals.active_item

        layout.separator()

        layout.prop(selection.owner, selection.propnames.corner1)
        layout.prop(selection.owner, selection.propnames.corner2)
        layout.prop(selection.owner, selection.propnames.corner3)
        layout.prop(selection.owner, selection.propnames.corner4)

        layout.separator()

        row = layout.row()
        row.prop(selection.owner, selection.propnames.room_from_id)
        row.operator("sollumz.search_portal_room_from",
                     text="", icon="VIEWZOOM")
        row = layout.row()
        row.prop(selection.owner, selection.propnames.room_to_id)
        row.operator("sollumz.search_portal_room_to", text="", icon="VIEWZOOM")

        layout.separator()
        layout.prop(selection.owner, selection.propnames.mirror_priority)
        layout.prop(selection.owner, selection.propnames.opacity)
        layout.prop(selection.owner, selection.propnames.audio_occlusion)


class SOLLUMZ_MT_portals_list_context_menu(bpy.types.Menu):
    bl_label = "Portals Specials"
    bl_idname = "SOLLUMZ_MT_portals_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op = layout.operator(ytyp_ops.SOLLUMZ_OT_archetype_select_all_mlo_portal.bl_idname, text="Select All")
        if (filter_opts := SOLLUMZ_UL_PORTAL_LIST.last_filter_options.get("portals_tool_panel", None)):
            filter_opts.apply_to_operator(op)


class SOLLUMZ_PT_PORTAL_FLAGS_PANEL(MultiSelectUIFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_PORTAL_FLAGS_PANEL"
    bl_label = "Portal Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_PORTAL_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_PORTAL_PANEL.bl_category

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def get_flags_active(self, context):
        selected_portal = get_selected_portal(context)
        return selected_portal.flags

    def get_flags_selection(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.portals.selection.flags

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        ytyp = get_selected_ytyp(context)
        self.layout.enabled = not ytyp.archetypes.has_multiple_selection
        super().draw(context)


class SOLLUMZ_UL_TIMECYCLE_MODIFIER_LIST(MultiSelectUIListMixin, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_TIMECYCLE_MODIFIER_LIST"
    default_item_icon = "MOD_TIME"
    multiselect_operator = ytyp_ops.SOLLUMZ_OT_archetype_select_mlo_tcm.bl_idname


class SOLLUMZ_PT_TIMECYCLE_MODIFIER_PANEL(MloChildTabPanel, bpy.types.Panel):
    bl_label = "Timecycle Modifiers"
    bl_idname = "SOLLUMZ_PT_TIMECYCLE_MODIFIER_PANEL"

    icon = "MOD_TIME"

    bl_order = 3

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
            self.layout, selected_archetype.timecycle_modifiers,
            "sollumz.createtimecyclemodifier", "sollumz.deletetimecyclemodifier",
            SOLLUMZ_UL_TIMECYCLE_MODIFIER_LIST, SOLLUMZ_MT_timecycle_modifiers_list_context_menu,
            "tool_panel"
        )

        row = layout.row()
        row.use_property_split = False
        row.prop(context.scene, "show_mlo_tcm_gizmo")

        if not selected_archetype.asset and context.scene.show_mlo_tcm_gizmo:
            row = layout.row()
            row.alert = True
            row.label(text="Gizmo will not appear when no object is linked.")

        if len(selected_archetype.timecycle_modifiers) == 0:
            return

        # has_multiple_selection = selected_archetype.timecycle_modifiers.has_multiple_selection
        selection = selected_archetype.timecycle_modifiers.selection
        # active = selected_archetype.timecycle_modifiers.active_item

        layout.separator()

        layout.prop(selection.owner, selection.propnames.name)
        layout.prop(selection.owner, selection.propnames.sphere_center)
        layout.prop(selection.owner, selection.propnames.sphere_radius)
        layout.prop(selection.owner, selection.propnames.percentage)
        layout.prop(selection.owner, selection.propnames.range)
        layout.prop(selection.owner, selection.propnames.start_hour)
        layout.prop(selection.owner, selection.propnames.end_hour)


class SOLLUMZ_MT_timecycle_modifiers_list_context_menu(bpy.types.Menu):
    bl_label = "Timecycle Modifiers Specials"
    bl_idname = "SOLLUMZ_MT_timecycle_modifiers_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op = layout.operator(ytyp_ops.SOLLUMZ_OT_archetype_select_all_mlo_tcm.bl_idname, text="Select All")
        if (filter_opts := SOLLUMZ_UL_TIMECYCLE_MODIFIER_LIST.last_filter_options.get("timecycle_modifiers_tool_panel", None)):
            filter_opts.apply_to_operator(op)


class SOLLUMZ_PT_MLO_FLAGS_PANEL(MloChildTabPanel, MultiSelectUIFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_MLO_FLAGS_PANEL"
    bl_label = "MLO Flags"

    icon = "BOOKMARKS"

    bl_order = 4

    @classmethod
    def poll_tab(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.type == ArchetypeType.MLO

    def get_flags_active(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.mlo_flags

    def get_flags_selection(self, context):
        selected_ytyp = get_selected_ytyp(context)
        return selected_ytyp.archetypes.selection.mlo_flags
