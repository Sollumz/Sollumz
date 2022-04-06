import bpy

from ..sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, BOUND_POLYGON_TYPES
from ..ybn.collision_materials import create_collision_material_from_index
from ..tools.meshhelper import create_box, create_sphere, create_capsule, create_cylinder
from mathutils import Vector, Matrix


def create_bound_shape(type):
    pobj = create_mesh(type)

    # Constrain scale for bound polys
    if pobj.sollum_type in BOUND_POLYGON_TYPES and type != SollumType.BOUND_POLY_BOX and type != SollumType.BOUND_POLY_TRIANGLE:
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

    if type == SollumType.BOUND_POLY_BOX:
        create_box(pobj.data)
    elif type == SollumType.BOUND_BOX:
        pobj.bound_dimensions = Vector((1, 1, 1))
    elif type == SollumType.BOUND_SPHERE or type == SollumType.BOUND_POLY_SPHERE:
        pobj.bound_radius = 1
    elif type == SollumType.BOUND_POLY_CAPSULE:
        pobj.bound_radius = 1
        pobj.bound_length = 1
    elif type == SollumType.BOUND_CAPSULE:
        pobj.bound_radius = 1
        pobj.margin = 0.5
    elif type == SollumType.BOUND_CYLINDER or type == SollumType.BOUND_POLY_CYLINDER:
        pobj.bound_length = 2
        pobj.bound_radius = 1
    elif type == SollumType.BOUND_DISC:
        pobj.margin = 0.04
        pobj.bound_radius = 1

    return pobj


def create_bound(sollum_type=SollumType.BOUND_COMPOSITE, aobj=None, do_link=True):

    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    if do_link:
        bpy.context.collection.objects.link(empty)
        bpy.context.view_layer.objects.active = bpy.data.objects[empty.name]

    if aobj:
        if aobj.sollum_type == SollumType.BOUND_COMPOSITE:
            empty.parent = aobj

    return empty


def create_mesh(sollum_type):
    name = SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = sollum_type
    bpy.context.collection.objects.link(obj)

    return obj


def convert_selected_to_bound(selected, use_name, multiple, bvhs, replace_original, do_center=True):

    center = Vector()
    cobjs = []

    if not multiple:
        cobj = create_bound()
        cobjs.append(cobj)
        gobj = create_bound(SollumType.BOUND_GEOMETRYBVH) if bvhs else create_bound(
            SollumType.BOUND_GEOMETRY)
        gobj.parent = cobj
        if do_center:
            for obj in selected:
                center += obj.location

            center /= len(selected)
            gobj.location = center

    for obj in selected:
        if multiple:
            cobj = create_bound()
            cobjs.append(cobj)
            gobj = create_bound(SollumType.BOUND_GEOMETRYBVH) if bvhs else create_bound(
                SollumType.BOUND_GEOMETRY)
            gobj.parent = cobj
            if do_center:
                gobj.location = obj.location
                obj.location = Vector()
        elif do_center:
            obj.location -= center

        if obj.type == 'MESH':
            name = obj.name

            poly_mesh = obj if replace_original else create_mesh(
                SollumType.BOUND_POLY_TRIANGLE)

            poly_mesh.parent = gobj

            if replace_original:
                poly_mesh.name = SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_TRIANGLE]
                # set properties
                poly_mesh.sollum_type = SollumType.BOUND_POLY_TRIANGLE
            else:
                poly_mesh.data = obj.data.copy()
                poly_mesh.matrix_world = obj.matrix_world

            if use_name:
                cobj.name = name

    return cobjs
