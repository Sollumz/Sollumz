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
    bl_action = "Create a Drawable"

    def run(self, context):
        selected = context.selected_objects
        if len(selected) == 0:
            create_drawable()
            return self.success()
        else:
            convert_selected_to_drawable(
                selected, context.scene.use_mesh_name, context.scene.create_seperate_objects)
            # self.messages.append(
            #    f"Succesfully converted {', '.join([obj.name for obj in context.selected_objects])} to a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]}.")
            return self.success(f"Succesfully converted {', '.join([obj.name for obj in context.selected_objects])} to a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]}.", True, False)


class SOLLUMZ_OT_create_drawable_model(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz drawable model"""
    bl_idname = "sollumz.createdrawablemodel"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE_MODEL]}"
    bl_action = "Create a Drawable Model"

    def run(self, context):
        create_drawable(DrawableType.DRAWABLE_MODEL)
        return self.success()


class SOLLUMZ_OT_create_geometry(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz geometry"""
    bl_idname = "sollumz.creategeometry"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]}"
    bl_action = "Create a Drawable Geometry"

    def run(self, context):
        create_drawable(DrawableType.GEOMETRY)
        return self.success()


class SOLLUMZ_OT_convert_to_shader_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Convert material to a sollumz shader material"""
    bl_idname = "sollumz.converttoshadermaterial"
    bl_label = "Convert Material To Shader Material"
    bl_action = "Convert a Material To a Shader Material"

    def convert_material(self, material):
        try:
            bsdf = material.node_tree.nodes["Principled BSDF"]

            if(bsdf == None):
                self.messages.append(
                    f"{material.name} Material must have a Principled BSDF node.")
                return None

            diffuse_node = None
            diffuse_input = bsdf.inputs["Base Color"]
            if diffuse_input.is_linked:
                diffuse_node = diffuse_input.links[0].from_node

            if not isinstance(diffuse_node, bpy.types.ShaderNodeTexImage):
                self.messages.append(
                    f"{material.name} Material has no diffuse image.")
                return None

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
                f"{material.name} was successfully converted to a sollumz material.")

            return new_material

        except:
            self.messages.append(
                f"{material.name} cannot be converted because : \n {traceback.format_exc()}")
            return None

    def run(self, context):

        for obj in context.selected_objects:

            if len(obj.data.materials) == 0:
                self.messages.append(
                    f"{obj.name} has no materials to convert.")

            for material in obj.data.materials:
                new_material = self.convert_material(material)
                for ms in obj.material_slots:
                    if(ms.material == material):
                        ms.material = new_material

        return self.success(None, False)


class SOLLUMZ_OT_create_shader_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz shader material"""
    bl_idname = "sollumz.createshadermaterial"
    bl_label = "Create Shader Material"
    bl_action = "Create a Shader Material"

    def run(self, context):

        objs = bpy.context.selected_objects
        if(len(objs) == 0):
            return self.fail(f"Please select a {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]} to add a shader material to.")

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
                    f"{obj.name} is not a {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]}, please select a valid {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]} to add a shader material to.")

        return self.success(None, False)


class SOLLUMZ_OT_BONE_FLAGS_NewItem(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_new_item"
    bl_label = "Add a new item"
    bl_action = "Add a Bone Flag"

    def run(self, context):
        bone = context.active_pose_bone.bone
        bone.bone_properties.flags.add()
        return self.success(f"Added a Bone Flag To {bone}.")


class SOLLUMZ_OT_BONE_FLAGS_DeleteItem(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_delete_item"
    bl_label = "Deletes an item"
    bl_action = "Delete a Bone Flag"

    @ classmethod
    def poll(cls, context):
        if context.active_pose_bone:
            return context.active_pose_bone.bone.bone_properties.flags

    def run(self, context):
        bone = context.active_pose_bone.bone
        list = bone.bone_properties.flags
        index = bone.bone_properties.ul_index
        list.remove(index)
        bone.bone_properties.ul_index = min(
            max(0, index - 1), len(list) - 1)
        return self.success(f"Deleted a bone flag from {bone}.")
