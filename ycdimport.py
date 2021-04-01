import os
import math 
import xml.etree.ElementTree as ET
from datetime import datetime 

from math import cos
from math import degrees
from math import radians
from math import sin
from math import sqrt 

import bpy
from mathutils import Vector, Matrix, Quaternion
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator

def xml_read_value(node, default=None, formatter=lambda x: x):
    if node is None:
        return default
    
    if 'value' not in node.attrib:
        return default

    return formatter(node.attrib['value'])

def xml_read_text(node, default=None, formatter=lambda x: x):
    if node is None:
        return default
    
    if node.text is None:
        return default

    return formatter(node.text)
class Channel:
    xml = None

    def __init__(self, xml):
        self.xml = xml

    def getValue(self, frame, calcValues):
        return NotImplemented

class ChannelConst(Channel):
    def __init__(self, value):
        super().__init__(None)
        self.value = value

    def getValue(self, frame, calcValues):
        return self.value

class ChannelStaticFloat(Channel):

    value = None

    def __init__(self, xml):
        super().__init__(xml)
        self.value = float(xml.find('Value').get('value'))

    def getValue(self, frame, calcValues):
        return self.value

class ChannelStaticVector(Channel):

    value = None

    def __init__(self, xml):
        super().__init__(xml)
        valueNode = xml.find('Value')
        x = float(valueNode.get('x'))
        y = float(valueNode.get('y'))
        z = float(valueNode.get('z'))
        self.value = Vector((x,y,z))

    def getValue(self, frame, calcValues):
        return self.value


class ChannelStaticQuaternion(Channel):

    value = None

    def __init__(self, xml):
        super().__init__(xml)
        valueNode = xml.find('Value')
        x = float(valueNode.get('x'))
        y = float(valueNode.get('y'))
        z = float(valueNode.get('z'))
        w = float(valueNode.get('w'))
        self.value = Quaternion((w,x,y,z))

    def getValue(self, frame, calcValues):
        return self.value


class ChannelCachedQuaternion1(Channel):

    quatIndex = None

    def __init__(self, xml):
        super().__init__(xml)
        self.quatIndex = int(xml.find('QuatIndex').get('value'))

    def getValue(self, frame, calcValues):
        vecLen = Vector((calcValues[0],calcValues[1],calcValues[2])).length
        return math.sqrt(max(1.0 - vecLen*vecLen, 0))

class ChannelQuantizeFloat(Channel):

    values = None

    def __init__(self, xml):
        super().__init__(xml)

        values_tokens = filter(len, xml.find('Values').text.replace('\n',' ').split(' '))
        self.values = list(map(float, values_tokens))

    def getValue(self, frame, channels):
        return self.values[frame % len(self.values)]

class ChannelIndirectQuantizeFloat(Channel):

    values = None
    frames = None

    def __init__(self, xml):
        super().__init__(xml)
        values_tokens = filter(len, xml.find('Values').text.replace('\n',' ').split(' '))
        self.values = list(map(float, values_tokens))
        frames_tokens = filter(len, xml.find('Frames').text.replace('\n',' ').split(' '))
        self.frames = list(map(int, frames_tokens))

    def getValue(self, frame, channels):
        frameId = self.frames[frame % len(self.frames)]
        return self.values[frameId % len(self.values)]

class ClipDictionary:

    Clips = None
    Animations = None

    def __init__(self, xml):
        self.Clips = []

        for clipNode in xml.find("Clips"):
            self.Clips.append(Clip(clipNode))

        self.Animations = []

        for animNode in xml.find("Animations"):
            anim = Animation(animNode)
            self.Animations.append(anim)
            anim.apply()

    def toObject(self):
        dictNode = bpy.data.objects.new('Clip Dictionary', None)
        bpy.context.collection.objects.link(dictNode)

        for clip in self.Clips:
            clipNode = clip.toObject()
            clipNode.parent = dictNode

        dictNode.sollumtype = "Clip Dictionary"

        return dictNode

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

    def __init__(self, xml):
        self.Hash = xml_read_text(xml.find("Hash"), "", str)
        self.Name = xml_read_text(xml.find("Name"), "", str)
        self.Type = xml_read_value(xml.find("Type"), "", str)
        self.Unknown30 = xml_read_value(xml.find("Unknown30"), 0, int)

        # TODO: Tags
        # TODO: Properties
        # hashes: boneid,left,right,blocked,create,release,destroy,allowed

        self.AnimationHash = xml_read_text(xml.find("AnimationHash"), "", str)
        self.StartTime = xml_read_value(xml.find("StartTime"), 0, float)
        self.EndTime = xml_read_value(xml.find("EndTime"), 0, float)
        self.Rate = xml_read_value(xml.find("Rate"), 0, float)

    def toObject(self):
        clipNode = bpy.data.objects.new(self.Name, None)
        bpy.context.collection.objects.link(clipNode)
        clipNode.sollumtype = "Clip"

        props = clipNode.clip_properties
        props.Hash = self.Hash
        props.Name = self.Name
        props.Type = self.Type
        props.Unknown30 = self.Unknown30
        props.AnimationHash = self.AnimationHash
        props.StartTime = self.StartTime
        props.EndTime = self.EndTime
        props.Rate = self.Rate        

        return clipNode


