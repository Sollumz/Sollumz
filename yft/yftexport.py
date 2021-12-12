import traceback
from ..yft.yftimport import get_fragment_drawable
from ..sollumz_properties import BOUND_TYPES, SollumType
from ..ydr.ydrexport import drawable_from_object
from ..ybn.ybnexport import composite_from_object, composite_from_objects
from ..resources.fragment import BoneTransformItem, BoneTransformsListProperty, ChildrenItem, Fragment, GroupItem, LODProperty, TransformItem
from ..tools.meshhelper import *
from ..tools.drawablehelper import get_drawable_geometries, join_drawable_geometries
from ..tools.blenderhelper import copy_object, delete_object, split_object


def get_group_objects(fragment, index=0):
    groups = []
    for child in fragment.children:
        if child.sollum_type == SollumType.FRAGGROUP:
            # print(f"{child.name} {index}")
            groups.append(child)
            index += 1
    for g in groups:
        groups += get_group_objects(g, index)
    return groups


def get_group_parent_index(gobjs, group):
    parent = group.parent
    if parent.sollum_type == SollumType.FRAGGROUP:
        return gobjs.index(parent)
    else:
        return 255


def get_bound_objects_from_groups(gobjs):
    bobjs = []
    for g in gobjs:
        for child in g.children:
            if child.sollum_type in BOUND_TYPES:
                if child not in bobjs:
                    bobjs.append(child)
    return bobjs


def get_child_objects_from_groups(gobjs):
    cobjs = []
    for g in gobjs:
        for child in g.children:
            if child.sollum_type == SollumType.FRAGCHILD:
                if child not in cobjs:
                    cobjs.append(child)
    return cobjs


