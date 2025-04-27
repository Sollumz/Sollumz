import traceback
import bpy
from bpy.props import (
    IntProperty,
    BoolProperty,
)
from mathutils import Vector, Color
from bpy.types import Context
from ..cwxml.light_preset import LightPreset
from ..cwxml.shader_preset import ShaderPreset, ShaderPresetParam
from ..lods import LODLevels
from ..sollumz_helper import SOLLUMZ_OT_base, find_sollumz_parent
from ..sollumz_properties import SOLLUMZ_UI_NAMES, LODLevel, LightType, SollumType, MaterialType
from ..sollumz_operators import SelectTimeFlagsRange, ClearTimeFlags
from ..ydr.shader_materials import create_shader, create_tinted_shader_graph, is_tint_material, shadermats
from ..tools.drawablehelper import MaterialConverter, set_recommended_bone_properties, convert_obj_to_drawable, convert_obj_to_model, convert_objs_to_single_drawable, center_drawable_to_models
from ..tools.boundhelper import convert_obj_to_composite, convert_objs_to_single_composite
from ..tools.blenderhelper import add_armature_modifier, add_child_of_bone_constraint, create_blender_object, create_empty_object, duplicate_object, get_child_of_constraint, set_child_of_constraint_space, tag_redraw
from ..sollumz_helper import get_sollumz_materials
from .properties import DrawableShaderOrder, LightProperties, get_light_presets_path, load_light_presets, light_presets, get_shader_presets_path, load_shader_presets, shader_presets
from ..tools.meshhelper import (
    mesh_add_missing_uv_maps,
    mesh_add_missing_color_attrs,
    mesh_rename_uv_maps_by_order,
    mesh_rename_color_attrs_by_order,
)
from ..shared.shader_nodes import SzShaderNodeParameter
from ..cwxml.shader import ShaderParameterFloatVectorDef, ShaderParameterTextureDef, ShaderManager


class SOLLUMZ_OT_create_drawable(bpy.types.Operator):
    """Create a Drawable empty"""
    bl_idname = "sollumz.createdrawable"
    bl_label = "Create Drawable"

    def execute(self, context):
        selected = context.selected_objects

        if selected:
            parent = selected[0]
        else:
            parent = None

        drawable_obj = create_empty_object(SollumType.DRAWABLE)
        drawable_obj.parent = parent

        return {"FINISHED"}


class SOLLUMZ_OT_create_drawable_dict(bpy.types.Operator):
    """Create a Drawable Dictionary empty"""
    bl_idname = "sollumz.createdrawabledict"
    bl_label = "Create Drawable Dictionary"

    def execute(self, context):
        selected = context.selected_objects

        if selected:
            parent = selected[0]
        else:
            parent = None

        ydd_obj = create_empty_object(SollumType.DRAWABLE_DICTIONARY)
        ydd_obj.parent = parent

        return {"FINISHED"}


class SOLLUMZ_OT_convert_to_drawable(bpy.types.Operator):
    """Convert the selected object to a Drawable"""
    bl_idname = "sollumz.converttodrawable"
    bl_label = "Convert to Drawable"
    bl_options = {"UNDO"}

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        auto_embed_col = context.scene.auto_create_embedded_col
        do_center = context.scene.center_drawable_to_selection

        if context.scene.create_seperate_drawables or len(selected_meshes) == 1:
            self.convert_separate_drawables(context, selected_meshes, auto_embed_col)
        else:
            self.convert_to_single_drawable(context, selected_meshes, auto_embed_col, do_center)

        self.report({"INFO"}, "Succesfully converted all selected objects to a Drawable.")

        return {"FINISHED"}

    def convert_separate_drawables(
        self,
        context: bpy.types.Context,
        selected_meshes: list[bpy.types.Object],
        auto_embed_col: bool = False
    ):
        for obj in selected_meshes:
            # override selected collection to create the drawable object in the same collection as the mesh
            with context.temp_override(collection=obj.users_collection[0]):
                drawable_obj = convert_obj_to_drawable(obj)

                if auto_embed_col:
                    composite_obj = convert_obj_to_composite(
                        duplicate_object(obj),
                        SollumType.BOUND_GEOMETRYBVH,
                        context.window_manager.sz_flag_preset_index
                    )
                    composite_obj.parent = drawable_obj
                    composite_obj.name = f"{drawable_obj.name}.col"

    def convert_to_single_drawable(
        self,
        context: bpy.types.Context,
        selected_meshes: list[bpy.types.Object],
        auto_embed_col: bool = False,
        do_center: bool = False
    ):
        # override selected collection to create the drawable object in the same collection as the selected meshes
        # the active mesh collection has preference in case the selected meshes are in different collections
        target_coll_obj = context.active_object if context.active_object in selected_meshes else selected_meshes[0]
        target_coll = target_coll_obj.users_collection[0]
        with context.temp_override(collection=target_coll):
            drawable_obj = convert_objs_to_single_drawable(selected_meshes)

            if do_center:
                center_drawable_to_models(drawable_obj)

            if auto_embed_col:
                col_objs = [duplicate_object(o) for o in selected_meshes]
                composite_obj = convert_objs_to_single_composite(
                    col_objs,
                    SollumType.BOUND_GEOMETRYBVH,
                    context.window_manager.sz_flag_preset_index
                )
                composite_obj.parent = drawable_obj


