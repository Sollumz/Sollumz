from bpy.types import (
    Object,
    Mesh,
)
from bmesh.types import BMesh
from enum import Enum
from typing import Optional
import numpy as np
from mathutils import Vector
from ..sollumz_properties import SollumType

class NavMeshAttr(str, Enum):
    FLAG_0 = ".navmesh.flag0"
    FLAG_1 = ".navmesh.flag1"
    FLAG_2 = ".navmesh.flag2"
    FLAG_3 = ".navmesh.flag3"
    FLAG_4 = ".navmesh.flag4"
    FLAG_5 = ".navmesh.flag5"

    @property
    def type(self):
        return "INT"

    @property
    def domain(self):
        return "FACE"


def mesh_add_navmesh_attribute(mesh: Mesh, attr: NavMeshAttr):
    mesh.attributes.new(attr, attr.type, attr.domain)


def mesh_has_navmesh_attribute(mesh: Mesh, attr: NavMeshAttr) -> bool:
    return attr in mesh.attributes
