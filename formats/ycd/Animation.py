from xml.etree.ElementTree import Element
import bpy

from ...tools import xml as Xml
from .utils import find_armatures
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

        print('Parsing anim from xml:', self.Hash)

        self.BoneIds = []
        for boneIdNode in node.find("BoneIds"):
            self.BoneIds.append(AnimBoneId.fromXml(boneIdNode))

        self.Sequences = []
        for seqNode in node.find("Sequences"):
            self.Sequences.append(AnimSequence.fromXml(seqNode, self))

        return self

    @staticmethod
    def fromObject(obj):
        self = Animation()

        props = obj.anim_properties

        self.Hash = props.Hash
        self.FrameCount = props.FrameCount
        self.Unknown10 = props.Unknown10
        self.SequenceFrameLimit = props.SequenceFrameLimit
        self.Duration = props.Duration
        self.Unknown1C = props.Unknown1C

        armatures = find_armatures()
        assert len(armatures) > 0

        armature = armatures[0]

        self.BoneIds = []
        self.Sequences = []

        for pbone in armature.pose.bones:
            bone = pbone.bone
            tag = pbone.bone.bone_properties.tag

            self.BoneIds.append(AnimBoneId(tag, 0, 0))
            self.BoneIds.append(AnimBoneId(tag, 1, 0))


        for act in bpy.data.actions:
            if act.ParentAnimHash == self.Hash:
                self.Sequences.append(AnimSequence.fromAction(armature, self, act))

        return self

    def toXml(self):
        animNode = Element("Item")

        Xml.CreateTextNode("Hash", self.Hash, animNode)
        Xml.CreateValueNode("Unknown10", self.Unknown10, animNode)
        Xml.CreateValueNode("FrameCount", self.FrameCount, animNode)
        Xml.CreateValueNode("SequenceFrameLimit", self.SequenceFrameLimit, animNode)
        Xml.CreateValueNode("Duration", self.Duration, animNode)
        Xml.CreateTextNode("Unknown1C", self.Unknown10, animNode)

        boneIdsNode = Xml.CreateNode("BoneIds", animNode)
        sequencesNode = Xml.CreateNode("Sequences", animNode)

        for boneId in self.BoneIds:
            boneIdsNode.append(boneId.toXml())

        for seq in self.Sequences:
            sequencesNode.append(seq.toXml())

        return animNode

    def toObject(self):
        armature = find_armatures()[0]

        obj = bpy.data.objects.new(self.Hash, None)
        bpy.context.collection.objects.link(obj)
        obj.sollumtype = "Animation"

        props = obj.anim_properties

        props.Hash = self.Hash
        props.FrameCount = self.FrameCount
        props.SequenceFrameLimit = self.SequenceFrameLimit
        props.Duration  = self.Duration
        props.Unknown10 = self.Unknown10
        props.Unknown1C = self.Unknown1C

        for seq in self.Sequences:
            print('Converting sequence to action', seq.Hash)
            seq.toAction(armature)

        return obj


class AnimBoneId:
    BoneId = None
    Track = None
    Unk0 = None

    def __init__(self, BoneId = None, Track = None, Unk0 = None):
        self.BoneId = BoneId
        self.Track = Track
        self.Unk0 = Unk0

    @staticmethod
    def fromXml(node):
        self = AnimBoneId()
        self.BoneId = Xml.ReadValue(node.find("BoneId"), None, int)
        self.Track = Xml.ReadValue(node.find("Track"), None, int)
        self.Unk0 = Xml.ReadValue(node.find("Unk0"), None, int)

        return self

    def toXml(self):
        node = Element("Item")
        Xml.CreateValueNode("BoneId", self.BoneId, node)
        Xml.CreateValueNode("Track", self.Track, node)
        Xml.CreateValueNode("Unk0", self.Unk0, node)
        return node
