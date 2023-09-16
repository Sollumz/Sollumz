import bpy
import os
from typing import Optional
from ..tools.blenderhelper import lod_level_enum_flag_prop_factory
from ..sollumz_helper import find_sollumz_parent
from ..sollumz_properties import SOLLUMZ_UI_NAMES, items_from_enums, TextureUsage, TextureFormat, LODLevel, SollumType, LightType, FlagPropertyGroup, TimeFlags
from ..ydr.shader_materials import shadermats
from bpy.app.handlers import persistent
from bpy.path import basename


class ShaderOrderItem(bpy.types.PropertyGroup):
    # For drawable shader order list
    index: bpy.props.IntProperty(min=0)
    name: bpy.props.StringProperty()
    filename: bpy.props.StringProperty()


class DrawableShaderOrder(bpy.types.PropertyGroup):
    items: bpy.props.CollectionProperty(type=ShaderOrderItem)
    active_index: bpy.props.IntProperty(min=0)

    def get_active_shader_item_index(self) -> int:
        return self.items[self.active_index].index

    def change_shader_index(self, old: int, new: int):
        if new >= len(self.items):
            return

        list_ind = self.active_index

        for i, item in enumerate(self.items):
            if item.index == new:
                item.index = old
            elif item.index == old:
                item.index = new
                list_ind = i

        self.active_index = list_ind


class DrawableProperties(bpy.types.PropertyGroup):
    lod_dist_high: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance High")
    lod_dist_med: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Med")
    lod_dist_low: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Low")
    lod_dist_vlow: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Vlow")
    unknown_9A: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Unknown 9A")

    shader_order: bpy.props.PointerProperty(type=DrawableShaderOrder)


class DrawableModelProperties(bpy.types.PropertyGroup):
    render_mask: bpy.props.IntProperty(name="Render Mask", default=255)
    flags: bpy.props.IntProperty(name="Flags", default=0)
    unknown_1: bpy.props.IntProperty(name="Unknown 1", default=0)
    sollum_lod: bpy.props.EnumProperty(
        items=items_from_enums(
            [LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW]),
        name="LOD Level",
        default="sollumz_high"
    )


class SkinnedDrawableModelProperties(bpy.types.PropertyGroup):
    very_high: bpy.props.PointerProperty(type=DrawableModelProperties)
    high: bpy.props.PointerProperty(type=DrawableModelProperties)
    medium: bpy.props.PointerProperty(type=DrawableModelProperties)
    low: bpy.props.PointerProperty(type=DrawableModelProperties)
    very_low: bpy.props.PointerProperty(type=DrawableModelProperties)

    def get_lod(self, lod_level: LODLevel) -> DrawableModelProperties:
        if lod_level == LODLevel.VERYHIGH:
            return self.very_high
        elif lod_level == LODLevel.HIGH:
            return self.high
        elif lod_level == LODLevel.MEDIUM:
            return self.medium
        elif lod_level == LODLevel.LOW:
            return self.low
        elif lod_level == LODLevel.VERYLOW:
            return self.very_low


