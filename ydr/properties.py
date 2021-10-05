import bpy
from Sollumz.sollumz_properties import items_from_enums, TextureType, TextureFormat, LodType

class DrawableProperties(bpy.types.PropertyGroup):
    lod_dist_high : bpy.props.FloatProperty(min = 0, max = 10000, default = 9998, name = "Lod Distance High")
    lod_dist_med : bpy.props.FloatProperty(min = 0, max = 10000, default = 9998, name = "Lod Distance Med")
    lod_dist_low : bpy.props.FloatProperty(min = 0, max = 10000, default = 9998, name = "Lod Distance Low")
    lod_dist_vlow : bpy.props.FloatProperty(min = 0, max = 10000, default = 9998, name = "Lod Distance Vlow")


class GeometryProperties(bpy.types.PropertyGroup):
    sollum_lod : bpy.props.EnumProperty(
        items = items_from_enums(LodType),
        name = "LOD",
        default = LodType.HIGH
    )

class ShaderProperties(bpy.types.PropertyGroup):
    renderbucket : bpy.props.IntProperty(name = "Render Bucket", default = 0)
    #????????? DONT KNOW IF I WANNA DO THIS
    #filename : bpy.props.EnumProperty(
    #    items = [("sollumz_none", "None", "Sollumz None")
    #            ],
    #    name = "FileName",
    #    default = "sollumz_none"
    #)
    #LAYOUT ENUM? 
    filename : bpy.props.StringProperty(name = "FileName", default = "default")

class TextureFlags(bpy.types.PropertyGroup):
    #usage flags 
    not_half : bpy.props.BoolProperty(name = "NOT_HALF", default = False)
    hd_split : bpy.props.BoolProperty(name = "HD_SPLIT", default = False)
    x2 : bpy.props.BoolProperty(name = "X2", default = False)
    x4 : bpy.props.BoolProperty(name = "X4", default = False)
    y4 : bpy.props.BoolProperty(name = "Y4", default = False)
    x8 : bpy.props.BoolProperty(name = "X8", default = False)
    x16 : bpy.props.BoolProperty(name = "X16", default = False)
    x32 : bpy.props.BoolProperty(name = "X32", default = False)
    x64 : bpy.props.BoolProperty(name = "X64", default = False)
    y64 : bpy.props.BoolProperty(name = "Y64", default = False)
    x128 : bpy.props.BoolProperty(name = "X128", default = False)
    x256 : bpy.props.BoolProperty(name = "X256", default = False)
    x512 : bpy.props.BoolProperty(name = "X512", default = False)
    y512 : bpy.props.BoolProperty(name = "Y512", default = False)
    x1024 : bpy.props.BoolProperty(name = "X1024", default = False)
    y1024 : bpy.props.BoolProperty(name = "Y1024", default = False)
    x2048 : bpy.props.BoolProperty(name = "X2048", default = False)
    y2048 : bpy.props.BoolProperty(name = "Y2048", default = False)
    embeddedscriptrt : bpy.props.BoolProperty(name = "EMBEDDEDSCRIPTRT", default = False)
    unk19 : bpy.props.BoolProperty(name = "UNK19", default = False)
    unk20 : bpy.props.BoolProperty(name = "UNK20", default = False)
    unk21 : bpy.props.BoolProperty(name = "UNK21", default = False)
    flag_full : bpy.props.BoolProperty(name = "FLAG_FULL", default = False)
    maps_half : bpy.props.BoolProperty(name = "MAPS_HALF", default = False)
    unk24 : bpy.props.BoolProperty(name = "UNK24", default = False)


class TextureProperties(TextureFlags, bpy.types.PropertyGroup):
    embedded : bpy.props.BoolProperty(name = "Embedded", default = False)
    ########################## CHECK CW TO SEE IF THIS IS TRUE ##########################
    usage : bpy.props.EnumProperty(
        items = items_from_enums(TextureType),
        name = "Usage",
        default = TextureType.DIFFUSE
    )

    ########################## CHECK CW TO SEE IF THIS IS TRUE ##########################
    format : bpy.props.EnumProperty(
        items = items_from_enums(TextureFormat),
        name = "Format",
        default = TextureFormat.DXT1
    )

    extra_flags : bpy.props.IntProperty(name = "Extra Flags", default = 0)


def register():
    bpy.types.Object.drawable_properties = bpy.props.PointerProperty(type = DrawableProperties)
    bpy.types.Object.geometry_properties = bpy.props.PointerProperty(type = GeometryProperties)
    bpy.types.Material.shader_properties = bpy.props.PointerProperty(type = ShaderProperties)
    bpy.types.ShaderNodeTexImage.texture_properties = bpy.props.PointerProperty(type = TextureProperties)

def unregister():
    del bpy.types.Object.drawable_properties
    del bpy.types.Object.geometry_properties
    del bpy.types.Material.shader_properties
    del bpy.types.ShaderNodeTexImage.texture_properties