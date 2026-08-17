import bpy
from bl_ui.space_statusbar import STATUSBAR_HT_header
from dataclasses import dataclass
from typing import Iterator, Optional

from .ydr.operators.materials import SOLLUMZ_OT_convert_active_material_to_selected, SOLLUMZ_OT_auto_convert_current_material
from .sollumz_preferences import get_addon_preferences, get_export_settings, get_import_settings, SollumzImportSettings, SollumzExportSettings
from .sollumz_operators import SOLLUMZ_OT_copy_location, SOLLUMZ_OT_copy_rotation, SOLLUMZ_OT_paste_location, SOLLUMZ_OT_paste_rotation
from .sollumz_properties import (
    SollumType,
    MaterialType,
    SOLLUMZ_UI_NAMES,
)
from .sollumz_helper import find_sollumz_parent
from .tools.blenderhelper import tag_redraw_all_areas
from .tabbed_panels import TabPanel
from .lods import (
    LODLevel,
    SOLLUMZ_OT_set_lod_level,
    SOLLUMZ_OT_hide_object,
    SOLLUMZ_OT_HIDE_COLLISIONS,
    SOLLUMZ_OT_HIDE_SHATTERMAPS,
    SOLLUMZ_OT_SHOW_COLLISIONS,
    SOLLUMZ_OT_SHOW_SHATTERMAPS
)
from .icons import icon_manager


def draw_list_with_add_remove(layout: bpy.types.UILayout, add_operator: str, remove_operator: str, *temp_list_args, **temp_list_kwargs):
    """Draw a UIList with an add and remove button on the right column. Returns the left column."""
    row = layout.row()
    list_col = row.column()
    list_col.template_list(*temp_list_args, **temp_list_kwargs)
    side_col = row.column()
    if add_operator or remove_operator:
        col = side_col.column(align=True)
        if add_operator:
            col.operator(add_operator, text="", icon="ADD")
        if remove_operator:
            col.operator(remove_operator, text="", icon="REMOVE")

    return list_col, side_col


class BasicListHelper:
    """Provides functionality for drawing simple lists where each item has a name and icon"""
    name_prop: str = "name"
    item_icon: str = "NONE"
    name_editable: bool = True

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        icon = self.get_item_icon(item)
        match icon:
            case str():
                icon_str, icon_value = icon, 0
            case int():
                icon_str, icon_value = "NONE", icon
            case _:
                raise ValueError(f"Invalid item icon. Only str or int supported, got '{icon}'")

        if self.name_editable:
            layout.prop(item, self.name_prop, text="", emboss=False, icon=icon_str, icon_value=icon_value)
        else:
            layout.label(text=getattr(item, self.name_prop), icon=icon_str, icon_value=icon_value)

    def get_item_icon(self, item) -> str | int:
        return self.item_icon


class FilterListHelper:
    order_by_name_key = "name"

    def filter_items(self, context, data, propname):
        helper = bpy.types.UI_UL_list
        items = getattr(data, propname)

        if self.use_filter_sort_alpha:
            ordered = helper.sort_items_by_name(items, self.order_by_name_key)
        else:
            ordered = []

        if self.use_filter_sort_reverse:
            ordered = list(reversed(ordered))

        # Filtered by self.filter_item
        filtered = [self.bitflag_filter_item] * len(items)

        for i, item in enumerate(items):
            if self.filter_item(item) and self._filter_item_name(item):
                continue

            filtered[i] &= ~self.bitflag_filter_item

        return filtered, ordered

    def _filter_item_name(self, item):
        try:
            name = getattr(item, self.order_by_name_key)
        except AttributeError:
            raise AttributeError(
                f"Invalid order_by_name_key for {self.__class__.__name__}! This should be the 'name' attribute for the list item.")

        return not self.filter_name or self.filter_name.lower() in name.lower()

    def filter_item(self, context):
        return True


class SollumzFileSettingsPanel:
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"

    operator_id = None

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator

        return operator.bl_idname in cls.operator_id

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        self.draw_settings(layout, self.get_settings(context))

    def get_settings(self, context: bpy.types.Context) -> bpy.types.ID:
        ...

    def draw_settings(self, layout: bpy.types.UILayout, settings: bpy.types.ID):
        ...


class SollumzImportSettingsPanel(SollumzFileSettingsPanel):
    operator_id = {"SOLLUMZ_OT_import_assets"}

    def get_settings(self, context: bpy.types.Context):
        return get_import_settings(context)

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        ...


class SollumzExportSettingsPanel(SollumzFileSettingsPanel):
    operator_id = {"SOLLUMZ_OT_export_assets"}

    def get_settings(self, context: bpy.types.Context):
        return get_export_settings(context)

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        ...


