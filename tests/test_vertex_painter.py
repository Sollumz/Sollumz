import bpy
import numpy as np
import pytest
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
def test_ops_vertex_paint_gradient(data_type, domain, gradient_type, use_hue_blend, context, plane_object):
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


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
@pytest.mark.parametrize(
    "mapping, expected_color",
    (
        ((0, 1, 2, 3), (0.1, 0.2, 0.3, 0.4)),  # identity, RGBA -> RGBA
        ((3, 2, 1, 0), (0.4, 0.3, 0.2, 0.1)),  # swizzle, ABGR -> RGBA
        ((1, 0, 3, 2), (0.2, 0.1, 0.4, 0.3)),  # swizzle, GRAB -> RGBA
        ((4, 3, 0, 4), (0.9, 0.4, 0.1, 0.9)),  # some unchanged, _AR_ -> RGBA
        ((0, 0, 0, 0), (0.1, 0.1, 0.1, 0.1)),  # all from RED
        ((1, 1, 1, 1), (0.2, 0.2, 0.2, 0.2)),  # all from GREEN
        ((2, 2, 2, 2), (0.3, 0.3, 0.3, 0.3)),  # all from BLUE
        ((3, 3, 3, 3), (0.4, 0.4, 0.4, 0.4)),  # all from ALPHA
        ((4, 4, 4, 4), (0.9, 0.9, 0.9, 0.9)),  # all unchanged
    ),
)
def test_ops_vertex_paint_transfer_channels_between_attributes(
    data_type, domain, mapping, expected_color, context, cube_object
):
    src_color = 0.1, 0.2, 0.3, 0.4
    placeholder = 0.9
    channels = "RED", "GREEN", "BLUE", "ALPHA", "NONE"
    r, g, b, a = mapping

    m = cube_object.data
    m.attributes.new("MySrc", data_type, domain)
    m.attributes.new("MyDst", data_type, domain)

    src_attr = m.attributes["MySrc"]
    dst_attr = m.attributes["MyDst"]
    for i in range(len(src_attr.data)):
        src_attr.data[i].color_srgb = src_color
        dst_attr.data[i].color_srgb = placeholder, placeholder, placeholder, placeholder

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_transfer_channels(
        src_attribute="MySrc",
        dst_attribute="MyDst",
        src_for_dst_r=channels[r],
        src_for_dst_g=channels[g],
        src_for_dst_b=channels[b],
        src_for_dst_a=channels[a],
    )

    for i in range(len(src_attr.data)):
        # src remains unchanged
        assert_allclose(src_attr.data[i].color_srgb, src_color, atol=COLOR_ATOL)
        # dst changed
        assert_allclose(dst_attr.data[i].color_srgb, expected_color, atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
@pytest.mark.parametrize(
    "mapping, expected_color",
    (
        ((0, 1, 2, 3), (0.1, 0.2, 0.3, 0.4)),  # identity, RGBA -> RGBA
        ((3, 2, 1, 0), (0.4, 0.3, 0.2, 0.1)),  # swizzle, ABGR -> RGBA
        ((1, 0, 3, 2), (0.2, 0.1, 0.4, 0.3)),  # swizzle, GRAB -> RGBA
        ((4, 3, 0, 4), (0.1, 0.4, 0.1, 0.4)),  # some unchanged, _AR_ -> RGBA
        ((0, 0, 0, 0), (0.1, 0.1, 0.1, 0.1)),  # all from RED
        ((1, 1, 1, 1), (0.2, 0.2, 0.2, 0.2)),  # all from GREEN
        ((2, 2, 2, 2), (0.3, 0.3, 0.3, 0.3)),  # all from BLUE
        ((3, 3, 3, 3), (0.4, 0.4, 0.4, 0.4)),  # all from ALPHA
        ((4, 4, 4, 4), (0.1, 0.2, 0.3, 0.4)),  # all unchanged
    ),
)
def test_ops_vertex_paint_transfer_channels_within_same_attribute(
    data_type, domain, mapping, expected_color, context, cube_object
):
    src_color = 0.1, 0.2, 0.3, 0.4
    channels = "RED", "GREEN", "BLUE", "ALPHA", "NONE"
    r, g, b, a = mapping

    m = cube_object.data
    m.attributes.new("MyAttr", data_type, domain)

    attr = m.attributes["MyAttr"]
    for i in range(len(attr.data)):
        attr.data[i].color_srgb = src_color

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_transfer_channels(
        src_attribute="MyAttr",
        dst_attribute="MyAttr",
        src_for_dst_r=channels[r],
        src_for_dst_g=channels[g],
        src_for_dst_b=channels[b],
        src_for_dst_a=channels[a],
    )

    for i in range(len(attr.data)):
        assert_allclose(attr.data[i].color_srgb, expected_color, atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


def test_ops_vertex_paint_transfer_channels_between_attributes_on_different_domains_point_to_corner(
    context, cube_object
):
    src_colors = (
        # a color per vertex of the cube
        (0.01, 0.02, 0.03, 0.04),
        (0.11, 0.12, 0.13, 0.14),
        (0.21, 0.22, 0.23, 0.24),
        (0.31, 0.32, 0.33, 0.34),
        (0.41, 0.42, 0.43, 0.44),
        (0.51, 0.52, 0.53, 0.54),
        (0.61, 0.62, 0.63, 0.64),
        (0.71, 0.72, 0.73, 0.74),
    )
    placeholder = 0.9

    m = cube_object.data
    m.attributes.new("MySrc", "FLOAT_COLOR", "POINT")
    m.attributes.new("MyDst", "FLOAT_COLOR", "CORNER")

    src_attr = m.attributes["MySrc"]
    dst_attr = m.attributes["MyDst"]
    for vertex in m.vertices:
        src_attr.data[vertex.index].color_srgb = src_colors[vertex.index]
    for loop in m.loops:
        dst_attr.data[loop.index].color_srgb = placeholder, placeholder, placeholder, placeholder

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_transfer_channels(
        src_attribute="MySrc",
        dst_attribute="MyDst",
        src_for_dst_r="RED",
        src_for_dst_g="GREEN",
        src_for_dst_b="BLUE",
        src_for_dst_a="ALPHA",
    )

    for vertex in m.vertices:
        # src remains unchanged
        assert_allclose(src_attr.data[vertex.index].color_srgb, src_colors[vertex.index], atol=COLOR_ATOL)

    for loop in m.loops:
        # dst changed
        assert_allclose(dst_attr.data[loop.index].color_srgb, src_colors[loop.vertex_index], atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


def test_ops_vertex_paint_transfer_channels_between_attributes_on_different_domains_corner_to_point(
    context, cube_object
):
    src_colors = (
        # a color per face corner of each vertex of the cube
        (0.2, 0.1, 0.25, 0.05),
        (0.4, 0.2, 0.45, 0.60),
        (0.6, 0.3, 0.55, 0.85),
    )
    avg_color = (0.4, 0.2, 0.416667, 0.5)  # each vertex should end up with the average of the face corner colors
    placeholder = 0.9

    m = cube_object.data
    m.attributes.new("MySrc", "FLOAT_COLOR", "CORNER")
    m.attributes.new("MyDst", "FLOAT_COLOR", "POINT")

    src_attr = m.attributes["MySrc"]
    dst_attr = m.attributes["MyDst"]
    vertex_to_loops = [[] for _ in range(len(m.vertices))]
    for poly in m.polygons:
        for loop_index in poly.loop_indices:
            loop = m.loops[loop_index]
            vertex_to_loops[loop.vertex_index].append(loop_index)

    for loops in vertex_to_loops:
        src_attr.data[loops[0]].color_srgb = src_colors[0]
        src_attr.data[loops[1]].color_srgb = src_colors[1]
        src_attr.data[loops[2]].color_srgb = src_colors[2]

    for vertex in m.vertices:
        dst_attr.data[vertex.index].color_srgb = placeholder, placeholder, placeholder, placeholder

    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    bpy.ops.sollumz.vertex_paint_transfer_channels(
        src_attribute="MySrc",
        dst_attribute="MyDst",
        src_for_dst_r="RED",
        src_for_dst_g="GREEN",
        src_for_dst_b="BLUE",
        src_for_dst_a="ALPHA",
    )

    for loops in vertex_to_loops:
        # src remains unchanged
        assert_allclose(src_attr.data[loops[0]].color_srgb, src_colors[0], atol=COLOR_ATOL)
        assert_allclose(src_attr.data[loops[1]].color_srgb, src_colors[1], atol=COLOR_ATOL)
        assert_allclose(src_attr.data[loops[2]].color_srgb, src_colors[2], atol=COLOR_ATOL)

    for vertex in m.vertices:
        # dst changed (average of all colors in face corners)
        assert_allclose(dst_attr.data[vertex.index].color_srgb, avg_color, atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
def test_ops_vertex_paint_multiproxy_enter_exit_without_modifications(data_type, domain, context, four_plane_objects):
    """Simple sanity check, just enter & exit multiproxy shouldn't modify anything."""
    src_colors = (
        (0.1, 0.1, 0.1, 0.1),
        (0.2, 0.2, 0.2, 0.2),
        (0.3, 0.3, 0.3, 0.3),
        (0.4, 0.4, 0.4, 0.4),
    )
    obj0, obj1, obj2, obj3 = four_plane_objects

    for obj_idx, obj in enumerate(four_plane_objects):
        mesh = obj.data
        attr = mesh.attributes.new("MyAttr", data_type, domain)
        for i in range(len(attr.data)):
            attr.data[i].color_srgb = src_colors[obj_idx]

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj0.select_set(True)
    obj1.select_set(True)
    obj2.select_set(True)
    obj3.select_set(True)

    bpy.ops.sollumz.vertex_paint_multiproxy()
    bpy.ops.sollumz.vertex_paint_multiproxy_exit()

    for obj_idx, obj in enumerate(four_plane_objects):
        mesh = obj.data
        attr = mesh.color_attributes["MyAttr"]
        for i in range(len(attr.data)):
            assert_allclose(attr.data[i].color_srgb, src_colors[obj_idx], atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("data_type", ("BYTE_COLOR", "FLOAT_COLOR"))
@pytest.mark.parametrize("domain", ("CORNER", "POINT"))
def test_ops_vertex_paint_multiproxy_all_have_same_attribute_all_modified(
    data_type, domain, context, four_plane_objects
):
    """All objects have the same attribute and can be modified in multiproxy."""
    src_colors = (
        (0.1, 0.1, 0.1, 0.1),
        (0.2, 0.2, 0.2, 0.2),
        (0.3, 0.3, 0.3, 0.3),
        (0.4, 0.4, 0.4, 0.4),
    )
    expected_colors = (
        (0.51, 0.52, 0.53, 0.54),
        (0.61, 0.62, 0.63, 0.64),
        (0.71, 0.72, 0.73, 0.74),
        (0.81, 0.82, 0.83, 0.84),
    )
    obj0, obj1, obj2, obj3 = four_plane_objects

    for obj_idx, obj in enumerate(four_plane_objects):
        mesh = obj.data
        attr = mesh.attributes.new("MyAttr", data_type, domain)
        for i in range(len(attr.data)):
            attr.data[i].color_srgb = src_colors[obj_idx]

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj0.select_set(True)
    obj1.select_set(True)
    obj2.select_set(True)
    obj3.select_set(True)

    bpy.ops.sollumz.vertex_paint_multiproxy()
    proxy_obj = context.active_object
    assert proxy_obj.name.startswith(".multiproxy")
    assert len(proxy_obj.data.color_attributes) == 1
    assert "MyAttr" in proxy_obj.data.color_attributes
    proxy_attr = proxy_obj.data.color_attributes["MyAttr"]
    assert len(proxy_attr.data) == (4 * 4)  # plane, both point and corner attributes have 4 elements on each plane
    for i in range(4 * 4):
        # use a different color for each part that corresponds to a different object
        proxy_attr.data[i].color_srgb = expected_colors[i // 4]

    bpy.ops.sollumz.vertex_paint_multiproxy_exit()

    for obj_idx, obj in enumerate(four_plane_objects):
        mesh = obj.data
        attr = mesh.color_attributes["MyAttr"]
        for i in range(len(attr.data)):
            assert_allclose(attr.data[i].color_srgb, expected_colors[obj_idx], atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


def test_ops_vertex_paint_multiproxy_only_some_objects_selected(context, four_plane_objects):
    """Only some objects selected and modified in multiproxy, other objects in the scene must remain unmodified."""
    src_colors = (
        (0.1, 0.1, 0.1, 0.1),
        (0.2, 0.2, 0.2, 0.2),
        (0.3, 0.3, 0.3, 0.3),
        (0.4, 0.4, 0.4, 0.4),
    )
    expected_colors = (
        (0.51, 0.52, 0.53, 0.54),
        (0.2, 0.2, 0.2, 0.2),
        (0.71, 0.72, 0.73, 0.74),
        (0.4, 0.4, 0.4, 0.4),
    )
    obj0, obj1, obj2, obj3 = four_plane_objects

    for obj_idx, obj in enumerate(four_plane_objects):
        mesh = obj.data
        attr = mesh.attributes.new("MyAttr", "FLOAT_COLOR", "CORNER")
        for i in range(len(attr.data)):
            attr.data[i].color_srgb = src_colors[obj_idx]

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj0.select_set(True)
    obj1.select_set(False)
    obj2.select_set(True)
    obj3.select_set(False)

    bpy.ops.sollumz.vertex_paint_multiproxy()
    proxy_obj = context.active_object
    assert proxy_obj.name.startswith(".multiproxy")
    assert len(proxy_obj.data.color_attributes) == 1
    assert "MyAttr" in proxy_obj.data.color_attributes
    proxy_attr = proxy_obj.data.color_attributes["MyAttr"]
    assert len(proxy_attr.data) == (4 * 2)
    for i in range(4 * 2):
        # use a different color for each part that corresponds to a different object
        proxy_attr.data[i].color_srgb = expected_colors[(i // 4) * 2]

    bpy.ops.sollumz.vertex_paint_multiproxy_exit()

    for obj_idx, obj in enumerate(four_plane_objects):
        mesh = obj.data
        attr = mesh.color_attributes["MyAttr"]
        for i in range(len(attr.data)):
            assert_allclose(attr.data[i].color_srgb, expected_colors[obj_idx], atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


def test_ops_vertex_paint_multiproxy_multiple_attributes_all_can_be_modified(context, four_plane_objects):
    """Objects have multiple color attributes and all of them can be modified in multiproxy."""
    src_colors = (
        (
            (0.1, 0.1, 0.1, 0.1),
            (0.2, 0.2, 0.2, 0.2),
            (0.3, 0.3, 0.3, 0.3),
            (0.4, 0.4, 0.4, 0.4),
        ),
        (
            (0.5, 0.5, 0.5, 0.5),
            (0.6, 0.6, 0.6, 0.6),
            (0.7, 0.7, 0.7, 0.7),
            (0.8, 0.8, 0.8, 0.8),
        ),
    )
    expected_colors = (
        (
            (0.51, 0.52, 0.53, 0.54),
            (0.61, 0.62, 0.63, 0.64),
            (0.71, 0.72, 0.73, 0.74),
            (0.81, 0.82, 0.83, 0.84),
        ),
        (
            (0.11, 0.12, 0.13, 0.14),
            (0.21, 0.22, 0.23, 0.24),
            (0.31, 0.32, 0.33, 0.34),
            (0.41, 0.42, 0.43, 0.44),
        ),
    )
    obj0, obj1, obj2, obj3 = four_plane_objects

    for obj_idx, obj in enumerate(four_plane_objects):
        mesh = obj.data
        attr0 = mesh.attributes.new("MyAttr0", "BYTE_COLOR", "CORNER")
        attr1 = mesh.attributes.new("MyAttr1", "FLOAT_COLOR", "POINT")
        for i in range(len(attr0.data)):
            attr0.data[i].color_srgb = src_colors[0][obj_idx]
        for i in range(len(attr1.data)):
            attr1.data[i].color_srgb = src_colors[1][obj_idx]

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj0.select_set(True)
    obj1.select_set(True)
    obj2.select_set(True)
    obj3.select_set(True)

    bpy.ops.sollumz.vertex_paint_multiproxy()
    proxy_obj = context.active_object
    assert proxy_obj.name.startswith(".multiproxy")
    assert len(proxy_obj.data.color_attributes) == 2
    assert "MyAttr0" in proxy_obj.data.color_attributes
    assert "MyAttr1" in proxy_obj.data.color_attributes
    proxy_attr0 = proxy_obj.data.color_attributes["MyAttr0"]
    proxy_attr1 = proxy_obj.data.color_attributes["MyAttr1"]
    for i in range(len(proxy_attr0.data)):
        proxy_attr0.data[i].color_srgb = expected_colors[0][i // 4]
    for i in range(len(proxy_attr1.data)):
        proxy_attr1.data[i].color_srgb = expected_colors[1][i // 4]

    bpy.ops.sollumz.vertex_paint_multiproxy_exit()

    for obj_idx, obj in enumerate(four_plane_objects):
        mesh = obj.data
        attr0 = mesh.color_attributes["MyAttr0"]
        attr1 = mesh.color_attributes["MyAttr1"]
        for i in range(len(attr0.data)):
            assert_allclose(attr0.data[i].color_srgb, expected_colors[0][obj_idx], atol=COLOR_ATOL)
        for i in range(len(attr1.data)):
            assert_allclose(attr1.data[i].color_srgb, expected_colors[1][obj_idx], atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


@pytest.mark.parametrize("subcase", ("ADD_MISSING", "SKIP_MISSING"))
def test_ops_vertex_paint_multiproxy_multiple_different_attributes(subcase, context, four_plane_objects):
    """Objects have different color attributes each, all of them can be modified in multiproxy. On exit ask the
    user if he wants to:
        - Add missing attributes to the mesh that don't have them (ADD_MISSING)
        - Ignore them, only apply to meshes that already have them (SKIP_MISSING)
    """
    src_colors = (
        (0.1, 0.1, 0.1, 0.1),
        (0.2, 0.2, 0.2, 0.2),
        (0.3, 0.3, 0.3, 0.3),
        (0.4, 0.4, 0.4, 0.4),
    )
    expected_colors = (
        (0.51, 0.52, 0.53, 0.54),
        (0.61, 0.62, 0.63, 0.64),
        (0.71, 0.72, 0.73, 0.74),
        (0.81, 0.82, 0.83, 0.84),
    )
    obj0, obj1, obj2, obj3 = four_plane_objects
    # A different attribute per object
    obj0.data.attributes.new("MyAttr0", "FLOAT_COLOR", "CORNER").data.foreach_set(
        "color_srgb", np.array([src_colors[0]] * 4).ravel()
    )
    obj1.data.attributes.new("MyAttr1", "FLOAT_COLOR", "POINT").data.foreach_set(
        "color_srgb", np.array([src_colors[1]] * 4).ravel()
    )
    obj2.data.attributes.new("MyAttr2", "BYTE_COLOR", "CORNER").data.foreach_set(
        "color_srgb", np.array([src_colors[2]] * 4).ravel()
    )
    obj3.data.attributes.new("MyAttr3", "BYTE_COLOR", "POINT").data.foreach_set(
        "color_srgb", np.array([src_colors[3]] * 4).ravel()
    )

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj0.select_set(True)
    obj1.select_set(True)
    obj2.select_set(True)
    obj3.select_set(True)

    bpy.ops.sollumz.vertex_paint_multiproxy()

    # Paint each attribute with a different color
    proxy_obj = context.active_object
    proxy_attrs = proxy_obj.data.color_attributes
    assert "MyAttr0" in proxy_attrs
    assert "MyAttr1" in proxy_attrs
    assert "MyAttr2" in proxy_attrs
    assert "MyAttr3" in proxy_attrs
    assert len(proxy_attrs) == 4
    proxy_attr0 = proxy_attrs["MyAttr0"]
    proxy_attr1 = proxy_attrs["MyAttr1"]
    proxy_attr2 = proxy_attrs["MyAttr2"]
    proxy_attr3 = proxy_attrs["MyAttr3"]
    assert proxy_attr0.data_type == "FLOAT_COLOR" and proxy_attr0.domain == "CORNER"
    assert proxy_attr1.data_type == "FLOAT_COLOR" and proxy_attr1.domain == "POINT"
    assert proxy_attr2.data_type == "BYTE_COLOR" and proxy_attr2.domain == "CORNER"
    assert proxy_attr3.data_type == "BYTE_COLOR" and proxy_attr3.domain == "POINT"
    proxy_attr0.data.foreach_set("color_srgb", np.array([expected_colors[0]] * 4 * 4).ravel())
    proxy_attr1.data.foreach_set("color_srgb", np.array([expected_colors[1]] * 4 * 4).ravel())
    proxy_attr2.data.foreach_set("color_srgb", np.array([expected_colors[2]] * 4 * 4).ravel())
    proxy_attr3.data.foreach_set("color_srgb", np.array([expected_colors[3]] * 4 * 4).ravel())

    bpy.ops.sollumz.vertex_paint_multiproxy_exit(
        missing_attributes_mode=subcase,  # This choice would be prompted to the user when called from the UI, here we just test each case directly
    )

    match subcase:
        case "SKIP_MISSING":
            # Each object only has its own attribute
            for obj_idx, obj in enumerate(four_plane_objects):
                mesh = obj.data
                assert f"MyAttr{obj_idx}" in mesh.color_attributes
                assert len(mesh.color_attributes) == 1
                attr = mesh.color_attributes[f"MyAttr{obj_idx}"]
                for i in range(len(attr.data)):
                    assert_allclose(attr.data[i].color_srgb, expected_colors[obj_idx], atol=COLOR_ATOL)
        case "ADD_MISSING":
            # All objects have all 4 four attributes now
            for obj_idx, obj in enumerate(four_plane_objects):
                mesh = obj.data
                assert "MyAttr0" in mesh.color_attributes
                assert "MyAttr1" in mesh.color_attributes
                assert "MyAttr2" in mesh.color_attributes
                assert "MyAttr3" in mesh.color_attributes
                assert len(mesh.color_attributes) == 4
                attr0 = mesh.color_attributes["MyAttr0"]
                attr1 = mesh.color_attributes["MyAttr1"]
                attr2 = mesh.color_attributes["MyAttr2"]
                attr3 = mesh.color_attributes["MyAttr3"]
                assert attr0.data_type == "FLOAT_COLOR" and attr0.domain == "CORNER"
                assert attr1.data_type == "FLOAT_COLOR" and attr1.domain == "POINT"
                assert attr2.data_type == "BYTE_COLOR" and attr2.domain == "CORNER"
                assert attr3.data_type == "BYTE_COLOR" and attr3.domain == "POINT"
                for attr_idx, attr in enumerate((attr0, attr1, attr2, attr3)):
                    for i in range(len(attr.data)):
                        assert_allclose(attr.data[i].color_srgb, expected_colors[attr_idx], atol=COLOR_ATOL)

    bpy.ops.object.mode_set(mode="OBJECT")


def test_ops_vertex_paint_multiproxy_same_attribute_on_different_domains_not_allowed(context, four_plane_objects):
    """Different meshes have an attribute with the same name but on different domains. No intuitive way to handle this,
    warn and cancel the operation.
    """
    obj0, obj1, obj2, obj3 = four_plane_objects
    obj0.data.attributes.new("MyAttr", "FLOAT_COLOR", "CORNER")
    obj1.data.attributes.new("MyAttr", "FLOAT_COLOR", "POINT")
    obj2.data.attributes.new("MyAttr", "FLOAT_COLOR", "CORNER")
    obj3.data.attributes.new("MyAttr", "FLOAT_COLOR", "POINT")

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj0.select_set(True)
    obj1.select_set(True)
    obj2.select_set(True)
    obj3.select_set(True)

    ret = bpy.ops.sollumz.vertex_paint_multiproxy()
    assert ret == {"CANCELLED"}
    assert not context.active_object.name.startswith(".multiproxy")

    bpy.ops.object.mode_set(mode="OBJECT")


def test_ops_vertex_paint_multiproxy_same_attribute_with_different_data_type_allowed(context, four_plane_objects):
    """Different meshes have an attribute named the same but with a different data type each. The proxy should fallback
    to FLOAT_COLOR. When always the same data type, it should maintain it.
    """
    obj0, obj1, obj2, obj3 = four_plane_objects
    obj0.data.attributes.new("MyAttr", "FLOAT_COLOR", "POINT")
    obj1.data.attributes.new("MyAttr", "BYTE_COLOR", "POINT")
    obj2.data.attributes.new("MyAttr", "FLOAT_COLOR", "POINT")
    obj3.data.attributes.new("MyAttr", "BYTE_COLOR", "POINT")
    for obj in four_plane_objects:
        obj.data.attributes.new("MyOtherAttrByte", "BYTE_COLOR", "POINT")
    for obj in four_plane_objects:
        obj.data.attributes.new("MyOtherAttrFloat", "FLOAT_COLOR", "POINT")

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj0.select_set(True)
    obj1.select_set(True)
    obj2.select_set(True)
    obj3.select_set(True)

    ret = bpy.ops.sollumz.vertex_paint_multiproxy()
    assert ret == {"FINISHED"}

    proxy_obj = context.active_object
    proxy_attrs = proxy_obj.data.color_attributes
    assert len(proxy_attrs) == 3
    assert "MyAttr" in proxy_attrs
    assert "MyOtherAttrByte" in proxy_attrs
    assert "MyOtherAttrFloat" in proxy_attrs
    assert proxy_attrs["MyAttr"].data_type == "FLOAT_COLOR"
    assert proxy_attrs["MyOtherAttrByte"].data_type == "BYTE_COLOR"
    assert proxy_attrs["MyOtherAttrFloat"].data_type == "FLOAT_COLOR"

    bpy.ops.sollumz.vertex_paint_multiproxy_exit()

    bpy.ops.object.mode_set(mode="OBJECT")


# TODO: handle modified mesh edge cases in multiproxy
# def test_ops_vertex_paint_multiproxy_one_mesh_modified_before_exit_not_allowed(context, four_plane_objects):
#     """User entered edit mode on an object managed by a multiproxy and modified it (added or deleted vertices), so TODO: warn and discard? trying to apply any color might be unreliable now. Can still apply on the objects"""
#     raise NotImplementedError()
#
#
# def test_ops_vertex_paint_multiproxy_proxy_mesh_modified_before_exit_not_allowed(context, four_plane_objects):
#     """User entered edit mode and modified proxy mesh (added or deleted vertices), so TODO: warn and discard? trying to apply any color might be unreliable now"""
#     raise NotImplementedError()


def test_ops_vertex_paint_multiproxy_one_object_deleted_before_exit(context, four_plane_objects):
    """Some object managed by the multiproxy got deleted before exiting, discard changes to deleted objects but still
    apply to remaining objects.
    """
    obj0, obj1, obj2, obj3 = four_plane_objects

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj1.select_set(True)
    obj2.select_set(True)
    obj3.select_set(True)

    bpy.ops.sollumz.vertex_paint_multiproxy()
    proxy_obj = context.active_object
    assert proxy_obj.name.startswith(".multiproxy")

    bpy.data.objects.remove(obj2)
    bpy.ops.sollumz.vertex_paint_multiproxy_exit()

    bpy.ops.object.mode_set(mode="OBJECT")


def test_ops_vertex_paint_multiproxy_all_objects_deleted_before_exit(context, four_plane_objects):
    """All objects managed by the multiproxy get deleted before exiting, discard."""
    obj0, obj1, obj2, obj3 = four_plane_objects

    context.view_layer.objects.active = obj0
    bpy.ops.object.mode_set(mode="VERTEX_PAINT")

    obj1.select_set(True)
    obj2.select_set(True)
    obj3.select_set(True)

    bpy.ops.sollumz.vertex_paint_multiproxy()
    proxy_obj = context.active_object
    assert proxy_obj.name.startswith(".multiproxy")

    bpy.data.objects.remove(obj0)
    bpy.data.objects.remove(obj1)
    bpy.data.objects.remove(obj2)
    bpy.data.objects.remove(obj3)
    bpy.ops.sollumz.vertex_paint_multiproxy_exit()

    # bpy.ops.object.mode_set(mode="OBJECT") # no objects in the scene, can't change mode
