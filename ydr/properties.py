import bpy
from ..sollumz_properties import SOLLUMZ_UI_NAMES, items_from_enums, TextureUsage, TextureFormat, LODLevel, SollumType, LightType
from ..ydr.shader_materials import shadermats, ShaderMaterial
from bpy.app.handlers import persistent


class DrawableProperties(bpy.types.PropertyGroup):
    lod_dist_high: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance High")
    lod_dist_med: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Med")
    lod_dist_low: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Low")
    lod_dist_vlow: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Vlow")


class DrawableModelProperties(bpy.types.PropertyGroup):
    render_mask: bpy.props.IntProperty(name="Render Mask", default=255)
    flags: bpy.props.IntProperty(name="Flags", default=0)
    sollum_lod: bpy.props.EnumProperty(
        items=items_from_enums(LODLevel),
        name="LOD Level",
        default="sollumz_high"
    )


class ShaderProperties(bpy.types.PropertyGroup):
    renderbucket: bpy.props.IntProperty(name="Render Bucket", default=0)
    filename: bpy.props.StringProperty(
        name="Shader Filename", default="default.sps")
    name: bpy.props.StringProperty(name="Shader Name", default="default")


class TextureFlags(bpy.types.PropertyGroup):
    # usage flags
    not_half: bpy.props.BoolProperty(name="NOT_HALF", default=False)
    hd_split: bpy.props.BoolProperty(name="HD_SPLIT", default=False)
    x2: bpy.props.BoolProperty(name="X2", default=False)
    x4: bpy.props.BoolProperty(name="X4", default=False)
    y4: bpy.props.BoolProperty(name="Y4", default=False)
    x8: bpy.props.BoolProperty(name="X8", default=False)
    x16: bpy.props.BoolProperty(name="X16", default=False)
    x32: bpy.props.BoolProperty(name="X32", default=False)
    x64: bpy.props.BoolProperty(name="X64", default=False)
    y64: bpy.props.BoolProperty(name="Y64", default=False)
    x128: bpy.props.BoolProperty(name="X128", default=False)
    x256: bpy.props.BoolProperty(name="X256", default=False)
    x512: bpy.props.BoolProperty(name="X512", default=False)
    y512: bpy.props.BoolProperty(name="Y512", default=False)
    x1024: bpy.props.BoolProperty(name="X1024", default=False)
    y1024: bpy.props.BoolProperty(name="Y1024", default=False)
    x2048: bpy.props.BoolProperty(name="X2048", default=False)
    y2048: bpy.props.BoolProperty(name="Y2048", default=False)
    embeddedscriptrt: bpy.props.BoolProperty(
        name="EMBEDDEDSCRIPTRT", default=False)
    unk19: bpy.props.BoolProperty(name="UNK19", default=False)
    unk20: bpy.props.BoolProperty(name="UNK20", default=False)
    unk21: bpy.props.BoolProperty(name="UNK21", default=False)
    flag_full: bpy.props.BoolProperty(name="FLAG_FULL", default=False)
    maps_half: bpy.props.BoolProperty(name="MAPS_HALF", default=False)
    unk24: bpy.props.BoolProperty(name="UNK24", default=False)


class TextureProperties(bpy.types.PropertyGroup):
    embedded: bpy.props.BoolProperty(name="Embedded", default=False)
    ########################## CHECK CW TO SEE IF THIS IS TRUE ##########################
    usage: bpy.props.EnumProperty(
        items=items_from_enums(TextureUsage),
        name="Usage",
        default=TextureUsage.DIFFUSE
    )

    ########################## CHECK CW TO SEE IF THIS IS TRUE ##########################
    format: bpy.props.EnumProperty(
        items=items_from_enums(TextureFormat),
        name="Format",
        default=TextureFormat.DXT1
    )

    extra_flags: bpy.props.IntProperty(name="Extra Flags", default=0)


class BoneFlag(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default="")


class BoneProperties(bpy.types.PropertyGroup):
    tag: bpy.props.IntProperty(name="BoneTag", default=0, min=0)
    flags: bpy.props.CollectionProperty(type=BoneFlag)
    ul_index: bpy.props.IntProperty(name="UIListIndex", default=0)


