import bpy
from .tools.blenderhelper import get_armature_obj, get_addon_preferences
from .sollumz_properties import SollumType, MaterialType


def draw_list_with_add_remove(layout: bpy.types.UILayout, add_operator: str, remove_operator: str, *temp_list_args, **temp_list_kwargs):
    """Draw a UIList with an add and remove button on the right column. Returns the left column."""
    row = layout.row()
    list_col = row.column()
    list_col.template_list(*temp_list_args, **temp_list_kwargs)
    col = row.column(align=True)
    col.operator(add_operator, text="", icon="ADD")
    col.operator(remove_operator, text="", icon="REMOVE")

    return list_col


class BasicListHelper:
    """Provides functionality for drawing simple lists where each item has a name and icon"""
    name_prop: str = "name"
    item_icon: str = "NONE"
    name_editable: bool = True

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if not self.name_editable:
            layout.label(text=getattr(item, self.name_prop),
                         icon=self.item_icon)
            return

        layout.prop(item, self.name_prop, text="",
                    emboss=False, icon=self.item_icon)


class OrderListHelper:
    orderkey = "name"

    def filter_items(self, context, data, propname):
        helper = bpy.types.UI_UL_list
        items = getattr(data, propname)
        ordered = helper.sort_items_by_name(items, self.orderkey)
        filtered = helper.filter_items_by_name(
            self.filter_name, self.bitflag_filter_item, items, propname=self.orderkey, flags=None, reverse=False)
        return filtered, ordered


class SOLLUMZ_PT_import_main(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"HIDE_HEADER"}
    bl_order = 0

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_import"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.import_settings, "batch_mode")
        layout.prop(operator.import_settings, "import_as_asset")


