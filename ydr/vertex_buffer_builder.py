import bpy
import numpy as np
from numpy.typing import NDArray
from typing import Tuple, Optional

from ..tools.meshhelper import flip_uvs
from ..cwxml.drawable import VertexBuffer


def get_bone_by_vgroup(vgroups: bpy.types.VertexGroups, bones: list[bpy.types.Bone]):
    bone_ind_by_name: dict[str, int] = {b.name: i for i, b in enumerate(bones)}

    return {i: bone_ind_by_name[group.name] if group.name in bone_ind_by_name else -1 for i, group in enumerate(vgroups)}


def remove_arr_field(name: str, vertex_arr: NDArray):
    names = [n for n in vertex_arr.dtype.names if n != name]
    return vertex_arr[names]


def remove_unused_colors(vertex_arr: NDArray, used_colors: set[str]) -> NDArray:
    """Remove color layers that aren't used by the shader"""
    new_names = []

    for name in vertex_arr.dtype.names:
        if "Colour" in name and name not in used_colors:
            continue
        new_names.append(name)

    return vertex_arr[new_names]


def remove_unused_uvs(vertex_arr: NDArray, used_texcoords: set[str]) -> NDArray:
    """Remove UV layers that aren't used by the shader"""
    new_names = []

    for name in vertex_arr.dtype.names:
        if "TexCoord" in name and name not in used_texcoords:
            continue
        new_names.append(name)

    return vertex_arr[new_names]


def dedupe_and_get_indices(vertex_arr: NDArray) -> Tuple[NDArray, NDArray[np.uint32]]:
    """Remove duplicate vertices from the buffer and get the new vertex indices in triangle order (used for IndexBuffer). Returns vertices, indices."""

    # Cannot use np.unique directly on the vertex array because it doesn't have a tolerance parameter, only checks exact
    # equality, so floating-point values that are only different due to rounding errors would not be deduplicated.
    # For example, normals calculated by Blender for the same vertex in different loops end up slightly different from
    # rounding errors, causing this vertex to appear multiple times on export.
    # So we first round the values in the vertex array and then pass it to np.unique.

    # Convert vertex array to a 2D unstructured array of float64 to be able to use np.round, it doesn't work on the
    # structured array.
    # Each vertex is converted to a float64 array by concatenating the struct fields: [x, y, z, nx, ny, nz, r, g, b, a, ...]
    vertex_arr_flatten = np.concatenate([vertex_arr[name] for name in vertex_arr.dtype.names], axis=1, dtype=np.float64)
    np.round(vertex_arr_flatten, out=vertex_arr_flatten, decimals=6)

    _, unique_indices, inverse_indices = np.unique(vertex_arr_flatten, axis=0, return_index=True, return_inverse=True)

    # Lookup the vertices in the original structured and un-rounded array
    vertex_arr = vertex_arr[unique_indices]
    index_arr = np.asarray(inverse_indices, dtype=np.uint32)
    return vertex_arr, index_arr


