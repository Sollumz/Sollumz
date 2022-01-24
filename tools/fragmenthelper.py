import bpy
from .blenderhelper import material_from_image
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
    width = len(shattermap[0]) / 2
    height = len(shattermap)

    img = bpy.data.images.new(name, width, height)

    pixels = []
    i = 0
    for row in reversed(shattermap):
        frow = [row[x:x+2] for x in range(0, len(row), 2)]
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
        return group[0][0], 1+group[-1][0]
    else:
        return [0, 0]


def remove_ff(row):
    target = longest(row, "FF")
    start = target[0]
    end = target[1]
    length = end - start
    if length > 1:
        row[start:end] = ["--"] * length
    return row


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
            # elif value == 255:
                # value = "--"
            elif value <= 15:
                value = "0{0:X}".format(value)
            else:
                value = "{0:X}".format(value)
            row.append(value)
        except:
            continue

    return reversed(values)
