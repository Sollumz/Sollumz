import bpy
from mathutils import Vector


from ..ydr.shader_materials import create_shader, create_tinted_shader_graph, obj_has_tint_mats, try_get_node
from ..sollumz_properties import SollumType, MaterialType, LODLevel
from ..tools.blenderhelper import create_empty_object, find_bsdf_and_material_output
from ..tools.meshhelper import mesh_add_missing_color_attrs, mesh_add_missing_uv_maps, mesh_rename_color_attrs_by_order, mesh_rename_uv_maps_by_order
from ..cwxml.drawable import BonePropertiesManager, Drawable, DrawableModel
from ..cwxml.shader import ShaderManager, ShaderParameterType
from ..shared.shader_nodes import SzShaderNodeParameter
from typing import Union


class MaterialConverter:
    def __init__(self, obj: bpy.types.Object, material: bpy.types.Material) -> None:
        self.obj = obj
        self.material: Union[bpy.types.Material, None] = material
        self.bsdf: Union[bpy.types.ShaderNodeBsdfPrincipled, None] = None
        self.diffuse_node: Union[bpy.types.ShaderNodeTexImage, None] = None
        self.specular_node: Union[bpy.types.ShaderNodeTexImage, None] = None
        self.normal_node: Union[bpy.types.ShaderNodeTexImage, None] = None

    def convert_shader_to_shader(self, shader_name: str):
        shader = ShaderManager.find_shader(shader_name)
        assert shader is not None

        # Store existing parameters before conversion
        existing_params = {}
        for param in shader.parameters:
            match param.type:
                case ShaderParameterType.TEXTURE:
                    node = try_get_node(self.material.node_tree, param.name)
                    if node and isinstance(node, bpy.types.ShaderNodeTexImage):
                        existing_params[param.name] = node.image
                case (ShaderParameterType.FLOAT |
                      ShaderParameterType.FLOAT2 |
                      ShaderParameterType.FLOAT3 |
                      ShaderParameterType.FLOAT4 |
                      ShaderParameterType.FLOAT4X4):
                    node = try_get_node(self.material.node_tree, param.name)
                    if node and isinstance(node, SzShaderNodeParameter):
                        count = node.num_cols * node.num_rows
                        existing_params[param.name] = [node.get(i) for i in range(count)]

        # Convert material in-place
        create_shader(shader_name, in_place_material=self.material)

        # Restore existing parameters
        for param in shader.parameters:
            if param.name not in existing_params:
                continue
                
            match param.type:
                case ShaderParameterType.TEXTURE:
                    node = try_get_node(self.material.node_tree, param.name)
                    if node and isinstance(node, bpy.types.ShaderNodeTexImage):
                        node.image = existing_params[param.name]
                case (ShaderParameterType.FLOAT |
                      ShaderParameterType.FLOAT2 |
                      ShaderParameterType.FLOAT3 |
                      ShaderParameterType.FLOAT4 |
                      ShaderParameterType.FLOAT4X4):
                    node = try_get_node(self.material.node_tree, param.name)
                    if node and isinstance(node, SzShaderNodeParameter):
                        values = existing_params[param.name]
                        for i, value in enumerate(values):
                            if i < node.num_cols * node.num_rows:
                                node.set(i, value)

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

    def _convert_in_place(self, shader_name):
        create_shader(shader_name, in_place_material=self.material)

    def _set_converted_node_images(self):
        for node, name in {self.diffuse_node: "DiffuseSampler", self.specular_node: "SpecSampler", self.normal_node: "BumpSampler"}.items():
            new_node: bpy.types.ShaderNodeTexImage = try_get_node(
                self.material.node_tree, name)

            if node is None or new_node is None:
                continue

            new_node.image = node.image

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
        
        if self.material.sollum_type == MaterialType.SHADER:
            self.convert_shader_to_shader(shader_name)
        else:
            # Get nodes from original material before conversion
            self._get_nodes()
            # Convert material in-place
            self._convert_in_place(shader_name)
            # Set images from original nodes to converted material
            self._set_converted_node_images()
        
        mesh = self.obj.data

        # Renaming UV maps and color attributes to avoid creating more attributes than needed if the mesh already has some
        mesh_rename_uv_maps_by_order(mesh)
        mesh_rename_color_attrs_by_order(mesh)

        # Adding the remaining UV maps and color attributes required by the shader
        mesh_add_missing_uv_maps(mesh)
        mesh_add_missing_color_attrs(mesh)

        # Creating tinted shader graph if the material has tinting
        if obj_has_tint_mats(self.obj):
            create_tinted_shader_graph(self.obj)

        return self.material

    def auto_convert(self) -> bpy.types.Material:
        """Attempt to automatically determine shader name from material node setup and convert the material to a Sollumz material."""
        shader_name = self._determine_shader_name()
        return self.convert(shader_name)


