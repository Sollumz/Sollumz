import bpy
from bpy.types import (
    SpaceView3D,
    Object,
)
import gpu
from gpu_extras import batch
import blf
from mathutils import Vector
from collections.abc import Sequence
from .cloth import (
    ClothAttr,
    is_cloth_mesh_object,
    mesh_get_cloth_attribute_values,
)
import bmesh


class ClothOverlaysDrawHandler:
    """Manages drawing the cloth overlays used to display the attributes at each vertex."""

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
            not wm.sz_ui_cloth_vertex_weight_visualize and
            not wm.sz_ui_cloth_inflation_scale_visualize and
            not wm.sz_ui_cloth_pinned_visualize
        ):
            return False

        obj = context.active_object
        if not is_cloth_mesh_object(obj):
            return False

        return True

    def draw_text(self):
        if not self.can_draw_anything():
            return

        context = bpy.context
        wm = context.window_manager
        obj = context.active_object

        attrs = []
        if wm.sz_ui_cloth_vertex_weight_visualize:
            attrs.append(ClothAttr.VERTEX_WEIGHT)
        if wm.sz_ui_cloth_inflation_scale_visualize:
            attrs.append(ClothAttr.INFLATION_SCALE)
        self.draw_attribute_values(obj, attrs)

    def draw_geometry(self):
        if not self.can_draw_anything():
            return

        context = bpy.context
        wm = context.window_manager
        obj = context.active_object

        if wm.sz_ui_cloth_pinned_visualize:
            self.draw_pinned_geometry(obj)

    def draw_attribute_values(self, cloth_obj: Object, attrs: Sequence[ClothAttr]):
        context = bpy.context
        region = context.region
        rv3d = context.region_data
        mesh = cloth_obj.data

        font_id = 0
        blf.size(font_id, 11)
        blf.color(font_id, 1.0, 1.0, 1.0, 1.0)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(font_id, 2, -2)

        matrix_world = cloth_obj.matrix_world

        def _draw_vertex_attributes(pos: Vector, attr_values):
            from bpy_extras.view3d_utils import location_3d_to_region_2d
            pos = matrix_world @ pos
            pos = location_3d_to_region_2d(region, rv3d, pos)
            if pos:
                for i, attr_value in enumerate(attr_values):
                    attr_type = attrs[i].type
                    if attr_type == "FLOAT_VECTOR":
                        attr_str = f"{attr_value[0]:.2g}  {attr_value[1]:.2g}"
                    elif attr_type == "INT":
                        attr_str = f"{attr_value}"
                    else:  # FLOAT
                        attr_str = f"{attr_value:.6g}"
                    w, h = blf.dimensions(font_id, attr_str)
                    attr_pos = pos - Vector((w * 0.5, h * i * 2 - (h * len(attr_values) / 2)))
                    blf.position(font_id, attr_pos.x, attr_pos.y, 0.0)
                    blf.draw(font_id, attr_str)

        if cloth_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            attr_layers = [(edit_mesh.verts.layers.float_vector if attr.type == "FLOAT_VECTOR" else edit_mesh.verts.layers.int if attr.type ==
                            "INT" else edit_mesh.verts.layers.float).get(attr, None) for attr in attrs]
            for v in edit_mesh.verts:
                attr_values = [attr.default_value if attr_layers[i] is None else v[attr_layers[i]]
                               for i, attr in enumerate(attrs)]
                _draw_vertex_attributes(v.co, attr_values)
        else:
            all_attr_values = [mesh_get_cloth_attribute_values(mesh, attr) for attr in attrs]
            for v in mesh.vertices:
                attr_values = [all_attr_values[i][v.index] for i, attr in enumerate(attrs)]
                _draw_vertex_attributes(v.co, attr_values)

        blf.disable(font_id, blf.SHADOW)

    def draw_pinned_geometry(self, cloth_obj: Object):
        transform = cloth_obj.matrix_world
        mesh = cloth_obj.data

        coords = []

        if cloth_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            pinned_layer = edit_mesh.verts.layers.int.get(ClothAttr.PINNED, None)
            for v in edit_mesh.verts:
                is_pinned = ClothAttr.PINNED.default_value if pinned_layer is None else v[pinned_layer]
                if is_pinned:
                    coords.append(transform @ v.co)
        else:
            pinned_values = mesh_get_cloth_attribute_values(mesh, ClothAttr.PINNED)
            for v in mesh.vertices:
                is_pinned = pinned_values[v.index] != 0
                if is_pinned:
                    coords.append(transform @ v.co)

        gpu.state.point_size_set(12.5)
        gpu.state.blend_set("ALPHA")
        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        pinned_verts_batch = batch.batch_for_shader(shader, "POINTS", {"pos": coords})
        shader.uniform_float("color", (1.0, 0.65, 0.0, 0.5))
        pinned_verts_batch.draw(shader)


draw_handlers = []


def register():
    handler = ClothOverlaysDrawHandler()
    handler.register()
    draw_handlers.append(handler)


def unregister():
    for handler in draw_handlers:
        handler.unregister()
    draw_handlers.clear()
