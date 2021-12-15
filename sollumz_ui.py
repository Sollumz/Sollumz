import bpy
from .sollumz_helper import *
from .sollumz_properties import *
from .ybn.ui import draw_bound_properties, draw_collision_material_properties
from .ydr.ui import draw_drawable_properties, draw_geometry_properties, draw_shader, draw_shader_texture_params, draw_shader_value_params
from .yft.ui import draw_fragment_properties, draw_archetype_properties, draw_group_properties, draw_lod_properties, draw_child_properties


class SOLLUMZ_PT_import_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
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
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
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
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
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
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
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


class SOLLUMZ_PT_export_main(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = ""
    bl_parent_id = "FILE_PT_operator"
    bl_options = {'HIDE_HEADER'}
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
                 text="", icon='NEWFOLDER')


class SOLLUMZ_PT_export_include(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
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


class SOLLUMZ_PT_export_exclude(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
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
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
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
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
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
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="MODIFIER_DATA")

    def draw(self, context):
        layout = self.layout
        layout.label(text="View")
        layout.prop(context.scene, "hide_collision")
        layout.prop(context.scene, "hide_high_lods")
        layout.prop(context.scene, "hide_medium_lods")
        layout.prop(context.scene, "hide_low_lods")
        layout.prop(context.scene, "hide_very_low_lods")
        layout.prop(context.space_data.overlay,
                    "show_bones", text="Show Skeleton")


class SOLLUMZ_PT_DEBUG_PANEL(bpy.types.Panel):
    bl_label = "Debug"
    bl_idname = "SOLLUMZ_PT_DEBUG_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="PREFERENCES")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("sollumz.debug_hierarchy")
        row.prop(context.scene, "debug_sollum_type")


class SOLLUMZ_PT_VERTEX_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Vertex Painter"
    bl_idname = "SOLLUMZ_PT_VERTEX_TOOL_PANELL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="BRUSH_DATA")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.scene, "vert_paint_color")
        row.operator("sollumz.paint_vertices")


class SOLLUMZ_PT_TERRAIN_PAINTER_PANEL(bpy.types.Panel):
    bl_label = "Terrain Painter"
    bl_idname = "SOLLUMZ_PT_TERRAIN_PAINTER_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_VERTEX_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
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
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="FILE")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("sollumz.importymap")
        row.operator("sollumz.exportymap")


class SOLLUMZ_PT_ENTITY_PANEL(bpy.types.Panel):
    bl_label = "Entity"
    bl_idname = 'SOLLUMZ_PT_ENTITY_PANEL'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_YMAP_TOOL_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        aobj = context.active_object
        if(aobj == None or aobj.sollum_type != SollumType.DRAWABLE):
            # have to put this outside of text = or it wont work?
            layout.label(
                text="Please select a valid object.")
            return
        layout.label(text="Entity Fields")
        # box.prop(aobj.ymap_properties, "archetype_name")
        layout.prop(aobj, "name", text="Archetype Name")
        # box.prop(aobj.ymap_properties, "position")
        row = layout.row()
        row.prop(aobj, "location", text="Position")
        # box.prop(aobj.ymap_properties, "rotation")
        row = layout.row()
        row.prop(aobj, "rotation_euler", text="Rotation")
        # box.prop(aobj.ymap_properties, "scale_xy")
        # box.prop(aobj.ymap_properties, "scale_z")
        row = layout.row()
        row.prop(aobj, "scale", text="ScaleXYZ")
        row = layout.row()
        row.prop(aobj.entity_properties, "flags")
        row.prop(aobj.entity_properties, "guid")
        row = layout.row()
        row.prop(aobj.entity_properties, "parent_index")
        row = layout.row()
        row.prop(aobj.entity_properties, "lod_dist")
        row.prop(aobj.entity_properties, "child_lod_dist")
        row.prop(aobj.entity_properties, "num_children")
        row = layout.row()
        row.prop(aobj.entity_properties, "ambient_occlusion_multiplier")
        row.prop(aobj.entity_properties, "artificial_ambient_occlusion")
        row.prop(aobj.entity_properties, "tint_value")
        row = layout.row()
        row.prop(aobj.entity_properties, "lod_level")
        row.prop(aobj.entity_properties, "priority_level")


