from enum import Enum

import numpy as np
from bpy.types import (
    Attribute,
    Mesh,
)
from mathutils import Vector


class LodLightAttr(str, Enum):
    RGBI = ".lodlights.rgbi"
    DIRECTION = ".lodlights.direction"
    FALLOFF = ".lodlights.falloff"
    FALLOFF_EXP = ".lodlights.falloff_exp"
    FLAGS = ".lodlights.flags"
    HASH = ".lodlights.hash"
    CONE_INNER_ANGLE = ".lodlights.cone_inner_angle"
    CONE_OUTER_ANGLE = ".lodlights.cone_outer_angle"
    CORONA_INTENSITY = ".lodlights.corona_intensity"

    @property
    def type(self):
        match self:
            case LodLightAttr.RGBI:
                return "BYTE_COLOR"
            case LodLightAttr.DIRECTION:
                return "FLOAT_VECTOR"
            case LodLightAttr.FALLOFF | LodLightAttr.FALLOFF_EXP:
                return "FLOAT"
            case (
                LodLightAttr.FLAGS
                | LodLightAttr.HASH
                | LodLightAttr.CONE_INNER_ANGLE
                | LodLightAttr.CONE_OUTER_ANGLE
                | LodLightAttr.CORONA_INTENSITY
            ):
                return "INT"

    @property
    def domain(self):
        return "POINT"

    @property
    def default_value(self) -> object:
        match self:
            case LodLightAttr.RGBI:
                return (1.0, 1.0, 1.0, 1.0)
            case LodLightAttr.DIRECTION:
                return Vector((0.0, 0.0, 0.0))
            case LodLightAttr.FALLOFF | LodLightAttr.FALLOFF_EXP:
                return 0.0
            case (
                LodLightAttr.FLAGS
                | LodLightAttr.HASH
                | LodLightAttr.CONE_INNER_ANGLE
                | LodLightAttr.CONE_OUTER_ANGLE
                | LodLightAttr.CORONA_INTENSITY
            ):
                return 0
            case _:
                assert False, f"Default value not set for LOD light attribute '{self}'"


def mesh_add_lod_light_attribute(mesh: Mesh, attr: LodLightAttr) -> Attribute:
    mesh_attr = mesh.attributes.get(attr, None)
    return mesh.attributes.new(attr, attr.type, attr.domain) if mesh_attr is None else mesh_attr


def mesh_has_lod_light_attribute(mesh: Mesh, attr: LodLightAttr) -> bool:
    return attr in mesh.attributes


def mesh_get_lod_light_attribute_values(mesh: Mesh, attr: LodLightAttr) -> np.ndarray:
    num = len(mesh.vertices)

    match attr.type:
        case "BYTE_COLOR":
            values = np.full((num, 4), attr.default_value, dtype=np.float32)
            prop_name = "color_srgb"
        case "FLOAT_VECTOR":
            values = np.full((num, 3), attr.default_value, dtype=np.float32)
            prop_name = "vector"
        case "FLOAT":
            values = np.full(num, attr.default_value, dtype=np.float32)
            prop_name = "value"
        case "INT":
            values = np.full(num, attr.default_value, dtype=np.int32)
            prop_name = "value"
        case _:
            assert False, f"Unhandled LOD light attribute type '{attr.type}'"

    mesh_attr = mesh.attributes.get(attr, None)
    if mesh_attr is not None:
        mesh_attr.data.foreach_get(prop_name, values.ravel())

    return values
