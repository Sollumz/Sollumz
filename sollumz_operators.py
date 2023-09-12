from math import fmod
import math
import traceback
import os
from typing import Optional
import bmesh
import bpy
import time
from collections import defaultdict
import re
from bpy_extras.io_utils import ImportHelper
import gpu
from mathutils import Color, Matrix, Vector
from .tools.vertexpainterhelper import channel_id_to_idx, copy_channel, fill_selected, get_isolated_channel_ids, invert_selected, posterize_selected, remap_selected, rgb_to_luminosity
from .sollumz_helper import SOLLUMZ_OT_base, find_sollumz_parent
from .sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, BOUND_TYPES, TimeFlags, ArchetypeType, LODLevel, channel_items, isolate_mode_name_prefix
from .sollumz_preferences import get_export_settings
from .cwxml.drawable import YDR, YDD
from .cwxml.fragment import YFT
from .cwxml.bound import YBN
from .cwxml.navmesh import YNV
from .cwxml.clipsdictionary import YCD
from .cwxml.ytyp import YTYP
from .cwxml.ymap import YMAP
from .ydr.ydrimport import import_ydr
from .ydr.ydrexport import export_ydr
from .ydd.yddimport import import_ydd
from .ydd.yddexport import export_ydd
from .yft.yftimport import import_yft
from .yft.yftexport import export_yft
from .ybn.ybnimport import import_ybn
from .ybn.ybnexport import export_ybn
from .ynv.ynvimport import import_ynv
from .ycd.ycdimport import import_ycd
from .ycd.ycdexport import export_ycd
from .ymap.ymapimport import import_ymap
from .ymap.ymapexport import export_ymap
from .tools.blenderhelper import add_child_of_bone_constraint, get_child_of_pose_bone, get_terrain_texture_brush, remove_number_suffix, create_blender_object, join_objects
from .tools.ytyphelper import ytyp_from_objects
from .ybn.properties import BoundProperties
from .ybn.properties import BoundFlags
from . import logger
from bpy.props import FloatVectorProperty, BoolProperty, FloatProperty, EnumProperty
from gpu_extras.batch import batch_for_shader
from bpy_extras import view3d_utils


class TimedOperator:
    @property
    def time_elapsed(self) -> float:
        """Get time elapsed since execution"""
        return round(time.time() - self._start, 3)

    def __init__(self) -> None:
        self._start: float = 0.0

    def execute(self, context: bpy.types.Context):
        self._start = time.time()
        return self.execute_timed(context)

    def execute_timed(self, context: bpy.types.Context):
        ...


class SOLLUMZ_OT_import(bpy.types.Operator, ImportHelper, TimedOperator):
    """Imports xml files exported by codewalker"""
    bl_idname = "sollumz.import"
    bl_label = "Import Codewalker XML"
    bl_options = {"UNDO"}

    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};*{YNV.file_extension};*{YCD.file_extension};*{YMAP.file_extension};",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    def draw(self, context):
        pass

    def execute_timed(self, context):
        logger.set_logging_operator(self)

        if not self.filepath or self.files[0].name == "":
            self.report({"INFO"}, "No file selected for import!")
            return {"CANCELLED"}

        for file in self.files:
            directory = os.path.dirname(self.filepath)
            filepath = os.path.join(directory, file.name)

            try:

                if YDR.file_extension in filepath:
                    import_ydr(filepath)
                elif YDD.file_extension in filepath:
                    import_ydd(filepath)
                elif YFT.file_extension in filepath:
                    import_yft(filepath)
                elif YBN.file_extension in filepath:
                    import_ybn(filepath)
                elif YNV.file_extension in filepath:
                    import_ynv(filepath)
                elif YCD.file_extension in filepath:
                    import_ycd(filepath)
                elif YMAP.file_extension in filepath:
                    import_ymap(filepath)
                else:
                    continue

                self.report({"INFO"}, f"Successfully imported '{filepath}'")
            except:
                self.report({"ERROR"},
                            f"Error importing: {filepath} \n {traceback.format_exc()}")

                return {"CANCELLED"}

        self.report(
            {"INFO"}, f"Imported in {self.time_elapsed} seconds")

        return {"FINISHED"}


