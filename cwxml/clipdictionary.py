# from .element import *
from abc import ABC as AbstractClass, abstractmethod
from enum import Enum
from mathutils import Vector
from .element import (
    ElementTree,
    ElementProperty,
    ListProperty,
    QuaternionProperty,
    TextProperty,
    ValueProperty,
    VectorProperty,
    Vector4Property
)
from xml.etree import ElementTree as ET
from inspect import isclass
from math import sqrt


class YCD:

    file_extension = ".ycd.xml"

    @staticmethod
    def from_xml_file(filepath):
        return ClipDictionary.from_xml_file(filepath)

    @staticmethod
    def write_xml(clips_dict, filepath):
        return clips_dict.write_xml(filepath)


class ItemTypeList(ListProperty, AbstractClass):
    class Item(ElementTree, AbstractClass):
        tag_name = "Item"

        @property
        @abstractmethod
        def type(self) -> str:
            raise NotImplementedError

    list_type = Item

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        type_map = {}
        for key, item_class in vars(cls).items():
            if isclass(item_class) and issubclass(item_class, ItemTypeList.Item) and key == item_class.__name__:
                type_map[item_class.type] = item_class
        for child in element:
            type_elem = child.find("Type")
            if type_elem is not None:
                type = type_elem.get("value")
                if type in type_map:
                    new.value.append(type_map[type].from_xml(child))
        return new


class AttributesList(ItemTypeList):
    class Attribute(ItemTypeList.Item, AbstractClass):
        tag_name = "Item"

        @property
        @abstractmethod
        def type(self) -> str:
            raise NotImplementedError

        def __init__(self):
            super().__init__()
            self.name_hash = TextProperty("NameHash", "")
            self.type = ValueProperty("Type", self.type)

    class FloatAttribute(Attribute):
        type = "Float"

        def __init__(self):
            super().__init__()
            self.value = ValueProperty("Value", 0.0)

    class IntAttribute(Attribute):
        type = "Int"

        def __init__(self):
            super().__init__()
            self.value = ValueProperty("Value", 0)

    class BoolAttribute(Attribute):
        type = "Bool"

        def __init__(self):
            super().__init__()
            self.value = ValueProperty("Value", 0)

    class Vector3Attribute(Attribute):
        type = "Vector3"

        def __init__(self):
            super().__init__()
            self.value = VectorProperty("Value")
            self.unknown2c = ValueProperty("Unknown2C", 1)

    class Vector4Attribute(Attribute):
        type = "Vector4"

        def __init__(self):
            super().__init__()
            self.value = Vector4Property("Value")

    class StringAttribute(Attribute):
        type = "String"

        def __init__(self):
            super().__init__()
            self.value = TextProperty("Value", "")

    class HashStringAttribute(Attribute):
        type = "HashString"

        def __init__(self):
            super().__init__()
            self.value = TextProperty("Value", "")

    list_type = Attribute
    tag_name = "Attributes"


class ValuesBuffer(ElementProperty):
    value_types = (list)

    def __init__(self):
        super().__init__(tag_name="Values", value=[])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        text = element.text.strip().split("\n")
        if len(text) > 0:
            for line in text:
                items = line.strip().split(" ")
                for item in items:
                    new.value.append(float(item))

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        columns = 10
        text = []

        for index, value in enumerate(self.value):
            text.append(str(value))
            if index < len(self.value) - 1:
                text.append(" ")
            if (index + 1) % columns == 0:
                text.append("\n")

        element.text = "".join(text)

        return element


class FramesBuffer(ElementProperty):
    value_types = (list)

    def __init__(self):
        super().__init__(tag_name="Frames", value=[])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        text = element.text.strip().split("\n")
        if len(text) > 0:
            for line in text:
                items = line.strip().split(" ")
                for item in items:
                    new.value.append(int(item))

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        columns = 10
        text = []

        for index, value in enumerate(self.value):
            text.append(str(value))
            if index < len(self.value) - 1:
                text.append(" ")
            if (index + 1) % columns == 0:
                text.append("\n")

        element.text = "".join(text)

        return element


