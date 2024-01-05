import bpy
import os
from typing import Optional
from ..tools.blenderhelper import lod_level_enum_flag_prop_factory
from ..sollumz_helper import find_sollumz_parent
from ..cwxml.light_preset import LightPresetsFile
from ..sollumz_properties import SOLLUMZ_UI_NAMES, items_from_enums, TextureUsage, TextureFormat, LODLevel, SollumType, LightType, FlagPropertyGroup, TimeFlags
from ..ydr.shader_materials import shadermats
from .render_bucket import RenderBucket, RenderBucketEnumItems
from .light_flashiness import Flashiness, LightFlashinessEnumItems
from bpy.app.handlers import persistent
from bpy.path import basename


class ShaderOrderItem(bpy.types.PropertyGroup):
    """Represents an item in the shader order list."""
    
    index: bpy.props.IntProperty(min=0)
    name: bpy.props.StringProperty()
    filename: bpy.props.StringProperty()


class DrawableShaderOrder(bpy.types.PropertyGroup):
    """
    Represents the order of drawable shaders.
    """

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
    """
    Represents the properties of a drawable object.
    """

    lod_dist_high: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance High")
    lod_dist_med: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Med")
    lod_dist_low: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Low")
    lod_dist_vlow: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Vlow")

    shader_order: bpy.props.PointerProperty(type=DrawableShaderOrder)


class DrawableModelProperties(bpy.types.PropertyGroup):
    """
    Represents the properties of a drawable model.
    """
    render_mask: bpy.props.IntProperty(name="Render Mask", default=255)
    flags: bpy.props.IntProperty(name="Flags", default=0)
    matrix_count: bpy.props.IntProperty(name="Matrix Count", default=0)
    sollum_lod: bpy.props.EnumProperty(
        items=items_from_enums(
            [LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW]),
        name="LOD Level",
        default="sollumz_high"
    )


class SkinnedDrawableModelProperties(bpy.types.PropertyGroup):
    """
    Represents the properties of a skinned drawable model.
    """

    very_high: bpy.props.PointerProperty(type=DrawableModelProperties)
    high: bpy.props.PointerProperty(type=DrawableModelProperties)
    medium: bpy.props.PointerProperty(type=DrawableModelProperties)
    low: bpy.props.PointerProperty(type=DrawableModelProperties)
    very_low: bpy.props.PointerProperty(type=DrawableModelProperties)

    def get_lod(self, lod_level: LODLevel) -> DrawableModelProperties:
        """
        Retrieves the drawable model properties for the specified LOD level.

        Parameters:
            lod_level (LODLevel): The LOD level.

        Returns:
            DrawableModelProperties: The drawable model properties for the specified LOD level.
        """
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
    """A class representing the properties of a shader."""
    
    index: bpy.props.IntProperty(min=0)

    renderbucket: bpy.props.EnumProperty(
        name="Render Bucket", items=RenderBucketEnumItems,
        default=RenderBucket.OPAQUE.name
    )
    filename: bpy.props.StringProperty(
        name="Shader Filename", default="default.sps")
    name: bpy.props.StringProperty(name="Shader Name", default="default")


class TextureFlags(bpy.types.PropertyGroup):
    """
    represents the texture flags.
    """
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
    """Represents the properties of a texture."""
    
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
    """Represents a bone flag."""
    name: bpy.props.StringProperty(default="")


class BoneProperties(bpy.types.PropertyGroup):
    """A class representing the properties of a bone in an armature.

    This class provides methods for calculating a unique tag for the bone,
    retrieving the bone object from the armature, and setting and getting the tag value.
    """

    @staticmethod
    def calc_tag_hash(bone_name: str) -> int:
        """Calculate the tag hash for a given bone name.

        Parameters:
            bone_name (str): The name of the bone.

        Returns:
            int: The calculated tag hash.
        """
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
        """Get the bone object associated with this BoneProperties.

        Returns:
            Optional[bpy.types.Bone]: The bone object, or None if not found.
        """
        armature: bpy.types.Armature = self.id_data
        if armature is None or not isinstance(armature, bpy.types.Armature):
            return None

        # no direct way to access the Bone from a PropertyGroup so iterate the armature bones until we find ourselves
        for bone in armature.bones:
            if bone.bone_properties == self:
                return bone
        return None

    def calc_tag(self) -> Optional[int]:
        """Calculate the tag for the associated bone.

        Returns:
            Optional[int]: The calculated tag, or None if the bone is not found.
        """
        bone = self.get_bone()
        if bone is None:
            return None

        is_root = bone.parent is None
        tag = 0 if is_root else BoneProperties.calc_tag_hash(bone.name)
        return tag

    def get_tag(self) -> int:
        """Get the tag value for the bone.

        Returns:
            int: The tag value.
        """
        if self.use_manual_tag:
            return self.manual_tag

        tag = self.calc_tag()
        if tag is None:
            # fallback to manual tag if for some reason we are not in a bone
            tag = self.manual_tag
        return tag

    def set_tag(self, value: int):
        """Set the tag value for the bone.

        Parameters:
            value (int): The tag value to set.
        """
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
    """Represents a shader material."""
    
    index: bpy.props.IntProperty("Index")
    name: bpy.props.StringProperty("Name")