class SOLLUMZ_OT_export(bpy.types.Operator, TimedOperator):
    """Exports codewalker xml files"""
    bl_idname = "sollumz.export"
    bl_label = "Export Codewalker XML"

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};*{YCD.file_extension};*{YMAP.file_extension};",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    directory: bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"}
    )

    def draw(self, context):
        pass

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute_timed(self, context: bpy.types.Context):
        logger.set_logging_operator(self)
        objs = self.collect_objects(context)
        export_settings = get_export_settings()

        if not objs:
            if export_settings.limit_to_selected:
                self.report(
                    {"INFO"}, "No Sollumz objects selected for export!")
            else:
                self.report(
                    {"INFO"}, "No Sollumz objects in the scene to export!")

            return {"CANCELLED"}

        for obj in objs:
            filepath = None
            try:
                if obj.sollum_type == SollumType.DRAWABLE:
                    filepath = self.get_filepath(obj, YDR.file_extension)
                    export_ydr(obj, filepath)
                elif obj.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                    filepath = self.get_filepath(obj, YDD.file_extension)
                    export_ydd(obj, filepath)
                elif obj.sollum_type == SollumType.FRAGMENT:
                    filepath = self.get_filepath(obj, YFT.file_extension)
                    export_yft(obj, filepath)
                elif obj.sollum_type == SollumType.CLIP_DICTIONARY:
                    filepath = self.get_filepath(obj, YCD.file_extension)
                    export_ycd(obj, filepath)
                elif obj.sollum_type in BOUND_TYPES:
                    filepath = self.get_filepath(obj, YBN.file_extension)
                    export_ybn(obj, filepath)
                elif obj.sollum_type == SollumType.YMAP:
                    filepath = self.get_filepath(obj, YMAP.file_extension)
                    export_ymap(obj, filepath)
                else:
                    continue

                self.report(
                    {"INFO"}, f"Successfully exported '{filepath}'")

            except:
                self.report({"ERROR"},
                            f"Error exporting: {filepath or obj.name} \n {traceback.format_exc()}")

                return {"CANCELLED"}

            if export_settings.export_with_ytyp:
                ytyp = ytyp_from_objects(objs)
                filepath = os.path.join(
                    self.directory, f"{ytyp.name}.ytyp.xml")
                ytyp.write_xml(filepath)
                self.report(
                    {"INFO"}, f"Successfully exported '{filepath}' (auto-generated)")

        self.report(
            {"INFO"}, f"Exported in {self.time_elapsed} seconds")

        return {"FINISHED"}

    def collect_objects(self, context: bpy.types.Context) -> list[bpy.types.Object]:
        export_settings = get_export_settings()

        objs = context.scene.objects

        if export_settings.limit_to_selected:
            objs = context.selected_objects

        return self.get_only_parent_objs(objs)

    def get_only_parent_objs(self, objs: list[bpy.types.Object]):
        parent_objs = set()
        objs = set(objs)

        for obj in objs:
            parent_obj = find_sollumz_parent(obj)

            if parent_obj is None or parent_obj in parent_objs:
                continue

            parent_objs.add(parent_obj)

        return list(parent_objs)

    def get_filepath(self, obj: bpy.types.Object, extension: str):
        name = remove_number_suffix(obj.name.lower())

        return os.path.join(self.directory, name + extension)


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
                if obj.sollum_type == SollumType.DRAWABLE_MODEL:
                    self.paint_mesh(obj.data, self.color)
                    self.messages.append(
                        f"{obj.name} was successfully painted.")
                else:
                    self.messages.append(
                        f"{obj.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_MODEL]} type.")
        else:
            self.message("No objects selected to paint.")
            return False

        return True


