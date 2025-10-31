"""Modal Operator to pick the index of a palette texture on an open Image Editor"""

from bpy.types import (
    Operator,
)


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
    bl_idname = "sollumz.pick_palette_color"
    bl_label = "Palette Color Picker"
    bl_description = "Pick a tint index from a Image Editor and set the vertex brush color channel"

    image_editors = []

    @classmethod
    def poll(cls, context):
        return len(get_all_image_editor_areas(context)) > 0

    def modal(self, context, event):
        if event.type == "MOUSEMOVE":
            for image_editor, tex_width in self.image_editors:
                if uv := is_in_texture(image_editor, (event.mouse_x, event.mouse_y)):
                    index = int(uv[0]*(tex_width))
                    context.window_manager.sz_ui_vertex_paint_pal_index = index
                    for area in context.screen.areas:
                        if area.type == 'VIEW_3D':
                            area.tag_redraw()
                    context.window.cursor_modal_set("EYEDROPPER")
                    return {"RUNNING_MODAL"}
            context.window.cursor_modal_set("STOP")
            return {"RUNNING_MODAL"}

        if event.type == "LEFTMOUSE":
            for image_editor, tex_width in self.image_editors:
                if uv := is_in_texture(image_editor, (event.mouse_x, event.mouse_y)):
                    index = int(uv[0]*(tex_width))
                    context.scene.tool_settings.unified_paint_settings.color.b = (index+0.5)/tex_width
                    self.report({"INFO"}, f"Picked index: {index}")
                    context.window.cursor_modal_restore()
                    return {"FINISHED"}
            return {"RUNNING_MODAL"}

        elif event.type in {"RIGHTMOUSE", "ESC"}:
            context.window.cursor_modal_restore()
            return {"CANCELLED"}

        return {"RUNNING_MODAL"}

    def invoke(self, context, event):
        context.window.cursor_modal_set("STOP")
        self.image_editors = get_all_image_editor_areas(context)
        context.window_manager.modal_handler_add(self)
        return {"RUNNING_MODAL"}
