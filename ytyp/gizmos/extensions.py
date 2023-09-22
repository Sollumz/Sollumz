import bpy
import math
import os
import functools
from mathutils import Matrix, Vector, Quaternion
from typing import Literal
from collections.abc import Iterator
from ..utils import get_selected_archetype, get_selected_extension, get_selected_ytyp
from ...tools.blenderhelper import tag_redraw
from ...sollumz_properties import ArchetypeType
from ..properties.ytyp import ArchetypeProperties
from ..properties.extensions import ExtensionType, ExtensionProperties


DEBUG_DRAW = False


def iter_archetype_extensions(context) -> Iterator[tuple[ArchetypeProperties, ExtensionProperties]]:
    """Iterate visible archetype extensions from the selected YTYP."""
    selected_ytyp = get_selected_ytyp(context)
    if selected_ytyp is None:
        return

    for archetype in selected_ytyp.archetypes:
        if not archetype.asset or archetype.type == ArchetypeType.MLO:
            continue

        if not archetype.asset.visible_get():
            continue

        for ext in archetype.extensions:
            yield (archetype, ext)


def can_draw_gizmos(context):
    tool = context.workspace.tools.from_space_view3d_mode(context.mode)
    if tool.idname != "sollumz.archetype_extension":
        return False

    return next(iter_archetype_extensions(context), None) is not None


@functools.cache
def get_extension_shapes() -> dict[ExtensionType, object]:
    """Gets a dictionary of shapes that represent each extension type."""
    shapes = {}

    def _load_extension_model(extension_type: ExtensionType, file_name: str):
        file_loc = os.path.join(os.path.dirname(__file__), "models", file_name)
        with open(file_loc, "r") as f:
            verts = []
            model_verts = []
            for line in f.readlines():
                if line.startswith("v"):
                    x, y, z = line.strip("v ").split(" ")
                    verts.append((float(x), float(y), float(z)))
                elif line.startswith("f"):
                    v0, v1, v2 = line.strip("f ").split(" ")
                    model_verts.append(verts[int(v0) - 1])
                    model_verts.append(verts[int(v1) - 1])
                    model_verts.append(verts[int(v2) - 1])

            shapes[extension_type] = bpy.types.Gizmo.new_custom_shape("TRIS", model_verts)

    for ext_type, model_file_name in (
        (ExtensionType.AUDIO_COLLISION, "AudioCollisionSettings.obj"),
        (ExtensionType.AUDIO_EMITTER, "AudioEmitter.obj"),
        (ExtensionType.BUOYANCY, "Buoyancy.obj"),
        (ExtensionType.DOOR, "Door.obj"),
        (ExtensionType.EXPLOSION_EFFECT, "ExplosionEffect.obj"),
        (ExtensionType.EXPRESSION, "Expression.obj"),
        (ExtensionType.LADDER, "LadderTop.obj"),
        (ExtensionType.LIGHT_SHAFT, "LightShaft.obj"),
        (ExtensionType.PARTICLE, "ParticleEffect.obj"),
        (ExtensionType.PROC_OBJECT, "ProcObject.obj"),
        (ExtensionType.SPAWN_POINT, "SpawnPoint.obj"),
        (ExtensionType.SPAWN_POINT_OVERRIDE, "SpawnPointOverride.obj"),
        (ExtensionType.WIND_DISTURBANCE, "WindDisturbance.obj"),
    ):
        _load_extension_model(ext_type, model_file_name)
    return shapes


@functools.cache
def get_cube_shape() -> object:
    """A 1x1x1 cube with origin in the middle."""
    return bpy.types.Gizmo.new_custom_shape("LINES", (
        # bottom face
        (-0.5, -0.5, -0.5), (-0.5, 0.5, -0.5),
        (-0.5, -0.5, -0.5), (0.5, -0.5, -0.5),
        (0.5, -0.5, -0.5), (0.5, 0.5, -0.5),
        (-0.5, 0.5, -0.5), (0.5, 0.5, -0.5),
        # top face
        (-0.5, -0.5, 0.5), (-0.5, 0.5, 0.5),
        (-0.5, -0.5, 0.5), (0.5, -0.5, 0.5),
        (0.5, -0.5, 0.5), (0.5, 0.5, 0.5),
        (-0.5, 0.5, 0.5), (0.5, 0.5, 0.5),
        # connect top and bottom faces
        (-0.5, -0.5, -0.5), (-0.5, -0.5, 0.5),
        (-0.5, 0.5, -0.5), (-0.5, 0.5, 0.5),
        (0.5, -0.5, -0.5), (0.5, -0.5, 0.5),
        (0.5, 0.5, -0.5), (0.5, 0.5, 0.5),
    ))


@functools.cache
def get_square_shape() -> object:
    """A 1x1 square, along XZ plane, with origin in the middle."""
    return bpy.types.Gizmo.new_custom_shape("LINES", (
        (-0.5, 0.0, -0.5), (0.5, 0.0, -0.5),
        (-0.5, 0.0, -0.5), (-0.5, 0.0, 0.5),
        (0.5, 0.0, 0.5), (0.5, 0.0, -0.5),
        (0.5, 0.0, 0.5), (-0.5, 0.0, 0.5),
    ))


@functools.cache
def get_line_shape() -> object:
    """A unit line along Y axis, from Y=0 to Y=1."""
    return bpy.types.Gizmo.new_custom_shape("LINES", (
        (0.0, 0.0, 0.0), (0.0, 1.0, 0.0),
    ))


@functools.cache
def get_ladder_shape() -> object:
    """Shape representing a ladder with a marker in-front to indicate its orientation.
    Origin is at the bottom and extends upwards.
    """
    return bpy.types.Gizmo.new_custom_shape("LINES", (
        # pillars
        (-0.15, 0.0, -0.04), (-0.15, 0.0, 1.04),
        (0.15, 0.0, -0.04), (0.15, 0.0, 1.04),
        # steps
        (-0.15, 0.0, 0.0), (0.15, 0.0, 0.0),
        (-0.15, 0.0, 0.25), (0.15, 0.0, 0.25),
        (-0.15, 0.0, 0.5), (0.15, 0.0, 0.5),
        (-0.15, 0.0, 0.75), (0.15, 0.0, 0.75),
        (-0.15, 0.0, 1.0), (0.15, 0.0, 1.0),
        # front marker
        (-0.2, 0.25, 0.2), (0.0, 0.1, 0.2),
        (0.2, 0.25, 0.2), (0.0, 0.1, 0.2),
        (-0.2, 0.25, 0.2), (0.2, 0.25, 0.2),
        (-0.2, 0.25, 0.2), (-0.2, 0.45, 0.2),
        (0.2, 0.25, 0.2), (0.2, 0.45, 0.2),
        (-0.2, 0.45, 0.2), (0.2, 0.45, 0.2),
    ))


