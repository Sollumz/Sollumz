import bpy
from ...sollumz_ui import BasicListHelper, SollumzFileSettingsPanel, draw_list_with_add_remove
from ...sollumz_properties import ArchetypeType
from ...sollumz_preferences import (
    get_import_settings,
    get_export_settings,
    SollumzImportSettings,
    SollumzExportSettings
)
from ..utils import (
    get_selected_ytyp,
    get_selected_archetype
)
from ...shared.multiselection import (
    MultiSelectUIListMixin
)
from ..operators import ytyp as ytyp_ops


class SOLLUMZ_UL_YTYP_LIST(BasicListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_YTYP_LIST"
    item_icon = "PRESET"


class SOLLUMZ_PT_YTYP_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Archetype Definition"
    bl_idname = "SOLLUMZ_PT_YTYP_TOOL_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"

    bl_order = 6

    def draw_header(self, context):
        self.layout.label(text="", icon="OBJECT_DATA")

    def draw(self, context):
        ...


class YtypToolChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_YTYP_TOOL_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_YTYP_TOOL_PANEL.bl_category


class SOLLUMZ_PT_YTYP_LIST_PANEL(YtypToolChildPanel, bpy.types.Panel):
    bl_label = "YTYPS"
    bl_idname = "SOLLUMZ_PT_YTYP_LIST_PANEL"
    bl_order = 0

    def draw(self, context):
        list_col, _ = draw_list_with_add_remove(self.layout, "sollumz.createytyp", "sollumz.deleteytyp",
                                                SOLLUMZ_UL_YTYP_LIST.bl_idname, "", context.scene, "ytyps", context.scene, "ytyp_index", rows=3)
        row = list_col.row()
        row.operator("sollumz.importytyp", icon="IMPORT")
        row.operator("sollumz.exportytyp", icon="EXPORT")


class SOLLUMZ_PT_import_ytyp(bpy.types.Panel, SollumzFileSettingsPanel):
    bl_options = {"HIDE_HEADER"}
    operator_id = "SOLLUMZ_OT_importytyp"

    def get_settings(self, context: bpy.types.Context) -> SollumzImportSettings:
        return get_import_settings(context)

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.use_property_split = False
        layout.prop(settings, "ytyp_mlo_instance_entities")


class SOLLUMZ_PT_export_ytyp(bpy.types.Panel, SollumzFileSettingsPanel):
    bl_options = {"HIDE_HEADER"}
    operator_id = "SOLLUMZ_OT_exportytyp"

    def get_settings(self, context: bpy.types.Context) -> SollumzExportSettings:
        return get_export_settings(context)

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        layout.use_property_split = False
        layout.prop(settings, "apply_transforms")


class SOLLUMZ_UL_ARCHETYPE_LIST(MultiSelectUIListMixin, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ARCHETYPE_LIST"
    multiselect_collection_name = "archetypes"
    multiselect_operator = ytyp_ops.SOLLUMZ_OT_ytyp_select_archetype.bl_idname

    def get_item_icon(self, item) -> str:
        icon = "SEQ_STRIP_META"
        if item.type == ArchetypeType.MLO:
            icon = "HOME"
        elif item.type == ArchetypeType.TIME:
            icon = "TIME"
        return icon


class SOLLUMZ_PT_ARCHETYPE_LIST_PANEL(YtypToolChildPanel, bpy.types.Panel):
    bl_label = "Archetypes"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_LIST_PANEL"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return get_selected_ytyp(context) is not None

    def draw(self, context):
        selected_ytyp = get_selected_ytyp(context)

        list_col, side_col = draw_list_with_add_remove(
            self.layout,
            "sollumz.createarchetype", "sollumz.deletearchetype",
            SOLLUMZ_UL_ARCHETYPE_LIST.bl_idname, "",
            selected_ytyp, selected_ytyp.archetypes._collection_propname,
            selected_ytyp, selected_ytyp.archetypes._active_index_propname,#"active_index_with_update_callback_for_ui",
            rows=3
        )

        side_col.separator()
        side_col.menu(SOLLUMZ_MT_archetype_context_menu.bl_idname, icon="DOWNARROW_HLT", text="")

        row = list_col.row()
        row.operator("sollumz.createarchetypefromselected",
                     icon="FILE_REFRESH")
        row.prop(context.scene, "create_archetype_type", text="")


class SOLLUMZ_MT_archetype_context_menu(bpy.types.Menu):
    bl_label = "Archetypes Specials"
    bl_idname = "SOLLUMZ_MT_archetype_context_menu"

    def draw(self, _context):
        layout = self.layout
        layout.operator(ytyp_ops.SOLLUMZ_OT_ytyp_select_all_archetypes.bl_idname, text="Select All")


class SOLLUMZ_PT_YTYP_TOOLS_PANEL(bpy.types.Panel):
    bl_label = "Tools"
    bl_idname = "SOLLUMZ_PT_YTYP_TOOLS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_LIST_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_ARCHETYPE_LIST_PANEL.bl_category

    @classmethod
    def poll(cls, context):
        selected_ytyp = get_selected_ytyp(context)
        return selected_ytyp is not None and selected_ytyp.archetypes

    def draw_header(self, context):
        self.layout.label(text="", icon="TOOL_SETTINGS")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        selected_ytyp = get_selected_ytyp(context)
        row = layout.row()
        row.prop(selected_ytyp, "all_flags")
        row.operator("sollumz.setflagsallarchs")

        selected_archetype = get_selected_archetype(context)

        if not selected_archetype:
            return

        layout.separator()

        row = layout.row()
        row.prop(selected_archetype, "all_entity_lod_dist")
        row.operator("sollumz.setentityloddistallarchs")