class SOLLUMZ_OT_convert_to_drawable_model(bpy.types.Operator):
    """Convert the selected object to a Drawable Model"""
    bl_idname = "sollumz.converttodrawablemodel"
    bl_label = "Convert to Drawable Model"
    bl_options = {"UNDO"}

    def execute(self, context):
        selected_meshes = [
            obj for obj in context.selected_objects if obj.type == "MESH"]

        if not selected_meshes:
            self.report({"INFO"}, f"No mesh objects selected!")
            return {"CANCELLED"}

        for obj in selected_meshes:
            convert_obj_to_model(obj)
            self.report(
                {"INFO"}, f"Converted {obj.name} to a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_MODEL]}.")

        return {"FINISHED"}


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


def shader_preset_from_material(material: bpy.types.Material) -> ShaderPreset:
    preset = ShaderPreset()
    shader_def = ShaderManager.find_shader(material.shader_properties.filename)

    for node in material.node_tree.nodes:
        param_def = shader_def.parameter_map.get(node.name, None)
        if param_def is None:
            continue

        if (
            isinstance(node, SzShaderNodeParameter) and
            isinstance(param_def, ShaderParameterFloatVectorDef) and
            not param_def.is_array
        ):
            param = ShaderPresetParam()
            param.name = node.name
            param.x = node.get(0)
            param.y = node.get(1) if node.num_cols > 1 else None
            param.z = node.get(2) if node.num_cols > 2 else None
            param.w = node.get(3) if node.num_cols > 3 else None
            preset.params.append(param)
        elif (
            isinstance(node, bpy.types.ShaderNodeTexImage) and
            isinstance(param_def, ShaderParameterTextureDef)
        ):
            param = ShaderPresetParam()
            param.name = node.name
            param.texture = node.sollumz_texture_name
            preset.params.append(param)

    return preset


def shader_preset_apply_to_material(material: bpy.types.Material, preset: ShaderPreset, apply_textures: bool = True):
    shader_def = ShaderManager.find_shader(material.shader_properties.filename)

    for param in preset.params:
        param_def = shader_def.parameter_map.get(param.name, None)
        if param_def is None:
            continue

        node = material.node_tree.nodes.get(param.name, None)
        if node is None:
            continue

        if (
            isinstance(node, SzShaderNodeParameter) and
            isinstance(param_def, ShaderParameterFloatVectorDef) and
            not param_def.is_array
        ):
            if node.num_cols > 0 and param.x is not None:
                node.set(0, param.x)
            if node.num_cols > 1 and param.y is not None:
                node.set(1, param.y)
            if node.num_cols > 2 and param.z is not None:
                node.set(2, param.z)
            if node.num_cols > 3 and param.w is not None:
                node.set(3, param.w)
        elif apply_textures and (
            isinstance(node, bpy.types.ShaderNodeTexImage) and
            isinstance(param_def, ShaderParameterTextureDef)
        ):
            # Try to get a loaded image...
            img = bpy.data.images.get(param.texture, None) or bpy.data.images.get(f"{param.texture}.dds", None)
            if not img:
                # Otherwise, search in the shared textures directories
                from .ydrimport import lookup_texture_file, is_non_color_texture
                texture_path = lookup_texture_file(param.texture, None)
                img = texture_path and bpy.data.images.load(str(texture_path), check_existing=True)
                if img and is_non_color_texture(shader_def.filename, param.name):
                    img.colorspace_settings.is_data = True

            if img:
                node.image = img


