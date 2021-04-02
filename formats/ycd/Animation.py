from xml.etree.ElementTree import Element
import bpy

from ...tools import xml as Xml
from .utils import find_bone_by_tag, find_armatures
from .AnimSequence import AnimSequence

class Animation:
    Hash = None
    Unknown10 = 0
    FrameCount = None
    SequenceFrameLimit = None
    Duration = None
    Unknown1C = None

    BoneIds = None
    Sequences = None

    @staticmethod
    def fromXml(node):
        self = Animation()
        self.Hash = Xml.ReadText(node.find("Hash"), "", str)
        self.FrameCount = Xml.ReadValue(node.find("FrameCount"), 1, int)
        self.Unknown10 = Xml.ReadValue(node.find("Unknown10"), 0, int)
        self.SequenceFrameLimit = Xml.ReadValue(node.find("SequenceFrameLimit"), 1, int)
        self.Duration = Xml.ReadValue(node.find("Duration"), 0, float)
        self.Unknown1C = Xml.ReadValue(node.find("Unknown1C"), "", str)

        self.BoneIds = []
        for boneIdNode in node.find("BoneIds"):
            self.BoneIds.append(AnimBoneId.fromXml(boneIdNode))

        self.Sequences = []
        for seqNode in node.find("Sequences"):
            self.Sequences.append(AnimSequence.fromXml(seqNode, self))

        return self

    @staticmethod
    def fromAction(action):
        #TODO: stub
        self = Animation()
        self.Hash = action.Hash
        self.FrameCount = action.FrameCount
        self.Unknown10 = action.Unknown10
        self.SequenceFrameLimit = action.SequenceFrameLimit
        self.Duration = action.Duration
        self.Unknown1C = action.Unknown1C

        return self

    def toXml(self):
        animNode = Element("Item")

        Xml.CreateTextNode("Hash", self.Hash, animNode)
        Xml.CreateValueNode("Unknown10", self.Unknown10, animNode)
        Xml.CreateValueNode("FrameCount", self.FrameCount, animNode)
        Xml.CreateValueNode("SequenceFrameLimit", self.SequenceFrameLimit, animNode)
        Xml.CreateValueNode("Duration", self.Duration, animNode)
        Xml.CreateTextNode("Unknown1C", self.Unknown10, animNode)

        #TODO: bone ids
        Xml.CreateNode("BoneIds", animNode)

        #TODO: sequences
        Xml.CreateNode("Sequences", animNode)

        return animNode

    def __apply(self):
        for seq in self.Sequences:
            for seqData in seq.SequenceData:
                bone = find_bone_by_tag(seqData.BoneId.BoneId)
                for frame in range(self.FrameCount):
                    seqData.apply(frame, bone)

            bone1 = find_bone_by_tag(23639)
            bone2 = find_bone_by_tag(58271)

            if bone1 is not None and bone2 is not None:
                bone1.matrix = bone2.matrix
                bone1.keyframe_insert(data_path="rotation_quaternion", frame=frame)

            bone1 = find_bone_by_tag(6442)
            bone2 = find_bone_by_tag(51826)

            if bone1 is not None and bone2 is not None:
                bone1.matrix = bone2.matrix
                bone1.keyframe_insert(data_path="rotation_quaternion", frame=frame)


    def toAction(self):
        action = bpy.data.actions.new(self.Hash)
        action.Hash = self.Hash
        action.FrameCount = self.FrameCount
        action.SequenceFrameLimit = self.SequenceFrameLimit
        action.Duration  = self.Duration
        action.Unknown10 = self.Unknown10
        action.Unknown1C = self.Unknown1C

        for ob in find_armatures():
            if ob.animation_data is None:
                ob.animation_data_create()
            ob.animation_data.action = action

        self.__apply()

        return action


class AnimBoneId:
    BoneId = None
    Track = None
    Unk0 = None

    @staticmethod
    def fromXml(node):
        self = AnimBoneId()
        self.BoneId = Xml.ReadValue(node.find("BoneId"), None, int)
        self.Track = Xml.ReadValue(node.find("Track"), None, int)
        self.Unk0 = Xml.ReadValue(node.find("Unk0"), None, int)

        return self