class SOLLUMZ_OT_paint_terrain_tex1(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 1 On Selected Object"""
    bl_idname = "sollumz.paint_tex1"
    bl_label = "Paint Texture 1"

    def run(self, context):
        get_terrain_texture_brush(1)
        return True


class SOLLUMZ_OT_paint_terrain_tex2(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 2 On Selected Object"""
    bl_idname = "sollumz.paint_tex2"
    bl_label = "Paint Texture 2"

    def run(self, context):
        get_terrain_texture_brush(2)
        return True


class SOLLUMZ_OT_paint_terrain_tex3(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 3 On Selected Object"""
    bl_idname = "sollumz.paint_tex3"
    bl_label = "Paint Texture 3"

    def run(self, context):
        get_terrain_texture_brush(3)
        return True


class SOLLUMZ_OT_paint_terrain_tex4(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 4 On Selected Object"""
    bl_idname = "sollumz.paint_tex4"
    bl_label = "Paint Texture 4"

    def run(self, context):
        get_terrain_texture_brush(4)
        return True


class SOLLUMZ_OT_paint_terrain_alpha(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Lookup Sampler Alpha On Selected Object"""
    bl_idname = "sollumz.paint_a"
    bl_label = "Paint Alpha"

    def run(self, context):
        get_terrain_texture_brush(5)
        return True
    

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
            point = Vector((a.x + radius * math.cos(angle), a.y + radius * math.sin(angle)))
            circle_points.append(point)

        circle_batch = batch_for_shader(circle_shader, 'LINE_LOOP', {
            "pos": circle_points})
        circle_shader.bind()
        circle_shader.uniform_float("color", line_params["colors"][1])
        circle_batch.draw(circle_shader)


class SOLLUMZ_OT_Gradient(bpy.types.Operator):
    """Draw a line with the mouse to paint a vertex color gradient"""
    bl_idname = "sollumz.gradient"
    bl_label = "Vertex Color Gradient"
    bl_description = "Paint vertex color gradient."
    bl_options = {"REGISTER", "UNDO"}

    _handle = None

    line_shader = gpu.shader.from_builtin('2D_SMOOTH_COLOR')
    circle_shader = gpu.shader.from_builtin('2D_UNIFORM_COLOR')

    start_color: FloatVectorProperty(
        name="Start Color",
        subtype='COLOR',
        default=[1.0,0.0,0.0],
        description="Start color of the gradient."
    )

    end_color: FloatVectorProperty(
        name="End Color",
        subtype='COLOR',
        default=[0.0,1.0,0.0],
        description="End color of the gradient."
    )

    circular_gradient: BoolProperty(
        name="Circular Gradient",
        description="Paint a circular gradient",
        default=False
    )

    use_hue_blend: BoolProperty(
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
        vertex_data = None # Will contain vert, and vert coordinates in 2d view space
        if mesh.use_paint_mask_vertex: # Face masking not currently supported
            vertex_data = [(v, view3d_utils.location_3d_to_region_2d(region, rv3d, obj.matrix_world @ v.co)) for v in bm.verts if v.select]
        else:
            vertex_data = [(v, view3d_utils.location_3d_to_region_2d(region, rv3d, obj.matrix_world @ v.co)) for v in bm.verts]

        # Vertex transformation math
        down_vector = Vector((0, -1, 0))
        direction_vector = Vector((end_point.x - start_point.x, end_point.y - start_point.y, 0)).normalized()
        rotation = direction_vector.rotation_difference(down_vector)

        translation_matrix = Matrix.Translation(Vector((-start_point.x, -start_point.y, 0)))
        inverse_translation_matrix = translation_matrix.inverted()
        rotation_matrix = rotation.to_matrix().to_4x4()
        combinedMat = inverse_translation_matrix @ rotation_matrix @ translation_matrix

        transStart = combinedMat @ start_point.to_4d() # Transform drawn line : rotate it to align to horizontal line
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
                color.h = fmod(1.0 + c1_hue + hue_separation * t, 1.0) 
                color.s = c1_sat + sat_separation * t
                color.v = c1_val + val_separation * t
            else:
                color.r = start_color[0] + (end_color[0] - start_color[0]) * t
                color.g = start_color[1] + (end_color[1] - start_color[1]) * t
                color.b = start_color[2] + (end_color[2] - start_color[2]) * t

            if mesh.use_paint_mask: # Masking by face
                face_loops = [loop for loop in vertex.link_loops if loop.face.select] # Get only loops that belong to selected faces
            else: # Masking by verts or no masking at all
                face_loops = [loop for loop in vertex.link_loops] # Get remaining vert loops

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
                mouse_position = Vector((event.mouse_region_x, event.mouse_region_y))
                self.line_params = {
                    "coords": [mouse_position, mouse_position],
                    "colors": [brush.color[:] + (1.0,),
                               brush.secondary_color[:] + (1.0,)],
                    "width": 1, # currently does nothing
                }
                args = (self, context, self.line_params, self.line_shader,
                    (self.circle_shader if self.circular_gradient else None))
                self._handle = bpy.types.SpaceView3D.draw_handler_add(draw_gradient_callback, args, 'WINDOW', 'POST_PIXEL')
        else:
            # Update or confirm gradient end point
            if event.type in {'MOUSEMOVE', 'LEFTMOUSE'}:
                line_params = self.line_params
                delta = 20

                # Update and constrain end point
                start_point = line_params["coords"][0]
                end_point = Vector((event.mouse_region_x, event.mouse_region_y))
                if event.shift:
                    end_point = self.axis_snap(start_point, end_point, delta)
                line_params["coords"] = [start_point, end_point]

                if event.type == 'LEFTMOUSE' and end_point != start_point: # Finish updating the line and paint the vertices
                    bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
                    self._handle = None

                    # Gradient will not work if there is no delta
                    if end_point == start_point:
                        return {'CANCELLED'}

                    # Use color gradient or force grayscale in isolate mode
                    start_color = line_params["colors"][0]
                    end_color = line_params["colors"][1]
                    isolate = get_isolated_channel_ids(context.active_object.data.vertex_colors.active)
                    use_hue_blend = self.use_hue_blend
                    if isolate is not None:
                        start_color = [rgb_to_luminosity(start_color)] * 3
                        end_color = [rgb_to_luminosity(end_color)] * 3
                        use_hue_blend = False

                    self.paintVerts(context, start_point, end_point, start_color, end_color, self.circular_gradient, use_hue_blend)
                    return {'FINISHED'}            

        # Allow camera navigation
        if event.type in {'MIDDLEMOUSE', 'WHEELUPMOUSE', 'WHEELDOWNMOUSE'}:
            return {'PASS_THROUGH'}

        if event.type in {'RIGHTMOUSE', 'ESC'}:
            if self._handle is not None:
                bpy.types.SpaceView3D.draw_handler_remove(self._handle, 'WINDOW')
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
        isolate = get_isolated_channel_ids(context.active_object.data.vertex_colors.active)
        use_hue_blend = self.use_hue_blend
        if isolate is not None:
            start_color = [rgb_to_luminosity(start_color)] * 3
            end_color = [rgb_to_luminosity(end_color)] * 3
            use_hue_blend = False

        self.paintVerts(context, start_point, end_point, start_color, end_color, self.circular_gradient, use_hue_blend)

        return {'FINISHED'}

    def invoke(self, context, event):
        if context.area.type == 'VIEW_3D':
            context.window_manager.modal_handler_add(self)
            return {'RUNNING_MODAL'}
        else:
            self.report({'WARNING'}, "View3D not found, cannot run operator")
            return {'CANCELLED'}


class SOLLUMZ_OT_Fill(bpy.types.Operator):
    """Fill the active vertex color channel(s)"""
    bl_idname = 'sollumz.fill'
    bl_label = 'Vertex Color Fill'
    bl_options = {'REGISTER', 'UNDO'}

    value: FloatProperty(
        name="Value",
        description="Value to fill active channel(s) with.",
        default=1.0,
        min=0.0,
        max=1.0
    )

    fill_with_color: BoolProperty(
        name="Fill with Color",
        description="Ignore active channels and fill with an RGB color",
        default=False
    )

    fill_color: FloatVectorProperty(
        name="Fill Color",
        subtype='COLOR',
        default=[1.0,1.0,1.0],
        description="Color to fill vertex color data with."
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bpy.context.object.mode == 'VERTEX_PAINT' and obj is not None and obj.type == 'MESH'

    def execute(self, context):
        settings = context.scene.sollumz_vertex_color_settings

        mesh = context.active_object.data
        vcol = mesh.vertex_colors.active if mesh.vertex_colors else mesh.vertex_colors.new()

        isolate_mode = get_isolated_channel_ids(vcol) is not None

        if self.fill_with_color or isolate_mode:
            active_channels = ['R', 'G', 'B']
            color = [self.value] * 4 if isolate_mode else self.fill_color
            fill_selected(mesh, vcol, color, active_channels)
        else:
            color = [self.value] * 4
            fill_selected(mesh, vcol, color, settings.active_channels)

        return {'FINISHED'}

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.prop(self, 'value', slider=True)
        row = layout.row()
        row.prop(self, 'fill_with_color')
        if self.fill_with_color:
            row = layout.row()
            row.prop(self, 'fill_color', text="")


class VERTEXCOLORMASTER_OT_Invert(bpy.types.Operator):
    """Invert active vertex color channel(s)"""
    bl_idname = 'sollumz.invert'
    bl_label = 'Invert Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bpy.context.object.mode == 'VERTEX_PAINT' and obj is not None and obj.type == 'MESH'

    def execute(self, context):
        settings = context.scene.sollumz_vertex_color_settings

        mesh = context.active_object.data
        vcol = mesh.vertex_colors.active if mesh.vertex_colors else mesh.vertex_colors.new()
        active_channels = settings.active_channels if get_isolated_channel_ids(vcol) is None else ['R', 'G', 'B']

        invert_selected(mesh, vcol, active_channels)

        return {'FINISHED'}


class SOLLUMZ_OT_Posterize(bpy.types.Operator):
    """Posterize active vertex color channel(s)"""
    bl_idname = 'sollumz.posterize'
    bl_label = 'Posterize Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    steps: bpy.props.IntProperty(
        name="Steps",
        default=2,
        min=2,
        max=256,
        description="Number of different grayscale values for posterization of active channel(s)."
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bpy.context.object.mode == 'VERTEX_PAINT' and obj is not None and obj.type == 'MESH'

    def execute(self, context):
        settings = context.scene.sollumz_vertex_color_settings

        # using posterize(), 2 steps -> 3 tones, but best to have 2 steps -> 2 tones
        steps = self.steps - 1

        mesh = context.active_object.data
        vcol = mesh.vertex_colors.active if mesh.vertex_colors else mesh.vertex_colors.new()
        active_channels = settings.active_channels if get_isolated_channel_ids(vcol) is None else ['R', 'G', 'B']

        posterize_selected(mesh, vcol, steps, active_channels)

        return {'FINISHED'}
    
class SOLLUMZ_OT_ApplyIsolatedChannel(bpy.types.Operator):
    """Apply isolated channel back to the vertex color layer it came from"""
    bl_idname = 'sollumz.apply_isolated'
    bl_label = "Apply Isolated Channel"
    bl_options = {'REGISTER', 'UNDO'}

    discard: BoolProperty(
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
        settings = context.scene.sollumz_vertex_color_settings
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
            error = "Mesh has no vertex color layer named '{0}'. Was it renamed or deleted?".format(vcol_info[0])
            self.report({'ERROR'}, error)
            return {'FINISHED'}

        # assuming iso_vcol has only grayscale data, RGB are equal, so copy from R
        copy_channel(mesh, iso_vcol, vcol, 0, channel_idx)
        mesh.vertex_colors.active = vcol
        mesh.vertex_colors.remove(iso_vcol)

        return {'FINISHED'}
    
class SOLLUMZ_OT_IsolateChannel(bpy.types.Operator):
    """Isolate a specific channel to paint in grayscale"""
    bl_idname = 'sollumz.isolate_channel'
    bl_label = 'Isolate Vertex Color Channel'
    bl_options = {'REGISTER', 'UNDO'}

    src_channel_id: EnumProperty(
        name="Source Channel",
        items=channel_items,
        description="Source (Src) color channel."
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bpy.context.object.mode == 'VERTEX_PAINT' and obj is not None and obj.type == 'MESH'

    def execute(self, context):
        settings = context.scene.sollumz_vertex_color_settings
        obj = context.active_object
        mesh = obj.data

        if mesh.vertex_colors is None:
            self.report({'ERROR'}, "Mesh has no vertex color layer to isolate.")
            return {'FINISHED'}

        # get the vcol and channel to isolate
        # create empty vcol using name template
        vcol = mesh.vertex_colors.active
        iso_vcol_id = "{0}_{1}_{2}".format(isolate_mode_name_prefix, self.src_channel_id, vcol.name)
        if iso_vcol_id in mesh.vertex_colors:
            error = "{0} Channel has already been isolated to {1}. Apply or Discard before isolating again.".format(self.src_channel_id, iso_vcol_id)
            self.report({'ERROR'}, error)
            return {'FINISHED'}

        iso_vcol = mesh.vertex_colors.new()
        iso_vcol.name = iso_vcol_id
        channel_idx = channel_id_to_idx(self.src_channel_id)

        copy_channel(mesh, vcol, iso_vcol, channel_idx, channel_idx, dst_all_channels=True, alpha_mode='FILL')
        mesh.vertex_colors.active = iso_vcol
        brush = context.tool_settings.vertex_paint.brush
        settings.brush_color = brush.color
        settings.brush_secondary_color = brush.secondary_color
        brush.color = [settings.brush_value_isolate] * 3
        brush.secondary_color = [settings.brush_secondary_value_isolate] * 3

        return {'FINISHED'}
    
class SOLLUMZ_OT_Remap(bpy.types.Operator):
    """Remap active vertex color channel(s)"""
    bl_idname = 'sollumz.remap'
    bl_label = 'Remap Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    active_channels: EnumProperty(
        name="Active Channels",
        options={'ENUM_FLAG'},
        items=channel_items,
        description="Which channels to enable.",
        default={'R', 'G', 'B'},
    )

    min0: FloatProperty(
        default=0,
        min=0,
        max=1
    )

    max0: FloatProperty(
        default=1,
        min=0,
        max=1
    )

    min1: FloatProperty(
        default=0,
        min=0,
        max=1
    )

    max1: FloatProperty(
        default=1,
        min=0,
        max=1
    )
    
    isolate_mode: BoolProperty(
        default=False,
    )

    def draw(self, context):
        layout = self.layout

        if not self.isolate_mode:
            col = layout.column()
            row = col.row(align=True)
            row.prop(self, 'active_channels')

        layout.label(text="Input Range")
        layout.prop(self, 'min0', text="Min", slider=True)
        layout.prop(self, 'max0', text="Max", slider=True)

        layout.label(text="Output Range")
        layout.prop(self, 'min1', text="Min", slider=True)
        layout.prop(self, 'max1', text="Max", slider=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return bpy.context.object.mode == 'VERTEX_PAINT' and obj is not None and obj.type == 'MESH'

    def invoke(self, context, event):
        settings = context.scene.sollumz_vertex_color_settings

        mesh = context.active_object.data
        vcol = mesh.vertex_colors.active if mesh.vertex_colors else mesh.vertex_colors.new()
        self.isolate_mode = True if get_isolated_channel_ids(vcol) is not None else False
        self.active_channels = settings.active_channels if not self.isolate_mode else {'R', 'G', 'B'}
        
        return self.execute(context)

    def execute(self, context):
        mesh = context.active_object.data
        vcol = mesh.vertex_colors.active if mesh.vertex_colors else mesh.vertex_colors.new()

        remap_selected(mesh, vcol, self.min0, self.max0, self.min1, self.max1, self.active_channels)

        return {'FINISHED'}

class SelectTimeFlagsRange(SOLLUMZ_OT_base):
    """Select range of time flags"""
    bl_label = "Select"

    def get_flags(self, context):
        return None

    def run(self, context):
        flags = self.get_flags(context)
        if not flags:
            return False
        start = int(flags.time_flags_start)
        end = int(flags.time_flags_end)
        index = 0
        for prop in TimeFlags.__annotations__:
            if index < 24:
                if start < end:
                    if index >= start and index < end:
                        flags[prop] = True
                elif start > end:
                    if index < end or index >= start:
                        flags[prop] = True
                elif start == 0 and end == 0:
                    flags[prop] = True
            index += 1
        flags.update_flag(context)
        return True


class ClearTimeFlags(SOLLUMZ_OT_base):
    """Clear all time flags"""
    bl_label = "Clear Selection"

    def get_flags(self, context):
        return None

    def run(self, context):
        flags = self.get_flags(context)
        if not flags:
            return False
        for prop in TimeFlags.__annotations__:
            flags[prop] = False
        flags.update_flag(context)
        return True


def sollumz_menu_func_import(self, context):
    self.layout.operator(SOLLUMZ_OT_import.bl_idname,
                         text=f"Codewalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension}, {YCD.file_extension})")


def sollumz_menu_func_export(self, context):
    self.layout.operator(SOLLUMZ_OT_export.bl_idname,
                         text=f"Codewalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension}, {YCD.file_extension})")


class SOLLUMZ_OT_debug_hierarchy(bpy.types.Operator):
    """Debug: Fix incorrect Sollum Type after update. Must set correct type for top-level object first."""
    bl_idname = "sollumz.debug_hierarchy"
    bl_label = "Fix Hierarchy"
    bl_options = {"UNDO"}
    bl_order = 100

    def execute(self, context):
        sollum_type = context.scene.debug_sollum_type
        for obj in context.selected_objects:
            if len(obj.children) < 1:
                self.report(
                    {"INFO"}, f"{obj.name} has no children! Skipping...")
                continue

            obj.sollum_type = sollum_type
            if sollum_type == SollumType.DRAWABLE:
                self.fix_drawable(obj)
            elif sollum_type == SollumType.DRAWABLE_DICTIONARY:
                self.fix_drawable_dict(obj)
            elif sollum_type == SollumType.BOUND_COMPOSITE:
                self.fix_composite(obj)

        self.report({"INFO"}, "Hierarchy successfuly set.")

        return {"FINISHED"}

    def fix_drawable(self, obj: bpy.types.Object):
        for model in obj.children:
            if model.type != "MESH":
                continue

            model.sollum_type = SollumType.DRAWABLE_MODEL

    def fix_drawable_dict(self, obj: bpy.types.Object):
        for draw in obj.children:
            if draw.type != "EMPTY":
                continue

            draw.sollum_type = SollumType.DRAWABLE
            self.fix_drawable(draw)

    def fix_composite(self, obj: bpy.types.Object):
        for bound in obj.children:
            if bound.type == "EMPTY":
                if "cloth" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_CLOTH
                    continue

                if "bvh" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_GEOMETRYBVH
                else:
                    bound.sollum_type = SollumType.BOUND_GEOMETRY
                for geom in bound.children:
                    if geom.type == "MESH":
                        if "Box" in geom.name:
                            geom.sollum_type = SollumType.BOUND_POLY_BOX
                        elif "Sphere" in geom.name:
                            geom.sollum_type = SollumType.BOUND_POLY_SPHERE
                        elif "Capsule" in geom.name:
                            geom.sollum_type = SollumType.BOUND_POLY_CAPSULE
                        elif "Cylinder" in geom.name:
                            geom.sollum_type = SollumType.BOUND_POLY_CYLINDER
                        else:
                            geom.sollum_type = SollumType.BOUND_POLY_TRIANGLE
            if bound.type == "MESH":
                if "box" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_POLY_BOX
                elif "sphere" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_POLY_SPHERE
                elif "capsule" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_POLY_CAPSULE
                elif "cylinder" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_POLY_CYLINDER
                else:
                    bound.sollum_type = SollumType.BOUND_POLY_TRIANGLE


class SOLLUMZ_OT_debug_fix_light_intensity(bpy.types.Operator):
    bl_idname = "sollumz.debug_fix_light_intensity"
    bl_label = "Re-adjust Light Intensity"
    bl_description = "Multiply light intensity by a factor of 500 to make older projects compatible with the light intensity change"
    bl_options = {"UNDO"}

    def execute(self, context):
        only_selected = context.scene.debug_lights_only_selected

        objects = context.selected_objects if only_selected else context.scene.objects
        light_objs = [obj for obj in objects if obj.type ==
                      "LIGHT" and obj.sollum_type == SollumType.LIGHT]

        if not light_objs:
            self.report(
                {"INFO"}, "No Sollumz lights selected" if only_selected else "No Sollumz lights in the scene.")
            return {"CANCELLED"}

        lights: list[bpy.types.Light] = []
        for light_obj in light_objs:
            if light_obj.data not in lights:
                lights.append(light_obj.data)

        for light in lights:
            light.energy = light.energy * 500

        return {"FINISHED"}


class SOLLUMZ_OT_copy_location(bpy.types.Operator):
    """Copy the location of an object to the clipboard"""
    bl_idname = "wm.sollumz_copy_location"
    bl_label = ""
    location: bpy.props.StringProperty()

    def execute(self, context):
        bpy.context.window_manager.clipboard = self.location
        self.report(
            {'INFO'}, "Location XDd copied to clipboard: {}".format(self.location))
        return {'FINISHED'}


class SOLLUMZ_OT_copy_rotation(bpy.types.Operator):
    """Copy the quaternion rotation of an object to the clipboard"""
    bl_idname = "wm.sollumz_copy_rotation"
    bl_label = ""
    rotation: bpy.props.StringProperty()

    def execute(self, context):
        rotation = self.rotation.strip('[]')
        bpy.context.window_manager.clipboard = rotation
        self.report(
            {'INFO'}, "Rotation copied to clipboard: {}".format(rotation))
        return {'FINISHED'}


class SOLLUMZ_OT_copy_all_locations(bpy.types.Operator):
    """Copy the locations of all selected objects to the clipboard"""
    bl_idname = "wm.sollumz_copy_all_locations"
    bl_label = ""
    locations: bpy.props.StringProperty()

    def execute(self, context):
        selected_objects = bpy.context.selected_objects
        locations_text = ""
        for obj in selected_objects:
            loc = obj.location
            locations_text += "{}: {:.6f}, {:.6f}, {:.6f}\n".format(
                obj.name, loc[0], loc[1], loc[2])
        bpy.context.window_manager.clipboard = locations_text
        self.report(
            {'INFO'}, "Locations copied to clipboard:\n{}".format(locations_text))
        return {'FINISHED'}


class SOLLUMZ_OT_paste_location(bpy.types.Operator):
    """Paste the location of an object from the clipboard"""
    bl_idname = "wm.sollumz_paste_location"
    bl_label = ""
    location: bpy.props.StringProperty()

    def execute(self, context):
        def parse_location_string(location_string):
            pattern = r"(-?\d+\.\d+)"
            matches = re.findall(pattern, location_string)
            if len(matches) == 3:
                return float(matches[0]), float(matches[1]), float(matches[2])
            else:
                return None

        location_string = bpy.context.window_manager.clipboard

        location = parse_location_string(location_string)
        if location is not None:
            selected_object = bpy.context.object

            selected_object.location = location
            self.report({'INFO'}, "Location set successfully.")
        else:
            self.report({'ERROR'}, "Invalid location string.")

        return {'FINISHED'}


class SOLLUMZ_OT_debug_reload_entity_sets(bpy.types.Operator):
    bl_idname = "sollumz.debug_reload_entity_sets"
    bl_label = "Reload Entity Sets"
    bl_description = "Reload old entity set entities."
    bl_options = {"UNDO"}

    def execute(self, context):
        for ytyp in context.scene.ytyps:
            for archetype in ytyp.archetypes:
                if archetype.type != ArchetypeType.MLO:
                    continue

                for entity_set in archetype.entity_sets:
                    for entity in entity_set.entities:
                        new_entity = archetype.new_entity()
                        for k, v in entity.items():
                            new_entity[k] = v

                        new_entity.attached_entity_set_id = str(entity_set.id)

        return {"FINISHED"}


class SOLLUMZ_OT_debug_migrate_drawable_models(bpy.types.Operator):
    """Convert old drawable model to use new LOD system"""
    bl_idname = "sollumz.migratedrawable"
    bl_label = "Migrate Drawable Model(s)"
    bl_options = {"UNDO"}

    def execute(self, context):
        selected_models = [
            obj for obj in context.selected_objects if obj.sollum_type == SollumType.DRAWABLE_MODEL]

        if not selected_models:
            self.report({"INFO"}, "No drawable models selected!")
            return {"CANCELLED"}

        parent = selected_models[0].parent

        models_by_lod: dict[LODLevel,
                            list[bpy.types.Object]] = defaultdict(list)

        for obj in selected_models:
            models_by_lod[obj.drawable_model_properties.sollum_lod].extend(
                obj.children)
            bpy.data.objects.remove(obj)

        model_obj = create_blender_object(SollumType.DRAWABLE_MODEL)
        model_obj.sollumz_lods.add_empty_lods()
        old_mesh = model_obj.data

        for lod_level, geometries in models_by_lod.items():

            if len(geometries) > 1:
                joined_obj = join_objects(geometries)
            else:
                joined_obj = geometries[0]

            model_obj.sollumz_lods.set_lod_mesh(lod_level, joined_obj.data)
            model_obj.sollumz_lods.set_active_lod(lod_level)

            context.view_layer.objects.active = joined_obj
            model_obj.select_set(True)

            bpy.ops.object.make_links_data(type='MODIFIERS')
            bpy.data.objects.remove(joined_obj)

        bpy.data.meshes.remove(old_mesh)

        model_obj.parent = parent

        # Set highest lod level
        for lod_level in [LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW]:
            if model_obj.sollumz_lods.get_lod(lod_level) != None:
                model_obj.sollumz_lods.set_active_lod(lod_level)
                break

        return {"FINISHED"}


class SOLLUMZ_OT_debug_migrate_bound_geometries(bpy.types.Operator):
    """Convert old bound geometries to new hiearchy using shape keys for damaged layers"""
    bl_idname = "sollumz.migrateboundgeoms"
    bl_label = "Migrate Bound Geometry(s)"
    bl_options = {"UNDO"}

    def execute(self, context):
        selected = [
            obj for obj in context.selected_objects if obj.sollum_type == SollumType.BOUND_GEOMETRY]

        if not selected:
            self.report({"INFO"}, "No bound geometries selected!")
            return {"CANCELLED"}

        for obj in selected:
            bound_meshes = []
            damaged_meshes = []

            for child in obj.children:
                if child.type != "MESH":
                    continue

                child.data.transform(child.matrix_basis)
                child.matrix_basis.identity()

                if child.sollum_type == SollumType.BOUND_POLY_TRIANGLE:
                    bound_meshes.append(child)
                elif child.sollum_type == SollumType.BOUND_POLY_TRIANGLE2:
                    damaged_meshes.append(child)

            joined_obj = join_objects(bound_meshes)
            joined_obj.sollum_type = SollumType.BOUND_GEOMETRY
            joined_obj.name = obj.name
            joined_obj.parent = obj.parent

            self.set_bound_geometry_properties(obj, joined_obj)
            self.set_composite_flags(obj, joined_obj)

            joined_obj.matrix_basis = obj.matrix_basis

            if damaged_meshes:
                joined_damaged_obj = join_objects(damaged_meshes)
                self.set_shape_keys(joined_obj, joined_damaged_obj)

                bpy.data.meshes.remove(joined_damaged_obj.data)

            bpy.data.objects.remove(obj)

        return {"FINISHED"}

    def set_bound_geometry_properties(self, old_obj: bpy.types.Object, new_obj: bpy.types.Object):
        for prop_name in BoundProperties.__annotations__.keys():
            value = getattr(old_obj.bound_properties, prop_name)
            setattr(new_obj.bound_properties, prop_name, value)

    def set_composite_flags(self, old_obj: bpy.types.Object, new_obj: bpy.types.Object):
        def set_flags(prop_name: str):
            flags_props = getattr(old_obj, prop_name)
            new_flags_props = getattr(new_obj, prop_name)

            for flag_name in BoundFlags.__annotations__.keys():
                value = getattr(flags_props, flag_name)
                setattr(new_flags_props, flag_name, value)

        set_flags("composite_flags1")
        set_flags("composite_flags2")

    def set_shape_keys(self, bound_obj: bpy.types.Object, damaged_obj: bpy.types.Object):
        bound_obj.shape_key_add(name="Basis")
        deformed_key = bound_obj.shape_key_add(name="Deformed")

        for i, vert in enumerate(damaged_obj.data.vertices):
            deformed_key.data[i].co = vert.co


class SOLLUMZ_OT_debug_replace_armature_constraints(bpy.types.Operator):
    """Replace the Armature constraints in all selected objects for Child Of constraints (for migrating pre version 0.3 projects)"""
    bl_idname = "sollumz.replace_armature_constraints"
    bl_label = "Replace Armature Constraints"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not context.selected_objects:
            self.report({"INFO"}, "No objects selected!")
            return {"CANCELLED"}

        for obj in context.selected_objects:
            constraint = self.get_armature_constraint(obj)

            if constraint is None or not constraint.targets:
                continue

            target = constraint.targets[0]
            armature_obj = target.target
            target_bone = target.subtarget

            obj.constraints.remove(constraint)

            add_child_of_bone_constraint(obj, armature_obj, target_bone)
            self.set_obj_child_of_bone_inverse(obj)

        return {"FINISHED"}

    @staticmethod
    def get_armature_constraint(obj: bpy.types.Object) -> Optional[bpy.types.ArmatureConstraint]:
        for constraint in obj.constraints:
            if constraint.type == "ARMATURE":
                return constraint

    @staticmethod
    def set_obj_child_of_bone_inverse(obj: bpy.types.Object):
        """Invert the transformations of the Child Of constraint bone on obj
        so that the object doesn't get double transformed"""
        # bone = get_child_of_bone(obj)
        bone = get_child_of_pose_bone(obj)

        if bone is None:
            return

        obj.matrix_local = bone.matrix.inverted() @ obj.matrix_local


class SOLLUMZ_OT_set_sollum_type(bpy.types.Operator):
    """Set the sollum type of all selected objects"""
    bl_idname = "sollumz.setsollumtype"
    bl_label = "Set Sollum Type"

    def execute(self, context):
        sollum_type = context.scene.all_sollum_type

        for obj in context.selected_objects:
            obj.sollum_type = sollum_type

        self.report(
            {"INFO"}, f"Sollum Type successfuly set to {SOLLUMZ_UI_NAMES[sollum_type]}.")

        return {"FINISHED"}


class SearchEnumHelper:
    """Helper class for searching and setting enums"""
    bl_label = "Search"

    def get_data_block(self, context):
        """Get the data-block containing the enum property"""
        ...

    def execute(self, context):
        data_block = self.get_data_block(context)
        prop_name = getattr(self, "bl_property")
        enum_value = getattr(self, prop_name)

        setattr(data_block, prop_name, enum_value)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)

        return {'FINISHED'}


def register():
    bpy.types.TOPBAR_MT_file_import.append(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(sollumz_menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(sollumz_menu_func_export)
