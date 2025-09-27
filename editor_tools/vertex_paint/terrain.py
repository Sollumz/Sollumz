"""Operators to help with terrain vertex color painting."""

import bpy
from bpy.props import IntProperty
from bpy.types import Operator


def apply_terrain_brush_settings(brush, idx: int, paint_alpha: float | None = None):
    if idx < 5:
        brush.blend = "MIX"
    if idx == 1:
        brush.color = (0, 0, 0)
        brush.strength = 1
    elif idx == 2:
        brush.color = (0, 0, 1)
        brush.strength = 1
    elif idx == 3:
        brush.color = (0, 1, 0)
        brush.strength = 1
    elif idx == 4:
        brush.color = (0, 1, 1)
        brush.strength = 1
    elif idx == 5:
        assert paint_alpha is not None, "paint_alpha required"
        if paint_alpha > 0:
            brush.color = (1, 1, 1)
            brush.blend = "ADD_ALPHA"
            brush.strength = paint_alpha
        else:
            brush.color = (0, 0, 0)
            brush.blend = "ERASE_ALPHA"
            brush.strength = paint_alpha * -1


def apply_terrain_brush_setting_to_current_brush(idx: int, paint_alpha: float | None = None):
    brush = bpy.context.scene.tool_settings.vertex_paint.brush
    apply_terrain_brush_settings(brush, idx, paint_alpha)


class SOLLUMZ_OT_vertex_paint_terrain_texture(Operator):
    bl_idname = "sollumz.vertex_paint_terrain_texture"
    bl_label = "Paint Terrain Texture"
    bl_description = "Apply brush color settings to paint a terrain texture layer"

    texture: IntProperty(name="Texture", min=1, max=4)

    @classmethod
    def poll(cls, context) -> bool:
        obj = context.active_object
        return obj and obj.mode == "VERTEX_PAINT"

    def execute(self, context):
        apply_terrain_brush_setting_to_current_brush(self.texture)
        return {"FINISHED"}


class SOLLUMZ_OT_vertex_paint_terrain_alpha(Operator):
    bl_idname = "sollumz.vertex_paint_terrain_alpha"
    bl_label = "Paint Terrain Alpha"
    bl_description = "Apply brush setting to paint a terrain lookup sampler alpha"

    alpha: bpy.props.FloatProperty(name="Alpha", min=-1.0, max=1.0)

    @classmethod
    def poll(cls, context) -> bool:
        obj = context.active_object
        return obj and obj.mode == "VERTEX_PAINT"

    def execute(self, context):
        apply_terrain_brush_setting_to_current_brush(5, self.alpha)
        return {"FINISHED"}
