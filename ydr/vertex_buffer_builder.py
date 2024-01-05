import bpy
import numpy as np
from numpy.typing import NDArray
from typing import Tuple, Optional

from ..tools.meshhelper import flip_uvs
from ..cwxml.drawable import VertexBuffer


def get_bone_by_vgroup(vgroups: bpy.types.VertexGroups, bones: list[bpy.types.Bone]):
    """
    Returns a dictionary mapping vertex group indices to bone indices.

    Parameters:
    - vgroups: A bpy.types.VertexGroups object representing the vertex groups.
    - bones: A list of bpy.types.Bone objects representing the bones.

    Returns:
    - A dictionary mapping vertex group indices to bone indices. If a vertex group name is not found in the bone indices, it is mapped to 0.
    """
    bone_ind_by_name: dict[str, int] = {
        b.name: i for i, b in enumerate(bones)}

    return {i: bone_ind_by_name[group.name] if group.name in bone_ind_by_name else 0 for i, group in enumerate(vgroups)}


from numpy import ndarray, ndarray as NDArray

def remove_arr_field(name: str, vertex_arr: NDArray) -> NDArray:
    """
    Remove a field from a structured NumPy array.

    Parameters:
        name (str): The name of the field to be removed.
        vertex_arr (ndarray): The structured NumPy array.

    Returns:
        ndarray: The modified structured NumPy array without the specified field.
    """
    names = [n for n in vertex_arr.dtype.names if n != name]
    return vertex_arr[names]
def remove_arr_field(name: str, vertex_arr: NDArray):
    names = [n for n in vertex_arr.dtype.names if n != name]
    return vertex_arr[names]


def remove_unused_colors(vertex_arr: NDArray, used_colors: set[str]) -> NDArray:
    """Remove color layers that aren't used by the shader.

    Parameters:
        vertex_arr (numpy.ndarray): The input vertex array.
        used_colors (set[str]): The set of color layers used by the shader.

    Returns:
        numpy.ndarray: The modified vertex array with unused color layers removed.
    """
    new_names = []

    for name in vertex_arr.dtype.names:
        if "Colour" in name and name not in used_colors:
            continue
        new_names.append(name)

    return vertex_arr[new_names]


def remove_unused_uvs(vertex_arr: NDArray, used_texcoords: set[str]) -> NDArray:
    """Remove UV layers that aren't used by the shader.

    Parameters:
        vertex_arr (NDArray): The input vertex array.
        used_texcoords (set[str]): A set of used texture coordinate names.

    Returns:
        NDArray: The modified vertex array with unused UV layers removed.
    """
    new_names = []

    for name in vertex_arr.dtype.names:
        if "TexCoord" in name and name not in used_texcoords:
            continue
        new_names.append(name)

    return vertex_arr[new_names]


def dedupe_and_get_indices(vertex_arr: NDArray) -> Tuple[NDArray, NDArray[np.uint32]]:
    """
    Remove duplicate vertices from the buffer and get the new vertex indices in triangle order (used for IndexBuffer).

    Parameters:
    vertex_arr (NDArray): The input vertex array.

    Returns:
    Tuple[NDArray, NDArray[np.uint32]]: A tuple containing the deduplicated vertex array and the new vertex indices in triangle order.
    """
    vertex_arr, unique_indices, inverse_indices = np.unique(
        vertex_arr, axis=0, return_index=True, return_inverse=True)

    return vertex_arr, np.arange(len(unique_indices), dtype=np.uint32)[inverse_indices]


