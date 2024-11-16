import bpy
from bpy.types import (
    Object,
)
import os
import numpy as np
from typing import Optional
from ..cwxml.drawable import YDD, DrawableDictionary, Skeleton, Bone
from ..cwxml.fragment import YFT, Fragment
from ..cwxml.cloth import YLD, ClothDictionary, CharacterCloth
from ..ydr.ydrimport import create_drawable_obj, create_drawable_skel, apply_rotation_limits
from ..ybn.ybnimport import create_bound_composite
from ..sollumz_properties import SollumType
from ..sollumz_preferences import get_import_settings
from ..tools.blenderhelper import create_empty_object, create_blender_object, add_child_of_bone_constraint
from ..tools.utils import get_filename

from .. import logger


def import_ydd(filepath: str):
    import_settings = get_import_settings()

    ydd_xml = YDD.from_xml_file(filepath)

    # Import the cloth .yld.xml if it exists
    yld_filepath = make_yld_filepath(filepath)
    yld_xml = YLD.from_xml_file(yld_filepath) if os.path.exists(yld_filepath) else None

    if import_settings.import_ext_skeleton:
        skel_yft = load_external_skeleton(filepath)

        if skel_yft is not None and skel_yft.drawable.skeleton is not None:
            return create_ydd_obj(ydd_xml, filepath, yld_xml, skel_yft)

    return create_ydd_obj(ydd_xml, filepath, yld_xml, None)


def load_external_skeleton(ydd_filepath: str) -> Optional[Fragment]:
    """Read first yft at ydd_filepath into a Fragment"""
    directory = os.path.dirname(ydd_filepath)

    yft_filepath = get_first_yft_path(directory)

    if yft_filepath is None:
        logger.warning(f"Could not find external skeleton yft in directory '{directory}'.")
        return None

    logger.info(f"Using '{yft_filepath}' as external skeleton...")

    return YFT.from_xml_file(yft_filepath)


def get_first_yft_path(directory: str) -> Optional[str]:
    for filepath in os.listdir(directory):
        if filepath.endswith(".yft.xml"):
            return os.path.join(directory, filepath)

    return None


def create_ydd_obj(ydd_xml: DrawableDictionary, filepath: str, yld_xml: Optional[ClothDictionary], external_skel: Optional[Fragment]):
    name = get_filename(filepath)
    if external_skel is not None:
        dict_obj = create_armature_parent(name, external_skel)
    else:
        dict_obj = create_empty_object(SollumType.DRAWABLE_DICTIONARY, name)

    ydd_skel = find_first_skel(ydd_xml)

    for drawable_xml in ydd_xml:
        if external_skel is not None:
            if not drawable_xml.skeleton.bones:
                external_bones = external_skel.drawable.skeleton.bones

            if not drawable_xml.skeleton.bones:
                external_armature = dict_obj
        else:
            if not drawable_xml.skeleton.bones and ydd_skel is not None:
                external_bones = ydd_skel.bones
            else:
                external_bones = None

            external_armature = None

        drawable_obj = create_drawable_obj(
            drawable_xml,
            filepath,
            external_armature=external_armature,
            external_bones=external_bones,
        )
        drawable_obj.parent = dict_obj

        if yld_xml is not None:
            cloth = next((c for c in yld_xml if c.name == drawable_xml.name), None)
            if cloth is not None:
                cloth_obj = create_character_cloth_mesh(cloth, drawable_xml.skeleton.bones or external_bones)
                bounds_obj = create_character_cloth_bounds(cloth, external_armature or drawable_obj, drawable_xml.skeleton.bones or external_bones)
                bounds_obj.parent = cloth_obj
                cloth_obj.parent = drawable_obj

    return dict_obj


def create_armature_parent(name: str, skel_yft: Fragment):
    armature = bpy.data.armatures.new(f"{name}.skel")
    dict_obj = create_blender_object(SollumType.DRAWABLE_DICTIONARY, name, armature)

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



def make_yld_filepath(ydd_filepath: str) -> str:
    """Get the .yld.xml filepath at the provided ydd filepath."""
    ydd_dir = os.path.dirname(ydd_filepath)
    ydd_name = get_filename(ydd_filepath)

    path = os.path.join(ydd_dir, f"{ydd_name}.yld.xml")
    return path


