from xml.etree import ElementTree as ET
from .element import (
    AttributeProperty,
    ElementTree,
    ElementProperty,
    ListProperty,
    QuaternionProperty,
    TextProperty,
    ValueProperty,
    VectorProperty
)
from .ymap import EntityList, ExtensionsList
from numpy import float32


class YTYP:

    file_extension = ".ytyp.xml"

    @staticmethod
    def from_xml_file(filepath):
        return CMapTypes.from_xml_file(filepath)

    @staticmethod
    def write_xml(cmap_types, filepath):
        return cmap_types.write_xml(filepath)


class BaseArchetype(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = AttributeProperty("type", "CBaseArchetypeDef")
        self.lod_dist = ValueProperty("lodDist")
        self.flags = ValueProperty("flags")
        self.special_attribute = ValueProperty("specialAttribute")
        self.bb_min = VectorProperty("bbMin")
        self.bb_max = VectorProperty("bbMax")
        self.bs_center = VectorProperty("bsCentre")
        self.bs_radius = ValueProperty("bsRadius")
        self.hd_texture_dist = ValueProperty("hdTextureDist")
        self.name = TextProperty("name")
        self.texture_dictionary = TextProperty("textureDictionary")
        self.clip_dictionary = TextProperty("clipDictionary")
        self.drawable_dictionary = TextProperty("drawableDictionary")
        self.physics_dictionary = TextProperty("physicsDictionary")
        self.asset_type = TextProperty("assetType")
        self.asset_name = TextProperty("assetName")
        self.extensions = ExtensionsList()


class TimeArchetype(BaseArchetype):
    def __init__(self):
        super().__init__()
        self.type = AttributeProperty("type", "CTimeArchetypeDef")
        self.time_flags = ValueProperty("timeFlags")


class Corner(ElementProperty):
    value_types = (tuple)
    tag_name = "Item"

    def __init__(self, tag_name=None, value=None):
        super().__init__("Item", value or tuple())

    @staticmethod
    def from_xml(element):
        value = element.text.split(",")
        value = [float(val) for val in value]
        if len(value) > 3:
            value = value[:3]
        return Corner(value=tuple(value))

    def to_xml(self):
        if not self.value or len(self.value) < 1:
            return None

        elem = ET.Element(self.tag_name)
        elem.text = ",".join([str(float32(val)) for val in self.value])
        return elem


class CornersList(ListProperty):
    list_type = Corner
    tag_name = "corners"


class AttachedObjectsBuffer(ElementProperty):
    value_types = (int)

    def __init__(self):
        super().__init__(tag_name="attachedObjects", value=[])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        if element.text:
            indices = element.text.strip().replace("\n", "").split()
            new.value = [int(i) for i in indices]

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        columns = 10
        text = []

        for index, entity_index in enumerate(self.value):
            text.append(str(entity_index))
            if index < len(self.value) - 1:
                text.append(" ")
            if (index + 1) % columns == 0:
                text.append("\n")

        element.text = "".join(text)

        return element


class Portal(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.room_from = ValueProperty("roomFrom")
        self.room_to = ValueProperty("roomTo")
        self.flags = ValueProperty("flags")
        self.mirror_priority = ValueProperty("mirrorPriority")
        self.opacity = ValueProperty("opacity")
        self.audio_occlusion = ValueProperty("audioOcclusion")
        self.corners = CornersList()
        self.attached_objects = AttachedObjectsBuffer()


class PortalsList(ListProperty):
    tag_name = "portals"
    list_type = Portal

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name="portals", value=value or [])
        self.item_type = AttributeProperty("itemType", "CMloPortalDef")


class Room(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("name")
        self.bb_min = VectorProperty("bbMin")
        self.bb_max = VectorProperty("bbMax")
        self.blend = ValueProperty("blend", 1)
        self.timecycle_name = TextProperty("timecycleName")
        self.secondary_timecycle_name = TextProperty("secondaryTimecycleName")
        self.flags = ValueProperty("flags")
        self.portal_count = ValueProperty("portalCount")
        self.floor_id = ValueProperty("floorId")
        self.exterior_visibility_depth = ValueProperty(
            "exteriorVisibiltyDepth", -1)
        self.attached_objects = AttachedObjectsBuffer()


class RoomsList(ListProperty):
    tag_name = "rooms"
    list_type = Room

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name="rooms", value=value or [])
        self.item_type = AttributeProperty("itemType", "CMloRoomDef")


class LocationsBuffer(ElementProperty):
    value_types = (int)

    def __init__(self):
        super().__init__(tag_name="locations", value=[])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        if element.text:
            indices = element.text.strip().replace("\n", "").split()
            new.value = [int(i) for i in indices]

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        columns = 10
        text = []

        for index, entity_index in enumerate(self.value):
            text.append(str(entity_index))
            if index < len(self.value) - 1:
                text.append(" ")
            if (index + 1) % columns == 0:
                text.append("\n")

        element.text = "".join(text)

        return element


class EntitySet(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("name")
        self.locations = LocationsBuffer()
        self.entities = EntityList()


class EntitySetsList(ListProperty):
    tag_name = "entitySets"
    list_type = EntitySet

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name="entitySets", value=value or [])
        self.item_type = AttributeProperty("itemType", "CMloEntitySet")


class TimeCycleModifier(ElementTree):
    tag_name = "Item"

    def __init__(self):
        self.name = TextProperty("name")
        self.sphere = QuaternionProperty("sphere")
        self.percentage = ValueProperty("percentage")
        self.range = ValueProperty("range")
        self.start_hour = ValueProperty("startHour")
        self.end_hour = ValueProperty("endHour")


class TimeCycleModifiersList(ListProperty):
    tag_name = "timeCycleModifiers"
    list_type = TimeCycleModifier

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name="timeCycleModifiers", value=value or [])
        self.item_type = AttributeProperty("itemType", "CMloTimeCycleModifier")


