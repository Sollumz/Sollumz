from typing import Optional, TypeAlias
from enum import IntEnum, Enum
from abc import ABC


class ExprDumpContext:
    var_map: dict['Expr', int] = {}
    last_var_id: int = 0
    output_text: str = ""

    def output(self, s: str):
        self.output_text += s
        self.output_text += "\n"

    def new_var_id(self) -> str:
        var_id = f"${self.last_var_id}"
        self.last_var_id += 1
        return var_id

    def get_var_id(self, expr: 'Expr', expr_callback) -> str:
        var_id = self.var_map.get(expr, None)
        if var_id is None:
            expr_str = expr_callback()
            var_id = self.new_var_id()
            self.var_map[expr] = var_id
            self.output(f"[{id(expr)}] {var_id} = {expr_str}")
        return var_id


class Expr(ABC):
    """Base class for all expressions."""

    def __str__(self):
        raise NotImplementedError(f"{self.__class__.__name__}.__str__ not implemented!")

    def dump(self, ctx: ExprDumpContext) -> str:
        """Includes this expression in the dump output. Returns its variable ID."""
        raise NotImplementedError(f"{self.__class__.__name__}.dump not implemented!")


class FloatExpr(Expr, ABC):
    """Base class for expressions that produce a float value."""

    def __add__(self, rhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(self, rhs, FloatBinaryExprOp.ADD)

    def __sub__(self, rhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(self, rhs, FloatBinaryExprOp.SUBTRACT)

    def __mul__(self, rhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(self, rhs, FloatBinaryExprOp.MULTIPLY)

    def __truediv__(self, rhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(self, rhs, FloatBinaryExprOp.DIVIDE)

    def __pow__(self, exp: 'FloatExpr', mod=None) -> 'FloatBinaryExpr':
        if mod is not None:
            raise NotImplementedError("mod not supported")

        return FloatBinaryExpr(self, exp, FloatBinaryExprOp.POWER)

    def __radd__(self, lhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(lhs, self, FloatBinaryExprOp.ADD)

    def __rsub__(self, lhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(lhs, self, FloatBinaryExprOp.SUBTRACT)

    def __rmul__(self, lhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(lhs, self, FloatBinaryExprOp.MULTIPLY)

    def __rtruediv__(self, lhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(lhs, self, FloatBinaryExprOp.DIVIDE)

    def __rpow__(self, base: 'FloatExpr', mod=None) -> 'FloatBinaryExpr':
        if mod is not None:
            raise NotImplementedError("mod not supported")

        return FloatBinaryExpr(base, self, FloatBinaryExprOp.POWER)

    def __lt__(self, rhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(self, rhs, FloatBinaryExprOp.LESS_THAN)

    def __gt__(self, rhs: 'FloatExpr') -> 'FloatBinaryExpr':
        return FloatBinaryExpr(self, rhs, FloatBinaryExprOp.GREATER_THAN)


class FloatConstantExpr(FloatExpr):
    """A constant float value."""

    value: float

    def __init__(self, value: float):
        self.value = value

    def __str__(self):
        return f"{self.value}"

    def dump(self, ctx: ExprDumpContext) -> str:
        return f"{self.value}"


Floaty: TypeAlias = FloatExpr | float | int


def floaty(v: Floaty) -> FloatExpr:
    """Converts a float-y value to a ``FloatExpr``."""
    if isinstance(v, float):
        return FloatConstantExpr(v)
    elif isinstance(v, int):
        return FloatConstantExpr(float(v))
    elif isinstance(v, FloatExpr):
        return v
    else:
        raise TypeError(f"Cannot convert '{v}' to a float expression")


def optional_floaty(v: Optional[Floaty]) -> Optional[FloatExpr]:
    """Converts a float-y value to a ``FloatExpr``. ``None`` is allowed."""
    return None if v is None else floaty(v)


class FloatBinaryExprOp(IntEnum):
    ADD = 0
    SUBTRACT = 1
    MULTIPLY = 2
    DIVIDE = 3
    POWER = 4
    LESS_THAN = 5
    GREATER_THAN = 6

    def token(self) -> str:
        match self:
            case FloatBinaryExprOp.ADD:
                return "+"
            case FloatBinaryExprOp.SUBTRACT:
                return "-"
            case FloatBinaryExprOp.MULTIPLY:
                return "*"
            case FloatBinaryExprOp.DIVIDE:
                return "/"
            case FloatBinaryExprOp.POWER:
                return "**"
            case FloatBinaryExprOp.LESS_THAN:
                return "<"
            case FloatBinaryExprOp.GREATER_THAN:
                return ">"
            case _:
                raise NotImplementedError(f"'{self}' not implemented!")


class FloatBinaryExpr(FloatExpr):
    """Operation between two floats that produces another float."""

    lhs: FloatExpr
    rhs: FloatExpr
    op: FloatBinaryExprOp

    def __init__(self, lhs: Floaty, rhs: Floaty, op: FloatBinaryExprOp):
        self.lhs = floaty(lhs)
        self.rhs = floaty(rhs)
        self.op = op

    def __str__(self):
        return f"({self.lhs} {self.op.token()} {self.rhs})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            lhs_id = self.lhs.dump(ctx)
            rhs_id = self.rhs.dump(ctx)
            return f"{lhs_id} {self.op.token()} {rhs_id}"
        var_id = ctx.get_var_id(self, g)
        return var_id


class FloatMapRangeExpr(FloatExpr):
    """Remap a float value from a range to a target range."""

    value: FloatExpr
    from_min: FloatExpr
    from_max: FloatExpr
    to_min: FloatExpr
    to_max: FloatExpr
    clamp: bool

    def __init__(
        self, value: Floaty,
        from_min: Floaty, from_max: Floaty,
        to_min: Floaty, to_max: Floaty,
        clamp: bool = False
    ):
        self.value = floaty(value)
        self.from_min = floaty(from_min)
        self.from_max = floaty(from_max)
        self.to_min = floaty(to_min)
        self.to_max = floaty(to_max)
        self.clamp = clamp

    def __str__(self):
        return f"map_range({self.value}, {self.from_min}, {self.from_max}, {self.to_min}, {self.to_max}, {self.clamp})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            value_id = self.value.dump(ctx)
            from_min_id = self.from_min.dump(ctx)
            from_max_id = self.from_max.dump(ctx)
            to_min_id = self.to_min.dump(ctx)
            to_max_id = self.to_max.dump(ctx)
            return f"map_range({value_id}, {from_min_id}, {from_max_id}, {to_min_id}, {to_max_id}, {self.clamp})"
        var_id = ctx.get_var_id(self, g)
        return var_id


class VectorComponent(IntEnum):
    X = 0
    Y = 1
    Z = 2

    def token(self) -> str:
        match self:
            case VectorComponent.X:
                return "x"
            case VectorComponent.Y:
                return "y"
            case VectorComponent.Z:
                return "z"
            case _:
                raise NotImplementedError(f"'{self}' not implemented!")


class VectorComponentExpr(FloatExpr):
    """Access a float component of a vector."""

    source: 'VectorExpr'
    component: VectorComponent

    def __init__(self, source: 'VectorExpr', component: VectorComponent):
        self.source = source
        self.component = component

    def __str__(self):
        return f"{self.source}.{self.component.token()}"

    def dump(self, ctx: ExprDumpContext) -> str:
        source_id = self.source.dump(ctx)
        return f"{source_id}.{self.component.token()}"


class VectorExpr(Expr, ABC):
    """Base class for expressions that produce a vector value."""

    def __add__(self, rhs: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(self, rhs, VectorBinaryExprOp.ADD)

    def __sub__(self, rhs: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(self, rhs, VectorBinaryExprOp.SUBTRACT)

    def __mul__(self, rhs: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(self, rhs, VectorBinaryExprOp.MULTIPLY)

    def __truediv__(self, rhs: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(self, rhs, VectorBinaryExprOp.DIVIDE)

    def __radd__(self, lhs: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(lhs, self, VectorBinaryExprOp.ADD)

    def __rsub__(self, lhs: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(lhs, self, VectorBinaryExprOp.SUBTRACT)

    def __rmul__(self, lhs: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(lhs, self, VectorBinaryExprOp.MULTIPLY)

    def __rtruediv__(self, lhs: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(lhs, self, VectorBinaryExprOp.DIVIDE)

    @property
    def x(self) -> VectorComponentExpr:
        return VectorComponentExpr(self, VectorComponent.X)

    @property
    def y(self) -> VectorComponentExpr:
        return VectorComponentExpr(self, VectorComponent.Y)

    @property
    def z(self) -> VectorComponentExpr:
        return VectorComponentExpr(self, VectorComponent.Z)

    # Aliases
    r = x
    g = y
    b = z

    def dot(self, other: 'VectorExpr') -> 'VectorDotExpr':
        return VectorDotExpr(self, other)

    def cross(self, other: 'VectorExpr') -> 'VectorBinaryExpr':
        return VectorBinaryExpr(self, other, VectorBinaryExprOp.CROSS)


class VectorConstantExpr(VectorExpr):
    """A constant vector value."""

    value_x: float
    value_y: float
    value_z: float

    def __init__(self, x: float, y: float, z: float):
        self.value_x = x
        self.value_y = y
        self.value_z = z

    def __str__(self):
        return f"vec({self.value_x}, {self.value_y}, {self.value_z})"

    def dump(self, ctx: ExprDumpContext) -> str:
        return f"vec({self.value_x}, {self.value_y}, {self.value_z})"


class VectorBinaryExprOp(IntEnum):
    ADD = 0
    SUBTRACT = 1
    MULTIPLY = 2
    DIVIDE = 3
    CROSS = 4

    def token(self) -> str:
        match self:
            case VectorBinaryExprOp.ADD:
                return "+"
            case VectorBinaryExprOp.SUBTRACT:
                return "-"
            case VectorBinaryExprOp.MULTIPLY:
                return "*"
            case VectorBinaryExprOp.DIVIDE:
                return "/"
            case VectorBinaryExprOp.CROSS:
                return "×"
            case _:
                raise NotImplementedError(f"'{self}' not implemented!")


class VectorBinaryExpr(VectorExpr):
    """Operation between two vectors that produces another vector."""

    lhs: VectorExpr
    rhs: VectorExpr
    op: VectorBinaryExprOp

    def __init__(self, lhs: VectorExpr, rhs: VectorExpr, op: VectorBinaryExprOp):
        self.lhs = lhs
        self.rhs = rhs
        self.op = op

    def __str__(self):
        return f"({self.lhs} {self.op.token()} {self.rhs})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            lhs_id = self.lhs.dump(ctx)
            rhs_id = self.rhs.dump(ctx)
            if self.op == VectorBinaryExprOp.CROSS:
                return f"cross({lhs_id}, {rhs_id})"
            else:
                return f"{lhs_id} {self.op.token()} {rhs_id}"
        var_id = ctx.get_var_id(self, g)
        return var_id


class VectorDotExpr(FloatExpr):
    """Dot product of two vectors, producing a float."""

    a: VectorExpr
    b: VectorExpr

    def __init__(self, a: VectorExpr, b: VectorExpr):
        self.a = a
        self.b = b

    def __str__(self):
        return f"dot({self.a}, {self.b})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            a_id = self.a.dump(ctx)
            b_id = self.b.dump(ctx)
            return f"dot({a_id}, {b_id})"
        var_id = ctx.get_var_id(self, g)
        return var_id


class ColorBlend(str, Enum):
    MIX = "MIX",
    DARKEN = "DARKEN",
    MULTIPLY = "MULTIPLY",
    BURN = "BURN",
    LIGHTEN = "LIGHTEN",
    SCREEN = "SCREEN",
    DODGE = "DODGE",
    ADD = "ADD",
    OVERLAY = "OVERLAY",
    SOFT_LIGHT = "SOFT_LIGHT",
    LINEAR_LIGHT = "LINEAR_LIGHT",
    DIFFERENCE = "DIFFERENCE",
    EXCLUSION = "EXCLUSION",
    SUBTRACT = "SUBTRACT",
    DIVIDE = "DIVIDE",
    HUE = "HUE",
    SATURATION = "SATURATION",
    COLOR = "COLOR",
    VALUE = "VALUE",


class VectorMixColorExpr(FloatExpr):
    """Mix two input colors (as vectors) by a factor."""

    a: VectorExpr
    b: VectorExpr
    factor: FloatExpr
    blend: ColorBlend

    def __init__(self, a: VectorExpr, b: VectorExpr, factor: Floaty, blend: ColorBlend = ColorBlend.MIX):
        self.a = a
        self.b = b
        self.factor = floaty(factor)
        self.blend = blend

    def __str__(self):
        return f"mix_color({self.a}, {self.b}, {self.factor}, {self.blend.value})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            a_id = self.a.dump(ctx)
            b_id = self.b.dump(ctx)
            factor_id = self.factor.dump(ctx)
            return f"mix_color({a_id}, {b_id}, {factor_id}, {self.blend.value})"
        var_id = ctx.get_var_id(self, g)
        return var_id


class ConstructVectorExpr(VectorExpr):
    """A vector created from three floats."""

    source_x: FloatExpr
    source_y: FloatExpr
    source_z: FloatExpr

    def __init__(self, source_x: Floaty, source_y: Floaty, source_z: Floaty):
        self.source_x = floaty(source_x)
        self.source_y = floaty(source_y)
        self.source_z = floaty(source_z)

    def __str__(self):
        return f"vec({self.source_x}, {self.source_y}, {self.source_z})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            x_id = self.source_x.dump(ctx)
            y_id = self.source_y.dump(ctx)
            z_id = self.source_z.dump(ctx)
            return f"vec({x_id}, {y_id}, {z_id})"
        var_id = ctx.get_var_id(self, g)
        return var_id


class UVMapVectorExpr(VectorExpr):
    """Access a UV map."""

    uv_map_index: int

    def __init__(self, uv_map_index: int):
        self.uv_map_index = uv_map_index

    def __str__(self):
        return f"uv({self.uv_map_index})"

    def dump(self, ctx: ExprDumpContext) -> str:
        return f"uv({self.uv_map_index})"


class ParameterComponentExpr(FloatExpr):
    """Access a float component of a parameter."""

    parameter: 'ParameterExpr'
    component_index: int

    def __init__(self, parameter: 'ParameterExpr', component_index: int):
        self.parameter = parameter
        self.component_index = component_index

    def __str__(self):
        return f"{self.source}[{self.component_index}]"

    def dump(self, ctx: ExprDumpContext) -> str:
        source_id = self.source.dump(ctx)
        return f"{source_id}[{self.component_index}]"


class ParameterExpr(Expr):
    """Access a parameter."""

    parameter_name: str

    def __init__(self, parameter_name: str):
        self.parameter_name = parameter_name

    def get(self, component_index: int) -> ParameterComponentExpr:
        if not isinstance(component_index, int):
            raise TypeError("component_index must be int")

        return ParameterComponentExpr(self, component_index)

    def __getitem__(self, component_index: int) -> ParameterComponentExpr:
        return self.get(component_index)

    @property
    def x(self) -> ParameterComponentExpr:
        return self.get(0)

    @property
    def y(self) -> ParameterComponentExpr:
        return self.get(1)

    @property
    def z(self) -> ParameterComponentExpr:
        return self.get(2)

    @property
    def w(self) -> ParameterComponentExpr:
        return self.get(3)

    def __str__(self):
        return f"param('{self.parameter_name}')"

    def dump(self, ctx: ExprDumpContext) -> str:
        return f"param('{self.parameter_name}')"


class TextureExpr(Expr):
    """Sample a texture at the specified UV."""

    texture_name: str
    uv: VectorExpr

    def __init__(self, texture_name: str, uv: VectorExpr):
        self.texture_name = texture_name
        self.uv = uv

    def __str__(self):
        return f"tex('{self.texture_name}', {self.uv})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            uv_id = self.uv.dump(ctx)
            return f"tex('{self.texture_name}', {uv_id})"
        var_id = ctx.get_var_id(self, g)
        return var_id

    @property
    def color(self) -> 'TextureColorExpr':
        return TextureColorExpr(self)

    @property
    def alpha(self) -> 'TextureAlphaExpr':
        return TextureAlphaExpr(self)


class TextureColorExpr(VectorExpr):
    """Read the color component of a texture."""

    texture: TextureExpr

    def __init__(self, texture: TextureExpr):
        self.texture = texture

    def __str__(self):
        return f"{self.texture}.color"

    def dump(self, ctx: ExprDumpContext) -> str:
        texture_id = self.texture.dump(ctx)
        return f"{texture_id}.color"


class TextureAlphaExpr(FloatExpr):
    """Read the alpha component of a texture."""

    texture: TextureExpr

    def __init__(self, texture: TextureExpr):
        self.texture = texture

    def __str__(self):
        return f"{self.texture}.alpha"

    def dump(self, ctx: ExprDumpContext) -> str:
        texture_id = self.texture.dump(ctx)
        return f"{texture_id}.alpha"


class ShaderExpr(Expr, ABC):
    """Base class for expressions that produce a shader."""


class BsdfPrincipledExpr(ShaderExpr):
    """A Principled BSDF shader expression."""

    base_color: Optional[VectorExpr]
    alpha: Optional[FloatExpr]
    metallic: Optional[FloatExpr]
    roughness: Optional[FloatExpr]
    specular_ior_level: Optional[FloatExpr]
    coat_weight: Optional[FloatExpr]
    normal: Optional[VectorExpr]

    def __init__(
        self,
        base_color: Optional[VectorExpr] = None,
        alpha: Optional[Floaty] = None,
        metallic: Optional[Floaty] = None,
        roughness: Optional[Floaty] = None,
        specular_ior_level: Optional[Floaty] = None,
        coat_weight: Optional[Floaty] = None,
        normal: Optional[VectorExpr] = None,
    ):
        self.base_color = base_color
        self.alpha = optional_floaty(alpha)
        self.metallic = optional_floaty(metallic)
        self.roughness = optional_floaty(roughness)
        self.specular_ior_level = optional_floaty(specular_ior_level)
        self.coat_weight = optional_floaty(coat_weight)
        self.normal = normal

    def __str__(self):
        s = f"bsdf_principled({self.base_color}"
        first_arg = True

        def _arg(name: str):
            nonlocal s, first_arg
            expr = getattr(self, name, None)
            if expr is None:
                return

            if not first_arg:
                s += ", "
            s += f"{name}={expr}"
            first_arg = False

        _arg("base_color")
        _arg("alpha")
        _arg("metallic")
        _arg("roughness")
        _arg("specular_ior_level")
        _arg("coat_weight")
        _arg("normal")

        s += ")"
        return s

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            s = "bsdf_principled("
            first_arg = True

            def _arg(name: str):
                nonlocal s, first_arg
                expr = getattr(self, name, None)
                if expr is None:
                    return

                expr_id = expr.dump(ctx)
                if not first_arg:
                    s += ", "
                s += f"{name}={expr_id}"
                first_arg = False

            _arg("base_color")
            _arg("alpha")
            _arg("metallic")
            _arg("roughness")
            _arg("specular_ior_level")
            _arg("coat_weight")
            _arg("normal")

            s += ")"
            return s
        var_id = ctx.get_var_id(self, g)
        return var_id


class EmissionExpr(ShaderExpr):
    """A emission shader expression."""

    color: VectorExpr
    strength: FloatExpr

    def __init__(self, color: VectorExpr, strength: Floaty):
        self.color = color
        self.strength = floaty(strength)

    def __str__(self):
        return f"emission({self.color}, {self.strength})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            color_id = self.color.dump(ctx)
            strength_id = self.strength.dump(ctx)
            return f"emission({color_id}, {strength_id})"
        var_id = ctx.get_var_id(self, g)
        return var_id

class ShaderMixExpr(ShaderExpr):
    """Mix two input shaders by a factor."""

    a: ShaderExpr
    b: ShaderExpr
    factor: FloatExpr

    def __init__(self, a: ShaderExpr, b: ShaderExpr, factor: Floaty):
        self.a = a
        self.b = b
        self.factor = floaty(factor)

    def __str__(self):
        return f"mix_shader({self.a}, {self.b}, {self.factor})"

    def dump(self, ctx: ExprDumpContext) -> str:
        def g():
            a_id = self.a.dump(ctx)
            b_id = self.b.dump(ctx)
            factor_id = self.factor.dump(ctx)
            return f"mix_shader({a_id}, {b_id}, {factor_id})"
        var_id = ctx.get_var_id(self, g)
        return var_id

def dump(expr: Expr) -> str:
    """Dump the expression to a string."""
    ctx = ExprDumpContext()
    expr.dump(ctx)
    return ctx.output_text
