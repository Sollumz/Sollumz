import os
from mathutils import Matrix, Vector
from ..sollumz_properties import BOUND_TYPES, SollumType
from ..ydr.ydrexport import drawable_from_object, get_used_materials, lights_from_object
from ..ybn.ybnexport import composite_from_objects
from ..cwxml.fragment import BoneTransform, Children, Fragment, Group, LOD, Transform, Window
from ..sollumz_helper import get_sollumz_objects_from_objects
from ..tools.fragmenthelper import image_to_shattermap
from ..tools.meshhelper import get_bound_center, get_sphere_radius, calculate_inertia, calculate_volume
from ..tools.utils import divide_vector_inv, prop_array_to_vector
from ..tools.blenderhelper import remove_number_suffix


def get_bone_tag_from_group_name(group_name, drawable):
    for bone in drawable.skeleton.bones:
        if bone.name == group_name:
            return bone.tag

    return 0


def get_fragment_drawable(fragment):
    for child in fragment.children:
        if child.sollum_type == SollumType.DRAWABLE:
            return child


def get_group_objects(fragment, index=0):
    groups = []
    for child in fragment.children:
        if child.sollum_type == SollumType.FRAGGROUP:
            groups.append(child)
            index += 1
    for g in groups:
        cgroups = get_group_objects(g, index)
        for cg in cgroups:
            if cg not in groups:
                groups.append(cg)

    return groups


def get_obj_parent_group_index(gobjs, obj):
    parent = obj.parent
    if parent.sollum_type == SollumType.FRAGGROUP:
        return gobjs.index(parent)
    else:
        return 255


def get_obj_parent_child_index(cobjs, obj):
    parent = obj.parent
    if parent.sollum_type == SollumType.FRAGCHILD:
        return cobjs.index(parent)
    else:
        return 0


def get_shattermap_image(obj):
    mat = obj.data.materials[0]
    return mat.node_tree.nodes["ShatterMap"].image


def get_window_material(obj):
    """Get first material with a vehicle_vehglass shader."""
    for material in obj.data.materials:
        if "vehicle_vehglass" in material.shader_properties.name:
            return material
    return None


def get_window_geometry_index(drawable_xml, window_shader_index):
    """Get index of the geometry using the window material."""
    for dmodel_xml in drawable_xml.drawable_models_high:
        for (index, geometry) in enumerate(dmodel_xml.geometries):
            if geometry.shader_index != window_shader_index:
                continue

            return index

    return 0


def obj_to_vehicle_window(obj, drawable_xml, materials):
    mesh = obj.data

    v1 = None
    v2 = None
    v3 = None

    for loop in mesh.loops:
        vert_idx = loop.vertex_index
        uv = mesh.uv_layers[0].data[loop.index].uv
        if uv.x == 0 and uv.y == 1:
            v1 = mesh.vertices[vert_idx].co
        elif uv.x == 1 and uv.y == 1:
            v2 = mesh.vertices[vert_idx].co
        elif uv.x == 0 and uv.y == 0:
            v3 = mesh.vertices[vert_idx].co

    shattermap = get_shattermap_image(obj)
    resx = shattermap.size[0]
    resy = shattermap.size[1]
    thickness = 0.01

    edge1 = (v2 - v1) / resx
    edge2 = (v3 - v1) / resy
    edge3 = edge1.normalized().cross(edge2.normalized()) * thickness

    mat = Matrix()
    mat[0] = edge1.x, edge2.x, edge3.x, v1.x
    mat[1] = edge1.y, edge2.y, edge3.y, v1.y
    mat[2] = edge1.z, edge2.z, edge3.z, v1.z
    mat.translation += obj.matrix_world.translation
    mat.invert_safe()

    window = Window()
    window.projection_matrix = mat
    window.shattermap = image_to_shattermap(shattermap)

    window.unk_float_17 = obj.vehicle_window_properties.unk_float_17
    window.unk_float_18 = obj.vehicle_window_properties.unk_float_18
    window.cracks_texture_tiling = obj.vehicle_window_properties.cracks_texture_tiling

    window_material = get_window_material(obj)

    if window_material is None:
        # Warning needed
        return window

    if window_material not in materials:
        # Warning needed
        return window

    window_shader_index = materials.index(window_material)
    window.unk_ushort_1 = get_window_geometry_index(
        drawable_xml, window_shader_index)

    return window


def create_bone_transforms(frag, drawable_obj):
    for bone in drawable_obj.data.bones:
        frag.bones_transforms.append(
            BoneTransform("Item", bone.matrix_local))