class SOLLUMZ_PT_import_textures(bpy.types.Panel, SollumzImportSettingsPanel):
    bl_label = "Textures"
    bl_order = 1

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        col = layout.column(align=True)
        col.prop(settings, "textures_mode", text="Mode")
        if settings.textures_mode == "CUSTOM_DIR":
            split = col.split(factor=0.4)
            split.column()
            split.column().prop(bpy.context.window_manager, "sz_ui_import_textures_extract_custom_directory_wrapper", text="")

    @classmethod
    def register(cls):
        def _get(self) -> str:
            return get_import_settings().textures_extract_custom_directory
        def _set(self, value: str):
            get_import_settings().textures_extract_custom_directory = value

        # Wrapper without subtype=DIR_PATH so it doesn't show the "open directory browser" button. Since we are
        # already in a file dialog, it reports an error saying it cannot open another one. Having this wrapper seems to
        # be the only way to hide that button.
        kw = SollumzImportSettings.__bases__[0].__annotations__["textures_extract_custom_directory"].keywords
        bpy.types.WindowManager.sz_ui_import_textures_extract_custom_directory_wrapper = bpy.props.StringProperty(
            name=kw["name"],
            description=kw["description"],
            get=_get, set=_set,
        )

    @classmethod
    def unregister(cls):
        del bpy.types.WindowManager.sz_ui_import_textures_extract_custom_directory_wrapper


class SOLLUMZ_PT_import_fragment(bpy.types.Panel, SollumzImportSettingsPanel):
    bl_label = "Fragment"
    bl_order = 2

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.prop(settings, "split_by_group")
        layout.prop(settings, "frag_import_vehicle_windows")


class SOLLUMZ_PT_import_ydd(bpy.types.Panel, SollumzImportSettingsPanel):
    bl_label = "Drawable Dictionary"
    bl_order = 3

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        col = layout.column(align=True)
        col.row(align=True).prop(settings, "dwd_import_external_skeleton", expand=True)

        if settings.dwd_import_external_skeleton == "SAVED":
            prefs = get_addon_preferences(bpy.context)
            if prefs.external_skeleton_paths:
                col.prop_search(
                    settings, "dwd_import_external_skeleton_saved_path",
                    prefs, "external_skeleton_paths",
                    text=" ", icon="ARMATURE_DATA",
                )
            else:
                split = col.split(factor=0.4)
                row = split.row()
                row = split.row()
                row.alert = True
                row.label(text="No external skeletons saved in preferences.", icon="ERROR")


class _SollumzImportYtypPanel(SollumzImportSettingsPanel):
    bl_label = "Archetype Definitions"

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.prop(settings, "ytyp_mlo_instance_entities")


class SOLLUMZ_PT_import_ytyp_generic(bpy.types.Panel, _SollumzImportYtypPanel):
    """Panel with YTYP import settings used in the 'Export RAGE Assets' button."""
    bl_order = 4


class SOLLUMZ_PT_import_ytyp_concrete(bpy.types.Panel, _SollumzImportYtypPanel):
    """Panel with YMAP import settings used in the 'Import YTYP' button.
    Same as the generic one but without the header.
    """
    operator_id = {"SOLLUMZ_OT_import_ytyp_io"}
    bl_options = {"HIDE_HEADER"}
    bl_order = 0

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.use_property_split = False
        super().draw_settings(layout, settings)

class _SollumzImportYmapPanel(SollumzImportSettingsPanel):
    bl_label = "Maps"

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.prop(settings, "ymap_instance_entities")


class SOLLUMZ_PT_import_ymap_generic(bpy.types.Panel, _SollumzImportYmapPanel):
    """Panel with YMAP import settings used in the 'Export RAGE Assets' button."""
    bl_order = 5


class SOLLUMZ_PT_import_ymap_concrete(bpy.types.Panel, _SollumzImportYmapPanel):
    """Panel with YMAP import settings used in the 'Import YMAP' button.
    Same as the generic one but without the header.
    """
    operator_id = {"SOLLUMZ_OT_import_ymap", "SOLLUMZ_OT_import_ymap_from_directory"}
    bl_options = {"HIDE_HEADER"}
    bl_order = 0

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.use_property_split = False
        super().draw_settings(layout, settings)


class SOLLUMZ_PT_export_include(bpy.types.Panel, SollumzExportSettingsPanel):
    bl_label = "Include"
    bl_order = 0

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        row = layout.row(heading="Limit To")
        row.prop(settings, "limit_to_selected", text="Selected Objects")


