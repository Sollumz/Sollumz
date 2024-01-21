import bpy
from bpy.types import (
    ShaderNodeTree,
    ShaderNode,
    NodeSocket,
    Material,
)
from typing import NamedTuple, Optional
from . import expr
from ...cwxml.shader import (
    ShaderDef,
    ShaderParameterType,
    ShaderParameterSubtype,
    ShaderParameterFloatDef,
    ShaderParameterFloat2Def,
    ShaderParameterFloat3Def,
    ShaderParameterFloat4Def,
    ShaderParameterFloat4x4Def,
    ShaderParameterTextureDef,
)
from ..shader_nodes import SzShaderNodeParameter, SzShaderNodeParameterDisplayType
from ...tools.meshhelper import get_uv_map_name


class CompiledExpr(NamedTuple):
    node: ShaderNode
    output_socket: Optional[int | str]

    @property
    def output(self) -> NodeSocket:
        assert self.output_socket is not None, "This compiled expression doesn't have an output socket"
        return self.node.outputs[self.output_socket]


class Compiler:
    node_tree: ShaderNodeTree
    root_expr: expr.Expr
    compiled_expr_cache: dict[expr.Expr, CompiledExpr] = {}
    separate_xyz_cache: dict[expr.VectorExpr, ShaderNode] = {}
    uv_map_cache: dict[int, ShaderNode] = {}

    def __init__(self, node_tree: ShaderNodeTree, root: expr.Expr):
        self.node_tree = node_tree
        self.root_expr = root

    def compile(self) -> CompiledExpr:
        return self.visit(self.root_expr)

    def visit(self, e: expr.Expr) -> CompiledExpr:
        compiled_expr = self.compiled_expr_cache.get(e, None)
        if compiled_expr is None:
            visit_fn_name = "visit_" + e.__class__.__name__
            visit_fn = getattr(self, visit_fn_name, self.visit_not_implemented)
            compiled_expr = visit_fn(e)
            self.compiled_expr_cache[e] = compiled_expr
        return compiled_expr

    def visit_FloatBinaryExpr(self, e: expr.FloatBinaryExpr) -> CompiledExpr:
        match e.op:
            case expr.FloatBinaryExprOp.ADD:
                op = "ADD"
            case expr.FloatBinaryExprOp.SUBTRACT:
                op = "SUBTRACT"
            case expr.FloatBinaryExprOp.MULTIPLY:
                op = "MULTIPLY"
            case expr.FloatBinaryExprOp.DIVIDE:
                op = "DIVIDE"
            case expr.FloatBinaryExprOp.POWER:
                op = "POWER"
            case expr.FloatBinaryExprOp.LESS_THAN:
                op = "LESS_THAN"
            case expr.FloatBinaryExprOp.GREATER_THAN:
                op = "GREATER_THAN"
            case _:
                raise NotImplementedError(f"{e.op} not implemented!")

        return self.compile_float_math(op, e.lhs, e.rhs)

    def visit_FloatMapRangeExpr(self, e: expr.FloatMapRangeExpr) -> CompiledExpr:
        map_range = self.node_tree.nodes.new("ShaderNodeMapRange")
        map_range.data_type = "FLOAT"
        map_range.clamp = e.clamp

        for input_socket, src in (
            ("Value", e.value),
            ("From Min", e.from_min),
            ("From Max", e.from_max),
            ("To Min", e.to_min),
            ("To Max", e.to_max),
        ):
            self.connect_float_input(src, map_range, input_socket)

        return CompiledExpr(map_range, 0)

    def visit_VectorMixColorExpr(self, e: expr.VectorMixColorExpr) -> CompiledExpr:
        mix = self.node_tree.nodes.new("ShaderNodeMix")
        mix.data_type = "RGBA"
        mix.blend_type = e.blend.value
        self.connect_vector_input(e.in_a, mix, "A")
        self.connect_vector_input(e.in_b, mix, "B")
        self.connect_float_input(e.factor, mix, "Factor")
        return CompiledExpr(mix, "Result")

    def visit_VectorDotExpr(self, e: expr.VectorDotExpr) -> CompiledExpr:
        return self.compile_vector_math("DOT_PRODUCT", e.in_a, e.in_b, output_socket=1)

    def visit_VectorBinaryExpr(self, e: expr.VectorBinaryExpr) -> CompiledExpr:
        match e.op:
            case expr.VectorBinaryExprOp.ADD:
                op = "ADD"
            case expr.VectorBinaryExprOp.SUBTRACT:
                op = "SUBTRACT"
            case expr.VectorBinaryExprOp.MULTIPLY:
                op = "MULTIPLY"
            case expr.VectorBinaryExprOp.DIVIDE:
                op = "DIVIDE"
            case expr.VectorBinaryExprOp.CROSS:
                op = "CROSS_PRODUCT"
            case _:
                raise NotImplementedError(f"{e.op} not implemented!")

        return self.compile_vector_math(op, e.lhs, e.rhs)

    def visit_VectorComponentExpr(self, e: expr.VectorComponentExpr) -> CompiledExpr:
        src = e.source
        xyz = self.separate_xyz_cache.get(src)
        if xyz is None:
            xyz = self.node_tree.nodes.new("ShaderNodeSeparateXYZ")
            self.connect_vector_input(src, xyz, 0)
            self.separate_xyz_cache[src] = xyz

        match e.component:
            case expr.VectorComponent.X:
                output_socket = 0
            case expr.VectorComponent.Y:
                output_socket = 1
            case expr.VectorComponent.Z:
                output_socket = 2
            case _:
                raise NotImplementedError(f"{e.component} not implemented!")

        return CompiledExpr(xyz, output_socket)

    def visit_ConstructVectorExpr(self, e: expr.ConstructVectorExpr) -> CompiledExpr:
        xyz = self.node_tree.nodes.new("ShaderNodeCombineXYZ")

        for input_socket, src in (("X", e.source_x), ("Y", e.source_y), ("Z", e.source_z)):
            self.connect_float_input(src, xyz, input_socket)

        return CompiledExpr(xyz, 0)

    def visit_VectorNormalMapExpr(self, e: expr.VectorNormalMapExpr) -> CompiledExpr:
        normal_map = self.node_tree.nodes.new("ShaderNodeNormalMap")
        normal_map.space = "TANGENT"
        normal_map.uv_map = get_uv_map_name(e.uv_map_index)
        self.connect_vector_input(e.color, normal_map, "Color")
        self.connect_float_input(e.strength, normal_map, "Strength")
        return CompiledExpr(normal_map, 0)

    def visit_UVMapVectorExpr(self, e: expr.UVMapVectorExpr) -> CompiledExpr:
        from ...tools.meshhelper import get_uv_map_name

        uv = self.uv_map_cache.get(e.uv_map_index)
        if uv is None:
            uv_map = get_uv_map_name(e.uv_map_index)
            uv = self.node_tree.nodes.get(uv_map, None) or self.node_tree.nodes.new("ShaderNodeUVMap")
            uv.name = uv_map
            uv.label = uv_map
            uv.uv_map = uv_map
            self.uv_map_cache[e.uv_map_index] = uv

        return CompiledExpr(uv, 0)

    def visit_ParameterExpr(self, e: expr.ParameterExpr) -> CompiledExpr:
        # TODO: check that node exists
        param_node = self.node_tree.nodes[e.parameter_name]
        return CompiledExpr(param_node, -1)

    def visit_ParameterComponentExpr(self, e: expr.ParameterComponentExpr) -> CompiledExpr:
        # TODO: check component index
        param_expr = self.visit(e.parameter)
        return CompiledExpr(param_expr.node, e.component_index)

    def visit_TextureExpr(self, e: expr.TextureExpr) -> CompiledExpr:
        # TODO: can only use each texture name once, because otherwise we would create multiple image texture nodes for the same texture parameter
        # check it

        tex = self.node_tree.nodes[e.texture_name]
        # tex = self.node_tree.nodes.new("ShaderNodeTexImage")
        # tex.name = e.texture_name
        # tex.label = e.texture_name

        self.connect_vector_input(e.uv, tex, 0)

        return CompiledExpr(tex, None)

    def visit_TextureColorExpr(self, e: expr.TextureColorExpr) -> CompiledExpr:
        tex_expr = self.visit(e.texture)
        return CompiledExpr(tex_expr.node, 0)

    def visit_TextureAlphaExpr(self, e: expr.TextureAlphaExpr) -> CompiledExpr:
        tex_expr = self.visit(e.texture)
        return CompiledExpr(tex_expr.node, 1)

    def visit_ColorAttributeExpr(self, e: expr.ColorAttributeExpr) -> CompiledExpr:
        color_attr = self.node_tree.nodes.new("ShaderNodeVertexColor")
        color_attr.layer_name = e.attribute_name
        return CompiledExpr(color_attr, None)

    def visit_ColorAttributeColorExpr(self, e: expr.ColorAttributeColorExpr) -> CompiledExpr:
        color_attr_expr = self.visit(e.color_attribute)
        return CompiledExpr(color_attr_expr.node, 0)

    def visit_ColorAttributeAlphaExpr(self, e: expr.ColorAttributeAlphaExpr) -> CompiledExpr:
        color_attr_expr = self.visit(e.color_attribute)
        return CompiledExpr(color_attr_expr.node, 1)

    def visit_BsdfPrincipledExpr(self, e: expr.BsdfPrincipledExpr) -> CompiledExpr:
        bsdf = self.node_tree.nodes.new("ShaderNodeBsdfPrincipled")

        # vector inputs
        for input_socket, src in (
            ("Base Color", e.base_color),
            ("Normal", e.normal),
        ):
            self.connect_vector_input(src, bsdf, input_socket)

        # float inputs
        for input_socket, src in (
            ("Alpha", e.alpha),
            ("Metallic", e.metallic),
            ("Roughness", e.roughness),
            ("Specular IOR Level", e.specular_ior_level),
            ("Coat Weight", e.coat_weight),
        ):
            self.connect_float_input(src, bsdf, input_socket)

        return CompiledExpr(bsdf, 0)

    def visit_EmissionExpr(self, e: expr.EmissionExpr) -> CompiledExpr:
        em = self.node_tree.nodes.new("ShaderNodeEmission")
        self.connect_vector_input(e.color, em, "Color")
        self.connect_float_input(e.strength, em, "Strength")
        return CompiledExpr(em, 0)

    def visit_ShaderMixExpr(self, e: expr.ShaderMixExpr) -> CompiledExpr:
        mix = self.node_tree.nodes.new("ShaderNodeMixShader")
        self.connect_float_input(e.factor, mix, "Fac")
        self.connect_shader_input(e.in_a, mix, 1)
        self.connect_shader_input(e.in_b, mix, 2)
        return CompiledExpr(mix, 0)

    def compile_vector_math(self, op: str, a: expr.VectorExpr, b: expr.VectorExpr, output_socket: int = 0) -> CompiledExpr:
        math = self.node_tree.nodes.new("ShaderNodeVectorMath")
        math.operation = op
        self.connect_vector_input(a, math, 0)
        self.connect_vector_input(b, math, 1)
        return CompiledExpr(math, output_socket)

    def compile_float_math(self, op: str, a: expr.FloatExpr, b: expr.FloatExpr) -> CompiledExpr:
        math = self.node_tree.nodes.new("ShaderNodeMath")
        math.operation = op
        self.connect_float_input(a, math, 0)
        self.connect_float_input(b, math, 1)
        return CompiledExpr(math, 0)

    def connect_float_input(self, src_expr: Optional[expr.FloatExpr], node: ShaderNode, input_socket: int | str):
        if isinstance(src_expr, expr.FloatConstantExpr):
            node.inputs[input_socket].default_value = src_expr.value
        elif src_expr is not None:
            compiled_src_expr = self.visit(src_expr)
            self.node_tree.links.new(compiled_src_expr.output, node.inputs[input_socket])

    def connect_vector_input(self, src_expr: Optional[expr.VectorExpr], node: ShaderNode, input_socket: int | str):
        if isinstance(src_expr, expr.VectorConstantExpr):
            node.inputs[input_socket].default_value = src_expr.value_x, src_expr.value_y, src_expr.value_z
        elif src_expr is not None:
            compiled_src_expr = self.visit(src_expr)
            self.node_tree.links.new(compiled_src_expr.output, node.inputs[input_socket])

    def connect_shader_input(self, src_expr: Optional[expr.ShaderExpr], node: ShaderNode, input_socket: int | str):
        if src_expr is not None:
            compiled_src_expr = self.visit(src_expr)
            self.node_tree.links.new(compiled_src_expr.output, node.inputs[input_socket])

    def visit_FloatConstantExpr(self, e: expr.FloatConstantExpr) -> CompiledExpr:
        raise NotImplementedError("FloatConstantExpr visited! Should be inlined in parent expression!")

    def visit_VectorConstantExpr(self, e: expr.VectorConstantExpr) -> CompiledExpr:
        raise NotImplementedError("VectorConstantExpr visited! Should be inlined in parent expression!")

    def visit_not_implemented(self, e: expr.Expr):
        raise NotImplementedError(f"Visit not implemented for '{e.__class__.__name__}'!")


