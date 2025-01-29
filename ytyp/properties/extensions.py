from bpy.types import (
    Object,
    Context,
    UILayout,
    PropertyGroup,
)
from bpy.props import (
    BoolProperty,
    EnumProperty,
    IntProperty,
    FloatProperty,
    FloatVectorProperty,
    StringProperty,
    PointerProperty,
    CollectionProperty,
)
from mathutils import Vector
from typing import Union, Optional, TYPE_CHECKING
from collections.abc import Iterator
from enum import Enum, IntEnum
from ...tools.utils import get_list_item
from ...ydr.light_flashiness import Flashiness, LightFlashinessEnumItems

if TYPE_CHECKING:
    from .ytyp import ArchetypeProperties


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
    LIGHT_EFFECT = "CExtensionDefLightEffect"


def ExtensionTypeEnumItems(self, context: Optional[Context]):
    # Using a function because the icons are only available after register() is executed
    try:
        return ExtensionTypeEnumItems._backing
    except AttributeError:
        from ...icons import icon
        ExtensionTypeEnumItems._backing = (
            (ExtensionType.DOOR, "Door", "", icon("extension_door"), 0),
            (ExtensionType.PARTICLE, "Particle", "", icon("extension_particle_effect"), 1),
            (ExtensionType.AUDIO_COLLISION, "Audio Collision Settings", "", icon("extension_audio_collision_settings"), 2),
            (ExtensionType.AUDIO_EMITTER, "Audio Emitter", "", icon("extension_audio_emitter"), 3),
            (ExtensionType.EXPLOSION_EFFECT, "Explosion Effect", "", icon("extension_explosion_effect"), 4),
            (ExtensionType.LADDER, "Ladder", "", icon("extension_ladder"), 5),
            (ExtensionType.BUOYANCY, "Buoyancy", "", icon("extension_buoyancy"), 6),
            (ExtensionType.LIGHT_SHAFT, "Light Shaft", "", icon("extension_light_shaft"), 7),
            (ExtensionType.SPAWN_POINT, "Spawn Point", "", icon("extension_spawn_point"), 8),
            (ExtensionType.SPAWN_POINT_OVERRIDE, "Spawn Point Override", "", icon("extension_spawn_point_override"), 9),
            (ExtensionType.WIND_DISTURBANCE, "Wind Disturbance", "", icon("extension_wind_disturbance"), 10),
            (ExtensionType.PROC_OBJECT, "Procedural Object", "", icon("extension_proc_object"), 11),
            (ExtensionType.EXPRESSION, "Expression", "", icon("extension_expression"), 12),
            (ExtensionType.LIGHT_EFFECT, "Light Effect", "", "OUTLINER_OB_LIGHT", 13),
        )
        return ExtensionTypeEnumItems._backing


def ExtensionTypeForArchetypesEnumItems(self, context: Optional[Context]):
    try:
        return ExtensionTypeForArchetypesEnumItems._backing
    except AttributeError:
        ExtensionTypeForArchetypesEnumItems._backing = tuple(e for e in ExtensionTypeEnumItems(self, context) if e[0] in {
            ExtensionType.PARTICLE,
            ExtensionType.AUDIO_COLLISION,
            ExtensionType.AUDIO_EMITTER,
            ExtensionType.EXPLOSION_EFFECT,
            ExtensionType.LADDER,
            ExtensionType.BUOYANCY,
            ExtensionType.LIGHT_SHAFT,
            ExtensionType.SPAWN_POINT,
            ExtensionType.WIND_DISTURBANCE,
            ExtensionType.PROC_OBJECT,
            ExtensionType.EXPRESSION,
        })
        return ExtensionTypeForArchetypesEnumItems._backing


def ExtensionTypeForEntitiesEnumItems(self, context: Optional[Context]):
    try:
        return ExtensionTypeForEntitiesEnumItems._backing
    except AttributeError:
        ExtensionTypeForEntitiesEnumItems._backing = tuple(e for e in ExtensionTypeEnumItems(self, context) if e[0] in {
            ExtensionType.DOOR,
            ExtensionType.SPAWN_POINT_OVERRIDE,
            ExtensionType.LIGHT_EFFECT,
            # TODO: ExtensionType.VERLET_CLOTH_CUSTOM_BOUNDS,
        })
        return ExtensionTypeForEntitiesEnumItems._backing


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
    offset_position: FloatVectorProperty(name="Offset Position", subtype="TRANSLATION")

    def find_owner_archetype(self) -> 'ArchetypeProperties':
        id_data = self.id_data
        path = self.path_from_id()
        archetype_path, _ = path.split(".extensions[")
        archetype = id_data.path_resolve(archetype_path)
        return archetype

    def draw_props_pre(self, layout: UILayout):
        pass

    def draw_props(self, layout: UILayout):
        row = layout.row()
        row.prop(self, "offset_position")
        for prop_name in self.__class__.__annotations__:
            row = layout.row()
            row.prop(self, prop_name)

    def draw_props_post(self, layout: UILayout):
        from ..operators.extensions import SOLLUMZ_OT_extension_update_location_from_selected
        layout.separator()
        row = layout.row()
        row.operator(SOLLUMZ_OT_extension_update_location_from_selected.bl_idname)