def create_character_cloth_mesh(cloth: CharacterCloth, bones: list[Bone]) -> Object:
    controller = cloth.controller
    vertices = controller.vertices
    indices = controller.indices

    vertices = np.array(vertices)
    indices = np.array(indices).reshape((-1, 3))


    mesh = bpy.data.meshes.new(f"{controller.name}.cloth")
    mesh.from_pydata(vertices, [], indices)
    obj = create_blender_object(SollumType.CHARACTER_CLOTH_MESH, f"{controller.name}.cloth", mesh)

    pin_radius = cloth.controller.bridge.pin_radius_high
    weights = cloth.controller.bridge.vertex_weights_high
    inflation_scale = cloth.controller.bridge.inflation_scale_high
    display_map = np.array(cloth.controller.bridge.display_map_high)
    pinned_vertices_count = cloth.controller.cloth_high.pinned_vertices_count

    has_pinned = pinned_vertices_count > 0
    has_pin_radius = len(pin_radius) > 0
    has_weights = len(weights) > 0
    has_inflation_scale = len(inflation_scale) > 0

    from ..ydr.cloth import ClothAttr, mesh_add_cloth_attribute

    if has_pinned:
        mesh_add_cloth_attribute(mesh, ClothAttr.PINNED)
    if has_pin_radius:
        mesh_add_cloth_attribute(mesh, ClothAttr.PIN_RADIUS)
    if has_weights:
        mesh_add_cloth_attribute(mesh, ClothAttr.VERTEX_WEIGHT)
    if has_inflation_scale:
        mesh_add_cloth_attribute(mesh, ClothAttr.INFLATION_SCALE)

    for mesh_vert_index, cloth_vert_index in enumerate(display_map):
        mesh_vert_index = cloth_vert_index # NOTE: in character cloths both are the same?

        if has_pinned:
            pinned = cloth_vert_index < pinned_vertices_count
            mesh.attributes[ClothAttr.PINNED].data[mesh_vert_index].value = 1 if pinned else 0

        if has_pin_radius:
            mesh.attributes[ClothAttr.PIN_RADIUS].data[mesh_vert_index].value = pin_radius[cloth_vert_index]

        if has_weights:
            mesh.attributes[ClothAttr.VERTEX_WEIGHT].data[mesh_vert_index].value = weights[cloth_vert_index]

        if has_inflation_scale:
            mesh.attributes[ClothAttr.INFLATION_SCALE].data[mesh_vert_index].value = inflation_scale[cloth_vert_index]


    def _create_group(bone_index: int):
        if bones and bone_index < len(bones):
            bone_name = bones[bone_index].name
        else:
            bone_name = f"UNKNOWN_BONE.{bone_index}"

        return obj.vertex_groups.new(name=bone_name)

    vertex_groups_by_bone_idx = {}
    for vert_idx, binding in enumerate(controller.bindings):
        for weight, idx in zip(binding.weights, binding.indices):
            if weight == 0.0:
                continue

            bone_idx = controller.bone_indices[idx]
            if bone_idx not in vertex_groups_by_bone_idx:
                vertex_groups_by_bone_idx[bone_idx] = _create_group(bone_idx)

            vgroup = vertex_groups_by_bone_idx[bone_idx]
            vgroup.add((vert_idx,), weight, "ADD")

    return obj

def create_character_cloth_bounds(cloth: CharacterCloth, armature_obj: Object, bones: list[Bone]) -> Object:
    bounds_obj = create_bound_composite(cloth.bounds)
    bounds_obj.name = f"{cloth.controller.name}.cloth.bounds"

    for bound_obj, bone_id in zip(bounds_obj.children, cloth.bounds_bone_ids):
        print(f"{bones=}")
        bone_name = next((b.name for b in bones if b.tag == bone_id), None)
        assert bone_name is not None, "Cloth bound attached to non-existing bone."

        add_child_of_bone_constraint(bound_obj, armature_obj, bone_name)

    return bounds_obj