# TODO: a bit ugly to have this stuff to create parameters here and depend on cwxml.shader
def create_shader_texture_node(node_tree: bpy.types.NodeTree, param: ShaderParameterTextureDef) -> bpy.types.ShaderNodeTexImage:
    tex_node = node_tree.nodes.new("ShaderNodeTexImage")
    tex_node.name = param.name
    tex_node.label = param.name
    tex_node.is_sollumz = True
    # link default UV
    if param.uv is not None:
        uv_map_node = node_tree.nodes[get_uv_map_name(param.uv)]
        node_tree.links.new(uv_map_node.outputs[0], tex_node.inputs[0])
    return tex_node


def create_shader_parameter_node(
    node_tree: bpy.types.NodeTree,
    param: (
        ShaderParameterFloatDef | ShaderParameterFloat2Def | ShaderParameterFloat3Def | ShaderParameterFloat4Def |
        ShaderParameterFloat4x4Def
    )
) -> SzShaderNodeParameter:
    node: SzShaderNodeParameter = node_tree.nodes.new(SzShaderNodeParameter.bl_idname)
    node.name = param.name
    node.label = node.name

    display_type = SzShaderNodeParameterDisplayType.DEFAULT
    match param.type:
        case ShaderParameterType.FLOAT:
            cols, rows = 1, max(1, param.count)
            if param.count == 0 and param.subtype == ShaderParameterSubtype.BOOL:
                display_type = SzShaderNodeParameterDisplayType.BOOL
        case ShaderParameterType.FLOAT2:
            cols, rows = 2, max(1, param.count)
        case ShaderParameterType.FLOAT3:
            cols, rows = 3, max(1, param.count)
            if param.count == 0 and param.subtype == ShaderParameterSubtype.RGB:
                display_type = SzShaderNodeParameterDisplayType.RGB
        case ShaderParameterType.FLOAT4:
            cols, rows = 4, max(1, param.count)
            if param.count == 0 and param.subtype == ShaderParameterSubtype.RGBA:
                display_type = SzShaderNodeParameterDisplayType.RGBA
        case ShaderParameterType.FLOAT4X4:
            cols, rows = 4, 4

    if param.hidden:
        display_type = SzShaderNodeParameterDisplayType.HIDDEN_IN_UI

    node.set_size(cols, rows)
    node.set_display_type(display_type)

    if rows == 1 and param.type in {ShaderParameterType.FLOAT, ShaderParameterType.FLOAT2,
                                    ShaderParameterType.FLOAT3, ShaderParameterType.FLOAT4}:
        node.set("X", param.x)
        if cols > 1:
            node.set("Y", param.y)
        if cols > 2:
            node.set("Z", param.z)
        if cols > 3:
            node.set("W", param.w)

    return node