class ChannelsList(ItemTypeList):
    class Channel(ItemTypeList.Item, AbstractClass):
        tag_name = "Item"

        @property
        @abstractmethod
        def type(self) -> str:
            raise NotImplementedError

        def __init__(self):
            super().__init__()
            self.type = ValueProperty("Type", "")

        def get_value(self, frame_id, channel_values):
            raise NotImplementedError

    class StaticQuaternion(Channel):
        type = "StaticQuaternion"

        def __init__(self):
            super().__init__()
            self.value = QuaternionProperty("Value")
            self.type = "StaticQuaternion"

        def get_value(self, frame_id, channel_values):
            return self.value

    class StaticVector3(Channel):
        type = "StaticVector3"

        def __init__(self):
            super().__init__()
            self.value = VectorProperty("Value")
            self.type = "StaticVector3"

        def get_value(self, frame_id, channel_values):
            return self.value

    class StaticFloat(Channel):
        type = "StaticFloat"

        def __init__(self):
            super().__init__()
            self.value = ValueProperty("Value", 0.0)
            self.type = "StaticFloat"

        def get_value(self, frame_id, channel_values):
            return self.value

    class RawFloat(Channel):
        type = "RawFloat"

        def __init__(self):
            super().__init__()
            self.values = ValuesBuffer()
            self.type = "RawFloat"

        def get_value(self, frame_id, channel_values):
            return self.values[frame_id % len(self.values)]

    class QuantizeFloat(Channel):
        type = "QuantizeFloat"

        def __init__(self):
            super().__init__()
            self.quantum = ValueProperty("Quantum", 0.0)
            self.offset = ValueProperty("Offset", 0.0)
            self.values = ValuesBuffer()
            self.type = "QuantizeFloat"

        def get_value(self, frame_id, channel_values):
            return self.values[frame_id % len(self.values)]

    class IndirectQuantizeFloat(QuantizeFloat):
        type = "IndirectQuantizeFloat"

        def __init__(self):
            super().__init__()
            self.frames = FramesBuffer()
            self.type = "IndirectQuantizeFloat"

        def get_value(self, frame_id, channel_values):
            return self.values[(self.frames[frame_id % len(self.frames)]) % len(self.values)]

    class LinearFloat(QuantizeFloat):
        type = "LinearFloat"

        def __init__(self):
            super().__init__()
            self.numints = ValueProperty("NumInts", 0)
            self.counts = ValueProperty("Counts", 0)
            self.type = "LinearFloat"

    class CachedQuaternion1(Channel):
        type = "CachedQuaternion1"

        def __init__(self):
            super().__init__()
            self.quat_index = ValueProperty("QuatIndex", 0)
            self.type = "CachedQuaternion1"

        def get_value(self, frame_id, channel_values):
            vec_len = Vector(
                (channel_values[0], channel_values[1], channel_values[2])).length

            return sqrt(max(1.0 - vec_len * vec_len, 0))

    class CachedQuaternion2(CachedQuaternion1):
        type = "CachedQuaternion2"

        def __init__(self):
            super().__init__()
            self.quat_index = ValueProperty("QuatIndex", 0)
            self.type = "CachedQuaternion2"

    list_type = Channel
    tag_name = "Channels"


class Animation(ElementTree):
    class BoneIdList(ListProperty):
        class BoneId(ElementTree):
            tag_name = "Item"

            def __init__(self):
                super().__init__()
                self.bone_id = ValueProperty("BoneId", 0)
                self.track = ValueProperty("Track", 0)
                self.format = ValueProperty("Unk0", 0)

        list_type = BoneId
        tag_name = "BoneIds"

    class SequenceDataList(ListProperty):
        class SequenceData(ElementTree):
            tag_name = "Item"

            def __init__(self):
                super().__init__()
                self.channels = ChannelsList()

        list_type = SequenceData
        tag_name = "SequenceData"

    class SequenceList(ListProperty):

        class Sequence(ElementTree):

            tag_name = "Item"

            def __init__(self):
                super().__init__()
                self.hash = TextProperty("Hash", "")
                self.frame_count = ValueProperty("FrameCount", 0)
                self.sequence_data = Animation.SequenceDataList()

        list_type = Sequence
        tag_name = "Sequences"

    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.hash = TextProperty("Hash", "")
        self.unknown10 = ValueProperty("Unknown10", 0)
        self.frame_count = ValueProperty("FrameCount", 0)
        self.sequence_frame_limit = ValueProperty("SequenceFrameLimit", 0)
        self.duration = ValueProperty("Duration", 0.0)
        self.unknown1C = TextProperty("Unknown1C")
        self.bone_ids = Animation.BoneIdList()
        self.sequences = Animation.SequenceList()


class Property(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name_hash = TextProperty("NameHash", "")
        self.unk_hash = TextProperty("UnkHash", "")
        self.attributes = AttributesList()


class ClipType(str, Enum):
    ANIMATION = "Animation"
    ANIMATION_LIST = "AnimationList"


class Clip(ItemTypeList.Item, AbstractClass):
    class TagList(ListProperty):
        class Tag(Property):
            tag_name = "Item"

            def __init__(self):
                super().__init__()
                self.start_phase = ValueProperty("StartPhase", 0.0)
                self.end_phase = ValueProperty("EndPhase", 0.0)

        list_type = Tag
        tag_name = "Tags"

    class PropertyList(ListProperty):
        list_type = Property
        tag_name = "Properties"

    def __init__(self):
        super().__init__()
        self.hash = TextProperty("Hash", "")
        self.name = TextProperty("Name", "")
        self.type = ValueProperty("Type", "Animation")
        self.unknown30 = ValueProperty("Unknown30", 0)
        self.tags = Clip.TagList()
        self.properties = Clip.PropertyList()


class ClipAnimationsList(ListProperty):
    class ClipAnimation(ElementTree):

        tag_name = "Item"

        def __init__(self):
            super().__init__()
            self.animation_hash = TextProperty("AnimationHash", "")
            self.start_time = ValueProperty("StartTime", 0.0)
            self.end_time = ValueProperty("EndTime", 0.0)
            self.rate = ValueProperty("Rate", 0.0)

    list_type = ClipAnimation
    tag_name = "Animations"


class ClipsList(ItemTypeList):
    class ClipAnimation(Clip):
        type = ClipType.ANIMATION

        def __init__(self):
            super().__init__()
            self.animation_hash = TextProperty("AnimationHash", "")
            self.start_time = ValueProperty("StartTime", 0.0)
            self.end_time = ValueProperty("EndTime", 0.0)
            self.rate = ValueProperty("Rate", 0.0)

    class ClipAnimationList(Clip):
        type = ClipType.ANIMATION_LIST

        def __init__(self):
            super().__init__()
            self.type = "AnimationList"
            self.duration = ValueProperty("Duration", 0.0)
            self.animations = ClipAnimationsList()

    list_type = Clip
    tag_name = "Clips"


class ClipDictionary(ElementTree):
    class AnimationsList(ListProperty):
        list_type = Animation
        tag_name = "Animations"

    tag_name = "ClipDictionary"

    def __init__(self):
        super().__init__()
        self.clips = ClipsList()
        self.animations = ClipDictionary.AnimationsList()
