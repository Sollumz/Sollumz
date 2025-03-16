import bpy
from bpy.types import (
    Object,
)
import os
from typing import Optional
from ..cwxml.drawable import YDD, Drawable, DrawableDictionary
from ..cwxml.fragment import YFT, Fragment
from ..ydr.ydrimport import create_drawable_obj, create_drawable_skel, apply_rotation_limits
from ..sollumz_properties import SollumType
from ..sollumz_preferences import get_import_settings
from ..tools.blenderhelper import create_empty_object, create_blender_object
from ..tools.utils import get_filename

from .. import logger


def import_ydd(filepath: str) -> Object:
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


def get_first_yft_path(directory: str) -> Optional[str]:
    for filepath in os.listdir(directory):
        if filepath.endswith(".yft.xml"):
            return os.path.join(directory, filepath)

    return None


def create_ydd_obj(ydd_xml: DrawableDictionary, filepath: str, external_skel: Optional[Fragment]) -> Object:
    name = get_filename(filepath)
    drawable_with_skeleton = (
        find_first_drawable_with_skeleton(ydd_xml)
        if external_skel is None
        else external_skel.drawable
    )

    if drawable_with_skeleton is None:
        dict_obj = create_empty_object(SollumType.DRAWABLE_DICTIONARY, name)
        external_armature = None
        external_bones = None
    else:
        # Use the same skeleton for all drawables in the dictionary. While drawables can technically have different
        # skeletons each, this does not occur in the base game. All drawables with a skeleton in a dictionary have
        # the same skeleton (same bones, same signature).
        # Before we created a Blender armature for each of these skeletons but it is a better UX to have a single
        # armature in the root object and instead have a per-drawable property to indicate if it should be exported
        # with skeleton (`sz_dwd_export_with_skeleton`).
        dict_obj = create_armature_parent(name, drawable_with_skeleton)
        external_armature = dict_obj
        external_bones = drawable_with_skeleton.skeleton.bones

    for drawable_xml in ydd_xml:
        # checking for skeleton here because `create_drawable_obj` assigns the external skeleton as the drawable skeleton
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


def create_armature_parent(name: str, drawable_with_skeleton: Drawable) -> Object:
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

    return None
