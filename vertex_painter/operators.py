import math
import bmesh
import bpy
import gpu
from mathutils import Color, Matrix, Vector
from ..sollumz_operators import SOLLUMZ_OT_base
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from .properties import *
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils


class SOLLUMZ_OT_paint_vertices(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint All Vertices Of Selected Object"""
    bl_idname = "sollumz.paint_vertices"
    bl_label = "Paint"
    bl_action = "Paint Vertices"

    color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    def paint_map(self, color_attr, color):
        for datum in color_attr.data:
            # Uses color_srgb to match the behavior of the old
            # vertex_colors code. Requires 3.4+.
            datum.color_srgb = color

    def paint_mesh(self, mesh, color):
        if not mesh.color_attributes:
            mesh.color_attributes.new("Color", 'BYTE_COLOR', 'CORNER')
        self.paint_map(mesh.attributes.active_color, color)

    def run(self, context):
        objs = context.selected_objects

        if len(objs) > 0:
            for obj in objs:
                if obj.sollum_type == SollumType.DRAWABLE_GEOMETRY:
                    self.paint_mesh(obj.data, self.color)
                    self.messages.append(
                        f"{obj.name} was successfully painted.")
                else:
                    self.messages.append(
                        f"{obj.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_GEOMETRY]} type.")
        else:
            self.message("No objects selected to paint.")
            return False

        return True


def copy_channel(mesh, src_vcol, dst_vcol, src_channel_idx, dst_channel_idx, swap=False,
                 dst_all_channels=False, alpha_mode='PRESERVE'):
    if dst_all_channels:
        color_size = len(src_vcol.data[0].color) if len(
            src_vcol.data) > 0 else 3
        if alpha_mode == 'OVERWRITE' or color_size < 4:
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_vcol.data[loop_index].color = [src_val] * color_size
        elif alpha_mode == 'FILL':
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_vcol.data[loop_index].color = [
                    src_val, src_val, src_val, 1.0]
        else:  # default to preserve
            for loop_index, loop in enumerate(mesh.loops):
                c = src_vcol.data[loop_index].color
                src_val = c[src_channel_idx]
                c[0] = src_val
                c[1] = src_val
                c[2] = src_val
                dst_vcol.data[loop_index].color = c
    else:
        if swap:
            for loop_index, loop in enumerate(mesh.loops):
                src_val = src_vcol.data[loop_index].color[src_channel_idx]
                dst_val = dst_vcol.data[loop_index].color[dst_channel_idx]
                dst_vcol.data[loop_index].color[dst_channel_idx] = src_val
                src_vcol.data[loop_index].color[src_channel_idx] = dst_val
        else:
            for loop_index, loop in enumerate(mesh.loops):
                dst_vcol.data[loop_index].color[dst_channel_idx] = src_vcol.data[loop_index].color[src_channel_idx]

    mesh.update()


def channel_id_to_idx(id):
    if id is red_id:
        return 0
    if id is green_id:
        return 1
    if id is blue_id:
        return 2
    if id is alpha_id:
        return 3
    # default to red
    return 0


def get_isolated_channel_ids(vcol):
    vcol_id = vcol.name
    prefix = isolate_mode_name_prefix
    prefix_len = len(prefix)

    if vcol_id.startswith(prefix) and len(vcol_id) > prefix_len + 3:
        # get vcol id from end of string
        iso_vcol_id = vcol_id[prefix_len + 3:]
        iso_channel_id = vcol_id[prefix_len + 1]  # get channel id
        if iso_channel_id in valid_channel_ids:
            return [iso_vcol_id, iso_channel_id]

    return None


def draw_gradient_callback(self, context, line_params, line_shader, circle_shader):
    line_batch = batch_for_shader(line_shader, 'LINES', {
        "pos": line_params["coords"],
        "color": line_params["colors"]})
    line_shader.bind()
    line_batch.draw(line_shader)

    if circle_shader is not None:
        a = line_params["coords"][0]
        b = line_params["coords"][1]
        radius = (b - a).length
        steps = 50
        circle_points = []
        for i in range(steps+1):
            angle = (2.0 * math.pi * i) / steps
            point = Vector((a.x + radius * math.cos(angle),
                           a.y + radius * math.sin(angle)))
            circle_points.append(point)

        circle_batch = batch_for_shader(circle_shader, 'LINE_LOOP', {
            "pos": circle_points})
        circle_shader.bind()
        circle_shader.uniform_float("color", line_params["colors"][1])
        circle_batch.draw(circle_shader)


def rgb_to_luminosity(color):
    # Y = 0.299 R + 0.587 G + 0.114 B
    return color[0] * 0.299 + color[1] * 0.587 + color[2] * 0.114


class SOLLUMZ_OT_OT_Gradient(bpy.types.Operator):
    """Draw a line with the mouse to paint a vertex color gradient"""
    bl_idname = "sollumz.gradient"
    bl_label = "Sollumz Gradient Tool"
    bl_description = "Paint vertex color gradient."
    bl_options = {"REGISTER", "UNDO"}

    _handle = None

    line_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    circle_shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

    start_color: bpy.props.FloatVectorProperty(
        name="Start Color",
        subtype='COLOR',
        default=[1.0, 0.0, 0.0],
        description="Start color of the gradient."
    )

    end_color: bpy.props.FloatVectorProperty(
        name="End Color",
        subtype='COLOR',
        default=[0.0, 1.0, 0.0],
        description="End color of the gradient."
    )

    circular_gradient: bpy.props.BoolProperty(
        name="Circular Gradient",
        description="Paint a circular gradient",
        default=False
    )

    use_hue_blend: bpy.props.BoolProperty(
        name="Use Hue Blend",
        description="Gradually blend start and end colors using full hue range instead of simple blend",
        default=False
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bpy.context.object.mode == 'VERTEX_PAINT' and obj is not None and obj.type == 'MESH'

    def paintVerts(self, context, start_point, end_point, start_color, end_color, circular_gradient=False, use_hue_blend=False):
        region = context.region
        rv3d = context.region_data

        obj = context.active_object
        mesh = obj.data

        # Create a new bmesh to work with
        bm = bmesh.new()
        bm.from_mesh(mesh)
        bm.verts.ensure_lookup_table()

        # List of structures containing 3d vertex and project 2d position of vertex
        vertex_data = None  # Will contain vert, and vert coordinates in 2d view space
        if mesh.use_paint_mask_vertex:  # Face masking not currently supported
            vertex_data = [(v, view3d_utils.location_3d_to_region_2d(
                region, rv3d, obj.matrix_world @ v.co)) for v in bm.verts if v.select]
        else:
            vertex_data = [(v, view3d_utils.location_3d_to_region_2d(
                region, rv3d, obj.matrix_world @ v.co)) for v in bm.verts]

        # Vertex transformation math
        down_vector = Vector((0, -1, 0))
        direction_vector = Vector(
            (end_point.x - start_point.x, end_point.y - start_point.y, 0)).normalized()
        rotation = direction_vector.rotation_difference(down_vector)

        translation_matrix = Matrix.Translation(
            Vector((-start_point.x, -start_point.y, 0)))
        inverse_translation_matrix = translation_matrix.inverted()
        rotation_matrix = rotation.to_matrix().to_4x4()
        combinedMat = inverse_translation_matrix @ rotation_matrix @ translation_matrix

        # Transform drawn line : rotate it to align to horizontal line
        transStart = combinedMat @ start_point.to_4d()
        transEnd = combinedMat @ end_point.to_4d()
        minY = transStart.y
        maxY = transEnd.y
        heightTrans = maxY - minY  # Get the height of transformed vector

        transVector = transEnd - transStart
        transLen = transVector.length

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

        color_layer = bm.loops.layers.color.active

        for data in vertex_data:
            vertex = data[0]
            vertCo4d = Vector((data[1].x, data[1].y, 0))
            transVec = combinedMat @ vertCo4d

            t = 0

            if circular_gradient:
                curVector = transVec.to_4d() - transStart
                curLen = curVector.length
                t = abs(max(min(curLen / transLen, 1), 0))
            else:
                t = abs(max(min((transVec.y - minY) / heightTrans, 1), 0))

            color = Color((1, 0, 0))
            if use_hue_blend:
                # Hue wraps, and fmod doesn't work with negative values
                color.h = math.fmod(1.0 + c1_hue + hue_separation * t, 1.0)
                color.s = c1_sat + sat_separation * t
                color.v = c1_val + val_separation * t
            else:
                color.r = start_color[0] + (end_color[0] - start_color[0]) * t
                color.g = start_color[1] + (end_color[1] - start_color[1]) * t
                color.b = start_color[2] + (end_color[2] - start_color[2]) * t

            if mesh.use_paint_mask:  # Masking by face
                # Get only loops that belong to selected faces
                face_loops = [
                    loop for loop in vertex.link_loops if loop.face.select]
            else:  # Masking by verts or no masking at all
                # Get remaining vert loops
                face_loops = [loop for loop in vertex.link_loops]

            for loop in face_loops:
                new_color = loop[color_layer]
                new_color[:3] = color
                loop[color_layer] = new_color

        bm.to_mesh(mesh)
        bm.free()
        bpy.ops.object.mode_set(mode='VERTEX_PAINT')

    def axis_snap(self, start, end, delta):
        if start.x - delta < end.x < start.x + delta:
            return Vector((start.x, end.y))
        if start.y - delta < end.y < start.y + delta:
            return Vector((end.x, start.y))
        return end

    def modal(self, context, event):
        context.area.tag_redraw()

        # Begin gradient line and initialize draw handler
        if self._handle is None:
            if event.type == 'LEFTMOUSE':
                # Store the foreground and background color for redo
                brush = context.tool_settings.vertex_paint.brush
                self.start_color = brush.color
                self.end_color = brush.secondary_color

                # Create arguments to pass to the draw handler callback
                mouse_position = Vector(
                    (event.mouse_region_x, event.mouse_region_y))
                self.line_params = {
                    "coords": [mouse_position, mouse_position],
                    "colors": [brush.color[:] + (1.0,),
                               brush.secondary_color[:] + (1.0,)],
                    "width": 1,  # currently does nothing
                }
                args = (self, context, self.line_params, self.line_shader,
                        (self.circle_shader if self.circular_gradient else None))
                self._handle = bpy.types.SpaceView3D.draw_handler_add(
                    draw_gradient_callback, args, 'WINDOW', 'POST_PIXEL')
        else:
            # Update or confirm gradient end point
            if event.type in {'MOUSEMOVE', 'LEFTMOUSE'}:
                line_params = self.line_params
                delta = 20

                # Update and constrain end point
                start_point = line_params["coords"][0]
                end_point = Vector(
                    (event.mouse_region_x, event.mouse_region_y))
                if event.shift:
                    end_point = self.axis_snap(start_point, end_point, delta)
                line_params["coords"] = [start_point, end_point]

                # Finish updating the line and paint the vertices
                if event.type == 'LEFTMOUSE' and end_point != start_point:
                    bpy.types.SpaceView3D.draw_handler_remove(
                        self._handle, 'WINDOW')
                    self._handle = None

                    # Gradient will not work if there is no delta
                    if end_point == start_point:
                        return {'CANCELLED'}

                    # Use color gradient or force grayscale in isolate mode
                    start_color = line_params["colors"][0]
                    end_color = line_params["colors"][1]
                    isolate = get_isolated_channel_ids(
                        context.active_object.data.vertex_colors.active)
                    use_hue_blend = self.use_hue_blend
                    if isolate is not None:
                        start_color = [rgb_to_luminosity(start_color)] * 3
                        end_color = [rgb_to_luminosity(end_color)] * 3
                        use_hue_blend = False

                    self.paintVerts(context, start_point, end_point, start_color,
                                    end_color, self.circular_gradient, use_hue_blend)
                    return {'FINISHED'}

        # Allow camera navigation
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            if self._handle is not None:
                bpy.types.SpaceView3D.draw_handler_remove(
                    self._handle, 'WINDOW')
                self._handle = None
            return {'CANCELLED'}

        # Keep running until completed or cancelled
        return {'RUNNING_MODAL'}

    def execute(self, context):
        start_point = self.line_params["coords"][0]
        end_point = self.line_params["coords"][1]
        start_color = self.start_color
        end_color = self.end_color

        # Use color gradient or force grayscale in isolate mode
        isolate = get_isolated_channel_ids(
            context.active_object.data.vertex_colors.active)
        use_hue_blend = self.use_hue_blend
        if isolate is not None:
            start_color = [rgb_to_luminosity(start_color)] * 3
            end_color = [rgb_to_luminosity(end_color)] * 3
            use_hue_blend = False

        self.paintVerts(context, start_point, end_point, start_color,
                        end_color, self.circular_gradient, use_hue_blend)

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


class SOLLUMZ_OT_IsolateChannel(SOLLUMZ_OT_base, bpy.types.Operator):
    """Isolate a specific channel to paint in grayscale"""
    bl_idname = 'sollumz.isolate_channel'
    bl_label = 'Isolate Channel'
    bl_options = {'REGISTER', 'UNDO'}

    src_channel_id: bpy.props.EnumProperty(
        name="Source Channel",
        items=channel_items,
        description="Source (Src) color channel."
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bpy.context.object.mode == 'VERTEX_PAINT' and obj is not None and obj.type == 'MESH'

    def execute(self, context):
        settings = context.scene.sollumz_vpaint_settings
        obj = context.active_object
        mesh = obj.data

        if mesh.vertex_colors is None:
            self.report(
                {'ERROR'}, "Mesh has no vertex color layer to isolate.")
            return {'FINISHED'}

        vcol = mesh.vertex_colors.active
        iso_vcol_id = "{0}_{1}_{2}".format(
            isolate_mode_name_prefix, self.src_channel_id, vcol.name)
        if iso_vcol_id in mesh.vertex_colors:
            error = "{0} Channel has already been isolated to {1}. Apply or Discard before isolating again.".format(
                self.src_channel_id, iso_vcol_id)
            self.report({'ERROR'}, error)
            return {'FINISHED'}

        iso_vcol = mesh.vertex_colors.new()
        iso_vcol.name = iso_vcol_id
        channel_idx = channel_id_to_idx(self.src_channel_id)

        copy_channel(mesh, vcol, iso_vcol, channel_idx, channel_idx,
                     dst_all_channels=True, alpha_mode='FILL')
        mesh.vertex_colors.active = iso_vcol
        brush = context.tool_settings.vertex_paint.brush
        settings.brush_color = brush.color
        settings.brush_secondary_color = brush.secondary_color
        brush.color = [settings.brush_value_isolate] * 3
        brush.secondary_color = [settings.brush_secondary_value_isolate] * 3

        return {'FINISHED'}


class SOLLUMZ_OT_ApplyIsolatedChannel(SOLLUMZ_OT_base, bpy.types.Operator):
    """Apply isolated channel back to the vertex color layer it came from"""
    bl_idname = 'sollumz.apply_isolated'
    bl_label = "Apply Isolated Channel"
    bl_options = {'REGISTER', 'UNDO'}

    discard: bpy.props.BoolProperty(
        name="Discard Changes",
        default=False,
        description="Discard changes to the isolated channel instead of applying them."
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj is not None and obj.type == 'MESH' and obj.data.vertex_colors is not None:
            vcol = obj.data.vertex_colors.active
            # operator will not work if the active vcol name doesn't match the right template
            vcol_info = get_isolated_channel_ids(vcol)
            return vcol_info is not None

    def execute(self, context):
        settings = context.scene.sollumz_vpaint_settings
        mesh = context.active_object.data

        iso_vcol = mesh.vertex_colors.active

        brush = context.tool_settings.vertex_paint.brush
        brush.color = settings.brush_color
        brush.secondary_color = settings.brush_secondary_color

        if self.discard:
            mesh.vertex_colors.remove(iso_vcol)
            return {'FINISHED'}

        vcol_info = get_isolated_channel_ids(iso_vcol)

        vcol = mesh.vertex_colors[vcol_info[0]]
        channel_idx = channel_id_to_idx(vcol_info[1])

        if vcol is None:
            error = "Mesh has no vertex color layer named '{0}'. Was it renamed or deleted?".format(
                vcol_info[0])
            self.report({'ERROR'}, error)
            return {'FINISHED'}

        # assuming iso_vcol has only grayscale data, RGB are equal, so copy from R
        copy_channel(mesh, iso_vcol, vcol, 0, channel_idx)
        mesh.vertex_colors.active = vcol
        mesh.vertex_colors.remove(iso_vcol)

        return {'FINISHED'}
