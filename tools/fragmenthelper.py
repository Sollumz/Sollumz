import bpy
from mathutils import Vector

from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from .blenderhelper import create_empty_object, material_from_image
from itertools import groupby


def get_rgb(value):
    if value == "##":
        return [0, 0, 0, 1]
    elif value == "--":
        return [1, 1, 1, 1]
    else:
        value = int(value, 16)
        return [value / 255, value / 255, value / 255, 1]


def shattermap_to_image(shattermap, name):
    width = int(len(shattermap[0]) / 2)
    height = int(len(shattermap))

    img = bpy.data.images.new(name, width, height)

    pixels = []
    i = 0
    for row in reversed(shattermap):
        frow = [row[x:x + 2] for x in range(0, len(row), 2)]
        for value in frow:
            pixels.append(get_rgb(value))
            i += 1

    pixels = [chan for px in pixels for chan in px]
    img.pixels = pixels
    return img


def shattermap_to_material(shattermap, name):
    img = shattermap_to_image(shattermap, name)
    return material_from_image(img, name, "ShatterMap")


def longest(lst, string):
    lst = [[*g]
           for k, g in groupby(enumerate(lst), key=lambda x: x[1]) if k == string]
    if len(lst) > 0:
        group = max(lst, key=len)
        return group[0][0], 1 + group[-1][0]
    else:
        return [0, 0]


def remove_ff(row):
    target = longest(row, "FF")
    start = target[0] + 1
    end = target[1]
    length = end - start
    if length > 1:
        row[start:end] = ["--"] * length
    return row


def convert_selected_to_fragment(objs, use_names=False, multiple=False, do_center=True):
    parent = None

    center = Vector()
    dobjs = []

    if not multiple:
        dobj = create_empty_object(SollumType.FRAGMENT)
        dobjs.append(dobj)
        if do_center:
            for obj in objs:
                center += obj.location

            center /= len(objs)
            dobj.location = center
        dmobj = create_empty_object(SollumType.FRAGLOD)
        gobj = create_empty_object(SollumType.FRAGGROUP)
        cobj = create_empty_object(SollumType.FRAGCHILD)
        dmobj.parent = dobj
        gobj.parent = dmobj
        cobj.parent = gobj

    for obj in objs:

        if obj.type != "MESH":
            raise Exception(
                f"{obj.name} cannot be converted because it has no mesh data.")

        if multiple:
            dobj = parent or create_empty_object()
            dobjs.append(dobj)
            if do_center:
                dobj.location = obj.location
                obj.location = Vector()
            dmobj = create_empty_object(SollumType.FRAGLOD)
            dmobj.parent = dobj
            gobj.parent = dmobj
            cobj.parent = gobj
        elif do_center:
            obj.location -= center

        obj.parent = gobj

        name = obj.name

        if use_names:
            obj.name = name + "_old"
            dobj.name = name

        obj.sollum_type = SollumType.BOUND_BOX

        new_obj = obj.copy()
        # add color layer
        if len(new_obj.data.vertex_colors) == 0:
            new_obj.data.vertex_colors.new()
        # add object to collection
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.collection.objects.link(new_obj)
        new_obj.name = name + "_geom"

    return dobjs

def image_to_shattermap(img):
    width = img.size[0]
    values = []
    row = []
    for idx in range(int(len(img.pixels) / 4) + 1):
        if idx % width == 0:
            row = remove_ff(row)
            values.append(row)
            row = []
        try:
            value = int(img.pixels[idx * 4] * 255)
            if value == 0:
                value = "##"
            elif value <= 15:
                value = "0{0:X}".format(value)
            else:
                value = "{0:X}".format(value)
            row.append(value)
        except:
            continue

    return reversed(values)
