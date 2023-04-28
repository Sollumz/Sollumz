import bpy

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

    active_channels: bpy.props.EnumProperty(
        name="Active Channels",
        options={'ENUM_FLAG'},
        items=channel_items,
        description="Which channels to enable.",
        default={'R', 'G', 'B'},
        update=update_active_channels
    )
    # Used only to store the color between RGBA and isolate modes
    brush_color: bpy.props.FloatVectorProperty(
        name="Brush Color",
        description="Brush primary color.",
        default=(1, 0, 0)
    )
    src_channel_id: bpy.props.EnumProperty(
        name="Source Channel",
        items=channel_items,
        # default=red_id,
        description="Source (Src) color channel."
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