class VertexBufferBuilder:
    """Builds Geometry vertex buffers from a mesh."""

    def __init__(self, mesh: bpy.types.Mesh, bone_by_vgroup: Optional[dict[int, int]] = None):
        self.mesh = mesh

        self._bone_by_vgroup = bone_by_vgroup
        self._has_weights = bone_by_vgroup is not None

        vert_inds = np.empty(len(mesh.loops), dtype=np.uint32)
        self.mesh.loops.foreach_get("vertex_index", vert_inds)

        self._vert_inds = vert_inds

    def build(self):
        if not self.mesh.loop_triangles:
            self.mesh.calc_loop_triangles()

        if bpy.app.version < (4, 1, 0):
            # needed to fill mesh loops normals with custom split normals pre-4.1
            self.mesh.calc_normals_split()

        mesh_attrs = self._collect_attrs()
        return self._structured_array_from_attrs(mesh_attrs)

    def _collect_attrs(self):
        """Returns a dict mapping arrays of all GTAV vertex attributes in ``self.mesh`` stored on the loop domain."""
        mesh_attrs = {}

        mesh_attrs["Position"] = self._get_positions()

        if self._has_weights:
            blend_weights, blend_indices = self._get_weights_indices()

            mesh_attrs["BlendWeights"] = blend_weights
            mesh_attrs["BlendIndices"] = blend_indices

        mesh_attrs["Normal"] = self._get_normals()

        colors = self._get_colors()

        for i, color in enumerate(colors):
            mesh_attrs[f"Colour{i}"] = color

        uvs = self._get_uvs()

        for i, uv in enumerate(uvs):
            mesh_attrs[f"TexCoord{i}"] = uv

        mesh_attrs["Tangent"] = self._get_tangents()

        return mesh_attrs

    def _structured_array_from_attrs(self, mesh_attrs: dict[str, NDArray]):
        """Combine ``mesh_attrs`` into single structured array."""
        # Data type for vertex data structured array
        struct_dtype = [VertexBuffer.VERT_ATTR_DTYPES[attr_name]
                        for attr_name in mesh_attrs]

        vertex_arr = np.empty(len(self._vert_inds), dtype=struct_dtype)

        for attr_name, arr in mesh_attrs.items():
            vertex_arr[attr_name] = arr

        return vertex_arr

    def _get_positions(self):
        positions = np.empty(len(self.mesh.vertices) * 3, dtype=np.float32)
        self.mesh.attributes["position"].data.foreach_get("vector", positions)
        positions = np.reshape(positions, (len(self.mesh.vertices), 3))

        return positions[self._vert_inds]

    def _get_normals(self):
        normals = np.empty(len(self.mesh.loops) * 3, dtype=np.float32)
        self.mesh.loops.foreach_get("normal", normals)
        return np.reshape(normals, (len(self.mesh.loops), 3))

    def _get_weights_indices(self) -> Tuple[NDArray[np.uint32], NDArray[np.uint32]]:
        """Get all BlendWeights and BlendIndices."""
        num_verts = len(self.mesh.vertices)
        bone_by_vgroup = self._bone_by_vgroup

        ind_arr = np.zeros((num_verts, 4), dtype=np.uint32)
        weights_arr = np.zeros((num_verts, 4), dtype=np.float32)

        for i, vert in enumerate(self.mesh.vertices):
            groups = self._get_sorted_vertex_group_elements(vert)
            for j, grp in enumerate(groups):
                if j > 3:
                    break

                weights_arr[i][j] = grp.weight
                ind_arr[i][j] = bone_by_vgroup[grp.group]

        weights_arr = self._normalize_weights(weights_arr)
        weights_arr, ind_arr = self._sort_weights_inds(weights_arr, ind_arr)

        weights_arr = self._convert_to_int_range(weights_arr)
        weights_arr = self._renormalize_converted_weights(weights_arr)

        # Return on loop domain
        return weights_arr[self._vert_inds], ind_arr[self._vert_inds]

    def _get_sorted_vertex_group_elements(self, vertex: bpy.types.MeshVertex) -> list[bpy.types.VertexGroupElement]:
        elements = []
        bone_by_vgroup = self._bone_by_vgroup
        for element in vertex.groups:
            bone_index = bone_by_vgroup.get(element.group, -1)

            # skip the group that doesn't have a corresponding bone
            if bone_index == -1:
                continue

            elements.append(element)

        # sort by weight so the groups with less influence are to be ignored
        elements = sorted(elements, reverse=True, key=lambda e: e.weight)
        return elements

    def _sort_weights_inds(self, weights_arr: NDArray[np.float32], ind_arr: NDArray[np.uint32]):
        """Sort BlendWeights and BlendIndices."""
        # Blend weights and indices are sorted by weights in ascending order starting from the 3rd index and continues to the left
        # Why? I dont know :/
        sort_inds = np.argsort(weights_arr, axis=1)

        # Apply sort on axis 1
        weights_sorted = np.take_along_axis(weights_arr, sort_inds, axis=1)
        ind_sorted = np.take_along_axis(ind_arr, sort_inds, axis=1)

        # Return with index shifted by 3
        return np.roll(weights_sorted, 3, axis=1), np.roll(ind_sorted, 3, axis=1)

    def _normalize_weights(self, weights_arr: NDArray[np.float32]) -> NDArray[np.float32]:
        """Normalize weights such that their sum is 1."""
        row_sums = weights_arr.sum(axis=1, keepdims=True)
        return np.divide(weights_arr, row_sums, out=np.zeros_like(
            weights_arr), where=row_sums != 0)

    def _convert_to_int_range(self, arr: NDArray[np.float32]) -> NDArray[np.uint32]:
        """Convert float array from range 0-1 to range 0-255"""
        return (np.rint(arr * 255)).astype(np.uint32)

    def _renormalize_converted_weights(self, weights_arr: NDArray[np.uint32]) -> NDArray[np.uint32]:
        """Re-normalize converted weights to ensure their sum to be 255."""
        row_sums = weights_arr.sum(axis=1, keepdims=True)
        to_be_subtracted = np.full_like(row_sums, 255, dtype=np.int32)
        deltas = np.subtract(to_be_subtracted, row_sums)
        max_indices = weights_arr.argmax(axis=1, keepdims=True)
        max_values = weights_arr.max(axis=1, keepdims=True)
        normalized_max_values = np.add(max_values, deltas)
        result = np.copy(weights_arr)
        np.put_along_axis(result, max_indices, normalized_max_values, axis=1)
        return result

    def _get_colors(self) -> list[NDArray[np.uint32]]:
        num_loops = len(self.mesh.loops)

        def _is_valid_color_attr(attr: bpy.types.Attribute):
            return (attr.domain == "CORNER" and
                    # `TintColor` only used for the tint shaders/geometry nodes
                    not attr.name.startswith("TintColor") and
                    # Name prefixed by `.` indicate a reserved attribute name for Blender
                    # e.g. `.a_1234` for anonymous attributes
                    # https://projects.blender.org/blender/blender/issues/97452
                    not attr.name.startswith("."))

        color_attrs = [attr for attr in self.mesh.color_attributes if _is_valid_color_attr(attr)]
        # Maximum of 2 color attributes for GTAV shaders
        color_attrs = color_attrs[:2]

        # Always have at least 1 color layer
        if len(color_attrs) == 0:
            return [np.full((len(self._vert_inds), 4), 255, dtype=np.uint32)]

        color_layers = []

        for color_attr in color_attrs:
            colors = np.empty(num_loops * 4, dtype=np.float32)
            color_attr.data.foreach_get("color_srgb", colors)

            colors = self._convert_to_int_range(colors)

            color_layers.append(np.reshape(colors, (num_loops, 4)))

        return color_layers

    def _get_uvs(self) -> list[NDArray[np.float32]]:
        num_loops = len(self.mesh.loops)
        # UV mesh attributes (maximum of 8 for GTAV shaders)
        uv_attrs = [attr for attr in self.mesh.attributes if attr.data_type ==
                    'FLOAT2' and attr.domain == 'CORNER'][:8]
        uv_layers: list[NDArray[np.float32]] = []

        for uv_attr in uv_attrs:
            uvs = np.empty(num_loops * 2, dtype=np.float32)
            uv_attr.data.foreach_get("vector", uvs)
            uvs = np.reshape(uvs, (num_loops, 2))

            flip_uvs(uvs)

            uv_layers.append(uvs)

        return uv_layers

    def _get_tangents(self):
        mesh = self.mesh
        num_loops = len(mesh.loops)

        if not mesh.uv_layers:
            return np.zeros((num_loops, 4), dtype=np.float32)

        mesh.calc_tangents()

        tangents = np.empty(num_loops * 3, dtype=np.float32)
        bitangent_signs = np.empty(num_loops, dtype=np.float32)

        mesh.loops.foreach_get("tangent", tangents)
        mesh.loops.foreach_get("bitangent_sign", bitangent_signs)

        tangents = np.reshape(tangents, (num_loops, 3))
        bitangent_signs = np.reshape(bitangent_signs, (-1, 1))

        return np.concatenate((tangents, bitangent_signs), axis=1)
