from mathutils import Vector, Quaternion

from ...tools import xml as Xml
from .utils import find_bone_by_tag
from .Channel import ChannelConst, ChannelStaticFloat, ChannelQuantizeFloat, ChannelIndirectQuantizeFloat, ChannelCachedQuaternion1, ChannelStaticVector, ChannelStaticQuaternion

class AnimSequence:
    Hash = None
    FrameCount = None
    SequenceData = []

    @staticmethod
    def fromXml(node, anim):
        self = AnimSequence()
        self.Hash = Xml.ReadText(node.find("Hash"), None, str)
        self.FrameCount = Xml.ReadValue(node.find("FrameCount"), None, int)

        for seqItem, boneId in zip(node.find("SequenceData"), anim.BoneIds):
            self.SequenceData.append(AnimSequenceDataItem.fromXml(seqItem, boneId))

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