class SOLLUMZ_PT_export_drawable(bpy.types.Panel, SollumzExportSettingsPanel):
    bl_label = "Drawable"
    bl_order = 1

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        layout.prop(settings, "apply_transforms")
        layout.prop(settings, "mesh_domain", expand=True)


# Empty for now
# class SOLLUMZ_PT_export_fragment(bpy.types.Panel, SollumzExportSettingsPanel):
#     bl_label = "Fragment"
#     bl_order = 2
#
#     def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
#         pass


# Empty for now
# class SOLLUMZ_PT_export_collision(bpy.types.Panel, SollumzExportSettingsPanel):
#     bl_label = "Collisions"
#     bl_order = 3
#
#     def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
#         pass


class SOLLUMZ_PT_export_ydd(bpy.types.Panel, SollumzExportSettingsPanel):
    bl_label = "Drawable Dictionary"
    bl_order = 4

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        layout.prop(settings, "exclude_skeleton")


class _SollumzExportYtypPanel(SollumzExportSettingsPanel):
    bl_label = "Archetype Definitions"

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        layout.enabled = self.is_enabled(settings)
        layout.prop(settings, "export_ytyps_include", text="Include", expand=True)
        if settings.export_ytyps_include == "SELECTED":
            from .ytyp.ui.ytyp import SOLLUMZ_UL_YTYP_LIST

            layout.template_list(
                SOLLUMZ_UL_YTYP_LIST.bl_idname,
                "",
                bpy.context.scene, "ytyps",
                bpy.context.scene, "ytyp_index",
                rows=3
            )

        layout.separator()
        layout.prop(settings, "apply_transforms")

    def is_enabled(self, settings: SollumzExportSettings):
        return True


class SOLLUMZ_PT_export_ytyp_generic(bpy.types.Panel, _SollumzExportYtypPanel):
    """Panel with YTYP export settings used in the 'Export RAGE Assets' button."""
    bl_order = 6

    def draw_header(self, context):
        settings = self.get_settings(context)
        self.layout.prop(settings, "export_ytyps", text="")

    def is_enabled(self, settings: SollumzExportSettings):
        return settings.export_ytyps


class SOLLUMZ_PT_export_ytyp_concrete(bpy.types.Panel, _SollumzExportYtypPanel):
    """Panel with YTYP export settings used in the 'Export YTYP' button.
    Same as the generic one but without the header.
    """
    operator_id = {"SOLLUMZ_OT_export_ytyp_io"}
    bl_options = {"HIDE_HEADER"}
    bl_order = 0


class _SollumzExportYmapPanel(SollumzExportSettingsPanel):
    bl_label = "Maps"

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        layout.enabled = self.is_enabled(settings)
        layout.prop(settings, "export_ymaps_include", text="Include", expand=True)
        if settings.export_ymaps_include == "SELECTED":
            from .shared.multiselection import multiselect_ui_draw_list
            from .ymap_next.properties.map import get_maps
            from .ymap_next.ui.map import SOLLUMZ_UL_maps_group_list, SOLLUMZ_MT_maps_group_list_context_menu

            if maps := get_maps(bpy.context):
                multiselect_ui_draw_list(
                    layout,
                    maps.groups,
                    "",
                    "",
                    SOLLUMZ_UL_maps_group_list,
                    SOLLUMZ_MT_maps_group_list_context_menu,
                    "tool_panel",
                )


    def is_enabled(self, settings: SollumzExportSettings):
        return True


class SOLLUMZ_PT_export_ymap_generic(bpy.types.Panel, _SollumzExportYmapPanel):
    """Panel with YMAP export settings used in the 'Export RAGE Assets' button."""
    bl_order = 7

    def draw_header(self, context):
        settings = self.get_settings(context)
        self.layout.prop(settings, "export_ymaps", text="")

    def is_enabled(self, settings: SollumzExportSettings):
        return settings.export_ymaps


class SOLLUMZ_PT_export_ymap_concrete(bpy.types.Panel, _SollumzExportYmapPanel):
    """Panel with YMAP export settings used in the 'Export YMAP' button.
    Same as the generic one but without the header.
    """
    operator_id = {"SOLLUMZ_OT_export_ymap"}
    bl_options = {"HIDE_HEADER"}
    bl_order = 0


