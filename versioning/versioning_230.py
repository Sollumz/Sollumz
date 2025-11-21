"""Handle changes between 2.3.0 and 2.4.0."""

import bpy
from bpy.types import (
    ShaderNode,
    ShaderNodeValue,
    ShaderNodeGroup,
    Material,
    BlendData,
    Object,
    Bone,
    Light,
    PropertyGroup,
)
from typing import Optional, NamedTuple, Callable, Any
from ..sollumz_properties import MaterialType
from ..cwxml.shader import ShaderManager
from ..ydr.shader_materials import create_parameter_node
from ..yft.properties import FragmentTemplateAsset


class OldShaderParam(NamedTuple):
    x: ShaderNodeValue
    y: ShaderNodeValue
    z: ShaderNodeValue
    w: ShaderNodeValue


class OldShaderArrayParam(NamedTuple):
    nodes: list[ShaderNode]


def collect_material_old_shader_parameters(material: Material) -> dict[str, OldShaderParam]:
    def _is_param_node(n: Optional[ShaderNode]) -> bool:
        return n is not None and isinstance(n, ShaderNodeValue) and getattr(node, "is_sollumz", False)

    result = {}
    node_tree = material.node_tree
    for node in node_tree.nodes:
        if not node.name.endswith("_x"):
            continue
        if not _is_param_node(node):
            continue

        param_name = node.name[:-2]
        param_x = node
        param_y = node_tree.nodes.get(f"{param_name}_y", None)
        param_z = node_tree.nodes.get(f"{param_name}_z", None)
        param_w = node_tree.nodes.get(f"{param_name}_w", None)

        if not all(_is_param_node(n) for n in (param_y, param_z, param_w)):
            continue

        result[param_name] = OldShaderParam(param_x, param_y, param_z, param_w)

    return result


def collect_material_old_shader_array_parameters(material: Material) -> dict[str, OldShaderArrayParam]:
    def _is_array_param_node(n: Optional[ShaderNode]) -> bool:
        return (n is not None and isinstance(n, ShaderNodeGroup) and getattr(node, "is_sollumz", False) and
                n.node_tree.name == "ArrayNode")

    result = {}
    node_tree = material.node_tree
    for node in node_tree.nodes:
        if not node.name.endswith(" 1"):
            continue
        if not _is_array_param_node(node):
            continue

        param_name = node.name[:-2]

        all_array_nodes = [n for n in node_tree.nodes if n.name.startswith(param_name)]

        if not all(_is_array_param_node(n) for n in all_array_nodes):
            continue

        all_array_nodes = sorted(all_array_nodes, key=lambda n: int(n.name[len(param_name):].strip()))
        result[param_name] = OldShaderArrayParam(all_array_nodes)

    return result


