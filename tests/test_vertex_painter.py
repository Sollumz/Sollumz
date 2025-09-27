import pytest
import bpy
from numpy.testing import assert_allclose


@pytest.mark.parametrize(
    "texture_index, expected_color",
    (
        (1, (0.0, 0.0, 0.0)),
        (2, (0.0, 0.0, 1.0)),
        (3, (0.0, 1.0, 0.0)),
        (4, (0.0, 1.0, 1.0)),
    ),
)
def test_ops_terrain_paint_texture(texture_index, expected_color, context, plane_object):
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_terrain_texture(texture=texture_index)

    brush = context.tool_settings.vertex_paint.brush
    assert_allclose(brush.color, expected_color)
    assert brush.blend == "MIX"
    assert brush.strength == 1.0

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("alpha", (1.0, 0.5))
def test_ops_terrain_paint_alpha_add(alpha, context, plane_object):
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")
    bpy.ops.sollumz.vertex_paint_terrain_alpha(alpha=alpha)

    brush = context.tool_settings.vertex_paint.brush
    assert_allclose(brush.color, (1.0, 1.0, 1.0))
    assert brush.blend == "ADD_ALPHA"
    assert brush.strength == alpha

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("alpha", (1.0, 0.5))
def test_ops_terrain_paint_alpha_remove(alpha, context, plane_object):
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")
    bpy.ops.sollumz.vertex_paint_terrain_alpha(alpha=-alpha)

    brush = context.tool_settings.vertex_paint.brush
    assert_allclose(brush.color, (0.0, 0.0, 0.0))
    assert brush.blend == "ERASE_ALPHA"
    assert brush.strength == alpha

    bpy.ops.object.mode_set(mode="OBJECT")


COLOR_ATOL = 0.0025


