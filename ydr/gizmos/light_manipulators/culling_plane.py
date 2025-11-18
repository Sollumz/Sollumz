import bpy
from bpy.types import (
    Context,
    Gizmo,
    GizmoGroup,
    Operator,
    Object,
    WorkSpaceTool,
)
import math
from typing import Literal, Optional
from mathutils import Matrix, Vector, Quaternion
from ....sollumz_properties import LightType, SollumType
from ....icons import ICON_GEOM_TOOL
from ....tools.blenderhelper import tag_redraw


def is_sollumz_light_obj(obj: Optional[Object]) -> bool:
    if obj is None or obj.type != "LIGHT" or obj.sollum_type != SollumType.LIGHT:
        return False

    light = obj.data
    return light.sollum_type != LightType.NONE


class LightCullingPlaneTool(WorkSpaceTool):
    bl_space_type = "VIEW_3D"
    bl_context_mode = "OBJECT"

    bl_idname = "sollumz.light_culling_planes"
    bl_label = "Edit Light Culling Planes"
    bl_description = "Edit culling planes of light objects"
    bl_icon = ICON_GEOM_TOOL

    def draw_settings(context, layout, tool):
        light_obj = context.view_layer.objects.active
        if not is_sollumz_light_obj(light_obj):
            return

        light = light_obj.data
        light_flags = light.light_flags
        light_props = light.light_properties

        layout.prop(light_flags, "enable_culling_plane", text="Culling Plane")
        row = layout.row()
        row.active = light_flags.enable_culling_plane

        row.prop(light_props, "culling_plane_offset", text="Offset")

        subrow = row.row(align=True)
        subrow.scale_x = 0.8
        subrow.operator(SOLLUMZ_OT_light_culling_plane_flip.bl_idname, text="Flip")

        subrow = row.row(align=True)
        subrow.scale_x = 0.65
        for label, normal in (
            ("+X", (1.0, 0.0, 0.0)),
            ("+Y", (0.0, 1.0, 0.0)),
            ("+Z", (0.0, 0.0, 1.0)),
            ("-X", (-1.0, 0.0, 0.0)),
            ("-Y", (0.0, -1.0, 0.0)),
            ("-Z", (0.0, 0.0, -1.0)),
        ):
            subrow.operator(SOLLUMZ_OT_light_culling_plane_set_normal.bl_idname, text=label).normal = normal


class SOLLUMZ_OT_light_culling_plane_set_normal(Operator):
    bl_idname = "sollumz.light_culling_plane_set_normal"
    bl_label = "Set Culling Plane Normal"
    bl_options = {"UNDO"}

    normal: bpy.props.FloatVectorProperty(name="Normal", size=3, subtype="XYZ")

    @classmethod
    def description(cls, context: Context, properties) -> str:
        return f"Sets the culling plane normal of the selected lights to {tuple(properties.normal)}"

    def execute(self, context: Context):
        for obj in context.selected_objects:
            if not is_sollumz_light_obj(obj):
                continue

            light_props = obj.data.light_properties
            light_props.culling_plane_normal = self.normal

        tag_redraw(context, space_type="PROPERTIES", region_type="WINDOW")
        tag_redraw(context, space_type="VIEW_3D", region_type="WINDOW")
        return {"FINISHED"}


class SOLLUMZ_OT_light_culling_plane_flip(Operator):
    bl_idname = "sollumz.light_culling_plane_flip"
    bl_label = "Flip Culling Plane"
    bl_description = "Flip the culling plane of the selected lights, changing on which side the light is visible"
    bl_options = {"UNDO"}

    def execute(self, context: Context):
        for obj in context.selected_objects:
            if not is_sollumz_light_obj(obj):
                continue

            light_props = obj.data.light_properties
            light_props.culling_plane_normal *= -1
            light_props.culling_plane_offset *= -1

        tag_redraw(context, space_type="PROPERTIES", region_type="WINDOW")
        tag_redraw(context, space_type="VIEW_3D", region_type="WINDOW")
        return {"FINISHED"}


class SOLLUMZ_OT_light_culling_plane_translate(Operator):
    bl_idname = "sollumz.light_culling_plane_translate"
    bl_label = "Light Culling Plane Translate"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    delta_offset: bpy.props.FloatProperty(name="Delta Offset")

    def execute(self, context: Context):
        light_obj = context.view_layer.objects.active
        light = light_obj.data
        light.light_properties.culling_plane_offset += self.delta_offset
        return {"FINISHED"}


