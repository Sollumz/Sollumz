import pytest
import bpy
from numpy.testing import assert_allclose


@pytest.mark.parametrize("op, expected_color", (
    ("paint_tex1", (0.0, 0.0, 0.0)),
    ("paint_tex2", (0.0, 0.0, 1.0)),
    ("paint_tex3", (0.0, 1.0, 0.0)),
    ("paint_tex4", (0.0, 1.0, 1.0)),
))
def test_ops_terrain_paint_texture(op, expected_color, context, plane_object):
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    op = getattr(bpy.ops.sollumz, op)
    op()

    brush = context.tool_settings.vertex_paint.brush
    assert_allclose(brush.color, expected_color)
    assert brush.blend == "MIX"
    assert brush.strength == 1.0

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("alpha", (1.0, 0.5))
def test_ops_terrain_paint_alpha_add(alpha, context, plane_object):
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")
    bpy.ops.sollumz.paint_a(alpha=alpha)

    brush = context.tool_settings.vertex_paint.brush
    assert_allclose(brush.color, (1.0, 1.0, 1.0))
    assert brush.blend == "ADD_ALPHA"
    assert brush.strength == alpha

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("alpha", (1.0, 0.5))
def test_ops_terrain_paint_alpha_remove(alpha, context, plane_object):
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")
    bpy.ops.sollumz.paint_a(alpha=-alpha)

    brush = context.tool_settings.vertex_paint.brush
    assert_allclose(brush.color, (0.0, 0.0, 0.0))
    assert brush.blend == "ERASE_ALPHA"
    assert brush.strength == alpha

    bpy.ops.object.mode_set(mode="OBJECT")
