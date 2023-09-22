import bpy
from typing import Union
from enum import Enum
from ...tools.utils import get_list_item


class ExtensionType(str, Enum):
    DOOR = "CExtensionDefDoor"
    PARTICLE = "CExtensionDefParticleEffect"
    AUDIO_COLLISION = "CExtensionDefAudioCollisionSettings"
    AUDIO_EMITTER = "CExtensionDefAudioEmitter"
    EXPLOSION_EFFECT = "CExtensionDefExplosionEffect"
    LADDER = "CExtensionDefLadder"
    BUOYANCY = "CExtensionDefBuoyancy"
    LIGHT_SHAFT = "CExtensionDefLightShaft"
    SPAWN_POINT = "CExtensionDefSpawnPoint"
    SPAWN_POINT_OVERRIDE = "CExtensionDefSpawnPointOverride"
    WIND_DISTURBANCE = "CExtensionDefWindDisturbance"
    PROC_OBJECT = "CExtensionDefProcObject"
    EXPRESSION = "CExtensionDefExpression"


ExtensionTypeEnumItems = (
    (ExtensionType.DOOR, "Door", "", 0),
    (ExtensionType.PARTICLE, "Particle", "", 1),
    (ExtensionType.AUDIO_COLLISION, "Audio Collision Settings", "", 2),
    (ExtensionType.AUDIO_EMITTER, "Audio Emitter", "", 3),
    (ExtensionType.EXPLOSION_EFFECT, "Explosion Effect", "", 4),
    (ExtensionType.LADDER, "Ladder", "", 5),
    (ExtensionType.BUOYANCY, "Buoyancy", "", 6),
    (ExtensionType.LIGHT_SHAFT, "Light Shaft", "", 7),
    (ExtensionType.SPAWN_POINT, "Spawn Point", "", 8),
    (ExtensionType.SPAWN_POINT_OVERRIDE, "Spawn Point Override", "", 9),
    (ExtensionType.WIND_DISTURBANCE, "Wind Disturbance", "", 10),
    (ExtensionType.PROC_OBJECT, "Procedural Object", "", 11),
    (ExtensionType.EXPRESSION, "Expression", "", 12),
)


class LightShaftDensityType(str, Enum):
    CONSTANT = "LIGHTSHAFT_DENSITYTYPE_CONSTANT"
    SOFT = "LIGHTSHAFT_DENSITYTYPE_SOFT"
    SOFT_SHADOW = "LIGHTSHAFT_DENSITYTYPE_SOFT_SHADOW"
    SOFT_SHADOW_HD = "LIGHTSHAFT_DENSITYTYPE_SOFT_SHADOW_HD"
    LINEAR = "LIGHTSHAFT_DENSITYTYPE_LINEAR"
    LINEAR_GRADIENT = "LIGHTSHAFT_DENSITYTYPE_LINEAR_GRADIENT"
    QUADRATIC = "LIGHTSHAFT_DENSITYTYPE_QUADRATIC"
    QUADRATIC_GRADIENT = "LIGHTSHAFT_DENSITYTYPE_QUADRATIC_GRADIENT"


LightShaftDensityTypeEnumItems = (
    (LightShaftDensityType.CONSTANT, "Constant", "", 0),
    (LightShaftDensityType.SOFT, "Soft", "", 1),
    (LightShaftDensityType.SOFT_SHADOW, "Soft Shadow", "", 2),
    (LightShaftDensityType.SOFT_SHADOW_HD, "Soft Shadow HD", "", 3),
    (LightShaftDensityType.LINEAR, "Linear", "", 4),
    (LightShaftDensityType.LINEAR_GRADIENT, "Linear Gradient", "", 5),
    (LightShaftDensityType.QUADRATIC, "Quadratic", "", 6),
    (LightShaftDensityType.QUADRATIC_GRADIENT, "Quadratic Gradient", "", 7),
)


class LightShaftVolumeType(str, Enum):
    SHAFT = "LIGHTSHAFT_VOLUMETYPE_SHAFT"
    CYLINDER = "LIGHTSHAFT_VOLUMETYPE_CYLINDER"


LightShaftVolumeTypeEnumItems = (
    (LightShaftVolumeType.SHAFT, "Shaft", "", 0),
    (LightShaftVolumeType.CYLINDER, "Cylinder", "", 1),
)


class BaseExtensionProperties:
    offset_position: bpy.props.FloatVectorProperty(
        name="Offset Position", subtype="TRANSLATION")


class DoorExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    enable_limit_angle: bpy.props.BoolProperty(name="Enable Limit Angle")
    starts_locked: bpy.props.BoolProperty(name="Starts Locked")
    can_break: bpy.props.BoolProperty(name="Can Break")
    limit_angle: bpy.props.FloatProperty(name="Limit Angle")
    door_target_ratio: bpy.props.FloatProperty(
        name="Door Target Ratio", min=0)
    audio_hash: bpy.props.StringProperty(name="Audio Hash")


class ParticleExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    offset_rotation: bpy.props.FloatVectorProperty(
        name="Offset Rotation", subtype="EULER")
    fx_name: bpy.props.StringProperty(name="FX Name")
    fx_type: bpy.props.IntProperty(name="FX Type")
    bone_tag: bpy.props.IntProperty(name="Bone Tag")
    scale: bpy.props.FloatProperty(name="Scale")
    probability: bpy.props.IntProperty(name="Probability")
    flags: bpy.props.IntProperty(name="Flags")
    color: bpy.props.FloatVectorProperty(
        name="Color", subtype="COLOR", min=0, max=1, size=4, default=(1, 1, 1, 1))


class AudioCollisionExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    settings: bpy.props.StringProperty(name="Settings")


class AudioEmitterExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    offset_rotation: bpy.props.FloatVectorProperty(
        name="Offset Rotation", subtype="EULER")
    effect_hash: bpy.props.StringProperty(name="Effect Hash")


class ExplosionExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    offset_rotation: bpy.props.FloatVectorProperty(
        name="Offset Rotation", subtype="EULER")
    explosion_name: bpy.props.StringProperty(name="Explosion Name")
    bone_tag: bpy.props.IntProperty(name="Bone Tag")
    explosion_tag: bpy.props.IntProperty(name="Explosion Tag")
    explosion_type: bpy.props.IntProperty(name="Explosion Type")
    flags: bpy.props.IntProperty(name="Flags", subtype="UNSIGNED")


class LadderExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    bottom: bpy.props.FloatVectorProperty(name="Bottom", subtype="TRANSLATION")
    top: bpy.props.FloatVectorProperty(name="Top", subtype="TRANSLATION")
    normal: bpy.props.FloatVectorProperty(name="Normal", subtype="TRANSLATION")
    material_type: bpy.props.StringProperty(
        name="Material Type", default="METAL_SOLID_LADDER")
    template: bpy.props.StringProperty(name="Template", default="default")
    can_get_off_at_top: bpy.props.BoolProperty(
        name="Can Get Off At Top", default=True)
    can_get_off_at_bottom: bpy.props.BoolProperty(
        name="Can Get Off At Bottom", default=True)


class BuoyancyExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    # No other properties?
    pass


class ExpressionExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    expression_dictionary_name: bpy.props.StringProperty(
        name="Expression Dictionary Name")
    expression_name: bpy.props.StringProperty(name="Expression Name")
    creature_metadata_name: bpy.props.StringProperty(
        name="Creature Metadata Name")
    initialize_on_collision: bpy.props.BoolProperty(
        name="Initialize on Collision")


class LightShaftExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    density_type: bpy.props.EnumProperty(items=LightShaftDensityTypeEnumItems, name="Density Type")
    volume_type: bpy.props.EnumProperty(items=LightShaftVolumeTypeEnumItems, name="Volume Type")
    scale_by_sun_intensity: bpy.props.BoolProperty(name="Scale by Sun Intensity")
    direction_amount: bpy.props.FloatProperty(name="Direction Amount")
    length: bpy.props.FloatProperty(name="Length")
    color: bpy.props.FloatVectorProperty(
        name="Color", subtype="COLOR", min=0, max=1, size=4, default=(1, 1, 1, 1))
    intensity: bpy.props.FloatProperty(name="Intensity")
    flashiness: bpy.props.IntProperty(name="Flashiness")
    flags: bpy.props.IntProperty(name="Flags")
    fade_in_time_start: bpy.props.FloatProperty(name="Fade In Time Start")
    fade_in_time_end: bpy.props.FloatProperty(name="Fade In Time End")
    flashiness: bpy.props.IntProperty(name="Flashiness")
    fade_out_time_start: bpy.props.FloatProperty(name="Fade Out Time Start")
    fade_out_time_end: bpy.props.FloatProperty(name="Fade Out Time End")
    fade_distance_start: bpy.props.FloatProperty(name="Fade Distance Start")
    fade_distance_end: bpy.props.FloatProperty(name="Fade Distance End")
    softness: bpy.props.FloatProperty(name="Softness")
    cornerA: bpy.props.FloatVectorProperty(
        name="Corner A", subtype="TRANSLATION")
    cornerB: bpy.props.FloatVectorProperty(
        name="Corner B", subtype="TRANSLATION")
    cornerC: bpy.props.FloatVectorProperty(
        name="Corner C", subtype="TRANSLATION")
    cornerD: bpy.props.FloatVectorProperty(
        name="Corner D", subtype="TRANSLATION")
    direction: bpy.props.FloatVectorProperty(
        name="Direction", subtype="XYZ")


class SpawnPointExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    offset_rotation: bpy.props.FloatVectorProperty(
        name="Offset Rotation", subtype="EULER")
    spawn_type: bpy.props.StringProperty(name="Spawn Type")
    ped_type: bpy.props.StringProperty(name="Ped Type")
    group: bpy.props.StringProperty(name="Group")
    interior: bpy.props.StringProperty(name="Interior")
    required_map: bpy.props.StringProperty(name="Required Map")
    probability: bpy.props.FloatProperty(name="Probability")
    time_till_ped_leaves: bpy.props.FloatProperty(name="Time Till Ped Leaves")
    radius: bpy.props.FloatProperty(name="Radius")
    start: bpy.props.FloatProperty(name="Start")
    end: bpy.props.FloatProperty(name="End")
    high_pri: bpy.props.BoolProperty(name="High Priority")
    extended_range: bpy.props.BoolProperty(name="Extended Range")
    short_range: bpy.props.BoolProperty(name="Short Range")

    # TODO: Use enums
    available_in_mp_sp: bpy.props.StringProperty(name="Available in MP/SP")
    scenario_flags: bpy.props.StringProperty(name="Scenario Flags")


class SpawnPointOverrideProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    scenario_type: bpy.props.StringProperty(name="Scenario Type")
    itime_start_override: bpy.props.FloatProperty(name="iTime Start Override")
    itime_end_override: bpy.props.FloatProperty(name="iTime End Override")
    group: bpy.props.StringProperty(name="Group")
    model_set: bpy.props.StringProperty(name="Model Set")
    radius: bpy.props.FloatProperty(name="Radius")
    time_till_ped_leaves: bpy.props.StringProperty(name="Time Till Ped Leaves")

    # TODO: Use enums
    available_in_mp_sp: bpy.props.StringProperty(name="Available in MP/SP")
    scenario_flags: bpy.props.StringProperty(name="Scenario Flags")


class WindDisturbanceExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    offset_rotation: bpy.props.FloatVectorProperty(
        name="Offset Rotation", subtype="EULER")
    disturbance_type: bpy.props.IntProperty(name="Disturbance Type")
    bone_tag: bpy.props.IntProperty(name="Bone Tag")
    size: bpy.props.FloatVectorProperty(name="Size", size=4, subtype="XYZ")
    strength: bpy.props.FloatProperty(name="Strength")
    flags: bpy.props.IntProperty(name="Flags")


class ProcObjectExtensionProperties(bpy.types.PropertyGroup, BaseExtensionProperties):
    radius_inner: bpy.props.FloatProperty(name="Radius Inner")
    radius_outer: bpy.props.FloatProperty(name="Radius Outer")
    spacing: bpy.props.FloatProperty(name="Spacing")
    min_scale: bpy.props.FloatProperty(name="Min Scale")
    max_scale: bpy.props.FloatProperty(name="Max Scale")
    min_scale_z: bpy.props.FloatProperty(name="Min Scale Z")
    max_scale_z: bpy.props.FloatProperty(name="Max Scale Z")
    min_z_offset: bpy.props.FloatProperty(name="Min Z Offset")
    max_z_offset: bpy.props.FloatProperty(name="Max Z Offset")
    object_hash: bpy.props.IntProperty(name="Object Hash", subtype="UNSIGNED")
    flags: bpy.props.IntProperty(name="Flags", subtype="UNSIGNED")