class ExtensionWithBoneTagMixin:
    def draw_props(self, layout: UILayout):
        row = layout.row()
        row.prop(self, "offset_position")
        for prop_name in self.__class__.__annotations__:
            icon = "NONE"
            if prop_name == "bone_tag":
                icon = "BONE_DATA"
                if self.is_bone_name_available():
                    prop_name = "bone_name"

            row = layout.row()
            row.prop(self, prop_name, icon=icon)

    def is_bone_name_available(self) -> str:
        archetype = self.find_owner_archetype()
        if not archetype.asset or archetype.asset.type != "ARMATURE":
            # No linked object, cannot retrieve the bone name
            return False

        bone_tag = self.bone_tag
        if bone_tag == -1:
            # Not set, name is available but just an empty string
            return True

        armature = archetype.asset.data
        for bone in armature.bones:
            if bone.bone_properties.tag == bone_tag:
                # Bone exists with the tag, we can retrieve the name
                return True

        # No bone found
        return False

    def bone_name_get(self) -> str:
        bone_tag = self.bone_tag
        if bone_tag == -1:
            return ""
        else:
            archetype = self.find_owner_archetype()
            if archetype.asset is None or archetype.asset.type != "ARMATURE":
                assert False, "bone_name_get should not be called when not available! Missing armature!"

            armature = archetype.asset.data
            for bone in armature.bones:
                if bone.bone_properties.tag == bone_tag:
                    return bone.name

            assert False, "bone_name_get should not be called when not available! Missing bone!"

    def bone_name_set(self, value: str):
        bone_name = value.strip()
        if not bone_name:
            self.bone_tag = -1
        else:
            archetype = self.find_owner_archetype()
            if not archetype.asset or archetype.asset.type != "ARMATURE":
                # No linked object, just clear the bone tag
                self.bone_tag = -1
                return

            armature = archetype.asset.data
            bone = armature.bones.get(bone_name, None)
            if not bone:
                # No bone found, just clear the bone tag
                self.bone_tag = -1
                return

            self.bone_tag = bone.bone_properties.tag

    def bone_name_search(self, context: Context, edit_text: str) -> Iterator[str]:
        archetype = self.find_owner_archetype()
        if not archetype.asset or archetype.asset.type != "ARMATURE":
            return

        armature = archetype.asset.data
        for bone in armature.bones:
            yield bone.name

    bone_name: StringProperty(
        name="Bone",
        get=bone_name_get,
        set=bone_name_set,
        search=bone_name_search,
        search_options=set(),
    )


class DoorExtensionProperties(BaseExtensionProperties, PropertyGroup):
    enable_limit_angle: BoolProperty(name="Enable Limit Angle")
    starts_locked: BoolProperty(name="Starts Locked")
    can_break: BoolProperty(name="Can Break")
    limit_angle: FloatProperty(name="Limit Angle")
    door_target_ratio: FloatProperty(name="Door Target Ratio", min=0)
    audio_hash: StringProperty(name="Audio Hash")


class ParticleFxType(IntEnum):
    AMBIENT = 0
    COLLISION = 1
    SHOT = 2
    BREAK = 3
    DESTROY = 4
    RAYFIRE = 6
    IN_WATER = 7

    # Unused, no vanilla props use it. There is some left-over code, but not sure if it is possible to still trigger the
    # conditions for this FX type, seems to require the object to be equipped by a ped playing an ambient clip with
    # "ObjectVfx" clip tags
    ANIM = 5


ParticleFxTypeEnumItems = tuple(label and (enum.name, f"{label} ({enum.value})", desc, enum.value) for enum, label, desc in (
    (
        ParticleFxType.AMBIENT,
        "Ambient",
        "Ambient effect. Valid FX names and specific trigger conditions are defined in the ENTITYFX_AMBIENT_PTFX block "
        "within entityfx.dat"
    ),
    (
        ParticleFxType.COLLISION,
        "Collision",
        "Trigger when this object collides with something. Valid FX names are defined in the ENTITYFX_COLLISION_PTFX "
        "block within entityfx.dat"
    ),
    (
        ParticleFxType.SHOT,
        "Shot",
        "Trigger when this object is shot at. Valid FX names are defined in the ENTITYFX_SHOT_PTFX block within "
        "entityfx.dat"
    ),
    (
        ParticleFxType.BREAK,
        "Break",
        "Fragments only, trigger when this fragment breaks apart. Valid FX names are defined in the "
        "FRAGMENTFX_BREAK_PTFX block within entityfx.dat"

    ),
    (
        ParticleFxType.DESTROY,
        "Destroy",
        "Fragments only, trigger when this fragment is destroyed. Valid FX names are defined in the "
        "FRAGMENTFX_DESTROY_PTFX block within entityfx.dat"

    ),
    (
        ParticleFxType.RAYFIRE,
        "RayFire",
        "Trigger during RayFire animation. Valid FX names are defined in the ENTITYFX_RAYFIRE_PTFX block within "
        "entityfx.dat"
    ),
    (
        ParticleFxType.IN_WATER,
        "In Water",
        "Trigger when this object is in water. Valid FX names are defined in the ENTITYFX_INWATER_PTFX block within "
        "entityfx.dat"
    ),
    (None, None, None),
    (ParticleFxType.ANIM, "Animation (Unused)", ""),
))