class LightProperties(bpy.types.PropertyGroup):
    """
    Represents the properties of a Sollumz light.
    """

    flashiness: bpy.props.EnumProperty(
        name="Flashiness",
        items=LightFlashinessEnumItems,
        default=Flashiness.CONSTANT.name
    )
    group_id: bpy.props.IntProperty(name="Group ID")
    falloff: bpy.props.FloatProperty(name="Falloff")
    falloff_exponent: bpy.props.FloatProperty(name="Falloff Exponent")
    culling_plane_normal: bpy.props.FloatVectorProperty(name="Culling Plane Normal")
    culling_plane_offset: bpy.props.FloatProperty(name="Culling Plane Offset")
    volume_intensity: bpy.props.FloatProperty(name="Volume Intensity", default=1.0)
    shadow_blur: bpy.props.FloatProperty(name="Shadow Blur")
    volume_size_scale: bpy.props.FloatProperty(name="Volume Size Scale", default=1.0)
    volume_outer_color: bpy.props.FloatVectorProperty(
        name="Volume Outer Color",
        subtype="COLOR",
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0)
    )
    light_hash: bpy.props.IntProperty(name="Light Hash")
    volume_outer_intensity: bpy.props.FloatProperty(name="Volume Outer Intensity", default=1.0)
    corona_size: bpy.props.FloatProperty(name="Corona Size")
    volume_outer_exponent: bpy.props.FloatProperty(name="Volume Outer Exponent", default=1.0)
    light_fade_distance: bpy.props.FloatProperty(name="Light Fade Distance")
    shadow_fade_distance: bpy.props.FloatProperty(name="Shadow Fade Distance")
    specular_fade_distance: bpy.props.FloatProperty(name="Specular Fade Distance")
    volumetric_fade_distance: bpy.props.FloatProperty(name="Volumetric Fade Distance")
    shadow_near_clip: bpy.props.FloatProperty(name="Shadow Near Clip")
    corona_intensity: bpy.props.FloatProperty(name="Corona Intensity", default=1.0)
    corona_z_bias: bpy.props.FloatProperty(name="Corona Z Bias", default=0.1)
    tangent: bpy.props.FloatVectorProperty(name="Tangent")
    cone_inner_angle: bpy.props.FloatProperty(name="Cone Inner Angle")
    cone_outer_angle: bpy.props.FloatProperty(name="Cone Outer Angle")
    extent: bpy.props.FloatVectorProperty(name="Extent", default=(1, 1, 1), subtype="XYZ")
    projected_texture_hash: bpy.props.StringProperty(name="Projected Texture Hash")


class LightPresetProp(bpy.types.PropertyGroup):
    """Represents a light preset property."""
    
    index: bpy.props.IntProperty("Index")
    name: bpy.props.StringProperty("Name")


class LightFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    """Represents the light flags."""
    interior_only: bpy.props.BoolProperty(
        name="Interior Only",
        description="Light will only be rendered when inside an interior",
        update=FlagPropertyGroup.update_flag)
    
    exterior_only: bpy.props.BoolProperty(
        name="Exterior Only", 
        description="Light will only be rendered when not inside an interior",
        update=FlagPropertyGroup.update_flag)
    
    dont_use_in_cutscene: bpy.props.BoolProperty(
        name="Dont Use In Cutscene", 
        description="Light will not be rendered in cutscenes",
        update=FlagPropertyGroup.update_flag)
    
    vehicle: bpy.props.BoolProperty(
        name="Vehicle", 
        description="Light will be rendered on vehicles",
        update=FlagPropertyGroup.update_flag)
    
    ignore_light_state: bpy.props.BoolProperty(
        name="Ignore Artificial Lights State",
        description="Light will ignore SET_ARTIFICIAL_LIGHTS_STATE(FALSE) from scripts and keep rendering",
        update=FlagPropertyGroup.update_flag)
    
    texture_projection: bpy.props.BoolProperty(
        name="Texture Projection", 
        description="Enable texture projection",
        update=FlagPropertyGroup.update_flag)
    
    cast_shadows: bpy.props.BoolProperty(
        name="Cast Shadows", 
        description="Light will cast shadows",
        update=FlagPropertyGroup.update_flag)
    
    static_shadows: bpy.props.BoolProperty(
        name="Cast Static Shadows", 
        description="Light will cast static shadows",
        update=FlagPropertyGroup.update_flag)
    
    dynamic_shadows: bpy.props.BoolProperty(
        name="Cast Dynamic Shadows", 
        description="Light will cast dynamic shadows",
        update=FlagPropertyGroup.update_flag)
    
    calc_from_sun: bpy.props.BoolProperty(
        name="Calculate From Sun", 
        description="Light will be calculated from sun position",
        update=FlagPropertyGroup.update_flag)
    
    enable_buzzing: bpy.props.BoolProperty(
        name="Enable Buzzing", 
        description="Light will be enabled when buzzing",
        update=FlagPropertyGroup.update_flag)
    
    force_buzzing: bpy.props.BoolProperty(
        name="Force Buzzing", 
        description="Light will be forced to buzz",
        update=FlagPropertyGroup.update_flag)
    
    draw_volume: bpy.props.BoolProperty(
        name="Draw Volume", 
        description="Force enable volume rendering, ignoring timecycle",
        update=FlagPropertyGroup.update_flag)
    
    no_specular: bpy.props.BoolProperty(
        name="No Specular", 
        description="Light will not reflect on specular materials",
        update=FlagPropertyGroup.update_flag)
    
    both_int_and_ext: bpy.props.BoolProperty(
        name="Both Interior And Exterior", 
        description="Light will be rendered both inside and outside",
        update=FlagPropertyGroup.update_flag)
    
    corona_only: bpy.props.BoolProperty(
        name="Corona Only", 
        description="Light will only render the corona",
        update=FlagPropertyGroup.update_flag)
    
    not_in_reflection: bpy.props.BoolProperty(
        name="Not In Reflection", 
        description="Light will not be rendered in reflections",
        update=FlagPropertyGroup.update_flag)
    
    only_in_reflection: bpy.props.BoolProperty(
        name="Only In Reflection", 
        description="Light will only be rendered in reflections",
        update=FlagPropertyGroup.update_flag)
    
    enable_culling_plane: bpy.props.BoolProperty(
        name="Enable Culling Plane", 
        description="Enable the culling plane",
        update=FlagPropertyGroup.update_flag)
    
    enable_vol_outer_color: bpy.props.BoolProperty(
        name="Enable Volume Outer Color", 
        description="Enable the volume outer color",
        update=FlagPropertyGroup.update_flag)
    
    higher_res_shadows: bpy.props.BoolProperty(
        name="Higher Res Shadows", 
        description="Light will render higher resolution shadows",
        update=FlagPropertyGroup.update_flag)
    
    only_low_res_shadows: bpy.props.BoolProperty(
        name="Only Low Res Shadows", 
        description="Light will only render low resolution shadows",
        update=FlagPropertyGroup.update_flag)
    
    far_lod_light: bpy.props.BoolProperty(
        name="Far Lod Light", 
        description="Light will be rendered as a far LOD Light",
        update=FlagPropertyGroup.update_flag)
    
    dont_light_alpha: bpy.props.BoolProperty(
        name="Don't Light Alpha", 
        description="Light won't affect transparent geometry, such as glass panes",
        update=FlagPropertyGroup.update_flag)
    
    cast_shadows_if_possible: bpy.props.BoolProperty(
        name="Cast Shadows If Possible", 
        description="Light will cast shadows if possible",
        update=FlagPropertyGroup.update_flag)
    
    cutscene: bpy.props.BoolProperty(
        name="Cutscene",
        description="Light will be rendered in cutscenes",
        update=FlagPropertyGroup.update_flag)
    
    moving_light_source: bpy.props.BoolProperty(
        name="Moving light Source", 
        description="Light will be rendered as a moving light source",
        update=FlagPropertyGroup.update_flag)
    
    use_vehicle_twin: bpy.props.BoolProperty(
        name="Use Vehicle Twin", 
        description="Light will use the vehicle twin",
        update=FlagPropertyGroup.update_flag)
    
    force_medium_lod_light: bpy.props.BoolProperty(
        name="Force Medium LOD Light", 
        description="Light will be rendered as a medium LOD Light",
        update=FlagPropertyGroup.update_flag)
    
    corona_only_lod_light: bpy.props.BoolProperty(
        name="Corona Only LOD Light", 
        description="Light will be rendered as a corona only LOD Light",
        update=FlagPropertyGroup.update_flag)
    
    delayed_render: bpy.props.BoolProperty(
        name="Delay Render", 
        description="Create Shadow casting light early in the frame to avoid visible shadow pop-in",
        update=FlagPropertyGroup.update_flag)
    
    already_tested_for_occlusion: bpy.props.BoolProperty(
        name="Already Tested For Occlusion", 
        description="Light has already been tested for occlusion",
        update=FlagPropertyGroup.update_flag)