@pytest.mark.parametrize("channel", (0, 1, 2))
@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
def test_ops_vertex_paint_isolate_channel_rgb(channel, data_type, domain, context, plane_object):
    # Prepare test data
    orig_color0 = 0.9, 0.7, 0.5, 0.3
    orig_color1 = 0.8, 0.6, 0.4, 0.2

    expected_isolated_color0 = [0.0, 0.0, 0.0, 0.0]
    expected_isolated_color0[channel] = orig_color0[channel]
    expected_isolated_color1 = [0.0, 0.0, 0.0, 0.0]
    expected_isolated_color1[channel] = orig_color1[channel]

    new_color0 = [0.0, 0.0, 0.0, 0.0]
    new_color0[channel] = 0.1
    new_color1 = [0.0, 0.0, 0.0, 0.0]
    new_color1[channel] = 0.2

    expected_merged_color0 = list(orig_color0)
    expected_merged_color0[channel] = 0.1
    expected_merged_color1 = list(orig_color1)
    expected_merged_color1[channel] = 0.2

    # Actual test
    m = plane_object.data
    m.attributes.new("MyColor", data_type, domain)
    m.attributes.active_color_name = "MyColor"

    m.attributes.active_color.data[0].color_srgb = orig_color0
    m.attributes.active_color.data[1].color_srgb = orig_color1

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=channel)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, expected_isolated_color0, atol=COLOR_ATOL)
    assert_allclose(m.attributes.active_color.data[1].color_srgb, expected_isolated_color1, atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = new_color0
    m.attributes.active_color.data[1].color_srgb = new_color1

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=channel)
    assert m.attributes.active_color_name == "MyColor"
    assert len(m.color_attributes) == 1
    assert_allclose(m.attributes.active_color.data[0].color_srgb, expected_merged_color0, atol=COLOR_ATOL)
    assert_allclose(m.attributes.active_color.data[1].color_srgb, expected_merged_color1, atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
def test_ops_vertex_paint_isolate_channel_alpha(data_type, domain, context, plane_object):
    # Prepare test data
    orig_color0 = 0.9, 0.7, 0.5, 0.3
    orig_color1 = 0.8, 0.6, 0.4, 0.2

    expected_isolated_color0 = 0.3, 0.3, 0.3, 0.0
    expected_isolated_color1 = 0.2, 0.2, 0.2, 0.0

    new_color0 = 0.1, 0.1, 0.1, 0.0
    new_color1 = 0.4, 0.4, 0.4, 0.0

    expected_merged_color0 = list(orig_color0)
    expected_merged_color0[3] = 0.1
    expected_merged_color1 = list(orig_color1)
    expected_merged_color1[3] = 0.4

    # Actual test
    m = plane_object.data
    m.attributes.new("MyColor", data_type, domain)
    m.attributes.active_color_name = "MyColor"

    m.attributes.active_color.data[0].color_srgb = orig_color0
    m.attributes.active_color.data[1].color_srgb = orig_color1

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=3)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, expected_isolated_color0, atol=COLOR_ATOL)
    assert_allclose(m.attributes.active_color.data[1].color_srgb, expected_isolated_color1, atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = new_color0
    m.attributes.active_color.data[1].color_srgb = new_color1

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=3)
    assert m.attributes.active_color_name == "MyColor"
    assert len(m.color_attributes) == 1
    assert_allclose(m.attributes.active_color.data[0].color_srgb, expected_merged_color0, atol=COLOR_ATOL)
    assert_allclose(m.attributes.active_color.data[1].color_srgb, expected_merged_color1, atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
def test_ops_vertex_paint_isolate_channel_switch_between_channels(data_type, domain, context, plane_object):
    m = plane_object.data
    m.attributes.new("MyColor", data_type, domain)
    m.attributes.active_color_name = "MyColor"

    m.attributes.active_color.data[0].color_srgb = 0.9, 0.7, 0.5, 0.3

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=0)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.9, 0.0, 0.0, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.8, 0.0, 0.0, 0.0

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=1)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.0, 0.7, 0.0, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.0, 0.6, 0.0, 0.0

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=2)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.0, 0.0, 0.5, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.0, 0.0, 0.4, 0.0

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=3)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.3, 0.3, 0.3, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.2, 0.2, 0.2, 0.0

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=3)
    assert m.attributes.active_color_name == "MyColor"
    assert len(m.color_attributes) == 1
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.8, 0.6, 0.4, 0.2), atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
def test_ops_vertex_paint_isolate_channel_extend(data_type, domain, context, plane_object):
    m = plane_object.data
    m.attributes.new("MyColor", data_type, domain)
    m.attributes.active_color_name = "MyColor"

    m.attributes.active_color.data[0].color_srgb = 0.9, 0.7, 0.5, 0.3

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=0, extend=True)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.9, 0.0, 0.0, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.8, 0.0, 0.0, 0.0

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=1, extend=True)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.8, 0.7, 0.0, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.8, 0.6, 0.0, 0.0

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=2, extend=True)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.8, 0.6, 0.5, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.8, 0.6, 0.4, 0.0

    # Alpha is isolated by itself even in extend mode
    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=3, extend=True)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.3, 0.3, 0.3, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.2, 0.2, 0.2, 0.0

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=3, extend=True)
    assert m.attributes.active_color_name == "MyColor"
    assert len(m.color_attributes) == 1
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.8, 0.6, 0.4, 0.2), atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
def test_ops_vertex_paint_isolate_channel_extend_from_alpha_to_rgb(data_type, domain, context, plane_object):
    m = plane_object.data
    m.attributes.new("MyColor", data_type, domain)
    m.attributes.active_color_name = "MyColor"

    m.attributes.active_color.data[0].color_srgb = 0.9, 0.7, 0.5, 0.3

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    # On alpha to RGB channel transition, the alpha channel should be applied to the original attribute and no longer
    # isolated, only the RGB channel will be isolated, even in extend mode. Cannot have alpha and RGB isolated at the
    # same time.
    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=3, extend=True)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.3, 0.3, 0.3, 0.0), atol=COLOR_ATOL)

    m.attributes.active_color.data[0].color_srgb = 0.25, 0.25, 0.25, 0.0

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=0, extend=True)
    assert m.attributes.active_color_name != "MyColor"
    assert len(m.color_attributes) == 2
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.9, 0.0, 0.0, 0.0), atol=COLOR_ATOL)

    bpy.ops.sollumz.vertex_paint_isolate_toggle_channel(channel=0)
    assert m.attributes.active_color_name == "MyColor"
    assert len(m.color_attributes) == 1
    assert_allclose(m.attributes.active_color.data[0].color_srgb, (0.9, 0.7, 0.5, 0.25), atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
@pytest.mark.parametrize("gradient_type", ("LINEAR", "RADIAL"))
@pytest.mark.parametrize("use_hue_blend", (False, True))
def test_ops_vertex_paint_gradient(data_type, domain, context, gradient_type, use_hue_blend, plane_object):
    m = plane_object.data
    m.attributes.new("MyColor", data_type, domain)
    m.attributes.active_color_name = "MyColor"

    for i in range(len(m.attributes.active_color.data)):
        m.attributes.active_color.data[i].color_srgb = 0.1, 0.2, 0.3, 0.4

    # Find 3D Viewport window
    area = next(area for area in context.screen.areas if area.type == "VIEW_3D")
    region = next(region for region in area.regions if region.type == "WINDOW")

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    with context.temp_override(area=area, region=region):
        bpy.ops.sollumz.vertex_paint_gradient(
            start_color=(1.0, 0.0, 0.0),
            end_color=(0.0, 0.0, 1.0),
            start_point=(0.0, 0.0),
            end_point=(context.region.width, context.region.height),
            type=gradient_type,
            use_hue_blend=use_hue_blend,
        )

    for i in range(len(m.attributes.active_color.data)):
        # rgb should have changed on all vertices
        assert m.attributes.active_color.data[i].color_srgb[:3] != (0.1, 0.2, 0.3)
        # alpha should remain unchanged
        assert_allclose(m.attributes.active_color.data[i].color_srgb[3:4], [0.4], atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")