class ShaderProperties(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty(min=0)

    renderbucket: bpy.props.IntProperty(name="Render Bucket", default=0)
    filename: bpy.props.StringProperty(
        name="Shader Filename", default="default.sps")
    name: bpy.props.StringProperty(name="Shader Name", default="default")


class TextureFlags(bpy.types.PropertyGroup):
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
    usage: bpy.props.EnumProperty(
        items=items_from_enums(TextureUsage),
        name="Usage",
        default=TextureUsage.UNKNOWN
    )

    format: bpy.props.EnumProperty(
        items=items_from_enums(TextureFormat),
        name="Format",
        default=TextureFormat.DXT1
    )

    extra_flags: bpy.props.IntProperty(name="Extra Flags", default=0)


class BoneFlag(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(default="")


class BoneProperties(bpy.types.PropertyGroup):
    @staticmethod
    def calc_tag_hash(bone_name: str) -> int:
        h = 0
        for char in str.upper(bone_name):
            char = ord(char)
            h = (h << 4) + char
            x = h & 0xF0000000

            if x != 0:
                h ^= x >> 24

            h &= ~x

        return h % 0xFE8F + 0x170

    def get_bone(self) -> Optional[bpy.types.Bone]:
        armature: bpy.types.Armature = self.id_data
        if armature is None or not isinstance(armature, bpy.types.Armature):
            return None

        # no direct way to access the Bone from a PropertyGroup so iterate the armature bones until we find ourselves
        for bone in armature.bones:
            if bone.bone_properties == self:
                return bone
        return None

    def calc_tag(self) -> Optional[int]:
        bone = self.get_bone()
        if bone is None:
            return None

        is_root = bone.parent is None
        tag = 0 if is_root else BoneProperties.calc_tag_hash(bone.name)
        return tag

    def get_tag(self) -> int:
        if self.use_manual_tag:
            return self.manual_tag

        tag = self.calc_tag()
        if tag is None:
            # fallback to manual tag if for some reason we are not in a bone
            tag = self.manual_tag
        return tag

    def set_tag(self, value: int):
        self.manual_tag = value
        self.use_manual_tag = value != self.calc_tag()

    tag: bpy.props.IntProperty(
            name="Tag", description="Unique value that identifies this bone in the armature",
            get=get_tag, set=set_tag, default=0, min=0, max=0xFFFF)
    manual_tag: bpy.props.IntProperty(name="Manual Tag", default=0, min=0, max=0xFFFF)
    use_manual_tag: bpy.props.BoolProperty(
        name="Use Manual Tag", description="Specify a tag instead of auto-calculating it",
        default=False)
    flags: bpy.props.CollectionProperty(type=BoneFlag)
    ul_index: bpy.props.IntProperty(name="UIListIndex", default=0)


class ShaderMaterial(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty("Index")
    name: bpy.props.StringProperty("Name")


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
    volume_intensity: bpy.props.FloatProperty(
        name="Volume Intensity", default=1.0)
    shadow_blur: bpy.props.FloatProperty(name="Shadow Blur")
    volume_size_scale: bpy.props.FloatProperty(
        name="Volume Size Scale", default=1.0)
    volume_outer_color: bpy.props.FloatVectorProperty(
        name="Volume Outer Color", subtype="COLOR", min=0.0, max=1.0, default=(1.0, 1.0, 1.0))
    light_hash: bpy.props.IntProperty(name="Light Hash")
    volume_outer_intensity: bpy.props.FloatProperty(
        name="Volume Outer Intensity", default=1.0)
    corona_size: bpy.props.FloatProperty(name="Corona Size")
    volume_outer_exponent: bpy.props.FloatProperty(
        name="Volume Outer Exponent", default=1.0)
    light_fade_distance: bpy.props.FloatProperty(name="Light Fade Distance")
    shadow_fade_distance: bpy.props.FloatProperty(name="Shadow Fade Distance")
    specular_fade_distance: bpy.props.FloatProperty(
        name="Specular Fade Distance")
    volumetric_fade_distance: bpy.props.FloatProperty(
        name="Volumetric Fade Distance")
    shadow_near_clip: bpy.props.FloatProperty(name="Shadow Near Clip")
    corona_intensity: bpy.props.FloatProperty(
        name="Corona Intensity", default=1.0)
    corona_z_bias: bpy.props.FloatProperty(name="Corona Z Bias", default=0.1)
    tangent: bpy.props.FloatVectorProperty(name="Tangent")
    cone_inner_angle: bpy.props.FloatProperty(name="Cone Inner Angle")
    cone_outer_angle: bpy.props.FloatProperty(name="Cone Outer Angle")
    extent: bpy.props.FloatVectorProperty(
        name="Extent", default=(1, 1, 1), subtype="XYZ")
    projected_texture_hash: bpy.props.StringProperty(
        name="Projected Texture Hash")


class LightFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    unk1: bpy.props.BoolProperty(
        name="Unk1", update=FlagPropertyGroup.update_flag)
    unk2: bpy.props.BoolProperty(
        name="Unk2", update=FlagPropertyGroup.update_flag)
    unk3: bpy.props.BoolProperty(
        name="Unk3", update=FlagPropertyGroup.update_flag)
    unk4: bpy.props.BoolProperty(
        name="Unk4", update=FlagPropertyGroup.update_flag)
    unk5: bpy.props.BoolProperty(
        name="Unk5", update=FlagPropertyGroup.update_flag)
    unk6: bpy.props.BoolProperty(
        name="Unk6", update=FlagPropertyGroup.update_flag)
    unk7: bpy.props.BoolProperty(
        name="Unk7", update=FlagPropertyGroup.update_flag)
    shadows: bpy.props.BoolProperty(
        name="ShadowS", update=FlagPropertyGroup.update_flag)
    shadowd: bpy.props.BoolProperty(
        name="ShadowD", update=FlagPropertyGroup.update_flag)
    sunlight: bpy.props.BoolProperty(
        name="Sunlight", update=FlagPropertyGroup.update_flag)
    unk11: bpy.props.BoolProperty(
        name="Unk11", update=FlagPropertyGroup.update_flag)
    electric: bpy.props.BoolProperty(
        name="Electric", update=FlagPropertyGroup.update_flag)
    volume: bpy.props.BoolProperty(
        name="Volume", update=FlagPropertyGroup.update_flag)
    specoff: bpy.props.BoolProperty(
        name="SpecOff", update=FlagPropertyGroup.update_flag)
    unk15: bpy.props.BoolProperty(
        name="Unk15", update=FlagPropertyGroup.update_flag)
    lightoff: bpy.props.BoolProperty(
        name="LightOff", update=FlagPropertyGroup.update_flag)
    prxoff: bpy.props.BoolProperty(
        name="PrxOff", update=FlagPropertyGroup.update_flag)
    unk18: bpy.props.BoolProperty(
        name="Unk18", update=FlagPropertyGroup.update_flag)
    culling: bpy.props.BoolProperty(
        name="Culling", update=FlagPropertyGroup.update_flag)
    unk20: bpy.props.BoolProperty(
        name="Unk20", update=FlagPropertyGroup.update_flag)
    unk21: bpy.props.BoolProperty(
        name="Unk21", update=FlagPropertyGroup.update_flag)
    unk22: bpy.props.BoolProperty(
        name="Unk22", update=FlagPropertyGroup.update_flag)
    unk23: bpy.props.BoolProperty(
        name="Unk23", update=FlagPropertyGroup.update_flag)
    glassoff: bpy.props.BoolProperty(
        name="GlassOff", update=FlagPropertyGroup.update_flag)
    unk25: bpy.props.BoolProperty(
        name="Unk25", update=FlagPropertyGroup.update_flag)
    unk26: bpy.props.BoolProperty(
        name="Unk26", update=FlagPropertyGroup.update_flag)
    unk27: bpy.props.BoolProperty(
        name="Unk27", update=FlagPropertyGroup.update_flag)
    unk28: bpy.props.BoolProperty(
        name="Unk28", update=FlagPropertyGroup.update_flag)
    unk29: bpy.props.BoolProperty(
        name="Unk29", update=FlagPropertyGroup.update_flag)
    unk30: bpy.props.BoolProperty(
        name="Unk30", update=FlagPropertyGroup.update_flag)
    unk31: bpy.props.BoolProperty(
        name="Unk31", update=FlagPropertyGroup.update_flag)
    unk32: bpy.props.BoolProperty(
        name="Unk32", update=FlagPropertyGroup.update_flag)


@persistent
def on_file_loaded(_):
    # Handler sets the default value of the ShaderMaterials collection on blend file load
    bpy.context.scene.shader_materials.clear()
    for index, mat in enumerate(shadermats):
        item = bpy.context.scene.shader_materials.add()
        item.index = index
        item.name = mat.name


def get_light_type(self):
    if self.type == "POINT":
        return 1 if not self.is_capsule else 3
    elif self.type == "SPOT":
        return 2
    else:
        return 0


def set_light_type(self, value):
    if value == 1:
        self.type = "POINT"
        self.is_capsule = False
    elif value == 3:
        self.type = "POINT"
        self.is_capsule = True
    elif value == 2:
        self.type = "SPOT"
        self.is_capsule = False


def get_texture_name(self):
    if self.image:
        return os.path.splitext(basename(self.image.filepath))[0]
    return "None"


def get_model_properties(model_obj: bpy.types.Object, lod_level: LODLevel) -> DrawableModelProperties:
    drawable_obj = find_sollumz_parent(model_obj, SollumType.DRAWABLE)

    if drawable_obj is not None and model_obj.vertex_groups:
        return drawable_obj.skinned_model_properties.get_lod(lod_level)

    lod = model_obj.sollumz_lods.get_lod(lod_level)

    if lod is None or lod.mesh is None:
        raise ValueError(
            f"Failed to get Drawable Model properties: {model_obj.name} has no {SOLLUMZ_UI_NAMES[lod_level]} LOD!")

    return lod.mesh.drawable_model_properties


def register():
    bpy.types.Scene.shader_material_index = bpy.props.IntProperty(
        name="Shader Material Index")  # MAKE ENUM WITH THE MATERIALS NAMES
    bpy.types.Scene.shader_materials = bpy.props.CollectionProperty(
        type=ShaderMaterial, name="Shader Materials")
    bpy.app.handlers.load_post.append(on_file_loaded)
    bpy.types.Object.drawable_properties = bpy.props.PointerProperty(
        type=DrawableProperties)
    bpy.types.Material.shader_properties = bpy.props.PointerProperty(
        type=ShaderProperties)
    bpy.types.ShaderNodeTexImage.texture_properties = bpy.props.PointerProperty(
        type=TextureProperties)
    bpy.types.ShaderNodeTexImage.texture_flags = bpy.props.PointerProperty(
        type=TextureFlags)
    bpy.types.ShaderNodeTexImage.sollumz_texture_name = bpy.props.StringProperty(
        name="Texture Name", description="Name of texture.", get=get_texture_name)

    # Store properties for the DrawableModel with HasSkin=1. This is so all skinned objects share
    # the same drawable model properties even when split by group. It seems there is only ever 1
    # DrawableModel with HasSkin=1 in any given Drawable.
    bpy.types.Object.skinned_model_properties = bpy.props.PointerProperty(
        type=SkinnedDrawableModelProperties)
    # DrawableModel properties stored per mesh for LOD system
    bpy.types.Mesh.drawable_model_properties = bpy.props.PointerProperty(
        type=DrawableModelProperties)
    # For backwards compatibility
    bpy.types.Object.drawable_model_properties = bpy.props.PointerProperty(
        type=DrawableModelProperties)

    bpy.types.Scene.create_seperate_drawables = bpy.props.BoolProperty(
        name="Separate Objects", description="Create a separate Drawable for each selected object")
    bpy.types.Scene.auto_create_embedded_col = bpy.props.BoolProperty(
        name="Auto-Embed Collision", description="Automatically create embedded static collision")
    bpy.types.Scene.center_drawable_to_selection = bpy.props.BoolProperty(
        name="Center to Selection", description="Center Drawable(s) to selection", default=True)

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
    bpy.types.Light.time_flags = bpy.props.PointerProperty(type=TimeFlags)
    bpy.types.Light.light_flags = bpy.props.PointerProperty(type=LightFlags)

    bpy.types.Scene.sollumz_auto_lod_ref_mesh = bpy.props.PointerProperty(
        type=bpy.types.Mesh, name="Reference Mesh", description="The mesh to copy and decimate for each LOD level. You'd usually want to set this as the highest LOD then run the tool for all lower LODs")
    bpy.types.Scene.sollumz_auto_lod_levels = lod_level_enum_flag_prop_factory()
    bpy.types.Scene.sollumz_auto_lod_decimate_step = bpy.props.FloatProperty(
        name="Decimate Step", min=0.0, max=0.99, default=0.6)

    bpy.types.Scene.sollumz_extract_lods_levels = lod_level_enum_flag_prop_factory()
    bpy.types.Scene.sollumz_extract_lods_parent_type = bpy.props.EnumProperty(name="Parent Type", items=(
        ("sollumz_extract_lods_parent_type_object", "Object", "Parent to an Object"),
        ("sollumz_extract_lods_parent_type_collection",
         "Collection", "Parent to a Collection")
    ), default=0)


def unregister():
    del bpy.types.ShaderNodeTexImage.sollumz_texture_name
    del bpy.types.Scene.shader_material_index
    del bpy.types.Scene.shader_materials
    del bpy.types.Object.drawable_properties
    del bpy.types.Mesh.drawable_model_properties
    del bpy.types.Object.skinned_model_properties
    del bpy.types.Material.shader_properties
    del bpy.types.ShaderNodeTexImage.texture_properties
    del bpy.types.ShaderNodeTexImage.texture_flags
    del bpy.types.Bone.bone_properties
    del bpy.types.Light.light_properties
    del bpy.types.Scene.create_light_type
    del bpy.types.Light.time_flags
    del bpy.types.Light.light_flags
    del bpy.types.Light.is_capsule
    del bpy.types.Scene.create_seperate_drawables
    del bpy.types.Scene.auto_create_embedded_col
    del bpy.types.Scene.center_drawable_to_selection
    del bpy.types.Scene.sollumz_auto_lod_ref_mesh
    del bpy.types.Scene.sollumz_auto_lod_levels
    del bpy.types.Scene.sollumz_auto_lod_decimate_step
    del bpy.types.Scene.sollumz_extract_lods_levels
    del bpy.types.Scene.sollumz_extract_lods_parent_type

    bpy.app.handlers.load_post.remove(on_file_loaded)
