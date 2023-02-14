import bpy
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ...sollumz_ui import FlagsPanel, TimeFlagsPanel
from ...sollumz_properties import AssetType, ArchetypeType
from ..utils import get_selected_archetype, get_selected_ytyp
from .ytyp import SOLLUMZ_PT_YTYP_TOOL_PANEL


class SOLLUMZ_PT_ARCHETYPE_TABS_PANEL(TabbedPanelHelper, bpy.types.Panel):
    bl_label = "Archetype"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_TABS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_YTYP_TOOL_PANEL.bl_idname

    default_tab = "SOLLUMZ_PT_ARCHETYPE_PANEL"

    bl_order = 2

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def draw_before(self, context: bpy.types.Context):
        self.layout.separator()


class SOLLUMZ_PT_ARCHETYPE_PANEL(TabPanel, bpy.types.Panel):
    bl_label = "Archetype"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL
    icon = "SEQ_STRIP_META"

    bl_order = 0

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        selected_archetype = get_selected_archetype(context)
        layout.prop(selected_archetype, "type")
        layout.prop(selected_archetype, "name")
        layout.prop(selected_archetype, "special_attribute")

        if selected_archetype.asset_type != AssetType.ASSETLESS:
            layout.prop(selected_archetype, "texture_dictionary")
            layout.prop(selected_archetype, "clip_dictionary")
            layout.prop(selected_archetype, "drawable_dictionary")
            layout.prop(selected_archetype, "physics_dictionary")
            layout.prop(selected_archetype, "hd_texture_dist")
            layout.prop(selected_archetype, "lod_dist")

        layout.prop(selected_archetype, "asset_type")
        layout.prop(selected_archetype, "asset_name")
        layout.prop(selected_archetype, "asset", text="Linked Object")


class SOLLUMZ_PT_ARCHETYPE_FLAGS_PANEL(TabPanel, FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_FLAGS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL.bl_idname

    parent_tab_panel = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL
    icon = "BOOKMARKS"

    bl_order = 2

    def get_flags(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.flags


class SOLLUMZ_PT_TIME_FlAGS_PANEL(TimeFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_TIME_FLAGS_PANEL"
    bl_label = "Time Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL.bl_idname
    select_operator = "sollumz.ytyp_time_flags_select_range"
    clear_operator = "sollumz.ytyp_time_flags_clear"

    bl_order = 3

    @classmethod
    def poll(cls, context):
        archetype = get_selected_archetype(context)
        return archetype and archetype.type == ArchetypeType.TIME

    def draw_header(self, context):
        self.layout.label(text="", icon="TIME")

    def get_flags(self, context):
        return get_selected_archetype(context).time_flags
