import bpy
from ...sollumz_helper import SOLLUMZ_OT_base
from ...sollumz_properties import SOLLUMZ_UI_NAMES, LightType, SollumType
from ...sollumz_operators import SelectTimeFlagsRange, ClearTimeFlags
from ...tools.blenderhelper import create_blender_object
from ...shared.presets import store as preset_store
from ..gta5.presets.light import LIGHT_PRESET_CATEGORY


class SOLLUMZ_OT_create_light(SOLLUMZ_OT_base, bpy.types.Operator):
    """Creates a light. Applies the 'Default' preset if available."""
    bl_idname = "sollumz.create_light"
    bl_label = "Create Light"
    bl_action = bl_label

    def run(self, context):
        scene = context.scene
        cursor_loc = scene.cursor.location
        light_type = scene.create_light_type
        active_obj = context.active_object
        blender_light_type = "POINT"
        if light_type == LightType.SPOT:
            blender_light_type = "SPOT"

        light_data = bpy.data.lights.new(name=SOLLUMZ_UI_NAMES[light_type], type=blender_light_type)
        light_data.sollum_type = light_type
        light_obj = create_blender_object(SollumType.LIGHT, SOLLUMZ_UI_NAMES[light_type], light_data)

        if active_obj and active_obj.sollum_type in [SollumType.DRAWABLE_MODEL, SollumType.DRAWABLE]:
            light_obj.parent = active_obj.parent if active_obj.sollum_type == SollumType.DRAWABLE_MODEL else active_obj
            light_obj.matrix_world.translation = cursor_loc
        else:
            light_obj.location = cursor_loc

        # Seed with the 'Default' light preset if it's available (bundled or user-saved).
        preset = preset_store.find_preset(LIGHT_PRESET_CATEGORY, "Default")
        if preset is not None:
            LIGHT_PRESET_CATEGORY.apply(light_data, preset.get("data", {}))
        return True


class SOLLUMZ_OT_LIGHT_TIME_FLAGS_select_range(SelectTimeFlagsRange, bpy.types.Operator):
    bl_idname = "sollumz.light_time_flags_select_range"

    @classmethod
    def poll(cls, context):
        return getattr(context, "light", None) and context.active_object.sollum_type == SollumType.LIGHT

    def get_flags(self, context):
        light = context.light
        return light.time_flags


class SOLLUMZ_OT_LIGHT_TIME_FLAGS_clear(ClearTimeFlags, bpy.types.Operator):
    bl_idname = "sollumz.light_time_flags_clear"

    @classmethod
    def poll(cls, context):
        return getattr(context, "light", None) and context.active_object.sollum_type == SollumType.LIGHT

    def get_flags(self, context):
        light = context.light
        return light.time_flags
