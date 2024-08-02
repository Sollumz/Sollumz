import bpy
from bpy.types import (
    SpaceView3D,
    Object,
)
import gpu
import gpu_extras
import blf
from mathutils import Vector
from collections.abc import Sequence
from typing import NamedTuple
from .cloth import (
    ClothAttr,
    is_cloth_mesh_object,
    mesh_get_cloth_attribute_values,
)
from bpy_extras.view3d_utils import location_3d_to_region_2d
from bpy_extras.mesh_utils import edge_loops_from_edges
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
        scene = context.scene
        if not scene.sz_ui_cloth_pinned_visualize:
            return False

        obj = context.active_object
        if not is_cloth_mesh_object(obj):
            return False

        return True

    def draw_text(self):
        pass
        # if not self.can_draw_anything():
        #     return

    def draw_geometry(self):
        if not self.can_draw_anything():
            return

        context = bpy.context
        scene = context.scene
        obj = context.active_object

        if scene.sz_ui_cloth_pinned_visualize:
            self.draw_pinned_geometry(obj)

    def draw_pinned_geometry(self, cloth_obj: Object):
        mesh = cloth_obj.data

        coords = []

        if cloth_obj.mode == "EDIT":
            edit_mesh = bmesh.from_edit_mesh(mesh)
            pinned_layer = edit_mesh.verts.layers.int.get(ClothAttr.PINNED, None)
            for v in edit_mesh.verts:
                is_pinned = ClothAttr.PINNED.default_value if pinned_layer is None else v[pinned_layer]
                if is_pinned:
                    coords.append(v.co + Vector((0.0, 0.0, 0.0)))
                    coords.append(v.co + Vector((1.0, 0.0, 0.0)))
        else:
            pinned_values = mesh_get_cloth_attribute_values(mesh, ClothAttr.PINNED)
            for v in mesh.vertices:
                is_pinned = pinned_values[v.index] != 0
                if is_pinned:
                    coords.append(v.co + Vector((0.0, 0.0, 0.0)))
                    coords.append(v.co + Vector((1.0, 0.0, 0.0)))

        shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        batch = gpu_extras.batch.batch_for_shader(shader, "LINES", {"pos": coords})
        shader.uniform_float("color", (1.0, 0.0, 1.0, 1.0))
        batch.draw(shader)

draw_handlers = []


def register():
    handler = ClothOverlaysDrawHandler()
    handler.register()
    draw_handlers.append(handler)


def unregister():
    for handler in draw_handlers:
        handler.unregister()
    draw_handlers.clear()
