import bpy
from bpy.types import (
    ShaderNodeTree,
    ShaderNode,
    NodeSocket,
    Material,
)
from typing import NamedTuple, Optional
from . import expr


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

    def visit_VectorDotExpr(self, e: expr.VectorDotExpr) -> CompiledExpr:
        return self.compile_vector_math("DOT_PRODUCT", e.a, e.b, output_socket=1)

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
            if isinstance(src, expr.VectorConstantExpr):
                xyz.inputs[0].default_value = src.value_x, src.value_y, src.value_z
            else:
                src_expr = self.visit(src)
                self.node_tree.links.new(src_expr.output, xyz.inputs[0])
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
            if isinstance(src, expr.FloatConstantExpr):
                xyz.inputs[input_socket].default_value = src.value
            else:
                src_expr = self.visit(src)
                self.node_tree.links.new(src_expr.output, xyz.inputs[input_socket])

        return CompiledExpr(xyz, 0)

    def visit_UVMapVectorExpr(self, e: expr.UVMapVectorExpr) -> CompiledExpr:
        from ...tools.meshhelper import get_uv_map_name

        # TODO: re-use UV map nodes if already exist
        uv_map = get_uv_map_name(e.uv_map_index)
        uv = self.node_tree.nodes.new("ShaderNodeUVMap")
        uv.name = uv_map
        uv.label = uv_map
        uv.uv_map = uv_map

        return CompiledExpr(uv, 0)

    def visit_TextureExpr(self, e: expr.TextureExpr) -> CompiledExpr:
        tex = self.node_tree.nodes.new("ShaderNodeTexImage")
        tex.name = e.texture_name
        tex.label = e.texture_name

        uv_expr = self.visit(e.uv)
        self.node_tree.links.new(uv_expr.output, tex.inputs[0])

        return CompiledExpr(tex, None)

    def visit_TextureColorExpr(self, e: expr.TextureColorExpr) -> CompiledExpr:
        tex_expr = self.visit(e.texture)
        return CompiledExpr(tex_expr.node, 0)

    def visit_TextureAlphaExpr(self, e: expr.TextureAlphaExpr) -> CompiledExpr:
        tex_expr = self.visit(e.texture)
        return CompiledExpr(tex_expr.node, 1)

    def visit_BsdfPrincipledExpr(self, e: expr.BsdfPrincipledExpr) -> CompiledExpr:
        bsdf = self.node_tree.nodes.new("ShaderNodeBsdfPrincipled")

        color_expr = self.visit(e.base_color)
        self.node_tree.links.new(color_expr.output, bsdf.inputs["Base Color"])

        # float inputs
        for input_socket, src in (
            ("Alpha", e.alpha),
            ("Metallic", e.metallic),
            ("Roughness", e.roughness),
        ):
            if isinstance(src, expr.FloatConstantExpr):
                bsdf.inputs[input_socket].default_value = src.value
            elif src is not None:
                src_expr = self.visit(src)
                self.node_tree.links.new(src_expr.output, bsdf.inputs[input_socket])

        return CompiledExpr(bsdf, 0)

    def compile_vector_math(self, op: str, a: expr.VectorExpr, b: expr.VectorExpr, output_socket: int = 0) -> CompiledExpr:
        math = self.node_tree.nodes.new("ShaderNodeVectorMath")
        math.operation = op

        if isinstance(a, expr.VectorConstantExpr):
            math.inputs[0].default_value = a.value_x, a.value_y, a.value_z
        else:
            a_expr = self.visit(a)
            self.node_tree.links.new(a_expr.output, math.inputs[0])

        if isinstance(b, expr.VectorConstantExpr):
            math.inputs[1].default_value = b.value_x, b.value_y, b.value_z
        else:
            b_expr = self.visit(b)
            self.node_tree.links.new(b_expr.output, math.inputs[1])

        return CompiledExpr(math, output_socket)

    def compile_float_math(self, op: str, a: expr.FloatExpr, b: expr.FloatExpr) -> CompiledExpr:
        math = self.node_tree.nodes.new("ShaderNodeMath")
        math.operation = op

        if isinstance(a, expr.FloatConstantExpr):
            math.inputs[0].default_value = a.value
        else:
            a_expr = self.visit(a)
            self.node_tree.links.new(a_expr.output, math.inputs[0])

        if isinstance(b, expr.FloatConstantExpr):
            math.inputs[1].default_value = b.value
        else:
            b_expr = self.visit(b)
            self.node_tree.links.new(b_expr.output, math.inputs[1])

        return CompiledExpr(math, 0)

    def visit_FloatConstantExpr(self, e: expr.FloatConstantExpr) -> CompiledExpr:
        raise NotImplementedError("FloatConstantExpr visited! Should be inlined in parent expression!")

    def visit_VectorConstantExpr(self, e: expr.VectorConstantExpr) -> CompiledExpr:
        raise NotImplementedError("VectorConstantExpr visited! Should be inlined in parent expression!")

    def visit_not_implemented(self, e: expr.Expr):
        raise NotImplementedError(f"Visit not implemented for '{e.__class__.__name__}'!")


def compile_expr(dest_node_tree: ShaderNodeTree, expr: expr.Expr) -> CompiledExpr:
    """Convert the expression into nodes."""
    return Compiler(dest_node_tree, expr).compile()


def compile_to_material(name: str, shader_expr: expr.ShaderExpr) -> Material:
    """Create a new Blender material from the given shader expression."""

    assert isinstance(shader_expr, expr.ShaderExpr)

    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    mat.node_tree.nodes.clear()

    compiled_shader_expr = compile_expr(mat.node_tree, shader_expr)

    mat_output = mat.node_tree.nodes.new("ShaderNodeOutputMaterial")
    mat.node_tree.links.new(compiled_shader_expr.output, mat_output.inputs["Surface"])

    return mat