class ParticleExtensionProperties(ExtensionWithBoneTagMixin, BaseExtensionProperties, PropertyGroup):
    offset_rotation: FloatVectorProperty(name="Offset Rotation", subtype="EULER")
    fx_name: StringProperty(name="FX Name")
    fx_type: IntProperty(name="FX Type", min=0, max=7, default=ParticleFxType.AMBIENT.value)
    bone_tag: IntProperty(name="Bone Tag", default=-1)
    scale: FloatProperty(name="Scale")
    probability: IntProperty(name="Probability", min=0, max=100, subtype="PERCENTAGE")
    flags: IntProperty(name="Flags", subtype="UNSIGNED")
    color: FloatVectorProperty(name="Tint Color", subtype="COLOR", min=0, max=1, size=4, default=(1, 1, 1, 1))

    # Wrapper properties for better UI
    def fx_type_get(self) -> int:
        return self.fx_type

    def fx_type_set(self, value: int):
        self.fx_type = value

    fx_type_enum: EnumProperty(
        items=ParticleFxTypeEnumItems,
        name="FX Type",
        get=fx_type_get,
        set=fx_type_set,
    )

    def is_flag_set(self, bit: int) -> bool:
        return (self.flags & (1 << bit)) != 0

    def set_flag(self, bit: int, enable: bool):
        if enable:
            self.flags |= 1 << bit
        else:
            self.flags &= ~(1 << bit)

    def flag_get(bit: int):
        return lambda s: s.is_flag_set(bit)

    def flag_set(bit: int):
        return lambda s, v: s.set_flag(bit, v)

    flag_has_tint: BoolProperty(
        name="Enable Tint",
        description="Tint the particle effect with the specified color",
        get=flag_get(0), set=flag_set(0)
    )
    flag_ignore_damaged_model: BoolProperty(
        name="Ignore Damaged Model",
        description="For fragments, do not trigger when using the damaged model. Used by Collision and Shot FX types",
        get=flag_get(1), set=flag_set(1)
    )
    flag_play_on_parent: BoolProperty(
        name="Play on Parent",
        description=(
            "For fragments when breaking, attach the particle to the parent instead of the broken apart piece. Used by "
            "Break FX type"
        ),
        get=flag_get(2), set=flag_set(2)
    )
    flag_only_on_damaged_model: BoolProperty(
        name="Only on Damaged Model",
        description="For fragments, only trigger when using the damaged model. Used by Ambient FX type",
        get=flag_get(3), set=flag_set(3)
    )
    flag_allow_rubber_bullet_shot_fx: BoolProperty(
        name="Allow Rubber Bullet Shot",
        description=(
            "When shot at, trigger even if the damage type of the weapon used is BULLET_RUBBER. Used by Shot FX type"
        ),
        get=flag_get(4), set=flag_set(4)
    )
    flag_allow_electric_bullet_shot_fx: BoolProperty(
        name="Allow Electric Bullet Shot",
        description=(
            "When shot at, trigger even if the damage type of the weapon used is ELECTRIC. Used by Shot FX type"
        ),
        get=flag_get(5), set=flag_set(5)
    )

    def draw_props(self, layout: UILayout):
        for prop_name in (
            "offset_position",
            "offset_rotation",
            "fx_name",
            "fx_type_enum",
            "bone_tag",
            "scale",
            "probability",
        ):
            icon = "NONE"
            row = layout.row()
            if prop_name == "bone_tag":
                icon = "BONE_DATA"
                if self.is_bone_name_available():
                    prop_name = "bone_name"
            row.prop(self, prop_name, icon=icon)

        col = layout.column(heading="Flags", align=True)

        def _prop_enabled(prop_name, enabled):
            row = col.row(align=True)
            row.active = enabled
            row.prop(self, prop_name)
        fx_type = self.fx_type
        is_shot = fx_type == ParticleFxType.SHOT
        _prop_enabled("flag_ignore_damaged_model", is_shot or fx_type == ParticleFxType.COLLISION)
        _prop_enabled("flag_play_on_parent", fx_type == ParticleFxType.BREAK)
        _prop_enabled("flag_only_on_damaged_model", fx_type == ParticleFxType.AMBIENT)
        _prop_enabled("flag_allow_rubber_bullet_shot_fx", is_shot)
        _prop_enabled("flag_allow_electric_bullet_shot_fx", is_shot)

        col = layout.column(heading="Tint Color")
        row = col.row()
        row.prop(self, "flag_has_tint", text="")
        row.prop(self, "color", text="")


