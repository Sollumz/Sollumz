import bpy
from .shader_materials import *
from .operators import *


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


def draw_shader_texture_params(layout, mat):
    # only using selected nodes because if you use the node tree weird bug
    # where if you select one of the image nodes it swaps around the order that you edit them in...
    # I think this is because when you select something "mat.node_tree.nodes" is reordered for the selected to be in front.....
    # annoyying as hell
    #selected_nodes = []
    # for n in nodes:
    # if(n.select == True):
    # selected_nodes.append(n)
    nodes = mat.node_tree.nodes
    for n in nodes:
        if(isinstance(n, bpy.types.ShaderNodeTexImage)):
            # if(n.name == "SpecSampler"):
            box = layout.box()
            row = box.row(align=True)
            row.label(text="Texture Type: " + n.name)
            if n.image:
                row.label(text="Texture Name: " + n.image.name)
                row = box.row()
                row.prop(n.image, "filepath", text="Texture Path")
            row = box.row(align=True)
            row.prop(n.texture_properties, "embedded")
            if(n.texture_properties.embedded == False):
                continue
            row.prop(n.texture_properties, "format")
            row.prop(n.texture_properties, "usage")
            #box = box.box()
            box.label(text="Flags")
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


def draw_shader_value_params(layout, mat):
    value_param_box = layout.box()
    # only using selected nodes because if you use the node tree weird bug
    # where if you select one of the image nodes it swaps around the order that you edit them in...
    # I think this is because when you select something "mat.node_tree.nodes" is reordered for the selected to be in front.....
    # annoyying as hell
    #selected_nodes = []
    # for n in nodes:
    # if(n.select == True):
    # selected_nodes.append(n)
    nodes = mat.node_tree.nodes
    for n in nodes:  # LOOP SERERATE SO TEXTURES SHOW ABOVE VALUE PARAMS
        if(isinstance(n, bpy.types.ShaderNodeValue)):
            if(n.name[-1] == "x"):
                row = value_param_box.row()
                row.label(text=n.name[:-2])

                x = n
                y = mat.node_tree.nodes[n.name[:-1] + "y"]
                z = mat.node_tree.nodes[n.name[:-1] + "z"]
                w = mat.node_tree.nodes[n.name[:-1] + "w"]

                row.prop(x.outputs[0], "default_value", text="X:")
                row.prop(y.outputs[0], "default_value", text="Y:")
                row.prop(z.outputs[0], "default_value", text="Z:")
                row.prop(w.outputs[0], "default_value", text="W:")


def draw_shader(layout, mat):
    layout.label(text="Material Properties")
    box = layout.box()
    row = box.row()
    row.prop(mat.shader_properties, "renderbucket")
    row.prop(mat.shader_properties, "filename")
    row.prop(mat.shader_properties, "name")


class SOLLUMZ_UL_SHADER_MATERIALS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_SHADER_MATERIALS_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        name = shadermats[item.index].ui_name
        # If the object is selected
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=name, icon='SHADING_TEXTURE')
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=name, emboss=False, icon='SHADING_TEXTURE')


class SOLLUMZ_PT_LIGHT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_LIGHT_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        return context.light and context.active_object.sollum_type != SollumType.NONE

    def draw(self, context):
        layout = self.layout
        light = context.light
        row = layout.row()
        row.enabled = False
        row.prop(light.light_properties, "type")  # MAKE THIS AN ENUM?
        layout.prop(light.light_properties, "flags")
        layout.prop(light.light_properties, "bone_id")
        layout.prop(light.light_properties, "group_id")
        layout.prop(light.light_properties, "time_flags")
        layout.prop(light.light_properties, "falloff")
        layout.prop(light.light_properties, "falloff_exponent")
        layout.prop(light.light_properties, "culling_plane_normal")
        layout.prop(light.light_properties, "culling_plane_offset")
        layout.prop(light.light_properties, "unknown_45")
        layout.prop(light.light_properties, "unknown_46")
        layout.prop(light.light_properties, "volume_intensity")
        layout.prop(light.light_properties, "volume_size_scale")
        layout.prop(light.light_properties, "volume_outer_color")
        layout.prop(light.light_properties, "light_hash")
        layout.prop(light.light_properties, "volume_outer_intensity")
        layout.prop(light.light_properties, "corona_size")
        layout.prop(light.light_properties, "volume_outer_exponent")
        layout.prop(light.light_properties, "light_fade_distance")
        layout.prop(light.light_properties, "shadow_fade_distance")
        layout.prop(light.light_properties, "specular_fade_distance")
        layout.prop(light.light_properties, "volumetric_fade_distance")
        layout.prop(light.light_properties, "shadow_near_clip")
        layout.prop(light.light_properties, "corona_intensity")
        layout.prop(light.light_properties, "corona_z_bias")
        layout.prop(light.light_properties, "tangent")
        layout.prop(light.light_properties, "cone_inner_angle")
        layout.prop(light.light_properties, "cone_outer_angle")
        layout.prop(light.light_properties, "extent")
        layout.prop(light.light_properties, "projected_texture_hash")


