import math
from mathutils import Vector, Quaternion

from ...tools import xml as Xml

class Channel:

    @staticmethod
    def fromXml(node):  # pylint: disable=unused-argument
        return NotImplemented

    def getValue(self, frame, calcValues): # pylint: disable=unused-argument
        return NotImplemented

    def toXml(self):
        node = Xml.CreateNode("Item")
        #TODO: implement
        return node

class ChannelConst(Channel):
    def __init__(self, value):
        self.value = value

    def getValue(self, frame, calcValues):
        return self.value

class ChannelStaticFloat(Channel):

    value = None

    def __init__(self, value = None):
        self.value = value

    @staticmethod
    def fromXml(node):
        self = ChannelStaticFloat()
        self.value = Xml.ReadValue(node.find('Value'), None, float)
        assert self.value is not None
        return self

    def getValue(self, frame, calcValues):
        return self.value

    def toXml(self):
        node = Xml.CreateNode("Item")
        Xml.CreateValueNode("Type", "StaticFloat", node)
        Xml.CreateValueNode("Value", self.value, node)
        return node

class ChannelStaticVector(Channel):

    value = None

    @staticmethod
    def fromXml(node):
        self = ChannelStaticVector()
        self.value = Xml.ReadVector(node.find('Value'))
        assert self.value is not None
        return self

    def getValue(self, frame, calcValues):
        return self.value


class ChannelStaticQuaternion(Channel):

    value = None

    @staticmethod
    def fromXml(node):
        self = ChannelStaticQuaternion()
        self.value = Xml.ReadQuaternion(node.find('Value'))
        assert self.value is not None
        return self

    def getValue(self, frame, calcValues):
        return self.value


class ChannelCachedQuaternion1(Channel):

    quatIndex = None

    @staticmethod
    def fromXml(node):
        self = ChannelCachedQuaternion1()
        self.quatIndex = Xml.ReadValue(node.find('QuatIndex'), None, int)
        assert self.quatIndex is not None
        return self

    def getValue(self, frame, calcValues):
        vecLen = Vector((calcValues[0],calcValues[1],calcValues[2])).length
        return math.sqrt(max(1.0 - vecLen*vecLen, 0))

class ChannelQuantizeFloat(Channel):

    values = None

    def __init__(self, values = None):
        self.values = values

    @staticmethod
    def fromXml(node):
        self = ChannelQuantizeFloat()
        text = Xml.ReadText(node.find('Values')).replace('\n',' ')
        values_tokens = filter(len, text.split(' '))
        self.values = list(map(float, values_tokens))
        return self

    def getValue(self, frame, calcValues):
        return self.values[frame % len(self.values)]

    def toXml(self):
        node = Xml.CreateNode("Item")
        Xml.CreateValueNode("Type", "QuantizeFloat", node)
        Xml.CreateValueNode("Quantum", "0", node)
        Xml.CreateValueNode("Offset", "0", node)
        Xml.CreateTextNode("Values", ' '.join(map(str, self.values)), node)
        return node

class ChannelIndirectQuantizeFloat(Channel):

    values = None
    frames = None

    @staticmethod
    def fromXml(node):
        self = ChannelIndirectQuantizeFloat()
        values_tokens = filter(len, node.find('Values').text.replace('\n',' ').split(' '))
        self.values = list(map(float, values_tokens))
        frames_tokens = filter(len, node.find('Frames').text.replace('\n',' ').split(' '))
        self.frames = list(map(int, frames_tokens))
        return self

    def getValue(self, frame, calcValues):
        frameId = self.frames[frame % len(self.frames)]
        return self.values[frameId % len(self.values)]