@persistent
def on_file_loaded(_):
    """
    Handler function that is called when a blend file is loaded.
    It sets the default value of the ShaderMaterials collection and loads light presets.
    """
    bpy.context.scene.shader_materials.clear()
    for index, mat in enumerate(shadermats):
        item = bpy.context.scene.shader_materials.add()
        item.index = index
        item.name = mat.name

    load_light_presets()


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


def get_light_presets_path() -> str:
    """
    Returns the path to the light_presets.xml file.

    The path is constructed based on the package name and the user resource directory.
    If the file does not exist, a FileNotFoundError is raised.

    Returns:
        str: The path to the light_presets.xml file.
    """
    package_name = __name__.split(".")[0]
    presets_path = f"{bpy.utils.user_resource('SCRIPTS', path='addons')}\\{package_name}\\ydr\\light_presets.xml"
    if os.path.exists(presets_path):
        return presets_path
    else:
        raise FileNotFoundError(
            f"light_presets.xml file not found! Please redownload this file from the github and place it in '{os.path.dirname(presets_path)}'")


light_presets = LightPresetsFile()


def load_light_presets():
    """
    Loads light presets from a file and adds them to the scene's light presets collection.
    """
    bpy.context.scene.light_presets.clear()
    path = get_light_presets_path()
    if os.path.exists(path):
        file = LightPresetsFile.from_xml_file(path)
        light_presets.presets = file.presets
        for index, preset in enumerate(light_presets.presets):
            item = bpy.context.scene.light_presets.add()
            item.name = str(preset.name)
            item.index = index


def get_texture_name(self):
    """
    Returns the name of the texture file without the extension.
    
    If the image is available, it extracts the base name of the file
    without the extension using the `os.path` module. Otherwise, it
    returns "None".
    """
    if self.image:
        return os.path.splitext(basename(self.image.filepath))[0]
    return "None"


def get_model_properties(model_obj: bpy.types.Object, lod_level: LODLevel) -> DrawableModelProperties:
    """
    Retrieves the properties of a drawable model based on the LOD level.

    Parameters:
        model_obj (bpy.types.Object): The model object.
        lod_level (LODLevel): The level of detail.

    Returns:
        DrawableModelProperties: The properties of the drawable model.

    Raises:
        ValueError: If the model object has no LOD or the LOD mesh is missing.
    """
    drawable_obj = find_sollumz_parent(model_obj, SollumType.DRAWABLE)

    if drawable_obj is not None and model_obj.vertex_groups:
        return drawable_obj.skinned_model_properties.get_lod(lod_level)

    lod = model_obj.sollumz_lods.get_lod(lod_level)

    if lod is None or lod.mesh is None:
        raise ValueError(
            f"Failed to get Drawable Model properties: {model_obj.name} has no {SOLLUMZ_UI_NAMES[lod_level]} LOD!")

    return lod.mesh.drawable_model_properties