def is_local_transform(context) -> bool:
    return context.scene.transform_orientation_slots[0].type == "LOCAL"


def get_extension_offset_position(ext: ExtensionProperties) -> Vector:
    ext_props = ext.get_properties()

    offset_pos = ext_props.offset_position
    if ext.extension_type == ExtensionType.LADDER:
        # In some cases, ladder's `top` and `offset_position` are not equal.
        # `offset_postion` is not used in ladders, so we use `top` as the extension
        # position and ignore `offset_position`. When modified, the operator will
        # change the `offset_position` to the value of `top`.
        offset_pos = ext_props.top

    return offset_pos


def get_extension_offset_rotation(ext: ExtensionProperties) -> Quaternion:
    ext_props = ext.get_properties()

    if ext.extension_type == ExtensionType.LADDER:
        # use ladder normal as rotation
        normal = ext_props.normal.normalized()
        offset_rot = normal.to_track_quat("Y", "Z")
    elif ext.extension_type == ExtensionType.LIGHT_SHAFT:
        # derived rotation from light shaft corners
        a = ext_props.cornerA
        b = ext_props.cornerB
        d = ext_props.cornerD

        right = a - b
        up = a - d
        if right.length_squared < 0.0001 or up.length_squared < 0.0001:
            # some corners in the same position, cannot extract directions, default to identity
            offset_rot = Quaternion()
        else:
            right.normalize()
            up.normalize()
            forward = up.cross(right)

            rotation_mat = Matrix((right, forward, up))
            rotation_mat.invert()
            offset_rot = rotation_mat.to_quaternion()
    elif hasattr(ext_props, "offset_rotation"):
        # extension has a defined rotation
        offset_rot = ext_props.offset_rotation.to_quaternion()
    else:
        # extension has no rotation, default to identity
        offset_rot = Quaternion()

    return offset_rot


def get_extension_offset_matrix(ext: ExtensionProperties) -> Matrix:
    offset_pos = get_extension_offset_position(ext)
    offset_rot = get_extension_offset_rotation(ext)
    return Matrix.LocRotScale(offset_pos, offset_rot, (1.0, 1.0, 1.0))


def get_extension_ladder_bottom_offset_matrix(ext: ExtensionProperties) -> Matrix:
    ext_props = ext.get_properties()

    offset_pos = ext_props.bottom
    offset_rot = get_extension_offset_rotation(ext)
    return Matrix.LocRotScale(offset_pos, offset_rot, (1.0, 1.0, 1.0))


def get_extension_world_matrix(ext: ExtensionProperties, archetype: ArchetypeProperties) -> Matrix:
    offset_mat = get_extension_offset_matrix(ext)
    if archetype.asset is None:
        return offset_mat
    else:
        return archetype.asset.matrix_world @ offset_mat


def get_extension_ladder_bottom_world_matrix(ext: ExtensionProperties, archetype: ArchetypeProperties) -> Matrix:
    offset_mat = get_extension_ladder_bottom_offset_matrix(ext)
    if archetype.asset is None:
        return offset_mat
    else:
        return archetype.asset.matrix_world @ offset_mat


def get_extension_light_shaft_dimensions(ext: ExtensionProperties) -> Vector:
    if ext.extension_type != ExtensionType.LIGHT_SHAFT:
        return Vector((1.0, 1.0))

    ext_props = ext.get_properties()

    a = ext_props.cornerA
    b = ext_props.cornerB
    d = ext_props.cornerD
    width = (b - a).length
    height = (d - a).length

    return Vector((width, height))


def get_transform_axis(
    ext: ExtensionProperties,
    archetype: ArchetypeProperties,
    axis: Literal["X", "Y", "Z"],
    local: bool = False
) -> Vector:
    if axis == "X":
        axis_vec = Vector((1.0, 0.0, 0.0))
    elif axis == "Y":
        axis_vec = Vector((0.0, 1.0, 0.0))
    elif axis == "Z":
        axis_vec = Vector((0.0, 0.0, 1.0))

    if local:
        rot = get_extension_offset_rotation(ext)
    else:  # global
        if archetype.asset is None:
            rot = Quaternion()
        else:
            rot = archetype.asset.matrix_world.to_quaternion()
            rot.invert()

    axis_vec.rotate(rot)

    return axis_vec


