"""Operators to paint a mesh with a gradient between two colors. Also provides
a workspace tool.

Based on the gradient tool from Vertex Color Master by Andrew Palmer:
    https://github.com/andyp123/blender_vertex_color_master
Released under GPLv3:
    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <http://www.gnu.org/licenses/>.
    All rights reserved.

Modified and optimized to paint vertices in real-time.
"""

import math

import bpy
import gpu
import numpy as np
from bl_ui.space_statusbar import STATUSBAR_HT_header
from bpy.props import (
    BoolProperty,
    EnumProperty,
    FloatVectorProperty,
)
from bpy.types import (
    Operator,
    SpaceView3D,
    WorkSpaceTool,
)
from gpu_extras.batch import batch_for_shader
from mathutils import Color, Matrix, Vector

from ...icons import ICON_GEOM_GRADIENT
from .utils import attr_domain_size, vertex_paint_unified_colors


def _np_location_3d_to_region_2d(region, rv3d, coords):
    """Like `bpy_extras.view3d_utils.location_3d_to_region_2d` but coords
    accepts a NumPy array of 4D vectors (with 3D vectors pad them with 1s
    before passing them to this function) and returns NumPy array of 2D vectors.
    """

    prj = coords @ np.array(rv3d.perspective_matrix).T
    width_half = region.width / 2.0
    height_half = region.height / 2.0

    coords_2d = np.empty((len(coords), 2), dtype=coords.dtype)
    coords_2d = prj[:, :2] / prj[:, 3:4]  # xy / w
    coords_2d *= [width_half, height_half]
    coords_2d += [width_half, height_half]
    return coords_2d


def _np_hsv_to_rgb(h, s, v):
    h = np.asarray(h)
    s = np.asarray(s)
    v = np.asarray(v)

    i = np.trunc(h * 6.0).astype(int)
    f = (h * 6.0) - i
    p = v * (1.0 - s)
    q = v * (1.0 - s * f)
    t = v * (1.0 - s * (1.0 - f))
    i = i % 6

    rgb_cases = np.stack(
        [
            np.stack([v, t, p], axis=-1),
            np.stack([q, v, p], axis=-1),
            np.stack([p, v, t], axis=-1),
            np.stack([p, q, v], axis=-1),
            np.stack([t, p, v], axis=-1),
            np.stack([v, p, q], axis=-1),
        ],
        axis=0,
    )

    rgb = rgb_cases[i, np.arange(i.size)]
    achromatic = s == 0.0
    if np.any(achromatic):
        rgb[achromatic] = np.stack([v, v, v], axis=-1)[achromatic]

    return rgb


