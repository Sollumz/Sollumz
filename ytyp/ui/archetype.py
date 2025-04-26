import bpy
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ...sollumz_properties import AssetType, ArchetypeType
from ..utils import get_selected_archetype, get_selected_ytyp
from .ytyp import YtypToolChildPanel
from ...shared.multiselection import (
    MultiSelectUIFlagsPanel,
    MultiSelectUITimeFlagsPanel,
)


class SOLLUMZ_PT_ARCHETYPE_TABS_PANEL(YtypToolChildPanel, TabbedPanelHelper, bpy.types.Panel):
    bl_label = "Archetype"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_TABS_PANEL"
    bl_options = {"HIDE_HEADER"}

    default_tab = "SOLLUMZ_PT_ARCHETYPE_PANEL"

    bl_order = 2

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def draw_before(self, context: bpy.types.Context):
        self.layout.separator()


class ArchetypeChildTabPanel(TabPanel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL.bl_category

    parent_tab_panel = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL


class ArchetypeChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL.bl_category


class SOLLUMZ_PT_ARCHETYPE_PANEL(ArchetypeChildTabPanel, bpy.types.Panel):
    bl_label = "Archetype"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_PANEL"

    icon = "SEQ_STRIP_META"

    bl_order = 0

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        ytyp = get_selected_ytyp(context)
        selection = ytyp.archetypes.selection
        active = ytyp.archetypes.active_item
        layout.prop(selection.owner, selection.propnames.type)
        layout.prop(selection.owner, selection.propnames.name)
        layout.prop(selection.owner, selection.propnames.special_attribute)

        if active.asset_type != AssetType.ASSETLESS:
            layout.prop(selection.owner, selection.propnames.texture_dictionary)
            layout.prop(selection.owner, selection.propnames.clip_dictionary)
            layout.prop(selection.owner, selection.propnames.drawable_dictionary)
            layout.prop(selection.owner, selection.propnames.physics_dictionary)
            layout.prop(selection.owner, selection.propnames.hd_texture_dist)
            layout.prop(selection.owner, selection.propnames.lod_dist)

        layout.prop(selection.owner, selection.propnames.asset_type)
        layout.prop(selection.owner, selection.propnames.asset_name)

        row = layout.row()
        row.enabled = not ytyp.archetypes.has_multiple_selection
        row.prop(active, "asset", text="Linked Object")


class SOLLUMZ_PT_ARCHETYPE_FLAGS_PANEL(ArchetypeChildTabPanel, MultiSelectUIFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_FLAGS_PANEL"
    icon = "BOOKMARKS"

    bl_order = 2

    def get_flags_active(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.flags

    def get_flags_selection(self, context):
        selected_ytyp = get_selected_ytyp(context)
        return selected_ytyp.archetypes.selection.flags


class SOLLUMZ_PT_TIME_FlAGS_PANEL(ArchetypeChildPanel, MultiSelectUITimeFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_TIME_FLAGS_PANEL"
    bl_label = "Time Flags"
    select_operator = "sollumz.ytyp_time_flags_select_range"
    clear_operator = "sollumz.ytyp_time_flags_clear"

    bl_order = 3

    @classmethod
    def poll(cls, context):
        archetype = get_selected_archetype(context)
        return archetype and archetype.type == ArchetypeType.TIME

    def draw_header(self, context):
        self.layout.label(text="", icon="TIME")

    def get_flags_active(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.time_flags

    def get_flags_selection(self, context):
        selected_ytyp = get_selected_ytyp(context)
        return selected_ytyp.archetypes.selection.time_flags
