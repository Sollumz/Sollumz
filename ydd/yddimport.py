import bpy
import os
import traceback
from mathutils import Vector, Quaternion, Matrix
from Sollumz.resources.drawable import *
from Sollumz.ydr.ydrimport import drawable_to_obj


def drawable_dict_to_obj(drawable_dict, filepath):

    name = os.path.basename(filepath)[:-8]
    vmodels = []
    # bones are shared in single ydd however they still have to be placed under a paticular drawable

    armature_with_skel_obj = None
    mod_objs = []
    drawable_with_skel = None
    for drawable in drawable_dict.value:
        if len(drawable.skeleton.bones) > 0:
            drawable_with_skel = drawable
            break

    for drawable in drawable_dict.value:
        drawable_obj = drawable_to_obj(
            drawable, filepath, drawable.name, bones_override=drawable_with_skel.skeleton.bones)
        if (armature_with_skel_obj is None and drawable_with_skel is not None and len(drawable.skeleton.bones) > 0):
            armature_with_skel_obj = drawable_obj

        for model in drawable_obj.children:
            if model.sollum_type != "sollumz_drawable_model":
                continue

            for geo in model.children:
                if geo.sollum_type != "sollumz_geometry":
                    continue

                mod_objs.append(geo)

        vmodels.append(drawable_obj)

    dict_obj = bpy.data.objects.new(name, None)
    dict_obj.sollum_type = "sollumz_drawable_dictionary"

    for vmodel in vmodels:
        vmodel.parent = dict_obj

    bpy.context.collection.objects.link(dict_obj)

    if armature_with_skel_obj is not None:
        for obj in mod_objs:
            mod = obj.modifiers.get("Armature")
            if mod is None:
                continue

            mod.object = armature_with_skel_obj

    return dict_obj


def import_ydd(filepath):
    try:
        ydd_xml = YDD.from_xml_file(filepath)
        drawable_dict_to_obj(ydd_xml, filepath)
        return f"Succesfully imported : {filepath}"
    except:
        return f"Error importing : {filepath} \n {traceback.format_exc()}"