def fragment_from_object(exportop, fobj, exportpath):
    fragment = Fragment()

    dobj = None
    for child in fobj.children:
        if child.sollum_type == SollumType.DRAWABLE:
            dobj = child
    if dobj is None:
        raise Exception("NO DRAWABLE TO EXPORT.")

    materials = None
    materials = get_used_materials(fobj)

    fragment.drawable = drawable_from_object(
        exportop, dobj, exportpath, None, materials, True)

    lights_from_object(fobj, fragment.lights, armature_obj=dobj)

    fragment.name = "pack:/" + remove_number_suffix(fobj.name)
    fragment.bounding_sphere_center = fragment.drawable.bounding_sphere_center
    fragment.bounding_sphere_radius = fragment.drawable.bounding_sphere_radius

    fragment.unknown_b0 = fobj.fragment_properties.unk_b0
    fragment.unknown_b8 = fobj.fragment_properties.unk_b8
    fragment.unknown_bc = fobj.fragment_properties.unk_bc
    fragment.unknown_c0 = fobj.fragment_properties.unk_c0
    fragment.unknown_c4 = fobj.fragment_properties.unk_c4
    fragment.unknown_cc = fobj.fragment_properties.unk_cc
    fragment.gravity_factor = fobj.fragment_properties.gravity_factor
    fragment.buoyancy_factor = fobj.fragment_properties.buoyancy_factor

    create_bone_transforms(fragment, dobj)

    lods = []
    for child in fobj.children:
        if child.sollum_type == SollumType.FRAGLOD:
            lods.append(child)

    lod1 = None
    lod2 = None
    lod3 = None

    for idx, lod in enumerate(lods):
        gobjs = get_group_objects(lod)
        bobjs = get_sollumz_objects_from_objects(gobjs, BOUND_TYPES)
        cobjs = get_sollumz_objects_from_objects(gobjs, SollumType.FRAGCHILD)
        vwobjs = get_sollumz_objects_from_objects(
            cobjs, SollumType.FRAGVEHICLEWINDOW)

        flod = LOD()
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

        flod.archetype.bounds = composite_from_objects(
            bobjs, exportop.export_settings, True)

        if exportop.export_settings.auto_calculate_inertia:
            flod.archetype.inertia_tensor = calculate_inertia(
                flod.archetype.bounds.box_min, flod.archetype.bounds.box_max) * flod.archetype.mass
        else:
            arch_it = prop_array_to_vector(
                lod.lod_properties.archetype_inertia_tensor)
            flod.archetype.inertia_tensor = arch_it

        flod.archetype.inertia_tensor_inv = divide_vector_inv(
            flod.archetype.inertia_tensor)

        gidx = 0
        for gobj in gobjs:
            group = Group()
            group.name = gobj.name if "group" not in gobj.name else gobj.name.replace(
                "_group", "").split(".")[0]
            group.parent_index = get_obj_parent_group_index(gobjs, gobj)
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

        for i, cobj in enumerate(cobjs):
            child = Children()
            gobj = cobj.parent
            child.group_index = gobjs.index(gobj)
            child.pristine_mass = cobj.child_properties.pristine_mass
            child.damaged_mass = cobj.child_properties.damaged_mass
            child.unk_vec = prop_array_to_vector(
                cobj.child_properties.unk_vec)

            if exportop.export_settings.auto_calculate_bone_tag:
                child.bone_tag = get_bone_tag_from_group_name(
                    flod.groups[child.group_index].name, fragment.drawable)
            else:
                child.bone_tag = cobj.child_properties.bone_tag

            bounds = flod.archetype.bounds

            if bounds is not None and i < len(bounds.children):
                child_bound = bounds.children[i]
                inertia = child_bound.inertia * child.pristine_mass
                child.inertia_tensor = Vector(
                    (inertia.x, inertia.y, inertia.z, child_bound.volume * child.pristine_mass))

            child_dobj = get_fragment_drawable(cobj)

            if child_dobj:
                child.drawable = drawable_from_object(
                    exportop, child_dobj, exportpath, None, materials, True, False)
            else:
                child.drawable.matrix = Matrix()
                child.drawable.shader_group = None
                child.drawable.skeleton = None
                child.drawable.joints = None

            transform = cobj.matrix_basis.transposed()
            a = transform[3][0] - pos_offset.x
            b = transform[3][1] - pos_offset.y
            c = transform[3][2] - pos_offset.z
            transform[3][0] = a
            transform[3][1] = b
            transform[3][2] = c
            flod.transforms.append(Transform("Item", transform))
            flod.children.append(child)

        for wobj in vwobjs:
            vehwindow = obj_to_vehicle_window(
                wobj, fragment.drawable, materials)
            vehwindow.item_id = get_obj_parent_child_index(cobjs, wobj)
            fragment.vehicle_glass_windows.append(vehwindow)

        if lod.lod_properties.type == 1:
            lod1 = flod
        elif lod.lod_properties.type == 2:
            lod2 = flod
        elif lod.lod_properties.type == 3:
            lod3 = flod

    fragment.physics.lod1 = lod1
    fragment.physics.lod2 = lod2
    fragment.physics.lod3 = lod3

    return fragment


def export_yft(exportop, obj, filepath, export_settings):
    fragment = fragment_from_object(exportop, obj, filepath)
    fragment.write_xml(filepath)

    if export_settings.export_with_hi:
        fragment.drawable.drawable_models_med = None
        fragment.drawable.drawable_models_low = None
        fragment.drawable.drawable_models_vlow = None
        for child in fragment.physics.lod1.children:
            child.drawable.drawable_models_med = None
            child.drawable.drawable_models_low = None
            child.drawable.drawable_models_vlow = None
        filepath = os.path.join(os.path.dirname(filepath),
                                os.path.basename(filepath).replace(".yft.xml", "_hi.yft.xml"))
        fragment.write_xml(filepath)
