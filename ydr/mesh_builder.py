import bpy
import numpy as np
from numpy.typing import NDArray
from traceback import format_exc
from ..tools.meshhelper import (
    create_uv_attr,
    create_color_attr,
    flip_uvs,
)
from .. import logger


class MeshBuilder:
    """Builds a bpy mesh from a structured numpy vertex array"""

    def __init__(self, name: str, vertex_arr: NDArray, ind_arr: NDArray[np.uint], mat_inds: NDArray[np.uint], drawable_mats: list[bpy.types.Material]):
        if "Position" not in vertex_arr.dtype.names:
            raise ValueError("Vertex array have a 'Position' field!")

        if ind_arr.ndim > 1 or ind_arr.size % 3 != 0:
            raise ValueError(
                "Indices array should be a 1D array in triangle order and it's size should be divisble by 3!")

        # Triangles using the same vertex 2+ times are not valid topology for Blender and can potentially crash/hang
        # Blender before we have a chance to call `Mesh.validate()`. Some vanilla models and, often, modded models have
        # some of these degenerate triangles, so remove them.
        faces = ind_arr.reshape((int(ind_arr.size / 3), 3))
        invalid_faces_mask = (faces[:,0] == faces[:,1]) | (faces[:,0] == faces[:,2]) | (faces[:,1] == faces[:,2])
        valid_faces_mask = ~invalid_faces_mask
        ind_arr = faces[valid_faces_mask].reshape((-1,))
        mat_inds = mat_inds[valid_faces_mask]

        self.vertex_arr = vertex_arr
        self.ind_arr = ind_arr
        self.mat_inds = mat_inds

        self.name = name
        self.materials = drawable_mats

        # Cache dtype names and attribute lists to avoid repeated iteration
        dtype_names = vertex_arr.dtype.names
        self._has_normals = "Normal" in dtype_names
        self._uv_attrs = tuple(name for name in dtype_names if name.startswith("TexCoord"))
        self._color_attrs = tuple(name for name in dtype_names if name.startswith("Colour"))
        self._has_uvs = len(self._uv_attrs) > 0
        self._has_colors = len(self._color_attrs) > 0

    def build(self):
        mesh = bpy.data.meshes.new(self.name)
        vert_pos = self.vertex_arr["Position"]
        faces = self.ind_arr.reshape((int(self.ind_arr.size / 3), 3))

        try:
            mesh.from_pydata(vert_pos, [], faces)
        except Exception:
            logger.error(
                f"Error during creation of fragment {self.name}:\n{format_exc()}\nEnsure the mesh data is not malformed."
            )
            return mesh

        self.create_mesh_materials(mesh)

        if self._has_normals:
            self.set_mesh_normals(mesh)

        if self._has_uvs:
            self.set_mesh_uvs(mesh)

        if self._has_colors:
            self.set_mesh_vertex_colors(mesh)

        mesh.validate()

        return mesh

    def create_mesh_materials(self, mesh: bpy.types.Mesh):
        drawable_mat_inds = np.unique(self.mat_inds)
        # Map drawable material indices to model material indices
        model_mat_inds = np.zeros(np.max(drawable_mat_inds) + 1, dtype=np.uint32)

        for mat_ind in drawable_mat_inds:
            mesh.materials.append(self.materials[mat_ind])
            model_mat_inds[mat_ind] = len(mesh.materials) - 1

        # Set material indices via attributes
        mesh.attributes.new("material_index", type="INT", domain="FACE")
        mesh.attributes["material_index"].data.foreach_set("value", model_mat_inds[self.mat_inds])

    def set_mesh_normals(self, mesh: bpy.types.Mesh):
        mesh.polygons.foreach_set("use_smooth", np.ones(len(mesh.polygons), dtype=bool))

        normals = self.vertex_arr["Normal"]
        lengths = np.linalg.norm(normals, axis=1, keepdims=True)
        np.divide(normals, lengths, out=normals, where=lengths != 0)
        mesh.normals_split_custom_set_from_vertices(normals)

        if bpy.app.version < (4, 1, 0):
            # needed to use custom split normals pre-4.1
            mesh.use_auto_smooth = True

    def set_mesh_uvs(self, mesh: bpy.types.Mesh):
        for attr_name in self._uv_attrs:
            uvmap_idx = int(attr_name[8:])
            uvs = self.vertex_arr[attr_name]
            flip_uvs(uvs)

            create_uv_attr(mesh, uvmap_idx, initial_values=uvs[self.ind_arr])

    def set_mesh_vertex_colors(self, mesh: bpy.types.Mesh):
        for attr_name in self._color_attrs:
            color_idx = int(attr_name[6:])
            colors = self.vertex_arr[attr_name] / 255

            create_color_attr(mesh, color_idx, initial_values=colors[self.ind_arr])

    def create_vertex_groups(self, obj: bpy.types.Object, bones: list[bpy.types.Bone]):
        def _get_vertex_group_name(bone_index: int) -> str:
            if bone_index == 99999:
                from .cloth_char import CLOTH_CHAR_VERTEX_GROUP_NAME
                return CLOTH_CHAR_VERTEX_GROUP_NAME
            elif bones and bone_index < len(bones):
                return bones[bone_index].name
            return f"UNKNOWN_BONE.{bone_index}"

        weights = self.vertex_arr["BlendWeights"] / 255  # Shape: (N, 4)
        indices = self.vertex_arr["BlendIndices"]  # Shape: (N, 4)

        num_verts = len(weights)

        # Flatten arrays for vectorized processing
        # Each vertex has 4 blend weights/indices, so we repeat vertex indices 4 times
        vert_indices = np.repeat(np.arange(num_verts, dtype=np.uint32), 4)
        flat_weights = weights.ravel()
        flat_bone_indices = indices.ravel()

        # Filter out invalid entries (zero weight with zero bone index)
        valid_mask = ~((flat_weights == 0) & (flat_bone_indices == 0))
        valid_vert_indices = vert_indices[valid_mask]
        valid_weights = flat_weights[valid_mask]
        valid_bone_indices = flat_bone_indices[valid_mask]

        # Get unique bones and create all vertex groups upfront
        unique_bones = np.unique(valid_bone_indices)
        vertex_groups: dict[int, bpy.types.VertexGroup] = {}
        for bone_idx in unique_bones:
            bone_idx_int = int(bone_idx)
            vertex_groups[bone_idx_int] = obj.vertex_groups.new(name=_get_vertex_group_name(bone_idx_int))

        # Sort by bone index to group vertices per bone
        sort_order = np.argsort(valid_bone_indices)
        sorted_bone_indices = valid_bone_indices[sort_order]
        sorted_vert_indices = valid_vert_indices[sort_order]
        sorted_weights = valid_weights[sort_order]

        # Find boundaries between different bone indices
        bone_changes = np.where(np.diff(sorted_bone_indices) != 0)[0] + 1
        bone_boundaries = np.concatenate([[0], bone_changes, [len(sorted_bone_indices)]])

        # Batch add vertices to each bone group
        for i in range(len(bone_boundaries) - 1):
            start = bone_boundaries[i]
            end = bone_boundaries[i + 1]

            bone_idx = int(sorted_bone_indices[start])
            vgroup = vertex_groups[bone_idx]

            batch_vert_indices = sorted_vert_indices[start:end]
            batch_weights = sorted_weights[start:end]

            # Group by unique weights to batch vertices with the same weight
            # vgroup.add() accepts a list of vertex indices, so we can add many at once
            unique_weights = np.unique(batch_weights)
            for weight in unique_weights:
                weight_mask = batch_weights == weight
                verts_with_weight = batch_vert_indices[weight_mask].tolist()
                vgroup.add(verts_with_weight, float(weight), "ADD")
