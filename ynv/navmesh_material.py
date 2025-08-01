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
    truncf,
    mix_color,
)
from ..shared.shader_expr import expr, compile_to_material
from .navmesh_attributes import NavMeshAttr

NAVMESH_MATERIAL_NAME = ".sz.navmesh"


class FlagRenderInfo(NamedTuple):
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


class ValueRenderInfo(NamedTuple):
    name: str
    data_index: int
    start_bit: int
    end_bit: int
    default_toggle: bool
    default_color_min: tuple[float, float, float]
    default_color_max: tuple[float, float, float]

    @property
    def toggle_name(self) -> str:
        return f"{self.name}__toggle"

    @property
    def color_min_name(self) -> str:
        return f"{self.name}__color_min"

    @property
    def color_max_name(self) -> str:
        return f"{self.name}__color_max"


# TODO: better default colors
ALL_FLAGS = tuple(FlagRenderInfo(*args) for args in (
    ("is_small",                   0, 1,     False, (0.0, 0.1, 0.1)),
    ("is_large",                   0, 2,     False, (0.1, 0.0, 0.1)),
    ("is_pavement",                0, 4,     True,  (0.0, 0.25, 0.0)),
    ("is_road",                    1, 2,     True,  (0.45, 0.0, 0.3)),
    ("is_near_car_node",           0, 8192,  False, (0.45, 0.0, 0.3)),
    ("is_train_track",             1, 8,     True,  (0.45, 0.0, 0.3)),
    ("is_in_shelter",              0, 8,     False, (0.0, 0.25, 0.0)),
    ("is_interior",                0, 16384, False, (0.0, 0.25, 0.0)),
    ("is_too_steep_to_walk_on",    0, 64,    True,  (0.0, 0.25, 0.0)),
    ("is_water",                   0, 128,   True,  (0.0, 0.0, 0.25)),
    ("is_shallow_water",           1, 16,    True,  (0.0, 0.0, 0.7)),
    ("is_network_spawn_candidate", 1, 1,     False, (0.15, 0.0, 0.0)),
    ("is_isolated",                0, 32768, False, (0.3, 0.0, 0.0)),
    ("lies_along_edge",            1, 4,     False, (0.3, 0.3, 0.3)),
    ("is_dlc_stitch",              2, 1,     False, (1.0, 0.0, 0.0)),
))

ALL_VALUES = tuple(ValueRenderInfo(*args) for args in (
    ("audio_reverb_size", 0,  8,  9,  False, (0.66, 0.0, 1.0), (0.08, 0.0, 0.1)),
    ("audio_reverb_wet",  0,  10, 11, False, (0.102, 0.1, 1.0), (0.002, 0.0, 0.1)),
    ("ped_density",       1,  5,  7,  True,  (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
))


def navmesh_material_shader_expr() -> expr.ShaderExpr:
    # round to avoid precision issues due to the shader interpolating values
    data0 = roundf(attribute(NavMeshAttr.POLY_DATA_0).fac)
    data1 = roundf(attribute(NavMeshAttr.POLY_DATA_1).fac)
    data2 = roundf(attribute(NavMeshAttr.POLY_DATA_2).fac)
    data = (data0, data1, data2)

    eps = 0.00001

    color = vec(0.0, 0.0, 0.0)
    for flag_info in ALL_FLAGS:
        flag_toggle = value(flag_info.toggle_name, default_value=1.0 if flag_info.default_toggle else 0.0)
        flag_color = vec_value(flag_info.color_name, default_value=flag_info.default_color)
        flag = ((data[flag_info.data_index] / (flag_info.flag_value - eps)) % 2.0) > (1.0 - eps)
        color += f2v(flag * flag_toggle) * flag_color

    for val_info in ALL_VALUES:
        val_toggle = value(val_info.toggle_name, default_value=1.0 if val_info.default_toggle else 0.0)
        val_color_min = vec_value(val_info.color_min_name, default_value=val_info.default_color_min)
        val_color_max = vec_value(val_info.color_max_name, default_value=val_info.default_color_max)

        num_bits = val_info.end_bit - val_info.start_bit + 1
        max_val = float((1 << num_bits) - 1)
        val = truncf(data[val_info.data_index] / float(1 << val_info.start_bit)) % float(1 << num_bits)
        val_normalized = (val - 1.0) / (max_val - 1.0)  # -1 because 0 = no color, 1 = min color, max_val = max color
        color += f2v((val > 0.0) * val_toggle) * mix_color(val_color_min, val_color_max, val_normalized)

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