class VertexBufferBuilder:
    """Builds Geometry vertex buffers from a mesh."""

    def __init__(self, mesh: bpy.types.Mesh, bone_by_vgroup: Optional[dict[int, int]] = None):
            """
            Initializes a VertexBufferBuilder object.

            Parameters:
                mesh (bpy.types.Mesh): The mesh object to build the vertex buffer for.
                bone_by_vgroup (Optional[dict[int, int]], optional): A dictionary mapping vertex group indices to bone indices. Defaults to None.
            """
            self.mesh = mesh

            self._bone_by_vgroup = bone_by_vgroup
            self._has_weights = bone_by_vgroup is not None

            vert_inds = np.empty(len(mesh.loops), dtype=np.uint32)
            self.mesh.loops.foreach_get("vertex_index", vert_inds)

            self._vert_inds = vert_inds

    def build(self):
            """
            Builds the vertex buffer.

            This method calculates loop triangles and split normals for the mesh,
            collects the mesh attributes, and returns a structured array from the attributes.

            Returns:
                numpy.ndarray: The structured array representing the vertex buffer.
            """
            if not self.mesh.loop_triangles:
                self.mesh.calc_loop_triangles()

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
            """Combine ``mesh_attrs`` into single structured array.

            Parameters:
                mesh_attrs (dict[str, NDArray]): A dictionary containing mesh attributes.

            Returns:
                numpy.ndarray: A structured array containing combined mesh attributes.
            """
            # Data type for vertex data structured array
            struct_dtype = [VertexBuffer.VERT_ATTR_DTYPES[attr_name]
                            for attr_name in mesh_attrs]

            vertex_arr = np.empty(len(self._vert_inds), dtype=struct_dtype)

            for attr_name, arr in mesh_attrs.items():
                vertex_arr[attr_name] = arr

            return vertex_arr
    

    def _get_positions(self):
            """
            Retrieves the positions of the vertices from the mesh.

            Returns:
                numpy.ndarray: An array containing the positions of the vertices.
            """
            positions = np.empty(len(self.mesh.vertices) * 3, dtype=np.float32)
            self.mesh.attributes["position"].data.foreach_get("vector", positions)
            positions = np.reshape(positions, (len(self.mesh.vertices), 3))

            return positions[self._vert_inds]
    

    def _get_normals(self):
            """
            Get the normals of the mesh.

            Returns:
                numpy.ndarray: An array containing the normals of the mesh.
            """
            normals = np.empty(len(self.mesh.loops) * 3, dtype=np.float32)
            self.mesh.loops.foreach_get("normal", normals)
            return np.reshape(normals, (len(self.mesh.loops), 3))
    

    def _get_weights_indices(self) -> Tuple[NDArray[np.uint32], NDArray[np.uint32]]:
            """Get all BlendWeights and BlendIndices.

            Returns:
                Tuple[NDArray[np.uint32], NDArray[np.uint32]]: A tuple containing the normalized blend weights
                and blend indices for each vertex.
            """
            num_verts = len(self.mesh.vertices)
            bone_by_vgroup = self._bone_by_vgroup

            ind_arr = np.zeros((num_verts, 4), dtype=np.uint32)
            weights_arr = np.zeros((num_verts, 4), dtype=np.float32)

            for i, vert in enumerate(self.mesh.vertices):
                for j, grp in enumerate(vert.groups):
                    if j > 3:
                        break

                    weights_arr[i][j] = grp.weight
                    ind_arr[i][j] = bone_by_vgroup[grp.group]

            weights_arr = self._normalize_weights(weights_arr)
            weights_arr, ind_arr = self._sort_weights_inds(weights_arr, ind_arr)

            weights_arr = self._convert_to_int_range(weights_arr)

            # Return on loop domain
            return weights_arr[self._vert_inds], ind_arr[self._vert_inds]
    

    def _sort_weights_inds(self, weights_arr: NDArray[np.float32], ind_arr: NDArray[np.uint32]):
            """
            Sort BlendWeights and BlendIndices.

            Parameters:
                weights_arr (NDArray[np.float32]): Array of blend weights.
                ind_arr (NDArray[np.uint32]): Array of blend indices.

            Returns:
                Tuple[NDArray[np.float32], NDArray[np.uint32]]: Tuple containing sorted blend weights and indices.
            """
            # Blend weights and indices are sorted by weights in ascending order starting from the 3rd index and continues to the left
            # Why? I dont know :/
            sort_inds = np.argsort(weights_arr, axis=1)

            # Apply sort on axis 1
            weights_sorted = np.take_along_axis(weights_arr, sort_inds, axis=1)
            ind_sorted = np.take_along_axis(ind_arr, sort_inds, axis=1)

            # Return with index shifted by 3
            return np.roll(weights_sorted, 3, axis=1), np.roll(ind_sorted, 3, axis=1)
    

    def _normalize_weights(self, weights_arr: NDArray[np.float32]) -> NDArray[np.float32]:
            """
            Normalize the weights array such that the sum of weights in each row is 1.

            Parameters:
            weights_arr (NDArray[np.float32]): The input weights array.

            Returns:
            NDArray[np.float32]: The normalized weights array.
            """
            row_sums = weights_arr.sum(axis=1, keepdims=True)
            return np.divide(weights_arr, row_sums, out=np.zeros_like(
                weights_arr), where=row_sums != 0)

    def _convert_to_int_range(self, arr: NDArray[np.float32]) -> NDArray[np.uint32]:
            """
            Convert float array from range 0-1 to range 0-255.

            Parameters:
            arr (ndarray): The input float array.

            Returns:
            ndarray: The converted array with values in the range 0-255.
            """
            return (np.rint(arr * 255)).astype(np.uint32)

    def _get_colors(self) -> list[NDArray[np.uint32]]:
            """
            Retrieves the color attributes of the mesh.

            Returns:
                A list of color layers, where each layer is a 2D array representing the colors
                for each vertex loop in the mesh. Each color is represented as a 4-component
                unsigned integer (RGBA) value.
            """
            num_loops = len(self.mesh.loops)

            def _is_valid_color_attr(attr: bpy.types.Attribute):
                return (attr.domain == "CORNER" and
                        not attr.name.startswith("TintColor") and
                        not attr.name.startswith("."))

            color_attrs = [attr for attr in self.mesh.color_attributes if _is_valid_color_attr(attr)]
            color_attrs = color_attrs[:2]

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
            """
            Retrieves UV coordinates from the mesh attributes.

            Returns:
                A list of NDArrays containing the UV coordinates.
            """
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
            """
            Calculate and return the tangents and bitangent signs for the mesh.

            Returns:
                numpy.ndarray: Array containing the tangents and bitangent signs.
            """
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