class AudioCollisionExtensionProperties(BaseExtensionProperties, PropertyGroup):
    settings: StringProperty(name="Settings")


class AudioEmitterExtensionProperties(BaseExtensionProperties, PropertyGroup):
    offset_rotation: FloatVectorProperty(name="Offset Rotation", subtype="EULER")
    effect_hash: StringProperty(name="Effect Hash")


class ExplosionFxType(IntEnum):
    SHOT_POINT = 0
    BREAK = 1
    DESTROY = 2
    SHOT_OFFSET = 3


ExplosionFxTypeEnumItems = tuple(label and (enum.name, f"{label} ({enum.value})", desc, enum.value) for enum, label, desc in (
    (
        ExplosionFxType.SHOT_POINT,
        "Shot (at impact point)",
        "Trigger when this object is shot at. The explosion will be created at the point where the object was shot"
    ),
    (
        ExplosionFxType.SHOT_OFFSET,
        "Shot (at offset position)",
        "Trigger when this object is shot at. The explosion will be created at the extension offset position"
    ),
    (
        ExplosionFxType.BREAK,
        "Break",
        "Fragments only, trigger when this fragment breaks apart"
    ),
    (
        ExplosionFxType.DESTROY,
        "Destroy",
        "Fragments only, trigger when this fragment is destroyed"
    ),
))


KNOWN_EXPLOSION_NAMES = (
    "exp_tag_air_defence",
    "exp_tag_apcshell",
    "exp_tag_balanced_cannons",
    "exp_tag_barrel",
    "exp_tag_bike",
    "exp_tag_bird_crap",
    "exp_tag_blimp",
    "exp_tag_blimp2",
    "exp_tag_boat",
    "exp_tag_bomb_cluster",
    "exp_tag_bomb_cluster_secondary",
    "exp_tag_bomb_gas",
    "exp_tag_bomb_incendiary",
    "exp_tag_bomb_standard",
    "exp_tag_bomb_standard_wide",
    "exp_tag_bomb_water",
    "exp_tag_bomb_water_secondary",
    "exp_tag_bombushka_cannon",
    "exp_tag_bullet",
    "exp_tag_buriedmine",
    "exp_tag_bzgas",
    "exp_tag_car",
    "exp_tag_dir_flame",
    "exp_tag_dir_flame_explode",
    "exp_tag_dir_gas_canister",
    "exp_tag_dir_steam",
    "exp_tag_dir_water_hydrant",
    "exp_tag_emplauncher_emp",
    "exp_tag_explosiveammo",
    "exp_tag_explosiveammo_shotgun",
    "exp_tag_extinguisher",
    "exp_tag_firework",
    "exp_tag_flare",
    "exp_tag_gas_canister",
    "exp_tag_gas_tank",
    "exp_tag_grenade",
    "exp_tag_grenadelauncher",
    "exp_tag_hi_octane",
    "exp_tag_hunter_barrage",
    "exp_tag_hunter_cannon",
    "exp_tag_mine_underwater",
    "exp_tag_molotov",
    "exp_tag_mortar_kinetic",
    "exp_tag_oppressor2_cannon",
    "exp_tag_orbital_cannon",
    "exp_tag_petrol_pump",
    "exp_tag_pipebomb",
    "exp_tag_plane",
    "exp_tag_plane_rocket",
    "exp_tag_programmablear",
    "exp_tag_propane",
    "exp_tag_proxmine",
    "exp_tag_railgun",
    "exp_tag_railgunxm3",
    "exp_tag_raygun",
    "exp_tag_rctank_rocket",
    "exp_tag_rocket",
    "exp_tag_rogue_cannon",
    "exp_tag_script_drone",
    "exp_tag_script_missile",
    "exp_tag_script_missile_large",
    "exp_tag_ship_destroy",
    "exp_tag_smokegrenade",
    "exp_tag_smokegrenadelauncher",
    "exp_tag_snowball",
    "exp_tag_stickybomb",
    "exp_tag_submarine_big",
    "exp_tag_tanker",
    "exp_tag_tankshell",
    "exp_tag_torpedo",
    "exp_tag_torpedo_underwater",
    "exp_tag_train",
    "exp_tag_truck",
    "exp_tag_valkyrie_cannon",
    "exp_tag_vehicle_bullet",
    "exp_tag_vehiclemine",
    "exp_tag_vehiclemine_emp",
    "exp_tag_vehiclemine_kinetic",
    "exp_tag_vehiclemine_slick",
    "exp_tag_vehiclemine_spike",
    "exp_tag_vehiclemine_tar",
)


