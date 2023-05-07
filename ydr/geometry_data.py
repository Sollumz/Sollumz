"""Intermediate data structures for parsing Drawable geometry data"""
import bpy
from mathutils import Vector, Matrix
from traceback import format_exc
from typing import Tuple, NamedTuple, Optional
from collections import defaultdict
from dataclasses import dataclass, field
from ..tools.meshhelper import create_uv_layer, create_color_attr, get_extents_from_points, flip_uv
from ..tools.utils import float32_tuple
from ..cwxml.drawable import Bone, Geometry
from ..cwxml.shader import ShaderManager
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
    def from_vertex(vertex: NamedTuple, bone_ids: Optional[list[int]] = None):
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
            weights: dict[int, float] = {}

            for i, w in zip(blendindices, blendweights):
                if bone_ids is not None and i < len(bone_ids):
                    bone_index = bone_ids[i]
                else:
                    bone_index = i

                if w == 0 and bone_index == 0:
                    continue

                weights[bone_index] = w / 255

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
    Tangent = Tuple[float, float, float, float]
    # (vert index, weight)
    VertexGroup = Tuple[int, float]

    vertices: list[Vector] = field(default_factory=list)
    normals: list[Vector] = field(default_factory=list)
    faces: list[Face] = field(default_factory=list)
    # Material indices are mapped to faces
    material_indices: list[int] = field(default_factory=list)
    tangents: dict[int, Tangent] = field(default_factory=dict)
    uv: dict[int, dict[int, Vector2]] = field(
        default_factory=lambda: defaultdict(dict))
    colors: dict[int, dict[int, Vector2]] = field(
        default_factory=lambda: defaultdict(dict))
    # Maps bone index to (vert_index, weight)
    vertex_groups: dict[int, list[VertexGroup]
                        ] = field(default_factory=lambda: defaultdict(list))

    def add_vertex(self, vert_attrs: VertexAttributes):
        self.vertices.append(vert_attrs.position)
        vert_index = len(self.vertices) - 1

        if vert_attrs.normal:
            self.normals.append(vert_attrs.normal)

        for layer_num, color in enumerate(vert_attrs.colors):
            self.colors[layer_num][vert_index] = color

        for layer_num, pos in enumerate(vert_attrs.uv):
            self.uv[layer_num][vert_index] = pos

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
    """Builds a bpy mesh object from ``GeometryData``"""

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

        self.create_mesh_materials(mesh, materials)
        self.set_mesh_normals(mesh)
        self.set_mesh_uvs(mesh)
        self.set_mesh_vertex_colors(mesh)

        mesh.validate()

        return mesh

    def set_mesh_normals(self, mesh: bpy.types.Mesh):
        mesh.polygons.foreach_set("use_smooth", [True] * len(mesh.polygons))
        mesh.normals_split_custom_set_from_vertices(
            [Vector(normal).normalized() for normal in self.geometry_data.normals])
        mesh.use_auto_smooth = True

    def set_mesh_uvs(self, mesh: bpy.types.Mesh):
        for coords in self.geometry_data.uv.values():
            create_uv_layer(mesh, coords)

    def set_mesh_vertex_colors(self, mesh: bpy.types.Mesh):
        for colors in self.geometry_data.colors.values():
            create_color_attr(mesh, colors)

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

    def create_vertex_groups(self, obj: bpy.types.Object, bones: list[Bone]):
        """Create vertex groups for this geometry based on the number
        of bones present in the drawable skeleton."""
        for bone_index in self.geometry_data.vertex_groups.keys():
            bone_name = f"UNKNOWN_BONE.{bone_index}"

            if bones and bone_index < len(bones):
                bone_name = bones[bone_index].name

            obj.vertex_groups.new(name=bone_name)

        self.set_geometry_weights(obj)

    def set_geometry_weights(self, obj: bpy.types.Object):
        """Set weights for this geometry."""
        for i, vertex_group in enumerate(self.geometry_data.vertex_groups.values()):
            for vertex_index, weight in vertex_group:
                obj.vertex_groups[i].add([vertex_index], weight, "ADD")


