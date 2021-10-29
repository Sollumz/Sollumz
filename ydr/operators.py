import bpy
import traceback
from Sollumz.tools.drawablehelper import *
from Sollumz.ydr.shader_materials import create_shader, shadermats
from Sollumz.sollumz_properties import DrawableType, MaterialType, SOLLUMZ_UI_NAMES
from Sollumz.sollumz_helper import SOLLUMZ_OT_base


class SOLLUMZ_OT_create_drawable(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz drawable"""
    bl_idname = "sollumz.createdrawable"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]}"
    bl_showtime = False
    bl_action = "create a drawable"

    def run(self, context):
        selected = context.selected_objects
        if len(selected) == 0:
            try:
                create_drawable()
                self.messages.append(
                    f"Created a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]}.")
                return True
            except:
                self.messages.append(
                    f"Failed to create a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]} \n {traceback.format_exc()}")
                return False
        else:
            try:
                convert_selected_to_drawable(
                    selected, context.scene.use_mesh_name, context.scene.create_seperate_objects)
                self.messages.append(
                    f"Succesfully converted {', '.join([obj.name for obj in context.selected_objects])} to a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]}.")
                return True
            except:
                self.messages.append(
                    f"Failed to create a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]} \n {traceback.format_exc()}")
                return False


class SOLLUMZ_OT_create_drawable_model(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz drawable model"""
    bl_idname = "sollumz.createdrawablemodel"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE_MODEL]}"
    bl_showtime = False
    bl_action = "create a drawable model"

    def run(self, context):

        try:
            create_drawable(DrawableType.DRAWABLE_MODEL)
            self.messages.append(
                f"Created a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE_MODEL]}.")
            return True
        except:
            self.messages.append(
                f"Failed to create a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE_MODEL]} \n {traceback.format_exc()}")
            return False


