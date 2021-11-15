import bpy

from ..sollumz_helper import is_sollum_type
from ..sollumz_properties import BoundType, PolygonType, SOLLUMZ_UI_NAMES
from ..ybn.collision_materials import create_collision_material_from_index
from ..tools.meshhelper import create_box, create_sphere, create_capsule, create_cylinder
from mathutils import Vector, Matrix


def create_bound_shape(type, aobj):
    pobj = create_mesh(type)

    # Constrain scale for bound polys
    if is_sollum_type(pobj, PolygonType) and type != PolygonType.BOX and type != PolygonType.TRIANGLE:
        constraint = pobj.constraints.new(type='LIMIT_SCALE')
        constraint.use_transform_limit = True
        # Why blender? So ugly
        constraint.use_min_x = True
        constraint.use_min_y = True
        constraint.use_min_z = True
        constraint.use_max_x = True
        constraint.use_max_y = True
        constraint.use_max_z = True
        constraint.min_x = 1
        constraint.min_y = 1
        constraint.min_z = 1
        constraint.max_x = 1
        constraint.max_y = 1
        constraint.max_z = 1

    if type == PolygonType.BOX:
        create_box(pobj.data)
    elif type == BoundType.BOX:
        pobj.bound_dimensions = Vector((1, 1, 1))
    elif type == BoundType.SPHERE or type == PolygonType.SPHERE:
        pobj.bound_radius = 1
    elif type == PolygonType.CAPSULE:
        pobj.bound_radius = 1
        pobj.bound_length = 1
    elif type == BoundType.CAPSULE:
        pobj.bound_radius = 1
        pobj.margin = 0.5
    elif type == BoundType.CYLINDER or type == PolygonType.CYLINDER:
        pobj.bound_length = 2
        pobj.bound_radius = 1
    elif type == BoundType.DISC:
        pobj.margin = 0.04
        pobj.bound_radius = 1

    if aobj:
        if aobj.sollum_type == BoundType.GEOMETRY or aobj.sollum_type == BoundType.GEOMETRYBVH or aobj.sollum_type == BoundType.COMPOSITE:
            pobj.parent = aobj

    return pobj


def create_bound(sollum_type=BoundType.COMPOSITE, aobj=None):

    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    bpy.context.collection.objects.link(empty)
    bpy.context.view_layer.objects.active = bpy.data.objects[empty.name]

    if aobj:
        if aobj.sollum_type == BoundType.COMPOSITE:
            empty.parent = aobj

    return empty


def create_mesh(sollum_type):
    name = SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = sollum_type
    obj.data.materials.append(create_collision_material_from_index(0))
    bpy.context.collection.objects.link(obj)

    return obj


def convert_selected_to_bound(objs, use_name, multiple, bvhs):
    selected = objs

    parent = None
    if not multiple:
        parent = create_bound()

    dobj = parent or create_bound()
    dmobj = create_bound(BoundType.GEOMETRYBVH) if bvhs else create_bound(
        BoundType.GEOMETRY)
    dmobj.parent = dobj

    for obj in selected:
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
            # add default collision mat
            new_obj.data.materials.append(
                create_collision_material_from_index(0))

        bpy.data.objects.remove(obj, do_unlink=True)
        bpy.context.collection.objects.link(new_obj)
