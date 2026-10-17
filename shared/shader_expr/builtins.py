from .expr import (
    floaty,
    Floaty,
    FloatExpr,
    FloatConstantExpr,
    FloatBinaryExpr,
    FloatBinaryExprOp,
    FloatMapRangeExpr,
    FloatUnaryExpr,
    FloatUnaryExprOp,
    VectorExpr,
    VectorConstantExpr,
    VectorMixColorExpr,
    VectorNormalMapExpr,
    UVMapVectorExpr,
    GeometryExpr,
    TangentExpr,
    FloatSocketExpr,
    ConstructVectorExpr,
    ParameterExpr,
    TextureExpr,
    ColorAttributeExpr,
    AttributeExpr,
    ShaderExpr,
    BsdfPrincipledExpr,
    BsdfDiffuseExpr,
    EmissionExpr,
    ShaderMixExpr,
    ValueExpr,
    VectorValueExpr,
)


def uv(index: int) -> UVMapVectorExpr:
    """Access a UV map."""
    assert isinstance(index, int)
    return UVMapVectorExpr(index)


def tex(texture_name: str, uv: VectorExpr) -> TextureExpr:
    """Sample a texture at the specified UV."""
    assert isinstance(texture_name, str)
    return TextureExpr(texture_name, uv)


def color_attribute(name: str) -> ColorAttributeExpr:
    """Access a color attribute."""
    assert isinstance(name, str)
    return ColorAttributeExpr(name)


def attribute(name: str) -> AttributeExpr:
    """Access an attribute."""
    assert isinstance(name, str)
    return AttributeExpr(name)


def param(parameter_name: str) -> ParameterExpr:
    """Access a parameter."""
    assert isinstance(parameter_name, str)
    return ParameterExpr(parameter_name)


def float_param(parameter_name: str) -> FloatExpr:
    return param(parameter_name).x


def vec(x: Floaty, y: Floaty, z: Floaty) -> VectorExpr:
    """Create a vector from three floats."""
    x = floaty(x)
    y = floaty(y)
    z = floaty(z)
    if all(isinstance(c, FloatConstantExpr) for c in (x, y, z)):
        return VectorConstantExpr(x.value, y.value, z.value)
    else:
        return ConstructVectorExpr(x, y, z)


def f2v(f: Floaty) -> VectorExpr:
    """Create a vector with the same value in the three components."""
    return vec(f, f, f)


def dot(a: VectorExpr, b: VectorExpr) -> FloatExpr:
    """Dot product of two vectors."""
    return a.dot(b)


def cross(a: VectorExpr, b: VectorExpr) -> VectorExpr:
    """Cross product of two vectors."""
    return a.cross(b)


def absf(value: Floaty) -> FloatExpr:
    """Absolute value of a float."""
    return FloatUnaryExpr(value, FloatUnaryExprOp.ABSOLUTE)


def float_socket(node, socket_key) -> FloatExpr:
    """Reference an output socket of an already-existing node as a float expression."""
    return FloatSocketExpr(node, socket_key)


def geometry(socket_name: str) -> GeometryExpr:
    """Access a vector output of the Geometry node, e.g. 'Incoming' or 'Normal'."""
    return GeometryExpr(socket_name)


def tangent(uv_map_index: int) -> TangentExpr:
    """The world-space tangent of a UV map."""
    return TangentExpr(uv_map_index)


def maxf(a: Floaty, b: Floaty) -> FloatExpr:
    """Maximum of two floats."""
    return FloatBinaryExpr(a, b, FloatBinaryExprOp.MAXIMUM)


def minf(a: Floaty, b: Floaty) -> FloatExpr:
    """Minimum of two floats."""
    return FloatBinaryExpr(a, b, FloatBinaryExprOp.MINIMUM)


def saturate(v: Floaty) -> FloatExpr:
    """Clamp a float to [0..1]."""
    return FloatMapRangeExpr(v, 0.0, 1.0, 0.0, 1.0, clamp=True)


def map_range(*args, **kwargs) -> FloatExpr:
    """Remap a float value from a range to a target range. See ``FloatMapRangeExpr`` for parameters."""
    return FloatMapRangeExpr(*args, **kwargs)


def roundf(value: Floaty) -> FloatExpr:
    """Round a float value."""
    return FloatUnaryExpr(value, FloatUnaryExprOp.ROUND)


def truncf(value: Floaty) -> FloatExpr:
    """Truncate a float value."""
    return FloatUnaryExpr(value, FloatUnaryExprOp.TRUNC)


def mix_color(*args, **kwargs) -> VectorExpr:
    """Mix two input colors (as vectors) by a factor. See ``VectorMixColorExpr`` for parameters."""
    return VectorMixColorExpr(*args, **kwargs)


def normal_map(*args, **kwargs) -> VectorExpr:
    """Calculate normal from an RGB normal map image, in tangent space. See ``VectorNormalMapExpr`` for parameters."""
    return VectorNormalMapExpr(*args, **kwargs)


def bsdf_principled(*args, **kwargs) -> ShaderExpr:
    """Create a Principled BSDF shader. See ``BsdfPrincipledExpr`` for parameters."""
    return BsdfPrincipledExpr(*args, **kwargs)


def bsdf_diffuse(*args, **kwargs) -> ShaderExpr:
    """Create a Diffuse BSDF shader. See ``BsdfDiffuseExpr`` for parameters."""
    return BsdfDiffuseExpr(*args, **kwargs)


def emission(*args, **kwargs) -> ShaderExpr:
    """Create a Emission shader. See ``EmissionExpr`` for parameters."""
    return EmissionExpr(*args, **kwargs)


def mix_shader(*args, **kwargs) -> VectorExpr:
    """Mix two input shader by a factor. See ``ShaderMixExpr`` for parameters."""
    return ShaderMixExpr(*args, **kwargs)


def value(*args, **kwargs) -> ValueExpr:
    """Define a value node with the given name. The name can be used to find the node in the node tree later.
    See ``ValueExpr`` for parameters.
    """
    return ValueExpr(*args, **kwargs)


def vec_value(*args, **kwargs) -> VectorValueExpr:
    """Define a vector value node with the given name. The name can be used to find the node in the node tree later.
    See ``VectorValueExpr`` for parameters.
    """
    return VectorValueExpr(*args, **kwargs)