class SOLLUMZ_OT_create_geometry(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz geometry"""
    bl_idname = "sollumz.creategeometry"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]}"
    bl_showtime = False
    bl_action = "create a drawable geometry"

    def run(self, context):
        try:
            create_drawable(DrawableType.GEOMETRY)
            self.messages.append(
                f"Created a {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]}.")
            return True
        except:
            self.messages.append(
                f"Failed to create a {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]} \n {traceback.format_exc()}")
            return False


class SOLLUMZ_OT_convert_to_shader_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Convert material to a sollumz shader material"""
    bl_idname = "sollumz.converttoshadermaterial"
    bl_label = "Convert Material To Shader Material"
    bl_showtime = False
    bl_action = "convert a material to a shader material"

    def convert_material(self, material):
        try:
            bsdf = material.node_tree.nodes["Principled BSDF"]

            if(bsdf == None):
                self.fail(material.name,
                          "Material must have a Principled BSDF node.")

            diffuse_node = None
            diffuse_input = bsdf.inputs["Base Color"]
            if diffuse_input.is_linked:
                diffuse_node = diffuse_input.links[0].from_node

            if not isinstance(diffuse_node, bpy.types.ShaderNodeTexImage):
                self.fail(material.name, "Material has no diffuse image.")

            specular_node = None
            specular_input = bsdf.inputs["Specular"]
            if specular_input.is_linked:
                specular_node = specular_input.links[0].from_node

            if not isinstance(diffuse_node, bpy.types.ShaderNodeTexImage):
                specular_node = None

            normal_node = None
            normal_input = bsdf.inputs["Normal"]
            if len(normal_input.links) > 0:
                normal_map_node = normal_input.links[0].from_node
                normal_map_input = normal_map_node.inputs["Color"]
                if len(normal_map_input.links) > 0:
                    normal_node = normal_map_input.links[0].from_node

            if not isinstance(normal_node, bpy.types.ShaderNodeTexImage):
                normal_node = None

            shader_name = "default"

            if normal_node != None and specular_node != None:
                shader_name = "normal_spec"
            elif normal_node != None and specular_node == None:
                shader_name = "normal"
            elif normal_node == None and specular_node != None:
                shader_name = "spec"

            new_material = create_shader(shader_name)
            # new_mat.name = mat.name

            bsdf = new_material.node_tree.nodes["Principled BSDF"]

            new_diffuse_node = None
            diffuse_input = bsdf.inputs["Base Color"]
            if diffuse_input.is_linked:
                new_diffuse_node = diffuse_input.links[0].from_node

            if(diffuse_node != None):
                new_diffuse_node.image = diffuse_node.image

            new_specular_node = None
            specular_input = bsdf.inputs["Specular"]
            if specular_input.is_linked:
                new_specular_node = specular_input.links[0].from_node

            if(specular_node != None):
                new_specular_node.image = specular_node.image

            new_normal_node = None
            normal_input = bsdf.inputs["Normal"]
            if len(normal_input.links) > 0:
                normal_map_node = normal_input.links[0].from_node
                normal_map_input = normal_map_node.inputs["Color"]
                if len(normal_map_input.links) > 0:
                    new_normal_node = normal_map_input.links[0].from_node

            if(normal_node != None):
                new_normal_node.image = normal_node.image

            self.messages.append(
                f"Material: {material.name} was successfully converted to a sollumz material.")

            return new_material

        except:
            self.messages.append(
                f"{material.name} cannot be converted because : \n {traceback.format_exc()}")

    def run(self, context):

        for obj in context.selected_objects:

            if len(obj.data.materials) == 0:
                self.messages.append(
                    f"{obj.name} has no materials to convert.")
                return False

            for material in obj.data.materials:
                new_material = self.convert_material(material)
                for ms in obj.material_slots:
                    if(ms.material == material):
                        ms.material = new_material

        return True


class SOLLUMZ_OT_create_shader_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz shader material"""
    bl_idname = "sollumz.createshadermaterial"
    bl_label = "Create Shader Material"
    bl_showtime = False
    bl_action = "create a shader material"

    def run(self, context):

        objs = bpy.context.selected_objects
        if(len(objs) == 0):
            self.messages.append(
                f"Please select a {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]} to add a shader material to.")
            return False

        for obj in objs:
            if self.is_sollum_type(obj, DrawableType.GEOMETRY):
                try:
                    shader = shadermats[context.scene.shader_material_index].value
                    mat = create_shader(shader)
                    obj.data.materials.append(mat)
                    self.messages.append(
                        f"Added a {shader} shader to {obj.name}.")
                except:
                    self.messages.append(
                        f"Failed adding {shader} to {obj.name} because : \n {traceback.format_exc()}")
            else:
                self.messages.append(
                    f"Object: {obj.name} is not a {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]}, please select a valid {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]} to add a shader material to.")

        return True


class SOLLUMZ_OT_BONE_FLAGS_NewItem(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_new_item"
    bl_label = "Add a new item"
    bl_showtime = False
    bl_action = "add a bone flag"

    def run(self, context):
        bone = context.active_pose_bone.bone
        try:
            bone.bone_properties.flags.add()
            self.messages.append(f"Added a bone flag to {bone}.")
            return True
        except:
            self.messages.append(
                f"Failure adding a bone flag to {bone} because : \n {traceback.format_exc()}")
            return False


class SOLLUMZ_OT_BONE_FLAGS_DeleteItem(bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_delete_item"
    bl_label = "Deletes an item"
    bl_showtime = False
    bl_action = "delete a bone flag"

    @ classmethod
    def poll(cls, context):
        return context.active_pose_bone.bone.bone_properties.flags

    def execute(self, context):
        bone = context.active_pose_bone.bone
        try:
            list = bone.bone_properties.flags
            index = bone.bone_properties.ul_index
            list.remove(index)
            bone.bone_properties.ul_index = min(
                max(0, index - 1), len(list) - 1)
            self.messages.append(
                f"Deleted a bone flag from {bone}.")
            return True
        except:
            self.messages.append(
                f"Failure deleting a bone flag from {bone} because : \n {traceback.format_exc()}")
            return False