def create_shader_parameters(dest_node_tree: ShaderNodeTree, shader_def: ShaderDef):
    for param in shader_def.parameters:
        match param.type:
            case ShaderParameterType.TEXTURE:
                create_shader_texture_node(dest_node_tree, param)
            case (ShaderParameterType.FLOAT |
                  ShaderParameterType.FLOAT2 |
                  ShaderParameterType.FLOAT3 |
                  ShaderParameterType.FLOAT4 |
                  ShaderParameterType.FLOAT4X4):
                create_shader_parameter_node(dest_node_tree, param)
            case _:
                raise Exception(f"Unknown shader parameter! {param.type=} {param.name=}")


def create_shader_uv_maps(dest_node_tree: ShaderNodeTree, shader_def: ShaderDef):
    """Creates a ``ShaderNodeUVMap`` node for each UV map used in the shader."""

    used_uv_maps = set(shader_def.uv_maps.values())
    for uv_map_index in used_uv_maps:
        uv_map = get_uv_map_name(uv_map_index)
        node = dest_node_tree.nodes.new("ShaderNodeUVMap")
        node.name = uv_map
        node.label = uv_map
        node.uv_map = uv_map


def compile_expr(dest_node_tree: ShaderNodeTree, expr: expr.Expr) -> CompiledExpr:
    """Convert the expression into nodes."""
    return Compiler(dest_node_tree, expr).compile()


def compile_to_material(name: str, shader_expr: expr.ShaderExpr, shader_def: Optional[ShaderDef] = None) -> Material:
    """Create a new Blender material from the given shader expression."""

    assert isinstance(shader_expr, expr.ShaderExpr)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()

    if shader_def is not None:
        create_shader_uv_maps(mat.node_tree, shader_def)
        create_shader_parameters(mat.node_tree, shader_def)

    compiled_shader_expr = compile_expr(mat.node_tree, shader_expr)

    mat_output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(compiled_shader_expr.output, mat_output.inputs["Surface"])

    return mat
