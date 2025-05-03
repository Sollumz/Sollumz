import bpy
from bpy.types import (
    SpaceView3D,
    Object,
)
import gpu
from gpu_extras.batch import batch_for_shader
import blf
from mathutils import Vector
from collections.abc import Sequence
from typing import NamedTuple
from ..sollumz_preferences import get_theme_settings
from .cable import (
    CableAttr,
    is_cable_mesh_object,
    mesh_get_cable_attribute_values,
)
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras.mesh_utils import edge_loops_from_edges
import bmesh


class CableOverlaysDrawHandler:
    """Manages drawing the cable overlays used to display the attributes at each vertex."""

    def __init__(self):
        self.handler_text = None
        self.handler_geometry = None

    def register(self):
        self.handler_text = SpaceView3D.draw_handler_add(self.draw_text, (), "WINDOW", "POST_PIXEL")
        self.handler_geometry = SpaceView3D.draw_handler_add(self.draw_geometry, (), "WINDOW", "POST_VIEW")

    def unregister(self):
        SpaceView3D.draw_handler_remove(self.handler_text, "WINDOW")
        SpaceView3D.draw_handler_remove(self.handler_geometry, "WINDOW")

    def can_draw_anything(self) -> bool:
        context = bpy.context
        wm = context.window_manager
        if (
            not wm.sz_ui_cable_radius_visualize and
            not wm.sz_ui_cable_diffuse_factor_visualize and
            not wm.sz_ui_cable_um_scale_visualize and
            not wm.sz_ui_cable_phase_offset_visualize and
            not wm.sz_ui_cable_material_index_visualize
        ):
            return False

        obj = context.active_object
        if not is_cable_mesh_object(obj):
            return False

        return True

    def draw_text(self):
        if not self.can_draw_anything():
            return

        context = bpy.context
        wm = context.window_manager
        obj = context.active_object

        attrs = []
        if wm.sz_ui_cable_radius_visualize:
            attrs.append(CableAttr.RADIUS)
        if wm.sz_ui_cable_diffuse_factor_visualize:
            attrs.append(CableAttr.DIFFUSE_FACTOR)
        if wm.sz_ui_cable_um_scale_visualize:
            attrs.append(CableAttr.UM_SCALE)
        if wm.sz_ui_cable_phase_offset_visualize:
            attrs.append(CableAttr.PHASE_OFFSET)
        if wm.sz_ui_cable_material_index_visualize:
            attrs.append(CableAttr.MATERIAL_INDEX)
        self.draw_attribute_values(obj, attrs)

    def draw_geometry(self):
        if not self.can_draw_anything():
            return

        context = bpy.context
        wm = context.window_manager
        obj = context.active_object

        if wm.sz_ui_cable_radius_visualize:
            self.draw_radius_geometry(obj)

    def draw_attribute_values(self, cable_obj: Object, attrs: Sequence[CableAttr]):
        context = bpy.context
        region = context.region
        rv3d = context.region_data
        mesh = cable_obj.data

        font_id = 0
        blf.size(font_id, 11)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(font_id, 2, -2)

        matrix_world = cable_obj.matrix_world

        def _draw_vertex_attributes(pos: Vector, attr_values):
            pos = matrix_world @ pos
            pos = location_3d_to_region_2d(region, rv3d, pos)
            if pos:
                for i, attr_value in enumerate(attr_values):
                    attr_type = attrs[i].type
                    if attr_type == "FLOAT_VECTOR":
                        attr_str = f"{attr_value[0]:.2f}  {attr_value[1]:.2f}"
                    elif attr_type == "INT":
                        attr_str = f"{attr_value}"
                    else:  # FLOAT
                        attr_str = f"{attr_value:.2f}"
                    w, h = blf.dimensions(font_id, attr_str)
                    attr_pos = pos - Vector((w * 0.5, h * i * 2 - (h * len(attr_values) / 2)))
                    blf.position(font_id, attr_pos.x, attr_pos.y, 0.0)
                    blf.draw(font_id, attr_str)

        if cable_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            try:
                attr_layers = [(edit_mesh.verts.layers.float_vector if attr.type == "FLOAT_VECTOR" else edit_mesh.verts.layers.int if attr.type == "INT" else edit_mesh.verts.layers.float).get(attr, None) for attr in attrs]
                for v in edit_mesh.verts:
                    attr_values = [attr.default_value if attr_layers[i] is None else v[attr_layers[i]]
                                   for i, attr in enumerate(attrs)]
                    _draw_vertex_attributes(v.co, attr_values)
            finally:
                edit_mesh.free()
        else:
            all_attr_values = [mesh_get_cable_attribute_values(mesh, attr) for attr in attrs]
            for v in mesh.vertices:
                attr_values = [all_attr_values[i][v.index] for i, attr in enumerate(attrs)]
                _draw_vertex_attributes(v.co, attr_values)

        blf.disable(font_id, blf.SHADOW)

    def draw_radius_geometry(self, cable_obj: Object):
        mesh = cable_obj.data
        if cable_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            try:
                edit_edges = [TempEditEdge((e.verts[0].index, e.verts[1].index))for e in edit_mesh.edges]
                pieces = edge_loops_from_edges(None, edges=edit_edges)
            finally:
                edit_mesh.free()
        else:
            pieces = edge_loops_from_edges(mesh)

        coords = []
        for piece in pieces:
            coords.extend(self.build_radius_geometry_for_cable_piece(cable_obj, piece))

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = batch_for_shader(shader, "LINES", {"pos": coords})
        shader.uniform_float("color", get_theme_settings().cable_overlay_radius)
        batch.draw(shader)

    def build_radius_geometry_for_cable_piece(self, cable_obj: Object, piece: list[int]) -> list[Vector]:
        """Builds the geometry to visualize the radius of this cable piece. The radius is represented with 4 lines
        around the cable mesh.
        """
        num_piece_verts = len(piece)
        mesh = cable_obj.data
        matrix_world = cable_obj.matrix_world

        num_verts_per_line = (num_piece_verts * 2 - 2)
        num_lines = 4
        coords = [None] * (num_lines * num_verts_per_line)

        def _add_piece_vertex(index_in_piece: int, pos: Vector, tangent: Vector, radius: float):
            world_up = Vector((0.0, 0.0, 1.0))
            right = tangent.cross(world_up).normalized()
            up = tangent.cross(right).normalized()
            pos = matrix_world @ pos
            va = pos + up * radius
            vb = pos - up * radius
            vc = pos + right * radius
            vd = pos - right * radius
            verts_per_line = (va, vb, vc, vd)
            if index_in_piece == 0:
                for k in range(num_lines):
                    coords[(num_verts_per_line * k) + 0] = verts_per_line[k]
            elif index_in_piece == (num_piece_verts - 1):
                for k in range(num_lines):
                    coords[(num_verts_per_line * (k + 1)) - 1] = verts_per_line[k]
            else:
                for k in range(num_lines):
                    coords[(num_verts_per_line * k) + index_in_piece * 2 - 1] = verts_per_line[k]
                    coords[(num_verts_per_line * k) + index_in_piece * 2] = verts_per_line[k]

        if cable_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            try:
                radius_layer = edit_mesh.verts.layers.float.get(CableAttr.RADIUS, None)
                prev_pos = None
                for i, vi in enumerate(piece):
                    v = edit_mesh.verts[vi]
                    radius_value = CableAttr.RADIUS.default_value if radius_layer is None else v[radius_layer]
                    if prev_pos is None:
                        if i + 1 < num_piece_verts:
                            tangent = (edit_mesh.verts[piece[i + 1]].co - v.co).normalized()
                        else:
                            tangent = Vector()
                    else:
                        tangent = (v.co - prev_pos).normalized()
                    _add_piece_vertex(i, v.co, tangent, radius_value)
                    prev_pos = v.co
            finally:
                edit_mesh.free()
        else:
            radius_values = mesh_get_cable_attribute_values(mesh, CableAttr.RADIUS)
            prev_pos = None
            for i, vi in enumerate(piece):
                v = mesh.vertices[vi]
                radius_value = radius_values[vi]
                if prev_pos is None:
                    if i + 1 < num_piece_verts:
                        tangent = (mesh.vertices[piece[i + 1]].co - v.co).normalized()
                    else:
                        tangent = Vector()
                else:
                    tangent = (v.co - prev_pos).normalized()
                _add_piece_vertex(i, v.co, tangent, radius_value)
                prev_pos = v.co

        return coords


class TempEditEdge(NamedTuple):
    """Helper class to use with ``edge_loops_from_edges``. This function expects each 'edge' to have a 'vertices' tuple
    of 2 ints, but BMesh edges don't have that layout, so we have to convert them.
    """
    vertices: tuple[int, int]


draw_handlers = []


def register():
    handler = CableOverlaysDrawHandler()
    handler.register()
    draw_handlers.append(handler)


def unregister():
    for handler in draw_handlers:
        handler.unregister()
    draw_handlers.clear()
