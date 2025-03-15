import bpy
from ..cwxml.drawable import DrawableDictionary
from ..ydr.ydrexport import create_drawable_xml, write_embedded_textures
from ..tools import jenkhash
from ..sollumz_properties import SollumType
from ..sollumz_preferences import get_export_settings
from .. import logger


def export_ydd(ydd_obj: bpy.types.Object, filepath: str) -> bool:
    ydd_xml = create_ydd_xml(ydd_obj)

    write_embedded_textures(ydd_obj, filepath)

    ydd_xml.write_xml(filepath)
    return True


def create_ydd_xml(ydd_obj: bpy.types.Object):
    ydd_xml = DrawableDictionary()

    ydd_armature = ydd_obj if ydd_obj.type == "ARMATURE" else None

    for child in ydd_obj.children:
        if child.sollum_type != SollumType.DRAWABLE:
            continue

        if child.type == "ARMATURE":
            logger.warning(
                f"Armature of drawable '{child.name}' will be ignored! The armature must be in the drawable dictionary "
                f"'{ydd_obj.name}'."
            )

        drawable_xml = create_drawable_xml(child, armature_obj=ydd_armature)

        if not child.sz_dwd_export_with_skeleton:
            drawable_xml.skeleton = None

        ydd_xml.append(drawable_xml)

    ydd_xml.sort(key=get_hash)

    return ydd_xml


def get_hash(item):
    return jenkhash.name_to_hash(item.name.split(".")[0])
