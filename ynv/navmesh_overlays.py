import bpy
from bpy.types import (
    SpaceView3D,
)
import gpu
import gpu_extras
import gpu_extras.batch
from mathutils import Vector
from .navmesh import (
    navmesh_is_valid,
    navmesh_get_grid_cell,
    navmesh_grid_get_cell_bounds,
)


class NavMeshOverlaysDrawHandler:
    """Manages drawing the navmesh overlays used to display the map grid bounds."""

    def __init__(self):
        self.handler_text = None
        self.handler_geometry = None

    def register(self):
        self.handler_geometry = SpaceView3D.draw_handler_add(self.draw_geometry, (), "WINDOW", "POST_VIEW")

    def unregister(self):
        SpaceView3D.draw_handler_remove(self.handler_geometry, "WINDOW")

    def can_draw_anything(self) -> bool:
        context = bpy.context
        wm = context.window_manager
        if not wm.sz_ui_nav_view_bounds:
            return False

        return True

    def draw_geometry(self):
        if not self.can_draw_anything():
            return

        context = bpy.context
        wm = context.window_manager

        if wm.sz_ui_nav_view_bounds:
            self.draw_grid_bounds()

    def draw_grid_bounds(self):
        context = bpy.context

        color_colums = (0.9, 0.45, 0.0, 0.8)
        color_walls = (0.8, 0.4, 0.0, 0.25)
        color_walls_end = (0.9, 0.45, 0.0, 0.0)

        columns_coords = []
        walls_coords = []
        walls_colors = []

        for navmesh_obj in context.scene.objects:
            if not navmesh_is_valid(navmesh_obj):
                continue

            if not navmesh_obj.visible_get():
                continue

            x, y = navmesh_get_grid_cell(navmesh_obj)
            if x < 0 or y < 0:
                continue

            cell_min, cell_max = navmesh_grid_get_cell_bounds(x, y)
            v0 = cell_min
            v1 = Vector((cell_min.x, cell_max.y, 0.0))
            v2 = cell_max
            v3 = Vector((cell_max.x, cell_min.y, 0.0))
            delta = Vector((0.0, 0.0, 250.0))
            # Render a line on each corner of the cell
            for v in (v0, v1, v2, v3):
                columns_coords.append(v + delta)
                columns_coords.append(v - delta)

            # Render a plane on each side of the cell
            # Each plane split in two halves to render them with a fade effect, starting from the center with some
            # alpha and ending at the top and bottom with 0 alpha
            for vi, vj in ((v0, v1), (v1, v2), (v2, v3), (v3, v0)):
                # top half
                walls_coords.append(vi)
                walls_coords.append(vj + delta)
                walls_coords.append(vi + delta)
                walls_colors.append(color_walls)
                walls_colors.append(color_walls_end)
                walls_colors.append(color_walls_end)

                walls_coords.append(vj + delta)
                walls_coords.append(vi)
                walls_coords.append(vj)
                walls_colors.append(color_walls_end)
                walls_colors.append(color_walls)
                walls_colors.append(color_walls)

                # bottom half
                walls_coords.append(vi - delta)
                walls_coords.append(vj)
                walls_coords.append(vi)
                walls_colors.append(color_walls_end)
                walls_colors.append(color_walls)
                walls_colors.append(color_walls)

                walls_coords.append(vj)
                walls_coords.append(vi - delta)
                walls_coords.append(vj - delta)
                walls_colors.append(color_walls)
                walls_colors.append(color_walls_end)
                walls_colors.append(color_walls_end)

        old_blend = gpu.state.blend_get()
        gpu.state.blend_set("ALPHA")
        gpu.state.depth_test_set("LESS_EQUAL")
        gpu.state.depth_mask_set(True)

        colums_shader = gpu.shader.from_builtin("UNIFORM_COLOR")
        walls_shader = gpu.shader.from_builtin("SMOOTH_COLOR")

        colums_shader.uniform_float("color", color_colums)
        columns_batch = gpu_extras.batch.batch_for_shader(colums_shader, "LINES", {"pos": columns_coords})
        walls_batch = gpu_extras.batch.batch_for_shader(
            walls_shader, "TRIS", {"pos": walls_coords, "color": walls_colors})

        columns_batch.draw(colums_shader)
        walls_batch.draw(walls_shader)

        gpu.state.depth_mask_set(False)
        gpu.state.blend_set(old_blend)


draw_handlers = []


def register():
    handler = NavMeshOverlaysDrawHandler()
    handler.register()
    draw_handlers.append(handler)


def unregister():
    for handler in draw_handlers:
        handler.unregister()
    draw_handlers.clear()