class SOLLUMZ_OT_save_shader_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Save a shader preset of the active material"""
    bl_idname = "sollumz.save_shader_preset"
    bl_label = "Save Shader Preset"
    bl_action = f"{bl_label}"

    name: bpy.props.StringProperty(name="Name")

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        mat = aobj and aobj.active_material
        if mat is None or mat.sollum_type != MaterialType.SHADER:
            cls.poll_message_set("No Sollumz shader material selected.")
            return False

        return True

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def run(self, context):
        self.name = self.name.strip()

        if len(self.name) == 0:
            self.warning("Please specify a name for the new shader preset.")
            return False

        mat = context.active_object.active_material
        if not mat:
            self.warning("No material selected!")
            return False

        load_shader_presets()

        for preset in shader_presets.presets:
            if preset.name == self.name:
                self.warning(
                    "A preset with that name already exists! If you wish to overwrite this preset, delete the original.")
                return False

        shader_preset = shader_preset_from_material(mat)
        shader_preset.name = self.name
        shader_presets.presets.append(shader_preset)

        filepath = get_shader_presets_path()
        shader_presets.write_xml(filepath)
        load_shader_presets()

        self.message(f"Saved preset '{shader_preset.name}'!")

        tag_redraw(context, space_type="VIEW_3D", region_type="UI")
        return True


class SOLLUMZ_OT_load_shader_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Apply a shader preset to the active material"""
    bl_idname = "sollumz.load_shader_preset"
    bl_label = "Apply Shader Preset to Selected"
    bl_context = "object"
    bl_options = {"REGISTER", "UNDO"}
    bl_action = f"{bl_label}"

    apply_textures: BoolProperty(name="Apply Textures", default=True)

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        mat = aobj and aobj.active_material
        if mat is None or mat.sollum_type != MaterialType.SHADER:
            cls.poll_message_set("No Sollumz shader material selected.")
            return False

        wm = context.window_manager
        if not (0 <= wm.sz_shader_preset_index < len(wm.sz_shader_presets)):
            cls.poll_message_set("No shader preset available.")
            return False

        return True

    def run(self, context):
        index = context.window_manager.sz_shader_preset_index
        mat = context.active_object.active_material
        if not mat:
            self.warning("No shaders selected!")
            return False

        load_shader_presets()
        shader_preset: ShaderPreset = shader_presets.presets[index]
        shader_preset_apply_to_material(mat, shader_preset, apply_textures=self.apply_textures)
        self.message(f"Applied preset '{shader_preset.name}' to {mat.name} material.")
        return True


class SOLLUMZ_OT_delete_shader_preset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete the selected shader preset"""
    bl_idname = "sollumz.delete_shader_preset"
    bl_label = "Delete Shader Preset"
    bl_action = f"{bl_label}"

    @classmethod
    def poll(cls, context):
        wm = context.window_manager
        return 0 <= wm.sz_shader_preset_index < len(wm.sz_shader_presets)

    def run(self, context):
        index = context.window_manager.sz_shader_preset_index
        load_shader_presets()
        filepath = get_shader_presets_path()

        try:
            preset = shader_presets.presets[index]
            shader_presets.presets.remove(preset)

            try:
                shader_presets.write_xml(filepath)
                load_shader_presets()

                return True
            except:
                self.error(f"Error during deletion of shader preset: {traceback.format_exc()}")
                return False

        except IndexError:
            self.warning(
                f"Shader preset does not exist! Ensure the preset file is present in the '{filepath}' directory.")
            return False


class MaterialConverterHelper:
    bl_options = {"UNDO"}

    def get_materials(self, obj: bpy.types.Object):
        materials = obj.data.materials

        if len(materials) == 0:
            self.report({"INFO"}, f"{obj.name} has no materials to convert!")

        return materials

    def get_shader_name(self):
        return shadermats[bpy.context.window_manager.sz_shader_material_index].value

    def convert_material(self, obj: bpy.types.Object, material: bpy.types.Material) -> bpy.types.Material | None:
        return MaterialConverter(obj, material).convert(self.get_shader_name())

    def execute(self, context):
        for obj in context.selected_objects:
            if obj.type != 'MESH':
                continue

            if not obj.data.materials:
                continue

            materials = self.get_materials(obj)

            for material in materials:
                new_material = self.convert_material(obj, material)

                if new_material is None:
                    continue

                self.report(
                    {"INFO"}, f"Successfully converted material '{new_material.name}'.")

        return {"FINISHED"}


class SOLLUMZ_OT_convert_allmaterials_to_selected(bpy.types.Operator, MaterialConverterHelper):
    """Convert all materials to the selected sollumz shader"""
    bl_idname = "sollumz.convertallmaterialstoselected"
    bl_label = "Convert All Materials To Selected"


class SOLLUMZ_OT_convert_material_to_selected(bpy.types.Operator, MaterialConverterHelper):
    """Convert objects material to the selected sollumz shader"""
    bl_idname = "sollumz.convertmaterialtoselected"
    bl_label = "Convert Material To Selected Sollumz Shader"

    def get_materials(self, obj: bpy.types.Object):
        if obj.active_material is None:
            self.report({"INFO"}, f"{obj.name} has no active material!")
            return []

        return [obj.active_material]


class SOLLUMZ_OT_auto_convert_material(bpy.types.Operator, MaterialConverterHelper):
    """Attempt to automatically determine shader name from material node setup and convert the material to a Sollumz material"""
    bl_idname = "sollumz.autoconvertmaterial"
    bl_label = "Convert Material To Shader Material"

    def convert_material(self, obj: bpy.types.Object, material: bpy.types.Material) -> bpy.types.Material | None:
        if material.sollum_type == MaterialType.SHADER:
            return None

        return MaterialConverter(obj, material).auto_convert()


def post_create_shader_add_default_images(material: bpy.types.Material):
    for n in material.node_tree.nodes:
        if isinstance(n, bpy.types.ShaderNodeTexImage) and not n.image:
            # TODO: don't create new texture for hidden texture parameters
            # TODO: should we reuse the image
            texture = bpy.data.images.new(name="Texture", width=512, height=512)
            n.image = texture


def post_create_shader_update_object(obj: bpy.types.Object, material: bpy.types.Material):
    mesh = obj.data

    # First, try renaming to avoid creating more attributes than needed if the mesh already has some
    mesh_rename_uv_maps_by_order(mesh)
    mesh_rename_color_attrs_by_order(mesh)

    # Then, just add the remaining attributes required by the shader
    mesh_add_missing_uv_maps(mesh)
    mesh_add_missing_color_attrs(mesh)

    if is_tint_material(material):
        create_tinted_shader_graph(obj)


class SOLLUMZ_OT_create_shader_material(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a sollumz shader material"""
    bl_idname = "sollumz.createshadermaterial"
    bl_label = "Create Shader Material"
    bl_action = "Create a Shader Material"

    shader_index: IntProperty(name="Shader Index", min=0, max=len(shadermats) - 1)

    def create_material(self, context, obj, shader_filename):
        if obj.type != "MESH":
            self.warning(f"Object {obj.name} is not a mesh and will be skipped.")
            return

        mesh = obj.data
        mat = create_shader(shader_filename)
        mesh.materials.append(mat)
        post_create_shader_add_default_images(mat)
        post_create_shader_update_object(obj, mat)
        self.message(f"Added a {shader_filename} shader to {obj.name}.")

    def run(self, context):
        objs = bpy.context.selected_objects
        if len(objs) == 0:
            self.warning("Please select a object to add a shader material to.")
            return False

        shader_filename = shadermats[self.shader_index].value
        for obj in objs:
            try:
                self.create_material(context, obj, shader_filename)
            except:
                self.message(f"Failed adding {shader_filename} to {obj.name} because : \n {traceback.format_exc()}")

        return True