class ExplosionExtensionProperties(ExtensionWithBoneTagMixin, BaseExtensionProperties, PropertyGroup):
    offset_rotation: FloatVectorProperty(name="Offset Rotation", subtype="EULER")
    explosion_name: StringProperty(
        name="Explosion Name",
        description=(
            "Name of the explosion to use, as defined in explosion.ymt or explosion.meta. If the explosion is marked "
            "as 'minorExplosion', it will trigger each time the conditions are met (e.g. each time the object is shot "
            "when using the Shot explosion type); otherwise, only once"
        ),
        search=lambda s, c, v: KNOWN_EXPLOSION_NAMES,
        search_options={"SUGGESTION"}
    )
    bone_tag: IntProperty(name="Bone Tag", default=-1)
    explosion_type: IntProperty(name="Explosion Type", min=0, max=3, default=ExplosionFxType.SHOT_POINT.value)
    flags: IntProperty(name="Flags", subtype="UNSIGNED")

    # Wrapper properties for better UI
    def explosion_type_get(self) -> int:
        return self.explosion_type

    def explosion_type_set(self, value: int):
        self.explosion_type = value

    explosion_type_enum: EnumProperty(
        items=ExplosionFxTypeEnumItems,
        name="Explosion Type",
        get=explosion_type_get,
        set=explosion_type_set,
    )

    def is_flag_set(self, bit: int) -> bool:
        return (self.flags & (1 << bit)) != 0

    def set_flag(self, bit: int, enable: bool):
        if enable:
            self.flags |= 1 << bit
        else:
            self.flags &= ~(1 << bit)

    def flag_get(bit: int):
        return lambda s: s.is_flag_set(bit)

    def flag_set(bit: int):
        return lambda s, v: s.set_flag(bit, v)

    flag_ignore_damaged_model: BoolProperty(
        name="Ignore Damaged Model",
        description="For fragments, do not trigger when using the damaged model. Used by Shot explosion type",
        get=flag_get(1), set=flag_set(1)
    )
    flag_play_on_parent: BoolProperty(
        name="Play on Parent",
        description=(
            "For fragments when breaking, attach the explosion to the parent instead of the broken apart piece. Used by "
            "Break explosion type"
        ),
        get=flag_get(2), set=flag_set(2)
    )
    flag_allow_rubber_bullet_shot_fx: BoolProperty(
        name="Allow Rubber Bullet Shot",
        description=(
            "When shot at, trigger even if the damage type of the weapon used is BULLET_RUBBER. Used by Shot explosion type"
        ),
        get=flag_get(4), set=flag_set(4)
    )
    flag_allow_electric_bullet_shot_fx: BoolProperty(
        name="Allow Electric Bullet Shot",
        description=(
            "When shot at, trigger even if the damage type of the weapon used is ELECTRIC. Used by Shot explosion type"
        ),
        get=flag_get(5), set=flag_set(5)
    )

    def draw_props(self, layout: UILayout):
        for prop_name in (
            "offset_position",
            "offset_rotation",
            "explosion_name",
            "explosion_type_enum",
            "bone_tag",
        ):
            icon = "NONE"
            row = layout.row()
            if prop_name == "bone_tag":
                icon = "BONE_DATA"
                if self.is_bone_name_available():
                    prop_name = "bone_name"
            row.prop(self, prop_name, icon=icon)

        col = layout.column(heading="Flags", align=True)

        def _prop_enabled(prop_name, enabled):
            row = col.row(align=True)
            row.active = enabled
            row.prop(self, prop_name)
        exp_type = self.explosion_type
        is_shot = exp_type == ExplosionFxType.SHOT_POINT or exp_type == ExplosionFxType.SHOT_OFFSET
        _prop_enabled("flag_ignore_damaged_model", is_shot)
        _prop_enabled("flag_play_on_parent", exp_type == ExplosionFxType.BREAK)
        _prop_enabled("flag_allow_rubber_bullet_shot_fx", is_shot)
        _prop_enabled("flag_allow_electric_bullet_shot_fx", is_shot)


class LadderExtensionProperties(BaseExtensionProperties, PropertyGroup):
    bottom: FloatVectorProperty(name="Bottom", subtype="TRANSLATION")
    top: FloatVectorProperty(name="Top", subtype="TRANSLATION")
    normal: FloatVectorProperty(name="Normal", subtype="TRANSLATION")
    material_type: StringProperty(name="Material Type", default="METAL_SOLID_LADDER")
    template: StringProperty(name="Template", default="default")
    can_get_off_at_top: BoolProperty(name="Can Get Off At Top", default=True)
    can_get_off_at_bottom: BoolProperty(name="Can Get Off At Bottom", default=True)

    def draw_props_post(self, layout: UILayout):
        super().draw_props_post(layout)

        from ..operators.extensions import SOLLUMZ_OT_update_bottom_from_selected
        row = layout.row()
        row.operator(SOLLUMZ_OT_update_bottom_from_selected.bl_idname)


