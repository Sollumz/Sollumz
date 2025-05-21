import bpy
from bpy.types import (
    Object,
    Scene,
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    CollectionProperty,
    PointerProperty,
)
import os
from typing import Optional
from ..tools.blenderhelper import lod_level_enum_flag_prop_factory
from ..sollumz_helper import find_sollumz_parent
from ..cwxml.light_preset import LightPresetsFile
from ..cwxml.shader_preset import ShaderPresetsFile
from ..sollumz_properties import SOLLUMZ_UI_NAMES, items_from_enums, LODLevel, SollumType, LightType, FlagPropertyGroup, TimeFlagsMixin
from ..ydr.shader_materials import shadermats, shadermats_by_filename
from .render_bucket import RenderBucket, RenderBucketEnumItems
from .light_flashiness import Flashiness, LightFlashinessEnumItems
from bpy.app.handlers import persistent
from bpy.path import basename


class ShaderOrderItem(bpy.types.PropertyGroup):
    # For drawable shader order list
    index: bpy.props.IntProperty(min=0)
    name: bpy.props.StringProperty()
    filename: bpy.props.StringProperty()


class DrawableShaderOrder(bpy.types.PropertyGroup):
    order_items: bpy.props.CollectionProperty(type=ShaderOrderItem)
    active_index: bpy.props.IntProperty(min=0)

    def get_active_shader_item_index(self) -> int:
        return self.order_items[self.active_index].index

    def swap_shaders(self, old: int, new: int) -> int:
        """Swaps two shaders. Shader at ``old`` index is placed at ``new`` index, and shader at ``new``
        is placed at ``old``.
        """
        if new >= len(self.order_items):
            return

        list_ind = self.active_index

        for i, item in enumerate(self.order_items):
            if item.index == new:
                item.index = old
            elif item.index == old:
                item.index = new
                list_ind = i

        self.active_index = list_ind

    def move_shader_up(self, index: int):
        self.swap_shaders(index, index - 1)

    def move_shader_down(self, index: int):
        self.swap_shaders(index, index + 1)

    def move_shader_to_top(self, index: int):
        """Moves the shader at ``index`` to the top. All previous shaders are moved down."""
        list_ind = self.active_index

        for i, item in enumerate(self.order_items):
            if item.index < index:
                # move previous shaders down
                item.index += 1
            elif item.index == index:
                # move our shader to the top
                item.index = 0
                list_ind = i

        self.active_index = list_ind

    def move_shader_to_bottom(self, index: int):
        """Moves the shader at ``index`` to the bottom. All subsequent shaders are moved up."""
        list_ind = self.active_index

        for i, item in enumerate(self.order_items):
            if item.index > index:
                # move subsequent shaders up
                item.index -= 1
            elif item.index == index:
                # move our shader to the bottom
                item.index = len(self.order_items) - 1
                list_ind = i

        self.active_index = list_ind


class CharClothProperties(bpy.types.PropertyGroup):
    weight: FloatProperty(name="Weight", default=1.0)
    num_pin_radius_sets: IntProperty(name="Number of Pin Radius Sets", min=1, max=4, default=1)
    pin_radius_scale: FloatProperty(name="Pin Radius Scale", default=1.0)
    pin_radius_threshold: FloatProperty(name="Pin Radius Threshold", default=0.04)
    wind_scale: FloatProperty(name="Wind Scale", default=1.0)


class DrawableProperties(bpy.types.PropertyGroup):
    lod_dist_high: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance High")
    lod_dist_med: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Med")
    lod_dist_low: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Low")
    lod_dist_vlow: bpy.props.FloatProperty(
        min=0, max=10000, default=9998, name="Lod Distance Vlow")

    shader_order: bpy.props.PointerProperty(type=DrawableShaderOrder)

    char_cloth: PointerProperty(type=CharClothProperties)


class DrawableModelProperties(bpy.types.PropertyGroup):
    render_mask: bpy.props.IntProperty(name="Render Mask", default=255)
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

    renderbucket: bpy.props.EnumProperty(
        name="Render Bucket", items=RenderBucketEnumItems,
        default=RenderBucket.OPAQUE.name
    )
    filename: bpy.props.StringProperty(name="Shader Filename", default="default.sps")
    name: bpy.props.StringProperty(name="Shader Name", default="default")

    def get_ui_name(self) -> str:
        s = shadermats_by_filename.get(self.filename, None)
        return (s and s.ui_name) or ""

    ui_name: bpy.props.StringProperty(name="Shader", get=get_ui_name)


