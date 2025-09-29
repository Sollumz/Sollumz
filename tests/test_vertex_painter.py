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
