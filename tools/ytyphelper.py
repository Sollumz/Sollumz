import bpy
import os
from ..sollumz_helper import has_embedded_textures, has_collision
from ..cwxml.ytyp import BaseArchetype, CMapTypes
from ..tools.meshhelper import get_extents, get_bound_center, get_sphere_radius
from ..sollumz_properties import SollumType


def base_archetype_from_object(obj):
    arch = BaseArchetype()
    arch.lod_dist = 60
    arch.flags = 32
    arch.special_attribute = 0
    arch.hd_texture_dist = 60
    arch.name = obj.name
    arch.texture_dictionary = obj.name if has_embedded_textures(obj) else ""
    arch.clip_dictionary = ""
    drawable_dictionary = ""
    if obj.parent:
        if obj.parent.sollum_type == SollumType.DRAWABLE_DICTIONARY:
            drawable_dictionary = obj.parent.name
    arch.drawable_dictionary = drawable_dictionary
    arch.physics_dictionary = obj.name if has_collision(obj) else ""
    bbmin, bbmax = get_extents(obj)
    arch.bb_min = bbmin
    arch.bb_max = bbmax
    arch.bs_center = get_bound_center(obj)
    arch.bs_radius = get_sphere_radius(bbmax, arch.bs_center)
    arch.asset_name = obj.name
    if obj.sollum_type == SollumType.FRAGMENT:
        arch.asset_type = "ASSET_TYPE_FRAGMENT"
    elif obj.sollum_type == SollumType.DRAWABLE:
        arch.asset_type = "ASSET_TYPE_DRAWABLE"
    elif obj.sollum_type == SollumType.DRAWABLE_DICTIONARY:
        arch.asset_type = "ASSET_TYPE_DRAWABLEDICTIONARY"
    return arch


def ytyp_from_objects(objs):
    ytyp = CMapTypes()
    ytyp.name = os.path.basename(
        bpy.data.filepath).replace(".blend", "") if bpy.data.filepath is not "" else "untitled"
    for obj in objs:
        ytyp.archetypes.append(base_archetype_from_object(obj))
    return ytyp
