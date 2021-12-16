import os
import traceback
from ..yft.yftimport import get_fragment_drawable
from ..sollumz_properties import BOUND_TYPES, SollumType
from ..ydr.ydrexport import drawable_from_object, get_used_materials
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
        cgroups = get_group_objects(g, index)
        for cg in cgroups:
            if cg not in groups:
                groups.append(cg)

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
                bobjs.append(child)
    return bobjs


def get_child_objects_from_groups(gobjs):
    cobjs = []
    for g in gobjs:
        for child in g.children:
            if child.sollum_type == SollumType.FRAGCHILD:
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
    fragment.gravity_factor = fobj.fragment_properties.gravity_factor
    fragment.buoyancy_factor = fobj.fragment_properties.buoyancy_factor

    dobj = None

    for child in fobj.children:
        if child.sollum_type == SollumType.DRAWABLE:
            dobj = child

    if dobj == None:
        raise Exception("NO DRAWABLE TO EXPORT.")

    materials = None
    materials = get_used_materials(fobj)

    # join geos cause split by bone
    for child in dobj.children:
        if child.sollum_type == SollumType.DRAWABLE_MODEL:
            join_drawable_geometries(child)
    fragment.drawable = drawable_from_object(
        exportop, dobj, exportpath, None, materials, export_settings, True)

    #geo = get_drawable_geometries(dobj)[0]
    #geos = split_object(geo, geo.parent)
    # for idx, bone in enumerate(fragment.drawable.skeleton.bones):
    for idx, bone in enumerate(dobj.data.bones):
        fragment.bones_transforms.append(
            BoneTransformItem("Item", Matrix().transposed()))

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
        flod.unknown_14 = lod.lod_properties.unknown_14
        flod.unknown_18 = lod.lod_properties.unknown_18
        flod.unknown_1c = lod.lod_properties.unknown_1c
        pos_offset = prop_array_to_vector(lod.lod_properties.position_offset)
        flod.position_offset = pos_offset
        flod.unknown_40 = prop_array_to_vector(lod.lod_properties.unknown_40)
        flod.unknown_50 = prop_array_to_vector(lod.lod_properties.unknown_50)
        flod.damping_linear_c = prop_array_to_vector(
            lod.lod_properties.damping_linear_c)
        flod.damping_linear_v = prop_array_to_vector(
            lod.lod_properties.damping_linear_v)
        flod.damping_linear_v2 = prop_array_to_vector(
            lod.lod_properties.damping_linear_v2)
        flod.damping_angular_c = prop_array_to_vector(
            lod.lod_properties.damping_angular_c)
        flod.damping_angular_v = prop_array_to_vector(
            lod.lod_properties.damping_angular_v)
        flod.damping_angular_v2 = prop_array_to_vector(
            lod.lod_properties.damping_angular_v2)

        flod.archetype.name = lod.lod_properties.archetype_name
        flod.archetype.mass = lod.lod_properties.archetype_mass
        flod.archetype.mass_inv = 1 / lod.lod_properties.archetype_mass
        flod.archetype.unknown_48 = lod.lod_properties.archetype_unknown_48
        flod.archetype.unknown_4c = lod.lod_properties.archetype_unknown_4c
        flod.archetype.unknown_50 = lod.lod_properties.archetype_unknown_50
        flod.archetype.unknown_54 = lod.lod_properties.archetype_unknown_54
        arch_it = prop_array_to_vector(
            lod.lod_properties.archetype_inertia_tensor)
        flod.archetype.inertia_tensor = arch_it
        flod.archetype.inertia_tensor_inv = divide_vector_inv(arch_it)
        flod.archetype.bounds = composite_from_objects(bobjs, export_settings)

        gidx = 0
        for gobj in gobjs:
            group = GroupItem()
            group.name = gobj.name if "group" not in gobj.name else gobj.name.replace(
                "_group", "").split(".")[0]
            group.parent_index = get_group_parent_index(gobjs, gobj)
            group.glass_window_index = gobj.group_properties.glass_window_index
            group.glass_flags = gobj.group_properties.glass_flags
            group.strength = gobj.group_properties.strength
            group.force_transmission_scale_up = gobj.group_properties.force_transmission_scale_up
            group.force_transmission_scale_down = gobj.group_properties.force_transmission_scale_down
            group.joint_stiffness = gobj.group_properties.joint_stiffness
            group.min_soft_angle_1 = gobj.group_properties.min_soft_angle_1
            group.max_soft_angle_1 = gobj.group_properties.max_soft_angle_1
            group.max_soft_angle_2 = gobj.group_properties.max_soft_angle_2
            group.max_soft_angle_3 = gobj.group_properties.max_soft_angle_3
            group.rotation_speed = gobj.group_properties.rotation_speed
            group.rotation_strength = gobj.group_properties.rotation_strength
            group.restoring_max_torque = gobj.group_properties.restoring_max_torque
            group.latch_strength = gobj.group_properties.latch_strength
            group.mass = gobj.group_properties.mass
            group.min_damage_force = gobj.group_properties.min_damage_force
            group.damage_health = gobj.group_properties.damage_health
            group.unk_float_5c = gobj.group_properties.unk_float_5c
            group.unk_float_60 = gobj.group_properties.unk_float_60
            group.unk_float_64 = gobj.group_properties.unk_float_64
            group.unk_float_68 = gobj.group_properties.unk_float_68
            group.unk_float_6c = gobj.group_properties.unk_float_6c
            group.unk_float_70 = gobj.group_properties.unk_float_70
            group.unk_float_74 = gobj.group_properties.unk_float_74
            group.unk_float_78 = gobj.group_properties.unk_float_78
            group.unk_float_a8 = gobj.group_properties.unk_float_a8
            flod.groups.append(group)
            gidx += 1

        bidx = 0
        for cobj in cobjs:
            child = ChildrenItem()
            gobj = gobjs[bidx]
            child.group_index = gobjs.index(gobj)
            child.bone_tag = cobj.child_properties.bone_tag
            child.pristine_mass = cobj.child_properties.pristine_mass
            child.damaged_mass = cobj.child_properties.damaged_mass
            child.unk_vec = prop_array_to_vector(
                cobj.child_properties.unk_vec)
            child.inertia_tensor = prop_array_to_vector(
                cobj.child_properties.inertia_tensor, 4)

            dobj = get_fragment_drawable(cobj)

            if dobj:
                child.drawable = drawable_from_object(
                    exportop, dobj, exportpath, None, materials, export_settings, True, False)
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
    delete_object(fobj, True)

    return fragment


def export_yft(exportop, obj, filepath, export_settings):
    fragment = fragment_from_object(exportop, obj, filepath, export_settings)
    fragment.write_xml(filepath)

    if export_settings.export_with_hi:
        fragment.drawable.drawable_models_med = None
        fragment.drawable.drawable_models_low = None
        fragment.drawable.drawable_models_vlow = None
        filepath = os.path.join(os.path.dirname(filepath),
                                os.path.basename(filepath).replace(".yft.xml", "_hi.yft.xml"))
        fragment.write_xml(filepath)
