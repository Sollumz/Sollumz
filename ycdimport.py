import bpy
import os
import xml.etree.ElementTree as ET
from mathutils import Vector, Matrix, Quaternion
import math 
import bmesh
from bpy_extras.io_utils import ImportHelper
from bpy.props import StringProperty, BoolProperty, EnumProperty
from bpy.types import Operator
from datetime import datetime 
import random 
from math import cos
from math import degrees
from math import radians
from math import sin
from math import sqrt 

from . import collisionmatoperators
from .tools import meshgen as MeshGen

class Channel:
    xml = None

    def __init__(self, xml):
        self.xml = xml

    def getValue(self, frame):
        return NotImplemented

class ChannelConst(Channel):
    def __init__(self, value):
        self.value = value

    def getValue(self, frame, calcValues):
        return self.value

class ChannelStaticFloat(Channel):

    value = None

    def __init__(self, xml):
        self.value = float(xml.find('Value').get('value'))

    def getValue(self, frame, calcValues):
        return self.value

class ChannelStaticVector(Channel):

    value = None

    def __init__(self, xml):
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
        self.quatIndex = int(xml.find('QuatIndex').get('value'))

    def getValue(self, frame, calcValues):
        vecLen = Vector((calcValues[0],calcValues[1],calcValues[2])).length
        return math.sqrt(max(1.0 - vecLen*vecLen, 0))

class ChannelQuantizeFloat(Channel):

    values = None

    def __init__(self, xml):
        values_tokens = filter(len, xml.find('Values').text.replace('\n',' ').split(' '))
        self.values = list(map(float, values_tokens))

    def getValue(self, frame, channels):
        return self.values[frame % len(self.values)]

class ChannelIndirectQuantizeFloat(Channel):

    values = None
    frames = None

    def __init__(self, xml):
        values_tokens = filter(len, xml.find('Values').text.replace('\n',' ').split(' '))
        self.values = list(map(float, values_tokens))
        frames_tokens = filter(len, xml.find('Frames').text.replace('\n',' ').split(' '))
        self.frames = list(map(int, frames_tokens))

    def getValue(self, frame, channels):
        frameId = self.frames[frame % len(self.frames)]
        return self.values[frameId % len(self.values)]


def find_bone_by_tag(tag):
    armature_object = bpy.context.scene.objects['head_000_r']

    bpy.context.view_layer.objects.active = armature_object
    bpy.ops.object.mode_set(mode='POSE')

    for bone in armature_object.pose.bones:
        if str(bone.bone.bone_properties.tag) == tag:
            return bone
    return None


def read_sequence_item_pos(bone, channels):

    FrameCount = 113

    channels_out = [None]*3

    for i in range(len(channels)):
        chan = channels[i]
        chanType = chan.find('Type').attrib["value"]

        if chanType == 'StaticFloat':
            channels_out[i] = ChannelStaticFloat(chan)

        elif chanType == 'QuantizeFloat':  
            channels_out[i] = ChannelQuantizeFloat(chan)

        elif chanType == 'IndirectQuantizeFloat':  
            channels_out[i] = ChannelIndirectQuantizeFloat(chan)

        elif chanType == 'StaticVector3':
            staticVec = ChannelStaticVector(chan)
            quat = staticVec.getValue(0, [0,0,0,0,0])
            channels_out[0] = ChannelConst(quat.x)
            channels_out[1] = ChannelConst(quat.y)
            channels_out[2] = ChannelConst(quat.z)

        else:
            raise Exception('Unknown channel type: ', chanType)

    for frame in range(FrameCount):
        values = [0,0,0]
        for i in range(len(channels_out)):
            if not channels_out[i] is None:
                values[i] = channels_out[i].getValue(frame, values)

        bone.location = Vector(values)
        bone.keyframe_insert(data_path="location", frame=frame)
        
    return None

