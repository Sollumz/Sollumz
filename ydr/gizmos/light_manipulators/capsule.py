import bpy
from bpy.types import (
    Context,
    Gizmo,
    GizmoGroup,
    Operator,
    Object,
)
import math
from typing import Optional
from mathutils import Matrix, Vector
from ....sollumz_properties import SollumType, LightType


class SOLLUMZ_OT_capsule_light_set_size(Operator):
    bl_idname = "sollumz.capsule_light_set_size"
    bl_label = "Capsule Light Scale"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    length: bpy.props.FloatProperty(name="Length")
    radius: bpy.props.FloatProperty(name="Radius")

    def execute(self, context: Context):
        light_obj = context.view_layer.objects.active
        if light_obj.type != "LIGHT" or light_obj.sollum_type != SollumType.LIGHT:
            return {"CANCELLED"}

        light = light_obj.data
        light.light_properties.extent[0] = self.length
        light.cutoff_distance = self.radius
        return {"FINISHED"}


class CapsuleLightManipulator:
    cage: Gizmo
    cage_last_transform: Matrix

    def __init__(self, gg: GizmoGroup):
        cage = gg.gizmos.new("GIZMO_GT_cage_2d")
        cage.select_bias = 1.0
        cage.draw_style = "BOX_TRANSFORM"
        cage.transform = {"SCALE"}
        cage.use_draw_hover = True
        cage.use_draw_modal = True
        cage.use_draw_value = True
        cage.use_draw_offset_scale = True
        cage.hide = False
        cage.target_set_handler("matrix", get=self.handler_get_cage_transform, set=self.handler_set_cage_transform)

        self.cage = cage
        self.cage_last_transform = Matrix.Identity(4)

    def draw_prepare(self, context: Context, active_light_obj: Optional[Object]):
        cage = self.cage
        if active_light_obj is None or active_light_obj.data.sollum_type != LightType.CAPSULE:
            cage.hide = True
            return

        cage.hide = False
        theme_ui = context.preferences.themes[0].user_interface
        cage.color = theme_ui.gizmo_primary
        cage.color_highlight = theme_ui.gizmo_hi

        cage.matrix_offset = self.apply_cage_clamping(cage.matrix_offset)

        # Determine in which direction the cage should be facing
        # The cage is a 2D plane, so as we rotate the camera around the capsule, at one point it will become a "line".
        # To avoid that, we have to rotate it 90° so it is facing the camera again.
        # We consider the two possible plane rotations (normal along X and normal along Y) and calculate which one is
        # facing the camera more.
        # Note: we only care about left/right and front/back views. If we would want the cage to be editable from
        # the top and bottom views (a plane with normal along Z) we would have to modify the handlers to take this into
        # account, as from that view only the radius would be editable.
        rv3d = context.space_data.region_3d
        view_dir = (active_light_obj.matrix_world.translation - rv3d.view_matrix.inverted().translation)
        view_dir.normalize()

        plane_mat = active_light_obj.matrix_world
        plane_dir1 = plane_mat.col[0]  # right
        plane_dir2 = plane_mat.col[1]  # forward

        dot1 = view_dir.dot(plane_dir1)
        dot2 = view_dir.dot(plane_dir2)

        half_pi = math.pi / 2
        if abs(dot1) > abs(dot2):
            cage.matrix_basis = plane_mat @ Matrix.Rotation(half_pi, 4, "Y")
        else:
            cage.matrix_basis = plane_mat @ Matrix.Rotation(half_pi, 4, "Z") @ Matrix.Rotation(half_pi, 4, "Y")

    def apply_cage_clamping(self, m: Matrix) -> Matrix:
        """Returns a new scale matrix clamped to avoid dimensions of size 0 on the capsule cage."""
        diameter = m.row[1].length
        length = m.row[0].length - diameter
        length = max(0.001, length)
        diameter = max(0.001, diameter)
        return Matrix(((length + diameter, 0.0, 0.0, 0.0),
                       (0.0, diameter, 0.0, 0.0),
                       (0.0, 0.0, 1.0, 0.0),
                       (0.0, 0.0, 0.0, 1.0)))

    def get_capsule_light_size_matrix(self, light_obj: Object) -> Matrix:
        light = light_obj.data
        length = light.light_properties.extent[0]
        radius = light.cutoff_distance  # falloff
        diameter = radius * 2.0
        m = Matrix(((length + diameter, 0.0, 0.0, 0.0),
                    (0.0, diameter, 0.0, 0.0),
                    (0.0, 0.0, 1.0, 0.0),
                    (0.0, 0.0, 0.0, 1.0)))
        return m

    def handler_get_cage_transform(self):
        light_obj = bpy.context.view_layer.objects.active
        if light_obj.type != "LIGHT" or light_obj.sollum_type != SollumType.LIGHT:
            m = Matrix.Identity(4)
        else:
            m = self.get_capsule_light_size_matrix(light_obj)

        return [v for row in m.transposed() for v in row]

    def handler_set_cage_transform(self, value):
        m = Matrix((value[0:4], value[4:8], value[8:12], value[12:16]))
        m.transpose()
        m = self.apply_cage_clamping(m)
        diameter = m.row[1].length
        radius = diameter * 0.5
        length = m.row[0].length - diameter
        bpy.ops.sollumz.capsule_light_set_size(True, length=length, radius=radius)
