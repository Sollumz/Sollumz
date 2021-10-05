import bpy
from Sollumz.sollumz_properties import is_sollum_type, ObjectType
from .properties import TextureFlags, TextureProperties


def draw_drawable_properties(layout, obj):
    layout.prop(obj.drawable_properties, "lod_dist_high")
    layout.prop(obj.drawable_properties, "lod_dist_med")
    layout.prop(obj.drawable_properties, "lod_dist_low")
    layout.prop(obj.drawable_properties, "lod_dist_vlow")
    
def draw_geometry_properties(layout, obj):
    layout.prop(obj.geometry_properties, "sollum_lod")

def draw_material_properties(layout, mat):
    box = layout.box()
    row = box.row()
    row.prop(mat.shader_properties, "renderbucket")
    row.prop(mat.shader_properties, "filename")

class SOLLUMZ_PT_SHADER_PANEL(bpy.types.Panel):
    bl_label = "Sollumz Shader Panel"
    bl_idname = "SOLLUMZ_PT_SHADER_PANEL"
    bl_space_type = 'NODE_EDITOR'
    bl_region_type = 'UI'
    bl_category = "Item"

    def draw(self, context):
        layout = self.layout

        nodes = context.selected_nodes
        aobj = bpy.context.active_object

        if aobj and aobj.data: #and aobj.sollum_type and is_sollum_type(aobj, ObjectType):
            mat = bpy.context.active_object.data.materials[0]
        else:
            return

        for n in nodes:
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                box = layout.box()
                box.prop(n, "image")
                row = box.row()
                for prop in TextureProperties.__annotations__:
                    row.prop(n.texture_properties, prop)

                # Flags
                box = box.box()
                row = box.row()
                item_index = 0
                for prop in TextureFlags.__annotations__:
                    if item_index % 4 == 0 and item_index > 1:
                        row = box.row()
                    row.prop(n.texture_properties, prop)
                    item_index += 1

            if(isinstance(n, bpy.types.ShaderNodeValue)):
                i = 0
                box = layout.box()
                for n in mat.node_tree.nodes:
                    if(isinstance(n, bpy.types.ShaderNodeValue)):
                        if(i == 4):
                            box = layout.box()
                            i = 0

                        #fix variable name for display
                        n_array = n.name.split('_')
                        name = n_array[0].capitalize()
                        letter = n_array[1].upper()
                        label = name + " " + letter
                        box.label(text = label)
                        
                        row = box.row()
                        row.prop(n.outputs[0], "default_value")
                        i += 1