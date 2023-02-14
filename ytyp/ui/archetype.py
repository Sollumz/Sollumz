import bpy
from ...sollumz_ui import FlagsPanel, TimeFlagsPanel
from ...sollumz_properties import AssetType, ArchetypeType
from ..utils import get_selected_archetype
from .ytyp import SOLLUMZ_PT_YTYP_PANEL


class SOLLUMZ_PT_ARCHETYPE_PANEL(bpy.types.Panel):
    bl_label = "Archetype"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_YTYP_PANEL.bl_idname

    bl_order = 0

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

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


class SOLLUMZ_PT_ARCHETYPE_FLAGS_PANEL(FlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_FLAGS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname

    bl_order = 1

    def get_flags(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.flags


class SOLLUMZ_PT_YTYP_TIME_FLAGS_PANEL(TimeFlagsPanel, bpy.types.Panel):
    bl_idname = "SOLLUMZ_PT_YTYP_TIME_FLAGS_PANEL"
    bl_label = "Time Flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_PANEL.bl_idname
    select_operator = "sollumz.ytyp_time_flags_select_range"
    clear_operator = "sollumz.ytyp_time_flags_clear"

    bl_order = 2

    @classmethod
    def poll(cls, context):
        archetype = get_selected_archetype(context)
        return archetype and archetype.type == ArchetypeType.TIME

    def get_flags(self, context):
        return get_selected_archetype(context).time_flags