class SOLLUMZ_PT_import_geometry(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_import"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.import_settings, "join_geometries")


class SOLLUMZ_PT_import_fragment(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Fragment"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_import"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.import_settings, "split_by_bone")


class SOLLUMZ_PT_import_skeleton(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Skeleton"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 3

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_import"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.import_settings, "import_ext_skeleton")


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


class SOLLUMZ_PT_import_animation(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Animation"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 4

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_import"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        armature_list_box = layout.box()

        armature_list_box.label(text="Target skeleton")

        armature_list_box.template_list(SOLLUMZ_UL_armature_list.bl_idname, "",
                                        bpy.data, "armatures", operator.import_settings, "selected_armature")


class SOLLUMZ_PT_import_ymap(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Ymap"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 5

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_import"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.import_settings, "ymap_skip_missing_entities")
        layout.prop(operator.import_settings, "ymap_exclude_entities")
        layout.prop(operator.import_settings, "ymap_box_occluders")
        layout.prop(operator.import_settings, "ymap_model_occluders")
        layout.prop(operator.import_settings, "ymap_car_generators")


class SOLLUMZ_PT_export_main(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"HIDE_HEADER"}
    bl_order = 0

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_export"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        row = layout.row(align=True)
        row.prop(operator.export_settings, "batch_mode")
        sub = row.row(align=True)
        sub.prop(operator.export_settings, "use_batch_own_dir",
                 text="", icon="NEWFOLDER")


class SOLLUMZ_PT_export_include(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Include"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_export"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        sublayout = layout.column(heading="Limit to")
        sublayout.enabled = (operator.export_settings.batch_mode == "OFF")
        sublayout.prop(operator.export_settings, "use_selection")
        sublayout.prop(operator.export_settings, "use_active_collection")

        col = layout.column()
        col.prop(operator.export_settings, "sollum_types")

        layout.prop(operator.export_settings, "export_with_ytyp")


class SOLLUMZ_PT_export_exclude(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Exclude"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 2

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_export"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.export_settings, "exclude_skeleton")


class SOLLUMZ_PT_export_fragment(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Fragment"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 4

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_export"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.export_settings, "export_with_hi")
        layout.prop(operator.export_settings, "auto_calculate_inertia")
        layout.prop(operator.export_settings, "auto_calculate_volume")


class SOLLUMZ_PT_export_ymap(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Ymap"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 5

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_export"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.export_settings, "ymap_exclude_entities")
        layout.prop(operator.export_settings, "ymap_box_occluders")
        layout.prop(operator.export_settings, "ymap_model_occluders")
        layout.prop(operator.export_settings, "ymap_car_generators")


class SOLLUMZ_PT_export_drawable(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Drawable"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 6

    @classmethod
    def poll(cls, context):
        sfile = context.space_data
        operator = sfile.active_operator
        return operator.bl_idname == "SOLLUMZ_OT_export"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        sfile = context.space_data
        operator = sfile.active_operator

        layout.prop(operator.export_settings, "auto_calculate_bone_tag")


class SOLLUMZ_PT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "General Tools"
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
        row.operator("sollumz.import")
        row.operator("sollumz.export")


class SOLLUMZ_PT_VIEW_PANEL(bpy.types.Panel):
    bl_label = "View"
    bl_idname = "SOLLUMZ_PT_VIEW_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname
    bl_order = 0

    def draw_header(self, context):
        self.layout.label(text="", icon="PREFERENCES")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.scene, "hide_high_lods")
        row.prop(context.scene, "hide_medium_lods")

        row2 = layout.row()
        row2.prop(context.scene, "hide_low_lods")
        row2.prop(context.scene, "hide_collision")

        row3 = layout.row()
        row3.prop(context.scene, "hide_very_low_lods")
        row3.prop(context.space_data.overlay,
                  "show_bones", text="Show Skeleton")

        row4 = layout.row()
        row4.prop(context.scene, "hide_vehicle_windows")


class SOLLUMZ_PT_OBJ_YMAP_LOCATION(bpy.types.Panel):
    bl_label = "Copy Objects Location to Clipboard"
    bl_idname = "SOLLUMZ_PT_OBJ_YMAP_LOCATION"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname
    bl_order = 3

    def draw_header(self, context):
        self.layout.label(text="", icon="OBJECT_ORIGIN")

    def draw(self, context):
        layout = self.layout

        # Get the locations of the selected objects
        selected_objects = bpy.context.selected_objects
        if len(selected_objects) > 0:
            for obj in selected_objects:
                loc = obj.location
                row = layout.row()
                row.label(text="{}: {:.2f}, {:.2f}, {:.2f}".format(obj.name, loc[0], loc[1], loc[2]))

                # Add a Clipboard button to copy the location to the clipboard
                clip_button = row.operator("wm.sollumz_copy_location", text="", icon='COPYDOWN')
                clip_button.location = "{:.2f}, {:.2f}, {:.2f}".format(loc[0], loc[1], loc[2])

            # Add a button to copy all selected objects' locations to the clipboard
            if len(selected_objects) > 1:
                row = layout.row()
                row.operator("wm.sollumz_copy_all_locations", text="Copy All Locations", icon='COPY_ID')
        else:
            layout.label(text="No objects selected")

class SOLLUMZ_OT_copy_location(bpy.types.Operator):
    """Copy the location of an object to the clipboard"""
    bl_idname = "wm.sollumz_copy_location"
    bl_label = ""
    location: bpy.props.StringProperty()

    def execute(self, context):
        bpy.context.window_manager.clipboard = self.location
        self.report({'INFO'}, "Location copied to clipboard: {}".format(self.location))
        return {'FINISHED'}

class SOLLUMZ_OT_copy_all_locations(bpy.types.Operator):
    """Copy the locations of all selected objects to the clipboard"""
    bl_idname = "wm.sollumz_copy_all_locations"
    bl_label = ""
    locations: bpy.props.StringProperty()

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        locations_text = ""
        for obj in selected_objects:
            loc = obj.location
            locations_text += "{}: {:.2f}, {:.2f}, {:.2f}\n".format(obj.name, loc[0], loc[1], loc[2])
        bpy.context.window_manager.clipboard = locations_text
        self.report({'INFO'}, "Locations copied to clipboard:\n{}".format(locations_text))
        return {'FINISHED'}

class SOLLUMZ_PT_VERTEX_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Vertex Painter"
    bl_idname = "SOLLUMZ_PT_VERTEX_TOOL_PANELL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname
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


class SOLLUMZ_PT_DEBUG_PANEL(bpy.types.Panel):
    bl_label = "Debug"
    bl_idname = "SOLLUMZ_PT_DEBUG_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname
    bl_order = 2

    def draw_header(self, context):
        self.layout.label(text="", icon="PREFERENCES")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Sollumz Version: 1.3.1")
        row = layout.row()
        row.operator("sollumz.debug_hierarchy")
        row.prop(context.scene, "debug_sollum_type")
        row = layout.row()
        row.operator("sollumz.debug_set_sollum_type")
        row.prop(context.scene, "all_sollum_type")
        row = layout.row()
        row.operator("sollumz.debug_fix_light_intensity")
        row.prop(context.scene, "debug_lights_only_selected")
        row = layout.row()
        row.operator("sollumz.debug_update_portal_names")


class SOLLUMZ_PT_TERRAIN_PAINTER_PANEL(bpy.types.Panel):
    bl_label = "Terrain Painter"
    bl_idname = "SOLLUMZ_PT_TERRAIN_PAINTER_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
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

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        obj = context.active_object
        row = layout.row()
        row.enabled = False
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

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        if context.active_object is None:
            return

        mat = aobj.active_material

        if not mat or mat.sollum_type == MaterialType.NONE:
            layout.label(text="No sollumz material active.", icon="ERROR")


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
        for index, prop_name in enumerate(data_block.__annotations__):
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
