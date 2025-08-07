import traceback
import bpy
from mathutils import Vector, Color
from ...cwxml.light_preset import LightPreset
from ...sollumz_helper import SOLLUMZ_OT_base
from ...sollumz_properties import SOLLUMZ_UI_NAMES, LightType, SollumType
from ...sollumz_operators import SelectTimeFlagsRange, ClearTimeFlags
from ...tools.blenderhelper import create_blender_object, tag_redraw
from ..properties import LightProperties, get_light_presets_path, load_light_presets, light_presets


class SOLLUMZ_OT_create_light(SOLLUMZ_OT_base, bpy.types.Operator):
    """Creates a light. Applies the selected preset to the new light."""
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

        # Apply light preset
        bpy.ops.object.select_all(action="DESELECT")  # Deselect everything to avoid applying the preset to other lights
        light_obj.select_set(True)
        bpy.ops.sollumz.load_light_preset()


class SOLLUMZ_OT_save_light_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Save a light preset of the selected light"""
    bl_idname = "sollumz.save_light_preset"
    bl_label = "Save Light Preset"
    bl_action = f"{bl_label}"

    name: bpy.props.StringProperty(name="Name")

    @classmethod
    def poll(cls, context):
        selected_light_obj = context.active_object
        return (selected_light_obj is not None and
                selected_light_obj.type == "LIGHT" and
                selected_light_obj.sollum_type == SollumType.LIGHT)

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def run(self, context):
        self.name = self.name.strip()
        if len(self.name) == 0:
            self.warning("Please specify a name for the new light preset.")
            return False

        selected_light_obj = context.active_object
        if not selected_light_obj or selected_light_obj.type != "LIGHT":
            self.warning("No light selected!")
            return False

        if selected_light_obj.sollum_type != SollumType.LIGHT:
            self.warning(f"Selected object must be a Sollumz {SOLLUMZ_UI_NAMES[SollumType.LIGHT]}!")
            return False

        load_light_presets()

        for preset in light_presets.presets:
            if preset.name == self.name:
                self.warning(
                    "A preset with that name already exists! If you wish to overwrite this preset, delete the original.")
                return False

        light: bpy.types.Light = selected_light_obj.data
        light_props: LightProperties = light.light_properties

        light_preset = LightPreset()
        light_preset.name = self.name
        # Blender properties
        light_preset.color = Vector(light.color)
        light_preset.energy = light.energy
        light_preset.cutoff_distance = light.cutoff_distance
        light_preset.shadow_soft_size = light.shadow_soft_size
        light_preset.volume_factor = light.volume_factor
        light_preset.shadow_buffer_clip_start = light.shadow_buffer_clip_start
        if light.type == "SPOT":
            light_preset.spot_size = light.spot_size
            light_preset.spot_blend = light.spot_blend
        # RAGE properties
        light_preset.time_flags = light.time_flags.total
        light_preset.flags = light.light_flags.total
        light_preset.projected_texture_hash = light_props.projected_texture_hash
        light_preset.flashiness = light_props.flashiness
        light_preset.volume_size_scale = light_props.volume_size_scale
        light_preset.volume_outer_color = Vector(light_props.volume_outer_color)
        light_preset.volume_outer_intensity = light_props.volume_outer_intensity
        light_preset.volume_outer_exponent = light_props.volume_outer_exponent
        light_preset.light_fade_distance = light_props.light_fade_distance
        light_preset.shadow_fade_distance = light_props.shadow_fade_distance
        light_preset.specular_fade_distance = light_props.specular_fade_distance
        light_preset.volumetric_fade_distance = light_props.volumetric_fade_distance
        light_preset.culling_plane_normal = Vector(light_props.culling_plane_normal)
        light_preset.culling_plane_offset = light_props.culling_plane_offset
        light_preset.corona_size = light_props.corona_size
        light_preset.corona_intensity = light_props.corona_intensity
        light_preset.corona_z_bias = light_props.corona_z_bias
        light_preset.shadow_blur = light_props.shadow_blur
        light_preset.extent = Vector(light_props.extent)

        light_presets.presets.append(light_preset)

        filepath = get_light_presets_path()
        light_presets.write_xml(filepath)
        load_light_presets()

        tag_redraw(context, space_type="VIEW_3D", region_type="UI")
        return True


class SOLLUMZ_OT_load_light_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Apply a light preset to the selected light(s)"""
    bl_idname = "sollumz.load_light_preset"
    bl_label = "Apply Light Preset to Selected"
    bl_context = "object"
    bl_options = {"REGISTER", "UNDO"}
    bl_action = f"{bl_label}"

    def run(self, context):
        index = context.window_manager.sz_light_preset_index
        selected_lights = []
        for obj in bpy.context.selected_objects:
            if obj.type == 'LIGHT':
                selected_lights.append(obj)

        if len(selected_lights) == 0:
            self.warning("No lights selected!")
            return False

        load_light_presets()
        preset: LightPreset = light_presets.presets[index]

        for light_obj in selected_lights:
            light: bpy.types.Light = light_obj.data
            light_props: LightProperties = light.light_properties

            light.color = Color(preset.color)
            light.energy = preset.energy
            light.cutoff_distance = preset.cutoff_distance
            light.shadow_soft_size = preset.shadow_soft_size
            light.volume_factor = preset.volume_factor
            light.shadow_buffer_clip_start = preset.shadow_buffer_clip_start
            if light.type == 'SPOT':
                light.spot_size = preset.spot_size
                light.spot_blend = preset.spot_blend
            light.time_flags.total = str(preset.time_flags)
            light.light_flags.total = str(preset.flags)
            light_props.projected_texture_hash = preset.projected_texture_hash
            light_props.flashiness = preset.flashiness
            light_props.volume_size_scale = preset.volume_size_scale
            light_props.volume_outer_color = Color(preset.volume_outer_color)
            light_props.volume_outer_intensity = preset.volume_outer_intensity
            light_props.volume_outer_exponent = preset.volume_outer_exponent
            light_props.light_fade_distance = preset.light_fade_distance
            light_props.shadow_fade_distance = preset.shadow_fade_distance
            light_props.specular_fade_distance = preset.specular_fade_distance
            light_props.volumetric_fade_distance = preset.volumetric_fade_distance
            light_props.culling_plane_normal = preset.culling_plane_normal
            light_props.culling_plane_offset = preset.culling_plane_offset
            light_props.corona_size = preset.corona_size
            light_props.corona_intensity = preset.corona_intensity
            light_props.corona_z_bias = preset.corona_z_bias
            light_props.shadow_blur = preset.shadow_blur
            light_props.extent = preset.extent

        self.message(f"Applied preset '{preset.name}' to {len(selected_lights)} light(s).")
        return True


class SOLLUMZ_OT_delete_light_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete the selected light preset"""
    bl_idname = "sollumz.delete_light_preset"
    bl_label = "Delete Light Preset"
    bl_action = f"{bl_label}"

    preset_blacklist = [
        "Default",
        "Point: Wall Light 1",
        "Spot: Wall Light 1",
        "Point: Wall Light 2",
        "Spot: Wall Light 2",
        "Spot: Streetlight 1"
    ]

    def run(self, context):
        index = context.window_manager.sz_light_preset_index
        load_light_presets()
        filepath = get_light_presets_path()

        try:
            preset = light_presets.presets[index]
            if preset.name in self.preset_blacklist:
                self.warning("Cannot delete a default preset!")
                return False

            light_presets.presets.remove(preset)

            try:
                light_presets.write_xml(filepath)
                load_light_presets()

                return True
            except:
                self.error(f"Error during deletion of light preset: {traceback.format_exc()}")
                return False

        except IndexError:
            self.warning(
                f"Light preset does not exist! Ensure the preset file is present in the '{filepath}' directory.")
            return False


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
