import bpy
import os
from typing import Optional
from ..cwxml.drawable import YDD, DrawableDictionary, Skeleton
from ..cwxml.fragment import YFT, Fragment
from ..ydr.ydrimport import create_drawable_obj, create_drawable_skel, apply_rotation_limits
from ..sollumz_properties import SollumType
from ..sollumz_preferences import get_import_settings
from ..tools.blenderhelper import create_empty_object, create_blender_object
from ..tools.utils import get_filename

from .. import logger


def import_ydd(filepath: str):
    import_settings = get_import_settings()

    ydd_xml = YDD.from_xml_file(filepath)

    if import_settings.import_ext_skeleton:
        skel_yft = load_external_skeleton(filepath)

        if skel_yft is not None and skel_yft.drawable.skeleton is not None:
            return create_ydd_obj_ext_skel(ydd_xml, filepath, skel_yft)

    return create_ydd_obj(ydd_xml, filepath)


def load_external_skeleton(ydd_filepath: str) -> Optional[Fragment]:
    """Read first yft at ydd_filepath into a Fragment"""
    directory = os.path.dirname(ydd_filepath)

    yft_filepath = get_first_yft_path(directory)

    if yft_filepath is None:
        logger.warning(
            f"Could not find external skeleton yft in directory '{directory}'.")
        return

    logger.info(f"Using '{yft_filepath}' as external skeleton...")

    return YFT.from_xml_file(yft_filepath)


def get_first_yft_path(directory: str):
    for filepath in os.listdir(directory):
        if filepath.endswith(".yft.xml"):
            return os.path.join(directory, filepath)


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