class SOLLUMZ_PT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAT_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        if(context.active_object == None):
            return

        mat = aobj.active_material
        if(mat == None):
            layout.label(text="No sollumz material active.", icon="ERROR")
            return

        if mat.sollum_type == MaterialType.SHADER:
            draw_shader(layout, mat)
        elif mat.sollum_type == MaterialType.COLLISION:
            draw_collision_material_properties(layout, mat)
        else:
            layout.label(text="No sollumz material active.", icon="ERROR")


class SOLLUMZ_PT_TXTPARAMS_PANEL(bpy.types.Panel):
    bl_label = "Texture Parameters"
    bl_idname = 'SOLLUMZ_PT_TXTPARAMS_PANEL'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname
    bl_order = 0

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj:
            mat = obj.active_material
            return mat and mat.sollum_type != MaterialType.NONE and mat.sollum_type != MaterialType.COLLISION
        else:
            return False

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        if(context.active_object == None):
            return

        mat = aobj.active_material
        if(mat == None):
            return

        draw_shader_texture_params(layout, mat)


class SOLLUMZ_PT_VALUEPARAMS_PANEL(bpy.types.Panel):
    bl_label = "Value Parameters"
    bl_idname = 'SOLLUMZ_PT_VALUEPARAMS_PANEL'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname
    bl_order = 1

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj:
            mat = obj.active_material
            return mat and mat.sollum_type != MaterialType.NONE and mat.sollum_type != MaterialType.COLLISION
        else:
            return False

    def draw(self, context):
        layout = self.layout

        aobj = context.active_object
        if(context.active_object == None):
            return

        mat = aobj.active_material
        if(mat == None):
            return

        draw_shader_value_params(layout, mat)


class SOLLUMZ_PT_OBJECT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {'DEFAULT_CLOSED'}

    def draw_drawable_model_properties(self, context, layout, obj):
        layout.prop(obj.drawable_model_properties, "render_mask")
        layout.prop(obj.drawable_model_properties, "flags")
        layout.prop(obj.drawable_model_properties, "sollum_lod")

    def draw_sollum_type(self, layout, obj):
        row = layout.row()
        row.enabled = False
        row.prop(obj, "sollum_type")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        obj = context.active_object

        if obj.sollum_type == SollumType.DRAWABLE:
            self.draw_sollum_type(layout, obj)
            draw_drawable_properties(layout, obj)
        elif obj.sollum_type == SollumType.DRAWABLE_GEOMETRY:
            self.draw_sollum_type(layout, obj)
            draw_geometry_properties(layout, obj)
        elif(obj.sollum_type == SollumType.DRAWABLE_MODEL):
            self.draw_sollum_type(layout, obj)
            self.draw_drawable_model_properties(context, layout, obj)
            self.draw_sollum_type(layout, obj)
        elif(obj.sollum_type == SollumType.FRAGMENT):
            self.draw_sollum_type(layout, obj)
            draw_fragment_properties(layout, obj)
        elif(obj.sollum_type == SollumType.FRAGGROUP):
            self.draw_sollum_type(layout, obj)
            draw_group_properties(layout, obj)
        elif(obj.sollum_type == SollumType.FRAGCHILD):
            self.draw_sollum_type(layout, obj)
            draw_child_properties(layout, obj)
        elif(obj.sollum_type == SollumType.FRAGLOD):
            self.draw_sollum_type(layout, obj)
            draw_lod_properties(layout, obj)
        elif obj.sollum_type in BOUND_TYPES:
            self.draw_sollum_type(layout, obj)
            draw_bound_properties(layout, obj)
        else:
            layout.label(
                text="No sollumz objects in scene selected.", icon="ERROR")


class SOLLUMZ_MT_sollumz(bpy.types.Menu):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_MT_sollumz"

    def draw(self, context):
        layout = self.layout


def DrawSollumzMenu(self, context):
    self.layout.separator()
    self.layout.menu(SOLLUMZ_MT_sollumz.bl_idname, icon="BLENDER")


def register():
    bpy.types.VIEW3D_MT_add.append(DrawSollumzMenu)


def unregister():
    bpy.types.VIEW3D_MT_add.remove(DrawSollumzMenu)
