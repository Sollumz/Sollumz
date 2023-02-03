import bpy
import os
from typing import Optional
from ..cwxml.drawable import YDD, DrawableDictionary, Skeleton
from ..cwxml.fragment import YFT, Fragment
from ..ydr.ydrimport import create_drawable_obj, create_drawable_skel, apply_rotation_limits
from ..sollumz_properties import SollumType, SollumzImportSettings
from ..tools.blenderhelper import create_empty_object, create_blender_object
from ..tools.utils import get_filename

from .. import logger


def import_ydd(filepath: str, import_settings: SollumzImportSettings):
    ydd_xml = YDD.from_xml_file(filepath)

    if import_settings.import_ext_skeleton:
        skel_yft = load_external_skeleton(filepath)
        return create_ydd_obj_ext_skel(ydd_xml, filepath, skel_yft)
    else:
        return create_ydd_obj(ydd_xml, filepath)


def load_external_skeleton(ydd_filepath: str):
    directory = os.path.dirname(ydd_filepath)
    ydd_name = get_filename(ydd_filepath)

    yft_filepath = os.path.join(directory, f"{ydd_name}.yft.xml")

    if not os.path.exists(yft_filepath):
        logger.warning(f"External skeleton not found at '{yft_filepath}'!")
        return None

    yft_xml: Fragment = YFT.from_xml_file(yft_filepath)

    return yft_xml


def create_ydd_obj_ext_skel(ydd_xml: DrawableDictionary, filepath: str, external_skel: Fragment):
    """Create ydd object with an external skeleton."""
    name = get_filename(filepath)
    dict_obj = create_armature_parent(name, external_skel)

    for drawable_xml in ydd_xml:
        external_bones = None
        external_armature = None

        if not drawable_xml.skeleton.bones:
            external_bones = external_skel.drawable.skeleton.bones

        if not drawable_xml.skeleton.bones:
            external_armature = dict_obj

        drawable_obj = create_drawable_obj(
            drawable_xml, filepath, external_armature=external_armature, external_bones=external_bones)
        drawable_obj.parent = dict_obj

    return dict_obj


def create_ydd_obj(ydd_xml: DrawableDictionary, filepath: str):

    name = get_filename(filepath)
    dict_obj = create_empty_object(SollumType.DRAWABLE_DICTIONARY, name)

    ydd_skel = find_first_skel(ydd_xml)

    for drawable_xml in ydd_xml:
        if not drawable_xml.skeleton.bones and ydd_skel is not None:
            external_bones = ydd_skel.bones
        else:
            external_bones = None

        drawable_obj = create_drawable_obj(
            drawable_xml, filepath, external_bones=external_bones)
        drawable_obj.parent = dict_obj

    return dict_obj


def create_armature_parent(name: str, skel_yft: Fragment):
    armature = bpy.data.armatures.new(f"{name}.skel")
    dict_obj = create_blender_object(
        SollumType.DRAWABLE_DICTIONARY, name, armature)

    create_drawable_skel(skel_yft.drawable.skeleton, dict_obj)

    rot_limits = skel_yft.drawable.joints.rotation_limits
    if rot_limits:
        apply_rotation_limits(rot_limits, dict_obj)

    return dict_obj


def find_first_skel(ydd_xml: DrawableDictionary) -> Optional[Skeleton]:
    """Find first skeleton in ``ydd_xml``"""
    for drawable_xml in ydd_xml:
        if drawable_xml.skeleton.bones:
            return drawable_xml.skeleton
