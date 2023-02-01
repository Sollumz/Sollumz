"""Intermediate data structures for parsing Drawable geometry data"""
import bpy
from mathutils import Vector
from traceback import format_exc
from typing import Tuple, NamedTuple
from collections import defaultdict
from dataclasses import dataclass, field
from ..tools.meshhelper import create_uv_layer, create_vertexcolor_layer
from ..cwxml.drawable import Bone
from .. import logger


def split_indices(indices: list[int]) -> list[tuple[int, int, int]]:
    """Split list of indices into groups of 3."""
    return (tuple(indices[i:i + 3]) for i in range(0, len(indices), 3))


@dataclass(frozen=True)
class VertexAttributes:
    # TODO: Integrate directly with xml class (from_vertex wont be needed)
    position: tuple[float, float, float]
    normal: tuple[float, float, float]
    uv: tuple[tuple[float, float]]
    colors: tuple[tuple[float, float, float]]
    weights: dict[int, float]

    @staticmethod
    def from_vertex(vertex: NamedTuple):
        position = ()
        normal = ()
        uv = []
        colors = []
        weights = {}

        position = tuple(vertex.position)

        if hasattr(vertex, "normal"):
            normal = tuple(vertex.normal)

        if hasattr(vertex, "blendweights"):
            blendindices = vertex.blendindices
            blendweights = vertex.blendweights

            weights = {i: w / 255 for i,
                       w in zip(blendindices, blendweights) if not (w == 0 and i == 0)}

        for key, value in vertex._asdict().items():
            if "texcoord" in key:
                uv.append(tuple(value))
            if "colour" in key:
                colors.append(tuple(value))

        return VertexAttributes(position, normal, tuple(uv), tuple(colors), weights)

    def __hash__(self) -> int:
        return hash(self.position)


@dataclass
class GeometryData:
    Vector = Tuple[float, float, float]
    Vector2 = Tuple[float, float]
    Face = Tuple[int, int, int]
    # (vert index, weight)
    VertexGroup = Tuple[int, float]

    vertices: list[Vector] = field(default_factory=list)
    normals: list[Vector] = field(default_factory=list)
    faces: list[Face] = field(default_factory=list)
    # Material indices are mapped to faces
    material_indices: list[int] = field(default_factory=list)
    uv: dict[int, list[Vector2]] = field(
        default_factory=lambda: defaultdict(list))
    colors: dict[int, list[Vector]] = field(
        default_factory=lambda: defaultdict(list))
    vertex_groups: dict[int, list[VertexGroup]
                        ] = field(default_factory=lambda: defaultdict(list))

    def add_vertex(self, vert_attrs: VertexAttributes):
        self.vertices.append(vert_attrs.position)
        vert_index = len(self.vertices) - 1

        if vert_attrs.normal:
            self.normals.append(vert_attrs.normal)

        for layer_num, color in enumerate(vert_attrs.colors):
            self.colors[layer_num].append(color)

        for layer_num, pos in enumerate(vert_attrs.uv):
            self.uv[layer_num].append(pos)

        for bone_index, weight in vert_attrs.weights.items():
            self.vertex_groups[bone_index].append((vert_index, weight))

    def add_faces(self, indices: list[int], shader_index: int):
        for face in split_indices(indices):
            self.faces.append(face)
            self.material_indices.append(shader_index)

    def add_vertices(self, vertices: list[VertexAttributes]):
        for vertex in vertices:
            self.add_vertex(vertex)


class MeshBuilder:
    def __init__(self, geometry_data: GeometryData):
        self.geometry_data = geometry_data

    def build(self, name: str, materials: list[bpy.types.Material]):
        mesh = bpy.data.meshes.new(name)

        try:
            mesh.from_pydata(self.geometry_data.vertices,
                             [], self.geometry_data.faces)
        except Exception:
            logger.error(
                f"Error during creation of fragment {name}:\n{format_exc()}\nEnsure the mesh data is not malformed.")
            return mesh

        mesh.validate()

        self.create_mesh_materials(mesh, materials)
        self.set_mesh_normals(mesh)
        self.set_mesh_uvs(mesh)
        self.set_mesh_vertex_colors(mesh)

        return mesh

    def set_mesh_normals(self, mesh: bpy.types.Mesh):
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.normals_split_custom_set_from_vertices(
            [Vector(normal).normalized() for normal in self.geometry_data.normals])
        mesh.use_auto_smooth = True

    def set_mesh_uvs(self, mesh: bpy.types.Mesh):
        for i, coords in self.geometry_data.uv.items():
            create_uv_layer(mesh, i, coords)

    def set_mesh_vertex_colors(self, mesh: bpy.types.Mesh):
        for i, colors in self.geometry_data.colors.items():
            create_vertexcolor_layer(mesh, i, colors)

    def create_mesh_materials(self, mesh: bpy.types.Mesh, frag_materials: list[bpy.types.Material]):
        # Remap shader indices to mesh material indices
        mat_indices: dict[int, int] = {}

        for i, polygon in enumerate(mesh.polygons):
            frag_mat_index = self.geometry_data.material_indices[i]

            if frag_mat_index not in mat_indices:
                mat = frag_materials[frag_mat_index]
                mesh.materials.append(mat)
                mat_indices[frag_mat_index] = len(mesh.materials) - 1

            polygon.material_index = mat_indices[frag_mat_index]

    def create_vertex_groups(self, obj: bpy.types.Object, bones: list[Bone], bone_ids: list[int] = None):
        """Create vertex groups for this geometry based on the number
        of bones present in the drawable skeleton."""

        # Some drawables have weights defined, but no associated bones (just the bone indices).
        # This is common in mp clothing, where the weights are defined, but the bone
        # indices index the bones on the mp skeleton (which has to be acquired externally).
        # These weights will still be imported, but under the name "EXTERNAL_BONE". This will
        # allow the remaining bones to be acquired later if need be.
        bone_ids = bone_ids or []

        for bone_index in self.geometry_data.vertex_groups.keys():
            bone_name = "UNKNOWN_BONE"

            if bones and bone_index < len(bones):
                bone_name = bones[bone_index].name
            elif bone_ids and bone_index < len(bone_ids):
                bone_name = f"EXTERNAL_BONE.{bone_index}"

            obj.vertex_groups.new(name=bone_name)

        self.set_geometry_weights(obj)

    def set_geometry_weights(self, obj: bpy.types.Object):
        """Set weights for this geometry."""
        for i, vertex_group in enumerate(self.geometry_data.vertex_groups.values()):
            for vertex_index, weight in vertex_group:
                obj.vertex_groups[i].add([vertex_index], weight, "ADD")
