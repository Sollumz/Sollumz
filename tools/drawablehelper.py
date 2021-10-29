import traceback
import bpy
from Sollumz.ydr.shader_materials import create_shader
from Sollumz.sollumz_properties import DrawableType, SOLLUMZ_UI_NAMES, MaterialType


def create_drawable(sollum_type=DrawableType.DRAWABLE):
    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    bpy.context.collection.objects.link(empty)
    bpy.context.view_layer.objects.active = bpy.data.objects[empty.name]

    return empty


def convert_selected_to_drawable(objs, use_names=False, multiple=False):
    parent = None
    if not multiple:
        parent = create_drawable(DrawableType.DRAWABLE)

    for obj in objs:
        # create material
        if(len(obj.data.materials) > 0):
            mat = obj.data.materials[0]
            if(mat.sollum_type != MaterialType.SHADER):
                # remove old materials
                for i in range(len(obj.material_slots)):
                    bpy.ops.object.material_slot_remove({'object': obj})
                mat = create_shader("default")
                obj.data.materials.append(mat)

        # set parents
        dobj = parent or create_drawable()
        dmobj = create_drawable(DrawableType.DRAWABLE_MODEL)
        dmobj.parent = dobj
        obj.parent = dmobj

        name = obj.name
        obj.name = name + "_geom"

        if use_names:
            dobj.name = name

        # set properties
        obj.sollum_type = DrawableType.GEOMETRY

        # add object to collection
        new_obj = obj.copy()
        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.collection.objects.link(new_obj)
