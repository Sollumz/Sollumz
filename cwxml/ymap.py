from abc import ABC as AbstractClass, abstractmethod
from xml.etree import ElementTree as ET
from .element import (
    AttributeProperty,
    ElementTree,
    FlagsProperty,
    ListProperty,
    QuaternionProperty,
    TextProperty,
    TextListProperty,
    ValueProperty,
    VectorProperty
)


class YMAP:

    @staticmethod
    def from_xml_file(filepath):
        return CMapData.from_xml_file(filepath)

    @staticmethod
    def write_xml(cmap_data, filepath):
        return cmap_data.write_xml(filepath)


class Extension(ElementTree, AbstractClass):
    tag_name = "Item"

    @property
    @abstractmethod
    def type(self) -> str:
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.type = AttributeProperty("type", self.type)
        self.name = TextProperty("name")
        self.offset_position = VectorProperty("offsetPosition")


class LightInstance(ElementTree):
    # Have to define another light class because the tag names are all different in entity extensions
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.position = TextListProperty("posn")
        self.color = TextListProperty("colour")
        self.flashiness = ValueProperty("flashiness")
        self.intensity = ValueProperty("intensity")
        self.flags = ValueProperty("flags")
        self.bone_id = ValueProperty("boneTag")
        self.light_type = ValueProperty("lightType")
        self.group_id = ValueProperty("groupId")
        self.time_flags = ValueProperty("timeFlags")
        self.falloff = ValueProperty("falloff")
        self.falloff_exponent = ValueProperty("falloffExponent")
        self.culling_plane = TextListProperty("cullingPlane")
        self.shadow_blur = ValueProperty("shadowBlur")
        self.padding1 = ValueProperty("padding1")
        self.padding2 = ValueProperty("padding2")
        self.padding3 = ValueProperty("padding3")
        self.volume_intensity = ValueProperty("volIntensity")
        self.volume_size_scale = ValueProperty("volSizeScale")
        self.volume_outer_color = TextListProperty("volOuterColour")
        self.light_hash = ValueProperty("lightHash")
        self.volume_outer_intensity = ValueProperty("volOuterIntensity")
        self.corona_size = ValueProperty("coronaSize")
        self.volume_outer_exponent = ValueProperty("volOuterExponent")
        self.light_fade_distance = ValueProperty("lightFadeDistance")
        self.shadow_fade_distance = ValueProperty("shadowFadeDistance")
        self.specular_fade_distance = ValueProperty("specularFadeDistance")
        self.volumetric_fade_distance = ValueProperty("volumetricFadeDistance")
        self.shadow_near_clip = ValueProperty("shadowNearClip")
        self.corona_intensity = ValueProperty("coronaIntensity")
        self.corona_z_bias = ValueProperty("coronaZBias")
        self.direction = TextListProperty("direction")
        self.tangent = TextListProperty("tangent")
        self.cone_inner_angle = ValueProperty("coneInnerAngle")
        self.cone_outer_angle = ValueProperty("coneOuterAngle")
        self.extents = TextListProperty("extents")
        self.projected_texture_key = ValueProperty("projectedTextureKey")


class LightInstancesListProperty(ListProperty):
    list_type = LightInstance
    tag_name = "instances"

    def __init__(self, tag_name=None, value=None):
        super().__init__(LightInstancesListProperty.tag_name, value=value)
        self.item_type = AttributeProperty("itemType", "CLightAttrDef")


class ExtensionParticleEffect(Extension):
    type = "CExtensionDefParticleEffect"

    def __init__(self):
        super().__init__()
        self.offset_rotation = QuaternionProperty("offsetRotation")
        self.fx_name = TextProperty("fxName")
        self.fx_type = ValueProperty("fxType")
        self.bone_tag = ValueProperty("boneTag")
        self.scale = ValueProperty("scale")
        self.probability = ValueProperty("probability")
        self.flags = ValueProperty("flags")
        self.color = ValueProperty("color", "0xFFFFFFFF")


class ExtensionLightEffect(Extension):
    type = "CExtensionDefLightEffect"

    def __init__(self):
        super().__init__()
        self.instances = LightInstancesListProperty()


class ExtensionAudioCollision(Extension):
    type = "CExtensionDefAudioCollisionSettings"

    def __init__(self):
        super().__init__()
        self.settings = TextProperty("settings")


class ExtensionAudioEmitter(Extension):
    type = "CExtensionDefAudioEmitter"

    def __init__(self):
        super().__init__()
        self.offset_rotation = QuaternionProperty("offsetRotation")
        self.effect_hash = TextProperty("effectHash")


class ExtensionExplosionEffect(Extension):
    type = "CExtensionDefExplosionEffect"

    def __init__(self):
        super().__init__()
        self.offset_rotation = QuaternionProperty("offsetRotation")
        self.explosion_name = TextProperty("explosionName")
        self.bone_tag = ValueProperty("boneTag")
        self.explosion_tag = ValueProperty("explosionTag")
        self.explosion_type = ValueProperty("explosionType")
        self.flags = ValueProperty("flags")