class _SollumzExportYtdPanel(SollumzExportSettingsPanel):
    bl_label = "Texture Dictionaries"

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        layout.enabled = self.is_enabled(settings)
        layout.prop(settings, "export_ytds_include", text="Include", expand=True)
        if settings.export_ytds_include == "SELECTED":
            from .shared.multiselection import multiselect_ui_draw_list
            from .ytd.ui import SOLLUMZ_UL_txd_list, SOLLUMZ_MT_txd_list_context_menu

            multiselect_ui_draw_list(
                layout,
                bpy.context.scene.sz_txds.texture_dictionaries,
                "",
                "",
                SOLLUMZ_UL_txd_list,
                SOLLUMZ_MT_txd_list_context_menu,
                "tool_panel",
            )

    def is_enabled(self, settings: SollumzExportSettings):
        return True


class SOLLUMZ_PT_export_ytd_generic(bpy.types.Panel, _SollumzExportYtdPanel):
    """Panel with YTD export settings used in the 'Export RAGE Assets' button."""
    bl_order = 8

    def draw_header(self, context):
        settings = self.get_settings(context)
        self.layout.prop(settings, "export_ytds", text="")

    def is_enabled(self, settings: SollumzExportSettings):
        return settings.export_ytds


class SOLLUMZ_PT_export_ytd_concrete(bpy.types.Panel, _SollumzExportYtdPanel):
    """Panel with YTD export settings used in the 'Export YTD' button.
    Same as the generic one but without the header.
    """
    operator_id = {"SOLLUMZ_OT_export_ytd"}
    bl_options = {"HIDE_HEADER"}
    bl_order = 0


class SOLLUMZ_PT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "General"
    bl_idname = "SOLLUMZ_PT_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 0

    def draw_header(self, context):
        self.layout.label(text="", icon="MODIFIER_DATA")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("sollumz.import_assets", icon="IMPORT")
        op = row.operator("sollumz.export_assets", icon="EXPORT")
        if context.scene.sollumz_export_path != "":
            op.directory = context.scene.sollumz_export_path
            op.direct_export = True


class GeneralToolChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_TOOL_PANEL.bl_category


class SOLLUMZ_PT_VIEW_PANEL(GeneralToolChildPanel, bpy.types.Panel):
    bl_label = "View"
    bl_idname = "SOLLUMZ_PT_VIEW_PANEL"
    bl_options = set()
    bl_order = 0

    def draw_header(self, context):
        self.layout.label(text="", icon="RESTRICT_VIEW_OFF")

    def draw(self, context):
        layout = self.layout

        grid = layout.grid_flow(align=True, row_major=True)
        grid.scale_x = 0.7
        if context.scene.sollumz_show_collisions:
            grid.operator(SOLLUMZ_OT_HIDE_COLLISIONS.bl_idname)
        else:
            grid.operator(SOLLUMZ_OT_SHOW_COLLISIONS.bl_idname)

        if context.scene.sollumz_show_shattermaps:
            grid.operator(SOLLUMZ_OT_HIDE_SHATTERMAPS.bl_idname)
        else:
            grid.operator(SOLLUMZ_OT_SHOW_SHATTERMAPS.bl_idname)

        layout.separator()

        layout.label(text="Level of Detail")

        active_obj = context.view_layer.objects.active
        active_lod_level = self._get_object_active_lod_level(active_obj)

        grid = layout.grid_flow(align=True, row_major=True)
        grid.enabled = active_obj is not None and context.view_layer.objects.active.mode == "OBJECT"
        grid.scale_x = 0.7
        for lod_level in LODLevel:
            grid.operator(
                SOLLUMZ_OT_set_lod_level.bl_idname,
                text=SOLLUMZ_UI_NAMES[lod_level],
                depress=active_lod_level == lod_level
            ).lod_level = lod_level
        grid.operator(SOLLUMZ_OT_hide_object.bl_idname, depress=active_lod_level == "hidden")

    def _get_object_active_lod_level(self, obj: Optional[bpy.types.Object]) -> Optional[str]:
        if obj is None:
            return None

        parent_obj = find_sollumz_parent(obj)
        if parent_obj is None:
            return None

        active_lod_level = None
        if parent_obj.hide_get():
            active_lod_level = "hidden"
        else:
            for child in parent_obj.children_recursive:
                if child.type == "MESH" and child.sollum_type == SollumType.DRAWABLE_MODEL:
                    # Simply use the LOD level of the first model we find. Might not be accurate if the user
                    # manually changes LODs of the models separately instead of using the buttons in the tools
                    # panel, but in general this should be enough.
                    active_lod_level = child.sz_lods.active_lod_level
                    break

        return active_lod_level


