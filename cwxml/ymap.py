from abc import ABC as AbstractClass, abstractmethod
from typing import Union, Type
from xml.etree import ElementTree as ET
from .element import (
    AttributeProperty,
    ElementProperty,
    ElementTree,
    ListProperty,
    QuaternionProperty,
    StringValueProperty,
    TextProperty,
    TextListProperty,
    ValueProperty,
    VectorProperty,
    TextPropertyRequired,
    ListPropertyRequired,
    ElementProperty,
    Vector4Property,
)


class YMAP:

    file_extension = ".ymap.xml"

    @staticmethod
    def from_xml_file(filepath):
        return CMapData.from_xml_file(filepath)

    @staticmethod
    def write_xml(cmap_data, filepath):
        return cmap_data.write_xml(filepath)


class HexColorProperty(ElementProperty):
    value_types = (tuple)

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or "color", value or (0, 0, 0, 0))

    @staticmethod
    def argb_hex_to_rgba(argb_hex: str) -> tuple[float, float, float, float]:
        argb = int(argb_hex, base=16)
        return (
            ((argb >> 16) & 0xFF) / 0xFF,
            ((argb >> 8) & 0xFF) / 0xFF,
            (argb & 0xFF) / 0xFF,
            ((argb >> 24) & 0xFF) / 0xFF
        )

    @staticmethod
    def rgba_to_argb_hex(rgba: tuple[float, float, float, float]) -> str:
        argb = (
            (int(rgba[3] * 0xFF) & 0xFF) << 24 |
            (int(rgba[0] * 0xFF) & 0xFF) << 16 |
            (int(rgba[1] * 0xFF) & 0xFF) << 8 |
            (int(rgba[2] * 0xFF) & 0xFF)
        )
        return f"0x{argb:08X}"

    @staticmethod
    def from_xml(element: ET.Element):
        if "value" not in element.attrib:
            ValueProperty.read_value_error(element)

        rgba = HexColorProperty.argb_hex_to_rgba(element.get("value"))

        return HexColorProperty(element.tag, rgba)

    def to_xml(self):
        argb_hex = HexColorProperty.rgba_to_argb_hex(self.value)

        return ET.Element(self.tag_name, attrib={"value": argb_hex})


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


class LightInstancesList(ListProperty):
    list_type = LightInstance
    tag_name = "instances"

    def __init__(self, tag_name=None, value=None):
        super().__init__(LightInstancesList.tag_name, value=value)
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
        self.color = HexColorProperty()


class ExtensionLightEffect(Extension):
    type = "CExtensionDefLightEffect"

    def __init__(self):
        super().__init__()
        self.instances = LightInstancesList()


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
        self.effect_hash = StringValueProperty("effectHash")


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
        self.creature_metadata_name = TextProperty("creatureMetadataname")
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
        self.color = HexColorProperty()
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
        self.scenario_flags = TextProperty("flags")
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
        self.scenario_flags = TextProperty("flags")
        self.radius = ValueProperty("Radius")
        self.time_till_ped_leaves = ValueProperty("TimeTillPedLeaves")


class ExtensionWindDisturbance(Extension):
    type = "CExtensionDefWindDisturbance"

    def __init__(self):
        super().__init__()
        self.offset_rotation = QuaternionProperty("offsetRotation")
        self.disturbance_type = ValueProperty("disturbanceType")
        self.bone_tag = ValueProperty("boneTag")
        self.size = Vector4Property("size")
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


