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

def draw_shader(layout, mat):  
        layout.label(text = "Material Properties")
        box = layout.box()
        row = box.row()
        row.prop(mat.shader_properties, "renderbucket")
        row.prop(mat.shader_properties, "filename")

        layout.label(text = "Texture Parameters")
        nodes = mat.node_tree.nodes
        for n in nodes:   
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
                box = layout.box()
                row = box.row(align = True)
                row.label(text = "Texture Type: " + n.name)
                row.label(text = "Texture Name: " + n.image.name)
                row = box.row()
                row.prop(n.image, "filepath", text = "Texture Path")
                row = box.row(align = True)
                row.prop(n.texture_properties, "embedded")
                row.prop(n.texture_properties, "format")
                row.prop(n.texture_properties, "usage")
                #box = box.box()
                box.label(text = "Flags")
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
                row = box.row()
                row.prop(n.texture_properties, "unk24") 
                row.prop(n.texture_properties, "extra_flags")
        
        layout.label(text = "Shader Parameters")
        value_param_box = layout.box()

        for n in nodes:  # LOOP SERERATE SO TEXTURES SHOW ABOVE VALUE PARAMS
            if(isinstance(n, bpy.types.ShaderNodeValue)):
                if(n.name[-1] == "x"):
                    row = value_param_box.row()
                    row.label(text = n.name[:-2])    

                    x = n
                    y = mat.node_tree.nodes[n.name[:-1] + "y"]
                    z = mat.node_tree.nodes[n.name[:-1] + "z"]
                    w = mat.node_tree.nodes[n.name[:-1] + "w"]

                    row.prop(x.outputs[0], "default_value", text = "X:")
                    row.prop(y.outputs[0], "default_value", text = "Y:")
                    row.prop(z.outputs[0], "default_value", text = "Z:")
                    row.prop(w.outputs[0], "default_value", text = "W:")

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

class SOLLUMZ_UL_BONE_FLAGS(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index): 
        custom_icon = 'FILE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}: 
            layout.prop(item, 'name', text='', icon = custom_icon, emboss=False, translate=False)
        elif self.layout_type in {'GRID'}: 
            layout.alignment = 'CENTER' 
            layout.prop(item, 'name', text='', icon = custom_icon, emboss=False, translate=False)

class SOLLUMZ_PT_BONE_PANEL(bpy.types.Panel):
    bl_label = "Bone Properties"
    bl_idname = "SOLLUMZ_PT_BONE_PANEL"
    bl_category = "Sollumz"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    #bl_context = "bone"
    
    def draw(self, context):
        layout = self.layout

        if (context.active_pose_bone == None):
            return

        bone = context.active_pose_bone.bone

        layout.prop(bone, "name", text = "Bone Name")
        layout.prop(bone.bone_properties, "tag", text = "BoneTag")

        layout.label(text="Flags")
        layout.template_list("SOLLUMZ_UL_BONE_FLAGS", "Flags", bone.bone_properties, "flags", bone.bone_properties, "ul_index")
        row = layout.row() 
        row.operator('sollumz.bone_flags_new_item', text='New')
        row.operator('sollumz.bone_flags_delete_item', text='Delete')