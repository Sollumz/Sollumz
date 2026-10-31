"""Operators to help with terrain vertex color painting."""

import bpy
from bpy.props import IntProperty
from bpy.types import Context, Operator

from ... import logger
from ...tools.meshhelper import get_color_attr_name
from .isolate import (
    isolate_exit,
    isolate_get_state,
)
from .utils import (
    vertex_paint_unified_colors,
    vertex_paint_unified_strength,
)

TERRAIN_LOOKUP_BLEND_COLOR_ATTR_INDEX = 0  # Alpha blends with the lookup sampler
TERRAIN_TEXTURE_BLEND_COLOR_ATTR_INDEX = 1  # Selects the texture layers


def apply_terrain_color_attribute(context: Context, attr_index: int):
    mesh = context.active_object.data
    attr_name = get_color_attr_name(attr_index)
    if attr_name not in mesh.color_attributes:
        logger.warning(f"Mesh has no '{attr_name}' color attribute, active attribute not changed.")
        return

    if isolate_get_state(context).base_attr_name == attr_name:
        # Already there, or isolating some of its channels which the user can keep painting on
        return

    isolate_exit(context)
    mesh.attributes.active_color_name = attr_name
    mesh.update_tag()


def apply_terrain_brush_settings(brush, idx: int, paint_alpha: float | None = None):
    context = bpy.context
    colors = vertex_paint_unified_colors(context, brush)
    strength = vertex_paint_unified_strength(context, brush)
    if idx < 5:
        brush.blend = "MIX"
    if idx == 1:
        colors.color = (0, 0, 0)
        strength.strength = 1
    elif idx == 2:
        colors.color = (0, 0, 1)
        strength.strength = 1
    elif idx == 3:
        colors.color = (0, 1, 0)
        strength.strength = 1
    elif idx == 4:
        colors.color = (0, 1, 1)
        strength.strength = 1
    elif idx == 5:
        assert paint_alpha is not None, "paint_alpha required"
        if paint_alpha > 0:
            colors.color = (1, 1, 1)
            brush.blend = "ADD_ALPHA"
            strength.strength = paint_alpha
        else:
            colors.color = (0, 0, 0)
            brush.blend = "ERASE_ALPHA"
            strength.strength = paint_alpha * -1


def apply_terrain_brush_setting_to_current_brush(idx: int, paint_alpha: float | None = None):
    brush = bpy.context.scene.tool_settings.vertex_paint.brush
    apply_terrain_brush_settings(brush, idx, paint_alpha)


class SOLLUMZ_OT_vertex_paint_terrain_texture(Operator):
    bl_idname = "sollumz.vertex_paint_terrain_texture"
    bl_label = "Paint Terrain Texture"
    bl_description = (
        "Apply brush color settings to paint a terrain texture layer and switch to the "
        f"'{get_color_attr_name(TERRAIN_TEXTURE_BLEND_COLOR_ATTR_INDEX)}' color attribute"
    )
    bl_options = {"UNDO"}

    texture: IntProperty(name="Texture", min=1, max=4)

    @classmethod
    def poll(cls, context) -> bool:
        obj = context.active_object
        return obj and obj.mode == "VERTEX_PAINT"

    def execute(self, context):
        with logger.use_operator_logger(self):
            apply_terrain_brush_setting_to_current_brush(self.texture)
            apply_terrain_color_attribute(context, TERRAIN_TEXTURE_BLEND_COLOR_ATTR_INDEX)
        return {"FINISHED"}


class SOLLUMZ_OT_vertex_paint_terrain_alpha(Operator):
    bl_idname = "sollumz.vertex_paint_terrain_alpha"
    bl_label = "Paint Terrain Alpha"
    bl_description = (
        "Apply brush settings to paint a terrain lookup sampler alpha and switch to the "
        f"'{get_color_attr_name(TERRAIN_LOOKUP_BLEND_COLOR_ATTR_INDEX)}' color attribute"
    )
    bl_options = {"UNDO"}

    alpha: bpy.props.FloatProperty(name="Alpha", min=-1.0, max=1.0)

    @classmethod
    def poll(cls, context) -> bool:
        obj = context.active_object
        return obj and obj.mode == "VERTEX_PAINT"

    def execute(self, context):
        with logger.use_operator_logger(self):
            apply_terrain_brush_setting_to_current_brush(5, self.alpha)
            apply_terrain_color_attribute(context, TERRAIN_LOOKUP_BLEND_COLOR_ATTR_INDEX)
        return {"FINISHED"}