class BuoyancyExtensionProperties(BaseExtensionProperties, PropertyGroup):
    # No additional properties
    pass


class ExpressionExtensionProperties(BaseExtensionProperties, PropertyGroup):
    expression_dictionary_name: StringProperty(name="Expression Dictionary Name")
    expression_name: StringProperty(name="Expression Name")
    creature_metadata_name: StringProperty(name="Creature Metadata Name")
    initialize_on_collision: BoolProperty(name="Initialize on Collision")


class LightShaftExtensionProperties(BaseExtensionProperties, PropertyGroup):
    density_type: EnumProperty(items=LightShaftDensityTypeEnumItems, name="Density Type")
    volume_type: EnumProperty(items=LightShaftVolumeTypeEnumItems, name="Volume Type")
    scale_by_sun_intensity: BoolProperty(name="Scale by Sun Intensity")
    direction_amount: FloatProperty(name="Direction Amount")
    length: FloatProperty(name="Length")
    color: FloatVectorProperty(
        name="Color", subtype="COLOR", min=0, max=1, size=4, default=(1, 1, 1, 1))
    intensity: FloatProperty(name="Intensity")
    flashiness: EnumProperty(name="Flashiness", items=LightFlashinessEnumItems,
                                       default=Flashiness.CONSTANT.name)
    flags: IntProperty(name="Flags")
    fade_in_time_start: FloatProperty(name="Fade In Time Start")
    fade_in_time_end: FloatProperty(name="Fade In Time End")
    fade_out_time_start: FloatProperty(name="Fade Out Time Start")
    fade_out_time_end: FloatProperty(name="Fade Out Time End")
    fade_distance_start: FloatProperty(name="Fade Distance Start")
    fade_distance_end: FloatProperty(name="Fade Distance End")
    softness: FloatProperty(name="Softness")
    cornerA: FloatVectorProperty(
        name="Corner A", subtype="TRANSLATION")
    cornerB: FloatVectorProperty(
        name="Corner B", subtype="TRANSLATION")
    cornerC: FloatVectorProperty(
        name="Corner C", subtype="TRANSLATION")
    cornerD: FloatVectorProperty(
        name="Corner D", subtype="TRANSLATION")
    direction: FloatVectorProperty(
        name="Direction", subtype="XYZ")

    # HACK: import/export iterates the annotations matching properties here with properties in the XML class,
    # if they don't match it prints a warning. This is not really flexible when we need a different layout
    # is the property group than in the XML. Often needed if we need some custom UI elements, like checkboxes
    # for the flags. For now, properties in this set will be skipped during import/export.
    # TODO: refactor extensions import/export/UI to be manually defined instead of depending on the property
    # group layout? More code but would give use more flexibility.
    ignored_in_import_export = {"flag_0", "flag_1", "flag_4", "flag_5", "flag_6"}

    def is_flag_set(self, bit: int) -> bool:
        return (self.flags & (1 << bit)) != 0

    def set_flag(self, bit: int, enable: bool):
        if enable:
            self.flags |= 1 << bit
        else:
            self.flags &= ~(1 << bit)

    def flag_get(bit: int):
        if bit == 5:
            # This flag has the same meaning as scale_by_sun_intensity bool, use the getter an setter
            # to keep them in sync. Ideally we would keep only the flag, but we need the same layout
            # as the XML for export (see above)
            return lambda s: s.is_flag_set(bit) or s.scale_by_sun_intensity
        else:
            return lambda s: s.is_flag_set(bit)

    def flag_set(bit: int):
        if bit == 5:
            def f(s, v):
                s.set_flag(bit, v)
                s.scale_by_sun_intensity = v
            return f
        else:
            return lambda s, v: s.set_flag(bit, v)

    # Using getters and setters because there isn't a nice way to have a list of checkboxes with EnumProperty and ENUM_FLAG option :(
    # BoolVectorProperty isn't a good option either because there are unused bits.
    flag_0: BoolProperty(name="Use Sun Direction", description="", get=flag_get(0), set=flag_set(0))
    flag_1: BoolProperty(name="Use Sun Color", description="", get=flag_get(1), set=flag_set(1))
    flag_4: BoolProperty(name="Scale By Sun Color", description="", get=flag_get(4), set=flag_set(4))
    flag_5: BoolProperty(name="Scale By Sun Intensity", description="", get=flag_get(5), set=flag_set(5))
    flag_6: BoolProperty(name="Draw In Front And Behind", description="", get=flag_get(6), set=flag_set(6))

    def draw_props_pre(self, layout: UILayout):
        from ..operators.extensions import (
            SOLLUMZ_OT_update_corner_a_location,
            SOLLUMZ_OT_update_corner_b_location,
            SOLLUMZ_OT_update_corner_c_location,
            SOLLUMZ_OT_update_corner_d_location,
            SOLLUMZ_OT_extension_update_location_from_selected,
            SOLLUMZ_OT_calculate_light_shaft_center_offset_location,
            SOLLUMZ_OT_update_light_shaft_direction,
        )
        row = layout.row()
        row.operator(SOLLUMZ_OT_extension_update_location_from_selected.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_update_corner_a_location.bl_idname)
        row.operator(SOLLUMZ_OT_update_corner_b_location.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_update_corner_d_location.bl_idname)
        row.operator(SOLLUMZ_OT_update_corner_c_location.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_update_light_shaft_direction.bl_idname)
        layout.separator()
        row = layout.row()
        row.operator(SOLLUMZ_OT_calculate_light_shaft_center_offset_location.bl_idname)
        layout.separator()

    def draw_props(self, layout: UILayout):
        row = layout.row()
        row.prop(self, "offset_position")
        for prop_name in self.__class__.__annotations__:
            if prop_name == "flags":
                # draw individual checkboxes for the bits instead of the flags IntProperty
                col = layout.column(heading="Flags")
                col.prop(self, "flag_0")
                col.prop(self, "flag_1")
                col.prop(self, "flag_4")
                col.prop(self, "flag_5")
                col.prop(self, "flag_6")
            elif (prop_name.startswith("flag_") or prop_name == "scale_by_sun_intensity"):
                # skip light shaft flag props, drawn above
                # and skip scale_by_sun_intensity because it is the same as flag_5
                continue
            else:
                if prop_name in {"direction_amount", "cornerA"}:
                    layout.separator()
                row = layout.row()
                row.prop(self, prop_name)

    def draw_props_post(self, layout: UILayout):
        pass


