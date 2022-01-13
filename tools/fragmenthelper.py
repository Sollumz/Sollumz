import bpy
from .blenderhelper import material_from_image


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

    img = bpy.data.images.new(name, width=width, height=height)

    pixels = []
    i = 0
    for row in shattermap:
        frow = [row[x:x+2] for x in range(0, len(row), 2)]
        for value in frow:
            pixels.append(get_rgb(value))
            i += 1

    pixels = [chan for px in pixels for chan in px]
    img.pixels = pixels
    return img


def shattermap_to_material(shattermap, name):
    img = shattermap_to_image(shattermap, name)
    return material_from_image(img, name)
