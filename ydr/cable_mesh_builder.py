
import bpy
from bpy.types import (
    Mesh
)
import numpy as np
from numpy.typing import NDArray
from typing import NamedTuple
from mathutils import Vector
from .cable import CableAttr, mesh_add_cable_attribute
from ..shared.math import distance_point_to_line

class CablePoint:
    point_index: int
    position: Vector
    radius: float = CableAttr.RADIUS.default_value
    diffuse_factor: float = CableAttr.DIFFUSE_FACTOR.default_value
    um_scale: float = CableAttr.UM_SCALE.default_value
    phase_offset: (float, float) = CableAttr.PHASE_OFFSET.default_value
    material_index: int = 0

    def __init__(self, point_index: int, position: Vector):
        self.point_index = point_index
        self.position = position

class CablePiece(NamedTuple):
    """A series of connected points of a cable mesh, aka a single cable."""
    points: list[CablePoint]


class CableMeshBuilder:
    """Builds a bpy mesh from a structured numpy vertex array, representing a cable mesh."""

    def __init__(self, name: str, vertex_arr: NDArray, ind_arr: NDArray[np.uint], mat_inds: NDArray[np.uint], drawable_mats: list[bpy.types.Material]):
        if "Position" not in vertex_arr.dtype.names:
            raise ValueError("Vertex array must have a 'Position' field!")

        if ind_arr.ndim > 1 or ind_arr.size % 3 != 0:
            raise ValueError(
                "Indices array should be a 1D array in triangle order and it's size should be divisble by 3!")

        self.vertex_arr = vertex_arr
        self.ind_arr = ind_arr
        self.mat_inds = mat_inds

        self.name = name
        self.materials = drawable_mats
        self.has_multiple_materials = len(drawable_mats) > 1

    def build(self) -> Mesh:
        mesh = bpy.data.meshes.new(self.name)

        verts = []
        verts_radius = []
        verts_diffuse_factor = []
        verts_um_scale = []
        verts_phase_offset = []
        verts_material_index = []
        edges = []

        pieces = self._gather_pieces()
        for piece in pieces:
            first_idx = len(verts)
            last_idx = first_idx + len(piece.points) - 1

            verts.extend(p.position for p in piece.points)
            verts_radius.extend(p.radius for p in piece.points)
            verts_diffuse_factor.extend(p.diffuse_factor for p in piece.points)
            verts_um_scale.extend(p.um_scale for p in piece.points)
            # NOTE: phase offset actually stored as FLOAT_VECTOR
            verts_phase_offset.extend((p.phase_offset[0], p.phase_offset[1], 0.0) for p in piece.points)
            if self.has_multiple_materials:
                verts_material_index.extend(p.material_index for p in piece.points)
            edges.extend(zip(range(first_idx, last_idx), range(first_idx + 1, last_idx + 1)))

        mesh.from_pydata(verts, edges, [])

        self._create_mesh_materials(mesh, verts_material_index)

        mesh_add_cable_attribute(mesh, CableAttr.RADIUS)
        mesh_add_cable_attribute(mesh, CableAttr.DIFFUSE_FACTOR)
        mesh_add_cable_attribute(mesh, CableAttr.UM_SCALE)
        mesh_add_cable_attribute(mesh, CableAttr.PHASE_OFFSET)
        mesh.attributes[CableAttr.RADIUS].data.foreach_set("value", verts_radius)
        mesh.attributes[CableAttr.DIFFUSE_FACTOR].data.foreach_set("value", verts_diffuse_factor)
        mesh.attributes[CableAttr.UM_SCALE].data.foreach_set("value", verts_um_scale)
        mesh.attributes[CableAttr.PHASE_OFFSET].data.foreach_set("vector", np.array(verts_phase_offset).ravel())

        return mesh

    def _create_mesh_materials(self, mesh: bpy.types.Mesh, verts_material_index: list[int]):
        if not self.has_multiple_materials:
            # Just a single material, 
            mesh.materials.append(self.materials[0])
            return

        drawable_mat_inds = np.unique(self.mat_inds)
        # Map drawable material indices to model material indices
        model_mat_inds = np.zeros(np.max(drawable_mat_inds) + 1, dtype=np.uint32)

        for mat_ind in drawable_mat_inds:
            mesh.materials.append(self.materials[mat_ind])
            model_mat_inds[mat_ind] = len(mesh.materials) - 1

        # NOTE: we just add the material and not assign it because Blender needs faces in the mesh to assign a
        #       material, but we don't have faces.
        #       On export, we just take the material from the materials list instead
        mesh_add_cable_attribute(mesh, CableAttr.MATERIAL_INDEX)
        mesh.attributes[CableAttr.MATERIAL_INDEX].data.foreach_set("value", model_mat_inds[verts_material_index])

        # mesh.attributes.new("material_index", type="INT", domain="FACE")
        # mesh.attributes["material_index"].data.foreach_set(
        #     "value", model_mat_inds[self.mat_inds])

    def _gather_pieces(self) -> list[CablePiece]:
        pieces = []

        # Get the unique vertex positions to simplify finding the cable pieces as the same vertex can appear multiple
        # times with positive/negative radius attribute within the two triangles that connect each segment.
        # We also take the tangent into account for the cases where two or more cables share a point. In these cases,
        # the position would be the same but the direction (tangent) would be different, so we want to have different
        # vertices in Blender.
        _, uniq_index, uniq_inverse_index = np.unique(self.vertex_arr[["Position", "Normal"]],
                                                      return_index=True, return_inverse=True, axis=0)

        # Remap index array to indices in the unique vertex positions array
        ind_arr = uniq_inverse_index[self.ind_arr]
        faces = ind_arr.reshape((int(ind_arr.size / 3), 3))

        num_points = len(uniq_index)

        material_index_per_vert = [0] * num_points

        # Find which point is the next one connected to each point. The game mesh connects two points with two
        # triangles, one going forward and the next one back. Here, we simplify the repesentation to a list of
        # points instead of triangles.
        next_map = [-1] * num_points
        prev_map = [-1] * num_points
        for face_index, (v0, v1, v2) in enumerate(faces):
            if v0 == v2: # forward tri
                assert next_map[v0] == -1, "Point already connected!"
                assert prev_map[v1] == -1, "Point already connected!"
                next_map[v0] = v1
                prev_map[v1] = v0
                material_index_per_vert[v0] = self.mat_inds[face_index]
                material_index_per_vert[v1] = self.mat_inds[face_index]
            else:
                pass

        uniq_pos = self.vertex_arr["Position"][uniq_index]
        uniq_col = self.vertex_arr["Colour0"][uniq_index]
        uniq_tc = self.vertex_arr["TexCoord0"][uniq_index]

        added = [False] * num_points
        for i in range(num_points):
            if added[i]:
                # Already added to a piece, skip
                continue

            # Make sure we start at the first point of this piece, go back if we are in the middle
            point_idx = i
            while prev_map[point_idx] != -1:
                point_idx = prev_map[point_idx]

            # Build the list of points of this piece
            piece_points = [CablePoint(point_idx, Vector(uniq_pos[point_idx]))]
            added[point_idx] = True
            while next_map[point_idx] != -1:
                point_idx = next_map[point_idx]
                piece_points.append(CablePoint(point_idx, Vector(uniq_pos[point_idx])))
                added[point_idx] = True

            # Collect attributes for every point
            start = piece_points[0]
            end = piece_points[-1]
            for point in piece_points:
                r, g, _, a = uniq_col[point.point_index]
                x, y = uniq_tc[point.point_index]
                D = distance_point_to_line(start.position, end.position, point.position)

                point.phase_offset = (r / 255, g / 255)
                point.diffuse_factor = a / 255
                point.radius = abs(x)
                point.um_scale = y / D if D != 0.0 else 0.0
                point.material_index = material_index_per_vert[point.point_index]

            pieces.append(CablePiece(piece_points))

        return pieces

