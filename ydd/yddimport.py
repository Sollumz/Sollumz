import bpy
import os
from typing import Optional
from ..cwxml.drawable import YDD, Drawable, DrawableDictionary, Skeleton
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

    external_skel = None
    if import_settings.import_ext_skeleton:
        skel_yft = load_external_skeleton(filepath)

        if skel_yft is not None and skel_yft.drawable.skeleton is not None:
            external_skel = skel_yft

    return create_ydd_obj(ydd_xml, filepath, external_skel)


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


def create_ydd_obj(ydd_xml: DrawableDictionary, filepath: str, external_skel: Optional[Fragment]):

    name = get_filename(filepath)
    skel_drawable = find_first_drawable_with_skeleton(ydd_xml) if external_skel is None else external_skel.drawable

    if skel_drawable is None:
        dict_obj = create_empty_object(SollumType.DRAWABLE_DICTIONARY, name)
        external_armature = None
        external_bones = None
    else:
        dict_obj = create_armature_parent(name, skel_drawable)
        external_armature = dict_obj  # use the same skeleton for all drawables in the dictionary
        external_bones = skel_drawable.skeleton.bones

    for drawable_xml in ydd_xml:
        # checking it here because `create_drawable_obj` modifies the skeleton
        has_its_own_skeleton = bool(drawable_xml.skeleton.bones)

        drawable_obj = create_drawable_obj(
            drawable_xml,
            filepath,
            external_armature=external_armature,
            external_bones=external_bones
        )
        drawable_obj.parent = dict_obj
        drawable_obj.sz_dwd_export_with_skeleton = has_its_own_skeleton

    return dict_obj


def create_armature_parent(name: str, drawable_with_skeleton: Drawable):
    armature = bpy.data.armatures.new(f"{name}.skel")
    dict_obj = create_blender_object(SollumType.DRAWABLE_DICTIONARY, name, armature)

    create_drawable_skel(drawable_with_skeleton.skeleton, dict_obj)

    rot_limits = drawable_with_skeleton.joints.rotation_limits
    if rot_limits:
        apply_rotation_limits(rot_limits, dict_obj)

    return dict_obj


def find_first_drawable_with_skeleton(ydd_xml: DrawableDictionary) -> Optional[Drawable]:
    """Find first skeleton in ``ydd_xml``"""
    for drawable_xml in ydd_xml:
        if drawable_xml.skeleton.bones:
            return drawable_xml

    return drawable_xml
