import math
import time

import bpy
import gpu
from bpy.types import SpaceView3D
from gpu_extras.batch import batch_for_shader

if bpy.app.version >= (4, 5, 0):
    _POINT_SHADER_NAME = "POINT_UNIFORM_COLOR"
else:
    _POINT_SHADER_NAME = "UNIFORM_COLOR"

_HIGHLIGHT_COLOR = (1.0, 0.9, 0.4, 1.0)
_HIGHLIGHT_MARKER_SIZE = 12.0

_handler: "MapDataHighlightOverlay | None" = None


class MapDataHighlightOverlay:
    """Standalone overlay that temporarily flashes a set of 3D positions."""

    def __init__(self):
        self._draw_handler = None
        self._batch = None
        self._flash_end_time: float = 0.0
        self._flash_duration: float = 3.0

    def register(self):
        self._draw_handler = SpaceView3D.draw_handler_add(self._draw, (), "WINDOW", "POST_VIEW")

    def unregister(self):
        if self._draw_handler is not None:
            SpaceView3D.draw_handler_remove(self._draw_handler, "WINDOW")
        if bpy.app.timers.is_registered(self._timer_tick):
            bpy.app.timers.unregister(self._timer_tick)

    def start_flash(self, positions: list[tuple[float, float, float]], duration: float = 3.0):
        """Begin flashing markers at the given positions for *duration* seconds."""
        shader = gpu.shader.from_builtin(_POINT_SHADER_NAME)
        self._batch = batch_for_shader(shader, "POINTS", {"pos": positions})
        self._flash_duration = duration
        self._flash_end_time = time.monotonic() + duration
        if not bpy.app.timers.is_registered(self._timer_tick):
            bpy.app.timers.register(self._timer_tick, first_interval=0.016)

    def _draw(self):
        if self._batch is None or time.monotonic() >= self._flash_end_time:
            return

        remaining = self._flash_end_time - time.monotonic()
        progress = max(0.0, min(1.0, remaining / self._flash_duration))
        pulse = 0.5 * (1.0 + math.sin(time.monotonic() * 8.0))
        alpha_fade = min(1.0, progress * 3.0)

        size = _HIGHLIGHT_MARKER_SIZE * (1.0 + 0.5 * pulse)
        color = (*_HIGHLIGHT_COLOR[:3], _HIGHLIGHT_COLOR[3] * alpha_fade)

        gpu.state.blend_set("ALPHA")
        shader = gpu.shader.from_builtin(_POINT_SHADER_NAME)
        gpu.state.point_size_set(size)
        shader.uniform_float("color", color)
        self._batch.draw(shader)
        gpu.state.blend_set("NONE")

    def _timer_tick(self):
        if time.monotonic() >= self._flash_end_time:
            self._batch = None
            _tag_redraw_3d()
            return None
        _tag_redraw_3d()
        return 0.016


def _tag_redraw_3d():
    for window in bpy.context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "VIEW_3D":
                area.tag_redraw()


def register():
    global _handler
    _handler = MapDataHighlightOverlay()
    _handler.register()


def unregister():
    global _handler
    if _handler is not None:
        _handler.unregister()
        _handler = None