class ExtensionsList(ListProperty):
    list_type = Extension
    tag_name = "extensions"

    @staticmethod
    def get_extension_xml_class_from_type(ext_type: str) -> Union[Type[Extension], None]:
        if ext_type == ExtensionLightEffect.type:
            return ExtensionLightEffect
        elif ext_type == ExtensionParticleEffect.type:
            return ExtensionParticleEffect
        elif ext_type == ExtensionAudioCollision.type:
            return ExtensionAudioCollision
        elif ext_type == ExtensionAudioEmitter.type:
            return ExtensionAudioEmitter
        elif ext_type == ExtensionExplosionEffect.type:
            return ExtensionExplosionEffect
        elif ext_type == ExtensionLadder.type:
            return ExtensionLadder
        elif ext_type == ExtensionBuoyancy.type:
            return ExtensionBuoyancy
        elif ext_type == ExtensionExpression.type:
            return ExtensionExpression
        elif ext_type == ExtensionLightShaft.type:
            return ExtensionLightShaft
        elif ext_type == ExtensionDoor.type:
            return ExtensionDoor
        elif ext_type == ExtensionSpawnPoint.type:
            return ExtensionSpawnPoint
        elif ext_type == ExtensionSpawnPointOverride.type:
            return ExtensionSpawnPointOverride
        elif ext_type == ExtensionWindDisturbance.type:
            return ExtensionWindDisturbance
        elif ext_type == ExtensionProcObject.type:
            return ExtensionProcObject

        return None

    @staticmethod
    def from_xml(element: ET.Element):
        new = ExtensionsList()

        for child in element.iter():
            if "type" in child.attrib:
                ext_type = child.get("type")
                ext_class = ExtensionsList.get_extension_xml_class_from_type(
                    ext_type)

                if ext_class is None:
                    print(f"Unknown extension type '{ext_type}'! Skipping...")
                    continue

                new.value.append(ext_class.from_xml(child))

        return new


class Entity(ElementTree):
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
        self.parent_index = ValueProperty("parentIndex", -1)
        self.lod_dist = ValueProperty("lodDist", 0)
        self.child_lod_dist = ValueProperty("childLodDist", 0)
        self.lod_level = TextProperty("lodLevel")
        self.num_children = ValueProperty("numChildren", 0)
        self.priority_level = TextProperty("priorityLevel")
        self.extensions = ExtensionsList()
        self.ambient_occlusion_multiplier = ValueProperty(
            "ambientOcclusionMultiplier", 0)
        self.artificial_ambient_occlusion = ValueProperty(
            "artificialAmbientOcclusion", 0)
        self.tint_value = ValueProperty("tintValue", 0)


class EntityList(ListPropertyRequired):
    list_type = Entity
    tag_name = "entities"


class ContainerLodsList(ElementTree):
    """This is not used by GTA5 but added for completion"""
    tag_name = "containerLods"

    def __init__(self):
        super().__init__()
        self.item_type = AttributeProperty(
            "itemType", "rage__fwContainerLodDef")


class BoxOccluder(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.center_x = ValueProperty("iCenterX")
        self.center_y = ValueProperty("iCenterY")
        self.center_z = ValueProperty("iCenterZ")
        self.cos_z = ValueProperty("iCosZ")
        self.length = ValueProperty("iLength")
        self.width = ValueProperty("iWidth")
        self.height = ValueProperty("iHeight")
        self.sin_z = ValueProperty("iSinZ")


class BoxOccludersList(ListPropertyRequired):
    list_type = BoxOccluder
    tag_name = "boxOccluders"

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name, value)
        self.item_type = AttributeProperty("itemType", "BoxOccluder")


class OccludeModel(ElementTree):
    class VertsProperty(ElementProperty):
        """Same as a TextProperty but formats the input and output and returns an empty element rather than None"""
        value_types = (str)

        def __init__(self, tag_name: str = "verts", value=None):
            super().__init__(tag_name, value or "")

        @staticmethod
        def from_xml(element: ET.Element):
            text = element.text.replace("\n", "").replace(" ", "")
            if not text:
                raise ValueError(
                    f'Missing verts data on {OccludeModel.VertsProperty.__name__}')
            return OccludeModel.VertsProperty(element.tag, text)

        def to_xml(self):
            element = ET.Element(self.tag_name)
            if not self.value or len(self.value) < 1:
                return element

            text = []
            for chunk in [self.value[i:i + 64] for i in range(0, len(self.value), 64)]:
                text.append(" ".join([chunk[j:j + 2]
                            for j in range(0, len(chunk), 2)]))
                text.append("\n")
            element.text = "".join(text)

            return element

    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.bmin = VectorProperty("bmin")
        self.bmax = VectorProperty("bmax")
        self.data_size = ValueProperty("dataSize")
        self.verts = self.VertsProperty("verts")
        self.num_verts_in_bytes = ValueProperty("numVertsInBytes")
        self.num_tris = ValueProperty("numTris")
        self.flags = ValueProperty("flags")


