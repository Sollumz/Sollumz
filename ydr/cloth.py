from bpy.types import (
    Object,
    Mesh,
    Attribute,
)
from enum import Enum
from typing import Optional
import numpy as np
from ..cwxml.shader import ShaderManager
from ..sollumz_properties import SollumType


class ClothAttr(str, Enum):
    PINNED = ".cloth.pinned"
    VERTEX_WEIGHT = ".cloth.weight"
    INFLATION_SCALE = ".cloth.inflation_scale"
    FORCE_TRANSFORM = ".cloth.force_transform"
    PIN_RADIUS = ".cloth.pin_radius"

    @property
    def type(self):
        match self:
            # pinned should be "BOOLEAN" but boolean attributes are not accessible through bmesh API
            case (
                ClothAttr.PINNED |
                ClothAttr.FORCE_TRANSFORM
            ):
                return "INT"
            case (
                ClothAttr.VERTEX_WEIGHT |
                ClothAttr.INFLATION_SCALE
            ):
                return "FLOAT"
            case ClothAttr.PIN_RADIUS:
                # really just 4 independent floats, representing up to 4 pin radius sets, not a color
                return "FLOAT_COLOR"
            case _:
                assert False, f"Type not set for cloth attribute '{self}'"

    @property
    def domain(self):
        match self:
            case (
                ClothAttr.PINNED |
                ClothAttr.PIN_RADIUS |
                ClothAttr.VERTEX_WEIGHT |
                ClothAttr.INFLATION_SCALE |
                ClothAttr.FORCE_TRANSFORM
            ):
                return "POINT"
            case _:
                assert False, f"Domain not set for cloth attribute '{self}'"

    @property
    def default_value(self) -> object:
        match self:
            case (
                ClothAttr.PINNED |
                ClothAttr.FORCE_TRANSFORM
            ):
                return 0
            case ClothAttr.PIN_RADIUS:
                return (0.0, 0.0, 0.0, 0.0)
            case ClothAttr.VERTEX_WEIGHT:
                return 0.002025
            case ClothAttr.INFLATION_SCALE:
                return 0.0
            case _:
                assert False, f"Default value not set for cloth attribute '{self}'"

    @property
    def label(self) -> str:
        match self:
            case ClothAttr.PINNED:
                return "Pinned"
            case ClothAttr.PIN_RADIUS:
                return "Pin Radius"
            case ClothAttr.VERTEX_WEIGHT:
                return "Mass Per Vertex"
            case ClothAttr.INFLATION_SCALE:
                return "Inflation Scale"
            case ClothAttr.FORCE_TRANSFORM:
                return "Force Transform"
            case _:
                assert False, f"Label not set for cloth attribute '{self}'"

    @property
    def description(self) -> str:
        match self:
            case ClothAttr.PINNED:
                return "If set, the vertex will be static"
            case ClothAttr.PIN_RADIUS:
                return "Soft-pinning radius"
            case ClothAttr.VERTEX_WEIGHT:
                return "Determines how heavy each vertex of the cloth mesh is"
            case ClothAttr.INFLATION_SCALE:
                return "Determines the elasticity of each vertex in the cloth mesh"
            case ClothAttr.FORCE_TRANSFORM:
                return (
                    "Apply a transform to the force vector at this vertex. "
                    "0 = no transform, 1 = rotate right, 2 = rotate left"
                )
            case _:
                assert False, f"Description not set for cloth attribute '{self}'"


def mesh_add_cloth_attribute(mesh: Mesh, attr: ClothAttr) -> Attribute:
    mesh_attr = mesh.attributes.get(attr, None)
    return mesh.attributes.new(attr, attr.type, attr.domain) if mesh_attr is None else mesh_attr


def mesh_has_cloth_attribute(mesh: Mesh, attr: ClothAttr) -> bool:
    return attr in mesh.attributes


def mesh_get_cloth_attribute_values(mesh: Mesh, attr: ClothAttr) -> np.ndarray:
    num = 0
    match attr.domain:
        case "EDGE":
            num = len(mesh.edges)
        case "POINT":
            num = len(mesh.vertices)
        case _:
            assert False, f"Domain '{attr.domain}' not handled"

    values = np.array([attr.default_value] * num)
    mesh_attr = mesh.attributes.get(attr, None)
    if mesh_attr is not None:
        if attr.type == "FLOAT_COLOR":
            mesh_attr.data.foreach_get("color", values.ravel())
        else:
            mesh_attr.data.foreach_get("value", values)

    return values


def is_cloth_mesh_object(mesh_obj: Optional[Object]) -> bool:
    """Checks whether the mesh object is valid cloth mesh."""
    if (
        mesh_obj is None or
        mesh_obj.sollum_type not in {SollumType.DRAWABLE_MODEL, SollumType.CHARACTER_CLOTH_MESH} or
        mesh_obj.type != "MESH"
    ):
        return False

    if mesh_obj.sollum_type == SollumType.CHARACTER_CLOTH_MESH:
        # Character cloth mesh are not supposed to have any materials, so don't need to check anything else
        return True

    mesh = mesh_obj.data
    return is_cloth_mesh(mesh)


def is_cloth_mesh(mesh: Optional[Mesh]) -> bool:
    """Gets whether the mesh is valid cloth mesh."""
    if mesh is None:
        return False

    num_cloth_materials = 0
    num_other_materials = 0
    for material in mesh.materials:
        shader_def = ShaderManager.find_shader(material.shader_properties.filename)
        is_cloth_material = shader_def is not None and shader_def.is_cloth
        if is_cloth_material:
            num_cloth_materials += 1
            if num_cloth_materials > 1:
                break
        else:
            num_other_materials += 1
            break

    return num_cloth_materials == 1 and num_other_materials == 0
