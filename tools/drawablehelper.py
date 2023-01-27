import bpy
from ..ydr.shader_materials import create_shader, try_get_node, ShaderManager
from ..sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, MaterialType, LODLevel
from ..tools.blenderhelper import join_objects, get_children_recursive, duplicate_object
from ..cwxml.drawable import BonePropertiesManager, TextureShaderParameter, VectorShaderParameter
from mathutils import Vector
from typing import Union, Optional


class MaterialConverter:
    def __init__(self, obj: bpy.types.Object, material: bpy.types.Material) -> None:
        self.obj = obj
        self.material: Union[bpy.types.Material, None] = material
        self.new_material: Union[bpy.types.Material, None] = None
        self.bsdf: Union[bpy.types.ShaderNodeBsdfPrincipled, None] = None
        self.diffuse_node: Union[bpy.types.ShaderNodeTexImage, None] = None
        self.specular_node: Union[bpy.types.ShaderNodeTexImage, None] = None
        self.normal_node: Union[bpy.types.ShaderNodeTexImage, None] = None

    def _convert_texture_node(self, param: TextureShaderParameter):
        node: bpy.types.ShaderNodeTexImage = try_get_node(
            self.material.node_tree, param.name)
        tonode: bpy.types.ShaderNodeTexImage = try_get_node(
            self.new_material.node_tree, param.name)

        if not node or not tonode:
            return

        tonode.image = node.image

    def _convert_vector_node(self, param: VectorShaderParameter):
        node_x = try_get_node(self.material.node_tree, param.name + "_x")

        if not node_x:
            return

        node_y = try_get_node(self.material.node_tree, param.name + "_y")
        node_z = try_get_node(self.material.node_tree, param.name + "_z")
        node_w = try_get_node(self.material.node_tree, param.name + "_w")
        tonode_x = try_get_node(self.new_material.node_tree, param.name + "_x")
        tonode_y = try_get_node(self.new_material.node_tree, param.name + "_y")
        tonode_z = try_get_node(self.new_material.node_tree, param.name + "_z")
        tonode_w = try_get_node(self.new_material.node_tree, param.name + "_w")
        tonode_x.outputs[0].default_value = node_x.outputs[0].default_value
        tonode_y.outputs[0].default_value = node_y.outputs[0].default_value
        tonode_z.outputs[0].default_value = node_z.outputs[0].default_value
        tonode_w.outputs[0].default_value = node_w.outputs[0].default_value

    def convert_shader_to_shader(self, shader_name):
        shader = ShaderManager.shaders[shader_name]
        # TODO: array nodes params
        for param in shader.parameters:
            if param.type == "Texture":
                self._convert_texture_node(param)
            elif param.type == "Vector":
                self._convert_vector_node(param)

        return self.new_material

    def _get_diffuse_node(self):
        diffuse_input = self.bsdf.inputs["Base Color"]

        if diffuse_input.is_linked:
            return diffuse_input.links[0].from_node

        return None

    def _get_specular_node(self):
        specular_input = self.bsdf.inputs["Specular"]

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
        self.bsdf = try_get_node(self.material.node_tree, "Principled BSDF")

        if self.bsdf is None:
            raise Exception(
                "Failed to convert material: Node tree must contain a Princpled BSDF node.")

        self.diffuse_node = self._get_diffuse_node()

        if self.diffuse_node is None:
            raise Exception(
                "Failed to convert material: Material must have an image node linked to the base color.")

        if not isinstance(self.diffuse_node, bpy.types.ShaderNodeTexImage):
            raise Exception(
                "Failed to convert material: Base color node is not an image node.")

        self.specular_node = self._get_specular_node()
        self.normal_node = self._get_normal_node()

    def _create_new_material(self, shader_name):
        self.new_material = create_shader(shader_name)

    def _set_new_node_images(self):
        if self.new_material is None:
            raise Exception(
                "Failed to set images: Sollumz material has not been created yet!")

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
            raise Exception(
                "Failed to convert material: Specular node is not an image node.")

        if has_normal_node and not isinstance(self.normal_node, bpy.types.ShaderNodeTexImage):
            raise Exception(
                "Failed to convert material: Normal map color input is not an image node.")
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

        return self.new_material

    def auto_convert(self) -> bpy.types.Material:
        """Attempt to automatically determine shader name from material node setup and convert the material to a Sollumz material."""
        shader_name = self._determine_shader_name()
        return self.convert(shader_name)


def create_drawable(sollum_type=SollumType.DRAWABLE):
    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    bpy.context.collection.objects.link(empty)
    bpy.context.view_layer.objects.active = bpy.data.objects[empty.name]

    return empty


def convert_selected_to_drawable(objs, use_names=False, multiple=False, do_center=True):
    parent = None

    center = Vector()
    dobjs = []

    if not multiple:
        dobj = create_drawable()
        dobjs.append(dobj)
        if do_center:
            for obj in objs:
                center += obj.location

            center /= len(objs)
            dobj.location = center
        dmobj = create_drawable(SollumType.DRAWABLE_MODEL)
        dmobj.parent = dobj

    for obj in objs:

        if obj.type != "MESH":
            raise Exception(
                f"{obj.name} cannot be converted because it has no mesh data.")

        if multiple:
            dobj = parent or create_drawable()
            dobjs.append(dobj)
            if do_center:
                dobj.location = obj.location
                obj.location = Vector()
            dmobj = create_drawable(SollumType.DRAWABLE_MODEL)
            dmobj.parent = dobj
        elif do_center:
            obj.location -= center

        obj.parent = dmobj

        name = obj.name

        if use_names:
            obj.name = name + "_old"
            dobj.name = name

        obj.sollum_type = SollumType.DRAWABLE_GEOMETRY

        new_obj = obj.copy()
        # add color layer
        if len(new_obj.data.vertex_colors) == 0:
            new_obj.data.vertex_colors.new()
        # add object to collection
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.collection.objects.link(new_obj)
        new_obj.name = name + "_geom"

    return dobjs


def join_drawable_geometries(drawable):
    join_objects(get_drawable_geometries(drawable))


def get_drawable_geometries(drawable):
    cobjs = []
    children = get_children_recursive(drawable)
    for obj in children:
        if obj.sollum_type == SollumType.DRAWABLE_GEOMETRY:
            cobjs.append(obj)
    return cobjs


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


def drawable_to_asset(drawable_obj: bpy.types.Object, name: Optional[str] = None):
    """Creates an asset from the drawable's high LOD."""
    mesh_objs = []

    for child in drawable_obj.children:
        if child.sollum_type != SollumType.DRAWABLE_MODEL or child.drawable_model_properties.sollum_lod != LODLevel.HIGH:
            continue

        mesh_objs.extend([duplicate_object(obj)
                         for obj in child.children if obj.type == "MESH"])

    joined_obj = join_objects(mesh_objs)

    joined_obj.modifiers.clear()
    joined_obj.parent = None

    joined_obj.name = name or drawable_obj.name

    joined_obj.asset_mark()
    joined_obj.asset_generate_preview()

    bpy.context.collection.objects.unlink(joined_obj)

    for child in drawable_obj.children_recursive:
        bpy.data.objects.remove(child)

    bpy.data.objects.remove(drawable_obj)
    bpy.data.orphans_purge(do_recursive=True)