class OccludeModelsList(ListPropertyRequired):
    list_type = OccludeModel
    tag_name = "occludeModels"

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name, value)
        self.item_type = AttributeProperty("itemType", "OccludeModel")


class PhysicsDictionariesList(ListProperty):
    """
    Same as ListPropertyRequired but only accepts items of type TextProperty.
    """
    class PhysicsDictionarie(TextProperty):
        tag_name = "Item"

    list_type = PhysicsDictionarie
    tag_name = "physicsDictionaries"

    def to_xml(self):
        element = ET.Element(self.tag_name)

        for child in vars(self).values():
            if isinstance(child, AttributeProperty):
                element.set(child.name, str(child.value))

        if self.value and len(self.value) > 0:
            for item in self.value:
                if isinstance(item, TextProperty):
                    element.append(item.to_xml())
                else:
                    raise TypeError(
                        f"{type(self).__name__} can only hold objects of type '{self.list_type.__name__}', not '{type(item)}'")

        return element


# TODO: InstancedData


class TimeCycleModifier(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("name")
        self.min_extents = VectorProperty("minExtents")
        self.max_extents = VectorProperty("maxExtents")
        self.percentage = ValueProperty("percentage")
        self.range = ValueProperty("range")
        self.start_hour = ValueProperty("startHour")
        self.end_hour = ValueProperty("endHour")


class TimeCycleModifiersList(ListPropertyRequired):
    list_type = TimeCycleModifier
    tag_name = "timeCycleModifiers"

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name, value)
        self.item_type = AttributeProperty("itemType", "CTimeCycleModifier")


class CarGenerator(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.position = VectorProperty("position")
        self.orient_x = ValueProperty("orientX")
        self.orient_y = ValueProperty("orientY")
        self.perpendicular_length = ValueProperty("perpendicularLength")
        self.car_model = TextPropertyRequired("carModel")
        self.flags = ValueProperty("flags")
        self.body_color_remap_1 = ValueProperty("bodyColorRemap1", -1)
        self.body_color_remap_2 = ValueProperty("bodyColorRemap2", -1)
        self.body_color_remap_3 = ValueProperty("bodyColorRemap3", -1)
        self.body_color_remap_4 = ValueProperty("bodyColorRemap4", -1)
        self.pop_group = TextPropertyRequired("popGroup")
        self.livery = ValueProperty("livery", -1)


class CarGeneratorsList(ListPropertyRequired):
    list_type = CarGenerator
    tag_name = "carGenerators"

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name, value)
        self.item_type = AttributeProperty("itemType", "CCarGen")


# TODO: Lod Lights


# TODO: Distant Lod Lights


class Block(ElementTree):
    tag_name = "block"

    def __init__(self):
        super().__init__()
        self.version = ValueProperty("version")
        self.flags = ValueProperty("flags")
        self.name = TextPropertyRequired("name")
        self.exported_by = TextPropertyRequired("exportedBy")
        self.owner = TextPropertyRequired("owner")
        self.time = TextPropertyRequired("time")


class CMapData(ElementTree, AbstractClass):
    tag_name = "CMapData"

    def __init__(self):
        super().__init__()
        self.name = TextPropertyRequired("name")
        self.parent = TextPropertyRequired("parent")
        self.flags = ValueProperty("flags", 0)
        self.content_flags = ValueProperty("contentFlags", 0)
        self.streaming_extents_min = VectorProperty("streamingExtentsMin")
        self.streaming_extents_max = VectorProperty("streamingExtentsMax")
        self.entities_extents_min = VectorProperty("entitiesExtentsMin")
        self.entities_extents_max = VectorProperty("entitiesExtentsMax")
        self.entities = EntityList()
        self.container_lods = ContainerLodsList()
        self.box_occluders = BoxOccludersList()
        self.occlude_models = OccludeModelsList()
        self.physics_dictionaries = PhysicsDictionariesList()
        # self.instanced_data = InstancedDataProperty()
        self.time_cycle_modifiers = TimeCycleModifiersList()
        self.car_generators = CarGeneratorsList()
        # self.lod_lights = LODLightsSOAProperty()
        # self.distant_lod_lights = DistantLODLightsSOAProperty()
        self.block = Block()
