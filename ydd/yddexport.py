import bpy
from typing import Optional
from ..cwxml.drawable import DrawableDictionary
from ..cwxml.cloth import ClothDictionary
from ..ydr.ydrexport import create_drawable_xml, write_embedded_textures
from ..ydr.cloth_char import cloth_char_export_dictionary
from ..ydr.cloth_diagnostics import (
    cloth_enter_export_context,
    cloth_export_context,
)
from ..tools import jenkhash
from ..sollumz_properties import SollumType
from ..sollumz_preferences import get_export_settings


def export_ydd(ydd_obj: bpy.types.Object, filepath: Optional[str]) -> bool:
    """If filepath is None, a dry run is done and no files are written."""
    export_settings = get_export_settings()

    with cloth_enter_export_context(ydd_obj):
        # Export a cloth dictionary .yld.xml if there is any cloth in the drawable dictionary
        yld_xml = cloth_char_export_dictionary(ydd_obj)

        ydd_xml = create_ydd_xml(ydd_obj, export_settings.exclude_skeleton, yld_xml)

    if filepath:
        if yld_xml is not None:
            yld_xml.sort(key=get_hash)
            from .yddimport import make_yld_filepath
            yld_filepath = make_yld_filepath(filepath)
            yld_xml.write_xml(yld_filepath)

        write_embedded_textures(ydd_obj, filepath)

        ydd_xml.write_xml(filepath)
    return True


def create_ydd_xml(
    ydd_obj: bpy.types.Object,
    exclude_skeleton: bool = False,
    yld_xml: Optional[ClothDictionary] = None,
):
    ydd_xml = DrawableDictionary()

    ydd_armature = find_ydd_armature(ydd_obj) if ydd_obj.type != "ARMATURE" else ydd_obj

    for child in ydd_obj.children:
        if child.sollum_type != SollumType.DRAWABLE:
            continue

        if child.type != "ARMATURE":
            armature_obj = ydd_armature
        else:
            armature_obj = None

        if yld_xml is not None:
            from ..tools.blenderhelper import remove_number_suffix
            drawable_name = remove_number_suffix(child.name)
            cloth = next((c for c in yld_xml if c.name == drawable_name), None)
        else:
            cloth = None

        with cloth_export_context().enter_drawable_context(child):
            drawable_xml = create_drawable_xml(child, armature_obj=armature_obj, char_cloth_xml=cloth)

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
    return jenkhash.name_to_hash(item.name.split(".")[0])