class SpawnPointExtensionProperties(BaseExtensionProperties, PropertyGroup):
    offset_rotation: FloatVectorProperty(name="Offset Rotation", subtype="EULER")
    spawn_type: StringProperty(name="Spawn Type")
    ped_type: StringProperty(name="Ped Type")
    group: StringProperty(name="Group")
    interior: StringProperty(name="Interior")
    required_map: StringProperty(name="Required Map")
    probability: FloatProperty(name="Probability")
    time_till_ped_leaves: FloatProperty(name="Time Till Ped Leaves")
    radius: FloatProperty(name="Radius")
    start: FloatProperty(name="Start")
    end: FloatProperty(name="End")
    high_pri: BoolProperty(name="High Priority")
    extended_range: BoolProperty(name="Extended Range")
    short_range: BoolProperty(name="Short Range")

    # TODO: Use enums
    available_in_mp_sp: StringProperty(name="Available in MP/SP")
    scenario_flags: StringProperty(name="Scenario Flags")


class SpawnPointOverrideProperties(BaseExtensionProperties, PropertyGroup):
    scenario_type: StringProperty(name="Scenario Type")
    itime_start_override: FloatProperty(name="iTime Start Override")
    itime_end_override: FloatProperty(name="iTime End Override")
    group: StringProperty(name="Group")
    model_set: StringProperty(name="Model Set")
    radius: FloatProperty(name="Radius")
    time_till_ped_leaves: FloatProperty(name="Time Till Ped Leaves")

    # TODO: Use enums
    available_in_mp_sp: StringProperty(name="Available in MP/SP")
    scenario_flags: StringProperty(name="Scenario Flags")


class WindDisturbanceExtensionProperties(ExtensionWithBoneTagMixin, BaseExtensionProperties, PropertyGroup):
    offset_rotation: FloatVectorProperty(name="Offset Rotation", subtype="EULER")
    disturbance_type: IntProperty(name="Disturbance Type")
    bone_tag: IntProperty(name="Bone Tag", default=-1)
    size: FloatVectorProperty(name="Size", size=4, subtype="XYZ")
    strength: FloatProperty(name="Strength")
    flags: IntProperty(name="Flags")


class ProcObjectExtensionProperties(BaseExtensionProperties, PropertyGroup):
    radius_inner: FloatProperty(name="Radius Inner")
    radius_outer: FloatProperty(name="Radius Outer")
    spacing: FloatProperty(name="Spacing")
    min_scale: FloatProperty(name="Min Scale")
    max_scale: FloatProperty(name="Max Scale")
    min_scale_z: FloatProperty(name="Min Scale Z")
    max_scale_z: FloatProperty(name="Max Scale Z")
    min_z_offset: FloatProperty(name="Min Z Offset")
    max_z_offset: FloatProperty(name="Max Z Offset")
    object_hash: IntProperty(name="Object Hash", subtype="UNSIGNED")
    flags: IntProperty(name="Flags", subtype="UNSIGNED")


