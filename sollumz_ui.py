import bpy
from .sollumz_helper import *
from .sollumz_properties import *
from .ybn.ui import draw_bound_properties, draw_collision_material_properties
from .ydr.ui import draw_drawable_properties, draw_geometry_properties, draw_shader, draw_light_properties
from .yft.ui import draw_fragment_properties, draw_archetype_properties, draw_lod_properties, draw_child_properties


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


class SOLLUMZ_PT_export_geometry(bpy.types.Panel):
    bl_space_type = 'FILE_BROWSER'
    bl_region_type = 'TOOL_PROPS'
    bl_label = "Geometry"
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

        layout.prop(operator.export_settings, "use_transforms")


class SOLLUMZ_PT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "General Tools"
    bl_idname = "SOLLUMZ_PT_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

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

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("sollumz.debug_hierarchy")
        row.prop(context.scene, "debug_sollum_type")


class SOLLUMZ_PT_VERTEX_TOOL_PANELL(bpy.types.Panel):
    bl_label = "Vertex Painter"
    bl_idname = "SOLLUMZ_PT_VERTEX_TOOL_PANELL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.scene, "vert_paint_color")
        row.operator("sollumz.paint_vertices")


class SOLLUMZ_PT_YMAP_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Ymap Tools"
    bl_idname = "SOLLUMZ_PT_YMAP_TOOL_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

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
        #box.prop(aobj.ymap_properties, "archetype_name")
        layout.prop(aobj, "name", text="Archetype Name")
        #box.prop(aobj.ymap_properties, "position")
        row = layout.row()
        row.prop(aobj, "location", text="Position")
        #box.prop(aobj.ymap_properties, "rotation")
        row = layout.row()
        row.prop(aobj, "rotation_euler", text="Rotation")
        #box.prop(aobj.ymap_properties, "scale_xy")
        #box.prop(aobj.ymap_properties, "scale_z")
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
        # layout.use_property_split = True
        aobj = context.active_object
        if(context.active_object == None):
            return

        mat = context.active_object.active_material

        if(mat == None):
            return

        if mat.sollum_type == MaterialType.SHADER:
            draw_shader(layout, mat)
        elif mat.sollum_type == MaterialType.COLLISION and aobj.sollum_type in BOUND_POLYGON_TYPES:
            draw_collision_material_properties(layout, mat)


class SOLLUMZ_PT_OBJECT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.sollum_type != SollumType.NONE

    def draw_drawable_model_properties(self, context, layout, obj):
        layout.prop(obj.drawable_model_properties, "render_mask")
        layout.prop(obj.drawable_model_properties, "flags")
        layout.prop(obj.drawable_model_properties, "sollum_lod")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        obj = context.active_object

        row = layout.row()
        row.enabled = False
        row.prop(obj, "sollum_type")

        if obj.sollum_type == SollumType.DRAWABLE:
            draw_drawable_properties(layout, obj)
        elif obj.sollum_type == SollumType.DRAWABLE_GEOMETRY:
            draw_geometry_properties(layout, obj)
        elif(obj.sollum_type == SollumType.DRAWABLE_MODEL):
            self.draw_drawable_model_properties(context, layout, obj)
        elif(obj.sollum_type == SollumType.FRAGMENT):
            draw_fragment_properties(layout, obj)
        elif(obj.sollum_type == SollumType.LOD):
            draw_lod_properties(layout, obj)
        elif(obj.sollum_type == SollumType.ARCHETYPE):
            draw_archetype_properties(layout, obj)
        elif(obj.sollum_type == SollumType.CHILD):
            draw_child_properties(layout, obj)
        elif(obj.sollum_type == SollumType.LIGHT):
            draw_light_properties(layout, obj)
        elif obj.sollum_type in BOUND_TYPES:
            draw_bound_properties(layout, obj)


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
