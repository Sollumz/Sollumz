from xml.etree.ElementTree import Element
import bpy

from ...tools import xml as Xml

class Clip:
    Hash = None
    Name = None
    Type = None
    Unknown30 = None

    Tags = []
    Properties = []
    AnimationHash = None
    StartTime = None
    EndTime = None
    Rate = None

    @staticmethod
    def fromXml(node):
        self = Clip()
        self.Hash = Xml.ReadText(node.find("Hash"), "", str)
        self.Name = Xml.ReadText(node.find("Name"), "", str)
        self.Type = Xml.ReadValue(node.find("Type"), "", str)
        self.Unknown30 = Xml.ReadValue(node.find("Unknown30"), 0, int)

        print('Parsing clip from xml:', self.Hash)

        # TODO: Tags
        # TODO: Properties
        # hashes: boneid,left,right,blocked,create,release,destroy,allowed

        if self.Type == "Animation":
            self.AnimationHash = Xml.ReadText(node.find("AnimationHash"), "", str)
            self.StartTime = Xml.ReadValue(node.find("StartTime"), 0, float)
            self.EndTime = Xml.ReadValue(node.find("EndTime"), 0, float)
            self.Rate = Xml.ReadValue(node.find("Rate"), 0, float)

        return self

    def toObject(self):
        clipNode = bpy.data.objects.new(self.Name, None)
        bpy.context.collection.objects.link(clipNode)
        clipNode.sollumtype = "Clip"

        props = clipNode.clip_properties
        props.Hash = self.Hash
        props.Name = self.Name
        props.Type = self.Type
        props.Unknown30 = self.Unknown30

        if self.Type == "Animation":
            props.AnimationHash = self.AnimationHash
            props.StartTime = self.StartTime
            props.EndTime = self.EndTime
            props.Rate = self.Rate

        return clipNode

    @staticmethod
    def fromObject(obj):
        self = Clip()

        props = obj.clip_properties

        self.Hash = props.Hash
        self.Name = props.Name
        self.Type = props.Type
        self.Unknown30 = props.Unknown30

        if self.Type == "Animation":
            self.AnimationHash = props.AnimationHash
            self.StartTime = props.StartTime
            self.EndTime = props.EndTime
            self.Rate = props.Rate

        return self

    def toXml(self):
        clipNode = Element("Item")
        Xml.CreateTextNode("Hash", self.Hash, clipNode)
        Xml.CreateTextNode("Name", self.Name, clipNode)
        Xml.CreateValueNode("Type", self.Type, clipNode)
        Xml.CreateValueNode("Unknown30", self.Unknown30, clipNode)

        Xml.CreateNode("Tags", clipNode) #TODO: tags
        Xml.CreateNode("Properties", clipNode) #TODO: properties

        if self.Type == "Animation":
            Xml.CreateTextNode("AnimationHash", self.AnimationHash, clipNode)
            Xml.CreateValueNode("StartTime", self.StartTime, clipNode)
            Xml.CreateValueNode("EndTime", self.EndTime, clipNode)
            Xml.CreateValueNode("Rate", self.Rate, clipNode)

        return clipNode
