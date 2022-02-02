from ..sollumz_helper import SOLLUMZ_OT_base
from ..sollumz_properties import SOLLUMZ_UI_NAMES, LightType, SollumType, TimeFlags
from ..sollumz_operators import SelectTimeFlagsRange, ClearTimeFlags
from ..ydr.shader_materials import create_shader, create_tinted_shader_graph, shadermats
from ..tools.drawablehelper import *
from ..resources.shader import ShaderManager
import traceback
import bpy


class SOLLUMZ_OT_create_drawable(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz drawable of the selected type."""
    bl_idname = "sollumz.createdrawable"
    bl_label = f"Create Drawable"
    bl_action = "Create a Drawable"
    bl_update_view = True

    def run(self, context):
        aobj = context.active_object
        selected = context.selected_objects
        drawable_type = context.scene.create_drawable_type
        if drawable_type == SollumType.DRAWABLE and len(selected) > 0:
            convert_selected_to_drawable(
                selected, context.scene.use_mesh_name, context.scene.create_seperate_objects)
            self.message(
                f"Succesfully converted {', '.join([obj.name for obj in context.selected_objects])} to a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE]}.")
            return True
        else:
            obj = create_drawable(drawable_type)
            if aobj:
                obj.parent = aobj
            return True


class SOLLUMZ_OT_create_light(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.create_light"
    bl_label = "Create Light"
    bl_action = bl_label

    def run(self, context):
        light_type = context.scene.create_light_type
        blender_light_type = 'POINT'
        if light_type == LightType.SPOT:
            blender_light_type = 'SPOT'

        light_data = bpy.data.lights.new(
            name=SOLLUMZ_UI_NAMES[light_type], type=blender_light_type)
        light_data.light_properties.type = light_type
        obj = bpy.data.objects.new(
            name=SOLLUMZ_UI_NAMES[light_type], object_data=light_data)
        obj.sollum_type = SollumType.LIGHT
        bpy.context.collection.objects.link(obj)


class SOLLUMZ_OT_auto_convert_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Convert material to a sollumz shader material"""
    bl_idname = "sollumz.autoconvertmaterial"
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


class SOLLUMZ_OT_convert_material_to_selected(SOLLUMZ_OT_base, bpy.types.Operator):
    """Convert objects material to the selected sollumz shader"""
    bl_idname = "sollumz.convertmaterialtoselected"
    bl_label = "Convert Material To Selected Sollumz Shader"
    bl_action = "Convert a Material To Selected Sollumz Shader"

    def run(self, context):
        shader = shadermats[context.scene.shader_material_index].value
        for obj in context.selected_objects:
            if len(obj.data.materials) == 0:
                self.messages.append(
                    f"{obj.name} has no materials to convert.")

            for material in obj.data.materials:
                new_material = convert_material_to_selected(material, shader)
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

    def create_material(self, context, obj, shader):
        mat = create_shader(shader)
        obj.data.materials.append(mat)
        if mat.shader_properties.filename in ShaderManager.tinted_shaders():
            create_tinted_shader_graph(obj)

        for n in mat.node_tree.nodes:
            if isinstance(n, bpy.types.ShaderNodeTexImage):
                texture = bpy.data.images.new(
                    name="Texture", width=512, height=512)
                n.image = texture

    def run(self, context):

        objs = bpy.context.selected_objects
        if(len(objs) == 0):
            self.warning(
                f"Please select a object to add a shader material to.")
            return False

        for obj in objs:
            shader = shadermats[context.scene.shader_material_index].value
            try:
                self.create_material(context, obj, shader)
                self.message(f"Added a {shader} shader to {obj.name}.")
            except:
                self.message(
                    f"Failed adding {shader} to {obj.name} because : \n {traceback.format_exc()}")

        return True


class SOLLUMZ_OT_set_all_textures_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Sets all textures to embedded on the selected objects active material"""
    bl_idname = "sollumz.setallembedded"
    bl_label = "Set all Textures Embedded"
    bl_action = "Set all Textures Embedded"

    def set_textures_embedded(self, obj):
        mat = obj.active_material
        if mat == None:
            self.message(f"No active material on {obj.name} will be skipped")
            return

        if mat.sollum_type == MaterialType.SHADER:
            for node in mat.node_tree.nodes:
                if(isinstance(node, bpy.types.ShaderNodeTexImage)):
                    node.texture_properties.embedded = True
            self.message(
                f"Set {obj.name}s material {mat.name} textures to embedded.")
        else:
            self.message(
                f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = bpy.context.selected_objects
        if(len(objs) == 0):
            self.warning(
                f"Please select objects to set all textures embedded.")
            return False

        for obj in objs:
            self.set_textures_embedded(obj)

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


class SOLLUMZ_OT_LIGHT_TIME_FLAGS_select_range(SelectTimeFlagsRange, bpy.types.Operator):
    bl_idname = "sollumz.light_time_flags_select_range"

    @classmethod
    def poll(cls, context):
        return context.light and context.active_object.sollum_type == SollumType.LIGHT

    def get_flags(self, context):
        light = context.light
        return light.time_flags


class SOLLUMZ_OT_LIGHT_TIME_FLAGS_clear(ClearTimeFlags, bpy.types.Operator):
    bl_idname = "sollumz.light_time_flags_clear"

    @classmethod
    def poll(cls, context):
        return context.light and context.active_object.sollum_type == SollumType.LIGHT

    def get_flags(self, context):
        light = context.light
        return light.time_flags
