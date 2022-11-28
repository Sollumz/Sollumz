import bpy
import os

from mathutils import Vector
from ..sollumz_helper import SOLLUMZ_OT_base, set_object_collection
from ..tools.ymaphelper import add_occluder_material, create_ymap, create_ymap_group
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType


class SOLLUMZ_OT_create_ymap(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz YMAP object"""
    bl_idname = "sollumz.createymap"
    bl_label = f"Create YMAP"
    bl_description = "Create a YMAP"

    def run(self, context):
        ymap_obj = create_ymap()
        context.view_layer.objects.active = bpy.data.objects[ymap_obj.name]
        ymap_obj.select_set(True)
        return True


class SOLLUMZ_OT_create_entity_group(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz 'Entities' group object"""
    bl_idname = "sollumz.create_entity_group"
    bl_label = f"Entities"
    bl_description = "Create 'Entities' group.\n\nOnly 1 per YMAP maximum.\nYou can't create 'Entities' group if the current YMAP already includes occlusions"

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        existing_groups = []
        # Do not let user create Entities Group if there is already one, and if there is any kind of Occlusion Group
        for child in aobj.children:
            existing_groups.append(child.name)
        for group in existing_groups:
            if group == "Entities" or group == "Box Occluders" or group == "Model Occluders":
                return False
        return True

    def run(self, context):
        ymap_obj = context.active_object
        create_ymap_group(sollum_type=SollumType.YMAP_ENTITY_GROUP, selected_ymap=ymap_obj, empty_name='Entities')
        return True


class SOLLUMZ_OT_create_model_occluder_group(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz 'Model Occluders' group object"""
    bl_idname = "sollumz.create_model_occluder_group"
    bl_label = f"Model Occluders"
    bl_description = "Create 'Model Occluders' group.\n\nOnly 1 per YMAP maximum.\nYou can't create 'Model Occluders' group if the current YMAP already includes an 'Entities' group"

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        existing_groups = []
        # Do not let user create Model Occluders Group if there is already one, and if there is already Entities Group
        for child in aobj.children:
            existing_groups.append(child.name)
        for group in existing_groups:
            if group == "Entities" or group == "Model Occluders":
                return False
        return True

    def run(self, context):
        ymap_obj = context.active_object
        create_ymap_group(sollum_type=SollumType.YMAP_MODEL_OCCLUDER_GROUP, selected_ymap=ymap_obj, empty_name='Model Occluders')
        return True


class SOLLUMZ_OT_create_box_occluder_group(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz 'Box Occluders' group object"""
    bl_idname = "sollumz.create_box_occluder_group"
    bl_label = f"Box Occluders"
    bl_description = "Create 'Box Occluders' group.\n\nOnly 1 per YMAP maximum.\nYou can't create 'Box Occluders' group if the current YMAP already includes an 'Entities' group"

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        existing_groups = []
        # Do not let user create Box Occluders Group if there is already one, and if there is already Entities Group
        for child in aobj.children:
            existing_groups.append(child.name)
        for group in existing_groups:
            if group == "Entities" or group == "Box Occluders":
                return False
        return True

    def run(self, context):
        ymap_obj = context.active_object
        create_ymap_group(sollum_type=SollumType.YMAP_BOX_OCCLUDER_GROUP, selected_ymap=ymap_obj, empty_name='Box Occluders')
        return True


class SOLLUMZ_OT_create_car_generator_group(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz 'Car Generators' group object"""
    bl_idname = "sollumz.create_car_generator_group"
    bl_label = f"Car Generators"
    bl_description = "Create 'Car Generators' group.\n\nOnly 1 per YMAP maximum"

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        existing_groups = []
        for child in aobj.children:
            existing_groups.append(child.name)
        for group in existing_groups:
            if group == "Car Generators":
                return False
        return True

    def run(self, context):
        ymap_obj = context.active_object
        create_ymap_group(sollum_type=SollumType.YMAP_CAR_GENERATOR_GROUP, selected_ymap=ymap_obj, empty_name='Car Generators')
        return True


class SOLLUMZ_OT_create_box_occluder(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz 'Box Occluder' object"""
    bl_idname = "sollumz.create_box_occluder"
    bl_label = "Create Box Occluder"
    bl_description = "Create a 'Box Occluder' object"

    def run(self, context):
        group_obj = context.active_object
        bpy.ops.mesh.primitive_cube_add(size=2)
        box_obj = bpy.context.view_layer.objects.active
        box_obj.sollum_type = SollumType.YMAP_BOX_OCCLUDER
        box_obj.name = "Box"
        box_obj.active_material = add_occluder_material(SollumType.YMAP_BOX_OCCLUDER)
        box_obj.parent = group_obj

        return True


class SOLLUMZ_OT_create_model_occluder(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz 'Model Occluder' object"""
    bl_idname = "sollumz.create_model_occluder"
    bl_label = "Create Model Occluder"
    bl_description = "Create a 'Model Occluder' object"

    def run(self, context):
        group_obj = context.active_object
        bpy.ops.mesh.primitive_cube_add(size=1)
        model_obj = bpy.context.view_layer.objects.active
        model_obj.name = "Model"
        model_obj.sollum_type = SollumType.YMAP_MODEL_OCCLUDER
        model_obj.ymap_properties.flags = 0
        model_obj.active_material = add_occluder_material(SollumType.YMAP_MODEL_OCCLUDER)
        set_object_collection(model_obj)
        bpy.context.view_layer.objects.active = model_obj
        model_obj.parent = group_obj

        return True


class SOLLUMZ_OT_create_car_generator(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz 'Car Generator' object"""
    bl_idname = "sollumz.create_car_generator"
    bl_label = "Create Car Generator"
    bl_description = "Create a 'Car Generator' object"

    def run(self, context):
        group_obj = context.active_object
        file_loc = os.path.join(os.path.dirname(__file__), "car_model.obj")
        bpy.ops.import_scene.obj(filepath=file_loc)
        cargen_obj = bpy.context.selected_objects[0]
        cargen_obj.name = "Car Generator"
        cargen_obj.sollum_type = SollumType.YMAP_CAR_GENERATOR
        cargen_obj.ymap_cargen_properties.orient_x = 0.0
        cargen_obj.ymap_cargen_properties.orient_y = 0.0
        cargen_obj.ymap_cargen_properties.perpendicular_length = 2.3
        cargen_obj.ymap_cargen_properties.car_model = ""
        cargen_obj.ymap_cargen_properties.flags = 0
        cargen_obj.ymap_cargen_properties.body_color_remap_1 = -1
        cargen_obj.ymap_cargen_properties.body_color_remap_2 = -1
        cargen_obj.ymap_cargen_properties.body_color_remap_3 = -1
        cargen_obj.ymap_cargen_properties.body_color_remap_4 = -1
        cargen_obj.ymap_cargen_properties.pop_group = ""
        cargen_obj.ymap_cargen_properties.livery = -1
        bpy.context.view_layer.objects.active = cargen_obj
        cargen_obj.parent = group_obj

        return True