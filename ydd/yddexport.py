import os
from ..cwxml.drawable import DrawableDictionary
from ..ydr.ydrexport import drawable_from_object, get_used_materials, texture_dictionary_from_materials
from ..tools.blenderhelper import remove_number_suffix
from ..tools import jenkhash
from ..sollumz_properties import SollumType


def get_hash(item):
    return jenkhash.Generate(item.name.split(".")[0])


def drawable_dict_from_object(exportop, obj, filepath, export_settings):

    drawable_dict = DrawableDictionary()

    bones = None
    for child in obj.children:
        if child.sollum_type == SollumType.DRAWABLE and child.type == "ARMATURE" and len(child.pose.bones) > 0:
            bones = child.pose.bones
            break

    for child in obj.children:
        if child.sollum_type == SollumType.DRAWABLE:
            drawable = drawable_from_object(
                exportop, child, filepath, bones, None, write_textures=False)

            if export_settings.exclude_skeleton:
                drawable.skeleton = None

            drawable_dict.append(drawable)

    # Write embedded texture dict folder
    ydd_mats = get_used_materials(obj)
    foldername = remove_number_suffix(obj.name.lower())
    texture_dictionary_from_materials(
        foldername, ydd_mats, os.path.dirname(filepath))

    drawable_dict.sort(key=get_hash)

    return drawable_dict


def export_ydd(exportop, obj, filepath, export_settings):
    drawable_dict_from_object(exportop, obj, filepath,
                              export_settings).write_xml(filepath)
