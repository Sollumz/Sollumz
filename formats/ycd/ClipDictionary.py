from xml.etree import ElementTree
from xml.etree.ElementTree import Element, SubElement, Comment, tostring

import bpy

from .Clip import Clip
from .Animation import Animation

def findAnimatedObject(context):
    objects = context.scene.objects
    for obj in objects:
        if obj.animation_data is not None:
            return obj

    return None

class ClipDictionary:

    Clips = None
    Animations = None

    @staticmethod
    def fromXml(node):
        self = ClipDictionary()
        self.Clips = []

        print('Parsing clip dictionary from xml')

        for clipNode in node.find("Clips"):
            self.Clips.append(Clip.fromXml(clipNode))

        self.Animations = []

        for animNode in node.find("Animations"):
            self.Animations.append(Animation.fromXml(animNode))

        return self

    def toObject(self):
        dictNode = bpy.data.objects.new('Clip Dictionary', None)
        bpy.context.collection.objects.link(dictNode)

        print('Creating clip objects')
        for clip in self.Clips:
            clipNode = clip.toObject()
            clipNode.parent = dictNode

        print('Creating anim objects')
        for anim in self.Animations:
            print('Creating anim', anim.Hash)
            animNode = anim.toObject()
            animNode.parent = dictNode

        dictNode.sollumtype = "Clip Dictionary"

        return dictNode

    @staticmethod
    def fromObject(obj):
        self = ClipDictionary()
        self.Clips = []
        self.Animations = []

        for node in obj.children:
            if node.sollumtype == "Clip":
                clip = Clip.fromObject(node)
                self.Clips.append(clip)
            elif node.sollumtype == "Animation":
                anim = Animation.fromObject(node)
                self.Animations.append(anim)

        return self

    def toXml(self):
        clipDictNode = Element("ClipDictionary")

        clipsNode = Element("Clips")
        animsNode = Element("Animations")

        for clip in self.Clips:
            clipsNode.append(clip.toXml())

        for anim in self.Animations:
            animsNode.append(anim.toXml())

        clipDictNode.append(clipsNode)
        clipDictNode.append(animsNode)

        return clipDictNode