def fragment_from_object(exportop, obj, exportpath, export_settings=None):
    fobj = copy_object(obj, True)

    fragment = Fragment()
    fragment.name = fobj.name.split(".")[0]
    fragment.bounding_sphere_center = get_bound_center(
        fobj, world=export_settings.use_transforms)
    fragment.bounding_sphere_radius = get_obj_radius(
        fobj, world=export_settings.use_transforms)

    fragment.unknown_b0 = fobj.fragment_properties.unk_b0
    fragment.unknown_b8 = fobj.fragment_properties.unk_b8
    fragment.unknown_bc = fobj.fragment_properties.unk_bc
    fragment.unknown_c0 = fobj.fragment_properties.unk_c0
    fragment.unknown_c4 = fobj.fragment_properties.unk_c4
    fragment.unknown_cc = fobj.fragment_properties.unk_cc
    fragment.unknown_d0 = fobj.fragment_properties.unk_d0
    fragment.unknown_d4 = fobj.fragment_properties.unk_d4

    dobj = None

    for child in fobj.children:
        if child.sollum_type == SollumType.DRAWABLE:
            dobj = child

    if dobj == None:
        raise Exception("NO DRAWABLE TO EXPORT.")

    # join geos cause split by bone
    join_drawable_geometries(dobj)
    fragment.drawable = drawable_from_object(
        exportop, dobj, exportpath, None, export_settings, True)

    geo = get_drawable_geometries(dobj)[0]
    geos = split_object(geo, geo.parent)
    # for idx, bone in enumerate(fragment.drawable.skeleton.bones):
    for idx, bone in enumerate(dobj.data.bones):
        if idx < len(geos):
            if bone.name == geos[idx].name:
                fragment.bones_transforms.append(
                    BoneTransformItem("Item", geo.matrix_basis))
        else:
            fragment.bones_transforms.append(
                BoneTransformItem("Item", Matrix()))

    lods = []
    for child in fobj.children:
        if child.sollum_type == SollumType.FRAGLOD:
            lods.append(child)

    lod1 = None
    lod2 = None
    lod3 = None

    for idx, lod in enumerate(lods):
        gobjs = get_group_objects(lod)
        bobjs = get_bound_objects_from_groups(gobjs)
        cobjs = get_child_objects_from_groups(gobjs)

        flod = LODProperty()
        flod.tag_name = f"LOD{idx+1}"
        flod.unknown_14 = lod.lod_properties.unk_14
        flod.unknown_18 = lod.lod_properties.unk_18
        flod.unknown_1c = lod.lod_properties.unk_1c
        pos_offset = prop_array_to_vector(lod.lod_properties.unk_30)
        flod.unknown_30 = pos_offset
        flod.unknown_40 = prop_array_to_vector(lod.lod_properties.unk_40)
        flod.unknown_50 = prop_array_to_vector(lod.lod_properties.unk_50)
        flod.unknown_60 = prop_array_to_vector(lod.lod_properties.unk_60)
        flod.unknown_70 = prop_array_to_vector(lod.lod_properties.unk_70)
        flod.unknown_80 = prop_array_to_vector(lod.lod_properties.unk_80)
        flod.unknown_90 = prop_array_to_vector(lod.lod_properties.unk_90)
        flod.unknown_a0 = prop_array_to_vector(lod.lod_properties.unk_a0)
        flod.unknown_b0 = prop_array_to_vector(lod.lod_properties.unk_b0)

        flod.archetype.name = lod.lod_properties.name
        flod.archetype.mass = lod.lod_properties.mass
        flod.archetype.mass_inv = lod.lod_properties.mass_inv
        flod.archetype.unknown_48 = lod.lod_properties.unknown_48
        flod.archetype.unknown_4c = lod.lod_properties.unknown_4c
        flod.archetype.unknown_50 = lod.lod_properties.unknown_50
        flod.archetype.unknown_54 = lod.lod_properties.unknown_54
        flod.archetype.inertia_tensor = prop_array_to_vector(
            lod.lod_properties.inertia_tensor)
        flod.archetype.inertia_tensor_inv = prop_array_to_vector(
            lod.lod_properties.inertia_tensor_inv)
        flod.archetype.bounds = composite_from_objects(
            bobjs, export_settings)

        gidx = 0
        for gobj in gobjs:
            group = GroupItem()
            group.index = gidx
            group.parent_index = get_group_parent_index(gobjs, gobj)
            group.name = gobj.name if "group" not in gobj.name else gobj.name.replace(
                "_group", "").split(".")[0]
            flod.groups.append(group)
            gidx += 1

        bidx = 0
        for cobj in cobjs:
            child = ChildrenItem()
            gobj = gobjs[bidx]
            child.group_index = gobjs.index(gobj)
            child.bone_tag = cobj.child_properties.bone_tag
            child.mass_1 = cobj.child_properties.mass_1
            child.mass_2 = cobj.child_properties.mass_2
            child.unk_vec = prop_array_to_vector(
                cobj.child_properties.unk_vec)
            child.inertia_tensor = prop_array_to_vector(
                cobj.child_properties.inertia_tensor, 4)

            dobj = get_fragment_drawable(cobj)

            if dobj:
                child.drawable = drawable_from_object(
                    exportop, dobj, exportpath, None, export_settings, True, False)
            else:
                child.drawable.matrix = Matrix()
                child.drawable.shader_group = None
                child.drawable.skeleton = None
                child.drawable.joints = None

            bidx += 1
            transform = cobj.matrix_basis.transposed()
            a = transform[3][0] - pos_offset.x
            b = transform[3][1] - pos_offset.y
            c = transform[3][2] - pos_offset.z
            transform[3][0] = a
            transform[3][1] = b
            transform[3][2] = c
            flod.transforms.append(TransformItem("Item", transform))
            flod.children.append(child)

        if lod.lod_properties.type == 1:
            lod1 = flod
        elif lod.lod_properties.type == 2:
            lod2 = flod
        elif lod.lod_properties.type == 3:
            lod3 = flod

    fragment.physics.lod1 = lod1
    fragment.physics.lod2 = lod2
    fragment.physics.lod3 = lod3

    # delete duplicated object
    #delete_object(fobj, True)

    return fragment


def export_yft(exportop, obj, filepath, export_settings):
    fragment_from_object(exportop, obj, filepath,
                         export_settings).write_xml(filepath)
