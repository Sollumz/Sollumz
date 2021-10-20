import bpy
from Sollumz.ydr.shader_materials import *
from .operators import *
import os

def draw_drawable_properties(layout, obj):
    layout.prop(obj.drawable_properties, "lod_dist_high")
    layout.prop(obj.drawable_properties, "lod_dist_med")
    layout.prop(obj.drawable_properties, "lod_dist_low")
    layout.prop(obj.drawable_properties, "lod_dist_vlow")
    
def draw_geometry_properties(layout, obj):
    return 
    #layout.label(text = "")

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
        row.prop(mat.shader_properties, "filename", text='Shader Name')

        layout.label(text = "Texture Parameters")
        nodes = mat.node_tree.nodes

        #only using selected nodes because if you use the node tree weird bug 
        #where if you select one of the image nodes it swaps around the order that you edit them in...
        #I think this is because when you select something "mat.node_tree.nodes" is reordered for the selected to be in front..... 
        #annoyying as hell
        selected_nodes = []
        for n in nodes:
            if(n.select == True):
                selected_nodes.append(n)

        for n in selected_nodes:
            if(isinstance(n, bpy.types.ShaderNodeTexImage)):
            #if(n.name == "SpecSampler"):
                box = layout.box()
                row = box.row(align = True)
                name = os.path.splitext(os.path.basename(n.image.filepath))[0]
                row.label(text = "Texture Type: " + n.name) 
                row.label(text = "Texture Name: " + name)
                row = box.row()
                row.prop(n.image, "filepath", text = "Texture Path")
                row = box.row(align = True)
                row.prop(n.texture_properties, "embedded")
                if(n.texture_properties.embedded == False):
                    break
                row.prop(n.texture_properties, "format")
                row.prop(n.texture_properties, "usage")
                #box = box.box()
                box.label(text = "Flags")
                row = box.row()
                row.prop(n.texture_flags, "not_half")
                row.prop(n.texture_flags, "hd_split")
                row.prop(n.texture_flags, "flag_full")
                row.prop(n.texture_flags, "maps_half")
                row = box.row()
                row.prop(n.texture_flags, "x2")
                row.prop(n.texture_flags, "x4")
                row.prop(n.texture_flags, "y4")
                row.prop(n.texture_flags, "x8")
                row = box.row()
                row.prop(n.texture_flags, "x16")
                row.prop(n.texture_flags, "x32")
                row.prop(n.texture_flags, "x64")
                row.prop(n.texture_flags, "y64")
                row = box.row()
                row.prop(n.texture_flags, "x128")
                row.prop(n.texture_flags, "x256")
                row.prop(n.texture_flags, "x512")
                row.prop(n.texture_flags, "y512")
                row = box.row()
                row.prop(n.texture_flags, "x1024")
                row.prop(n.texture_flags, "y1024")
                row.prop(n.texture_flags, "x2048")
                row.prop(n.texture_flags, "y2048")
                row = box.row()
                row.prop(n.texture_flags, "embeddedscriptrt")
                row.prop(n.texture_flags, "unk19")
                row.prop(n.texture_flags, "unk20")
                row.prop(n.texture_flags, "unk21")
                row = box.row()
                row.prop(n.texture_flags, "unk24") 
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

class SOLLUMZ_UL_SHADER_MATERIALS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_SHADER_MATERIALS_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        name = shadermats[item.index].ui_name
        # If the object is selected
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=name, icon='MATERIAL')
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=name, emboss=False, icon='MATERIAL')

class SOLLUMZ_PT_DRAWABLE_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Drawable Tools"
    bl_idname = "SOLLUMZ_PT_DRAWABLE_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        pass

class SOLLUMZ_PT_CREATE_SHADER_PANEL(bpy.types.Panel):
    bl_label = "Create Shader"
    bl_idname = "SOLLUMZ_PT_CREATE_SHADER_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.template_list(
            SOLLUMZ_UL_SHADER_MATERIALS_LIST.bl_idname, "", context.scene, "shader_materials", context.scene, "shader_material_index"
        )
        layout.operator(SOLLUMZ_OT_create_shader_material.bl_idname)

class SOLLUMZ_PT_CREATE_DRAWABLE_PANEL(bpy.types.Panel):
    bl_label = "Create Drawable Objects"
    bl_idname = "SOLLUMZ_PT_CREATE_DRAWABLE_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_drawable.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_drawable_model.bl_idname)
        row.operator(SOLLUMZ_OT_create_geometry.bl_idname)

class SOLLUMZ_PT_DRAWABLE_CONVERSION_PANEL(bpy.types.Panel):
    bl_label = "Conversion"
    bl_idname = "SOLLUMZ_PT_DRAWABLE_CONVERSION_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(SOLLUMZ_OT_convert_mesh_to_drawable.bl_idname)
        row.prop(context.scene, 'multiple_ydrs')
        row.prop(context.scene, 'convert_ydr_use_mesh_names')
        row = layout.row()
        row.operator(SOLLUMZ_OT_convert_to_shader_material.bl_idname)

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
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "bone"
    
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