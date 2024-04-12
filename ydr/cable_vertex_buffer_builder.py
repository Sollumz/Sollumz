from bpy.types import (
    Mesh
)
from mathutils import Vector
from bpy_extras.mesh_utils import edge_loops_from_edges
import numpy as np
from numpy.typing import NDArray

from ..cwxml.drawable import VertexBuffer
from ..shared.math import distance_point_to_line
from .cable import CableAttr, is_cable_mesh, mesh_get_cable_attribute_values


class CableVertexBufferBuilder:
    """Builds Geometry vertex buffers from a cable mesh."""

    def __init__(self, mesh: Mesh):
        assert is_cable_mesh(mesh), "Non-cable mesh passed to CableVertexBufferBuilder"
        self.mesh = mesh

    def build(self) -> tuple[NDArray, NDArray]:
        verts_position = np.empty((len(self.mesh.vertices), 3), dtype=np.float32)
        self.mesh.attributes["position"].data.foreach_get("vector", verts_position.ravel())
        verts_radius = mesh_get_cable_attribute_values(self.mesh, CableAttr.RADIUS)
        verts_diffuse_factor = mesh_get_cable_attribute_values(self.mesh, CableAttr.DIFFUSE_FACTOR)
        verts_um_scale = mesh_get_cable_attribute_values(self.mesh, CableAttr.UM_SCALE)
        verts_phase_offset = mesh_get_cable_attribute_values(self.mesh, CableAttr.PHASE_OFFSET)
        verts_material = mesh_get_cable_attribute_values(self.mesh, CableAttr.MATERIAL_INDEX)

        verts_phase_offset.clip(0.0, 1.0, out=verts_phase_offset)
        verts_diffuse_factor.clip(0.0, 1.0, out=verts_diffuse_factor)
        verts_material.clip(0, len(self.mesh.materials) - 1, out=verts_material)

        pieces = edge_loops_from_edges(self.mesh)

        # Each segment between two points is composed of 2 triangles (6 vertices)
        num_output_verts = sum((len(piece_vertices) - 1) * 6 for piece_vertices in pieces)

        # Vertex Layout:
        #   Position
        #   Normal = tangent
        #   Colour0
        #    r = phase offset 1
        #    g = phase offset 2
        #    b = (unused)
        #    a = diffuse, lerp factor between shader_cableDiffuse and shader_cableDiffuse2
        #   TexCoord0
        #    x = radius (signed)
        #    y = distance from line * micromovement scale (further from the line and larger scale more affected by wind)
        struct_dtype = [VertexBuffer.VERT_ATTR_DTYPES[attr_name]
                        for attr_name in ("Position", "Normal", "Colour0", "TexCoord0")]
        output_vertex_arr = np.empty(num_output_verts, dtype=struct_dtype)
        output_vertex_materials_arr = np.empty(num_output_verts, dtype=np.int32)
        v_pos = output_vertex_arr["Position"]
        v_tan = output_vertex_arr["Normal"]
        v_col = output_vertex_arr["Colour0"]
        v_tex = output_vertex_arr["TexCoord0"]

        out_vi = 0  # Current output vertex index
        for piece_vertices in pieces:
            num_vertices = len(piece_vertices)
            if num_vertices <= 1:
                # Cannot have a cable with just 1 vertex
                continue

            # Calculate tangents and distances (distance from vertex to line connecting start and end vertices)
            tangents = [None] * num_vertices
            distances = [None] * num_vertices
            start = Vector(verts_position[piece_vertices[0]])
            end = Vector(verts_position[piece_vertices[-1]])
            for i in range(num_vertices):
                vcurr = piece_vertices[i]
                pcurr = Vector(verts_position[vcurr])
                if i == 0:
                    # For the first vertex, tangent is just the direction to the next vertex
                    vnext = piece_vertices[i + 1]
                    pnext = Vector(verts_position[vnext])
                    tangent = (pnext - pcurr).normalized()
                elif i + 1 < num_vertices:
                    # For the middle points, tangent is the direction from the previous vertex to the next one
                    vprev = piece_vertices[i - 1]
                    vnext = piece_vertices[i + 1]
                    pprev = Vector(verts_position[vprev])
                    pnext = Vector(verts_position[vnext])
                    tangent = (pnext - pprev).normalized()
                else:
                    # For the last, use the direction from the previous vertex to this one
                    vprev = piece_vertices[i - 1]
                    pprev = Vector(verts_position[vprev])
                    tangent = (pcurr - pprev).normalized()

                tangents[i] = tangent

                distances[i] = distance_point_to_line(start, end, pcurr)

            # Build output vertices
            for i0 in range(num_vertices - 1):
                i1 = i0 + 1
                v0 = piece_vertices[i0]
                v1 = piece_vertices[i1]

                # First triangle (v0 -r -> v1 -r -> v0 +r)
                v_pos[out_vi] = verts_position[v0]
                v_tan[out_vi] = tangents[i0]
                v_col[out_vi][0] = int(verts_phase_offset[v0][0] * 255)
                v_col[out_vi][1] = int(verts_phase_offset[v0][1] * 255)
                v_col[out_vi][2] = 0  # unused
                v_col[out_vi][3] = int(verts_diffuse_factor[v0] * 255)
                v_tex[out_vi][0] = -verts_radius[v0]  # negative
                v_tex[out_vi][1] = distances[i0] * verts_um_scale[v0]
                output_vertex_materials_arr[out_vi] = verts_material[v0]

                v_pos[out_vi + 1] = verts_position[v1]
                v_tan[out_vi + 1] = tangents[i1]
                v_col[out_vi + 1][0] = int(verts_phase_offset[v1][0] * 255)
                v_col[out_vi + 1][1] = int(verts_phase_offset[v1][1] * 255)
                v_col[out_vi + 1][2] = 0  # unused
                v_col[out_vi + 1][3] = int(verts_diffuse_factor[v1] * 255)
                v_tex[out_vi + 1][0] = -verts_radius[v1]  # negative
                v_tex[out_vi + 1][1] = distances[i1] * verts_um_scale[v1]
                output_vertex_materials_arr[out_vi + 1] = verts_material[v1]

                #   same as first vertex but with positive radius
                output_vertex_arr[out_vi + 2] = output_vertex_arr[out_vi]
                v_tex[out_vi + 2][0] = verts_radius[v0]  # positive
                output_vertex_materials_arr[out_vi + 2] = verts_material[v0]

                # Second triangle (v0 +r -> v1 -r -> v1 +r)
                output_vertex_arr[out_vi + 3] = output_vertex_arr[out_vi + 2]
                output_vertex_arr[out_vi + 4] = output_vertex_arr[out_vi + 1]
                output_vertex_arr[out_vi + 5] = output_vertex_arr[out_vi + 1]
                v_tex[out_vi + 5][0] = verts_radius[v1]  # positive
                output_vertex_materials_arr[out_vi + 3] = output_vertex_materials_arr[out_vi + 2]
                output_vertex_materials_arr[out_vi + 4] = output_vertex_materials_arr[out_vi + 1]
                output_vertex_materials_arr[out_vi + 5] = output_vertex_materials_arr[out_vi + 1]

                out_vi += 6

        return output_vertex_arr, output_vertex_materials_arr
