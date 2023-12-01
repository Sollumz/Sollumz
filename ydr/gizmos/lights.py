import bpy
import functools
import math
from mathutils import Matrix
from ...sollumz_properties import SollumType, LightType


@functools.cache
def get_cylinder_shape() -> object:
    def _build_circle(cx: float, cy: float, cz: float, radius: float) -> list[tuple[float, float, float]]:
        verts = []
        NUM_SEGMENTS = 24
        step_delta_angle = 2 * math.pi / NUM_SEGMENTS
        angle = 0.0
        for _ in range(NUM_SEGMENTS):
            x = math.cos(angle) * radius
            z = math.sin(angle) * radius
            next_x = math.cos(angle + step_delta_angle) * radius
            next_z = math.sin(angle + step_delta_angle) * radius

            verts.append((cx + x, cy + z, cz))
            verts.append((cx + next_x, cy + next_z, cz))

            angle += step_delta_angle

        return verts

    all_verts = [
        # lines connecting top and bottom of the cylinder
        (0.5, 0.0, -0.5), (0.5, 0.0, 0.5),
        (-0.5, 0.0, -0.5), (-0.5, 0.0, 0.5),
        (0.0, 0.5, -0.5), (0.0, 0.5, 0.5),
        (0.0, -0.5, -0.5), (0.0, -0.5, 0.5),
    ]
    # cylinder caps
    all_verts.extend(_build_circle(0.0, 0.0, -0.5, 0.5))
    all_verts.extend(_build_circle(0.0, 0.0, 0.5, 0.5))
    return bpy.types.Gizmo.new_custom_shape("LINES", all_verts)


@functools.cache
def get_capsule_cap_shape() -> object:
    all_verts = []
    NUM_SEGMENTS = 12
    step_delta_angle = math.pi / NUM_SEGMENTS
    angle = 0.0
    radius = 0.5
    for _ in range(NUM_SEGMENTS):
        x = math.cos(angle) * radius
        z = math.sin(angle) * radius
        next_x = math.cos(angle + step_delta_angle) * radius
        next_z = math.sin(angle + step_delta_angle) * radius

        all_verts.append((x, 0.0, z))
        all_verts.append((next_x, 0.0, next_z))

        all_verts.append((0.0, x, z))
        all_verts.append((0.0, next_x, next_z))

        angle += step_delta_angle

    return bpy.types.Gizmo.new_custom_shape("LINES", all_verts)


class SOLLUMZ_OT_capsule_light_set_size(bpy.types.Operator):
    bl_idname = "sollumz.capsule_light_set_size"
    bl_label = "Capsule Light Scale"
    bl_description = bl_label
    bl_options = {"UNDO_GROUPED", "INTERNAL"}

    length: bpy.props.FloatProperty(name="Length")
    radius: bpy.props.FloatProperty(name="Radius")

    def execute(self, context):
        light_obj = context.view_layer.objects.active
        if light_obj.type != "LIGHT" or light_obj.sollum_type != SollumType.LIGHT:
            return {"CANCELLED"}

        light = light_obj.data
        light.light_properties.extent[0] = self.length
        light.cutoff_distance = self.radius
        return {"FINISHED"}


class SOLLUMZ_GT_capsule(bpy.types.Gizmo):
    bl_idname = "SOLLUMZ_GT_capsule"

    def __init__(self):
        super().__init__()
        self.length = 1.0
        self.radius = 1.0

    def draw(self, context):
        mat = self.matrix_world
        diameter = self.radius * 2.0
        cylinder_mat = (mat @
                        Matrix.Scale(diameter, 4, (1.0, 0.0, 0.0)) @
                        Matrix.Scale(diameter, 4, (0.0, 1.0, 0.0)) @
                        Matrix.Scale(self.length, 4, (0.0, 0.0, 1.0)))
        cap_mat = (mat @
                   Matrix.Translation((0.0, 0.0, -self.length * 0.5)) @
                   Matrix.Scale(diameter, 4) @
                   Matrix.Scale(-1.0, 4))
        cap2_mat = (mat @
                    Matrix.Translation((0.0, 0.0, self.length * 0.5)) @
                    Matrix.Scale(diameter, 4))

        self.draw_custom_shape(get_cylinder_shape(), matrix=cylinder_mat)
        self.draw_custom_shape(get_capsule_cap_shape(), matrix=cap_mat)
        self.draw_custom_shape(get_capsule_cap_shape(), matrix=cap2_mat)