class TextureProperties(bpy.types.PropertyGroup):
    embedded: bpy.props.BoolProperty(name="Embedded", default=False)


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
    def _get_favorite(self):
        from ..sollumz_preferences import get_addon_preferences
        preferences = get_addon_preferences(bpy.context)
        return preferences.is_favorite_shader(self.name)

    def _set_favorite(self, value):
        from ..sollumz_preferences import get_addon_preferences
        preferences = get_addon_preferences(bpy.context)
        preferences.toggle_favorite_shader(self.name, value)

    index: bpy.props.IntProperty(name="Index")
    name: bpy.props.StringProperty(name="Name")
    search_name: bpy.props.StringProperty(name="Name")  # name without '_' or spaces used by list search filter
    favorite: BoolProperty(
        name="Favorite",
        get=_get_favorite,
        set=_set_favorite,
    )


class LightProperties(bpy.types.PropertyGroup):
    flashiness: bpy.props.EnumProperty(name="Flashiness", items=LightFlashinessEnumItems,
                                       default=Flashiness.CONSTANT.name)
    group_id: bpy.props.IntProperty(name="Group ID")
    culling_plane_normal: bpy.props.FloatVectorProperty(name="Culling Plane Normal", subtype="XYZ")
    culling_plane_offset: bpy.props.FloatProperty(name="Culling Plane Offset", subtype="DISTANCE")
    shadow_blur: bpy.props.FloatProperty(name="Shadow Blur", min=0.0, max=1.0, subtype="FACTOR")
    volume_size_scale: bpy.props.FloatProperty(name="Volume Size Scale", default=1.0)
    volume_outer_color: bpy.props.FloatVectorProperty(
        name="Volume Outer Color",
        subtype="COLOR",
        min=0.0,
        max=1.0,
        default=(1.0, 1.0, 1.0)
    )
    light_hash: bpy.props.IntProperty(
        name="Light ID",
        description=(
            "Identifier used to link the light in the base model with the correct light in a Light Effect entity "
            "extension"
        ),
        min=0, max=255,
    )
    volume_outer_intensity: bpy.props.FloatProperty(name="Volume Outer Intensity", default=1.0)
    corona_size: bpy.props.FloatProperty(name="Corona Size")
    volume_outer_exponent: bpy.props.FloatProperty(name="Volume Outer Exponent", default=1.0)
    light_fade_distance: bpy.props.FloatProperty(name="Light Fade Distance")
    shadow_fade_distance: bpy.props.FloatProperty(name="Shadow Fade Distance")
    specular_fade_distance: bpy.props.FloatProperty(name="Specular Fade Distance")
    volumetric_fade_distance: bpy.props.FloatProperty(name="Volumetric Fade Distance")
    corona_intensity: bpy.props.FloatProperty(name="Corona Intensity", default=1.0)
    corona_z_bias: bpy.props.FloatProperty(name="Corona Z Bias", default=0.1)
    extent: bpy.props.FloatVectorProperty(name="Extent", default=(1, 1, 1), subtype="XYZ", soft_min=0.01, unit="LENGTH")
    projected_texture_hash: bpy.props.StringProperty(name="Projected Texture Hash")


