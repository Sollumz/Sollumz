import traceback
import bpy
from bpy.types import (
    Material,
    ShaderNodeBsdfPrincipled,
    ShaderNodeTexImage,
)
from bpy.props import (
    IntProperty,
    BoolProperty,
)
from ...cwxml.shader_preset import ShaderPreset, ShaderPresetParam
from ...sollumz_helper import SOLLUMZ_OT_base
from ...sollumz_properties import MaterialType
from ...tools.blenderhelper import tag_redraw
from ...tools.meshhelper import (
    mesh_add_missing_uv_maps,
    mesh_add_missing_color_attrs,
    mesh_rename_uv_maps_by_order,
    mesh_rename_color_attrs_by_order,
)
from ...shared.shader_nodes import SzShaderNodeParameter
from ...cwxml.shader import (
    ShaderParameterFloatVectorDef,
    ShaderParameterTextureDef,
    ShaderParameterDef,
    ShaderParameterType,
    ShaderManager,
)
from ..properties import get_shader_presets_path, load_shader_presets, shader_presets
from ..shader_materials import (
    create_shader,
    create_tinted_shader_graph,
    is_tint_material,
    shadermats,
    try_get_node,
    find_bsdf_and_material_output,
    obj_has_tint_mats,
)


def shader_preset_from_material(material: Material) -> ShaderPreset:
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
            isinstance(node, ShaderNodeTexImage) and
            isinstance(param_def, ShaderParameterTextureDef)
        ):
            param = ShaderPresetParam()
            param.name = node.name
            param.texture = node.sollumz_texture_name
            preset.params.append(param)

    return preset


def shader_preset_apply_to_material(material: Material, preset: ShaderPreset, apply_textures: bool = True):
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
            isinstance(node, ShaderNodeTexImage) and
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


class MaterialConverter:
    def __init__(self, obj: bpy.types.Object, material: Material) -> None:
        self.obj = obj
        self.material: Material = material
        self.new_material: Material | None = None
        self.bsdf: ShaderNodeBsdfPrincipled | None = None
        self.diffuse_node: ShaderNodeTexImage | None = None
        self.specular_node: ShaderNodeTexImage | None = None
        self.normal_node: ShaderNodeTexImage | None = None

    def _convert_texture_node(self, param: ShaderParameterTextureDef):
        src_node: bpy.types.ShaderNodeTexImage = try_get_node(self.material.node_tree, param.name)
        if not src_node or not isinstance(src_node, ShaderNodeTexImage):
            return

        dst_node: bpy.types.ShaderNodeTexImage = try_get_node(self.new_material.node_tree, param.name)
        if not dst_node or not isinstance(dst_node, ShaderNodeTexImage):
            return

        dst_node.image = src_node.image

    def _convert_parameter_node(self, param: ShaderParameterDef):
        src_node: SzShaderNodeParameter = try_get_node(self.material.node_tree, param.name)
        if not src_node or not isinstance(src_node, SzShaderNodeParameter):
            return

        dst_node: SzShaderNodeParameter = try_get_node(self.new_material.node_tree, param.name)
        if not dst_node or not isinstance(dst_node, SzShaderNodeParameter):
            return

        src_count = src_node.num_cols * src_node.num_rows
        dst_count = dst_node.num_cols * dst_node.num_rows
        for i in range(min(src_count, dst_count)):
            dst_node.set(i, src_node.get(i))

    def convert_shader_to_shader(self, shader_name: str):
        shader = ShaderManager.find_shader(shader_name)
        assert shader is not None

        for param in shader.parameters:
            match param.type:
                case ShaderParameterType.TEXTURE:
                    self._convert_texture_node(param)
                case (ShaderParameterType.FLOAT |
                      ShaderParameterType.FLOAT2 |
                      ShaderParameterType.FLOAT3 |
                      ShaderParameterType.FLOAT4 |
                      ShaderParameterType.FLOAT4X4):
                    self._convert_parameter_node(param)
                case _:
                    raise Exception(f"Unknown shader parameter! {param.type=} {param.name=}")

    def _get_diffuse_node(self):
        diffuse_input = self.bsdf.inputs["Base Color"]

        if diffuse_input.is_linked:
            return diffuse_input.links[0].from_node

        return None

    def _get_specular_node(self):
        specular_input = self.bsdf.inputs["Specular IOR Level"]

        if specular_input.is_linked:
            return specular_input.links[0].from_node

        return None

    def _get_normal_node(self):
        normal_input = self.bsdf.inputs["Normal"]
        if len(normal_input.links) > 0:
            normal_map_node = normal_input.links[0].from_node
            normal_map_input = normal_map_node.inputs["Color"]
            if len(normal_map_input.links) > 0:
                return normal_map_input.links[0].from_node

        return None

    def _get_nodes(self):
        self.bsdf, _ = find_bsdf_and_material_output(self.material)

        if self.bsdf is None:
            raise Exception("Failed to convert material: Node tree must contain a Princpled BSDF node.")

        self.diffuse_node = self._get_diffuse_node()

        if self.diffuse_node is not None and not isinstance(self.diffuse_node, bpy.types.ShaderNodeTexImage):
            raise Exception("Failed to convert material: Base color node is not an image node.")

        self.specular_node = self._get_specular_node()
        self.normal_node = self._get_normal_node()

    def _create_new_material(self, shader_name):
        self.new_material = create_shader(shader_name)

    def _set_new_node_images(self):
        if self.new_material is None:
            raise Exception("Failed to set images: Sollumz material has not been created yet!")

        for node, name in {self.diffuse_node: "DiffuseSampler", self.specular_node: "SpecSampler", self.normal_node: "BumpSampler"}.items():
            new_node: bpy.types.ShaderNodeTexImage = try_get_node(
                self.new_material.node_tree, name)

            if node is None or new_node is None:
                continue

            new_node.image = node.image

    def _get_material_slot(self):
        for slot in self.obj.material_slots:
            if slot.material == self.material:
                return slot

    def _replace_material(self):
        if self.new_material is None:
            raise Exception(
                "Failed to replace material: Sollumz material has not been created yet!")

        mat_name = f"{self.material.name}_{self.new_material.name}"

        self.new_material.name = mat_name

        slot = self._get_material_slot()
        slot.material = self.new_material

    def _determine_shader_name(self):
        self._get_nodes()

        has_specular_node = self.specular_node is not None
        has_normal_node = self.normal_node is not None

        if has_specular_node and not isinstance(self.specular_node, bpy.types.ShaderNodeTexImage):
            raise Exception("Failed to convert material: Specular node is not an image node.")

        if has_normal_node and not isinstance(self.normal_node, bpy.types.ShaderNodeTexImage):
            raise Exception("Failed to convert material: Normal map color input is not an image node.")

        if has_normal_node and has_specular_node:
            return "normal_spec.sps"
        elif has_normal_node:
            return "normal.sps"
        elif has_specular_node:
            return "spec.sps"

        return "default.sps"

    def convert(self, shader_name: str) -> bpy.types.Material:
        """Convert the material to a Sollumz material of the provided shader name."""
        self._create_new_material(shader_name)

        if self.material.sollum_type == MaterialType.SHADER:
            self.convert_shader_to_shader(shader_name)
        else:
            self._get_nodes()
            self._set_new_node_images()

        self._replace_material()

        if obj_has_tint_mats(self.obj):
            create_tinted_shader_graph(self.obj)

        return self.new_material

    def auto_convert(self) -> bpy.types.Material:
        """Attempt to automatically determine shader name from material node setup and convert the material to a Sollumz material."""
        shader_name = self._determine_shader_name()
        return self.convert(shader_name)


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