def set_recommended_bone_properties(bone):
    bone_item = BonePropertiesManager.bones.get(bone.name)
    if bone_item is None:
        return

    bone.bone_properties.tag = bone_item.tag
    bone.bone_properties.flags.clear()
    flags_restricted = set(["LimitRotation", "Unk0"])
    for flag_name in bone_item.flags:
        if flag_name in flags_restricted:
            continue

        flag = bone.bone_properties.flags.add()
        flag.name = flag_name


def convert_obj_to_drawable(obj: bpy.types.Object):
    drawable_obj = create_empty_object(SollumType.DRAWABLE)
    drawable_obj.location = obj.location
    drawable_obj.rotation_mode = obj.rotation_mode
    drawable_obj.rotation_euler = obj.rotation_euler
    drawable_obj.rotation_quaternion = obj.rotation_quaternion
    drawable_obj.rotation_axis_angle = obj.rotation_axis_angle

    obj_name = obj.name

    convert_obj_to_model(obj)
    obj.name = f"{obj.name}.model"
    # Set drawable obj name after converting obj to a model to avoid .00# suffix
    drawable_obj.name = obj_name

    drawable_obj.parent = obj.parent
    obj.parent = drawable_obj
    obj.location = Vector()
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.rotation_quaternion = (1.0, 0.0, 0.0, 0.0)
    obj.rotation_axis_angle = (0.0, 0.0, 1.0, 0.0)

    return drawable_obj


def convert_objs_to_single_drawable(objs: list[bpy.types.Object]):
    drawable_obj = create_empty_object(SollumType.DRAWABLE)

    for obj in objs:
        convert_obj_to_model(obj)
        obj.name = f"{obj.name}.model"
        obj.parent = drawable_obj

    return drawable_obj


def convert_obj_to_model(obj: bpy.types.Object):
    obj.sollum_type = SollumType.DRAWABLE_MODEL
    obj.sz_lods.get_lod(LODLevel.HIGH).mesh = obj.data
    obj.sz_lods.active_lod_level = LODLevel.HIGH


def center_drawable_to_models(drawable_obj: bpy.types.Object):
    model_objs = [
        child for child in drawable_obj.children if child.sollum_type == SollumType.DRAWABLE_MODEL]

    center = Vector()

    for obj in model_objs:
        center += obj.location

    center /= len(model_objs)

    drawable_obj.location = center

    for obj in model_objs:
        obj.location -= center


def get_model_xmls_by_lod(drawable_xml: Drawable) -> dict[LODLevel, DrawableModel]:
    return {
        LODLevel.VERYHIGH: drawable_xml.hi_models,
        LODLevel.HIGH: drawable_xml.drawable_models_high,
        LODLevel.MEDIUM: drawable_xml.drawable_models_med,
        LODLevel.LOW: drawable_xml.drawable_models_low,
        LODLevel.VERYLOW: drawable_xml.drawable_models_vlow,
    }
