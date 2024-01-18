from .expr import (
    floaty,
    Floaty,
    FloatExpr,
    FloatConstantExpr,
    FloatMapRangeExpr,
    VectorExpr,
    VectorConstantExpr,
    VectorMixColorExpr,
    UVMapVectorExpr,
    ConstructVectorExpr,
    ParameterExpr,
    TextureExpr,
    ShaderExpr,
    BsdfPrincipledExpr,
    EmissionExpr,
    ShaderMixExpr,
)


def uv(index: int) -> UVMapVectorExpr:
    """Access a UV map."""
    assert isinstance(index, int)
    return UVMapVectorExpr(index)


def tex(texture_name: str, uv: VectorExpr) -> TextureExpr:
    """Sample a texture at the specified UV."""
    assert isinstance(texture_name, str)
    return TextureExpr(texture_name, uv)


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


def dot(a: VectorExpr, b: VectorExpr) -> FloatExpr:
    """Dot product of two vectors."""
    return a.dot(b)


def cross(a: VectorExpr, b: VectorExpr) -> VectorExpr:
    """Cross product of two vectors."""
    return a.cross(b)


def map_range(*args, **kwargs) -> FloatExpr:
    """Remap a float value from a range to a target range. See ``FloatMapRangeExpr`` for parameters."""
    return FloatMapRangeExpr(*args, **kwargs)


def mix_color(*args, **kwargs) -> VectorExpr:
    """Mix two input colors (as vectors) by a factor. See ``VectorMixColorExpr`` for parameters."""
    return VectorMixColorExpr(*args, **kwargs)


def bsdf_principled(*args, **kwargs) -> ShaderExpr:
    """Create a Principled BSDF shader. See ``BsdfPrincipledExpr`` for parameters."""
    return BsdfPrincipledExpr(*args, **kwargs)


def emission(*args, **kwargs) -> ShaderExpr:
    """Create a Emission shader. See ``EmissionExpr`` for parameters."""
    return EmissionExpr(*args, **kwargs)


def mix_shader(*args, **kwargs) -> VectorExpr:
    """Mix two input shader by a factor. See ``ShaderMixExpr`` for parameters."""
    return ShaderMixExpr(*args, **kwargs)