class SOLLUMZ_GGT_capsule_light(bpy.types.GizmoGroup):
    bl_idname = "SOLLUMZ_GGT_capsule_light"
    bl_label = "Capsule Light Widget"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT", "DEPTH_3D", "SCALE", "SHOW_MODAL_ALL"}

    @classmethod
    def poll(cls, context):
        return context.space_data.show_object_viewport_light and len(bpy.data.lights) > 0

    def setup(self, context):
        cage = self.gizmos.new("GIZMO_GT_cage_2d")
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

        self.active_light_obj = None

    def refresh(self, context):
        pass

    def draw_prepare(self, context):
        theme = context.preferences.themes[0]
        color_default = theme.view_3d.light[0:3]
        color_selected = theme.view_3d.object_selected
        color_active = theme.view_3d.object_active

        active_obj = context.view_layer.objects.active
        self.active_light_obj = None
        gz_idx = 1  # gizmo at index 0 is the cage
        for light_obj in context.view_layer.objects:
            if light_obj.type != "LIGHT" or light_obj.sollum_type != SollumType.LIGHT:
                continue

            if not light_obj.visible_get():
                continue

            light = light_obj.data
            if light.sollum_type != LightType.CAPSULE:
                continue

            light_selected = light_obj.select_get()
            light_active = light_obj == active_obj
            length = light.light_properties.extent[0]
            radius = light.cutoff_distance  # falloff

            if light_active:
                self.active_light_obj = light_obj

            if gz_idx < len(self.gizmos):
                gz = self.gizmos[gz_idx]
            else:
                gz = self.gizmos.new(SOLLUMZ_GT_capsule.bl_idname)
                gz.alpha = 0.9

            gz.matrix_basis = light_obj.matrix_world.normalized()
            gz.length = length
            gz.radius = radius
            gz.color = (
                color_active if light_active and light_selected else
                color_selected if light_selected else
                color_default
            )

            gz_idx += 1

        # Remove unused gizmos
        for i in range(gz_idx, len(self.gizmos)):
            self.gizmos.remove(self.gizmos[-1])

        self.draw_prepare_cage(context)

    def draw_prepare_cage(self, context):
        cage = self.cage
        light_obj = self.active_light_obj
        if light_obj is None:
            cage.hide = True
            return

        cage.hide = False
        theme_ui = context.preferences.themes[0].user_interface
        cage.color = theme_ui.gizmo_primary
        cage.color_highlight = theme_ui.gizmo_hi

        cage.matrix_offset = self.apply_cage_clamping(cage.matrix_offset)

        rv3d = context.space_data.region_3d
        view_dir = (light_obj.matrix_world.translation - rv3d.view_matrix.inverted().translation)
        view_dir.normalize()
        view_rot = view_dir.to_track_quat("Y", "Z")

        mat1 = light_obj.matrix_world @ Matrix.Rotation(math.pi / 2, 4, "Y")
        mat2 = mat1 @ Matrix.Rotation(math.pi / 2, 4, "X")
        dot_product1 = view_rot.dot(mat1.to_quaternion())
        dot_product2 = view_rot.dot(mat2.to_quaternion())
        if dot_product1 < dot_product2:  # TODO: this "facing camera" check is not really correct
            cage.matrix_basis = mat1
        else:
            cage.matrix_basis = mat2

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

    def get_capsule_light_size_matrix(self, light_obj: bpy.types.Object) -> Matrix:
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