class SOLLUMZ_GT_archetype_extension(bpy.types.Gizmo):
    bl_idname = "SOLLUMZ_GT_archetype_extension"

    def __init__(self):
        super().__init__()
        self.linked_archetype = None
        self.linked_extension = None

    def setup(self):
        self.use_event_handle_all = True  # prevent clicks on gizmo from passing through
        self.line_width = 5

    def draw(self, context):
        self.draw_select(context)

    def draw_select(self, context, select_id=None):
        selected_archetype = get_selected_archetype(context)
        selected_extension = get_selected_extension(context)
        archetype = self.linked_archetype
        ext = self.linked_extension
        ext_props = ext.get_properties()
        asset = archetype.asset

        if not archetype or not ext or not asset:
            return

        is_active = selected_archetype == archetype and selected_extension == ext
        is_ladder = ext.extension_type == ExtensionType.LADDER
        is_light_shaft = ext.extension_type == ExtensionType.LIGHT_SHAFT

        theme = context.preferences.themes[0]

        self.color = theme.view_3d.object_active if is_active else theme.view_3d.object_selected
        self.color_highlight = self.color
        self.alpha = 0.6
        self.alpha_highlight = 0.8

        offset_matrix = get_extension_offset_matrix(ext)
        gizmo_matrix = asset.matrix_world @ offset_matrix

        extension_shape = get_extension_shapes().get(ext.extension_type, None)

        if is_active and not is_light_shaft:
            self.draw_custom_shape(get_cube_shape(), matrix=gizmo_matrix @ Matrix.Scale(0.4, 4), select_id=select_id)

        if extension_shape is not None:
            rv3d = context.space_data.region_3d

            # make extension shape face the camera so it is recognizable from all view angles
            ext_shape_loc = gizmo_matrix.to_translation()
            if rv3d.is_perspective:
                ext_shape_dir = (rv3d.view_matrix.inverted().to_translation() - ext_shape_loc)
                ext_shape_dir.normalize()
                ext_shape_rot = ext_shape_dir.to_track_quat("Z", "Y")
            else:
                ext_shape_rot = rv3d.view_rotation
            ext_shape_rot = ext_shape_rot @ Matrix.Rotation(math.radians(90.0), 3, "Y").to_quaternion()
            ext_shape_scale = 0.55, 0.55, 0.55
            if is_light_shaft:
                # Scale based on light shaft size
                light_shaft_width, light_shaft_height = get_extension_light_shaft_dimensions(ext)
                size = min(light_shaft_width, light_shaft_height)
                scale = max(size / 2.0, 0.05)
                ext_shape_scale = scale, scale, scale
            ext_shape_mat = Matrix.LocRotScale(ext_shape_loc, ext_shape_rot, ext_shape_scale)

            self.draw_custom_shape(extension_shape, matrix=ext_shape_mat, select_id=select_id)

        if hasattr(ext_props, "offset_rotation"):
            self.draw_preset_arrow(gizmo_matrix @ Matrix.Translation((0.0, 0.25, 0.0)) @ Matrix.Scale(0.325, 4),
                                   axis="POS_Y", select_id=-1 if select_id is None else select_id)

        if is_ladder:
            self.draw_ladder_gizmo(context, select_id)
        elif is_light_shaft:
            self.draw_light_shaft_gizmo(context, select_id)

    def draw_ladder_gizmo(self, context, select_id):
        archetype = self.linked_archetype
        ext = self.linked_extension
        ext_props = ext.get_properties()
        asset = archetype.asset

        select_id_int = -1 if select_id is None else select_id

        normal = ext_props.normal.normalized()
        offset_rot_mat = normal.to_track_quat("Y", "Z").to_matrix().to_4x4()

        bottom_matrix = asset.matrix_world @ Matrix.Translation(ext_props.bottom) @ offset_rot_mat
        self.draw_preset_box(bottom_matrix @ Matrix.Scale(0.05, 4), select_id=select_id_int)

        length = (ext_props.top - ext_props.bottom).length
        ladder_shape_matrix = bottom_matrix @ Matrix.Scale(length, 4, (0.0, 0.0, 1.0))
        self.draw_custom_shape(get_ladder_shape(), matrix=ladder_shape_matrix, select_id=select_id)

    def draw_light_shaft_gizmo(self, context, select_id):
        selected_archetype = get_selected_archetype(context)
        selected_extension = get_selected_extension(context)
        archetype = self.linked_archetype
        ext = self.linked_extension
        ext_props = ext.get_properties()
        asset = archetype.asset

        is_active = selected_archetype == archetype and selected_extension == ext
        select_id_int = -1 if select_id is None else select_id

        a = ext_props.cornerA
        b = ext_props.cornerB
        c = ext_props.cornerC
        d = ext_props.cornerD

        rotation_mat = get_extension_offset_rotation(ext).to_matrix().to_4x4()

        o = (a + b + c + d) / 4.0
        translation_mat = Matrix.Translation(o)

        width = (b - a).length
        height = (d - a).length
        scale_mat = Matrix(((width, 0.0, 0.0, 0.0),
                            (0.0, 1.0, 0.0, 0.0),
                            (0.0, 0.0, height, 0.0),
                            (0.0, 0.0, 0.0, 1.0)))
        light_shaft_frame_matrix = asset.matrix_world @ translation_mat @ rotation_mat @ scale_mat
        light_shaft_frame_end_matrix = Matrix.Translation(
            ext_props.direction * ext_props.length) @ light_shaft_frame_matrix

        if not is_active:
            self.draw_custom_shape(get_square_shape(), matrix=light_shaft_frame_matrix, select_id=select_id)
            self.draw_custom_shape(get_square_shape(), matrix=light_shaft_frame_end_matrix, select_id=select_id)

        direction_rotation_mat = ext_props.direction.to_track_quat("Y", "Z").to_matrix().to_4x4()
        direction_scale_mat = Matrix.Scale(ext_props.length, 4, (0.0, 1.0, 0.0))

        line_shape = get_line_shape()

        def _calc_line_matrix(corner: Vector) -> Matrix:
            return asset.matrix_world @  Matrix.Translation(corner) @ direction_rotation_mat @ direction_scale_mat
        self.draw_custom_shape(line_shape, matrix=_calc_line_matrix(a), select_id=select_id)
        self.draw_custom_shape(line_shape, matrix=_calc_line_matrix(b), select_id=select_id)
        self.draw_custom_shape(line_shape, matrix=_calc_line_matrix(c), select_id=select_id)
        self.draw_custom_shape(line_shape, matrix=_calc_line_matrix(d), select_id=select_id)

        if DEBUG_DRAW:
            self.color = 1.0, 0.0, 0.0
            self.draw_preset_box(asset.matrix_world @  Matrix.Translation(a) @ Matrix.Scale(0.015, 4),
                                 select_id=select_id_int)
            self.color = 0.0, 1.0, 0.0
            self.draw_preset_box(asset.matrix_world @  Matrix.Translation(b) @ Matrix.Scale(0.015, 4),
                                 select_id=select_id_int)
            self.color = 0.0, 0.0, 1.0
            self.draw_preset_box(asset.matrix_world @  Matrix.Translation(c) @ Matrix.Scale(0.015, 4),
                                 select_id=select_id_int)
            self.color = 1.0, 1.0, 1.0
            self.draw_preset_box(asset.matrix_world @  Matrix.Translation(d) @ Matrix.Scale(0.015, 4),
                                 select_id=select_id_int)

            sc = Matrix.Scale(0.5, 4)
            self.color = 1.0, 0.0, 0.0
            self.draw_preset_arrow(asset.matrix_world @ translation_mat @ rotation_mat @ sc, axis="POS_X",
                                   select_id=select_id_int)
            self.color = 0.0, 1.0, 0.0
            self.draw_preset_arrow(asset.matrix_world @ translation_mat @ rotation_mat @ sc, axis="POS_Y",
                                   select_id=select_id_int)
            self.color = 0.0, 0.0, 1.0
            self.draw_preset_arrow(asset.matrix_world @ translation_mat @ rotation_mat @ sc, axis="POS_Z",
                                   select_id=select_id_int)

    def invoke(self, context, event):
        selected_ytyp = get_selected_ytyp(context)

        archetypes = list(selected_ytyp.archetypes)
        if self.linked_archetype not in archetypes:
            return {"PASS_THROUGH"}

        extensions = list(self.linked_archetype.extensions)
        if self.linked_extension not in extensions:
            return {"PASS_THROUGH"}

        bpy.ops.sollumz.extension_select(True,
                                         archetype_index=archetypes.index(self.linked_archetype),
                                         extension_index=extensions.index(self.linked_extension))
        return {"PASS_THROUGH"}

    def modal(self, context, event, tweak):
        return {"PASS_THROUGH"}