class SOLLUMZ_OT_convert_active_material_to_selected(bpy.types.Operator):
    """Convert the active material of the active object to the selected sollumz shader"""
    bl_idname = "sollumz.convert_active_material_to_selected"
    bl_label = "Convert Active Material To Selected"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return (aobj is not None and
                aobj.type == "MESH" and
                aobj.active_material is not None)

    def execute(self, context):
        aobj = context.active_object
        mat = aobj.active_material

        shader_name = shadermats[context.window_manager.sz_shader_material_index].value
        new_material = MaterialConverter(aobj, mat).convert(shader_name)

        if new_material is None:
            self.report({"ERROR"}, f"Failed to convert material '{mat.name}'!")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Successfully converted material '{new_material.name}' to {shader_name}")
        return {"FINISHED"}


class SOLLUMZ_OT_auto_convert_materials(bpy.types.Operator, MaterialConverterHelper):
    """Attempt to automatically determine shader name from material node setup and convert all materials to Sollumz materials\nAffects all selected objects"""
    bl_idname = "sollumz.autoconvertmaterials"
    bl_label = "Auto Convert All Materials"

    def convert_material(self, obj: bpy.types.Object, material: bpy.types.Material) -> bpy.types.Material | None:
        if material.sollum_type == MaterialType.SHADER:
            return None

        return MaterialConverter(obj, material).auto_convert()


class SOLLUMZ_OT_auto_convert_current_material(bpy.types.Operator):
    """Attempt to automatically determine shader name from current active material and convert it to a Sollumz material"""
    bl_idname = "sollumz.auto_convert_current_material"
    bl_label = "Auto Convert Current Material"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return (aobj is not None and
                aobj.type == "MESH" and
                aobj.active_material is not None)

    def execute(self, context):
        aobj = context.active_object
        mat = aobj.active_material

        new_material = MaterialConverter(aobj, mat).auto_convert()

        if new_material is None:
            self.report({"ERROR"}, f"Failed to auto-convert material '{mat.name}'!")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Successfully auto-converted material '{new_material.name}'")
        return {"FINISHED"}


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