class SOLLUMZ_PT_OBJ_YMAP_LOCATION(GeneralToolChildPanel, bpy.types.Panel):
    bl_label = "Object Location & Rotation Tools"
    bl_idname = "SOLLUMZ_PT_OBJ_YMAP_LOCATION"
    bl_order = 3

    def draw_header(self, context):
        self.layout.label(text="", icon="OBJECT_ORIGIN")

    def draw(self, context):
        layout = self.layout
        selected_objects = bpy.context.selected_objects

        if not selected_objects:
            layout.label(text="No objects selected")
            return

        for obj in selected_objects:
            loc = obj.location
            rot = obj.matrix_world.to_quaternion()

            box = layout.box()
            row = box.row(align=True)
            row.prop(obj, "name", text="", emboss=False)

            row.operator(SOLLUMZ_OT_copy_location.bl_idname, text="", icon='COPYDOWN') \
               .location = "{:.6f}, {:.6f}, {:.6f}".format(loc[0], loc[1], loc[2])

            row.operator(SOLLUMZ_OT_copy_rotation.bl_idname, text="", icon='COPYDOWN') \
               .rotation = "{:.6f}, {:.6f}, {:.6f}, {:.6f}".format(rot.x, rot.y, rot.z, rot.w)

            row.operator(SOLLUMZ_OT_paste_location.bl_idname, text="", icon='PASTEDOWN')

            row.operator(SOLLUMZ_OT_paste_rotation.bl_idname, text="", icon='PASTEDOWN')


class SOLLUMZ_PT_VERTEX_TOOL_PANEL(GeneralToolChildPanel, bpy.types.Panel):
    bl_label = "Vertex Painter"
    bl_idname = "SOLLUMZ_PT_VERTEX_TOOL_PANEL"
    bl_order = 1

    def draw_header(self, context):
        self.layout.label(text="", icon="BRUSH_DATA")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(context.scene, "vert_paint_color1", text="")
        row.operator(
            "sollumz.paint_vertices").color = context.scene.vert_paint_color1

        row2 = layout.row()
        row2.prop(context.scene, "vert_paint_color2", text="")
        row2.operator(
            "sollumz.paint_vertices").color = context.scene.vert_paint_color2

        row3 = layout.row()
        row3.prop(context.scene, "vert_paint_color3", text="")
        row3.operator(
            "sollumz.paint_vertices").color = context.scene.vert_paint_color3

        preferences = get_addon_preferences(bpy.context)
        extra = preferences.extra_color_swatches
        if extra:
            row4 = layout.row()
            row4.prop(context.scene, "vert_paint_color4", text="")
            row4.operator(
                "sollumz.paint_vertices").color = context.scene.vert_paint_color4

            row5 = layout.row()
            row5.prop(context.scene, "vert_paint_color5", text="")
            row5.operator(
                "sollumz.paint_vertices").color = context.scene.vert_paint_color5

            row6 = layout.row()
            row6.prop(context.scene, "vert_paint_color6", text="")
            row6.operator(
                "sollumz.paint_vertices").color = context.scene.vert_paint_color6


class SOLLUMZ_PT_SET_SOLLUM_TYPE_PANEL(GeneralToolChildPanel, bpy.types.Panel):
    bl_label = "Set Sollum Type"
    bl_idname = "SOLLUMZ_PT_SET_SOLLUM_TYPE_PANEL"
    bl_order = 2

    def draw_header(self, context):
        self.layout.label(text="", icon="MESH_MONKEY")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("sollumz.setsollumtype")
        row.prop(context.scene, "all_sollum_type", text="")


class SOLLUMZ_PT_EXPORT_PATH_PANEL(GeneralToolChildPanel, bpy.types.Panel):
    bl_label = "Export Path"
    bl_idname = "SOLLUMZ_PT_EXPORT_PATH_PANEL"
    bl_order = 4

    def draw_header(self, context):
        self.layout.label(text="", icon="FILEBROWSER")

    def draw(self, context):
        self.layout.prop(context.scene, "sollumz_export_path", text="")


class SOLLUMZ_PT_OBJECT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        icon_manager.icon_label("sollumz_icon", self)

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        obj = context.active_object
        row = layout.row()
        row.prop(obj, "sollum_type")

        if not obj or obj.sollum_type == SollumType.NONE:
            layout.label(
                text="No sollumz objects in scene selected.", icon="ERROR")