class GeometryBuilder:
    """Builds ``Geometry`` cwxml object(s) from ``GeometryData``. If vertex limit is reached, multiple will be made."""

    def __init__(self, loop_triangles: list[bpy.types.MeshLoopTriangle], mesh: bpy.types.Mesh, material: bpy.types.Material, mat_index: int, vertex_groups: bpy.types.VertexGroups, bones: list[bpy.types.Bone]):
        self.loop_triangles = loop_triangles
        self.mesh = mesh
        self.material = material
        self.mat_index = mat_index
        self.vertex_groups = vertex_groups
        self.bones = bones
        self.geometry_xmls: list[Geometry] = []

        self.has_weights = False
        self.has_tangents = False
        self.num_used_uv_layers = 0

    def build(self):
        self.create_geometries()
        self.set_vertex_layout()
        self.set_extents()
        self.set_bone_ids()

        return self.geometry_xmls

    def get_vertices(self):
        """Get all vertices in the mesh as tuples ready to be added to a Geometry."""
        mesh = self.mesh

        # Map loop indices to vertices
        vertices: dict[int, tuple] = {}

        weights = self.get_weights()
        used_uvs = self.get_used_uv_layers()

        tangent_required = self.get_tangent_required()

        self.num_used_uv_layers = len(used_uvs)

        for tri in self.loop_triangles:
            for loop_index in tri.loops:
                loop = mesh.loops[loop_index]
                vert_index = loop.vertex_index
                loop_index = loop.index

                if loop_index in vertices:
                    continue

                vertex = []

                self.add_position(vertex, mesh.vertices, vert_index)

                if vert_index in weights:
                    self.add_weights(vertex, vert_index, weights)

                self.add_normal(vertex, loop)

                self.add_color_layers(vertex, loop_index,
                                      mesh.color_attributes)

                self.add_uv_layers(vertex, loop_index,
                                   mesh.uv_layers, used_uvs)

                if loop.tangent and tangent_required:
                    self.add_tangent(vertex, loop)

                vertices[loop_index] = tuple(vertex)

        return vertices

    def create_geometries(self):
        """Create ``Geometry`` objects from vertices. Vertices are split into multiple geometries if the vertex limit is passed."""
        vert_map = self.get_vertices()

        geometry_xml = self.add_geometry()
        vertices: dict[tuple, int] = {}

        limit_has_been_hit = False

        for tri in self.loop_triangles:
            # Vertex limit for geometries is 2^16 - 1 since vertex indices are 16 bit unsigned ints.
            if (len(vertices) + 3) >= 65535:
                geometry_xml = self.add_geometry()
                vertices = {}
                limit_has_been_hit = True

            for loop_index in tri.loops:
                vertex = vert_map[loop_index]

                if vertex in vertices:
                    geom_vert_index = vertices[vertex]
                else:
                    geom_vert_index = len(vertices)
                    vertices[vertex] = geom_vert_index

                    geometry_xml.vertex_buffer.data.append(vertex)

                geometry_xml.index_buffer.data.append(geom_vert_index)

        if limit_has_been_hit:
            logger.warning(
                f"Maximum vertex limit exceeded for '{self.mesh.name} - {self.material.name}'! The mesh has been split accordingly. Consider lowering the poly count.")

    def add_geometry(self):
        """Add a ``Geometry`` to ``self.geometry_xmls``."""
        geom_xml = Geometry()
        geom_xml.shader_index = self.mat_index

        self.geometry_xmls.append(geom_xml)

        return geom_xml

    def get_weights(self):
        """Get all weights and bone indices of ``mesh`` mapped by vertex index"""
        bones = self.bones

        weights: dict[int, tuple[tuple, tuple]] = defaultdict(list)
        bone_ind_by_name: dict[str, int] = {
            b.name: i for i, b in enumerate(bones)}

        for vert in self.mesh.vertices:
            if not vert.groups:
                continue

            weight_pairs = self.get_weight_pairs(vert, bone_ind_by_name)

            group_weights, group_indices = self.get_sorted_weights(
                weight_pairs)
            weights_normalized = self.normalize_weights(group_weights)

            weights[vert.index] = tuple((weights_normalized, group_indices))

        return weights

    def get_weight_pairs(self, vertex: bpy.types.MeshVertex, bone_ind_by_name: dict[str, int]):
        """Get (bone_index, weight) pairs for all vertex groups in ``vertex``."""
        vertex_groups = self.vertex_groups
        weight_pairs: list[tuple(int, float)] = []

        for i, group_element in enumerate(vertex.groups):
            if i > 4 or group_element.group >= len(vertex_groups):
                continue

            vertex_group = vertex_groups[group_element.group]
            group_name = vertex_group.name
            has_invalid_group_name = group_name not in bone_ind_by_name or group_name not in bone_ind_by_name

            if vertex_group.lock_weight or has_invalid_group_name:
                continue

            # Get index of bone affected by vertex group
            bone_index = bone_ind_by_name[group_name]
            weight_pairs.append((bone_index, group_element.weight))

        return weight_pairs

    def get_sorted_weights(self, weight_pairs: list[tuple[int, float]]):
        """Get sorted weights for vertex given (bone_index, weight) pairs."""
        # Blend weights and indices are sorted by weights in ascending order starting from the 3rd index and continues to the left
        # Why? I dont know :/
        groups_sorted = sorted(
            weight_pairs, key=lambda x: x[1], reverse=True)
        group_weights = [0, 0, 0, 0]
        group_indices = [0, 0, 0, 0]

        for i, (bone_index, weight) in enumerate(groups_sorted):
            group_weights[2 - i] = weight
            group_indices[2 - i] = bone_index

        return tuple(group_weights), tuple(group_indices)

    def normalize_weights(self, weights: tuple[float, float, float, float]):
        """Normalize weights such that their sum is 255."""
        total_weights = sum(weights)

        if total_weights == 0:
            return weights

        return tuple(int(round((w/total_weights) * 255)) for w in weights)

    def get_used_uv_layers(self):
        """Get the indices of all UV layers that do not contain all (0, 0) UV coords."""
        used_uvs: dict[int, bool] = {}
        loop_triangles = self.loop_triangles

        for tri in loop_triangles:
            for loop_index in tri.loops:
                for i, uv_layer in enumerate(self.mesh.uv_layers):
                    if i in used_uvs and used_uvs[i] == True:
                        continue

                    loop_uv = uv_layer.data[loop_index].uv

                    if loop_uv[0] != 0 or loop_uv[1] != 0:
                        used_uvs[i] = True

        return list(used_uvs.keys())

    def get_tangent_required(self):
        shader_name = self.material.shader_properties.filename
        shader = ShaderManager.shaders[shader_name]

        return shader.required_tangent

    def add_position(self, vertex: list[tuple], vertices: bpy.types.MeshVertices, vert_index: int):
        """Add Position component to ``vertex``."""
        position = tuple(vertices[vert_index].co)
        vertex.append(position)

    def add_weights(self, vertex: list[tuple], vert_index: int, weights: dict[int, tuple[tuple, tuple]]):
        """Add BlendIndices and BlendWeights to ``vertex``."""
        blend_weights = weights[vert_index][0]
        blend_indices = weights[vert_index][1]

        vertex.append(blend_weights)
        vertex.append(blend_indices)

        self.has_weights = True

    def add_normal(self, vertex: list[tuple], loop: bpy.types.MeshLoop):
        """Add Normal component to ``vertex``."""
        vertex.append(float32_tuple(loop.normal))

    def add_color_layers(self, vertex: list[tuple], loop_index: int, color_attrs: bpy.types.AttributeGroup):
        """Add color layers to ``vertex`` (i.e. Colour0, Colour1, ...)"""
        if not color_attrs:
            vertex.append((255, 255, 255, 255))
            return

        for color_layer in color_attrs:
            if color_layer.domain != "CORNER" or "TintColor" in color_layer.name:
                continue

            color = color_layer.data[loop_index].color_srgb
            color_255 = tuple(int(round(x * 255)) for x in color)

            vertex.append(color_255)

    def add_uv_layers(self, vertex: list[tuple], loop_index: int, loop_layers: bpy.types.UVLoopLayers, used_uvs: list[int]):
        """Add all UV layers to ``vertex`` (i.e. Texcoord0, Texcoord1, ...)"""
        for i in used_uvs:
            uv_layer = loop_layers[i]
            uv = uv_layer.data[loop_index].uv

            vertex.append(float32_tuple(flip_uv(uv)))

    def add_tangent(self, vertex: list[tuple], loop: bpy.types.MeshLoop):
        """Add the Tangent to ``vertex``."""
        loop_tangent = loop.tangent.to_4d()
        loop_tangent[3] = loop.bitangent_sign
        tangent = float32_tuple(loop_tangent)

        vertex.append(tangent)
        self.has_tangents = True

    def set_extents(self):
        """Set the extents for each geometry in ``self.geometry_xmls``"""
        for geom_xml in self.geometry_xmls:
            vertex_positions = [vert[0]
                                for vert in geom_xml.vertex_buffer.data]
            bbmin, bbmax = get_extents_from_points(vertex_positions)
            geom_xml.bounding_box_max = Vector(bbmax)
            geom_xml.bounding_box_min = Vector(bbmin)

    def set_bone_ids(self):
        """Set BoneIds for each geometry in ``self.geometry_xmls`` based on the number of bones."""
        for geom_xml in self.geometry_xmls:
            if self.has_weights:
                geom_xml.bone_ids = [i for i in range(len(self.bones))]
            else:
                geom_xml.bone_ids = []

    def set_vertex_layout(self):
        """Set vertex layout of each geometry in ``self.geometry_xmls``"""
        num_color_layers = len(
            [layer for layer in self.mesh.color_attributes if "TintColor" not in layer.name])

        for geom_xml in self.geometry_xmls:
            layout: list[str] = []

            layout.append("Position")

            if self.has_weights:
                layout.append("BlendWeights")
                layout.append("BlendIndices")

            layout.append("Normal")

            if num_color_layers == 0:
                layout.append("Colour0")
            else:
                for i in range(num_color_layers):
                    layout.append(f"Colour{i}")

            for i in range(self.num_used_uv_layers):
                layout.append(f"TexCoord{i}")

            if self.has_tangents:
                layout.append("Tangent")

            geom_xml.vertex_buffer.layout = layout

        return layout
