from mathutils import Vector, Quaternion
from collections import Counter

from ...tools import xml as Xml
from .utils import find_bone_by_tag
from .Channel import ChannelConst, ChannelStaticFloat, ChannelQuantizeFloat, ChannelIndirectQuantizeFloat, ChannelCachedQuaternion1, ChannelStaticVector, ChannelStaticQuaternion
import bpy

class AnimSequence:
    Hash = None
    FrameCount = None
    SequenceData = []
    ParentAnimHash = None

    @staticmethod
    def fromXml(node, anim):
        self = AnimSequence()
        self.Hash = Xml.ReadText(node.find("Hash"), None, str)
        self.FrameCount = Xml.ReadValue(node.find("FrameCount"), None, int)
        self.ParentAnimHash = anim.Hash
        print('Parsing anim sequence from xml:', self.Hash)

        for seqItem, boneId in zip(node.find("SequenceData"), anim.BoneIds):
            self.SequenceData.append(AnimSequenceDataItem.fromXml(seqItem, boneId))

        return self

    def toXml(self):
        node = Xml.CreateNode("Item")

        Xml.CreateTextNode("Hash", self.Hash, node)
        Xml.CreateValueNode("FrameCount", self.FrameCount, node)
        seqDataNode = Xml.CreateNode("SequenceData", node)

        for seq in self.SequenceData:
            seqNode = seq.toXml()
            seqDataNode.append(seqNode)

        return node

    def apply(self, armature):

        for seqData in self.SequenceData:
            bone = find_bone_by_tag(armature, seqData.BoneId.BoneId)
            for frame in range(self.FrameCount):
                seqData.apply(frame, bone)

        bone1 = find_bone_by_tag(armature, 23639)
        bone2 = find_bone_by_tag(armature, 58271)

        if bone1 is not None and bone2 is not None:
            bone1.matrix = bone2.matrix
            bone1.keyframe_insert(data_path="rotation_quaternion", frame=frame)

        bone1 = find_bone_by_tag(armature, 6442)
        bone2 = find_bone_by_tag(armature, 51826)

        if bone1 is not None and bone2 is not None:
            bone1.matrix = bone2.matrix
            bone1.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    def toAction(self, armature):
        action = bpy.data.actions.new(self.Hash)
        action.Hash = self.Hash
        action.FrameCount = self.FrameCount
        action.ParentAnimHash = self.ParentAnimHash

        if armature.animation_data is None:
            armature.animation_data_create()
        armature.animation_data.action = action

        self.apply(armature)
        return action

    @staticmethod
    def retrieveAnimSequenceDataFromAction(armature, anim, action):
        pos_frames = {}
        rot_frames = {}
        bones = {}

        for boneIdNode in anim.BoneIds:
            bid = boneIdNode.BoneId
            pos_frames[bid] = []
            rot_frames[bid] = []
            bones[bid] = find_bone_by_tag(armature, bid)

        scene = bpy.context.scene
        armature.animation_data.action = action
        for f in range(scene.frame_start, scene.frame_end+1):
            scene.frame_set(f)

            for boneIdNode in anim.BoneIds:
                bid = boneIdNode.BoneId
                track = boneIdNode.Track
                pbone = bones[bid]

                if track == 0:
                    pos_frames[bid].append(armature.matrix_world @ pbone.head)
                elif track == 1:
                    rot_frames[bid].append(pbone.rotation_quaternion)

        return pos_frames, rot_frames, bones


    @staticmethod
    def fromAction(armature, anim, action):
        self = AnimSequence()
        self.Hash = action.Hash
        self.FrameCount = action.FrameCount
        self.ParentAnimHash = action.ParentAnimHash

        print('Retrieving anim sequence from action:', self.Hash)

        pos_frames, rot_frames, bones = AnimSequence.retrieveAnimSequenceDataFromAction(armature, anim, action)

        for boneIdNode in anim.BoneIds:
            bid = boneIdNode.BoneId
            track = boneIdNode.Track
            if track == 0:
                self.SequenceData.append(AnimSequenceDataItem.fromBone(bones[bid], track, pos_frames[bid]))
            elif track == 1:
                self.SequenceData.append(AnimSequenceDataItem.fromBone(bones[bid], track, rot_frames[bid]))

        return self