class SOLLUMZ_OT_vertex_paint_gradient(Operator):
    bl_idname = "sollumz.vertex_paint_gradient"
    bl_label = "Vertex Paint Gradient"
    bl_description = "Draw a line to paint a color gradient to the selected vertices"
    bl_options = {"REGISTER", "UNDO", "DEPENDS_ON_CURSOR"}
    bl_cursor_pending = "PICK_AREA"

    start_color: FloatVectorProperty(
        name="Start Color",
        subtype="COLOR_GAMMA",
        default=[1.0, 0.0, 0.0],
        description="Start color of the gradient",
        size=3,
        min=0.0,
        max=1.0,
        options={"SKIP_SAVE"},
    )

    end_color: FloatVectorProperty(
        name="End Color",
        subtype="COLOR_GAMMA",
        default=[0.0, 1.0, 0.0],
        description="End color of the gradient",
        size=3,
        min=0.0,
        max=1.0,
        options={"SKIP_SAVE"},
    )

    start_point: FloatVectorProperty(name="Start Point", size=2, options={"HIDDEN", "SKIP_SAVE"})
    end_point: FloatVectorProperty(name="End Point", size=2, options={"HIDDEN", "SKIP_SAVE"})

    type: EnumProperty(
        name="Type",
        items=(
            ("LINEAR", "Linear", ""),
            ("RADIAL", "Radial", ""),
        ),
        default="LINEAR",
        options={"SKIP_SAVE"},
    )
    use_hue_blend: BoolProperty(
        name="Use Hue Blend",
        description="Gradually blend start and end colors using full hue range instead of simple blend",
        default=False,
        options={"SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context) -> bool:
        area = context.area
        obj = context.active_object
        return area and area.type == "VIEW_3D" and obj and obj.mode == "VERTEX_PAINT" and obj.type == "MESH"

    def _paint_verts(
        self,
        context,
    ):
        start_point = Vector(self.start_point)
        end_point = Vector(self.end_point)
        start_color = self.start_color
        end_color = self.end_color

        radial = self.type == "RADIAL"
        use_hue_blend = self.use_hue_blend

        region = context.region
        rv3d = context.region_data

        obj = context.active_object
        mesh = obj.data
        color_attr = mesh.attributes.active_color

        if self._cached_data is None:
            vertex_mask = None
            loop_mask = None
            loop_vertex_index = None
            if mesh.use_paint_mask_vertex:
                vertex_mask = np.empty(len(mesh.vertices), dtype=np.bool_)
                mesh.vertices.foreach_get("select", vertex_mask.ravel())
            elif mesh.use_paint_mask:
                face_mask = np.empty(len(mesh.polygons), dtype=np.bool_)
                mesh.polygons.foreach_get("select", face_mask.ravel())
                match color_attr.domain:
                    case "POINT":
                        vertex_mask = np.empty(len(mesh.vertices), dtype=np.bool_)
                        for p in mesh.polygons:
                            for v in p.vertices:
                                vertex_mask[v] = face_mask[p.index]
                    case "CORNER":
                        loop_mask = np.empty(len(mesh.loops), dtype=np.bool_)
                        for p in mesh.polygons:
                            for loop in p.loop_indices:
                                loop_mask[loop] = face_mask[p.index]
                    case _:
                        raise AssertionError(f"Unsupported domain '{color_attr.domain}'")

                del face_mask

            if color_attr.domain == "CORNER":
                # Also need loop_vertex_index later to map vertex colors to loop colors
                loop_vertex_index = np.empty(len(mesh.loops), dtype=np.int32)
                mesh.loops.foreach_get("vertex_index", loop_vertex_index)

                if loop_mask is None and vertex_mask is not None:
                    # Build loop mask from vertex mask
                    loop_mask = vertex_mask[loop_vertex_index]

            vertex_pos = np.empty((len(mesh.vertices), 3), dtype=np.float32)
            mesh.vertices.foreach_get("co", vertex_pos.ravel())

            vertex_pos = np.pad(vertex_pos, [(0, 0), (0, 1)], mode="constant", constant_values=1.0)
            vertex_pos = vertex_pos @ np.array(obj.matrix_world).T

            # Get original color data to keep the values of the alpha channel (we only overwrite RGB)
            color_data = np.empty((attr_domain_size(mesh, color_attr), 4), dtype=np.float32)
            color_attr.data.foreach_get("color_srgb", color_data.ravel())

            # Temporary buffers where we store the final vertex colors
            colors = np.empty((len(mesh.vertices), 3), dtype=np.float32)

            self._cached_data = (vertex_pos, vertex_mask, loop_mask, loop_vertex_index, color_data, colors)
        else:
            vertex_pos, vertex_mask, loop_mask, loop_vertex_index, color_data, colors = self._cached_data

        vertex_pos_2d = _np_location_3d_to_region_2d(region, rv3d, vertex_pos)

        # Vertex transformation math
        down_vector = Vector((0, -1, 0))
        direction_vector = Vector((end_point.x - start_point.x, end_point.y - start_point.y, 0)).normalized()
        rotation = direction_vector.rotation_difference(down_vector)

        translation_matrix = Matrix.Translation(Vector((-start_point.x, -start_point.y, 0)))
        inverse_translation_matrix = translation_matrix.inverted()
        rotation_matrix = rotation.to_matrix().to_4x4()
        combined_mat = inverse_translation_matrix @ rotation_matrix @ translation_matrix

        trans_start = combined_mat @ start_point.to_4d()  # Transform drawn line : rotate it to align to horizontal line
        trans_end = combined_mat @ end_point.to_4d()
        min_y = trans_start.y
        max_y = trans_end.y

        trans_vector = trans_end - trans_start
        trans_len = trans_vector.length

        # Calculate hue, saturation and value shift for blending
        if use_hue_blend:
            start_color = Color(start_color[:3])
            end_color = Color(end_color[:3])
            c1_hue = start_color.h
            c2_hue = end_color.h
            hue_separation = c2_hue - c1_hue
            if hue_separation > 0.5:
                hue_separation = hue_separation - 1
            elif hue_separation < -0.5:
                hue_separation = hue_separation + 1
            c1_sat = start_color.s
            sat_separation = end_color.s - c1_sat
            c1_val = start_color.v
            val_separation = end_color.v - c1_val

        vertex_pos_4d = np.pad(vertex_pos_2d, ((0, 0), (0, 1)), mode="constant", constant_values=0.0)
        vertex_pos_4d = np.pad(vertex_pos_4d, ((0, 0), (0, 1)), mode="constant", constant_values=1.0)
        trans_vecs = vertex_pos_4d @ np.array(combined_mat).T
        if radial:
            cur_vectors = trans_vecs - np.array(trans_start)[np.newaxis, :]
            cur_lens = np.linalg.norm(cur_vectors, axis=1)
            t = cur_lens / trans_len
        else:
            height_trans = max_y - min_y  # Get the height of transformed vector
            if height_trans == 0.0:
                height_trans = 0.000001
            t = (trans_vecs[:, 1] - min_y) / height_trans

        np.clip(t, 0.0, 1.0, out=t)
        np.abs(t, out=t)

        if use_hue_blend:
            h = np.fmod(1.0 + c1_hue + hue_separation * t, 1.0)
            s = c1_sat + sat_separation * t
            v = c1_val + val_separation * t
            colors[:] = _np_hsv_to_rgb(h, s, v)
        else:
            s = np.array(start_color[:3])
            e = np.array(end_color[:3])
            colors[:] = s + (e - s) * t[:, np.newaxis]

        match color_attr.domain:
            case "POINT":
                if vertex_mask is None:
                    color_data[:, :3] = colors
                else:
                    color_data[vertex_mask, :3] = colors[vertex_mask]
            case "CORNER":
                if loop_mask is None:
                    color_data[:, :3] = colors[loop_vertex_index]
                else:
                    color_data[loop_mask, :3] = colors[loop_vertex_index][loop_mask]
            case _:
                raise AssertionError(f"Unsupported domain '{color_attr.domain}'")

        color_attr.data.foreach_set("color_srgb", color_data.ravel())

        mesh.update_tag()

    def _restore_verts(self, context):
        mesh = context.active_object.data
        color_attr = mesh.attributes.active_color
        color_attr.data.foreach_set("color_srgb", self._saved_color_data.ravel())

    def _axis_snap(self, start, end, delta):
        if start.x - delta < end.x < start.x + delta:
            return Vector((start.x, end.y))
        if start.y - delta < end.y < start.y + delta:
            return Vector((end.x, start.y))
        return end

    def _cleanup(self, context):
        if self._handle is not None:
            SpaceView3D.draw_handler_remove(self._handle, "WINDOW")
            self._handle = None
        context.workspace.status_text_set(None)
        STATUSBAR_HT_header.remove(self._draw_status_bar)

    def modal(self, context, event: bpy.types.Event):
        context.area.tag_redraw()

        if event.type == "SPACE":
            self._move_prev = Vector((event.mouse_region_x, event.mouse_region_y))
            self._move = event.value != "RELEASE"

        # Update gradient start/end points
        if event.type in {"MOUSEMOVE", "LEFTMOUSE"}:
            mouse_point = Vector((event.mouse_region_x, event.mouse_region_y))
            if self._move:
                # Move start and end points
                delta = mouse_point - self._move_prev
                self._move_prev = mouse_point

                start_point = Vector(self.start_point)
                end_point = Vector(self.end_point)

                start_point += delta
                end_point += delta
                self.start_point = start_point
                self.end_point = end_point
            else:
                # Update and constraint end point
                start_point = Vector(self.start_point)
                end_point = mouse_point
                if event.ctrl:
                    end_point = self._axis_snap(start_point, end_point, 20)
                self.end_point = end_point

            if end_point != start_point:
                self._paint_verts(context)

            finish = event.type == "LEFTMOUSE" and event.value == "RELEASE"
            if finish:
                self._cleanup(context)
                return {"FINISHED"}
            else:
                return {"RUNNING_MODAL"}

        # Allow camera navigation
        if event.type in {"MIDDLEMOUSE", "WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            return {"PASS_THROUGH"}

        if event.type in {"RIGHTMOUSE", "ESC"}:
            self._restore_verts(context)
            self._cleanup(context)
            return {"CANCELLED"}

        # Keep running until completed or cancelled
        return {"RUNNING_MODAL"}

    def execute(self, context):
        self._cached_data = None
        self._paint_verts(context)
        return {"FINISHED"}

    def invoke(self, context, event):
        # Store the primary and secondary color from the current brush
        colors = vertex_paint_unified_colors(context)
        self.start_color = colors.color
        self.end_color = colors.secondary_color

        # Current mouse position as starting point
        mouse_position = Vector((event.mouse_region_x, event.mouse_region_y))
        self.start_point = mouse_position
        self.end_point = mouse_position

        # Save the current color attribute data to restore it if the user cancels
        mesh = context.active_object.data
        color_attr = mesh.attributes.active_color
        self._saved_color_data = np.empty((attr_domain_size(mesh, color_attr), 4), dtype=np.float32)
        color_attr.data.foreach_get("color_srgb", self._saved_color_data.ravel())

        self._move_prev = Vector((0.0, 0.0))
        self._move = False

        self._cached_data = None

        self._handle = SpaceView3D.draw_handler_add(self._draw_gradient_callback, (), "WINDOW", "POST_PIXEL")
        context.workspace.status_text_set(" ")
        STATUSBAR_HT_header.prepend(self._draw_status_bar)

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def _draw_status_bar(self, header, context):
        layout = header.layout.row(align=True)
        layout.label(text=" Cancel", icon="EVENT_ESC")
        layout.label(text="    Move", icon="EVENT_SPACEKEY")
        layout.label(text=" Snap", icon="EVENT_CTRL")

    def _draw_gradient_callback(self):
        line_shader = gpu.shader.from_builtin("SMOOTH_COLOR")
        circle_shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        line_coords = (self.start_point, self.end_point)
        colors = (self.start_color[:] + (1.0,), self.end_color[:] + (1.0,))
        line_batch = batch_for_shader(
            line_shader,
            "LINES",
            {"pos": line_coords, "color": colors},
        )
        line_shader.bind()
        line_batch.draw(line_shader)

        if self.type == "RADIAL":
            a = Vector(line_coords[0])
            b = Vector(line_coords[1])
            radius = (b - a).length
            steps = 50
            circle_points = []
            for i in range(steps + 1):
                angle = (2.0 * math.pi * i) / steps
                point = Vector((a.x + radius * math.cos(angle), a.y + radius * math.sin(angle)))
                circle_points.append(point)

            circle_batch = batch_for_shader(circle_shader, "LINE_LOOP", {"pos": circle_points})
            circle_shader.bind()
            circle_shader.uniform_float("color", colors[1])
            circle_batch.draw(circle_shader)


class VertexPaintGradientTool(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "PAINT_VERTEX"

    bl_idname = "sollumz.vertex_paint_gradient_tool"
    bl_label = "Gradient"
    bl_description = "Paint a gradient"
    bl_icon = ICON_GEOM_GRADIENT

    bl_keymap = (
        (
            SOLLUMZ_OT_vertex_paint_gradient.bl_idname,
            {"type": "LEFTMOUSE", "value": "PRESS"},
            {"properties": []},
        ),
    )

    def draw_settings(context, layout, tool):
        row = layout.row(align=True)
        row.ui_units_x = 4
        colors = vertex_paint_unified_colors(context)
        row.prop(colors, "color", text="")
        row.prop(colors, "secondary_color", text="")

        props = tool.operator_properties(SOLLUMZ_OT_vertex_paint_gradient.bl_idname)
        row = layout.row(align=True)
        row.prop(props, "type", expand=True)
        layout.prop(props, "use_hue_blend")
