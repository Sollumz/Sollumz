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


class SOLLUMZ_GT_capsule(bpy.types.Gizmo):
    bl_idname = "SOLLUMZ_GT_capsule"

    def __init__(self):
        super().__init__()
        self.length = 1.0
        self.radius = 1.0

    def draw(self, context):
        mat = self.matrix_world
        cylinder_mat = (mat @
                        Matrix.Scale(self.radius, 4, (1.0, 0.0, 0.0)) @
                        Matrix.Scale(self.radius, 4, (0.0, 1.0, 0.0)) @
                        Matrix.Scale(self.length, 4, (0.0, 0.0, 1.0)))
        cap_mat = (mat @
                   Matrix.Translation((0.0, 0.0, -self.length * 0.5)) @
                   Matrix.Scale(self.radius, 4) @
                   Matrix.Scale(-1.0, 4))
        cap2_mat = (mat @
                    Matrix.Translation((0.0, 0.0, self.length * 0.5)) @
                    Matrix.Scale(self.radius, 4))

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
        pass

    def refresh(self, context):
        pass

    def draw_prepare(self, context):
        theme = context.preferences.themes[0]
        color_default = theme.view_3d.light[0:3]
        # color_selected = theme.view_3d.object_selected
        color_active = theme.view_3d.object_active

        gz_idx = 0
        for light_obj in bpy.data.objects:
            if light_obj.type != "LIGHT" or light_obj.sollum_type != SollumType.LIGHT:
                continue

            if not light_obj.visible_get():
                continue

            light = light_obj.data
            if light.sollum_type != LightType.CAPSULE:
                continue

            length = light.light_properties.extent[0]
            radius = light.cutoff_distance  # falloff

            if gz_idx < len(self.gizmos):
                gz = self.gizmos[gz_idx]
            else:
                gz = self.gizmos.new(SOLLUMZ_GT_capsule.bl_idname)

            gz.matrix_basis = light_obj.matrix_world.normalized()
            gz.length = length
            gz.radius = radius
            gz.color = color_active if light_obj.select_get() else color_default
            gz.alpha = 0.9

            gz_idx += 1

        # Remove unused gizmos
        for i in range(gz_idx, len(self.gizmos)):
            self.gizmos.remove(self.gizmos[-1])
