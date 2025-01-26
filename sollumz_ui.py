import bpy
from typing import Optional
from .sollumz_preferences import get_addon_preferences, get_export_settings, get_import_settings, SollumzImportSettings, SollumzExportSettings
from .sollumz_operators import SOLLUMZ_OT_copy_location, SOLLUMZ_OT_copy_rotation, SOLLUMZ_OT_paste_location, SOLLUMZ_OT_paste_rotation
from .tools.blenderhelper import get_armature_obj
from .sollumz_properties import (
    SollumType,
    MaterialType,
    SOLLUMZ_UI_NAMES,
)
from .sollumz_helper import find_sollumz_parent
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
    col = side_col.column(align=True)
    col.operator(add_operator, text="", icon="ADD")
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
        except:
            AttributeError(
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

        return operator.bl_idname == cls.operator_id

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
    operator_id = "SOLLUMZ_OT_import_assets"

    def get_settings(self, context: bpy.types.Context):
        return get_import_settings(context)

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        ...


class SollumzExportSettingsPanel(SollumzFileSettingsPanel):
    operator_id = "SOLLUMZ_OT_export_assets"

    def get_settings(self, context: bpy.types.Context):
        return get_export_settings(context)

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        ...


class SOLLUMZ_PT_import_asset(bpy.types.Panel, SollumzImportSettingsPanel):
    bl_label = "Import Asset"
    bl_order = 0

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.prop(settings, "import_as_asset")


class SOLLUMZ_PT_import_fragment(bpy.types.Panel, SollumzImportSettingsPanel):
    bl_label = "Fragment"
    bl_order = 1

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.prop(settings, "split_by_group")


class SOLLUMZ_PT_import_ydd(bpy.types.Panel, SollumzImportSettingsPanel):
    bl_label = "Drawable Dictionary"
    bl_order = 2

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.prop(settings, "import_ext_skeleton")


class SOLLUMZ_UL_armature_list(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_armature_list"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()

            # Armature is contained in "skel" object, so we need its parent
            armature_obj = get_armature_obj(item)
            if armature_obj is not None:
                armature_parent = armature_obj.parent

                row.label(text=item.name if armature_parent is None else f"{armature_parent.name} - {item.name}",
                          icon="OUTLINER_DATA_ARMATURE")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="OUTLINER_DATA_ARMATURE")


class SOLLUMZ_PT_import_ymap(bpy.types.Panel, SollumzImportSettingsPanel):
    bl_label = "Ymap"
    bl_order = 3

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzImportSettings):
        layout.prop(settings, "ymap_skip_missing_entities")
        layout.prop(settings, "ymap_exclude_entities")
        layout.prop(settings, "ymap_instance_entities")
        layout.prop(settings, "ymap_box_occluders")
        layout.prop(settings, "ymap_model_occluders")
        layout.prop(settings, "ymap_car_generators")


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
        layout.prop(settings, "export_with_ytyp")


class SOLLUMZ_PT_export_fragment(bpy.types.Panel, SollumzExportSettingsPanel):
    bl_label = "Fragment"
    bl_order = 2

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        layout.column().prop(settings, "export_lods")


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


class SOLLUMZ_PT_export_ymap(bpy.types.Panel, SollumzExportSettingsPanel):
    bl_label = "Ymap"
    bl_order = 5

    def draw_settings(self, layout: bpy.types.UILayout, settings: SollumzExportSettings):
        layout.prop(settings, "ymap_exclude_entities")
        layout.prop(settings, "ymap_box_occluders")
        layout.prop(settings, "ymap_model_occluders")
        layout.prop(settings, "ymap_car_generators")


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
        row.operator("sollumz.import_assets")

        if context.scene.sollumz_export_path != "":
            op = row.operator("sollumz.export_assets")
            op.directory = context.scene.sollumz_export_path
            op.direct_export = True
        else:
            row.operator("sollumz.export_assets")


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

    @classmethod
    def poll(self, context):
        preferences = get_addon_preferences(bpy.context)
        show_panel = preferences.show_vertex_painter
        return show_panel

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


class SOLLUMZ_PT_DEBUG_PANEL(GeneralToolChildPanel, bpy.types.Panel):
    bl_label = "Debug"
    bl_idname = "SOLLUMZ_PT_DEBUG_PANEL"
    bl_order = 4

    def draw_header(self, context):
        self.layout.label(text="", icon="PREFERENCES")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator("sollumz.debug_hierarchy")
        row.prop(context.scene, "debug_sollum_type")
        row = layout.row()
        row.operator("sollumz.debug_fix_light_intensity")
        row.prop(context.scene, "debug_lights_only_selected")

        layout.separator()

        layout.label(text="Migration")
        layout.operator("sollumz.migratedrawable")
        layout.label(
            text="This will join all geometries for each LOD Level into a single object.", icon="ERROR")
        layout.operator("sollumz.migrateboundgeoms")
        layout.operator("sollumz.replace_armature_constraints")


class SOLLUMZ_PT_EXPORT_PATH_PANEL(GeneralToolChildPanel, bpy.types.Panel):
    bl_label = "Export path"
    bl_idname = "SOLLUMZ_PT_EXPORT_PATH_PANEL"
    bl_order = 5

    def draw_header(self, context):
        self.layout.label(text="", icon="FILEBROWSER")

    def draw(self, context):
        self.layout.prop(context.scene, "sollumz_export_path", text="")


class SOLLUMZ_PT_TERRAIN_PAINTER_PANEL(GeneralToolChildPanel, bpy.types.Panel):
    bl_label = "Terrain Painter"
    bl_idname = "SOLLUMZ_PT_TERRAIN_PAINTER_PANEL"
    bl_parent_id = SOLLUMZ_PT_VERTEX_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        self.layout.label(text="", icon="IMAGE")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("sollumz.paint_tex1")
        row.operator("sollumz.paint_tex2")
        row = layout.row()
        row.operator("sollumz.paint_tex3")
        row.operator("sollumz.paint_tex4")
        row = layout.row()
        row.operator("sollumz.paint_a")
        row.prop(context.scene, "vert_paint_alpha")


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

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        mat = aobj.active_material

        if not mat or mat.sollum_type == MaterialType.NONE:
            layout.label(text="No sollumz material active.", icon="ERROR")
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