class ExtensionProperties(bpy.types.PropertyGroup):
    def get_properties(self) -> BaseExtensionProperties:
        if self.extension_type == ExtensionType.DOOR:
            return self.door_extension_properties
        elif self.extension_type == ExtensionType.PARTICLE:
            return self.particle_extension_properties
        elif self.extension_type == ExtensionType.AUDIO_COLLISION:
            return self.audio_collision_extension_properties
        elif self.extension_type == ExtensionType.AUDIO_EMITTER:
            return self.audio_emitter_extension_properties
        elif self.extension_type == ExtensionType.BUOYANCY:
            return self.buoyancy_extension_properties
        elif self.extension_type == ExtensionType.EXPLOSION_EFFECT:
            return self.explosion_extension_properties
        elif self.extension_type == ExtensionType.EXPRESSION:
            return self.expression_extension_properties
        elif self.extension_type == ExtensionType.LADDER:
            return self.ladder_extension_properties
        elif self.extension_type == ExtensionType.LIGHT_SHAFT:
            return self.light_shaft_extension_properties
        elif self.extension_type == ExtensionType.PROC_OBJECT:
            return self.proc_object_extension_properties
        elif self.extension_type == ExtensionType.SPAWN_POINT:
            return self.spawn_point_extension_properties
        elif self.extension_type == ExtensionType.SPAWN_POINT_OVERRIDE:
            return self.spawn_point_override_properties
        elif self.extension_type == ExtensionType.WIND_DISTURBANCE:
            return self.wind_disturbance_properties

    extension_type: bpy.props.EnumProperty(name="Type", items=ExtensionTypeEnumItems)
    name: bpy.props.StringProperty(name="Name", default="Extension")

    door_extension_properties: bpy.props.PointerProperty(
        type=DoorExtensionProperties)
    particle_extension_properties: bpy.props.PointerProperty(
        type=ParticleExtensionProperties)
    audio_collision_extension_properties: bpy.props.PointerProperty(
        type=AudioCollisionExtensionProperties)
    audio_emitter_extension_properties: bpy.props.PointerProperty(
        type=AudioEmitterExtensionProperties)
    explosion_extension_properties: bpy.props.PointerProperty(
        type=ExplosionExtensionProperties)
    ladder_extension_properties: bpy.props.PointerProperty(
        type=LadderExtensionProperties)
    buoyancy_extension_properties: bpy.props.PointerProperty(
        type=BuoyancyExtensionProperties)
    expression_extension_properties: bpy.props.PointerProperty(
        type=ExpressionExtensionProperties)
    light_shaft_extension_properties: bpy.props.PointerProperty(
        type=LightShaftExtensionProperties)
    spawn_point_extension_properties: bpy.props.PointerProperty(
        type=SpawnPointExtensionProperties)
    spawn_point_override_properties: bpy.props.PointerProperty(
        type=SpawnPointOverrideProperties)
    wind_disturbance_properties: bpy.props.PointerProperty(
        type=WindDisturbanceExtensionProperties)
    proc_object_extension_properties: bpy.props.PointerProperty(
        type=ProcObjectExtensionProperties)


class ExtensionsContainer:
    def new_extension(self, ext_type=None) -> ExtensionProperties:
        # Fallback type if no type is provided or invalid
        if ext_type is None or ext_type not in ExtensionType._value2member_map_:
            ext_type = ExtensionType.DOOR

        item: ExtensionProperties = self.extensions.add()
        item.extension_type = ext_type

        # assign some sane defaults to light shaft and ladder so the gizmos are shown properly
        light_shaft_props = item.light_shaft_extension_properties
        s = 0.1  # half size
        light_shaft_props.cornerA = -s, 0.0, s
        light_shaft_props.cornerB = s, 0.0, s
        light_shaft_props.cornerC = s, 0.0, -s
        light_shaft_props.cornerD = -s, 0.0, -s
        light_shaft_props.length = s * 4.0
        light_shaft_props.direction = 0.0, 1.0, 0.0

        ladder_props = item.ladder_extension_properties
        ladder_props.bottom = 0.0, 0.0, -2.5

        return item

    def delete_selected_extension(self):
        if not self.selected_extension:
            return

        self.extensions.remove(self.extension_index)
        self.extension_index = max(self.extension_index - 1, 0)

    def duplicate_selected_extension(self) -> ExtensionProperties:
        def _copy_property_group(dst: bpy.types.PropertyGroup, src: bpy.types.PropertyGroup):
            if getattr(src, "offset_position", None) is not None:
                # __annotations__ doesn't include `offset_position` as it is from a base class
                # manually copy it instead
                setattr(dst, "offset_position", getattr(src, "offset_position"))

            for prop_name in src.__annotations__.keys():
                src_value = getattr(src, prop_name)
                if isinstance(src_value, bpy.types.PropertyGroup):
                    _copy_property_group(getattr(dst, prop_name), src_value)
                else:
                    setattr(dst, prop_name, src_value)

        src_ext = self.selected_extension
        if not src_ext:
            return None

        new_ext: ExtensionProperties = self.extensions.add()
        _copy_property_group(new_ext, src_ext)
        self.extension_index = len(self.extensions) - 1
        return new_ext

    extensions: bpy.props.CollectionProperty(type=ExtensionProperties, name="Extensions")
    extension_index: bpy.props.IntProperty(name="Extension")

    @property
    def selected_extension(self) -> Union[ExtensionProperties, None]:
        return get_list_item(self.extensions, self.extension_index)