class AnimSequenceDataItem:

    #Bone = None
    BoneId = None
    Channels = []

    def apply(self, frame, bone):
        if self.BoneId.Track == 0:
            self.apply_pos(frame, bone)
        elif self.BoneId.Track == 1:
            self.apply_rot(frame, bone)


    def apply_pos(self, frame, bone):
        if bone is None:
            return

        values = self.getValue(frame)
        bone.location = Vector(values)
        bone.keyframe_insert(data_path="location", frame=frame)

    def apply_rot(self, frame, bone):
        if bone is None:
            return

        values = self.getValue(frame)

        for i in range(len(self.Channels)):
            if isinstance(self.Channels[i], ChannelCachedQuaternion1):
                cached = self.Channels[i]
                val = cached.getValue(frame, values)
                if cached.quatIndex == 0:
                    values = [ val, values[0], values[1], values[2], 0 ]
                elif cached.quatIndex == 1:
                    values = [ values[0], val, values[1], values[2], 0 ]
                elif cached.quatIndex == 2:
                    values = [ values[0], values[1], val, values[2], 0 ]
                elif cached.quatIndex == 3:
                    values = [ values[0], values[1], values[2], val, 0 ]

        rotation = Quaternion((values[3], values[0], values[1], values[2]))

        if bone.bone.parent is not None:
            rotation = bone.bone.convert_local_to_pose(rotation.to_matrix().to_4x4(), bone.bone.matrix.to_4x4(), parent_matrix=bone.bone.parent.matrix_local.to_4x4(), invert=True)
        else:
            rotation = bone.bone.convert_local_to_pose(rotation.to_matrix().to_4x4(), bone.bone.matrix.to_4x4(), invert=True)

        bone.rotation_quaternion = rotation.to_quaternion()
        bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)

    def getValue(self, frame):
        values = []
        for i in range(len(self.Channels)):
            while len(values) <= i:
                values.append(None)

            chan = self.Channels[i]
            if chan is not None:
                values[i] = chan.getValue(frame, values)

        return values

    @staticmethod
    def fromXml(node, boneId):
        self = AnimSequenceDataItem()
        self.BoneId = boneId
        #self.Bone = find_bone_by_tag(self.BoneId.BoneId)
        channelsNode = node.find("Channels")

        # allowedBones = ["40269", "28252", "45509", "61163"] # [ "40269", "28252", "61163", "39317"  ]

        # if not boneId in allowedBones:
        #    continue

        #if bone is None:
        #    continue

        self.Channels = []

        for i, chanNode in enumerate(channelsNode):
            chanType = Xml.ReadValue(chanNode.find('Type'))

            if chanType == 'StaticFloat':
                self.Channels.append(ChannelStaticFloat.fromXml(chanNode))

            elif chanType == 'QuantizeFloat':
                self.Channels.append(ChannelQuantizeFloat.fromXml(chanNode))

            elif chanType == 'IndirectQuantizeFloat':
                self.Channels.append(ChannelIndirectQuantizeFloat.fromXml(chanNode))

            elif chanType == 'StaticVector3':
                staticVec = ChannelStaticVector.fromXml(chanNode)
                quat = staticVec.getValue(0, [0,0,0,0,0])

                self.Channels = [
                    ChannelConst(quat.x),
                    ChannelConst(quat.y),
                    ChannelConst(quat.z),
                ]
            elif chanType == 'StaticQuaternion' and i == 0:
                staticQuat = ChannelStaticQuaternion.fromXml(chanNode)
                quat = staticQuat.getValue(0, [0,0,0,0,0])
                self.Channels = [
                    ChannelConst(quat.x),
                    ChannelConst(quat.y),
                    ChannelConst(quat.z),
                    ChannelConst(quat.w)
                ]

            elif chanType == 'CachedQuaternion1' or chanType == 'CachedQuaternion2':
                self.Channels.append(ChannelCachedQuaternion1.fromXml(chanNode))

            else:
                raise Exception('Unknown channel type: ', chanType)

        return self

    def toXml(self):
        node = Xml.CreateNode("Item")
        channelsNode = Xml.CreateNode("Channels", node)

        for chan in self.Channels:
            channelsNode.append(chan.toXml())

        return node

    @staticmethod
    def genProperChannelFromValues(values):
        counter = Counter(values)
        numUniq = len(counter)
        if numUniq == 1:
            return ChannelStaticFloat(values[0])

        return ChannelQuantizeFloat(values)

    @staticmethod
    def fromBone(pbone, track, frames):
        self = AnimSequenceDataItem()

        self.BoneId = pbone.bone.bone_properties.tag
        self.Channels = []

        if track == 0:
            channel_x = list(map(lambda vec: vec.x, frames))
            channel_y = list(map(lambda vec: vec.y, frames))
            channel_z = list(map(lambda vec: vec.z, frames))
            self.Channels.append(AnimSequenceDataItem.genProperChannelFromValues(channel_x))
            self.Channels.append(AnimSequenceDataItem.genProperChannelFromValues(channel_y))
            self.Channels.append(AnimSequenceDataItem.genProperChannelFromValues(channel_z))

        elif track == 1:
            channel_x = list(map(lambda quat: quat.x, frames))
            channel_y = list(map(lambda quat: quat.y, frames))
            channel_z = list(map(lambda quat: quat.z, frames))
            channel_w = list(map(lambda quat: quat.w, frames))
            self.Channels.append(AnimSequenceDataItem.genProperChannelFromValues(channel_x))
            self.Channels.append(AnimSequenceDataItem.genProperChannelFromValues(channel_y))
            self.Channels.append(AnimSequenceDataItem.genProperChannelFromValues(channel_z))
            self.Channels.append(AnimSequenceDataItem.genProperChannelFromValues(channel_w))

        return self
