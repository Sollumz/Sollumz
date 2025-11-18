import bpy
from bpy.types import (
    Gizmo,
    GizmoGroup,
    Operator,
)
import gpu
import functools
import math
from mathutils import Matrix, Vector
from ...sollumz_properties import SollumType, LightType
from .light_manipulators import CapsuleLightManipulator, CullingPlaneLightManipulator


class SOLLUMZ_OT_object_select(Operator):
    bl_idname = "sollumz.object_select"
    bl_label = "Select"
    bl_description = bl_label
    bl_options = {"UNDO", "INTERNAL"}

    object_name: bpy.props.StringProperty()
    extend: bpy.props.BoolProperty(default=False)

    def execute(self, context):
        obj = context.scene.objects.get(self.object_name)
        if obj is None:
            return {"CANCELLED"}

        if not self.extend:
            bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        context.view_layer.objects.active = obj
        return {"FINISHED"}

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)


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
    return Gizmo.new_custom_shape("LINES", all_verts)


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

    return Gizmo.new_custom_shape("LINES", all_verts)


class SOLLUMZ_GT_capsule(Gizmo):
    bl_idname = "SOLLUMZ_GT_capsule"

    length: bpy.props.FloatProperty(default=1.0)
    radius: bpy.props.FloatProperty(default=1.0)

    def draw(self, context):
        self.draw_common(context, None)

    def draw_select(self, context, select_id):
        self.draw_common(context, select_id)

    def draw_common(self, context, select_id):
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

        self.draw_custom_shape(get_cylinder_shape(), matrix=cylinder_mat, select_id=select_id)
        self.draw_custom_shape(get_capsule_cap_shape(), matrix=cap_mat, select_id=select_id)
        self.draw_custom_shape(get_capsule_cap_shape(), matrix=cap2_mat, select_id=select_id)


@functools.cache
def get_culling_plane_shader() -> tuple[gpu.types.GPUShader, gpu.types.GPUBatch]:

    vert_out = gpu.types.GPUStageInterfaceInfo("gizmo_culling_plane_shader_interface")
    vert_out.smooth("VEC3", "pos")

    shader_info = gpu.types.GPUShaderCreateInfo()
    # shader_info.define("DEBUG_RENDER", "1")
    shader_info.push_constant("MAT4", "ModelViewProjectionMatrix")
    shader_info.push_constant("VEC3", "Color")
    shader_info.push_constant("FLOAT", "Scale")
    shader_info.vertex_in(0, "VEC3", "position")
    shader_info.vertex_out(vert_out)
    shader_info.fragment_out(0, "VEC4", "FragColor")

    shader_info.vertex_source("""
        void main()
        {
            pos = position * Scale;
            gl_Position = ModelViewProjectionMatrix * vec4(position, 1.0f);
        }
    """)

    shader_info.fragment_source("""
        void main()
        {
            float test = 0.0;
            test += step(0.9925, (1.0 + cos((pos.x + pos.y) * 20.0)) * 0.5);
            test += step(0.9925, (1.0 + cos((pos.x - pos.y) * 20.0)) * 0.5);
            test *= float(dot(pos, pos) / (Scale * Scale) < (0.5 * 0.5));
            test += float(pos.z > 0.0);
            vec3 col = Color;
            if (test == 0.0) {
        #if DEBUG_RENDER
                col = vec3(1.0, 0.5, 0.5);
        #else
                discard;
        #endif
            }

            FragColor = vec4(col, 1.0);
        }
    """)

    shader = gpu.shader.create_from_info(shader_info)
    del vert_out
    del shader_info

    coords = (
        (-0.5, 0.5, 0.0),
        (0.5, 0.5, 0.0),
        (-0.5, -0.5, 0.0),
        (0.5, -0.5, 0.0),

        (0.05, 0.5, 0.015),
        (-0.05, 0.5, 0.015),
        (0.0, 0.5, 0.05),

        (0.05, -0.5, 0.015),
        (-0.05, -0.5, 0.015),
        (0.0, -0.5, 0.05),

        (0.5, 0.05, 0.015),
        (0.5, -0.05, 0.015),
        (0.5, 0.0, 0.05),

        (-0.5, 0.05, 0.015),
        (-0.5, -0.05, 0.015),
        (-0.5, 0.0, 0.05),
    )
    indices = (
        # base quad
        (0, 1, 2),
        (2, 1, 3),

        # arrows indicating side with light
        (4, 5, 6),
        (7, 8, 9),
        (10, 11, 12),
        (13, 14, 15),
    )
    from gpu_extras.batch import batch_for_shader
    batch = batch_for_shader(shader, "TRIS", {"position": coords}, indices=indices)

    return shader, batch


