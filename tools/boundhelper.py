import bpy
from Sollumz.sollumz_properties import BoundType, PolygonType, SOLLUMZ_UI_NAMES
from Sollumz.ybn.collision_materials import create_collision_material_from_index
from Sollumz.meshhelper import create_box, create_sphere, create_capsule, create_cylinder


def create_poly(aobj, type):
    pobj = create_bound(type, True)

    if type == PolygonType.BOX:
        create_box(pobj.data)
    elif type == PolygonType.SPHERE:
        create_sphere(pobj.data)
    elif type == PolygonType.CAPSULE:
        create_capsule(pobj)
    elif type == PolygonType.CYLINDER:
        create_cylinder(pobj.data)

    pobj.parent = aobj
    return pobj


def create_bound(sollum_type=BoundType.COMPOSITE, with_mesh=False):

    if with_mesh:
        return create_mesh(sollum_type)

    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    bpy.context.collection.objects.link(empty)
    bpy.context.view_layer.objects.active = bpy.data.objects[empty.name]

    return empty


def create_mesh(sollum_type):
    name = SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = sollum_type
    obj.data.materials.append(create_collision_material_from_index(0))
    bpy.context.collection.objects.link(obj)

    return obj


def convert_selected_to_bound(objs, use_name=False, multiple=False):
    selected = objs

    parent = None
    if not multiple:
        parent = create_bound()

    for obj in selected:
        # set parents
        dobj = parent or create_bound(BoundType.COMPOSITE)
        dmobj = create_bound(BoundType.GEOMETRYBVH)
        dmobj.parent = dobj
        obj.parent = dmobj

        name = obj.name
        obj.name = name + "_mesh"

        if use_name:
            dobj.name = name

        # set properties
        obj.sollum_type = PolygonType.TRIANGLE

        # add object to collection
        new_obj = obj.copy()

        # Remove materials
        if new_obj.type == 'MESH':
            new_obj.data.materials.clear()

        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.collection.objects.link(new_obj)
