"""
Simple Wavefront .obj reader for loading Sollumz builtin models. Only supports
vertices (`v`) and triangular faces (`f` with three vertex indices).
"""

import bpy
import io
import numpy as np
from numpy.typing import NDArray
from typing import NamedTuple
from pathlib import Path


class ObjMesh(NamedTuple):
    vertices: NDArray[np.float32]
    indices: NDArray[np.uint16]

    def as_vertices_only(self) -> NDArray[np.float32]:
        return self.vertices[self.indices.flatten()]

    def as_bpy_mesh(self, name: str) -> bpy.types.Mesh:
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.vertices, [], self.indices)
        return mesh


def obj_read(obj_io: io.TextIOBase) -> ObjMesh:
    vertices = []
    indices = []
    for line in obj_io.readlines():
        line = line.strip()
        c = line[0] if len(line) > 0 else None
        match c:
            case "v":
                x, y, z = line.strip("v ").split(" ")
                vertices.extend((float(x), float(y), float(z)))
            case "f":
                v0, v1, v2 = line.strip("f ").split(" ")
                indices.extend((int(v0) - 1, int(v1) - 1, int(v2) - 1))
            case _:
                # ignore unknown/unsupported elements
                pass

    return ObjMesh(
        vertices=np.reshape(np.array(vertices, dtype=np.float32), (-1, 3)),
        indices=np.reshape(np.array(indices, dtype=np.uint16), (-1, 3))
    )


def obj_read_from_file(file_path: Path) -> ObjMesh:
    with file_path.open("r") as f:
        return obj_read(f)


def obj_read_from_str(obj_str: str) -> ObjMesh:
    with io.StringIO(obj_str) as s:
        return obj_read(s)
