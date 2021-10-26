import bpy
from Sollumz.ydr.ydrimport import drawable_to_obj
from Sollumz.ybn.ybnimport import composite_to_obj
from Sollumz.sollumz_properties import SOLLUMZ_UI_NAMES, DrawableType, BoundType
from time import time


def fragment_to_obj(fragment, filepath):

    start = time()

    if(fragment.drawable != None):
        parent = drawable_to_obj(fragment.drawable, filepath, fragment.name)
    parent.sollum_type = DrawableType.FRAGMENT

    end = time()
    print(str(end - start) + " seconds to import to import main drawable")
    start = time()

    if(fragment.physics.lod1.archetype.bounds != None):
        obj = composite_to_obj(fragment.physics.lod1.archetype.bounds,
                               SOLLUMZ_UI_NAMES[BoundType.COMPOSITE], True)
    obj.parent = parent

    end = time()
    print(str(end - start) + " seconds to import bounds")
    start = time()

    lod1 = fragment.physics.lod1

    children_obj = bpy.data.objects.new("Children", None)
    children_obj.parent = parent
    bpy.context.collection.objects.link(children_obj)

    for item in lod1.children:
        # if(item.drawable != None):
        # if(len(item.drawable.drawable_models_high) > 0):
        child = drawable_to_obj(
            item.drawable, "", item.drawable.name, None, fragment.drawable.shader_group)
        child.parent = children_obj

    end = time()
    print(str(end - start) + " seconds to import children")

    return
