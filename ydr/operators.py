import bpy
import traceback
from ..tools.drawablehelper import *
from ..ydr.shader_materials import create_shader, shadermats
from ..sollumz_properties import DrawableType, SOLLUMZ_UI_NAMES
from ..sollumz_helper import SOLLUMZ_OT_base, is_sollum_type


class SOLLUMZ_OT_create_drawable(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz drawable"""
    bl_idname = "sollumz.createdrawable"
    bl_label = f"Create Drawable"
    bl_action = "Create a Drawable"

    def run(self, context):
        selected = context.selected_objects
        if len(selected) == 0:
            create_drawable()
            return True
        else:
            convert_selected_to_drawable(
                selected, context.scene.use_mesh_name, context.scene.create_seperate_objects)
            # self.messages.append(
            #    f"Succesfully converted {', '.join([obj.name for obj in context.selected_objects])} to a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]}.")
            self.message(
                f"Succesfully converted {', '.join([obj.name for obj in context.selected_objects])} to a {SOLLUMZ_UI_NAMES[DrawableType.DRAWABLE]}.")
            return True


class SOLLUMZ_OT_create_drawable_model(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz drawable model"""
    bl_idname = "sollumz.createdrawablemodel"
    bl_label = f"Create Drawable Model"
    bl_action = "Create a Drawable Model"

    def run(self, context):
        create_drawable(DrawableType.DRAWABLE_MODEL)
        return True


class SOLLUMZ_OT_create_drawable_dictionary(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz drawable dictionary"""
    bl_idname = "sollumz.createdrawabledictionary"
    bl_label = f"Create Drawable Dictionary"
    bl_action = "Create a Drawable Dictionary"

    def run(self, context):
        create_drawable(DrawableType.DRAWABLE_DICTIONARY)
        return True


class SOLLUMZ_OT_create_geometry(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz geometry"""
    bl_idname = "sollumz.creategeometry"
    bl_label = f"Create Drawable Geometry"
    bl_action = "Create a Drawable Geometry"

    def run(self, context):
        name = SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        obj.sollum_type = DrawableType.GEOMETRY
        bpy.context.collection.objects.link(obj)
        return True


class SOLLUMZ_OT_convert_to_shader_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Convert material to a sollumz shader material"""
    bl_idname = "sollumz.converttoshadermaterial"
    bl_label = "Convert Material To Shader Material"
    bl_action = "Convert a Material To a Shader Material"

    def run(self, context):

        for obj in context.selected_objects:

            if len(obj.data.materials) == 0:
                self.messages.append(
                    f"{obj.name} has no materials to convert.")

            for material in obj.data.materials:
                new_material = convert_material(material)
                if new_material != None:
                    for ms in obj.material_slots:
                        if(ms.material == material):
                            ms.material = new_material

        return True


class SOLLUMZ_OT_create_shader_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz shader material"""
    bl_idname = "sollumz.createshadermaterial"
    bl_label = "Create Shader Material"
    bl_action = "Create a Shader Material"

    def run(self, context):

        objs = bpy.context.selected_objects
        if(len(objs) == 0):
            self.message(
                f"Please select a {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]} to add a shader material to.")
            return False

        for obj in objs:
            if is_sollum_type(obj, DrawableType.GEOMETRY):
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

        return True


class SOLLUMZ_OT_BONE_FLAGS_NewItem(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_new_item"
    bl_label = "Add a new item"
    bl_action = "Add a Bone Flag"

    def run(self, context):
        bone = context.active_pose_bone.bone
        bone.bone_properties.flags.add()
        self.message(f"Added bone flag to bone: {bone.name}")
        return True


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
        self.message(f"Deleted bone flag from: {bone.name}")
        return True
