import bpy
from ..cwxml.drawable import DrawableDictionary
from ..ydr.ydrexport import create_drawable_xml, write_embedded_textures
from ..tools import jenkhash
from ..sollumz_properties import SollumType
from ..sollumz_preferences import get_export_settings


def export_ydd(ydd_obj: bpy.types.Object, filepath: str) -> bool:
    export_settings = get_export_settings()

    ydd_xml = create_ydd_xml(ydd_obj, export_settings.exclude_skeleton)

    write_embedded_textures(ydd_obj, filepath)

    ydd_xml.write_xml(filepath)
    return True


def create_ydd_xml(ydd_obj: bpy.types.Object, exclude_skeleton: bool = False):
    ydd_xml = DrawableDictionary()

    ydd_armature = find_ydd_armature(
        ydd_obj) if ydd_obj.type != "ARMATURE" else ydd_obj

    for child in ydd_obj.children:
        if child.sollum_type != SollumType.DRAWABLE:
            continue

        if child.type != "ARMATURE":
            armature_obj = ydd_armature
        else:
            armature_obj = None

        drawable_xml = create_drawable_xml(child, armature_obj=armature_obj)

        if exclude_skeleton or child.type != "ARMATURE":
            drawable_xml.skeleton = None

        ydd_xml.append(drawable_xml)

    ydd_xml.sort(key=get_hash)

    return ydd_xml


def find_ydd_armature(ydd_obj: bpy.types.Object):
    """Find first drawable with an armature in ``ydd_obj``."""
    for child in ydd_obj.children:
        if child.type == "ARMATURE":
            return child


def get_hash(item):
    return jenkhash.Generate(item.name.split(".")[0])