class Animation:
    Hash = None
    Unknown10 = 0
    FrameCount = None
    SequenceFrameLimit = None
    Duration = None
    Unknown1C = None

    BoneIds = None
    Sequences = None

    def __init__(self, xml):
        self.Hash = xml_read_text(xml.find("Hash"), "", str)
        self.FrameCount = xml_read_value(xml.find("FrameCount"), 1, int)
        self.Unknown10 = xml_read_value(xml.find("Unknown10"), 0, int)
        self.SequenceFrameLimit = xml_read_value(xml.find("SequenceFrameLimit"), 1, int)
        self.Duration = xml_read_value(xml.find("Duration"), 0, float)
        self.Unknown1C = xml_read_value(xml.find("Unknown1C"), "", str)

        self.BoneIds = []
        for boneIdNode in xml.find("BoneIds"):
            self.BoneIds.append(AnimBoneId(boneIdNode))

        self.Sequences = []
        for seqNode in xml.find("Sequences"):
            self.Sequences.append(AnimSequence(self, seqNode))

        self.create_action()

    def apply(self):
        for frame in range(self.FrameCount):
            for seq in self.Sequences:
                for seqData in seq.SequenceData:
                    seqData.apply(frame, seqData.Bone)

            
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


    def create_action(self):
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

        return action


class AnimBoneId:
    BoneId = None
    Track = None
    Unk0 = None

    def __init__(self, xml):
        self.BoneId = xml_read_value(xml.find("BoneId"), None, int)
        self.Track = xml_read_value(xml.find("Track"), None, int)
        self.Unk0 = xml_read_value(xml.find("Unk0"), None, int)

class AnimSequence:
    Hash = None
    FrameCount = None
    SequenceData = []

    def __init__(self, anim, xml):
        self.Hash = xml_read_text(xml.find("Hash"), None, str)
        self.FrameCount = xml_read_value(xml.find("FrameCount"), None, int)

        for seqItem, boneId in zip(xml.find("SequenceData"), anim.BoneIds):
            self.SequenceData.append(AnimSequenceDataItem(seqItem, boneId))

class AnimSequenceDataItem:

    Bone = None
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
            if type(self.Channels[i]) is ChannelCachedQuaternion1:
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
            rotation = bone.bone.convert_local_to_pose(rotation.to_matrix().to_4x4(), bone.bone.matrix.to_4x4(), parent_matrix=bone.bone.parent.matrix.to_4x4(), invert=True)
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

    def __init__(self, xml, boneId):
        self.BoneId = boneId
        self.Bone = find_bone_by_tag(self.BoneId.BoneId)
        channelsNode = xml.find("Channels")

        # allowedBones = ["40269", "28252", "45509", "61163"] # [ "40269", "28252", "61163", "39317"  ]

        # if not boneId in allowedBones:
        #    continue

        #if bone is None:
        #    continue

        self.Channels = []

        for i in range(len(channelsNode)):
            chanNode = channelsNode[i]
            chanType = xml_read_value(chanNode.find('Type'))

            if chanType == 'StaticFloat':
                self.Channels.append(ChannelStaticFloat(chanNode))

            elif chanType == 'QuantizeFloat':  
                self.Channels.append(ChannelQuantizeFloat(chanNode))

            elif chanType == 'IndirectQuantizeFloat':  
                self.Channels.append(ChannelIndirectQuantizeFloat(chanNode))

            elif chanType == 'StaticVector3':
                staticVec = ChannelStaticVector(chanNode)
                quat = staticVec.getValue(0, [0,0,0,0,0])

                self.Channels = [
                    ChannelConst(quat.x),
                    ChannelConst(quat.y),
                    ChannelConst(quat.z),
                ]
            elif chanType == 'StaticQuaternion' and i == 0:
                staticQuat = ChannelStaticQuaternion(chanNode)
                quat = staticQuat.getValue(0, [0,0,0,0,0])
                self.Channels = [
                    ChannelConst(quat.x),
                    ChannelConst(quat.y),
                    ChannelConst(quat.z),
                    ChannelConst(quat.w)
                ]

            elif chanType == 'CachedQuaternion1' or chanType == 'CachedQuaternion2':
                self.Channels.append(ChannelCachedQuaternion1(chanNode))

            else:
                raise Exception('Unknown channel type: ', chanType)

def find_armatures():
    armatures = []
    for obj in bpy.context.scene.collection.objects:
        if isinstance(obj.data, bpy.types.Armature):
            armatures.append(obj)

    return armatures

def find_bone_by_tag(tag):
    for armature_object in find_armatures():

        bpy.context.view_layer.objects.active = armature_object
        bpy.ops.object.mode_set(mode='POSE')

        for bone in armature_object.pose.bones:
            if bone.bone.bone_properties.tag == tag:
                return bone
    return None

def read_bones(root):
    bones = []
    for boneNode in root:
        bone = {}
        bone["BoneId"] = xml_read_value(boneNode.find("BoneId"), None, int)
        bone["Track"] = xml_read_value(boneNode.find("Track"), None, int)
        bone["Unk0"] = xml_read_value(boneNode.find("Unk0"), None, int)
        bones.append(bone)

    return bones


def read_ycd_xml(context, filepath, root):
    
    filename = os.path.basename(filepath[:-8]) 

    clipDict = ClipDictionary(root)
    
    clipDict.toObject()
    
class ImportYcdXml(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ycd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ycd"

    # ImportHelper mixin class uses this
    filename_ext = ".ycd.xml"

    def execute(self, context):
        tree = ET.parse(self.filepath)
        root = tree.getroot() 
        
        read_ycd_xml(context, self.filepath, root) 

        # for obj in objs:
            # context.scene.collection.objects.link(obj)

        return {'FINISHED'}
    
# Only needed if you want to add into a dynamic menu
def menu_func_import_ycd(self, context):
    self.layout.operator(ImportYcdXml.bl_idname, text="Ycd (.ycd.xml)")

def register():
    bpy.utils.register_class(ImportYcdXml)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ycd)

def unregister():
    bpy.utils.unregister_class(ImportYcdXml)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ycd)