class LightEffectExtensionProperties(BaseExtensionProperties, PropertyGroup):
    ignored_in_import_export = {"parent_obj"}

    linked_lights_object: PointerProperty(name="Linked Lights", type=Object)

    def draw_props_post(self, layout: UILayout):
        from ..operators.extensions import SOLLUMZ_OT_light_effect_create_lights_from_entity
        layout.separator()
        row = layout.row()
        row.operator(SOLLUMZ_OT_light_effect_create_lights_from_entity.bl_idname)


class ExtensionProperties(PropertyGroup):
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
        elif self.extension_type == ExtensionType.LIGHT_EFFECT:
            return self.light_effect_properties

    def translate(self, offset: Vector):
        props = self.get_properties()

        if self.extension_type == ExtensionType.LADDER:
            props.top += offset
            props.bottom.xy = props.top.xy
            props.bottom.z = min(props.bottom.z, props.top.z)

            props.offset_position = props.top
        else:
            props.offset_position += offset

            if self.extension_type == ExtensionType.LIGHT_SHAFT:
                # move light shaft corners along with the offset_position
                for c in (props.cornerA, props.cornerB, props.cornerC, props.cornerD):
                    c += offset

    def _get_extension_type_int(self) -> int:
        return self["extension_type"]  # using indexer to get the integer value instead of a string

    def _set_extension_type_int(self, value: int):
        self["extension_type"] = value  # using indexer to set the integer value directly

    extension_type: EnumProperty(name="Type", items=ExtensionTypeEnumItems)
    extension_type_for_archetypes: EnumProperty(
        name="Type", items=ExtensionTypeForArchetypesEnumItems,
        get=_get_extension_type_int, set=_set_extension_type_int,
    )
    extension_type_for_entities: EnumProperty(
        name="Type", items=ExtensionTypeForEntitiesEnumItems,
        get=_get_extension_type_int, set=_set_extension_type_int,
    )

    name: StringProperty(name="Name", default="Extension")

    door_extension_properties: PointerProperty(type=DoorExtensionProperties)
    particle_extension_properties: PointerProperty(type=ParticleExtensionProperties)
    audio_collision_extension_properties: PointerProperty(type=AudioCollisionExtensionProperties)
    audio_emitter_extension_properties: PointerProperty(type=AudioEmitterExtensionProperties)
    explosion_extension_properties: PointerProperty(type=ExplosionExtensionProperties)
    ladder_extension_properties: PointerProperty(type=LadderExtensionProperties)
    buoyancy_extension_properties: PointerProperty(type=BuoyancyExtensionProperties)
    expression_extension_properties: PointerProperty(type=ExpressionExtensionProperties)
    light_shaft_extension_properties: PointerProperty(type=LightShaftExtensionProperties)
    spawn_point_extension_properties: PointerProperty(type=SpawnPointExtensionProperties)
    spawn_point_override_properties: PointerProperty(type=SpawnPointOverrideProperties)
    wind_disturbance_properties: PointerProperty(type=WindDisturbanceExtensionProperties)
    proc_object_extension_properties: PointerProperty(type=ProcObjectExtensionProperties)
    light_effect_properties: PointerProperty(type=LightEffectExtensionProperties)


class ExtensionsContainer:
    IS_ARCHETYPE = None  # True = archetype, False = entity
    DEFAULT_EXTENSION_TYPE = None

    def new_extension(self, ext_type=None) -> ExtensionProperties:
        # Fallback type if no type is provided or invalid
        if ext_type is None or ext_type not in ExtensionType._value2member_map_:
            assert self.DEFAULT_EXTENSION_TYPE is not None
            ext_type = self.DEFAULT_EXTENSION_TYPE

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
        def _copy_property_group(dst: PropertyGroup, src: PropertyGroup):
            if getattr(src, "offset_position", None) is not None:
                # __annotations__ doesn't include `offset_position` as it is from a base class
                # manually copy it instead
                setattr(dst, "offset_position", getattr(src, "offset_position"))

            for prop_name in src.__annotations__.keys():
                if prop_name in {"extension_type_for_archetypes", "extension_type_for_entities"}:
                    # wrappers around "extension_type", skip them
                    continue

                src_value = getattr(src, prop_name)
                if isinstance(src_value, PropertyGroup):
                    _copy_property_group(getattr(dst, prop_name), src_value)
                else:
                    setattr(dst, prop_name, src_value)

        src_ext = self.selected_extension
        if not src_ext:
            return None

        new_ext: ExtensionProperties = self.extensions.add()
        # NOTE: we get the selected extension again because modifying a parent collection can re-allocate its property
        # groups, so their references become invalid and might cause use-after-free crashes.
        src_ext = self.selected_extension
        _copy_property_group(new_ext, src_ext)
        self.extension_index = len(self.extensions) - 1
        return new_ext

    extensions: CollectionProperty(type=ExtensionProperties, name="Extensions")
    extension_index: IntProperty(name="Extension")

    @property
    def selected_extension(self) -> Union[ExtensionProperties, None]:
        return get_list_item(self.extensions, self.extension_index)