class PresetEntry(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty("Index")
    name: bpy.props.StringProperty("Name")


class LightTimeFlags(TimeFlagsMixin, bpy.types.PropertyGroup):
    pass


class LightFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
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
    from ..sollumz_preferences import get_config_directory_path
    return os.path.join(get_config_directory_path(), "light_presets.xml")


def get_shader_presets_path() -> str:
    from ..sollumz_preferences import get_config_directory_path
    return os.path.join(get_config_directory_path(), "shader_presets.xml")


_default_light_presets_path = os.path.join(os.path.dirname(__file__), "light_presets.xml")

_default_shader_presets_path = os.path.join(os.path.dirname(__file__), "shader_presets.xml")


def get_default_light_presets_path() -> str:
    return _default_light_presets_path


def get_default_shader_presets_path() -> str:
    return _default_shader_presets_path


light_presets = LightPresetsFile()

shader_presets = ShaderPresetsFile()


def load_light_presets():
    bpy.context.window_manager.sz_light_presets.clear()

    path = get_light_presets_path()
    if not os.path.exists(path):
        path = get_default_light_presets_path()
        if not os.path.exists(path):
            return

    file = LightPresetsFile.from_xml_file(path)
    light_presets.presets = file.presets
    for index, preset in enumerate(light_presets.presets):
        item = bpy.context.window_manager.sz_light_presets.add()
        item.name = str(preset.name)
        item.index = index


def load_shader_presets():
    bpy.context.window_manager.sz_shader_presets.clear()

    path = get_shader_presets_path()
    if not os.path.exists(path):
        path = get_default_shader_presets_path()
        if not os.path.exists(path):
            return

    file = ShaderPresetsFile.from_xml_file(path)
    shader_presets.presets = file.presets
    for index, preset in enumerate(shader_presets.presets):
        item = bpy.context.window_manager.sz_shader_presets.add()
        item.name = str(preset.name)
        item.index = index


def get_texture_name(self):
    if self.image:
        return os.path.splitext(basename(self.image.filepath))[0]
    return ""


def get_model_properties(model_obj: bpy.types.Object, lod_level: LODLevel) -> DrawableModelProperties:
    drawable_obj = find_sollumz_parent(model_obj, SollumType.DRAWABLE)

    if drawable_obj is not None and model_obj.vertex_groups:
        return drawable_obj.skinned_model_properties.get_lod(lod_level)

    lod = model_obj.sz_lods.get_lod(lod_level)
    lod_mesh = lod.mesh

    if lod_mesh is None:
        raise ValueError(
            f"Failed to get Drawable Model properties: {model_obj.name} has no {SOLLUMZ_UI_NAMES[lod_level]} LOD!")

    return lod_mesh.drawable_model_properties


def refresh_ui_collections():
    # Initialize shader materials collection with an entry per shader
    # We need the shader list as a collection property to be able to display it on the UI
    bpy.context.window_manager.sz_shader_materials.clear()
    for index, mat in enumerate(shadermats):
        item = bpy.context.window_manager.sz_shader_materials.add()
        item.index = index
        item.name = mat.name
        item.search_name = mat.ui_name.replace(" ", "").replace("_", "")

    load_light_presets()
    load_shader_presets()


@persistent
def on_blend_file_loaded(_):
    refresh_ui_collections()


def register():
    bpy.types.WindowManager.sz_shader_material_index = bpy.props.IntProperty(
        name="Shader Material Index", min=0, max=len(shadermats) - 1)
    bpy.types.WindowManager.sz_shader_materials = bpy.props.CollectionProperty(
        type=ShaderMaterial, name="Shader Materials"
    )
    bpy.types.Object.drawable_properties = bpy.props.PointerProperty(
        type=DrawableProperties)
    bpy.types.Material.shader_properties = bpy.props.PointerProperty(
        type=ShaderProperties)
    bpy.types.ShaderNodeTexImage.texture_properties = bpy.props.PointerProperty(
        type=TextureProperties)
    bpy.types.ShaderNodeTexImage.sollumz_texture_name = bpy.props.StringProperty(
        name="Texture Name", description="Name of texture", get=get_texture_name)

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
    bpy.types.Light.time_flags = bpy.props.PointerProperty(type=LightTimeFlags)
    bpy.types.Light.light_flags = bpy.props.PointerProperty(type=LightFlags)

    bpy.types.Scene.sollumz_auto_lod_ref_mesh = bpy.props.PointerProperty(
        type=bpy.types.Mesh, name="Reference Mesh", description="The mesh to copy and decimate for each LOD level. You'd usually want to set this as the highest LOD then run the tool for all lower LODs")
    bpy.types.Scene.sollumz_auto_lod_levels = lod_level_enum_flag_prop_factory()
    bpy.types.Scene.sollumz_auto_lod_decimate_step = bpy.props.FloatProperty(
        name="Decimate Step", min=0.0, max=0.99, default=0.6)

    bpy.types.WindowManager.sz_light_preset_index = bpy.props.IntProperty(name="Light Preset Index")
    bpy.types.WindowManager.sz_light_presets = bpy.props.CollectionProperty(type=PresetEntry, name="Light Presets")

    bpy.types.WindowManager.sz_shader_preset_index = bpy.props.IntProperty(name="Shader Preset Index")
    bpy.types.WindowManager.sz_shader_presets = bpy.props.CollectionProperty(type=PresetEntry, name="Shader Presets")

    bpy.types.Scene.sollumz_extract_lods_levels = lod_level_enum_flag_prop_factory()
    bpy.types.Scene.sollumz_extract_lods_parent_type = bpy.props.EnumProperty(name="Parent Type", items=(
        ("sollumz_extract_lods_parent_type_object", "Object", "Parent to an Object"),
        ("sollumz_extract_lods_parent_type_collection",
         "Collection", "Parent to a Collection")
    ), default=0)

    from .cable import CableAttr
    bpy.types.WindowManager.sz_ui_cable_radius_visualize = bpy.props.BoolProperty(
        name="Show Radius", description="Display the cable radius values on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cable_radius = bpy.props.FloatProperty(
        name=CableAttr.RADIUS.label, description=CableAttr.RADIUS.description,
        min=0.0001, default=CableAttr.RADIUS.default_value,
        subtype="DISTANCE"
    )
    bpy.types.WindowManager.sz_ui_cable_diffuse_factor_visualize = bpy.props.BoolProperty(
        name="Show Diffuse Factor", description="Display the cable diffuse factor values on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cable_diffuse_factor = bpy.props.FloatProperty(
        name=CableAttr.DIFFUSE_FACTOR.label, description=CableAttr.DIFFUSE_FACTOR.description,
        min=0.0, max=1.0, default=CableAttr.DIFFUSE_FACTOR.default_value,
        subtype="FACTOR"
    )
    bpy.types.WindowManager.sz_ui_cable_um_scale_visualize = bpy.props.BoolProperty(
        name="Show Micromovements Scale", description="Display the cable micromovements scale values on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cable_um_scale = bpy.props.FloatProperty(
        name=CableAttr.UM_SCALE.label, description=CableAttr.UM_SCALE.description,
        min=0.0, default=CableAttr.UM_SCALE.default_value
    )
    bpy.types.WindowManager.sz_ui_cable_phase_offset_visualize = bpy.props.BoolProperty(
        name="Show Phase Offset", description="Display the cable phase offset values on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cable_phase_offset = bpy.props.FloatVectorProperty(
        name=CableAttr.PHASE_OFFSET.label, description=CableAttr.PHASE_OFFSET.description,
        size=2, min=0.0, max=1.0, default=CableAttr.PHASE_OFFSET.default_value[0:2]
    )
    bpy.types.WindowManager.sz_ui_cable_material_index_visualize = bpy.props.BoolProperty(
        name="Show Material Index", description="Display the cable material indices on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cable_material_index = bpy.props.IntProperty(
        name=CableAttr.MATERIAL_INDEX.label, description=CableAttr.MATERIAL_INDEX.description,
        min=0, default=CableAttr.MATERIAL_INDEX.default_value,
    )

    from .cloth import ClothAttr

    bpy.types.WindowManager.sz_ui_cloth_vertex_weight_visualize = bpy.props.BoolProperty(
        name="Show Weights", description="Display the cloth weight values on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cloth_vertex_weight = bpy.props.FloatProperty(
        name=ClothAttr.VERTEX_WEIGHT.label, description=ClothAttr.VERTEX_WEIGHT.description,
        min=0.00001, max=1.0, default=ClothAttr.VERTEX_WEIGHT.default_value,
        precision=6, step=1
    )
    bpy.types.WindowManager.sz_ui_cloth_inflation_scale_visualize = bpy.props.BoolProperty(
        name="Show Inflation Scale", description="Display the cloth inflation scale values on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cloth_inflation_scale = bpy.props.FloatProperty(
        name=ClothAttr.INFLATION_SCALE.label, description=ClothAttr.INFLATION_SCALE.description,
        min=0.0, max=1.0, default=ClothAttr.INFLATION_SCALE.default_value
    )
    bpy.types.WindowManager.sz_ui_cloth_pinned_visualize = bpy.props.BoolProperty(
        name="Show Pinned", description="Display the cloth pinned vertices on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cloth_pin_radius_set = bpy.props.IntProperty(
        name="Pin Radius Set",
        min=1, max=4, default=1
    )
    bpy.types.WindowManager.sz_ui_cloth_pin_radius = bpy.props.FloatProperty(
        name=ClothAttr.PIN_RADIUS.label, description=ClothAttr.PIN_RADIUS.description,
        min=0.0, max=1.0, default=0.1, step=5,
    )
    bpy.types.WindowManager.sz_ui_cloth_pin_radius_gradient_min = bpy.props.FloatProperty(
        name="Pin Radius Gradient Minimum",
        min=0.0, max=1.0, default=0.1, step=5,
    )
    bpy.types.WindowManager.sz_ui_cloth_pin_radius_gradient_max = bpy.props.FloatProperty(
        name="Pin Radius Gradient Maximum",
        min=0.0, max=1.0, default=0.8, step=5,
    )
    bpy.types.WindowManager.sz_ui_cloth_pin_radius_visualize = bpy.props.BoolProperty(
        name="Show Pin Radius", description="Display the cloth pin radius on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cloth_force_transform_visualize = bpy.props.BoolProperty(
        name="Show Force Transform", description="Display the cloth force transforms on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cloth_force_transform = bpy.props.IntProperty(
        name=ClothAttr.FORCE_TRANSFORM.label, description=ClothAttr.FORCE_TRANSFORM.description,
        min=0, max=2, default=ClothAttr.FORCE_TRANSFORM.default_value
    )
    bpy.types.WindowManager.sz_ui_cloth_diag_material_errors_visualize = bpy.props.BoolProperty(
        name="Show Material Errors",
        description="Display faces that have a non-cloth material on the 3D Viewport",
        default=False
    )
    bpy.types.WindowManager.sz_ui_cloth_diag_binding_errors_visualize = bpy.props.BoolProperty(
        name="Show Binding Errors",
        description="Display vertices of the drawable mesh that failed to bind to the cloth mesh on the 3D Viewport",
        default=False
    )
    # bpy.types.WindowManager.sz_ui_cloth_diag_bindings_visualize = bpy.props.BoolProperty(
    #     name="Show Bindings",
    #     description="",
    #     default=False
    # )

    bpy.app.handlers.load_post.append(on_blend_file_loaded)
    refresh_ui_collections()


def unregister():
    del bpy.types.ShaderNodeTexImage.sollumz_texture_name
    del bpy.types.WindowManager.sz_shader_material_index
    del bpy.types.WindowManager.sz_shader_materials
    del bpy.types.Object.drawable_properties
    del bpy.types.Mesh.drawable_model_properties
    del bpy.types.Object.skinned_model_properties
    del bpy.types.Material.shader_properties
    del bpy.types.ShaderNodeTexImage.texture_properties
    del bpy.types.Bone.bone_properties
    del bpy.types.Light.light_properties
    del bpy.types.Scene.create_light_type
    del bpy.types.Light.time_flags
    del bpy.types.Light.light_flags
    del bpy.types.Light.is_capsule
    del bpy.types.WindowManager.sz_light_presets
    del bpy.types.WindowManager.sz_light_preset_index
    del bpy.types.WindowManager.sz_shader_presets
    del bpy.types.WindowManager.sz_shader_preset_index
    del bpy.types.Scene.create_seperate_drawables
    del bpy.types.Scene.auto_create_embedded_col
    del bpy.types.Scene.center_drawable_to_selection
    del bpy.types.Scene.sollumz_auto_lod_ref_mesh
    del bpy.types.Scene.sollumz_auto_lod_levels
    del bpy.types.Scene.sollumz_auto_lod_decimate_step
    del bpy.types.Scene.sollumz_extract_lods_levels
    del bpy.types.Scene.sollumz_extract_lods_parent_type

    del bpy.types.WindowManager.sz_ui_cable_radius_visualize
    del bpy.types.WindowManager.sz_ui_cable_radius
    del bpy.types.WindowManager.sz_ui_cable_diffuse_factor_visualize
    del bpy.types.WindowManager.sz_ui_cable_diffuse_factor
    del bpy.types.WindowManager.sz_ui_cable_um_scale_visualize
    del bpy.types.WindowManager.sz_ui_cable_um_scale
    del bpy.types.WindowManager.sz_ui_cable_phase_offset_visualize
    del bpy.types.WindowManager.sz_ui_cable_phase_offset
    del bpy.types.WindowManager.sz_ui_cable_material_index_visualize
    del bpy.types.WindowManager.sz_ui_cable_material_index

    del bpy.types.WindowManager.sz_ui_cloth_vertex_weight
    del bpy.types.WindowManager.sz_ui_cloth_vertex_weight_visualize
    del bpy.types.WindowManager.sz_ui_cloth_inflation_scale
    del bpy.types.WindowManager.sz_ui_cloth_inflation_scale_visualize
    del bpy.types.WindowManager.sz_ui_cloth_pinned_visualize
    del bpy.types.WindowManager.sz_ui_cloth_pin_radius_set
    del bpy.types.WindowManager.sz_ui_cloth_pin_radius
    del bpy.types.WindowManager.sz_ui_cloth_pin_radius_gradient_min
    del bpy.types.WindowManager.sz_ui_cloth_pin_radius_gradient_max
    del bpy.types.WindowManager.sz_ui_cloth_pin_radius_visualize
    del bpy.types.WindowManager.sz_ui_cloth_force_transform
    del bpy.types.WindowManager.sz_ui_cloth_force_transform_visualize
    del bpy.types.WindowManager.sz_ui_cloth_diag_material_errors_visualize
    del bpy.types.WindowManager.sz_ui_cloth_diag_binding_errors_visualize
    # del bpy.types.WindowManager.sz_ui_cloth_diag_bindings_visualize

    bpy.app.handlers.load_post.remove(on_blend_file_loaded)