class SOLLUMZ_OT_extension_select(bpy.types.Operator):
    bl_idname = "sollumz.extension_select"
    bl_label = "Extension Select"
    bl_description = bl_label
    bl_options = {"UNDO", "INTERNAL"}

    archetype_index: bpy.props.IntProperty(name="Archetype Index")
    extension_index: bpy.props.IntProperty(name="Extension Index")

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        selected_ytyp.archetype_index = self.archetype_index
        selected_archetype = get_selected_archetype(context)
        selected_archetype.extension_index = self.extension_index
        tag_redraw(context, space_type="VIEW_3D", region_type="UI")
        tag_redraw(context, space_type="VIEW_3D", region_type="TOOL_PROPS")
        tag_redraw(context, space_type="VIEW_3D", region_type="TOOL_HEADER")
        return {"FINISHED"}


class SOLLUMZ_OT_extension_translate(bpy.types.Operator):
    bl_idname = "sollumz.extension_translate"
    bl_label = "Extension Translate"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    delta_position: bpy.props.FloatVectorProperty(name="Delta Position", subtype="TRANSLATION", size=3)

    def execute(self, context):
        ext = get_selected_extension(context)
        ext_props = ext.get_properties()

        if ext.extension_type == ExtensionType.LADDER:
            ext_props.top += self.delta_position
            ext_props.bottom.xy = ext_props.top.xy
            ext_props.bottom.z = min(ext_props.bottom.z, ext_props.top.z)

            ext_props.offset_position = ext_props.top
        else:
            ext_props.offset_position += self.delta_position

            if ext.extension_type == ExtensionType.LIGHT_SHAFT:
                # move light shaft corners along with the offset_position
                for c in (ext_props.cornerA, ext_props.cornerB, ext_props.cornerC, ext_props.cornerD):
                    c += self.delta_position
        return {"FINISHED"}


class SOLLUMZ_OT_extension_rotate(bpy.types.Operator):
    bl_idname = "sollumz.extension_rotate"
    bl_label = "Extension Rotate"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    delta_rotation: bpy.props.FloatVectorProperty(name="Delta Rotation", subtype="QUATERNION", size=4)

    def execute(self, context):
        ext = get_selected_extension(context)
        if ext.extension_type == ExtensionType.LIGHT_SHAFT:
            self.rotate_light_shaft(ext)
        else:
            ext_props = ext.get_properties()
            ext_props.offset_rotation.rotate(self.delta_rotation)
        return {"FINISHED"}

    def rotate_light_shaft(self, ext: ExtensionProperties):
        ext_props = ext.get_properties()
        a = ext_props.cornerA
        b = ext_props.cornerB
        c = ext_props.cornerC
        d = ext_props.cornerD

        o = (a + b + c + d) / 4.0

        a -= o
        b -= o
        c -= o
        d -= o

        a.rotate(self.delta_rotation)
        b.rotate(self.delta_rotation)
        c.rotate(self.delta_rotation)
        d.rotate(self.delta_rotation)
        ext_props.cornerA = a + o
        ext_props.cornerB = b + o
        ext_props.cornerC = c + o
        ext_props.cornerD = d + o
        ext_props.direction.rotate(self.delta_rotation)


class SOLLUMZ_OT_extension_rotate_ladder_normal(bpy.types.Operator):
    bl_idname = "sollumz.extension_rotate_ladder_normal"
    bl_label = "Extension Rotate Ladder"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    delta_angle: bpy.props.FloatProperty(name="Delta Angle", subtype="ANGLE")

    def execute(self, context):
        ext = get_selected_extension(context)
        ext_props = ext.get_properties()

        ext_props.normal.rotate(Quaternion((0.0, 0.0, 1.0), self.delta_angle))
        return {"FINISHED"}


class SOLLUMZ_OT_extension_translate_ladder_bottom_z(bpy.types.Operator):
    bl_idname = "sollumz.extension_translate_ladder_bottom_z"
    bl_label = "Extension Translate Ladder Bottom"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    delta_z: bpy.props.FloatProperty(name="Delta Z", subtype="DISTANCE")

    def execute(self, context):
        ext = get_selected_extension(context)
        ext_props = ext.get_properties()

        ext_props.bottom.z += self.delta_z
        ext_props.top.z = max(ext_props.top.z, ext_props.bottom.z)
        ext_props.offset_position = ext_props.top
        return {"FINISHED"}


class SOLLUMZ_OT_extension_scale_light_shaft_frame(bpy.types.Operator):
    bl_idname = "sollumz.extension_scale_light_shaft_frame"
    bl_label = "Extension Scale Light Shaft Frame"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    width_scale: bpy.props.FloatProperty(name="Width Scale", subtype="FACTOR")
    height_scale: bpy.props.FloatProperty(name="Height Scale", subtype="FACTOR")

    def execute(self, context):
        ext = get_selected_extension(context)
        if ext.extension_type != ExtensionType.LIGHT_SHAFT:
            return {"CANCELLED"}

        ext_props = ext.get_properties()

        a = ext_props.cornerA
        b = ext_props.cornerB
        c = ext_props.cornerC
        d = ext_props.cornerD

        o = (a + b + c + d) / 4.0
        right = (a - b).normalized()
        up = (a - d).normalized()

        width, height = (a - b).length, (a - d).length
        width *= self.width_scale
        height *= self.height_scale
        width = max(width, 0.01)
        height = max(height, 0.01)
        half_width = width / 2.0
        half_height = height / 2.0
        new_a = o + right * half_width + up * half_height
        new_b = o - right * half_width + up * half_height
        new_c = o - right * half_width - up * half_height
        new_d = o + right * half_width - up * half_height

        ext_props.cornerA = new_a
        ext_props.cornerB = new_b
        ext_props.cornerC = new_c
        ext_props.cornerD = new_d
        return {"FINISHED"}


class SOLLUMZ_OT_extension_offset_light_shaft_end_point(bpy.types.Operator):
    bl_idname = "sollumz.extension_offset_light_shaft_end_point"
    bl_label = "Extension Offset Light Shaft End Point"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    delta_offset: bpy.props.FloatVectorProperty(name="Delta Offset", subtype="TRANSLATION", size=2)

    def execute(self, context):
        ext = get_selected_extension(context)
        if ext.extension_type != ExtensionType.LIGHT_SHAFT:
            return {"CANCELLED"}

        ext_props = ext.get_properties()

        a = ext_props.cornerA
        b = ext_props.cornerB
        c = ext_props.cornerC
        d = ext_props.cornerD

        o = (a + b + c + d) / 4.0
        right = (a - b).normalized()
        up = (a - d).normalized()

        end_vec = o + ext_props.direction * ext_props.length
        end_vec += right * self.delta_offset.x
        end_vec += up * self.delta_offset.y
        ext_props.length = (end_vec - o).length
        ext_props.direction = (end_vec - o).normalized()
        return {"FINISHED"}


