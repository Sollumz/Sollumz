import bpy

class Sollumz_PT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz Material Panel"
    bl_idname = "Sollumz_PT_MAT_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout

        mat = bpy.context.active_object.data.materials[0]

        if(mat == None):
            return 

        box = layout.box()
        row = box.row()
        row.prop(mat.shader_properties, "embedded")
        row.prop(mat.shader_properties, "renderbucket")
        row.prop(mat.shader_properties, "filename")

        if(mat.shader_properties.embedded == True):
            row = box.row()
            row.prop(mat.shader_properties.texture_properties, "usage")
            row.prop(mat.shader_properties.texture_properties, "usageflags")
            row.prop(mat.shader_properties.texture_properties, "format")

class SOLLUMZ_PT_MAIN_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "scene"

    def draw_drawable_properties(self, context, layout, obj):
        layout.prop(obj.drawable_properties, "lod_dist_high")
        layout.prop(obj.drawable_properties, "lod_dist_med")
        layout.prop(obj.drawable_properties, "lod_dist_low")
        layout.prop(obj.drawable_properties, "lod_dist_vlow")
    
    def draw_geometry_properties(self, context, layout, obj):
        layout.prop(obj.geometry_properties, "sollum_lod")

    def draw(self, context):
        layout = self.layout

        obj = bpy.context.active_object

        if(obj == None):
            return

        layout.prop(obj, "sollum_type")
        
        if(obj.sollum_type == "sollumz_drawable"):
            self.draw_drawable_properties(context, layout, obj)
        elif(obj.sollum_type == "sollumz_geometry"):
            self.draw_geometry_properties(context, layout, obj)