class SOLLUMZ_OT_change_shader(SOLLUMZ_OT_base, bpy.types.Operator):
    """Change the shader used by the active material"""
    bl_idname = "sollumz.change_shader"
    bl_label = "Change Shader"
    bl_action = "Change Shader of Material"

    shader_index: IntProperty(name="Shader Index", min=0, max=len(shadermats) - 1)

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return (
            aobj and
            aobj.type == "MESH" and
            aobj.active_material and
            aobj.active_material.sollum_type == MaterialType.SHADER
        )

    def run(self, context):
        aobj = context.active_object
        mat = aobj.active_material
        old_shader_filename = mat.shader_properties.filename
        new_shader_filename = shadermats[self.shader_index].value

        tmp_preset = shader_preset_from_material(mat)
        create_shader(new_shader_filename, in_place_material=mat)
        shader_preset_apply_to_material(mat, tmp_preset, apply_textures=True)

        post_create_shader_add_default_images(mat)
        for obj in bpy.data.objects:  # update all objects that are using this material
            if obj.type == "MESH" and mat.name in obj.data.materials:
                post_create_shader_update_object(obj, mat)

        self.message(f"Changed {old_shader_filename} shader to {new_shader_filename}.")
        return True


class SOLLUMZ_OT_set_all_textures_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Sets all textures to embedded on the selected objects active material"""
    bl_idname = "sollumz.setallembedded"
    bl_label = "Set all Textures Embedded"
    bl_action = "Set all Textures Embedded"

    def set_textures_embedded(self, obj):
        mat = obj.active_material
        if mat is None:
            self.message(f"No active material on {obj.name} will be skipped")
            return

        if mat.sollum_type == MaterialType.SHADER:
            for node in mat.node_tree.nodes:
                if isinstance(node, bpy.types.ShaderNodeTexImage):
                    node.texture_properties.embedded = True
            self.message(
                f"Set {obj.name}s material {mat.name} textures to embedded.")
        else:
            self.message(
                f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            self.set_textures_embedded(obj)

        return True


class SOLLUMZ_OT_set_all_materials_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Sets all materials to embedded"""
    bl_idname = "sollumz.setallmatembedded"
    bl_label = "Set all Materials Embedded"
    bl_action = "Set All Materials Embedded"

    def set_materials_embedded(self, obj):
        for mat in obj.data.materials:
            if mat.sollum_type == MaterialType.SHADER:
                for node in mat.node_tree.nodes:
                    if isinstance(node, bpy.types.ShaderNodeTexImage):
                        node.texture_properties.embedded = True
                self.message(
                    f"Set {obj.name}s material {mat.name} textures to embedded.")
            else:
                self.message(
                    f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            self.set_materials_embedded(obj)

        return True


class SOLLUMZ_OT_remove_all_textures_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Remove all embeded textures on the selected objects active material"""
    bl_idname = "sollumz.removeallembedded"
    bl_label = "Remove all Embeded Textures"
    bl_action = "Remove all Embeded Textures"

    def set_textures_unembedded(self, obj):
        mat = obj.active_material
        if mat == None:
            self.message(f"No active material on {obj.name} will be skipped")
            return

        if mat.sollum_type == MaterialType.SHADER:
            for node in mat.node_tree.nodes:
                if (isinstance(node, bpy.types.ShaderNodeTexImage)):
                    node.texture_properties.embedded = False
            self.message(
                f"Set {obj.name}s material {mat.name} textures to unembedded.")
        else:
            self.message(
                f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            self.set_textures_unembedded(obj)

        return True


class SOLLUMZ_OT_unset_all_materials_embedded(SOLLUMZ_OT_base, bpy.types.Operator):
    """Make all materials on the selected object use non-embedded textures"""
    bl_idname = "sollumz.removeallmatembedded"
    bl_label = "Set all Materials Unembedded"
    bl_action = "Set all Materials Unembedded"

    def set_materials_unembedded(self, obj):
        for mat in obj.data.materials:
            if mat.sollum_type == MaterialType.SHADER:
                for node in mat.node_tree.nodes:
                    if (isinstance(node, bpy.types.ShaderNodeTexImage)):
                        node.texture_properties.embedded = False
                self.message(
                    f"Set {obj.name}s materials to unembedded.")
            else:
                self.message(
                    f"Skipping object {obj.name} because it does not have a sollumz shader active.")

    def run(self, context):
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            self.set_materials_unembedded(obj)

        return True


class SOLLUMZ_OT_update_tinted_shader_graph(SOLLUMZ_OT_base, bpy.types.Operator):
    """Update the tinted shader graph"""
    bl_idname = "sollumz.update_tinted_shader_graph"
    bl_label = "Update Tinted Shader"
    bl_action = "Update Tinted Shader"

    def run(self, context): 
        objs = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if len(objs) == 0:
            self.message(
                f"No mesh objects selected!")
            return False

        for obj in objs:
            create_tinted_shader_graph(obj)

        return True


class SOLLUMZ_OT_BONE_FLAGS_NewItem(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_new_item"
    bl_label = "Add a new item"
    bl_action = "Add a Bone Flag"

    def run(self, context):
        bone = context.active_bone
        bone.bone_properties.flags.add()
        self.message(f"Added bone flag to bone: {bone.name}")
        return True


class SOLLUMZ_OT_BONE_FLAGS_DeleteItem(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.bone_flags_delete_item"
    bl_label = "Deletes an item"
    bl_action = "Delete a Bone Flag"

    @classmethod
    def poll(cls, context):
        return context.active_bone is not None and context.active_bone.bone_properties.flags

    def run(self, context):
        bone = context.active_bone
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


class SOLLUMZ_OT_apply_bone_properties_to_armature(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.apply_bone_properties_to_armature"
    bl_label = "To Armature"
    bl_action = bl_label

    def run(self, context):
        armature = context.active_object
        if armature is None or armature.type != "ARMATURE":
            return

        if armature.pose is None:
            return

        for pbone in armature.pose.bones:
            bone = pbone.bone
            set_recommended_bone_properties(bone)

        self.message(f"Apply bone properties to armature: {armature.name}")
        return True


class SOLLUMZ_OT_apply_bone_properties_to_selected_bones(SOLLUMZ_OT_base, bpy.types.Operator):
    bl_idname = "sollumz.apply_bone_properties_to_selected_bones"
    bl_label = "To Selected Bones"
    bl_action = bl_label

    def run(self, context):
        pbones = context.selected_pose_bones
        if pbones is None:
            return

        count = 0
        for pbone in pbones:
            bone = pbone.bone
            set_recommended_bone_properties(bone)
            count += 1

        self.message(f"Apply bone properties to {count} bone(s)")
        return True


class BonePoseModeRestrictedHelper:
    @classmethod
    def poll(cls, context: Context):
        cls.poll_message_set("Must be in object mode or pose mode.")
        return context.mode == "POSE" and len(context.selected_pose_bones) > 0


class SOLLUMZ_OT_clear_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.removeboneflags"
    bl_label = "Remove Bone Flags"
    bl_description = "Remove all bone flags for selected bones"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            pBone.bone.bone_properties.flags.clear()
        tag_redraw(context)
        self.report({'INFO'}, "Flags Removed")
        return {'FINISHED'}


class SOLLUMZ_OT_rotation_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.rotationboneflags"
    bl_label = "Add Rotation Flags"
    bl_description = "Add rotation flags for selected bones"

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "RotX"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "RotY"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "RotZ"
        tag_redraw(context)
        self.report({'INFO'}, f'Rotation Flags Added for {len(selected_bones)} bone(s)')
        return {'FINISHED'}


class SOLLUMZ_OT_translation_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.transformboneflags"
    bl_label = "Add Translation Flags"
    bl_description = "Add translation flags for selected bones"

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "TransX"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "TransY"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "TransZ"
        tag_redraw(context)
        self.report({'INFO'}, f'Translation Flags Added for {len(selected_bones)} bone(s)')
        return {'FINISHED'}


class SOLLUMZ_OT_scale_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.scaleboneflags"
    bl_label = "Add Scale Flags"
    bl_description = "Add scale flags for selected bones"

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "ScaleX"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "ScaleY"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "ScaleZ"
        tag_redraw(context)
        self.report({'INFO'}, f'Scale Flags Added for {len(selected_bones)} bone(s)')
        return {'FINISHED'}


class SOLLUMZ_OT_limit_bone_flags(bpy.types.Operator, BonePoseModeRestrictedHelper):
    bl_idname = "sollumz.limitboneflags"
    bl_label = "Add Limit Flags"
    bl_description = "Removes selected bone flags and adds the proper limit flags for custom bone locations"

    def execute(self, context):
        selected_bones = context.selected_pose_bones
        for pBone in selected_bones:
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "LimitRotation"
            new_flag = pBone.bone.bone_properties.flags.add()
            new_flag.name = "LimitTranslation"
        tag_redraw(context)
        self.report({'INFO'}, f'Limit Flags Added for {len(selected_bones)} bone(s)')
        return {'FINISHED'}


class OperatorMoveShaderUpBase:
    move_to_top = False

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        if aobj is None or aobj.sollum_type != SollumType.DRAWABLE:
            return False

        drawable_props = aobj.drawable_properties
        num_shaders = len(drawable_props.shader_order.order_items)
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        return shader_ind < num_shaders and shader_ind != 0

    def execute(self, context):
        aobj = context.active_object
        drawable_props = aobj.drawable_properties
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        if self.move_to_top:
            drawable_props.shader_order.move_shader_to_top(shader_ind)
        else:
            drawable_props.shader_order.move_shader_up(shader_ind)

        return {"FINISHED"}


class OperatorMoveShaderDownBase:
    move_to_bottom = False

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        if aobj is None or aobj.sollum_type != SollumType.DRAWABLE:
            return False

        drawable_props = aobj.drawable_properties
        num_shaders = len(drawable_props.shader_order.order_items)
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        return shader_ind < num_shaders - 1 and num_shaders > 1

    def execute(self, context):
        aobj = context.active_object
        drawable_props = aobj.drawable_properties
        shader_ind = drawable_props.shader_order.get_active_shader_item_index()

        if self.move_to_bottom:
            drawable_props.shader_order.move_shader_to_bottom(shader_ind)
        else:
            drawable_props.shader_order.move_shader_down(shader_ind)

        return {"FINISHED"}


class SOLLUMZ_OT_move_shader_up(OperatorMoveShaderUpBase, bpy.types.Operator):
    bl_idname = "sollumz.move_shader_up"
    bl_label = "Up"
    bl_description = "Move shader up in the rendering order"


class SOLLUMZ_OT_move_shader_to_top(OperatorMoveShaderUpBase, bpy.types.Operator):
    bl_idname = "sollumz.move_shader_to_top"
    bl_label = "Move To Top"
    bl_description = "Move shader to the top in the rendering order"

    move_to_top = True


class SOLLUMZ_OT_move_shader_down(OperatorMoveShaderDownBase, bpy.types.Operator):
    bl_idname = "sollumz.move_shader_down"
    bl_label = "Down"
    bl_description = "Move shader down in the rendering order"


class SOLLUMZ_OT_move_shader_to_bottom(OperatorMoveShaderDownBase, bpy.types.Operator):
    bl_idname = "sollumz.move_shader_to_bottom"
    bl_label = "Move To Bottom"
    bl_description = "Move shader to the bottom in the rendering order"

    move_to_bottom = True


class SOLLUMZ_OT_order_shaders(bpy.types.Operator):
    bl_idname = "sollumz.order_shaders"
    bl_label = "Order Shaders"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Determine shader rendering order"

    def draw(self, context):
        layout = self.layout
        shader_order = context.active_object.drawable_properties.shader_order

        row = layout.row()
        col = row.column()

        col.template_list("SOLLUMZ_UL_SHADER_ORDER_LIST", "", shader_order, "order_items",
                          shader_order, "active_index", maxrows=40)

        col = row.column()
        col.operator(SOLLUMZ_OT_move_shader_to_top.bl_idname, text="", icon="TRIA_UP")
        subcol = col.column(align=True)
        subcol.operator(SOLLUMZ_OT_move_shader_up.bl_idname, text="", icon="TRIA_UP")
        subcol.operator(SOLLUMZ_OT_move_shader_down.bl_idname, text="", icon="TRIA_DOWN")
        col.operator(SOLLUMZ_OT_move_shader_to_bottom.bl_idname, text="", icon="TRIA_DOWN")

    def execute(self, context):
        aobj = context.active_object
        self.apply_order(aobj)

        return {"FINISHED"}

    def invoke(self, context, event):
        wm = context.window_manager

        aobj = context.active_object
        self.add_initial_items(aobj)

        return wm.invoke_props_dialog(self, width=800)

    def add_initial_items(self, drawable_obj: bpy.types.Object):
        """Add initial shader sort items based on materials from drawable_obj"""
        shader_order: DrawableShaderOrder = drawable_obj.drawable_properties.shader_order
        mats = get_sollumz_materials(drawable_obj)
        self.validate_indices(mats)

        shader_order.order_items.clear()

        for mat in mats:
            item = shader_order.order_items.add()
            item.index = mat.shader_properties.index
            item.name = mat.name
            item.filename = mat.shader_properties.filename

    def validate_indices(self, mats: list[bpy.types.Material]):
        """Ensure valid and unique shader indices (in-case user changed them or blend file is from previous version)"""
        shader_inds = [mat.shader_properties.index for mat in mats]
        has_repeating_indices = any(
            shader_inds.count(i) > 1 for i in shader_inds)
        inds_out_of_range = any(i >= len(mats) for i in shader_inds)

        if not has_repeating_indices and not inds_out_of_range:
            return

        for i, mat in enumerate(mats):
            mat.shader_properties.index = i

    def apply_order(self, drawable_obj: bpy.types.Object):
        """Set material shader indices based on shader order"""
        shader_order: DrawableShaderOrder = drawable_obj.drawable_properties.shader_order
        mats = get_sollumz_materials(drawable_obj)

        if len(shader_order.order_items) != len(mats):
            self.report(
                {"ERROR"}, "Failed to apply order, shader collection size mismatch!")
            return {"CANCELLED"}

        for i, mat in enumerate(mats):
            mat.shader_properties.index = shader_order.order_items[i].index

        return {"FINISHED"}


class SOLLUMZ_OT_add_child_of_constraint(bpy.types.Operator):
    bl_idname = "sollumz.add_child_of_constraint"
    bl_label = "Add Bone Constraint"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Add Child Of constraint to the selected Drawable Model and set the proper constraint properties"

    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        for obj in context.selected_objects:
            parent_obj = find_sollumz_parent(obj)

            if parent_obj is None or parent_obj.type != "ARMATURE":
                self.report(
                    {"INFO"}, f"{obj.name} must be parented to a Drawable armature, or Drawable that is parented to a Fragment!")
                return {"CANCELLED"}

            add_child_of_bone_constraint(obj, armature_obj=parent_obj)

        return {"FINISHED"}


class SOLLUMZ_OT_add_armature_modifier_constraint(bpy.types.Operator):
    bl_idname = "sollumz.add_armature_modifier"
    bl_label = "Add Armature Modifier"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Add armature modifier to object with first Sollumz parent as the modifier object"

    @classmethod
    def poll(self, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        for obj in context.selected_objects:
            parent_obj = find_sollumz_parent(obj)
            is_drawable_model = obj.sollum_type == SollumType.DRAWABLE_MODEL

            if parent_obj is None or not is_drawable_model:
                self.report(
                    {"INFO"}, f"{obj.name} must be a Drawable Model and parented to a Drawable!")
                return {"CANCELLED"}

            if parent_obj.type != "ARMATURE":
                self.report(
                    {"INFO"}, f"{obj.name} must be parented to a Drawable armature, or Drawable that is parented to a Fragment!")
                return {"CANCELLED"}

            add_armature_modifier(obj, parent_obj)

        return {"FINISHED"}


class SOLLUMZ_OT_set_correct_child_of_space(bpy.types.Operator):
    bl_idname = "sollumz.set_correct_child_of_space"
    bl_label = "Set correct space for bone parenting"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Sets the owner space and target space such that it behaves the same way as bone parenting"

    @classmethod
    def poll(self, context):
        return context.active_object is not None and get_child_of_constraint(context.active_object) is not None

    def execute(self, context):
        constraint = get_child_of_constraint(context.active_object)
        set_child_of_constraint_space(constraint)

        return {"FINISHED"}


class SOLLUMZ_OT_auto_lod(bpy.types.Operator):
    bl_idname = "sollumz.auto_lod"
    bl_label = "Generate LODs"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = (
        "Generate drawable model LODs via decimate modifier. Starts from the selected reference mesh, generating a "
        "new decimated mesh for each selected LOD level"
    )

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: Context):
        aobj = context.active_object
        ref_mesh = context.scene.sollumz_auto_lod_ref_mesh

        if ref_mesh is None:
            self.report(
                {"INFO"}, "No reference mesh specified! You must specify a mesh to use as the highest LOD level!")
            return {"CANCELLED"}

        lods = self.get_selected_lods_sorted(context)

        if not lods:
            return {"CANCELLED"}

        obj_lods: LODLevels = aobj.sz_lods

        decimate_step = context.scene.sollumz_auto_lod_decimate_step
        last_mesh = ref_mesh

        previous_mode = aobj.mode
        previous_lod_level = obj_lods.active_lod_level

        for lod_level in lods:
            bpy.ops.object.mode_set(mode="OBJECT") # make sure we are in object mode before switching LODs
            mesh = last_mesh.copy()
            mesh.name = self.get_lod_mesh_name(aobj.name, lod_level)

            obj_lods.get_lod(lod_level).mesh = mesh
            obj_lods.active_lod_level = lod_level

            bpy.ops.object.mode_set(mode="EDIT")
            bpy.ops.mesh.select_all(action="SELECT")
            bpy.ops.mesh.decimate(ratio=1.0 - decimate_step)

            last_mesh = mesh

        bpy.ops.object.mode_set(mode="OBJECT")
        obj_lods.active_lod_level = previous_lod_level

        bpy.ops.object.mode_set(mode=previous_mode)

        return {"FINISHED"}

    def get_lod_mesh_name(self, obj_name: str, lod_level: LODLevel):
        return f"{obj_name}.{SOLLUMZ_UI_NAMES[lod_level].lower()}"

    def get_selected_lods_sorted(self, context: Context) -> tuple[LODLevel]:
        return tuple(lod for lod in LODLevel if lod in context.scene.sollumz_auto_lod_levels)


class SOLLUMZ_OT_extract_lods(bpy.types.Operator):
    bl_idname = "sollumz.extract_lods"
    bl_label = "Extract LODs"
    bl_options = {"REGISTER", "UNDO"}
    bl_description = "Extract all meshes of the selected Drawable Model into separate objects"

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: Context):
        aobj = context.active_object
        parent = self.create_parent(context, f"{aobj.name}.LODs")
        lod_levels = context.scene.sollumz_extract_lods_levels

        lods = aobj.sz_lods
        for lod_level in lod_levels:
            lod = lods.get_lod(lod_level)
            lod_mesh = lod.mesh
            if lod_mesh is None:
                continue

            lod_obj = create_blender_object(SollumType.NONE, lod_mesh.name, lod_mesh)
            self.parent_object(lod_obj, parent)

        return {"FINISHED"}

    def create_parent(self, context: Context, name: str) -> bpy.types.Object | bpy.types.Collection:
        parent_type = context.scene.sollumz_extract_lods_parent_type

        if parent_type == "sollumz_extract_lods_parent_type_collection":
            parent = bpy.data.collections.new(name)
            context.collection.children.link(parent)
        else:
            parent = create_empty_object(SollumType.NONE, name)

        return parent

    def parent_object(self, obj: bpy.types.Object, parent: bpy.types.Object | bpy.types.Collection):
        if isinstance(parent, bpy.types.Object):
            obj.parent = parent
        elif isinstance(parent, bpy.types.Collection):
            if obj.users_collection:
                obj.users_collection[0].objects.unlink(obj)

            parent.objects.link(obj)


class SOLLUMZ_OT_uv_maps_rename_by_order(bpy.types.Operator):
    """Rename UV maps based on their order in the list. Does not affect UV maps already in use"""
    bl_idname = "sollumz.uv_maps_rename_by_order"
    bl_label = "Rename UV Maps by Order"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if context.active_object.type == "MESH":
            selected_meshes.append(context.active_object)

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        for mesh_obj in selected_meshes:
            mesh_rename_uv_maps_by_order(mesh_obj.data)

        return {"FINISHED"}


class SOLLUMZ_OT_uv_maps_add_missing(bpy.types.Operator):
    """Add the missing UV maps used by the Sollumz shaders of the mesh"""
    bl_idname = "sollumz.uv_maps_add_missing"
    bl_label = "Add Missing UV Maps"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if context.active_object.type == "MESH":
            selected_meshes.append(context.active_object)

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        for mesh_obj in selected_meshes:
            mesh_add_missing_uv_maps(mesh_obj.data)

        return {"FINISHED"}


class SOLLUMZ_OT_color_attrs_rename_by_order(bpy.types.Operator):
    """Rename colors attributes based on their order in the list. Does not affect color attributes already in use"""
    bl_idname = "sollumz.color_attrs_rename_by_order"
    bl_label = "Rename Color Attributes by Order"
    bl_options = {"UNDO"}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if context.active_object.type == "MESH":
            selected_meshes.append(context.active_object)

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        for mesh_obj in selected_meshes:
            mesh_rename_color_attrs_by_order(mesh_obj.data)

        return {"FINISHED"}


class SOLLUMZ_OT_color_attrs_add_missing(bpy.types.Operator):
    """Add the missing color attributes used by the Sollumz shaders of the mesh"""
    bl_idname = "sollumz.color_attrs_add_missing"
    bl_label = "Add Missing Color Attributes"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        return context.active_object is not None and context.active_object.sollum_type == SollumType.DRAWABLE_MODEL

    def execute(self, context: bpy.types.Context):
        selected_meshes = [obj for obj in context.selected_objects if obj.type == "MESH"]
        if context.active_object.type == "MESH":
            selected_meshes.append(context.active_object)

        if not selected_meshes:
            self.report({"INFO"}, "No mesh objects selected!")
            return {"CANCELLED"}

        for mesh_obj in selected_meshes:
            mesh_add_missing_color_attrs(mesh_obj.data)

        return {"FINISHED"}
