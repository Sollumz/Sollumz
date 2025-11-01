from enum import Enum

import bpy
from bpy.types import (
    Brush,
    UnifiedPaintSettings,
)

from ...icons import icon

CHANNEL_LABELS = ("Red", "Green", "Blue", "Alpha")
CHANNEL_ICONS = ("RGBA_RED", "RGBA_GREEN", "RGBA_BLUE", "RGBA_ALPHA")


class Channel(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2
    ALPHA = 3

    @property
    def label(self) -> str:
        return CHANNEL_LABELS[self.value]

    @property
    def icon(self) -> int:
        return icon(CHANNEL_ICONS[self.value])


def ChannelEnumItems(self, context):
    # Using a function because the icons are only available after register() is executed
    try:
        return ChannelEnumItems._backing
    except AttributeError:
        ChannelEnumItems._backing = tuple((ch.name, ch.label, "", ch.icon, ch.value) for ch in Channel)
        return ChannelEnumItems._backing


def ChannelWithNoneEnumItems(self, context):
    try:
        return ChannelWithNoneEnumItems._backing
    except AttributeError:
        ChannelWithNoneEnumItems._backing = tuple((ch.name, ch.label, "", ch.icon, ch.value) for ch in Channel) + (
            ("NONE", "None", "", "CANCEL", -1),
        )
        return ChannelWithNoneEnumItems._backing


def attr_domain_size(mesh, attr) -> int:
    match attr.domain:
        case "POINT":
            return len(mesh.vertices)
        case "CORNER":
            return len(mesh.loops)
        case _:
            raise AssertionError(f"Unsupported domain '{attr.domain}'")

def vertex_paint_unified_settings(context) -> UnifiedPaintSettings:
    ts = context.tool_settings
    if bpy.app.version >= (5, 0, 0):
        ups = ts.vertex_paint.unified_paint_settings
    else:
        ups = ts.unified_paint_settings
    return ups


def vertex_paint_unified_colors(
    context, brush_override: Brush | None = None
) -> Brush | UnifiedPaintSettings:
    """Returns the correct paint settings according to whether unified color is enabled. Can access `.color` or
    `.secondary_color` on the returned object.
    """
    ts = context.tool_settings
    brush = brush_override or ts.vertex_paint.brush
    ups = vertex_paint_unified_settings(context)
    props = ups if ups.use_unified_color else brush
    return props


def vertex_paint_unified_strength(
    context, brush_override: Brush | None = None
) -> Brush | UnifiedPaintSettings:
    """Returns the correct paint settings according to whether unified strength is enabled. Can access `.strength`."""
    ts = context.tool_settings
    brush = brush_override or ts.vertex_paint.brush
    ups = vertex_paint_unified_settings(context)
    props = ups if ups.use_unified_strength else brush
    return props