class SOLLUMZ_GT_culling_plane(Gizmo):
    bl_idname = "SOLLUMZ_GT_culling_plane"

    extend: bpy.props.BoolProperty(default=False)

    def draw(self, context):
        self.draw_common(context, None)

    def draw_select(self, context, select_id):
        self.draw_common(context, select_id)

    def draw_common(self, context, select_id):
        if select_id is not None:
            gpu.select.load_id(select_id)
        mat = self.matrix_world
        scale = 2.5 if self.extend else 1.5
        color = self.color_highlight if self.is_highlight else self.color
        shader, batch = get_culling_plane_shader()
        with gpu.matrix.push_pop():
            gpu.matrix.multiply_matrix(mat)
            gpu.matrix.scale_uniform(scale)

            mvp_mat = gpu.matrix.get_projection_matrix() @ gpu.matrix.get_model_view_matrix()
            shader.uniform_float("ModelViewProjectionMatrix", mvp_mat)
            shader.uniform_float("Color", color)
            shader.uniform_float("Scale", scale)
            batch.draw(shader)


class SOLLUMZ_GGT_lights(GizmoGroup):
    bl_idname = "SOLLUMZ_GGT_lights"
    bl_label = "Light Widgets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT", "DEPTH_3D", "SCALE", "SHOW_MODAL_ALL"}

    @classmethod
    def poll(cls, context):
        return (
            context.space_data.show_object_viewport_light and
            context.space_data.overlay.show_extras and
            len(bpy.data.lights) > 0
        )

    def setup(self, context):
        self.capsule_manipulator = CapsuleLightManipulator(self)
        self.culling_plane_manipulator = CullingPlaneLightManipulator(self)

        self.active_light_obj = None

        self.capsule_gizmos = []
        self.culling_plane_gizmos = []

    def refresh(self, context):
        pass

    def draw_prepare(self, context):
        theme = context.preferences.themes[0]
        color_default = theme.view_3d.light[0:3]
        color_selected = theme.view_3d.object_selected
        color_active = theme.view_3d.object_active

        active_obj = context.view_layer.objects.active
        self.active_light_obj = None
        capsule_gz_idx = 0
        culling_plane_gz_idx = 0
        for light_obj in context.view_layer.objects:
            if light_obj.type != "LIGHT" or light_obj.sollum_type != SollumType.LIGHT:
                continue

            if not light_obj.visible_get():
                continue

            light = light_obj.data
            light_selected = light_obj.select_get()
            light_active = light_obj == active_obj
            if light_active:
                self.active_light_obj = light_obj

            gz_color = (
                color_active if light_active and light_selected else
                color_selected if light_selected else
                color_default
            )

            if light.sollum_type == LightType.CAPSULE:
                length = light.light_properties.extent[0]
                radius = light.cutoff_distance  # falloff

                if capsule_gz_idx < len(self.capsule_gizmos):
                    gz = self.capsule_gizmos[capsule_gz_idx]
                else:
                    gz = self.gizmos.new(SOLLUMZ_GT_capsule.bl_idname)
                    self.capsule_gizmos.append(gz)
                    gz.alpha = 0.9

                gz.use_event_handle_all = False
                gz.matrix_basis = light_obj.matrix_world.normalized()
                gz.length = length
                gz.radius = radius
                gz.color = gz_color
                gz.color_highlight = gz_color
                gz.alpha_highlight = gz.alpha
                op = gz.target_set_operator(SOLLUMZ_OT_object_select.bl_idname)
                op.object_name = light_obj.name

                capsule_gz_idx += 1

            if light.light_flags.enable_culling_plane:
                if culling_plane_gz_idx < len(self.culling_plane_gizmos):
                    gz = self.culling_plane_gizmos[culling_plane_gz_idx]
                else:
                    gz = self.gizmos.new(SOLLUMZ_GT_culling_plane.bl_idname)
                    self.culling_plane_gizmos.append(gz)
                    gz.alpha = 0.9

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

                gz.use_event_handle_all = False
                gz.matrix_basis = plane_mat
                gz.extend = light_active and light_selected
                gz.color = gz_color
                gz.color_highlight = gz_color
                gz.alpha_highlight = gz.alpha
                op = gz.target_set_operator(SOLLUMZ_OT_object_select.bl_idname)
                op.object_name = light_obj.name

                culling_plane_gz_idx += 1

        # Remove unused gizmos
        for i in range(capsule_gz_idx, len(self.capsule_gizmos)):
            self.gizmos.remove(self.capsule_gizmos[i])
        del self.capsule_gizmos[capsule_gz_idx:]

        for i in range(culling_plane_gz_idx, len(self.culling_plane_gizmos)):
            self.gizmos.remove(self.culling_plane_gizmos[i])
        del self.culling_plane_gizmos[culling_plane_gz_idx:]

        self.capsule_manipulator.draw_prepare(context, self.active_light_obj)
        self.culling_plane_manipulator.draw_prepare(context, self.active_light_obj)
