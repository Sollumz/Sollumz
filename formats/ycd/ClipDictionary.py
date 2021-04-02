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

        for clipNode in node.find("Clips"):
            self.Clips.append(Clip.fromXml(clipNode))

        self.Animations = []

        for animNode in node.find("Animations"):
            anim = Animation.fromXml(animNode)
            anim.toAction()
            self.Animations.append(anim)

        return self

    def toObject(self):
        dictNode = bpy.data.objects.new('Clip Dictionary', None)
        bpy.context.collection.objects.link(dictNode)

        for clip in self.Clips:
            clipNode = clip.toObject()
            clipNode.parent = dictNode

        dictNode.sollumtype = "Clip Dictionary"

        return dictNode

    @staticmethod
    def fromObject(obj):
        self = ClipDictionary()
        self.Clips = []
        self.Animations = []

        for clipNode in obj.children:
            clip = Clip.fromObject(clipNode)
            self.Clips.append(clip)

        return self

    def toXml(self):
        clipDictNode = Element("ClipDictionary")

        clipsNode = Element("Clips")
        animsNode = Element("Animations")

        for clip in self.Clips:
            clipsNode.append(clip.toXml())

        for act in bpy.data.actions:
            anim = Animation.fromAction(act)
            animsNode.append(anim.toXml())

        clipDictNode.append(clipsNode)
        clipDictNode.append(animsNode)

        return clipDictNode
