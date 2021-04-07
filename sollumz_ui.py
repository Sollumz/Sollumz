import bpy

class SOLLUMZ_PT_SHADER_PANEL(bpy.types.Panel):
    bl_label = "Sollumz Shader Panel"
    bl_idname = "Sollumz_PT_SHADER_PANEL"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Item"

    def draw(self, context):
        layout = self.layout

        nodes = context.selected_nodes
        mat = bpy.context.active_object.data.materials[0]

        for n in nodes:
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                box = layout.box()
                box.prop(n, "image")
                row = box.row()
                row.prop(n.texture_properties, "embedded")
                row.prop(n.texture_properties, "format")
                row.prop(n.texture_properties, "extra_flags")
                box = box.box()
                row = box.row()
                row.prop(n.texture_properties, "not_half")
                row.prop(n.texture_properties, "hd_split")
                row.prop(n.texture_properties, "flag_full")
                row.prop(n.texture_properties, "maps_half")
                row = box.row()
                row.prop(n.texture_properties, "x2")
                row.prop(n.texture_properties, "x4")
                row.prop(n.texture_properties, "y4")
                row.prop(n.texture_properties, "x8")
                row = box.row()
                row.prop(n.texture_properties, "x16")
                row.prop(n.texture_properties, "x32")
                row.prop(n.texture_properties, "x64")
                row.prop(n.texture_properties, "y64")
                row = box.row()
                row.prop(n.texture_properties, "x128")
                row.prop(n.texture_properties, "x256")
                row.prop(n.texture_properties, "x512")
                row.prop(n.texture_properties, "y512")
                row = box.row()
                row.prop(n.texture_properties, "x1024")
                row.prop(n.texture_properties, "y1024")
                row.prop(n.texture_properties, "x2048")
                row.prop(n.texture_properties, "y2048")
                row = box.row()
                row.prop(n.texture_properties, "embeddedscriptrt")
                row.prop(n.texture_properties, "unk19")
                row.prop(n.texture_properties, "unk20")
                row.prop(n.texture_properties, "unk21")
                row.prop(n.texture_properties, "unk24") 

        i = 0
        box = layout.box()
        for n in mat.node_tree.nodes:
            if(isinstance(n, bpy.types.ShaderNodeValue)):
                if(i == 4):
                    box = layout.box()
                    i = 0
                box.label(text = n.name)
                row = box.row()
                row.prop(n.outputs[0], "default_value")
                i += 1

class SOLLUMZ_PT_MAT_PANEL(bpy.types.Panel):
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
        row.prop(mat.shader_properties, "renderbucket")
        row.prop(mat.shader_properties, "filename")

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