class SOLLUMZ_PT_ENTITY_PANEL(bpy.types.Panel):
    bl_label = "Entity Definition"
    bl_idname = "SOLLUMZ_PT_ENTITY_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 1

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj is not None and aobj.sollum_type == SollumType.DRAWABLE

    def draw(self, context):
        layout = self.layout
        grid = layout.grid_flow(columns=2, even_columns=True, even_rows=True)
        grid.use_property_split = True
        aobj = context.active_object
        grid.prop(aobj.entity_properties, "flags")
        grid.prop(aobj.entity_properties, "guid")
        grid.prop(aobj.entity_properties, "parent_index")
        grid.prop(aobj.entity_properties, "lod_dist")
        grid.prop(aobj.entity_properties, "child_lod_dist")
        grid.prop(aobj.entity_properties, "num_children")
        grid.prop(aobj.entity_properties, "ambient_occlusion_multiplier")
        grid.prop(aobj.entity_properties, "artificial_ambient_occlusion")
        grid.prop(aobj.entity_properties, "tint_value")
        grid.prop(aobj.entity_properties, "lod_level")
        grid.prop(aobj.entity_properties, "priority_level")


class SOLLUMZ_PT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAT_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "material"
    bl_options = {"DEFAULT_CLOSED"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object

        return obj is not None and obj.active_material is not None

    def draw_header(self, context):
        icon_manager.icon_label("sollumz_icon", self)

    def draw_header_preset(self, context):
        from .ydr.gta5.presets.shader import SHADER_PRESET_CATEGORY, SOLLUMZ_PT_shader_presets
        from .ybn.gta5.presets.collision_material import COLLISION_MATERIAL_PRESET_CATEGORY, SOLLUMZ_PT_collision_material_presets
        if SHADER_PRESET_CATEGORY.poll(context)[0]:
            SOLLUMZ_PT_shader_presets.draw_panel_header(self.layout)
        elif COLLISION_MATERIAL_PRESET_CATEGORY.poll(context)[0]:
            SOLLUMZ_PT_collision_material_presets.draw_panel_header(self.layout)

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        mat = aobj.active_material

        if not mat or mat.sollum_type == MaterialType.NONE:
            layout.label(text="Material is not a Sollumz material.", icon="ERROR")

            box = layout.box()

            from .ydr.ui import SOLLUMZ_UL_SHADER_MATERIALS_LIST

            wm = context.window_manager

            box.template_list(
                SOLLUMZ_UL_SHADER_MATERIALS_LIST.bl_idname, "",
                wm, "sz_shader_materials", wm, "sz_shader_material_index",
            )

            row = box.row()
            row.operator(SOLLUMZ_OT_convert_active_material_to_selected.bl_idname,
                         text="Convert to Selected", icon="FILE_REFRESH")
            row.operator(SOLLUMZ_OT_auto_convert_current_material.bl_idname, text="Auto Convert", icon="FILE_REFRESH")

            return


class FlagsPanel:
    bl_label = "Flags"
    bl_options = {"DEFAULT_CLOSED"}

    def get_flags(self, context):
        raise NotImplementedError(
            f"Failed to display flags. '{self.__class__.__name__}.get_flags()' method not defined.")

    def draw(self, context):
        data_block = self.get_flags(context)
        self.layout.prop(data_block, "total")
        self.layout.separator()
        grid = self.layout.grid_flow(columns=2)
        for index, prop_name in enumerate(data_block.get_flag_names()):
            if index > data_block.size - 1:
                break
            grid.prop(data_block, prop_name)


class TimeFlagsPanel(FlagsPanel):
    bl_label = "Time Flags"
    select_operator = None
    clear_operator = None

    def draw(self, context):
        super().draw(context)
        if self.select_operator is None or self.clear_operator is None:
            raise NotImplementedError(
                f"'select_operator' and 'clear_operator' bl_idnames must be defined for {self.__class__.__name__}!")
        flags = self.get_flags(context)
        row = self.layout.row()
        row.operator(self.select_operator)
        row.prop(flags, "time_flags_start", text="from")
        row.prop(flags, "time_flags_end", text="to")
        row = self.layout.row()
        row.operator(self.clear_operator)


class NoVisibilityToggle:
    """Mixin for panels that get no show/hide toggle and are not listed in Preferences > UI > Panels."""
    sz_panel_no_visibility_toggle = True


def space_type_ui_name(space_type: str) -> str:
    item = bpy.types.Space.bl_rna.properties["type"].enum_items.get(space_type)
    return item.name if item is not None else space_type


def context_mode_ui_name(context_mode: str) -> str:
    item = bpy.types.Context.bl_rna.properties["mode"].enum_items.get(context_mode)
    return item.name if item is not None else context_mode


class PanelVisibility:
    """Show/hide state of the UI panels."""

    @dataclass(frozen=True, slots=True)
    class Node:
        panel: type
        idname: str
        label: str
        children: tuple["Node", ...]

    @dataclass(frozen=True, slots=True)
    class Group:
        space_type: str
        region_type: str
        category: str
        roots: tuple["Node", ...]

        @property
        def label(self) -> str:
            category = self.category
            if category and category.islower():
                # bl_context identifiers like "object" or "material"
                category = category.replace("_", " ").title()
            space_name = space_type_ui_name(self.space_type)
            return f"{space_name} › {category}" if category else space_name

    def __init__(self):
        self._tree: tuple[PanelVisibility.Group, ...] = ()
        self._original_polls: dict[type, object | None] = {}
        self._hidden_ids: set[str] = set()

    def is_hidden(self, panel_id: str) -> bool:
        return panel_id in self._hidden_ids

    @property
    def has_hidden(self) -> bool:
        return bool(self._hidden_ids)

    def sync(self, hidden_panels):
        """Sync the runtime state with the `hidden_panels` preferences collection."""
        self._hidden_ids.clear()
        self._hidden_ids.update(entry.name for entry in hidden_panels)

    def set_hidden(self, context, panel_id: str, hidden: bool):
        prefs = get_addon_preferences(context)
        prefs.set_panel_hidden(panel_id, hidden)
        self.sync(prefs.hidden_panels)

    def show_all(self, context):
        prefs = get_addon_preferences(context)
        prefs.clear_hidden_panels()
        self.sync(prefs.hidden_panels)

    def hook_panels(self, classes):
        """Build the panels tree from `classes` and replace the `poll` of each panel in it with one
        that also checks whether the user hid the panel before delegating to the original function.
        """
        self._tree = self._build_panel_tree(classes)
        for node in self._iter_nodes():
            cls = node.panel
            if cls in self._original_polls:
                continue  # already wrapped, don't stack wrappers

            assert not getattr(cls, "is_registered", False), (
                f"Panel '{node.idname}' is already registered. Its poll must be replaced before "
                f"registration, Blender only calls poll on classes that defined it at registration time."
            )

            original_bound_poll = getattr(cls, "poll", None)  # resolved through the MRO, bound to cls
            self._original_polls[cls] = cls.__dict__.get("poll")  # exact descriptor, to restore later
            cls.poll = classmethod(self._make_poll(node.idname, original_bound_poll))

    def _make_poll(self, panel_id: str, original_poll):
        def poll(cls, context):
            if self.is_hidden(panel_id):
                return False
            return original_poll(context) if original_poll is not None else True
        return poll

    def unhook_panels(self):
        """Restore the original `poll` of every panel hooked by `hook_panels` and drop the tree."""
        for cls, original_poll in self._original_polls.items():
            if original_poll is not None:
                cls.poll = original_poll
            elif "poll" in cls.__dict__:
                del cls.poll  # the panel had no own poll, remove ours to fall back to any inherited one
        self._original_polls.clear()
        self._tree = ()

    def draw_prefs_section(self, layout: bpy.types.UILayout):
        """Draw the panels tree with a show/hide toggle on each panel."""
        row = layout.row()
        row.label(text="Panels")
        subrow = row.row()
        subrow.alignment = "RIGHT"
        subrow.operator(SOLLUMZ_OT_prefs_show_all_panels.bl_idname, text="   Show All   ", icon="HIDE_OFF")

        box = layout.box()
        for group in self._tree:
            if bpy.app.version >= (4, 1, 0):
                group_idname = f"sollumz_prefs_ui_panels_group_{group.space_type}_{group.region_type}_{group.category}"
                group_header, group_body = box.panel(group_idname, default_closed=True)
            else:
                group_header, group_body = box, box
            group_header.label(text=group.label)
            if group_body:
                for root in group.roots:
                    self._draw_node(group_body, root, indent=1, parent_hidden=False)

    def _draw_node(self, layout: bpy.types.UILayout, node: Node, indent: int, parent_hidden: bool):
        row = layout.row(align=True)
        row.alignment = "LEFT"
        row.active = not parent_hidden
        for _ in range(indent):
            row.label(text="", icon="BLANK1")

        hidden = self.is_hidden(node.idname)
        row.operator(
            SOLLUMZ_OT_prefs_toggle_panel_visibility.bl_idname,
            text=node.label,
            icon="CHECKBOX_DEHLT" if hidden else "CHECKBOX_HLT",
            emboss=False,
        ).panel_id = node.idname

        for child in node.children:
            self._draw_node(layout, child, indent + 1, parent_hidden or hidden)

    @staticmethod
    def _panel_idname(panel: type) -> str:
        return getattr(panel, "bl_idname", None) or panel.__name__

    @staticmethod
    def _is_visibility_toggleable(panel: type) -> bool:
        """Whether the user can show/hide this panel."""
        if getattr(panel, "sz_panel_no_visibility_toggle", False):
            return False

        if getattr(panel, "bl_space_type", None) == "FILE_BROWSER":
            # The import/export settings panels
            return False

        if getattr(panel, "bl_region_type", None) == "HEADER":
            # Popover panels (e.g. preset panels), opened from a button drawn by other UI, not
            # persistent panels the user would toggle here
            return False

        if issubclass(panel, TabPanel):
            # Tab panels are always part of other parent panel
            return False

        return True

    def _build_panel_tree(self, classes) -> tuple[Group, ...]:
        """Build the tree of panels found in `classes`. Panels whose visibility is not
        user-controlled are removed along with their whole subtree. Groups come out in
        display order, sorted by display label.
        """
        panels = [cls for cls in classes if issubclass(cls, bpy.types.Panel)]
        by_idname = {self._panel_idname(cls): cls for cls in panels}

        children_by_parent: dict[str, list[type]] = {}
        root_panels = []
        for cls in panels:
            parent_idname = getattr(cls, "bl_parent_id", None)
            if parent_idname in by_idname:
                children_by_parent.setdefault(parent_idname, []).append(cls)
            else:
                # either a root panel or a child of a panel not defined by us
                root_panels.append(cls)

        def _build_node(cls) -> PanelVisibility.Node | None:
            if not self._is_visibility_toggleable(cls):
                return None  # remove the whole subtree

            idname = self._panel_idname(cls)
            children = tuple(
                node
                for child in children_by_parent.get(idname, ())
                if (node := _build_node(child)) is not None
            )
            label = getattr(cls, "bl_label", None) or idname
            return PanelVisibility.Node(cls, idname, label, children)

        groups = {}
        for cls in root_panels:
            node = _build_node(cls)
            if node is None:
                continue

            parent_idname = getattr(cls, "bl_parent_id", None)
            group_cls = (bpy.types.Panel.bl_rna_get_subclass_py(parent_idname) if parent_idname else None) or cls
            space_type = getattr(group_cls, "bl_space_type", "") or ""
            region_type = getattr(group_cls, "bl_region_type", "") or ""
            category = getattr(group_cls, "bl_category", None) or getattr(group_cls, "bl_context", None) or ""
            groups.setdefault((space_type, region_type, category), []).append(node)

        return tuple(sorted(
            (
                PanelVisibility.Group(space_type, region_type, category, tuple(nodes))
                for (space_type, region_type, category), nodes in groups.items()
            ),
            key=lambda group: group.label.casefold(),
        ))

    def _iter_nodes(self) -> Iterator[Node]:
        """Flat iteration over every node in the tree."""
        def _flatten(nodes):
            for node in nodes:
                yield node
                yield from _flatten(node.children)

        for group in self._tree:
            yield from _flatten(group.roots)


_panel_visibility = PanelVisibility()


def panel_visibility() -> PanelVisibility:
    return _panel_visibility


class SOLLUMZ_OT_prefs_toggle_panel_visibility(bpy.types.Operator):
    """Show or hide this panel"""
    bl_idname = "sollumz.prefs_toggle_panel_visibility"
    bl_label = "Toggle Panel Visibility"
    bl_options = {"INTERNAL"}

    panel_id: bpy.props.StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        panels = panel_visibility()
        panels.set_hidden(context, self.panel_id, not panels.is_hidden(self.panel_id))
        tag_redraw_all_areas(context)
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_show_all_panels(bpy.types.Operator):
    """Show all panels hidden in the panel list"""
    bl_idname = "sollumz.prefs_show_all_panels"
    bl_label = "Show All"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        return panel_visibility().has_hidden

    def execute(self, context):
        panel_visibility().show_all(context)
        tag_redraw_all_areas(context)
        return {"FINISHED"}


def statusbar_draw_sollumz_version(header, context):
    from .meta import sollumz_version
    layout = header.layout.row(align=True)
    layout.label(text=sollumz_version(), icon_value=icon_manager.get_icon("sollumz_icon"))


def statusbar_register_draw():
    STATUSBAR_HT_header.append(statusbar_draw_sollumz_version)


def statusbar_unregister_draw():
    STATUSBAR_HT_header.remove(statusbar_draw_sollumz_version)


def register():
    statusbar_unregister_draw()
    if get_addon_preferences().show_version_in_statusbar:
        statusbar_register_draw()


def unregister():
    statusbar_unregister_draw()


def pre_register_classes(classes):
    panel_visibility().hook_panels(classes)


def post_unregister_classes():
    panel_visibility().unhook_panels()