class SOLLUMZ_PT_DRAWABLE_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Drawable Tools"
    bl_idname = "SOLLUMZ_PT_DRAWABLE_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 1

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="MESH_CUBE")

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

    def draw_header(self, context):
        self.layout.label(text="", icon="SHADING_RENDERED")

    def draw(self, context):
        layout = self.layout
        layout.template_list(
            SOLLUMZ_UL_SHADER_MATERIALS_LIST.bl_idname, "", context.scene, "shader_materials", context.scene, "shader_material_index"
        )
        layout.operator(SOLLUMZ_OT_create_shader_material.bl_idname)
        layout.operator(SOLLUMZ_OT_convert_to_shader_material.bl_idname)


class SOLLUMZ_PT_CREATE_DRAWABLE_PANEL(bpy.types.Panel):
    bl_label = "Create Drawable Objects"
    bl_idname = "SOLLUMZ_PT_CREATE_DRAWABLE_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_DRAWABLE_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        self.layout.label(text="", icon="CUBE")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(SOLLUMZ_OT_create_drawable.bl_idname)
        row.prop(context.scene, "use_mesh_name")
        row.prop(context.scene, "create_seperate_objects")
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_drawable_model.bl_idname)
        row.operator(SOLLUMZ_OT_create_geometry.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_drawable_dictionary.bl_idname)
        layout.separator()
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_light.bl_idname)
        row.prop(context.scene, 'create_light_type', text='')


class SOLLUMZ_UL_BONE_FLAGS(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname, index):
        custom_icon = 'FILE'

        if self.layout_type in {'DEFAULT', 'COMPACT'}:
            layout.prop(item, 'name', text='', icon=custom_icon,
                        emboss=False, translate=False)
        elif self.layout_type in {'GRID'}:
            layout.alignment = 'CENTER'
            layout.prop(item, 'name', text='', icon=custom_icon,
                        emboss=False, translate=False)


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

        layout.prop(bone, "name", text="Bone Name")
        layout.prop(bone.bone_properties, "tag", text="BoneTag")

        layout.label(text="Flags")
        layout.template_list("SOLLUMZ_UL_BONE_FLAGS", "Flags",
                             bone.bone_properties, "flags", bone.bone_properties, "ul_index")
        row = layout.row()
        row.operator('sollumz.bone_flags_new_item', text='New')
        row.operator('sollumz.bone_flags_delete_item', text='Delete')


class SOLLUMZ_MT_add_drawable(bpy.types.Menu):

    bl_label = "Drawable"
    bl_idname = "SOLLUMZ_MT_add_drawable"

    def draw(self, context):
        layout = self.layout
        layout.operator(SOLLUMZ_OT_create_drawable.bl_idname,
                        text=SOLLUMZ_UI_NAMES[SollumType.DRAWABLE])
        layout.operator(SOLLUMZ_OT_create_drawable_model.bl_idname,
                        text=SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_MODEL])
        layout.operator(SOLLUMZ_OT_create_geometry.bl_idname,
                        text=SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_GEOMETRY])


def DrawDrawableMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_add_drawable.bl_idname)


def register():
    bpy.types.SOLLUMZ_MT_sollumz.append(DrawDrawableMenu)


def unregister():
    bpy.types.SOLLUMZ_MT_sollumz.remove(DrawDrawableMenu)