class ExtensionLadder(Extension):
    type = "CExtensionDefLadder"

    def __init__(self):
        super().__init__()
        self.bottom = VectorProperty("bottom")
        self.top = VectorProperty("top")
        self.normal = VectorProperty("normal")
        self.material_type = TextProperty("materialType")
        self.template = TextProperty("template")
        self.can_get_off_at_top = ValueProperty("canGetOffAtTop", True)
        self.can_get_off_at_bottom = ValueProperty("canGetOffAtBottom", True)


class ExtensionBuoyancy(Extension):
    type = "CExtensionDefBuoyancy"


class ExtensionExpression(Extension):
    type = "CExtensionDefExpression"

    def __init__(self):
        super().__init__()
        self.expression_dictionary_name = TextProperty(
            "expressionDictionaryName")
        self.expression_name = TextProperty("expressionName")
        self.create_metadata_name = TextProperty("creatureMetadataname")
        self.intialize_on_collision = ValueProperty(
            "initialiseOnCollision", False)


class ExtensionLightShaft(Extension):
    type = "CExtensionDefLightShaft"

    def __init__(self):
        super().__init__()
        self.cornerA = VectorProperty("cornerA")
        self.cornerB = VectorProperty("cornerB")
        self.cornerC = VectorProperty("cornerC")
        self.cornerD = VectorProperty("cornerD")
        self.direction = VectorProperty("direction")
        self.direction_amount = ValueProperty("directionAmount")
        self.length = ValueProperty("length")
        self.fade_in_time_start = ValueProperty("fadeInTimeStart")
        self.fade_in_time_end = ValueProperty("fadeInTimeEnd")
        self.fade_out_time_start = ValueProperty("fadeOutTimeStart")
        self.fade_out_time_end = ValueProperty("fadeOutTimeEnd")
        self.fade_distance_start = ValueProperty("fadeDistanceStart")
        self.fade_distance_end = ValueProperty("fadeDistanceEnd")
        self.color = ValueProperty("color")
        self.intensity = ValueProperty("intensity")
        self.flashiness = ValueProperty("flashiness")
        self.flags = ValueProperty("flags")
        # CExtensionDefLightShaftDensityType
        self.density_type = TextProperty("densityType")
        # CExtensionDefLightShaftVolumeType
        self.volume_type = TextProperty("volumeType")
        self.softness = ValueProperty("softness")
        self.scale_by_sun_intensity = ValueProperty(
            "scaleBySunIntensity", False)


class ExtensionDoor(Extension):
    type = "CExtensionDefDoor"

    def __init__(self):
        super().__init__()
        self.enable_limit_angle = ValueProperty("enableLimitAngle", False)
        self.starts_locked = ValueProperty("startsLocked", False)
        self.can_break = ValueProperty("canBreak", False)
        self.limit_angle = ValueProperty("limitAngle", False)
        self.door_target_ratio = ValueProperty("doorTargetRatio")
        self.audio_hash = TextProperty("audioHash")


class ExtensionSpawnPoint(Extension):
    type = "CExtensionDefSpawnPoint"

    def __init__(self):
        super().__init__()
        self.offset_rotation = QuaternionProperty("offsetRotation")
        self.spawn_type = TextProperty("spawnType")
        self.ped_type = TextProperty("pedType")
        self.group = TextProperty("group")
        self.interior = TextProperty("interior")
        self.required_imap = TextProperty("required_imap")
        # CSpawnPoint__AvailabilityMpSp
        self.available_in_mp_sp = TextProperty("availableInMpSp")
        self.probability = ValueProperty("probability")
        self.time_till_ped_leaves = ValueProperty("timeTillPedLeaves")
        self.radius = ValueProperty("radius")
        self.start = ValueProperty("start")
        self.end = ValueProperty("end")
        # CScenarioPointFlags__Flags
        self.scenario_flags = FlagsProperty("flags")
        self.high_pri = ValueProperty("highPri", False)
        self.extended_range = ValueProperty("extendedRange", False)
        self.short_range = ValueProperty("shortRange", False)


class ExtensionSpawnPointOverride(Extension):
    type = "CExtensionDefSpawnPointOverride"

    def __init__(self):
        super().__init__()
        self.scenario_type = TextProperty("ScenarioType")
        self.itime_start_override = ValueProperty("iTimeStartOverride")
        self.itime_end_override = ValueProperty("iTimeEndOverride")
        self.group = TextProperty("Group")
        self.model_set = TextProperty("ModelSet")
        self.available_in_mp_sp = TextProperty("AvailabilityInMpSp")
        self.scenario_flags = FlagsProperty()
        self.radius = TextProperty("Radius")
        self.time_till_ped_leaves = ValueProperty("TimeTillPedLeaves")