def read_sequence_item_rot(bone, channels):

    FrameCount = 113

    channels_out = [None]*5

    for i in range(len(channels)):
        chan = channels[i]
        chanType = chan.find('Type').attrib["value"]

        if chanType == 'StaticFloat':
            channels_out[i] = ChannelStaticFloat(chan)
        elif chanType == 'StaticQuaternion' and i == 0:
            staticQuat = ChannelStaticQuaternion(chan)
            quat = staticQuat.getValue(0, [0,0,0,0,0])
            channels_out[0] = ChannelConst(quat.x)
            channels_out[1] = ChannelConst(quat.y)
            channels_out[2] = ChannelConst(quat.z)
            channels_out[3] = ChannelConst(quat.w)

        elif chanType == 'QuantizeFloat':  
            channels_out[i] = ChannelQuantizeFloat(chan)
        elif chanType == 'IndirectQuantizeFloat':  
            channels_out[i] = ChannelIndirectQuantizeFloat(chan)
        elif chanType == 'CachedQuaternion1' or chanType == 'CachedQuaternion2':
            channels_out[i] = ChannelCachedQuaternion1(chan)
        else:
            raise Exception('Unknown channel type: ', chanType)

    for frame in range(FrameCount):
        values = [0,0,0,0,0]
        for i in range(len(channels_out)):
            if not channels_out[i] is None:
                values[i] = channels_out[i].getValue(frame, values)

        for i in range(len(channels_out)):
            if type(channels_out[i]) is ChannelCachedQuaternion1:
                cached = channels_out[i]
                val = cached.getValue(frame, values)
                if cached.quatIndex == 0:
                    values = [ val, values[0], values[1], values[2], 0 ]
                elif cached.quatIndex == 1:
                    values = [ values[0], val, values[1], values[2], 0 ]
                elif cached.quatIndex == 2:
                    values = [ values[0], values[1], val, values[2], 0 ]
                elif cached.quatIndex == 3:
                    values = [ values[0], values[1], values[2], val, 0 ]


        #print(bone.bone.matrix.inverted_safe())

        #armature_mat = bone.bone.matrix_local
        rotation = Quaternion((values[3], values[0], values[1], values[2]))

        if bone.bone.parent is not None:
            rotation = bone.bone.convert_local_to_pose(rotation.to_matrix().to_4x4(), bone.bone.matrix.to_4x4(), parent_matrix=bone.bone.parent.matrix.to_4x4(), invert=True)
        else:
            rotation = bone.bone.convert_local_to_pose(rotation.to_matrix().to_4x4(), bone.bone.matrix.to_4x4(), invert=True)


        bone.rotation_quaternion = rotation.to_quaternion()
        #bone.matrix = rotation
        bone.keyframe_insert(data_path="rotation_quaternion", frame=frame)
        
    return None

def read_sequence(root, bones):
    sequenceData = root.find("SequenceData")

    for seqItem, boneNode in zip(sequenceData, bones):
        boneId = boneNode["BoneId"]
        bone = find_bone_by_tag(boneId)
        channels = seqItem.find("Channels")

        # allowedBones = ["40269", "28252", "45509", "61163"] # [ "40269", "28252", "61163", "39317"  ]

        # if not boneId in allowedBones:
        #    continue

        if bone is None:
            continue

        if boneNode["Track"] == "0": # Position
            read_sequence_item_pos(bone, channels)
        if boneNode["Track"] == "1": # Rotation
            read_sequence_item_rot(bone, channels)

    
    return None

def read_bones(root):
    bones = []
    for boneNode in root:
        bone = {}
        bone["BoneId"] = boneNode.find("BoneId").attrib["value"]
        bone["Track"] = boneNode.find("Track").attrib["value"]
        bone["Unk0"] = boneNode.find("Unk0").attrib["value"]
        bones.append(bone)

    return bones

def read_animation(root):
    hashname = root.find("Hash").text

    bones = read_bones(root.find("BoneIds"))
    sequences = root.find("Sequences")

    action = bpy.data.actions.new(hashname)
    
    ob = bpy.context.scene.objects['head_000_r']

    if ob.animation_data is None:
        ob.animation_data_create()

    ob.animation_data.action = action

    for sequence in sequences:
        read_sequence(sequence, bones)

    return None

def read_clip_dict(name, root):
    clips = root.find("Clips") 
    animations = root.find("Animations") 

    actions = []

    for anim in animations:
        read_animation(anim)
        #action = read_animation(anim)
        #actions.append(action)

    return actions

def read_ycd_xml(context, filepath, root):
    
    filename = os.path.basename(filepath[:-8]) 
    
    actions = read_clip_dict(filename, root)
    
    return actions
    
class ImportYcdXml(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ycd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ycd"

    # ImportHelper mixin class uses this
    filename_ext = ".ycd.xml"

    def execute(self, context):
        tree = ET.parse(self.filepath)
        root = tree.getroot() 
        
        actions = read_ycd_xml(context, self.filepath, root) 

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