class SOLLUMZ_OT_light_culling_plane_rotate(Operator):
    bl_idname = "sollumz.light_culling_plane_rotate"
    bl_label = "Light Culling Plane Rotate"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    delta_rotation: bpy.props.FloatVectorProperty(name="Delta Rotation", subtype="QUATERNION", size=4)

    def execute(self, context: Context):
        light_obj = context.view_layer.objects.active
        light = light_obj.data
        normal = light.light_properties.culling_plane_normal
        if normal == Vector((0.0, 0.0, 0.0)):
            normal = Vector((0.0, 0.0, 1.0))
        normal.rotate(self.delta_rotation)
        normal.normalize()
        light.light_properties.culling_plane_normal = normal
        return {"FINISHED"}


# TODO: get_transform_axis and rotation dials mostly taken from archetype extension gizmos code.
# Refactor to share code between similar gizmos.

def get_transform_axis(light_obj: Object, axis: Literal["X", "Y", "Z"]) -> Vector:
    if axis == "X":
        axis_vec = Vector((1.0, 0.0, 0.0))
    elif axis == "Y":
        axis_vec = Vector((0.0, 1.0, 0.0))
    elif axis == "Z":
        axis_vec = Vector((0.0, 0.0, 1.0))

    return axis_vec


class CullingPlaneLightManipulator:
    gg: GizmoGroup
    translation_gizmo: Gizmo
    translation_gizmo_last_offset: float
    # Arrow gizmos call `set` -> `get` when in-use; when released it calls `get` once again
    # (`set` -> `get` -> `get`), we use this variables to detect the last `get` and reset the
    # `last_offset_*` variables to 0.0, otherwise the arrow gizmo is placed at the last offset.
    translation_gizmo_just_called_set: bool
    rotation_gizmos: tuple[Gizmo, Gizmo, Gizmo]
    rotation_gizmo_last_offset: float

    def __init__(self, gg: GizmoGroup):
        self.gg = gg

        theme = bpy.context.preferences.themes[0]
        theme_ui = theme.user_interface
        axis_x_color = theme_ui.axis_x
        axis_y_color = theme_ui.axis_y
        axis_z_color = theme_ui.axis_z
        axis_alpha = 0.6
        axis_alpha_hi = 1.0

        arrow = gg.gizmos.new("GIZMO_GT_arrow_3d")
        arrow.select_bias = 1.0
        arrow.line_width = 3
        arrow.color = theme_ui.gizmo_primary
        arrow.color_highlight = theme_ui.gizmo_hi
        arrow.use_draw_modal = True
        arrow.use_draw_value = True
        arrow.use_draw_hover = True
        arrow.draw_style = "CROSS"

        dial_x = gg.gizmos.new("GIZMO_GT_dial_3d")
        dial_x.select_bias = 1.0
        dial_x.scale_basis = 0.6
        dial_x.line_width = 3
        dial_x.color = axis_x_color
        dial_x.color_highlight = axis_x_color
        dial_x.alpha = axis_alpha
        dial_x.alpha_highlight = axis_alpha_hi
        dial_x.use_draw_modal = True
        dial_x.use_draw_value = True

        dial_y = gg.gizmos.new("GIZMO_GT_dial_3d")
        dial_y.select_bias = 1.0
        dial_y.scale_basis = 0.6
        dial_y.line_width = 3
        dial_y.color = axis_y_color
        dial_y.color_highlight = axis_y_color
        dial_y.alpha = axis_alpha
        dial_y.alpha_highlight = axis_alpha_hi
        dial_y.use_draw_modal = True
        dial_y.use_draw_value = True

        dial_z = gg.gizmos.new("GIZMO_GT_dial_3d")
        dial_z.select_bias = 1.0
        dial_z.scale_basis = 0.6
        dial_z.line_width = 3
        dial_z.color = axis_z_color
        dial_z.color_highlight = axis_z_color
        dial_z.alpha = axis_alpha
        dial_z.alpha_highlight = axis_alpha_hi
        dial_z.use_draw_modal = True
        dial_z.use_draw_value = True

        self.translation_gizmo = arrow
        self.translation_gizmo_last_offset = 0.0
        self.translation_gizmo_just_called_set = False
        self.rotation_gizmos = (dial_x, dial_y, dial_z)
        self.rotation_gizmo_last_angle = 0.0

        arrow.target_set_handler("offset", get=self.handler_get_offset, set=self.handler_set_offset)
        dial_x.target_set_handler("offset", get=self.handler_get_rotation_x, set=self.handler_set_rotation_x)
        dial_y.target_set_handler("offset", get=self.handler_get_rotation_y, set=self.handler_set_rotation_y)
        dial_z.target_set_handler("offset", get=self.handler_get_rotation_z, set=self.handler_set_rotation_z)

    def draw_prepare(self, context: Context, active_light_obj: Optional[Object]):
        arrow = self.translation_gizmo
        dial_x, dial_y, dial_z = self.rotation_gizmos
        if active_light_obj is None or not active_light_obj.data.light_flags.enable_culling_plane:
            arrow.hide = True
            dial_x.hide = True
            dial_y.hide = True
            dial_z.hide = True
            return

        light_obj = context.view_layer.objects.active
        light = light_obj.data
        light_translation_mat = Matrix.Translation(light_obj.matrix_world.translation)

        parent_rot_mat = (
            parent_obj.matrix_world.to_3x3().to_4x4()
            if (parent_obj := light_obj.parent)
            else Matrix.Identity(4)
        )

        plane_normal = light.light_properties.culling_plane_normal
        if plane_normal == Vector((0.0, 0.0, 0.0)):
            plane_normal = Vector((0.0, 0.0, 1.0))

        plane_rot_mat = plane_normal.to_track_quat("Z", "Y").to_matrix().to_4x4()
        plane_offset_mat = Matrix.Translation((0.0, 0.0, -light.light_properties.culling_plane_offset))
        plane_mat = light_translation_mat @ parent_rot_mat @ plane_rot_mat @ plane_offset_mat

        dial_mat = light_translation_mat @ parent_rot_mat
        x_matrix = dial_mat @ Matrix.Rotation(math.radians(90), 4, "Y")
        y_matrix = dial_mat @ Matrix.Rotation(math.radians(-90), 4, "X")
        z_matrix = dial_mat

        arrow.hide = False
        if arrow.is_modal:
            arrow.draw_options = {"ORIGIN", "STEM"}
        else:
            arrow.matrix_basis = plane_mat
            arrow.draw_options = {"STEM"}

        tool = context.workspace.tools.from_space_view3d_mode(context.mode)
        if tool.idname == LightCullingPlaneTool.bl_idname:
            # Only show rotation dials when the edit tool is selected
            for dial_gizmo, matrix_basis in (
                (dial_x, x_matrix),
                (dial_y, y_matrix),
                (dial_z, z_matrix),
            ):
                dial_gizmo.hide = False
                if dial_gizmo.is_modal:
                    dial_gizmo.draw_options = {"ANGLE_VALUE"}
                else:
                    dial_gizmo.matrix_basis = matrix_basis
                    dial_gizmo.draw_options = {"CLIP"}

            if dial_x.is_modal or dial_y.is_modal or dial_z.is_modal:
                # While a rotation gizmo is in-use, hide the other rotation gizmos
                dial_x.hide = not dial_x.is_modal
                dial_y.hide = not dial_y.is_modal
                dial_z.hide = not dial_z.is_modal
            elif arrow.is_modal:
                # While translation gizmo is in-use, hide the rotation gizmos
                dial_x.hide = True
                dial_y.hide = True
                dial_z.hide = True
        else:
            dial_x.hide = True
            dial_y.hide = True
            dial_z.hide = True

    def translate_culling_plane(self, context: Context, offset: float):
        bpy.ops.sollumz.light_culling_plane_translate(True, delta_offset=offset)

    def rotate_culling_plane_normal(self, context: Context, delta_angle: float, axis: Literal["X", "Y", "Z"]):
        light_obj = context.view_layer.objects.active
        axis_vec = get_transform_axis(light_obj, axis)

        bpy.ops.sollumz.light_culling_plane_rotate(True, delta_rotation=Quaternion(axis_vec, delta_angle))

        self.gg.draw_prepare(context)  # refresh view to update dial rotation

    # Gizmos getter/setter handlers
    def handler_get_offset(self):
        if not self.translation_gizmo_just_called_set:
            self.translation_gizmo_last_offset = 0.0
        self.translation_gizmo_just_called_set = False
        return self.translation_gizmo_last_offset

    def handler_set_offset(self, value):
        delta_offset = value - self.translation_gizmo_last_offset
        self.translation_gizmo_last_offset = value
        self.translate_culling_plane(bpy.context, -delta_offset)
        self.translation_gizmo_just_called_set = True

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
        self.rotate_culling_plane_normal(bpy.context, -delta_angle, "X")

    def handler_set_rotation_y(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_culling_plane_normal(bpy.context, -delta_angle, "Y")

    def handler_set_rotation_z(self, value):
        delta_angle = value - self.rotation_gizmo_last_angle
        self.rotation_gizmo_last_angle = value
        self.rotate_culling_plane_normal(bpy.context, -delta_angle, "Z")