class ExtensionWindDisturbance(Extension):
    type = "CExtensionDefWindDisturbance"

    def __init__(self):
        super().__init__()
        self.offset_rotation = QuaternionProperty("offsetRotation")
        self.disturbance_type = ValueProperty("disturbanceType")
        self.bone_tag = ValueProperty("boneTag")
        self.size = QuaternionProperty("size")
        self.strength = ValueProperty("strength")
        self.flags = ValueProperty("flags")


class ExtensionProcObject(Extension):
    type = "CExtensionProcObject"

    def __init__(self):
        super().__init__()
        self.radius_inner = ValueProperty("radiusInner")
        self.radius_outer = ValueProperty("radiusOuter")
        self.spacing = ValueProperty("spacing")
        self.min_scale = ValueProperty("minScale")
        self.max_scale = ValueProperty("maxScale")
        self.min_scaleZ = ValueProperty("minScaleZ")
        self.max_scaleZ = ValueProperty("maxScaleZ")
        self.min_z_offset = ValueProperty("minZOffset")
        self.max_z_offset = ValueProperty("maxZOffset")
        self.object_hash = ValueProperty("objectHash")
        self.flags = ValueProperty("flags")


class ExtensionsListProperty(ListProperty):
    list_type = Extension
    tag_name = "extensions"

    @staticmethod
    def from_xml(element: ET.Element):
        new = ExtensionsListProperty()

        for child in element.iter():
            if "type" in child.attrib:
                ext_type = child.get("type")
                if ext_type == ExtensionLightEffect.type:
                    new.value.append(ExtensionLightEffect.from_xml(child))
                elif ext_type == ExtensionParticleEffect.type:
                    new.value.append(ExtensionParticleEffect.from_xml(child))
                elif ext_type == ExtensionAudioCollision.type:
                    new.value.append(ExtensionAudioCollision.from_xml(child))
                elif ext_type == ExtensionAudioEmitter.type:
                    new.value.append(ExtensionAudioEmitter.from_xml(child))
                elif ext_type == ExtensionExplosionEffect.type:
                    new.value.append(ExtensionExplosionEffect.from_xml(child))
                elif ext_type == ExtensionLadder.type:
                    new.value.append(ExtensionLadder.from_xml(child))
                elif ext_type == ExtensionBuoyancy.type:
                    new.value.append(ExtensionBuoyancy.from_xml(child))
                elif ext_type == ExtensionExpression.type:
                    new.value.append(ExtensionExpression.from_xml(child))
                elif ext_type == ExtensionLightShaft.type:
                    new.value.append(ExtensionLightShaft.from_xml(child))
                elif ext_type == ExtensionDoor.type:
                    new.value.append(ExtensionDoor.from_xml(child))
                elif ext_type == ExtensionSpawnPoint.type:
                    new.value.append(ExtensionSpawnPoint.from_xml(child))
                elif ext_type == ExtensionSpawnPointOverride.type:
                    new.value.append(
                        ExtensionSpawnPointOverride.from_xml(child))
                elif ext_type == ExtensionWindDisturbance.type:
                    new.value.append(ExtensionWindDisturbance.from_xml(child))
                elif ext_type == ExtensionProcObject.type:
                    new.value.append(ExtensionProcObject.from_xml(child))
        return new


class EntityItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = AttributeProperty("type", "CEntityDef")
        self.archetype_name = TextProperty("archetypeName")
        self.flags = ValueProperty("flags", 0)
        self.guid = ValueProperty("guid", 0)
        self.position = VectorProperty("position")
        self.rotation = QuaternionProperty("rotation")
        self.scale_xy = ValueProperty("scaleXY", 0)
        self.scale_z = ValueProperty("scaleZ", 0)
        self.parent_index = ValueProperty("parentIndex", 0)
        self.lod_dist = ValueProperty("lodDist", 0)
        self.child_lod_dist = ValueProperty("childLodDist", 0)
        self.lod_level = TextProperty("lodLevel")
        self.num_children = ValueProperty("numChildren", 0)
        self.priority_level = TextProperty("priorityLevel")
        self.extensions = ExtensionsListProperty()
        self.ambient_occlusion_multiplier = ValueProperty(
            "ambientOcclusionMultiplier", 0)
        self.artificial_ambient_occlusion = ValueProperty(
            "artificialAmbientOcclusion", 0)
        self.tint_value = ValueProperty("tintValue", 0)


class EntityListProperty(ListProperty):
    list_type = EntityItem
    tag_name = "entities"


class CMapData(ElementTree, AbstractClass):
    tag_name = "CMapData"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("name")
        self.parent = TextProperty("parent")
        self.flags = ValueProperty("flags", 0)
        self.content_flags = ValueProperty("contentFlags", 0)
        self.streaming_extents_min = VectorProperty("streamingExtentsMin")
        self.streaming_extents_max = VectorProperty("streamingExtentsMax")
        self.entities_extents_min = VectorProperty("entitiesExtentsMin")
        self.entities_extents_max = VectorProperty("entitiesExtentsMax")
        self.entities = EntityListProperty()
