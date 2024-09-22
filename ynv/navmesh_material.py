import bpy
from bpy.types import (
    Material
)
from typing import NamedTuple
from ..shared.shader_expr.builtins import (
    vec,
    f2v,
    bsdf_diffuse,
    attribute,
    value,
    vec_value,
    roundf,
)
from ..shared.shader_expr import expr, compile_to_material
from .navmesh_attributes import NavMeshAttr

NAVMESH_MATERIAL_NAME = ".sz.navmesh"


class AttributeRenderInfo(NamedTuple):
    name: str
    data_index: int
    flag_value: int
    default_toggle: bool
    default_color: tuple[float, float, float]

    @property
    def toggle_name(self) -> str:
        return f"{self.name}__toggle"

    @property
    def color_name(self) -> str:
        return f"{self.name}__color"


# TODO: better default colors
ALL_ATTRIBUTES = tuple(AttributeRenderInfo(*args) for args in (
    ("is_small",                   0, 1,     False, (0.0, 0.1, 0.1)),
    ("is_large",                   0, 2,     True,  (0.1, 0.0, 0.1)),
    ("is_pavement",                0, 4,     False, (0.0, 0.25, 0.0)),
    ("is_road",                    1, 2,     False, (0.45, 0.0, 0.3)),
    ("is_near_car_node",           0, 8192,  False, (0.45, 0.0, 0.3)),
    ("is_train_track",             1, 8,     False, (0.45, 0.0, 0.3)),
    ("is_in_shelter",              0, 8,     False, (0.0, 0.25, 0.0)),
    ("is_interior",                0, 16384, False, (0.0, 0.25, 0.0)),
    ("is_too_steep_to_walk_on",    0, 64,    False, (0.0, 0.25, 0.0)),
    ("is_water",                   0, 128,   False, (0.0, 0.0, 0.95)),
    ("is_shallow_water",           1, 16,    False, (0.0, 0.0, 0.15)),
    ("is_network_spawn_candidate", 1, 1,     False, (0.15, 0.0, 0.0)),
    ("is_isolated",                0, 32768, False, (0.3, 0.0, 0.0)),
    ("lies_along_edge",            1, 4,     False, (0.3, 0.3, 0.3)),
))


def navmesh_material_shader_expr() -> expr.ShaderExpr:
    # round to avoid precision issues due to the shader interpolating values
    data0 = roundf(attribute(NavMeshAttr.POLY_DATA_0).fac)
    data1 = roundf(attribute(NavMeshAttr.POLY_DATA_1).fac)
    data = (data0, data1)

    eps = 0.00001

    color = vec(0.0, 0.0, 0.0)
    for attr in ALL_ATTRIBUTES:
        flag_toggle = value(attr.toggle_name, default_value=1.0 if attr.default_toggle else 0.0)
        flag_color = vec_value(attr.color_name, default_value=attr.default_color)
        flag = ((data[attr.data_index] / (attr.flag_value - eps)) % 2.0) > (1.0 - eps)
        color += f2v(flag * flag_toggle) * flag_color

    return bsdf_diffuse(
        color=color,
    )


def get_navmesh_material() -> Material:
    mat = bpy.data.materials.get(NAVMESH_MATERIAL_NAME, None)
    if mat is not None:
        return mat

    mat = compile_to_material(NAVMESH_MATERIAL_NAME, navmesh_material_shader_expr())

    from ..ydr.shader_materials_v2 import organize_node_tree
    organize_node_tree(mat.node_tree)

    return mat
