from Sollumz.resources.drawable import *
from Sollumz.meshhelper import *
from Sollumz.tools.utils import *
from Sollumz.ydr.ydrexport import drawable_from_object
import Sollumz.tools.jenkhash as Jenkhash


def get_hash(obj):
    return Jenkhash.Generate(obj.name.split(".")[0])


def drawable_dict_from_object(obj):

    drawable_dict = DrawableDictionary()

    bones = None
    for child in obj.children:
        if child.sollum_type == "sollumz_drawable" and child.type == 'ARMATURE' and len(child.pose.bones) > 0:
            bones = child.pose.bones
            break

    for child in obj.children:
        if child.sollum_type == "sollumz_drawable":
            drawable = drawable_from_object(child, bones)
            drawable_dict.value.append(drawable)

    drawable_dict.value.sort(key=get_hash)

    return drawable_dict