class MloArchetype(BaseArchetype):
    def __init__(self):
        super().__init__()
        self.type = AttributeProperty("type", "CMloArchetypeDef")
        self.mlo_flags = ValueProperty("mloFlags")
        self.entities = EntityList()
        self.rooms = RoomsList()
        self.portals = PortalsList()
        self.entity_sets = EntitySetsList()
        self.timecycle_modifiers = TimeCycleModifiersList()


class ArchetypesList(ListProperty):
    list_type = BaseArchetype
    tag_name = "archetypes"

    @staticmethod
    def from_xml(element: ET.Element):
        new = ArchetypesList()

        for child in element.iter():
            if "type" in child.attrib:
                arch_type = child.get("type")
                if arch_type == "CBaseArchetypeDef":
                    new.value.append(BaseArchetype.from_xml(child))
                elif arch_type == "CMloArchetypeDef":
                    new.value.append(MloArchetype.from_xml(child))
                elif arch_type == "CTimeArchetypeDef":
                    new.value.append(TimeArchetype.from_xml(child))

        return new


class CompositeEntityType(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name")
        self.lod_dist = ValueProperty("lodDist")
        self.flags = ValueProperty("flags")
        self.special_attribute = ValueProperty("specialAttribute")
        self.bb_min = VectorProperty("bbMin")
        self.bb_max = VectorProperty("bbMax")
        self.bs_center = VectorProperty("bsCentre")
        self.bs_radius = ValueProperty("bsRadius")
        self.start_model = TextProperty("StartModel")
        self.end_model = TextProperty("EndModel")
        self.start_imap_file = TextProperty("StartImapFile")
        self.end_imap_file = TextProperty("EndImapFile")
        self.ptfx_assetname = TextProperty("PtFxAssetName")
        # TODO
        # self.animations = AnimationsList()


class CompositeEntityTypeList(ListProperty):
    list_type = CompositeEntityType
    tag_name = "compositeEntityTypes"

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name="compositeEntityTypes", value=value or [])
        self.item_type = AttributeProperty("itemType", "CCompositeEntityType")


class CMapTypes(ElementTree):
    tag_name = "CMapTypes"

    def __init__(self):
        super().__init__()
        self.extensions = ExtensionsList()
        self.archetypes = ArchetypesList()
        self.name = TextProperty("name")
        # TODO: Investigate: Not used in any ytyp file in the game?
        # self.dependencies = DependenciesListProperty()
        self.composite_entity_type = CompositeEntityTypeList()
