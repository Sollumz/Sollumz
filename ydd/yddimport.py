import bpy
import os
from ..resources.drawable import *
from ..resources.fragment import YFT
from ..ydr.ydrimport import drawable_to_obj
from ..tools.drawablehelper import join_drawable_geometries
from ..sollumz_properties import SollumType
from ..sollumz_helper import find_fragment_file


def drawable_dict_to_obj(drawable_dict, filepath):

    name = os.path.basename(filepath)[:-8]
    vmodels = []
    # bones are shared in single ydd however they still have to be placed under a paticular drawable

    armature_with_skel_obj = None
    mod_objs = []
    drawable_with_skel = None
    for drawable in drawable_dict.values():
        if len(drawable.skeleton.bones) > 0:
            drawable_with_skel = drawable
            break

    for drawable in drawable_dict.values():
        drawable_obj = drawable_to_obj(
            drawable, filepath, drawable.name, bones_override=drawable_with_skel.skeleton.bones if drawable_with_skel else None)
        if (armature_with_skel_obj is None and drawable_with_skel is not None and len(drawable.skeleton.bones) > 0):
            armature_with_skel_obj = drawable_obj

        for model in drawable_obj.children:
            if model.sollum_type != SollumType.DRAWABLE_MODEL:
                continue
            for geo in model.children:
                if geo.sollum_type != SollumType.DRAWABLE_GEOMETRY:
                    continue
                mod_objs.append(geo)

        vmodels.append(drawable_obj)

    dict_obj = bpy.data.objects.new(name, None)
    dict_obj.sollum_type = SollumType.DRAWABLE_DICTIONARY
    bpy.context.collection.objects.link(dict_obj)

    for vmodel in vmodels:
        vmodel.parent = dict_obj

    if armature_with_skel_obj is not None:
        for obj in mod_objs:
            mod = obj.modifiers.get("Armature")
            if mod is None:
                continue
            mod.object = armature_with_skel_obj

    return dict_obj


def import_ydd(export_op, filepath, import_settings):
    ydd_xml = YDD.from_xml_file(filepath)

    if import_settings.import_ext_skeleton:
        skel_filepath = find_fragment_file(filepath)
        if skel_filepath:
            yft = YFT.from_xml_file(skel_filepath)
            for drawable in ydd_xml.values():
                drawable.skeleton = yft.drawable.skeleton
        else:
            export_op.warning("No external skeleton file found.")

    drawable_dict = drawable_dict_to_obj(ydd_xml, filepath)
    if import_settings.join_geometries:
        for child in drawable_dict.children:
            if child.sollum_type == SollumType.DRAWABLE:
                for grandchild in child.children:
                    if grandchild.sollum_type == SollumType.DRAWABLE_MODEL:
                        join_drawable_geometries(grandchild)
