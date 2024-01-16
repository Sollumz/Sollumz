from .expr import (
    floaty,
    Floaty,
    FloatExpr,
    FloatConstantExpr,
    VectorExpr,
    VectorConstantExpr,
    UVMapVectorExpr,
    ConstructVectorExpr,
    TextureExpr,
    ShaderExpr,
    BsdfPrincipledExpr,
)


def uv(index: int) -> UVMapVectorExpr:
    """Access a UV map."""
    assert isinstance(index, int)
    return UVMapVectorExpr(index)


def tex(texture_name: str, uv: VectorExpr) -> TextureExpr:
    """Sample a texture at the specified UV."""
    assert isinstance(texture_name, str)
    return TextureExpr(texture_name, uv)


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


def bsdf_principled(*args, **kwargs) -> ShaderExpr:
    """Create a Principled BSDF shader. See ``BsdfPrincipledExpr`` for parameters."""
    return BsdfPrincipledExpr(*args, **kwargs)
