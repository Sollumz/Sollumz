"""Modal Operator to pick the index of a palette texture on an open Image Editor"""

import bpy
from bl_ui.space_statusbar import STATUSBAR_HT_header
from bpy.types import (
    Operator,
    SpaceImageEditor,
)

from .utils import vertex_paint_unified_colors


def get_all_image_editor_areas(context):
    image_editors = []
    for window in context.window_manager.windows:
        for area in window.screen.areas:
            if area.type == "IMAGE_EDITOR":
                if image := area.spaces.active.image:
                    width = image.size[0]
                else:
                    width = 256
                image_editors.append((area, width))
    return image_editors


def is_in_texture(area, position):
    x, y = position
    for region in area.regions:
        if region.type != "WINDOW":
            continue

        rx = region.x
        ry = region.y
        rw = region.width
        rh = region.height
        if rx <= x <= rx + rw and ry <= y <= ry + rh:
            u, v = region.view2d.region_to_view(x - rx, y - ry)
            if 0 <= v <= 1 and 0 <= u <= 1:
                return (u, v)
            else:
                return None


class SOLLUMZ_OT_pick_palette_color(Operator):
    bl_idname = "sollumz.vertex_paint_pick_palette_color"
    bl_label = "Palette Color Picker"
    bl_description = "Pick a tint index from a Image Editor and set the vertex brush color channel"

    @classmethod
    def poll(cls, context):
        if not get_all_image_editor_areas(context):
            cls.poll_message_set("No Image Editor open")
            return False

        return True

    def modal(self, context, event):
        if event.type == "MOUSEMOVE":
            for image_editor, tex_width in self._image_editors:
                if uv := is_in_texture(image_editor, (event.mouse_x, event.mouse_y)):
                    index = int(uv[0] * (tex_width))
                    self._index = index
                    self._uv = uv
                    self._tex_width = tex_width
                    image_editor.tag_redraw()
                    context.window.cursor_modal_set("EYEDROPPER")
                    return {"RUNNING_MODAL"}

            if self._uv is not None:
                self._uv = None
                self._redraw_image_editors()
            context.window.cursor_modal_set("STOP")
            return {"RUNNING_MODAL"}

        elif event.type == "LEFTMOUSE":
            for image_editor, tex_width in self._image_editors:
                if uv := is_in_texture(image_editor, (event.mouse_x, event.mouse_y)):
                    index = int(uv[0] * (tex_width))
                    vertex_paint_unified_colors(context).color.b = (index + 0.5) / tex_width
                    self.report({"INFO"}, f"Picked index: {index}")
                    self._cleanup(context)
                    return {"FINISHED"}

            return {"RUNNING_MODAL"}

        elif event.type in {"RIGHTMOUSE", "ESC"}:
            self._cleanup(context)
            return {"CANCELLED"}

        # Allow camera navigation
        elif event.type in {"MIDDLEMOUSE", "WHEELUPMOUSE", "WHEELDOWNMOUSE"}:
            self._redraw_image_editors()
            return {"PASS_THROUGH"}

        return {"RUNNING_MODAL"}

    def invoke(self, context, event):
        self._image_editors = get_all_image_editor_areas(context)
        self._uv = None
        self._index = None
        self._tex_width = None
        self._draw_overlay_handle = SpaceImageEditor.draw_handler_add(self._draw_overlay, (), "WINDOW", "POST_PIXEL")

        context.window.cursor_modal_set("STOP")
        context.workspace.status_text_set(" ")
        STATUSBAR_HT_header.prepend(self._draw_status_bar)

        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}

    def _cleanup(self, context):
        context.window.cursor_modal_restore()
        context.workspace.status_text_set(None)
        STATUSBAR_HT_header.remove(self._draw_status_bar)

        if self._draw_overlay_handle is not None:
            SpaceImageEditor.draw_handler_remove(self._draw_overlay_handle, "WINDOW")
            self._draw_overlay_handle = None
            self._redraw_image_editors()

    def _redraw_image_editors(self):
        for image_editor, _ in self._image_editors:
            image_editor.tag_redraw()

    def _draw_status_bar(self, header, context):
        layout = header.layout.row(align=True)
        layout.label(text=" Cancel", icon="EVENT_ESC")
        layout.label(text="Pick", icon="MOUSE_LMB")

    def _draw_overlay(self):
        """Draw an overlay over the palette image to show the selected column."""
        if self._uv is None or self._index is None or self._tex_width is None:
            return

        import blf
        import gpu.shader
        import gpu_extras

        context = bpy.context
        region = context.region
        view = region.view2d

        theme = context.preferences.themes[0]
        selected_color = theme.user_interface.wcol_toggle.inner_sel

        u, v = self._uv
        x0, y0 = view.view_to_region(u, v, clip=False)

        index = self._index
        tex_width = self._tex_width
        u1 = index / tex_width
        u2 = (index + 1.0) / tex_width
        x1, y1 = view.view_to_region(u1, 0, clip=False)
        x2, y2 = view.view_to_region(u2, 1, clip=False)

        if bpy.app.version >= (4, 5, 0):
            shader = gpu.shader.from_builtin("POLYLINE_UNIFORM_COLOR")
            shader.uniform_float("lineWidth", 4)
        else:
            shader = gpu.shader.from_builtin("UNIFORM_COLOR")
            gpu.state.line_width_set(4)
        batch = gpu_extras.batch.batch_for_shader(
            shader,
            "LINES",
            {"pos": ((x1, y1), (x1, y2), (x2, y1), (x2, y2), (x1, y1), (x2, y1), (x1, y2), (x2, y2))},
        )
        shader.uniform_float("color", selected_color)
        batch.draw(shader)

        blf.position(0, x0 + 16, y0 + 32, 0)
        blf.size(0, 15.0)
        blf.color(0, 0.9, 0.9, 0.9, 1.0)
        blf.draw(0, f"Index: {index}")
