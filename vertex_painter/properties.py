import bpy
from mathutils import Color

type_vcol = 'VCOL'
type_vgroup = 'VGROUP'
type_uv = 'UV'
type_normal = 'NORMALS'

channel_blend_mode_items = (('ADD', "Add", ""),
                            ('SUB', "Subtract", ""),
                            ('MUL', "Multiply", ""),
                            ('DIV', "Divide", ""),
                            ('LIGHTEN', "Lighten",  ""),
                            ('DARKEN', "Darken", ""),
                            ('MIX', "Mix", ""))

red_id = 'R'
green_id = 'G'
blue_id = 'B'
alpha_id = 'A'

channel_items = ((red_id, "R", ""),
                 (green_id, "G", ""),
                 (blue_id, "B", ""),
                 (alpha_id, "A", ""))

isolate_mode_name_prefix = 'Sollumz-alpha'

valid_channel_ids = 'RGBA'


class SollumzVertexPainterProperties(bpy.types.PropertyGroup):

    def update_active_channels(self, context):
        if self.use_grayscale or not self.match_brush_to_active_channels:
            return None

        active_channels = self.active_channels

        # set draw color based on mask
        draw_color = [0.0, 0.0, 0.0]
        if red_id in active_channels:
            draw_color[0] = 1.0
        if green_id in active_channels:
            draw_color[1] = 1.0
        if blue_id in active_channels:
            draw_color[2] = 1.0

        context.tool_settings.vertex_paint.brush.color = draw_color

        return None

    def update_brush_value_isolate(self, context):
        brush = context.tool_settings.vertex_paint.brush
        v1 = self.brush_value_isolate
        v2 = self.brush_secondary_value_isolate
        brush.color = Color((v1, v1, v1))
        brush.secondary_color = Color((v2, v2, v2))

        return None

    def toggle_grayscale(self, context):
        brush = context.tool_settings.vertex_paint.brush

        if self.use_grayscale:
            self.brush_color = brush.color
            self.brush_secondary_color = brush.secondary_color

            v1 = self.brush_value_isolate
            v2 = self.brush_secondary_value_isolate
            brush.color = Color((v1, v1, v1))
            brush.secondary_color = Color((v2, v2, v2))
        else:
            brush.color = self.brush_color
            brush.secondary_color = self.brush_secondary_color

        return None

    active_channels: bpy.props.EnumProperty(
        name="Active Channels",
        options={'ENUM_FLAG'},
        items=channel_items,
        description="Which channels to enable.",
        default={'R', 'G', 'B'},
        update=update_active_channels
    )

    match_brush_to_active_channels: bpy.props.BoolProperty(
        name="Match Active Channels",
        default=True,
        description="Change the brush color to match the active channels.",
        update=update_active_channels
    )

    use_grayscale: bpy.props.BoolProperty(
        name="Use Grayscale",
        default=False,
        description="Show grayscale values instead of RGB colors.",
        update=toggle_grayscale
    )

    # Used only to store the color between RGBA and isolate modes
    brush_color: bpy.props.FloatVectorProperty(
        name="Brush Color",
        description="Brush primary color.",
        default=(1, 0, 0)
    )

    brush_secondary_color: bpy.props.FloatVectorProperty(
        name="Brush Secondary Color",
        description="Brush secondary color.",
        default=(1, 0, 0)
    )

    # Replacement for color in the isolate mode UI
    brush_value_isolate: bpy.props.FloatProperty(
        name="Brush Value",
        description="Value of the brush color.",
        default=1.0,
        min=0.0, max=1.0,
        update=update_brush_value_isolate
    )

    brush_secondary_value_isolate: bpy.props.FloatProperty(
        name="Brush Value",
        description="Value of the brush secondary color.",
        default=0.0,
        min=0.0, max=1.0,
        update=update_brush_value_isolate
    )

    def vcol_layer_items(self, context):
        obj = context.active_object
        mesh = obj.data

        items = [] if mesh.vertex_colors is None else [
            ("{0} {1}".format(type_vcol, vcol.name),
             vcol.name, "") for vcol in mesh.vertex_colors]
        ext = [] if obj.vertex_groups is None else [
            ("{0} {1}".format(type_vgroup, group.name),
             "W: " + group.name, "") for group in obj.vertex_groups]
        items.extend(ext)
        ext = [] if mesh.uv_layers is None else [
            ("{0} {1}".format(type_uv, uv.name),
             "UV: " + uv.name, "") for uv in mesh.uv_layers]
        items.extend(ext)
        ext = [("{0} {1}".format(type_normal, "Normals"), "Normals", "")]
        items.extend(ext)

        return items

    src_vcol_id: bpy.props.EnumProperty(
        name="Source Layer",
        items=vcol_layer_items,
        description="Source (Src) vertex color layer.",
    )

    src_channel_id: bpy.props.EnumProperty(
        name="Source Channel",
        items=channel_items,
        # default=red_id,
        description="Source (Src) color channel."
    )

    dst_vcol_id: bpy.props.EnumProperty(
        name="Destination Layer",
        items=vcol_layer_items,
        description="Destination (Dst) vertex color layer.",
    )

    dst_channel_id: bpy.props.EnumProperty(
        name="Destination Channel",
        items=channel_items,
        # default=green_id,
        description="Destination (Dst) color channel."
    )

    channel_blend_mode: bpy.props.EnumProperty(
        name="Channel Blend Mode",
        items=channel_blend_mode_items,
        description="Channel blending operation.",
    )


def register():
    bpy.types.Scene.vert_paint_color1 = bpy.props.FloatVectorProperty(
        name="Vert Color 1",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color2 = bpy.props.FloatVectorProperty(
        name="Vert Color 2",
        subtype="COLOR_GAMMA",
        default=(0.0, 0.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color3 = bpy.props.FloatVectorProperty(
        name="Vert Color 3",
        subtype="COLOR_GAMMA",
        default=(0.0, 1.0, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color4 = bpy.props.FloatVectorProperty(
        name="Vert Color 4",
        subtype="COLOR_GAMMA",
        default=(1.0, 0.0, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color5 = bpy.props.FloatVectorProperty(
        name="Vert Color 5",
        subtype="COLOR_GAMMA",
        default=(0.0, 1.0, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color6 = bpy.props.FloatVectorProperty(
        name="Vert Color 6",
        subtype="COLOR_GAMMA",
        default=(1.0, 0.0, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.sollumz_vpaint_settings = bpy.props.PointerProperty(
        type=SollumzVertexPainterProperties)

    bpy.types.Scene.vert_paint_alpha = bpy.props.FloatProperty(
        name="Alpha", min=-1, max=1)


def unregister():
    del bpy.types.Scene.vert_paint_color1
    del bpy.types.Scene.vert_paint_color2
    del bpy.types.Scene.vert_paint_color3
    del bpy.types.Scene.vert_paint_color4
    del bpy.types.Scene.vert_paint_color5
    del bpy.types.Scene.vert_paint_color6
    del bpy.types.Scene.sollumz_vpaint_settings
    del bpy.types.Scene.vert_paint_alpha
