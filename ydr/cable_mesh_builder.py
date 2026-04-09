
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
from .. import logger


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

        uniq_pos = self.vertex_arr["Position"][uniq_index]


        # Maximum distance between a neg/pos vertex pair to be considered a corrupted pair rather than
        # two adjacent cable points.. Tuned against ~5000 vanilla cable models; real corrupted pairs have
        # displacements of ~0.05, typical segment lengths are ~0.8.
        _MAX_CORRUPTED_PAIR_DISTANCE = 0.1

        # If the pair displacement is >= this fraction of the segment length, the vertices are adjacent
        # cable points, not a corrupted pair. Set to 0.5 because real corrupted pairs have ratios ~0.06,
        # while false matches (backward tris between close adjacent points) have ratios ~1.0.
        _FALSE_MATCH_RATIO = 0.5

        # Find which point is the next one connected to each point. The game mesh connects two points with two
        # triangles, one going forward and the next one back. Here, we simplify the repesentation to a list of
        # points instead of triangles.
        next_map = [-1] * num_points
        prev_map = [-1] * num_points
        dup_map = {}  # Maps duplicate vertex index → original unique vertex index
        for face_index, (v0, v1, v2) in enumerate(faces):
            if v0 == v2:  # forward tri
                src = v0
            elif np.array_equal(uniq_pos[v0], uniq_pos[v2]):
                # Corrupted forward tri: v0 and v2 share position but divergent normals broke dedup.
                # Pick the vertex already integrated in the cable chain (has prev/next set by adjacent segment).
                # (e.g. dt1_rd1_cablemesh115623_thvy, v_35_cables1empty)
                src = v2 if (prev_map[v2] != -1 or next_map[v2] != -1) else v0
            elif np.array_equal(uniq_pos[v0], uniq_pos[v1]) and v0 != v1:
                # Bridge forward tri: v0 and v1 are at the same cable position (bridge +
                # neg/pos pair with different normals). v2 is the next cable point.
                # Direction is reversed from standard: next_map[v2] = pair_vertex.
                # (e.g. sc1_05_cablemesh28159_thvy — bridge vertex pattern)
                if prev_map[v0] != -1 or next_map[v0] != -1:
                    pair = v0
                elif prev_map[v1] != -1 or next_map[v1] != -1:
                    pair = v1
                else:
                    pair = v0
                src = v2
                v1 = pair
            elif np.linalg.norm(uniq_pos[v0] - uniq_pos[v2]) < _MAX_CORRUPTED_PAIR_DISTANCE:
                d_pair = np.linalg.norm(uniq_pos[v0] - uniq_pos[v2])
                d_seg = np.linalg.norm(uniq_pos[v0] - uniq_pos[v1])

                if v1 == v0 or v1 == v2:
                    # Degenerate: A_pos and B_neg dedupped to the same vertex.
                    # Treat as simple forward tri.
                    # (e.g. sc1_05_cablemesh28159_thvy — bridge vertex pattern)
                    src = v0 if v1 != v0 else v2
                elif d_pair >= d_seg * _FALSE_MATCH_RATIO:
                    # False match: v0 and v2 are at adjacent cable points, not a corrupted neg/pos pair.
                    # In real corrupted pairs the displacement is much smaller than the segment length.
                    # (e.g. sc1_05_cablemesh28159_thvy — backward tri between close adjacent points)
                    continue
                else:
                    # Corrupted forward tri: v0 and v2 are a neg/pos pair with slightly different
                    # positions. Keep BOTH as separate cable points, forming: first → second → v1.
                    # (e.g. sc1_rd_wireset_29)
                    has_prev_v0 = prev_map[v0] != -1
                    has_prev_v2 = prev_map[v2] != -1
                    if has_prev_v0 and has_prev_v2:
                        p0, p2 = uniq_pos[v0], uniq_pos[v2]
                        logger.warning(
                            f"Cable mesh '{self.name}': corrupted pair at "
                            f"({p0[0]:.4f}, {p0[1]:.4f}, {p0[2]:.4f}) and "
                            f"({p2[0]:.4f}, {p2[1]:.4f}, {p2[2]:.4f}) "
                            f"both already connected, skipping face. "
                            "Some geometry may be lost."
                        )
                        continue
                    elif has_prev_v0:
                        first, second = v0, v2
                    elif has_prev_v2:
                        first, second = v2, v0
                    else:
                        d0 = np.linalg.norm(uniq_pos[v0] - uniq_pos[v1])
                        d2 = np.linalg.norm(uniq_pos[v2] - uniq_pos[v1])
                        first, second = (v0, v2) if d0 >= d2 else (v2, v0)

                    if (next_map[first] != -1 or
                            prev_map[second] != -1 or next_map[second] != -1 or
                            prev_map[v1] != -1):
                        pf, ps = uniq_pos[first], uniq_pos[second]
                        logger.warning(
                            f"Cable mesh '{self.name}': cannot connect corrupted pair at "
                            f"({pf[0]:.4f}, {pf[1]:.4f}, {pf[2]:.4f}) and "
                            f"({ps[0]:.4f}, {ps[1]:.4f}, {ps[2]:.4f}), skipping face. "
                            "Some geometry may be lost."
                        )
                        continue

                    next_map[first] = second
                    prev_map[second] = first
                    next_map[second] = v1
                    prev_map[v1] = second
                    material_index_per_vert[first] = self.mat_inds[face_index]
                    material_index_per_vert[second] = self.mat_inds[face_index]
                    material_index_per_vert[v1] = self.mat_inds[face_index]
                    continue
            else:
                continue

            # Duplicate connection: exact same link already exists, skip silently.
            # (e.g. ch1_rdprops_telewrs07 — overlapping cables with identical Position+Normal)
            if next_map[src] == v1 and prev_map[v1] == src:
                continue

            # Mutual cycle: v1->src already exists, src->v1 would create A<->B loop.
            # (e.g. v_39_cable1yellow)
            if next_map[v1] == src:
                ps = uniq_pos[src]
                logger.warning(
                    f"Cable mesh '{self.name}': mutual connection at "
                    f"({ps[0]:.4f}, {ps[1]:.4f}, {ps[2]:.4f}), skipping face. "
                    "Some geometry may be lost."
                )
                continue

            # Conflicting connections: src or v1 already connected to different vertices.
            # Duplicate the already-connected vertex so each cable gets its own copy.
            # (e.g. ch3_rd1_props_ch3_11_spline091, sc1_05_cablemesh28159_thvy)
            actual_src = src
            actual_dst = v1

            if next_map[src] != -1:
                dup = num_points
                num_points += 1
                dup_map[dup] = src
                next_map.append(-1)
                prev_map.append(-1)
                material_index_per_vert.append(0)
                actual_src = dup

            if prev_map[v1] != -1:
                dup = num_points
                num_points += 1
                dup_map[dup] = v1
                next_map.append(-1)
                prev_map.append(-1)
                material_index_per_vert.append(0)
                actual_dst = dup

            next_map[actual_src] = actual_dst
            prev_map[actual_dst] = actual_src
            material_index_per_vert[actual_src] = self.mat_inds[face_index]
            material_index_per_vert[actual_dst] = self.mat_inds[face_index]

        uniq_col = self.vertex_arr["Colour0"][uniq_index]
        uniq_tc = self.vertex_arr["TexCoord0"][uniq_index]

        # Collect positions covered by connected vertices, for orphan suppression.
        num_orig = len(uniq_index)
        connected_positions = set()
        for j in range(num_points):
            if next_map[j] != -1 or prev_map[j] != -1:
                orig_j = dup_map.get(j, j)
                if orig_j < num_orig:
                    connected_positions.add(tuple(uniq_pos[orig_j].flat))

        added = [False] * num_points
        for i in range(num_points):
            if added[i]:
                # Already added to a piece, skip
                continue

            # Make sure we start at the first point of this piece, go back if we are in the middle.
            # Track visited to handle cycles in prev_map (e.g. v_39_cable1yellow).
            point_idx = i
            visited = {point_idx}
            while prev_map[point_idx] != -1:
                prev_idx = prev_map[point_idx]
                if added[prev_idx] or prev_idx in visited:
                    break
                visited.add(prev_idx)
                point_idx = prev_idx

            # Build the list of points of this piece
            orig = dup_map.get(point_idx, point_idx)
            piece_points = [CablePoint(point_idx, Vector(uniq_pos[orig]))]
            added[point_idx] = True
            while next_map[point_idx] != -1:
                next_idx = next_map[point_idx]
                if added[next_idx]:
                    break
                point_idx = next_idx
                orig = dup_map.get(point_idx, point_idx)
                piece_points.append(CablePoint(point_idx, Vector(uniq_pos[orig])))
                added[point_idx] = True

            # Skip single-point pieces — orphaned vertices from corrupted geometry
            # (e.g. apa_mp_stilts_b_bedcable2, id1_06_cables_dyn_01)
            if len(piece_points) <= 1:
                # Silently drop redundant orphans whose position is already covered by
                # a connected vertex (e.g. bridge/neg-pos duplicates at bridge positions).
                orig_orphan = dup_map.get(piece_points[0].point_index,
                                          piece_points[0].point_index)
                if orig_orphan < num_orig and tuple(uniq_pos[orig_orphan].flat) in connected_positions:
                    continue

                pos = piece_points[0].position
                logger.warning(
                    f"Cable mesh '{self.name}': removed single-point piece "
                    f"at ({pos.x:.4f}, {pos.y:.4f}, {pos.z:.4f}). "
                    "Some geometry may be lost."
                )
                continue

            # Collect attributes for every point
            start = piece_points[0]
            end = piece_points[-1]
            for point in piece_points:
                orig = dup_map.get(point.point_index, point.point_index)
                r, g, _, a = uniq_col[orig]
                x, y = uniq_tc[orig]
                D = distance_point_to_line(start.position, end.position, point.position)

                point.phase_offset = (r / 255, g / 255)
                point.diffuse_factor = a / 255
                point.radius = abs(x)
                point.um_scale = y / D if D != 0.0 else 0.0
                point.material_index = material_index_per_vert[point.point_index]

            pieces.append(CablePiece(piece_points))

        return pieces