def register():
    # Shader Materials
    bpy.types.Scene.shader_material_index = bpy.props.IntProperty(name="Shader Material Index")
    bpy.types.Scene.shader_materials = bpy.props.CollectionProperty(type=ShaderMaterial, name="Shader Materials")
    bpy.app.handlers.load_post.append(on_file_loaded)

    # Drawable Properties
    bpy.types.Object.drawable_properties = bpy.props.PointerProperty(type=DrawableProperties)

    # Shader Properties
    bpy.types.Material.shader_properties = bpy.props.PointerProperty(type=ShaderProperties)

    # Texture Properties
    bpy.types.ShaderNodeTexImage.texture_properties = bpy.props.PointerProperty(type=TextureProperties)
    bpy.types.ShaderNodeTexImage.texture_flags = bpy.props.PointerProperty(type=TextureFlags)
    bpy.types.ShaderNodeTexImage.sollumz_texture_name = bpy.props.StringProperty(
        name="Texture Name", description="Name of texture.", get=get_texture_name)

    # Skinned Drawable Model Properties
    bpy.types.Object.skinned_model_properties = bpy.props.PointerProperty(type=SkinnedDrawableModelProperties)

    # Drawable Model Properties
    bpy.types.Mesh.drawable_model_properties = bpy.props.PointerProperty(type=DrawableModelProperties)
    bpy.types.Object.drawable_model_properties = bpy.props.PointerProperty(type=DrawableModelProperties)

    # Scene Properties
    bpy.types.Scene.create_seperate_drawables = bpy.props.BoolProperty(
        name="Separate Objects", description="Create a separate Drawable for each selected object")
    bpy.types.Scene.auto_create_embedded_col = bpy.props.BoolProperty(
        name="Auto-Embed Collision", description="Automatically create embedded static collision")
    bpy.types.Scene.center_drawable_to_selection = bpy.props.BoolProperty(
        name="Center to Selection", description="Center Drawable(s) to selection", default=True)

    # Bone Properties
    bpy.types.Bone.bone_properties = bpy.props.PointerProperty(type=BoneProperties)

    # Light Properties
    bpy.types.Light.sollum_type = bpy.props.EnumProperty(
        items=items_from_enums(LightType),
        name="Light Type",
        default=LightType.POINT,
        options={"HIDDEN"},
        get=get_light_type,
        set=set_light_type
    )
    bpy.types.Light.is_capsule = bpy.props.BoolProperty()
    bpy.types.Light.light_properties = bpy.props.PointerProperty(type=LightProperties)
    bpy.types.Scene.create_light_type = bpy.props.EnumProperty(
        items=[
            (LightType.POINT.value, SOLLUMZ_UI_NAMES[LightType.POINT], SOLLUMZ_UI_NAMES[LightType.POINT]),
            (LightType.SPOT.value, SOLLUMZ_UI_NAMES[LightType.SPOT], SOLLUMZ_UI_NAMES[LightType.SPOT]),
            (LightType.CAPSULE.value, SOLLUMZ_UI_NAMES[LightType.CAPSULE], SOLLUMZ_UI_NAMES[LightType.CAPSULE]),
        ],
        name="Light Type",
        default=LightType.POINT,
        options={"HIDDEN"}
    )
    bpy.types.Light.time_flags = bpy.props.PointerProperty(type=TimeFlags)
    bpy.types.Light.light_flags = bpy.props.PointerProperty(type=LightFlags)

    # LOD Properties
    bpy.types.Scene.sollumz_auto_lod_ref_mesh = bpy.props.PointerProperty(
        type=bpy.types.Mesh, name="Reference Mesh",
        description="The mesh to copy and decimate for each LOD level. You'd usually want to set this as the highest LOD then run the tool for all lower LODs")
    bpy.types.Scene.sollumz_auto_lod_levels = lod_level_enum_flag_prop_factory()
    bpy.types.Scene.sollumz_auto_lod_decimate_step = bpy.props.FloatProperty(
        name="Decimate Step", min=0.0, max=0.99, default=0.6)

    # Light Presets
    bpy.types.Scene.light_preset_index = bpy.props.IntProperty(name="Light Preset Index")
    bpy.types.Scene.light_presets = bpy.props.CollectionProperty(type=LightPresetProp, name="Light Presets")

    # Extract LODs Properties
    bpy.types.Scene.sollumz_extract_lods_levels = lod_level_enum_flag_prop_factory()
    bpy.types.Scene.sollumz_extract_lods_parent_type = bpy.props.EnumProperty(name="Parent Type", items=(
        ("sollumz_extract_lods_parent_type_object", "Object", "Parent to an Object"),
        ("sollumz_extract_lods_parent_type_collection", "Collection", "Parent to a Collection")
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
    del bpy.types.Scene.light_presets
    del bpy.types.Scene.light_preset_index
    del bpy.types.Scene.create_seperate_drawables
    del bpy.types.Scene.auto_create_embedded_col
    del bpy.types.Scene.center_drawable_to_selection
    del bpy.types.Scene.sollumz_auto_lod_ref_mesh
    del bpy.types.Scene.sollumz_auto_lod_levels
    del bpy.types.Scene.sollumz_auto_lod_decimate_step
    del bpy.types.Scene.sollumz_extract_lods_levels
    del bpy.types.Scene.sollumz_extract_lods_parent_type

    bpy.app.handlers.load_post.remove(on_file_loaded)
