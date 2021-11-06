import traceback
from Sollumz.resources.drawable import *
from Sollumz.tools.meshhelper import *
from Sollumz.tools.utils import *
from Sollumz.ydr.ydrexport import drawable_from_object
import Sollumz.tools.jenkhash as Jenkhash
from Sollumz.sollumz_properties import DrawableType


def get_hash(item):
    return Jenkhash.Generate(item[1].name.split(".")[0])


def drawable_dict_from_object(obj, filepath):

    drawable_dict = DrawableDictionary()

    bones = None
    for child in obj.children:
        if child.sollum_type == DrawableType.DRAWABLE and child.type == 'ARMATURE' and len(child.pose.bones) > 0:
            bones = child.pose.bones
            break

    for child in obj.children:
        if child.sollum_type == DrawableType.DRAWABLE:
            drawable = drawable_from_object(child, filepath, bones)
            drawable_dict[drawable.name] = drawable

    drawable_dict.sort(key=get_hash)

    return drawable_dict


def export_ydd(obj, filepath):
    drawable_dict_from_object(obj, filepath).write_xml(filepath)
