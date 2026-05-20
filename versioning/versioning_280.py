"""Handle changes between 2.8.0 and 2.9.0."""

from bpy.types import (
    BlendData,
    Material,
    Scene,
    ShaderNodeTexImage,
)

from ..sollumz_properties import MaterialType


def update_archetype_spawn_point_extensions(scene: Scene):
    from .versioning_230 import move_renamed_prop, get_src_props

    for ytyp in scene.ytyps:
        for arch in ytyp.archetypes_:
            for ext in arch.extensions:
                ext_dst_props = ext.spawn_point_extension_properties
                ext_src_props = get_src_props(ext_dst_props)

                move_renamed_prop(ext_dst_props, ext_src_props, "required_map", "required_imap")

                time_float_to_int = lambda v: min(24, max(0, int(v)))
                move_renamed_prop(ext_dst_props, ext_src_props, "start", "start", time_float_to_int)
                move_renamed_prop(ext_dst_props, ext_src_props, "end", "end", time_float_to_int)


def restore_shader_parameter_node_metadata(material: Material):
    """Rebuild ``is_sollumz``, ``num_cols``, ``num_rows`` and ``display_type`` on shader parameter
    nodes from the shader definition. Blender 5.x does not preserve these custom RNA properties
    on nodes inside materials saved by Blender 4.x, which hides texture samplers and breaks the
    value parameter layout in the Sollumz material panel.
    """
    if material.sollum_type != MaterialType.SHADER:
        return

    node_tree = material.node_tree
    if node_tree is None:
        return

    from szio.gta5.shader import ShaderManager
    from ..ydr.shader_materials import get_shader_parameter_layout
    from ..shared.shader_nodes import SzShaderNodeParameter

    shader_def = ShaderManager.find_shader(material.shader_properties.filename)
    if shader_def is None:
        return

    for node in node_tree.nodes:
        param = shader_def.parameter_map.get(node.name, None)
        if param is None:
            continue

        if isinstance(node, ShaderNodeTexImage):
            node.is_sollumz = True
        elif isinstance(node, SzShaderNodeParameter):
            node.is_sollumz = True
            cols, rows, display_type = get_shader_parameter_layout(param)
            node.num_cols = cols
            node.num_rows = rows
            node.display_type = int(display_type)


def do_versions(data_version: int, data: BlendData):
    if data_version < 9:
        for scene in data.scenes:
            update_archetype_spawn_point_extensions(scene)

    if data_version < 10:
        for mat in data.materials:
            restore_shader_parameter_node_metadata(mat)
