import bpy
from .tools.blenderhelper import get_armature_obj
from .sollumz_properties import SollumType, MaterialType


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

    @ classmethod
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


class SOLLUMZ_PT_import_geometry(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 1

    @ classmethod
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

    @ classmethod
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

    @ classmethod
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

            # Armature is contained in "skel" object, so we need its parent (which is pack:/... or ped root..)
            armature_obj = get_armature_obj(item)
            if armature_obj is not None:
                armature_parent = armature_obj.parent

                row.label(text=F"{armature_parent.name} - {item.name}",
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

    @ classmethod
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


class SOLLUMZ_PT_export_main(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {"HIDE_HEADER"}
    bl_order = 0

    @ classmethod
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


class SOLLUMZ_PT_export_geometry(bpy.types.Panel):
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"
    bl_label = "Geometry"
    bl_parent_id = "FILE_PT_operator"
    bl_order = 3

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

        layout.prop(operator.export_settings, "use_transforms")


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
        layout.label(text="View")

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


class SOLLUMZ_PT_DEBUG_PANEL(bpy.types.Panel):
    bl_label = "Debug"
    bl_idname = "SOLLUMZ_PT_DEBUG_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        self.layout.label(text="", icon="PREFERENCES")

    def draw(self, context):
        layout = self.layout
        layout.label(text="Sollumz Version: 1.3.1")
        row = layout.row()
        row.operator("sollumz.debug_hierarchy")
        row.prop(context.scene, "debug_sollum_type")


class SOLLUMZ_PT_VERTEX_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Vertex Painter"
    bl_idname = "SOLLUMZ_PT_VERTEX_TOOL_PANELL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        self.layout.label(text="", icon="BRUSH_DATA")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.scene, "vert_paint_color")
        row.operator("sollumz.paint_vertices")


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


class SOLLUMZ_PT_YMAP_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Ymap Tools"
    bl_idname = "SOLLUMZ_PT_YMAP_TOOL_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        self.layout.label(text="", icon="FILE")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("sollumz.importymap")
        row.operator("sollumz.exportymap")


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

    @ classmethod
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