class ShaderMaterial(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty('Index')
    name: bpy.props.StringProperty('Name')


class LightProperties(bpy.types.PropertyGroup):
    flashiness: bpy.props.IntProperty(name="Flashiness")
    group_id: bpy.props.IntProperty(name="Group ID")
    falloff: bpy.props.FloatProperty(name="Falloff")
    falloff_exponent: bpy.props.FloatProperty(name="Falloff Exponent")
    culling_plane_normal: bpy.props.FloatVectorProperty(
        name="Culling Plane Normal")
    culling_plane_offset: bpy.props.FloatProperty(name="Culling Plane Offset")
    unknown_45: bpy.props.FloatProperty(name="Unknown 45")
    unknown_46: bpy.props.FloatProperty(name="Unknown 46")
    volume_intensity: bpy.props.FloatProperty(name="Volume Intensity")
    volume_size_scale: bpy.props.FloatProperty(name="Volume Size Scale")
    volume_outer_color: bpy.props.FloatVectorProperty(
        name="Volume Outer Color", subtype='COLOR')
    light_hash: bpy.props.IntProperty(name="Light Hash")
    volume_outer_intensity: bpy.props.FloatProperty(
        name="Volume Outer Intensity")
    corona_size: bpy.props.FloatProperty(name="Corona Size")
    volume_outer_exponent: bpy.props.FloatProperty(
        name="Volume Outer Exponent")
    light_fade_distance: bpy.props.FloatProperty(name="Light Fade Distance")
    shadow_fade_distance: bpy.props.FloatProperty(name="Shadow Fade Distance")
    specular_fade_distance: bpy.props.FloatProperty(
        name="Specular Fade Distance")
    volumetric_fade_distance: bpy.props.FloatProperty(
        name="Volumetric Fade Distance")
    shadow_near_clip: bpy.props.FloatProperty(name="Shadow Near Clip")
    corona_intensity: bpy.props.FloatProperty(name="Corona Intensity")
    corona_z_bias: bpy.props.FloatProperty(name="Corona Z Bias")
    tangent: bpy.props.FloatVectorProperty(name="Tangent")
    cone_inner_angle: bpy.props.FloatProperty(name="Cone Inner Angle")
    cone_outer_angle: bpy.props.FloatProperty(name="Cone Outer Angle")
    extent: bpy.props.FloatVectorProperty(
        name="Extent", default=(1, 1, 1), subtype="XYZ")
    projected_texture_hash: bpy.props.StringProperty(
        name="Projected Texture Hash")


class LightTimeFlags(bpy.types.PropertyGroup):
    hour1: bpy.props.BoolProperty(name="12:00 AM - 1:00 AM")
    hour2: bpy.props.BoolProperty(name="1:00 AM - 2:00 AM")
    hour3: bpy.props.BoolProperty(name="2:00 AM - 3:00 AM")
    hour4: bpy.props.BoolProperty(name="3:00 AM - 4:00 AM")
    hour5: bpy.props.BoolProperty(name="4:00 AM - 5:00 AM")
    hour6: bpy.props.BoolProperty(name="5:00 AM - 6:00 AM")
    hour7: bpy.props.BoolProperty(name="6:00 AM - 7:00 AM")
    hour8: bpy.props.BoolProperty(name="7:00 AM - 8:00 AM")
    hour9: bpy.props.BoolProperty(name="8:00 AM - 9:00 AM")
    hour10: bpy.props.BoolProperty(name="9:00 AM - 10:00 AM")
    hour11: bpy.props.BoolProperty(name="10:00 AM - 11:00 AM")
    hour12: bpy.props.BoolProperty(name="11:00 AM - 12:00 PM")
    hour13: bpy.props.BoolProperty(name="12:00 PM - 1:00 PM")
    hour14: bpy.props.BoolProperty(name="1:00 PM - 2:00 PM")
    hour15: bpy.props.BoolProperty(name="2:00 PM - 3:00 PM")
    hour16: bpy.props.BoolProperty(name="3:00 PM - 4:00 PM")
    hour17: bpy.props.BoolProperty(name="4:00 PM - 5:00 PM")
    hour18: bpy.props.BoolProperty(name="5:00 PM - 6:00 PM")
    hour19: bpy.props.BoolProperty(name="6:00 PM - 7:00 PM")
    hour20: bpy.props.BoolProperty(name="7:00 PM - 8:00 PM")
    hour21: bpy.props.BoolProperty(name="8:00 PM - 9:00 PM")
    hour22: bpy.props.BoolProperty(name="9:00 PM - 10:00 PM")
    hour23: bpy.props.BoolProperty(name="10:00 PM - 11:00 PM")
    hour24: bpy.props.BoolProperty(name="11:00 PM - 12:00 AM")
    unk1: bpy.props.BoolProperty(name="Unk1")
    unk2: bpy.props.BoolProperty(name="Unk2")
    unk3: bpy.props.BoolProperty(name="Unk3")
    unk4: bpy.props.BoolProperty(name="Unk4")
    unk5: bpy.props.BoolProperty(name="Unk5")
    unk6: bpy.props.BoolProperty(name="Unk6")
    unk7: bpy.props.BoolProperty(name="Unk7")
    unk8: bpy.props.BoolProperty(name="Unk8")


class LightFlags(bpy.types.PropertyGroup):
    unk1: bpy.props.BoolProperty(name="Unk1")
    unk2: bpy.props.BoolProperty(name="Unk2")
    unk3: bpy.props.BoolProperty(name="Unk3")
    unk4: bpy.props.BoolProperty(name="Unk4")
    unk5: bpy.props.BoolProperty(name="Unk5")
    unk6: bpy.props.BoolProperty(name="Unk6")
    unk7: bpy.props.BoolProperty(name="Unk7")
    shadows: bpy.props.BoolProperty(name="ShadowS")
    shadowd: bpy.props.BoolProperty(name="ShadowD")
    sunlight: bpy.props.BoolProperty(name="Sunlight")
    unk11: bpy.props.BoolProperty(name="Unk11")
    electric: bpy.props.BoolProperty(name="Electric")
    volume: bpy.props.BoolProperty(name="Volume")
    specoff: bpy.props.BoolProperty(name="SpecOff")
    unk15: bpy.props.BoolProperty(name="Unk15")
    lightoff: bpy.props.BoolProperty(name="LightOff")
    prxoff: bpy.props.BoolProperty(name="PrxOff")
    unk18: bpy.props.BoolProperty(name="Unk18")
    culling: bpy.props.BoolProperty(name="Culling")
    unk20: bpy.props.BoolProperty(name="Unk20")
    unk21: bpy.props.BoolProperty(name="Unk21")
    unk22: bpy.props.BoolProperty(name="Unk22")
    unk23: bpy.props.BoolProperty(name="Unk23")
    glassoff: bpy.props.BoolProperty(name="GlassOff")
    unk25: bpy.props.BoolProperty(name="Unk25")
    unk26: bpy.props.BoolProperty(name="Unk26")
    unk27: bpy.props.BoolProperty(name="Unk27")
    unk28: bpy.props.BoolProperty(name="Unk28")
    unk29: bpy.props.BoolProperty(name="Unk29")
    unk30: bpy.props.BoolProperty(name="Unk30")
    unk31: bpy.props.BoolProperty(name="Unk31")
    unk32: bpy.props.BoolProperty(name="Unk32")

# Handler sets the default value of the ShaderMaterials collection on blend file load


@persistent
def on_file_loaded(_):
    bpy.context.scene.shader_materials.clear()
    for index, mat in enumerate(shadermats):
        item = bpy.context.scene.shader_materials.add()
        item.index = index
        item.name = mat.name


def get_light_type(self):
    if self.type == 'POINT':
        return 1 if not self.is_capsule else 3
    elif self.type == 'SPOT':
        return 2
    else:
        return 0


def set_light_type(self, value):
    if value == 1:
        self.type = 'POINT'
        self.is_capsule = False
    elif value == 3:
        self.type = 'POINT'
        self.is_capsule = True
    elif value == 2:
        self.type = 'SPOT'
        self.is_capsule = False


time_items = [("0", "12:00 AM", ""),
              ("1", "1:00 AM", ""),
              ("2", "2:00 AM", ""),
              ("3", "3:00 AM", ""),
              ("4", "4:00 AM", ""),
              ("5", "5:00 AM", ""),
              ("6", "6:00 AM", ""),
              ("7", "7:00 AM", ""),
              ("8", "8:00 AM", ""),
              ("9", "9:00 AM", ""),
              ("10", "10:00 AM", ""),
              ("11", "11:00 AM", ""),
              ("12", "12:00 PM", ""),
              ("13", "1:00 PM", ""),
              ("14", "2:00 PM", ""),
              ("15", "3:00 PM", ""),
              ("16", "4:00 PM", ""),
              ("17", "5:00 PM", ""),
              ("18", "6:00 PM", ""),
              ("19", "7:00 PM", ""),
              ("20", "8:00 PM", ""),
              ("21", "9:00 PM", ""),
              ("22", "10:00 PM", ""),
              ("23", "11:00 PM", "")]


def register():
    bpy.types.Scene.shader_material_index = bpy.props.IntProperty(
        name="Shader Material Index")  # MAKE ENUM WITH THE MATERIALS NAMES
    bpy.types.Scene.shader_materials = bpy.props.CollectionProperty(
        type=ShaderMaterial, name='Shader Materials')
    bpy.app.handlers.load_post.append(on_file_loaded)
    bpy.types.Object.drawable_properties = bpy.props.PointerProperty(
        type=DrawableProperties)
    bpy.types.Object.drawable_model_properties = bpy.props.PointerProperty(
        type=DrawableModelProperties)
    bpy.types.Material.shader_properties = bpy.props.PointerProperty(
        type=ShaderProperties)
    bpy.types.ShaderNodeTexImage.texture_properties = bpy.props.PointerProperty(
        type=TextureProperties)
    bpy.types.ShaderNodeTexImage.texture_flags = bpy.props.PointerProperty(
        type=TextureFlags)
    bpy.types.Bone.bone_properties = bpy.props.PointerProperty(
        type=BoneProperties)
    bpy.types.Light.sollum_type = bpy.props.EnumProperty(
        items=items_from_enums(LightType),
        name="Light Type",
        default=LightType.POINT,
        options={"HIDDEN"},
        get=get_light_type,
        set=set_light_type
    )
    bpy.types.Light.is_capsule = bpy.props.BoolProperty()
    bpy.types.Light.light_properties = bpy.props.PointerProperty(
        type=LightProperties)
    bpy.types.Scene.create_light_type = bpy.props.EnumProperty(
        items=[
            (LightType.POINT.value,
             SOLLUMZ_UI_NAMES[LightType.POINT], SOLLUMZ_UI_NAMES[LightType.POINT]),
            (LightType.SPOT.value,
             SOLLUMZ_UI_NAMES[LightType.SPOT], SOLLUMZ_UI_NAMES[LightType.SPOT]),
            (LightType.CAPSULE.value,
             SOLLUMZ_UI_NAMES[LightType.CAPSULE], SOLLUMZ_UI_NAMES[LightType.CAPSULE]),
        ],
        name="Light Type",
        default=LightType.POINT,
        options={"HIDDEN"}
    )
    bpy.types.Light.time_flags = bpy.props.PointerProperty(type=LightTimeFlags)
    bpy.types.Light.time_flags_start = bpy.props.EnumProperty(
        items=time_items, name="Time Start")
    bpy.types.Light.time_flags_end = bpy.props.EnumProperty(
        items=time_items, name="Time End")
    bpy.types.Light.light_flags = bpy.props.PointerProperty(type=LightFlags)


def unregister():
    del bpy.types.Scene.shader_material_index
    del bpy.types.Scene.shader_materials
    del bpy.types.Object.drawable_properties
    del bpy.types.Object.drawable_model_properties
    del bpy.types.Material.shader_properties
    del bpy.types.ShaderNodeTexImage.texture_properties
    del bpy.types.ShaderNodeTexImage.texture_flags
    del bpy.types.Bone.bone_properties
    del bpy.types.Light.light_properties
    del bpy.types.Scene.create_light_type
    del bpy.types.Light.time_flags
    del bpy.types.Light.time_flags_start
    del bpy.types.Light.time_flags_end
    del bpy.types.Light.light_flags
    del bpy.types.Light.is_capsule

    bpy.app.handlers.load_post.remove(on_file_loaded)
