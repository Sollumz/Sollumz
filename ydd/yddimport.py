import bpy
from bpy.types import (
    Object,
)
import os
from typing import Optional, NamedTuple
from collections import defaultdict
from ..cwxml.drawable import YDD, Drawable, DrawableDictionary, Skeleton, Bone
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
        # Use the same skeleton for all drawables in the dictionary. In the base game only difference in skeletons in
        # the same dictionary are the ped facial bones, where each head drawable has its own facial bones. We merge all
        # these sets in the same skeleton.
        # Before we created a Blender armature for each of these skeletons but it is a better UX to have a single
        # armature in the root object and instead have a per-drawable property to indicate if it should be exported
        # with skeleton (`sz_dwd_export_with_skeleton`).
        # TODO: only do this with ped drawable dictionaries
        skel, facials_root = merge_skeleton_facial_roots(ydd_xml, drawable_with_skeleton.skeleton)
        drawable_with_skeleton.skeleton = skel
        dict_obj = create_armature_parent(name, drawable_with_skeleton)
        external_armature = dict_obj
        external_bones = drawable_with_skeleton.skeleton.bones

        # Assign each facial bones set to their own collection so they can be easily hidden away
        armature: bpy.types.Armature = dict_obj.data
        facial_bones_coll = armature.collections.new("FACIAL_BONES")
        for variation_index, (_, facial_root) in facials_root.items():
            variation_coll = armature.collections.new(f"FACIAL_{variation_index:03}", parent=facial_bones_coll)

            def _assign(b: BoneHierarchy):
                variation_coll.assign(armature.bones[b.bone.name])
                for c in b.children:
                    _assign(c)
            _assign(facial_root)

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


class BoneHierarchy(NamedTuple):
    bone: Bone
    children: list["BoneHierarchy"]


def build_bone_hierarchy(skeleton: Skeleton, root_bone: Bone) -> BoneHierarchy:
    bones_by_parent = defaultdict(list)
    for bone in skeleton.bones:
        bones_by_parent[bone.parent_index].append(bone)

    def _build_hierarchy(bone: Bone, depth: int = 0) -> BoneHierarchy:
        hier = BoneHierarchy(bone, [])
        for child_bone in bones_by_parent[bone.index]:
            child_hier = _build_hierarchy(child_bone, depth + 1)
            hier.children.append(child_hier)
        return hier

    return _build_hierarchy(root_bone)


FACIAL_ROOT_TAG = 65068


def find_skeleton_facial_bones_hierarchy(skeleton: Skeleton) -> Optional[BoneHierarchy]:
    bone_by_tag = {bone.tag: bone for bone in skeleton.bones}

    facial_root = bone_by_tag.get(FACIAL_ROOT_TAG, None)
    if facial_root is None:
        return None

    return build_bone_hierarchy(skeleton, facial_root)


def merge_skeleton_facial_roots(ydd_xml: DrawableDictionary, skeleton: Skeleton) -> tuple[Skeleton, dict[int, tuple[Drawable, BoneHierarchy]]]:

    facial_roots = {}
    for drawable_xml in ydd_xml:
        if drawable_xml.skeleton.bones:
            facial_root = find_skeleton_facial_bones_hierarchy(drawable_xml.skeleton)
            variation_index = int(facial_root.children[0].bone.name[-3:])
            assert variation_index not in facial_roots
            facial_roots[variation_index] = drawable_xml, facial_root

    if facial_roots:
        facial_roots = dict(sorted(facial_roots.items()))

        skeleton_hierarchy = build_bone_hierarchy(skeleton, skeleton.bones[0])

        def _insert_facial_roots(b: BoneHierarchy):
            for i, c in enumerate(list(b.children)):
                if c.bone.tag == FACIAL_ROOT_TAG:
                    del b.children[i]  # remove existing facial root
                    # add the facial roots for each variation
                    for variation_index, (_, facial_root) in facial_roots.items():
                        facial_root.bone.name += f"_{variation_index:03}"
                        b.children.append(facial_root)
                    return True
                else:
                    found = _insert_facial_roots(c)
                    if found:
                        return True

            return False
        _insert_facial_roots(skeleton_hierarchy)

        new_skeleton = Skeleton()

        def _build_bones_flat_list(b: BoneHierarchy):
            b.bone.index = len(new_skeleton.bones)
            b.bone.sibling_index = None  # not used during import
            new_skeleton.bones.append(b.bone)
            for c in b.children:
                c.bone.parent_index = b.bone.index
                _build_bones_flat_list(c)

        _build_bones_flat_list(skeleton_hierarchy)

        bones_by_tag = defaultdict(dict)
        bones_by_tag2 = defaultdict(dict)
        for bone in new_skeleton.bones:
            key = None
            if bone.name.startswith("FB_"):
                key = int(bone.name[-3:])
            bones_by_tag[bone.tag][key] = bone
            bones_by_tag2[bone.tag][key] = bone.name

        # TODO: fixup vertex bindings
        # for variation_index, (drawable_xml, _) in facial_roots.items():
        #     for geom in drawable_xml.all_geoms:
        #         if not geom.bone_ids:
        #             continue
        #
        #         # print(f">{geom.bone_ids}")
        #         for i in range(len(geom.bone_ids)):
        #             bone_tag = drawable_xml.skeleton.bones[geom.bone_ids[i]].tag
        #             bone = bones_by_tag[bone_tag].get(variation_index, None)
        #             bone = bone or bones_by_tag[bone_tag][None]
        #
        #             # print(f"  {geom.bone_ids[i]}   ->   {bone.index}")
        #             geom.bone_ids[i] = bone.index
        #         # print(f"<{geom.bone_ids}")

        return new_skeleton, facial_roots
    else:
        return skeleton, {}