class SOLLUMZ_OT_archetype_extensions_detect_ctrl_pressed(bpy.types.Operator):
    """Operator that runs as modal in the background to detect when CTRL is pressed down."""
    bl_idname = "sollumz.archetype_extensions_detect_ctrl_pressed"
    bl_label = "DetectCtrlPressed"
    bl_options = {"INTERNAL"}

    def invoke(self, context, event):
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def modal(self, context, event):
        tool = context.workspace.tools.from_space_view3d_mode(context.mode)
        if tool.idname != "sollumz.archetype_extension":
            return {"FINISHED"}
        gg_props = tool.gizmo_group_properties(SOLLUMZ_GGT_archetype_extensions.bl_idname)
        gg_props.ctrl_pressed = event.ctrl
        return {"PASS_THROUGH"}


class SOLLUMZ_GGT_archetype_extensions(bpy.types.GizmoGroup):
    bl_idname = "SOLLUMZ_GGT_archetype_extensions"
    bl_label = "Archetype Extension Widget"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "SELECT"}

    ctrl_pressed: bpy.props.BoolProperty()

    @property
    def properties(self) -> bpy.types.GizmoGroupProperties:
        """Cannot directly access properties defined in the gizmo group (like ``ctrl_pressed``).
        This returns the struct that holds the properties."""
        context = bpy.context
        tool = context.workspace.tools.from_space_view3d_mode(context.mode)
        gg_props = tool.gizmo_group_properties(SOLLUMZ_GGT_archetype_extensions.bl_idname)
        return gg_props

    @classmethod
    def poll(cls, context):
        return can_draw_gizmos(context)

    def translate_extension(self, context, offset: float, axis: Literal["X", "Y", "Z"]):
        axis_vec = get_transform_axis(get_selected_extension(context), get_selected_archetype(context), axis,
                                      local=is_local_transform(context))

        bpy.ops.sollumz.extension_translate(True, delta_position=axis_vec * offset)

    def rotate_extension(self, context, delta_angle: float, axis: Literal["X", "Y", "Z"]):
        axis_vec = get_transform_axis(get_selected_extension(context), get_selected_archetype(context), axis,
                                      local=is_local_transform(context))

        bpy.ops.sollumz.extension_rotate(True, delta_rotation=Quaternion(axis_vec, delta_angle))

        self.draw_prepare(context)  # refresh view to update dial rotation

    def rotate_extension_ladder_normal(self, context, delta_angle: float):
        ext = get_selected_extension(context)
        if ext.extension_type != ExtensionType.LADDER:
            return

        bpy.ops.sollumz.extension_rotate_ladder_normal(True, delta_angle=delta_angle)

        self.draw_prepare(context)  # refresh view to update dial rotation

    def translate_extension_ladder_bottom_z(self, context, delta_z: float):
        ext = get_selected_extension(context)
        if ext.extension_type != ExtensionType.LADDER:
            return

        bpy.ops.sollumz.extension_translate_ladder_bottom_z(True, delta_z=delta_z)

    def scale_extension_light_shaft_frame(self, context, width_scale: float, height_scale: float):
        ext = get_selected_extension(context)
        if ext.extension_type != ExtensionType.LIGHT_SHAFT:
            return

        bpy.ops.sollumz.extension_scale_light_shaft_frame(True, width_scale=width_scale, height_scale=height_scale)

    def offset_light_shaft_end_point(self, context, delta_offset: Vector):
        ext = get_selected_extension(context)
        if ext.extension_type != ExtensionType.LIGHT_SHAFT:
            return

        bpy.ops.sollumz.extension_offset_light_shaft_end_point(True, delta_offset=delta_offset)

    def get_extension_light_shaft_cage_world_transform(self, context) -> Matrix:
        # Matrix transform with position in the center of the light shaft frame instead
        # of `offset_position`

        ext = get_selected_extension(context)
        if ext.extension_type != ExtensionType.LIGHT_SHAFT:
            return Matrix.Identity(4)

        selected_archetype = get_selected_archetype(context)
        asset = selected_archetype.asset
        ext_props = ext.get_properties()

        a = ext_props.cornerA
        b = ext_props.cornerB
        c = ext_props.cornerC
        d = ext_props.cornerD

        rotation_mat = get_extension_offset_rotation(ext).to_matrix().to_4x4()

        o = (a + b + c + d) / 4.0
        translation_mat = Matrix.Translation(o)

        return asset.matrix_world @ translation_mat @ rotation_mat

    # Gizmos getter/setter handlers
    def handler_get_x(self):
        if not self.translation_gizmo_x_just_called_set:
            self.translation_gizmo_last_offset_x = 0.0
        self.translation_gizmo_x_just_called_set = False
        return self.translation_gizmo_last_offset_x

    def handler_get_y(self):
        if not self.translation_gizmo_y_just_called_set:
            self.translation_gizmo_last_offset_y = 0.0
        self.translation_gizmo_y_just_called_set = False
        return self.translation_gizmo_last_offset_y

    def handler_get_z(self):
        if not self.translation_gizmo_z_just_called_set:
            self.translation_gizmo_last_offset_z = 0.0
        self.translation_gizmo_z_just_called_set = False
        return self.translation_gizmo_last_offset_z

    def handler_set_x(self, value):
        delta_offset = value - self.translation_gizmo_last_offset_x
        self.translation_gizmo_last_offset_x = value
        self.translate_extension(bpy.context, delta_offset, "X")
        self.translation_gizmo_x_just_called_set = True

    def handler_set_y(self, value):
        delta_offset = value - self.translation_gizmo_last_offset_y
        self.translation_gizmo_last_offset_y = value
        self.translate_extension(bpy.context, delta_offset, "Y")
        self.translation_gizmo_y_just_called_set = True

    def handler_set_z(self, value):
        delta_offset = value - self.translation_gizmo_last_offset_z
        self.translation_gizmo_last_offset_z = value
        self.translate_extension(bpy.context, delta_offset, "Z")
        self.translation_gizmo_z_just_called_set = True

    def handler_get_rotation_x(self):
        self.rotation_gizmo_last_angle = 0.0
        return 0.0

    def handler_get_rotation_y(self):
        self.rotation_gizmo_last_angle = 0.0
        return 0.0

    def handler_get_rotation_z(self):
        self.rotation_gizmo_last_angle = 0.0
        return 0.0

    def handler_set_rotation_x(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_extension(bpy.context, -delta_angle, "X")

    def handler_set_rotation_y(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_extension(bpy.context, -delta_angle, "Y")

    def handler_set_rotation_z(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_extension(bpy.context, -delta_angle, "Z")

    def handler_get_ladder_bottom_z(self):
        if not self.ladder_bottom_gizmo_just_called_set:
            self.ladder_bottom_gizmo_last_offset_z = 0.0
        self.ladder_bottom_gizmo_just_called_set = False
        return self.ladder_bottom_gizmo_last_offset_z

    def handler_set_ladder_bottom_z(self, value):
        delta_z = self.ladder_bottom_gizmo_last_offset_z - value
        self.ladder_bottom_gizmo_last_offset_z = value
        self.translate_extension_ladder_bottom_z(bpy.context, delta_z)
        self.ladder_bottom_gizmo_just_called_set = True

    def handler_get_ladder_normal_angle(self):
        self.rotation_gizmo_last_angle = 0.0
        return 0.0

    def handler_set_ladder_normal_angle(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_extension_ladder_normal(bpy.context, -delta_angle)

    def handler_get_light_shaft_transform(self):
        return [v for row in self.light_shaft_cage_last_transform.transposed() for v in row]

    def handler_set_light_shaft_transform(self, value):
        m = Matrix((value[0:4], value[4:8], value[8:12], value[12:16]))
        m.transpose()
        m = self.apply_light_shaft_cage_scale_clamping(m)
        delta_transform = self.light_shaft_cage_last_transform.inverted() @ m
        self.light_shaft_cage_last_transform = m

        delta_width_scale, delta_height_scale, _ = delta_transform.to_3x3() @ Vector((1.0, 1.0, 0.0))
        self.scale_extension_light_shaft_frame(bpy.context, delta_width_scale, delta_height_scale)

    def handler_get_light_shaft_end_transform(self):
        return [v for row in self.light_shaft_cage_end_last_transform.transposed() for v in row]

    def handler_set_light_shaft_end_transform(self, value):
        m = Matrix((value[0:4], value[4:8], value[8:12], value[12:16]))
        m.transpose()
        m = self.apply_light_shaft_cage_end_snapping(m)
        delta_transform = self.light_shaft_cage_end_last_transform.inverted() @ m
        self.light_shaft_cage_end_last_transform = m

        self.offset_light_shaft_end_point(bpy.context, delta_transform.translation.xy)

    def handler_set_light_shaft_direction_rotation_x(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_light_shaft_direction(bpy.context, -delta_angle, "X")

    def handler_set_light_shaft_direction_rotation_y(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_light_shaft_direction(bpy.context, -delta_angle, "Y")

    def handler_set_light_shaft_direction_rotation_z(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_light_shaft_direction(bpy.context, -delta_angle, "Z")

    def apply_light_shaft_cage_scale_clamping(self, m: Matrix) -> Matrix:
        """Returns a new scale matrix clamped to avoid dimensions of size 0 on the light shaft cage."""
        MIN_SIZE = 0.02
        base_width, base_height = self.light_shaft_cage.dimensions
        min_width_scale = MIN_SIZE / base_width
        min_height_scale = MIN_SIZE / base_height

        width_scale, height_scale, _ = m.to_3x3() @ Vector((1.0, 1.0, 0.0))

        new_width_scale = max(min_width_scale, width_scale)
        new_height_scale = max(min_height_scale, height_scale)
        return Matrix(((new_width_scale, 0.0, 0.0, 0.0),
                       (0.0, new_height_scale, 0.0, 0.0),
                       (0.0, 0.0, 1.0, 0.0),
                       (0.0, 0.0, 0.0, 1.0)))

    def apply_light_shaft_cage_end_snapping(self, m: Matrix) -> Matrix:
        """Returns a new offset matrix with snapping applied if required."""
        m = m.copy()
        if self.properties.ctrl_pressed:
            if self.light_shaft_cage_end_snap_origin_transform is None:
                self.light_shaft_cage_end_snap_origin_transform = m.copy()

            snap_delta_transform = self.light_shaft_cage_end_snap_origin_transform.inverted() @ m
            if abs(snap_delta_transform.translation.x) > abs(snap_delta_transform.translation.y):
                m.translation.y = self.light_shaft_cage_end_snap_origin_transform.translation.y
            else:
                m.translation.x = self.light_shaft_cage_end_snap_origin_transform.translation.x
        else:
            self.light_shaft_cage_end_snap_origin_transform = None

        return m

    def setup(self, context):
        theme = context.preferences.themes[0]
        axis_x_color = theme.user_interface.axis_x
        axis_y_color = theme.user_interface.axis_y
        axis_z_color = theme.user_interface.axis_z
        axis_alpha = 0.6
        axis_alpha_hi = 1.0

        arrow_x = self.gizmos.new("GIZMO_GT_arrow_3d")
        arrow_x.select_bias = 2.0
        arrow_x.line_width = 3
        arrow_x.color = axis_x_color
        arrow_x.color_highlight = axis_x_color
        arrow_x.alpha = axis_alpha
        arrow_x.alpha_highlight = axis_alpha_hi
        arrow_x.use_draw_modal = True
        arrow_x.use_draw_value = True

        arrow_y = self.gizmos.new("GIZMO_GT_arrow_3d")
        arrow_y.select_bias = 2.0
        arrow_y.line_width = 3
        arrow_y.color = axis_y_color
        arrow_y.color_highlight = axis_y_color
        arrow_y.alpha = axis_alpha
        arrow_y.alpha_highlight = axis_alpha_hi
        arrow_y.use_draw_modal = True
        arrow_y.use_draw_value = True

        arrow_z = self.gizmos.new("GIZMO_GT_arrow_3d")
        arrow_z.select_bias = 2.0
        arrow_z.line_width = 3
        arrow_z.color = axis_z_color
        arrow_z.color_highlight = axis_z_color
        arrow_z.alpha = axis_alpha
        arrow_z.alpha_highlight = axis_alpha_hi
        arrow_z.use_draw_modal = True
        arrow_z.use_draw_value = True

        dial_x = self.gizmos.new("GIZMO_GT_dial_3d")
        dial_x.select_bias = 2.0
        dial_x.scale_basis = 0.6
        dial_x.line_width = 3
        dial_x.color = axis_x_color
        dial_x.color_highlight = axis_x_color
        dial_x.alpha = axis_alpha
        dial_x.alpha_highlight = axis_alpha_hi
        dial_x.use_draw_modal = True
        dial_x.use_draw_value = True

        dial_y = self.gizmos.new("GIZMO_GT_dial_3d")
        dial_y.select_bias = 2.0
        dial_y.scale_basis = 0.6
        dial_y.line_width = 3
        dial_y.color = axis_y_color
        dial_y.color_highlight = axis_y_color
        dial_y.alpha = axis_alpha
        dial_y.alpha_highlight = axis_alpha_hi
        dial_y.use_draw_modal = True
        dial_y.use_draw_value = True

        dial_z = self.gizmos.new("GIZMO_GT_dial_3d")
        dial_z.select_bias = 2.0
        dial_z.scale_basis = 0.6
        dial_z.line_width = 3
        dial_z.color = axis_z_color
        dial_z.color_highlight = axis_z_color
        dial_z.alpha = axis_alpha
        dial_z.alpha_highlight = axis_alpha_hi
        dial_z.use_draw_modal = True
        dial_z.use_draw_value = True

        ladder_bottom_arrow = self.gizmos.new("GIZMO_GT_arrow_3d")
        ladder_bottom_arrow.select_bias = 2.0
        ladder_bottom_arrow.draw_style = "BOX"
        ladder_bottom_arrow.length *= 0.5
        ladder_bottom_arrow.line_width = 3
        ladder_bottom_arrow.color = axis_z_color
        ladder_bottom_arrow.color_highlight = axis_z_color
        ladder_bottom_arrow.alpha = axis_alpha
        ladder_bottom_arrow.alpha_highlight = axis_alpha_hi
        ladder_bottom_arrow.use_draw_modal = True
        ladder_bottom_arrow.use_draw_value = True
        ladder_bottom_arrow.hide = True

        ladder_normal_dial = self.gizmos.new("GIZMO_GT_dial_3d")
        ladder_normal_dial.select_bias = 2.0
        ladder_normal_dial.scale_basis = 0.725
        ladder_normal_dial.line_width = 3
        ladder_normal_dial.color = axis_z_color
        ladder_normal_dial.color_highlight = axis_z_color
        ladder_normal_dial.alpha = axis_alpha
        ladder_normal_dial.alpha_highlight = axis_alpha_hi
        ladder_normal_dial.use_draw_modal = True
        ladder_normal_dial.use_draw_value = True
        ladder_normal_dial.hide = True

        light_shaft_cage = self.gizmos.new("GIZMO_GT_cage_2d")
        light_shaft_cage.select_bias = 4.0
        light_shaft_cage.scale_basis = 0.6
        light_shaft_cage.draw_style = "BOX_TRANSFORM"
        light_shaft_cage.transform = {"SCALE"}
        light_shaft_cage.color = theme.view_3d.object_active
        light_shaft_cage.color_highlight = theme.view_3d.object_active
        light_shaft_cage.alpha = axis_alpha
        light_shaft_cage.alpha_highlight = axis_alpha_hi
        light_shaft_cage.use_draw_modal = True
        light_shaft_cage.use_draw_value = True
        light_shaft_cage.use_draw_offset_scale = True
        light_shaft_cage.hide = True

        light_shaft_cage_end = self.gizmos.new("GIZMO_GT_cage_2d")
        light_shaft_cage_end.select_bias = 5.0
        light_shaft_cage_end.scale_basis = 0.6
        light_shaft_cage_end.draw_style = "BOX_TRANSFORM"
        light_shaft_cage_end.draw_options = {"XFORM_CENTER_HANDLE"}
        light_shaft_cage_end.transform = {"TRANSLATE"}
        light_shaft_cage_end.color = theme.view_3d.object_active
        light_shaft_cage_end.color_highlight = theme.view_3d.object_active
        light_shaft_cage_end.alpha = axis_alpha
        light_shaft_cage_end.alpha_highlight = axis_alpha_hi
        light_shaft_cage_end.use_draw_modal = True
        light_shaft_cage_end.use_draw_value = True
        light_shaft_cage_end.use_draw_offset_scale = True
        light_shaft_cage_end.hide = True

        self.translation_gizmos = (arrow_x, arrow_y, arrow_z)
        self.translation_gizmo_last_offset_x = 0.0
        self.translation_gizmo_last_offset_y = 0.0
        self.translation_gizmo_last_offset_z = 0.0
        # Arrow gizmos call `set` -> `get` when in-use; when released it calls `get` once again
        # (`set` -> `get` -> `get`), we use this variables to detect the last `get` and reset the
        # `last_offset_*` variables to 0.0, otherwise the arrow gizmo is placed at the last offset.
        self.translation_gizmo_x_just_called_set = False
        self.translation_gizmo_y_just_called_set = False
        self.translation_gizmo_z_just_called_set = False

        self.rotation_gizmos = (dial_x, dial_y, dial_z)
        self.rotation_gizmo_last_angle = 0.0

        self.ladder_bottom_arrow = ladder_bottom_arrow
        self.ladder_bottom_gizmo_last_offset_z = 0.0
        self.ladder_bottom_gizmo_just_called_set = False
        self.ladder_normal_dial = ladder_normal_dial

        self.light_shaft_cage = light_shaft_cage
        self.light_shaft_cage_last_transform = Matrix.Identity(4)
        self.light_shaft_cage_end = light_shaft_cage_end
        self.light_shaft_cage_end_last_transform = Matrix.Identity(4)
        self.light_shaft_cage_end_snap_origin_transform = None

        self.extension_gizmos = []

        # Assign handlers to all interaction gizmos
        arrow_x.target_set_handler("offset", get=self.handler_get_x, set=self.handler_set_x)
        arrow_y.target_set_handler("offset", get=self.handler_get_y, set=self.handler_set_y)
        arrow_z.target_set_handler("offset", get=self.handler_get_z, set=self.handler_set_z)
        dial_x.target_set_handler("offset", get=self.handler_get_rotation_x, set=self.handler_set_rotation_x)
        dial_y.target_set_handler("offset", get=self.handler_get_rotation_y, set=self.handler_set_rotation_y)
        dial_z.target_set_handler("offset", get=self.handler_get_rotation_z, set=self.handler_set_rotation_z)
        ladder_bottom_arrow.target_set_handler("offset",
                                               get=self.handler_get_ladder_bottom_z,
                                               set=self.handler_set_ladder_bottom_z)
        ladder_normal_dial.target_set_handler("offset",
                                              get=self.handler_get_ladder_normal_angle,
                                              set=self.handler_set_ladder_normal_angle)
        light_shaft_cage.target_set_handler("matrix",
                                            get=self.handler_get_light_shaft_transform,
                                            set=self.handler_set_light_shaft_transform)
        light_shaft_cage_end.target_set_handler("matrix",
                                                get=self.handler_get_light_shaft_end_transform,
                                                set=self.handler_set_light_shaft_end_transform)

        # Cannot call operators here, use timers to call it as soon as possible
        def _invoke_archetype_extensions_detect_ctrl_pressed_operator():
            bpy.ops.sollumz.archetype_extensions_detect_ctrl_pressed("INVOKE_DEFAULT")
        bpy.app.timers.register(_invoke_archetype_extensions_detect_ctrl_pressed_operator, first_interval=0.0)

    def refresh(self, context):
        selected_extension = get_selected_extension(context)
        # By default, hide all interaction gizmos (no extension is selected)
        hide_translation_gizmos = True
        hide_rotation_gizmos = True
        hide_ladder_gizmos = True
        hide_light_shaft_gizmos = True

        if selected_extension is not None:
            # Show necessary interaction gizmos for the current extension type
            is_ladder = selected_extension.extension_type == ExtensionType.LADDER
            is_light_shaft = selected_extension.extension_type == ExtensionType.LIGHT_SHAFT
            has_rotation = hasattr(selected_extension.get_properties(), "offset_rotation")

            hide_translation_gizmos = False
            hide_rotation_gizmos = not has_rotation and not is_light_shaft
            hide_ladder_gizmos = not is_ladder
            hide_light_shaft_gizmos = not is_light_shaft

        arrow_x, arrow_y, arrow_z = self.translation_gizmos
        arrow_x.hide = hide_translation_gizmos
        arrow_y.hide = hide_translation_gizmos
        arrow_z.hide = hide_translation_gizmos

        dial_x, dial_y, dial_z = self.rotation_gizmos
        dial_x.hide = hide_rotation_gizmos
        dial_y.hide = hide_rotation_gizmos
        dial_z.hide = hide_rotation_gizmos

        self.ladder_bottom_arrow.hide = hide_ladder_gizmos
        self.ladder_normal_dial.hide = hide_ladder_gizmos

        self.light_shaft_cage.hide = hide_light_shaft_gizmos
        self.light_shaft_cage_end.hide = hide_light_shaft_gizmos

        # Update linked extensions, do it always to prevent old references to
        # deleted PropertyGroups. It could cause Blender to crash.
        last_used_gizmo = -1
        for i, (archetype, ext) in enumerate(iter_archetype_extensions(context)):
            if i < len(self.extension_gizmos):
                gz = self.extension_gizmos[i]
            else:
                gz = self.gizmos.new(SOLLUMZ_GT_archetype_extension.bl_idname)
                gz.use_draw_scale = True
                self.extension_gizmos.append(gz)

            gz.linked_archetype = archetype
            gz.linked_extension = ext
            gz.hide = False
            last_used_gizmo = i

        # Hide unused gizmos
        for i in range(last_used_gizmo + 1, len(self.extension_gizmos)):
            self.extension_gizmos[i].hide = True

    def draw_prepare(self, context):
        def _prepare_arrow(arrow_gizmo, matrix_basis):
            if arrow_gizmo.is_modal:
                arrow_gizmo.draw_options = {"ORIGIN", "STEM"}
            else:
                arrow_gizmo.matrix_basis = matrix_basis
                arrow_gizmo.draw_options = {"STEM"}

        def _prepare_dial(dial_gizmo, matrix_basis, clip=True):
            if dial_gizmo.is_modal:
                dial_gizmo.draw_options = {"ANGLE_VALUE"}
            else:
                dial_gizmo.matrix_basis = matrix_basis
                dial_gizmo.draw_options = {"CLIP"} if clip else set()

        self.refresh(context)  # in case the selected archetype or extension changed

        selected_extension = get_selected_extension(context)
        if selected_extension is None:
            # The interaction gizmos are hidden if no extension is selected
            return

        selected_archetype = get_selected_archetype(context)

        ext_mat = get_extension_world_matrix(selected_extension, selected_archetype)
        if not is_local_transform(context):
            ext_mat = Matrix.Translation(ext_mat.to_translation())

        x_matrix = ext_mat @ Matrix.Rotation(math.radians(90), 4, "Y")
        y_matrix = ext_mat @ Matrix.Rotation(math.radians(-90), 4, "X")
        z_matrix = ext_mat

        arrow_x, arrow_y, arrow_z = self.translation_gizmos
        _prepare_arrow(arrow_x, x_matrix)
        _prepare_arrow(arrow_y, y_matrix)
        _prepare_arrow(arrow_z, z_matrix)

        dial_x, dial_y, dial_z = self.rotation_gizmos
        _prepare_dial(dial_x, x_matrix)
        _prepare_dial(dial_y, y_matrix)
        _prepare_dial(dial_z, z_matrix)

        if dial_x.is_modal or dial_y.is_modal or dial_z.is_modal:
            # While a rotation gizmo is in-use, hide all other translation/rotation gizmos
            arrow_x.hide = True
            arrow_y.hide = True
            arrow_z.hide = True
            dial_x.hide = not dial_x.is_modal
            dial_y.hide = not dial_y.is_modal
            dial_z.hide = not dial_z.is_modal
        elif arrow_x.is_modal or arrow_y.is_modal or arrow_z.is_modal:
            # While translation gizmos are in-use, hide the rotation gizmos
            dial_x.hide = True
            dial_y.hide = True
            dial_z.hide = True

        if not self.ladder_bottom_arrow.hide:
            top_mat = get_extension_world_matrix(selected_extension, selected_archetype)
            bottom_mat = get_extension_ladder_bottom_world_matrix(selected_extension, selected_archetype)

            bottom_arrow_mat = bottom_mat @ Matrix.Rotation(math.radians(-180), 4, 'X')
            _prepare_arrow(self.ladder_bottom_arrow, bottom_arrow_mat)

            middle = (top_mat.translation + bottom_mat.translation) / 2.0
            normal_dial_mat = Matrix.LocRotScale(middle, top_mat.to_quaternion(), (1.0, 1.0, 1.0))
            _prepare_dial(self.ladder_normal_dial, normal_dial_mat, clip=False)

        if not self.light_shaft_cage.hide:
            selected_extension = get_selected_extension(context)
            ext_props = selected_extension.get_properties()

            light_shaft_transform = (self.get_extension_light_shaft_cage_world_transform(context) @
                                     Matrix.Rotation(math.radians(90), 4, 'X'))

            if not self.light_shaft_cage.is_modal:
                self.light_shaft_cage.dimensions = get_extension_light_shaft_dimensions(selected_extension)
                self.light_shaft_cage.matrix_basis = light_shaft_transform
                # Cage gizmo stores edited transform in `matrix_offset`, so reset it when it is not modal
                # anymore as we update `dimensions` instead
                self.light_shaft_cage.matrix_offset = Matrix.Identity(4)
                self.light_shaft_cage_last_transform = Matrix.Identity(4)
            else:
                m = self.apply_light_shaft_cage_scale_clamping(self.light_shaft_cage.matrix_offset)
                self.light_shaft_cage.matrix_offset = m

            if not self.light_shaft_cage_end.is_modal:
                self.light_shaft_cage_end.dimensions = get_extension_light_shaft_dimensions(selected_extension)
                self.light_shaft_cage_end.matrix_basis = (Matrix.Translation(ext_props.direction * ext_props.length) @
                                                          light_shaft_transform)
                self.light_shaft_cage_end.matrix_offset = Matrix.Identity(4)
                self.light_shaft_cage_end_last_transform = Matrix.Identity(4)
            else:
                m = self.apply_light_shaft_cage_end_snapping(self.light_shaft_cage_end.matrix_offset)
                self.light_shaft_cage_end.matrix_offset = m
