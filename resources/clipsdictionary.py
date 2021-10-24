from typing import Text
from .codewalker_xml import *
from xml.etree import ElementTree as ET


class YCD:

    @staticmethod
    def from_xml_file(filepath):
        return ClipsDictionary.from_xml_file(filepath)

    @staticmethod
    def write_xml(clips_dict, filepath):
        return clips_dict.write_xml(filepath)


class AttributesListProperty(ListProperty):
    class Attribute(ElementTree):
        tag_name = 'Item'

        def __init__(self):
            super().__init__()
            self.name_hash = TextProperty('NameHash', '')
            self.type = ValueProperty('Type', 'Int')
            self.value = ValueProperty('Value', 0)

    list_type = Attribute

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'Tags', value=value or [])


class TagListProperty(ListProperty):
    class Tag(ElementTree):
        tag_name = 'Item'

        def __init__(self):
            super().__init__()
            self.name_hash = TextProperty('NameHash', '')
            self.unk_hash = TextProperty('UnkHash', '')
            self.attributes = AttributesListProperty()

    list_type = Tag

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'Tags', value=value or [])


class ClipsListProperty(ListProperty):
    class Clip(ElementTree):
        tag_name = 'Item'

        def __init__(self):
            super().__init__()
            self.hash = TextProperty('Hash', '')
            self.name = TextProperty('Name', '')
            self.type = ValueProperty('Type', 'Animation')
            self.unknown30 = ValueProperty('Unknown30', 0)
            self.tags = TagListProperty()

    list_type = Clip

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'Clips', value=value or [])


class ValuesBuffer(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name=tag_name or 'Values', value=[])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        text = element.text.strip().split('\n')
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
                text.append(' ')
            if index % columns == 0 and index > 0:
                text.append('\n')

        element.text = ''.join(text)

        return element


class Channel(ElementTree, AbstractClass):
    tag_name = 'Item'

    @property
    @abstractmethod
    def type(self) -> str:
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        # Types
        # StaticQuaternion = 0,
        # StaticVector3 = 1,
        # StaticFloat = 2,
        # RawFloat = 3,
        # QuantizeFloat = 4,
        # IndirectQuantizeFloat = 5,
        # LinearFloat = 6,
        # CachedQuaternion1 = 7,
        # CachedQuaternion2 = 8,
        self.type = ValueProperty('Type', '')


class StaticQuaternion(Channel):
    type = 'StaticQuaternion'

    def __init__(self):
        super().__init__()
        self.value = QuaternionProperty('Value')


class StaticVector3(Channel):
    type = 'StaticVector3'

    def __init__(self):
        super().__init__()
        self.value = VectorProperty('Value')


class StaticFloat(Channel):
    type = 'StaticFloat'

    def __init__(self):
        super().__init__()
        self.value = ValueProperty('Value', 0.0)


class RawFloat(Channel):
    type = 'RawFloat'

    def __init__(self):
        super().__init__()
        self.values = ValuesBuffer()


class QuantizeFloat(Channel):
    type = 'QuantizeFloat'

    def __init__(self):
        super().__init__()
        self.quantum = ValueProperty('Quantum', 0.0)
        self.offset = ValueProperty('Offset', 0.0)
        self.values = ValuesBuffer()


class IndirectQuantizeFloat(QuantizeFloat):
    type = 'IndirectQuantizeFloat'

    def __init__(self):
        super().__init__()
        self.frames = ValuesBuffer('Frames')


class LinearFloat(QuantizeFloat):
    type = 'LinearFloat'

    def __init__(self):
        super().__init__()
        self.numints = ValueProperty('NumInts', 0)
        self.counts = ValueProperty('Counts', 0)


class CachedQuaternion1(Channel):
    type = 'CachedQuaternion1'

    def __init__(self):
        super().__init__()
        self.quat_index = ValueProperty('QuatIndex', 0)


class CachedQuaternion2(CachedQuaternion1):
    type = 'CachedQuaternion2'


class ChannelsListProperty(ListProperty):
    list_type = Channel

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'Channels', value=value or [])


class SequencesDataListProperty(ListProperty):
    class SequenceData(ElementTree):
        tag_name = 'Item'

        def __init__(self):
            super().__init__()
            self.channels = ChannelsListProperty()

    list_type = SequenceData

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'SequenceData', value=value or [])


class SequencesListProperty(ListProperty):
    class Sequence(ElementTree):
        tag_name = 'Item'

        def __init__(self):
            super().__init__()
            self.hash = TextProperty('Hash', '')
            self.frame_count = ValueProperty('FrameCount', 0)

    list_type = Sequence

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'Sequences', value=value or [])


class BoneIdsListProperty(ListProperty):
    class BoneId(ElementTree):
        tag_name = 'Item'

        def __init__(self):
            super().__init__()
            self.bone_id = ValueProperty('BoneId', 0)
            self.track = ValueProperty('Track', 0)
            self.unk0 = ValueProperty('Unk0', 0)

    list_type = BoneId

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'BoneIds', value=value or [])


class AnimationsListProperty(ListProperty):
    class Animation(ElementTree):

        tag_name = 'Item'

        def __init__(self):
            super().__init__()
            self.hash = TextProperty('Hash', '')
            self.unknown10 = ValueProperty('Unknown10', 0)
            self.frame_count = ValueProperty('FrameCount', 0)
            self.sequence_frame_limit = ValueProperty('SequenceFrameLimit', 0)
            self.duration = ValueProperty('Duration', 0.0)
            self.unknown1C = TextProperty('Unknown1c')
            self.bone_ids = BoneIdsListProperty()


class ClipsDictionary(ElementTree):
    tag_name = 'ClipsDictionary'

    def __init__(self):
        super().__init__()
        self.clips = ClipsListProperty()