def upgrade_material_old_shader_parameters(material: Material):
    """Update material shader parameters, changed in commit a588b5a (feat(shader): typed shader parameters)"""
    if not material.use_nodes or material.sollum_type != MaterialType.SHADER:
        return

    params = collect_material_old_shader_parameters(material)
    array_params = collect_material_old_shader_array_parameters(material)
    if len(params) == 0 and len(array_params) == 0:
        return

    shader_name = material.shader_properties.filename
    shader_def = ShaderManager.find_shader(shader_name)
    if shader_def is None:
        return

    node_tree = material.node_tree
    # Convert value parameters
    for param_name, param_old_nodes in params.items():
        param_def = shader_def.parameter_map[param_name]

        param_node = create_parameter_node(node_tree, param_def)
        param_node.location = param_old_nodes[0].location

        for i in range(param_node.num_cols):
            socket = param_old_nodes[i].outputs[0]

            # Copy value
            v = socket.default_value
            param_node.set(i, v)

            if not socket.is_linked:
                continue

            # Connect new node
            for link in socket.links:
                node_tree.links.new(link.to_socket, param_node.outputs[i])

        for n in param_old_nodes:
            node_tree.nodes.remove(n)

    # Convert array parameters
    for param_name, param_old_nodes in array_params.items():
        old_nodes = param_old_nodes.nodes
        param_def = shader_def.parameter_map[param_name]

        param_node = create_parameter_node(node_tree, param_def)
        param_node.location = old_nodes[0].location

        for i in range(param_node.num_cols * param_node.num_rows):
            n = old_nodes[i // 4]
            v = n.inputs[i % 4].default_value
            param_node.set(i, v)

        for n in old_nodes:
            node_tree.nodes.remove(n)


def get_src_props(rna_instance) -> PropertyGroup:
    if bpy.app.version >= (5, 0, 0):
        return rna_instance.bl_system_properties_get()
    else:
        return rna_instance


def move_renamed_prop(
    dst_props: PropertyGroup,
    src_props: PropertyGroup,
    old_name: str,
    new_name: str,
    map_fn: Optional[Callable[[Any], Any]] = None
):
    """If ``old_name`` exists in ``src_props``, copy its value to ``dst_props.new_name`` and delete ``old_name``.
    ``map_fn`` can be used to transform the old value, in case the property type or value meaning changed.
    """
    old_val = src_props.get(old_name, None)
    if old_val is None:
        return

    new_val = old_val if map_fn is None else map_fn(old_val)
    setattr(dst_props, new_name, new_val)
    if bpy.app.version < (5, 0, 0):
        del dst_props[old_name]


def upgrade_fragment_properties(obj: Object):
    src_props = get_src_props(obj)
    if src_props is None:
        return

    src_frag_props = src_props.get("fragment_properties", None)
    if src_frag_props is None:
        return
    dst_frag_props = obj.fragment_properties

    def _map_template_asset(v: float) -> str:
        # was stored as a float, now an enum
        enum_value_int = (int(v) >> 8) & 0xFF
        try:
            enum_value = FragmentTemplateAsset(enum_value_int)
        except ValueError:
            enum_value = FragmentTemplateAsset.NONE
        return enum_value.name

    for old_prop, new_prop, map_fn in (
        ("unk_c0", "template_asset", _map_template_asset),
        ("unk_cc", "unbroken_elasticity", None),
    ):
        move_renamed_prop(dst_frag_props, src_frag_props, old_prop, new_prop, map_fn)

    src_lod_props = src_frag_props.get("lod_properties", None)
    if src_lod_props is None:
        return
    dst_lod_props = dst_frag_props.lod_properties

    for old_prop, new_prop in (
        ("unknown_1c", "min_move_force"),
        ("unknown_50", "unbroken_cg_offset"),
    ):
        move_renamed_prop(dst_lod_props, src_lod_props, old_prop, new_prop)

    src_arch_props = src_lod_props.get("archetype_properties", None)
    if src_arch_props is None:
        return
    dst_arch_props = dst_lod_props.archetype_properties

    for old_prop, new_prop in (
        ("unknown_48", "gravity_factor"),
        ("unknown_4c", "max_speed"),
        ("unknown_50", "max_ang_speed"),
        ("unknown_54", "buoyancy_factor"),
    ):
        move_renamed_prop(dst_arch_props, src_arch_props, old_prop, new_prop)


def upgrade_vehicle_window_properties(obj: Object):
    src_props = get_src_props(obj)
    if src_props is None:
        return

    src_window_props = src_props.get("vehicle_window_properties", None)
    if src_window_props is None:
        return
    dst_window_props = obj.vehicle_window_properties

    for old_prop, new_prop in (
        ("unk_float_17", "data_min"),
        ("unk_float_18", "data_max"),
    ):
        move_renamed_prop(dst_window_props, src_window_props, old_prop, new_prop)


def upgrade_bone_group_properties(bone: Bone):
    src_props = get_src_props(bone)
    if src_props is None:
        return

    src_group_props = src_props.get("group_properties", None)
    if src_group_props is None:
        return
    dst_group_props = bone.group_properties

    for old_prop, new_prop in (
        ("unk_float_5c", "weapon_health"),
        ("unk_float_60", "weapon_scale"),
        ("unk_float_64", "vehicle_scale"),
        ("unk_float_68", "ped_scale"),
        ("unk_float_6c", "ragdoll_scale"),
        ("unk_float_70", "explosion_scale"),
        ("unk_float_74", "object_scale"),
        ("unk_float_78", "ped_inv_mass_scale"),
        ("unk_float_a8", "melee_scale"),
    ):
        move_renamed_prop(dst_group_props, src_group_props, old_prop, new_prop)


def upgrade_bone_tag(bone: Bone):
    src_props = get_src_props(bone.bone_properties)
    if src_props is None:
        return

    old_tag = src_props.get("tag", None)
    if old_tag is None:
        # No stored 'tag' value, this is a newer bone, skip it
        return

    bone_props = bone.bone_properties
    if bone_props.use_manual_tag:
        # User possibly already changed the tag to something else, skip it
        return

    bone_props.set_tag(old_tag)


def upgrade_light_flags(light: Light):
    src_props = get_src_props(light)
    if src_props is None:
        return

    src_light_flags = src_props.get("light_flags", None)
    if src_light_flags is None:
        return
    dst_light_flags = light.light_flags

    for old_prop, new_prop in (
        ("unk1", "interior_only"),
        ("unk2", "exterior_only"),
        ("unk3", "dont_use_in_cutscene"),
        ("unk4", "vehicle"),
        ("unk5", "ignore_light_state"),
        ("unk6", "texture_projection"),
        ("unk7", "cast_shadows"),
        ("shadows", "static_shadows"),
        ("shadowd", "dynamic_shadows"),
        ("sunlight", "calc_from_sun"),
        ("unk11", "enable_buzzing"),
        ("electric", "force_buzzing"),
        ("volume", "draw_volume"),
        ("specoff", "no_specular"),
        ("unk15", "both_int_and_ext"),
        ("lightoff", "corona_only"),
        ("prxoff", "not_in_reflection"),
        ("unk18", "only_in_reflection"),
        ("culling", "enable_culling_plane"),
        ("unk20", "enable_vol_outer_color"),
        ("unk21", "higher_res_shadows"),
        ("unk22", "only_low_res_shadows"),
        ("unk23", "far_lod_light"),
        ("glassoff", "dont_light_alpha"),
        ("unk25", "cast_shadows_if_possible"),
        ("unk26", "cutscene"),
        ("unk27", "moving_light_source"),
        ("unk28", "use_vehicle_twin"),
        ("unk29", "force_medium_lod_light"),
        ("unk30", "corona_only_lod_light"),
        ("unk31", "delayed_render"),
        ("unk32", "already_tested_for_occlusion"),
    ):
        move_renamed_prop(dst_light_flags, src_light_flags, old_prop, new_prop)


def upgrade_light_shadow_blur(light: Light):
    src_props = get_src_props(light)
    if src_props is None:
        return

    src_light_props = src_props.get("light_properties", None)
    if src_light_props is None:
        return

    shadow_blur_val = src_light_props.get("shadow_blur", None)
    if shadow_blur_val is None:
        return

    dst_light_props = light.light_properties
    dst_light_props.shadow_blur = max(0.0, min(1.0, shadow_blur_val / 255))


def do_versions(data_version: int, data: BlendData):
    if data_version < 0:
        # commit a588b5a (feat(shader): typed shader parameters)
        for material in data.materials:
            upgrade_material_old_shader_parameters(material)

        for obj in data.objects:
            # commit 268453b (tweak(yft): update fragment properties names)
            upgrade_fragment_properties(obj)
            upgrade_vehicle_window_properties(obj)

        for armature in data.armatures:
            for bone in armature.bones:
                # commit 614dbf5 (Auto-calculate bone tag setting per bone)
                # This is an older change but users still have problems when opening old .blend files with rigged models
                # shared in resources lists or old tutorials, confused as to why their animation doesn't work when exported
                upgrade_bone_tag(bone)

                # commit 268453b (tweak(yft): update fragment properties names)
                upgrade_bone_group_properties(bone)

    if data_version < 1:
        for light in data.lights:
            # commit bc37e25 (feat(ydr): update light flags to correct names)
            upgrade_light_flags(light)
            # normalize shadow_blur property
            upgrade_light_shadow_blur(light)
