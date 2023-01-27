import bpy
from traceback import format_exc
from typing import Union
from mathutils import Matrix, Vector
from ..tools.utils import multiW
from ..tools.meshhelper import create_uv_layer
from ..cwxml.fragment import YFT, Fragment, LOD, Group, Children, BoneTransform, Window
from ..tools.fragmenthelper import shattermap_to_material
from ..tools.blenderhelper import create_empty_object, get_children_recursive
from ..tools.drawablehelper import drawable_to_asset
from ..ydr.ydrimport import drawable_to_obj, shadergroup_to_materials, create_lights
from ..ybn.ybnimport import bound_to_obj
from ..sollumz_properties import SollumType

import_op: bpy.types.Operator


def import_yft(filepath: str, import_operator: bpy.types.Operator):
    global import_op
    import_op = import_operator

    yft_xml = YFT.from_xml_file(filepath)
    fragment_to_obj(yft_xml, filepath)


def fragment_to_obj(frag_xml: Fragment, filepath: str):
    frag_obj = create_empty_object(
        SollumType.FRAGMENT, frag_xml.name.replace("pack:/", ""))

    set_fragment_properties(frag_xml, frag_obj)

    materials = get_fragment_materials(frag_xml, filepath)
    drawable_obj = create_fragment_drawable(
        frag_obj, frag_xml, filepath, materials, frag_xml.drawable.name)

    if import_op.import_settings.import_as_asset:
        drawable_to_asset(drawable_obj, frag_obj.name)
        bpy.data.objects.remove(frag_obj)
        return

    if frag_xml.lights:
        create_lights(frag_xml.lights, parent=frag_obj,
                      armature_obj=drawable_obj)

    for id, lod_xml in frag_xml.get_lods_by_id().items():
        if not lod_xml.groups:
            continue

        lod_obj = create_lod_obj(frag_obj, lod_xml, id)
        group_objs = create_groups(lod_xml, lod_obj)
        child_objs = create_children(lod_xml, group_objs, filepath, materials)

        create_bounds(lod_xml, child_objs)
        create_vehicle_windows(frag_xml, materials, child_objs)

        lod_obj.parent = frag_obj


def create_lod_obj(frag_obj: bpy.types.Object, lod_xml: LOD, id: int):
    lod_obj = create_empty_object(SollumType.FRAGLOD, lod_xml.tag_name)
    lod_obj.lod_properties.type = id
    set_lod_properties(lod_xml, lod_obj)

    lod_obj.parent = frag_obj

    return lod_obj


def create_groups(lod_xml: LOD, lod_obj: bpy.types.Object):
    group_objs: list[bpy.types.Object] = []

    group_xml: Group
    for group_xml in lod_xml.groups:
        parent_index = group_xml.parent_index

        if 0 > parent_index >= len(lod_xml.groups):
            import_op.report(
                {"WARNING"}, f"Parent index of {parent_index} is out of range for group '{group_xml.name}'! Skipping...")
            continue

        group_obj = create_empty_object(
            SollumType.FRAGGROUP, name=f"{group_xml.name}_group")
        set_group_properties(group_xml, group_obj)

        group_objs.append(group_obj)

        # A parent index of 255 means the group is parented directly under the lod
        if parent_index == 255:
            group_obj.parent = lod_obj
            continue

        group_obj.parent = group_objs[parent_index]

    return group_objs


def create_children(lod_xml: LOD, group_objs: list[bpy.types.Object], filepath: str, materials: list[bpy.types.Material]):
    child_objs: list[bpy.types.Object] = []

    child_xml: Children
    for child_id, child_xml in enumerate(lod_xml.children):
        group_id = child_xml.group_index

        if group_id < 0 or group_id >= len(group_objs):
            import_op.report(
                {"WARNING"}, f"Fragment child #{child_id} has an invalid group index of {group_id}. Skipping...")
            continue

        group_obj = group_objs[group_id]
        name = group_obj.name.replace("_group", "_child")

        child_obj = create_empty_object(SollumType.FRAGCHILD, name=name)
        set_child_properties(child_xml, child_obj, group_obj)

        if child_xml.drawable.drawable_models_high:
            create_fragment_drawable(child_obj, child_xml,
                                     filepath, materials, f"Drawable{child_id}")

        child_objs.append(child_obj)
        child_obj.parent = group_obj

        if not lod_xml.transforms:
            continue

        set_child_transforms(lod_xml, child_obj, child_id)

    return child_objs


def create_bounds(lod_xml: LOD, child_objs: list[bpy.types.Object]) -> Union[bpy.types.Object, None]:
    bounds_xml = lod_xml.archetype.bounds

    if bounds_xml is None:
        import_op.report(
            {"WARNING"}, "Fragment has no collisions! (Make sure the yft file has not been damaged.) Skipping...")
        return None

    # Each bound corresponds to a fragment child
    for child_obj, bound_xml in zip(child_objs, bounds_xml.children):
        bound = bound_to_obj(bound_xml)
        group_obj = child_obj.parent
        bound.name = group_obj.name.replace("_group", "_col")
        bound.parent = group_obj


def create_vehicle_windows(frag_xml: Fragment, materials: list[bpy.types.Material], child_objs: list[bpy.types.Object]):
    window_xml: Window
    for window_xml in frag_xml.vehicle_glass_windows:
        # Each window corresponds to a fragment group
        child_obj = get_window_child(window_xml, child_objs)

        if child_obj is None:
            import_op.report(
                {"WARNING"}, f"Window has an invalid child index (ItemID) of {window_xml.item_id}! Expected a number in the range 0-{len(child_objs)} Skipping...")
            continue

        window_name = child_obj.name.replace("_child", "_vehicle_window")

        try:
            mesh = create_vehicle_window_mesh(
                window_xml, window_name, child_obj.matrix_basis)
        except:
            import_op.report(
                {"ERROR"}, f"Error during creation of vehicle window mesh:\n{format_exc()}")
            continue

        texcoords = [[0, 1], [0, 0], [1, 0], [1, 1]]
        create_uv_layer(mesh, 0, "UVMap", texcoords, flip_uvs=False)

        shattermap_mat = shattermap_to_material(
            window_xml.shattermap, mesh.name + "_shattermap.bmp")
        mesh.materials.append(shattermap_mat)

        # UnkUShort1 indexes the geometry that the window uses.
        # The VehicleGlassWindow uses the same material that the geometry uses.
        geometry_index = window_xml.unk_ushort_1
        window_mat = get_geometry_material(frag_xml, materials, geometry_index)
        mesh.materials.append(window_mat)

        window_obj = bpy.data.objects.new(mesh.name, mesh)
        window_obj.sollum_type = SollumType.FRAGVEHICLEWINDOW

        set_veh_window_properties(window_xml, window_obj)

        bpy.context.collection.objects.link(window_obj)

        window_obj.parent = child_obj


def get_fragment_materials(frag_xml: Fragment, filepath: str) -> Union[list[bpy.types.Material], None]:
    if not frag_xml.drawable:
        return None

    return shadergroup_to_materials(frag_xml.drawable.shader_group, filepath)


def create_fragment_drawable(frag_obj: bpy.types.Object, frag_xml: Fragment, filepath: str, materials: list[bpy.types.Material], name: str) -> Union[bpy.types.Object, None]:
    if not frag_xml.drawable:
        return None

    drawable_xml = frag_xml.drawable

    drawable_obj = drawable_to_obj(drawable=drawable_xml, filepath=filepath,
                                   name=name, materials=materials, import_settings=import_op.import_settings)

    if drawable_obj is not None:
        drawable_obj.matrix_basis = drawable_xml.matrix
        drawable_obj.parent = frag_obj

    return drawable_obj


def set_child_transforms(lod_xml: LOD, child_obj: bpy.types.Object, child_id: int):
    transform = lod_xml.transforms[child_id].value
    a = transform[3][0] + lod_xml.position_offset.x
    b = transform[3][1] + lod_xml.position_offset.y
    c = transform[3][2] + lod_xml.position_offset.z
    transform[3][0] = a
    transform[3][1] = b
    transform[3][2] = c

    child_obj.matrix_basis = transform.transposed()


def get_window_child(window_xml: Window, child_objs: list[bpy.types.Object]) -> Union[bpy.types.Object, None]:
    child_id = window_xml.item_id

    if child_id < 0 or child_id >= len(child_objs):
        return None

    return child_objs[child_id]


def create_vehicle_window_mesh(window_xml: Window, name: str, child_matrix: Vector):
    verts = calculate_window_verts(window_xml)
    verts = [(vert - child_matrix.translation) @ child_matrix
             for vert in verts]
    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)

    return mesh


def calculate_window_verts(window_xml: Window):
    """Calculate the 4 vertices of the window from the projection matrix."""
    proj_mat = get_window_projection_matrix(window_xml)

    min = Vector((0, 0, 0))
    max = Vector((window_xml.width / 2, window_xml.height, 1))

    v0 = multiW(proj_mat, Vector((min.x, min.y, 0)))
    v1 = multiW(proj_mat, Vector((min.x, max.y, 0)))
    v2 = multiW(proj_mat, Vector((max.x, max.y, 0)))
    v3 = multiW(proj_mat, Vector((max.x, min.y, 0)))

    return v0, v1, v2, v3


def get_window_projection_matrix(window_xml: Window):
    proj_mat: Matrix = window_xml.projection_matrix
    proj_mat[3][3] = 1

    return proj_mat.transposed().inverted_safe()


def get_geometry_material(frag_xml: Fragment, materials: list[bpy.types.Material], geometry_index: int) -> Union[bpy.types.Material, None]:
    """Get the material that the given geometry uses."""
    for dmodel in frag_xml.drawable.drawable_models_high:
        geometries = dmodel.geometries

        if geometry_index > len(geometries):
            return None

        geometry = geometries[geometry_index]
        shader_index = geometry.shader_index

        if shader_index > len(materials):
            return None

        return materials[shader_index]


def set_fragment_properties(frag_xml: Fragment, frag_obj: bpy.types.Object):
    frag_obj.fragment_properties.unk_b0 = frag_xml.unknown_b0
    frag_obj.fragment_properties.unk_b8 = frag_xml.unknown_b8
    frag_obj.fragment_properties.unk_bc = frag_xml.unknown_bc
    frag_obj.fragment_properties.unk_c0 = frag_xml.unknown_c0
    frag_obj.fragment_properties.unk_c4 = frag_xml.unknown_c4
    frag_obj.fragment_properties.unk_cc = frag_xml.unknown_cc
    frag_obj.fragment_properties.gravity_factor = frag_xml.gravity_factor
    frag_obj.fragment_properties.buoyancy_factor = frag_xml.buoyancy_factor


def set_lod_properties(lod_xml: LOD, lod_obj: bpy.types.Object):
    lod_obj.lod_properties.unknown_14 = lod_xml.unknown_14
    lod_obj.lod_properties.unknown_18 = lod_xml.unknown_18
    lod_obj.lod_properties.unknown_1c = lod_xml.unknown_1c
    lod_obj.lod_properties.position_offset = lod_xml.position_offset
    lod_obj.lod_properties.unknown_40 = lod_xml.unknown_40
    lod_obj.lod_properties.unknown_50 = lod_xml.unknown_50
    lod_obj.lod_properties.damping_linear_c = lod_xml.damping_linear_c
    lod_obj.lod_properties.damping_linear_v = lod_xml.damping_linear_v
    lod_obj.lod_properties.damping_linear_v2 = lod_xml.damping_linear_v2
    lod_obj.lod_properties.damping_angular_c = lod_xml.damping_angular_c
    lod_obj.lod_properties.damping_angular_v = lod_xml.damping_angular_v
    lod_obj.lod_properties.damping_angular_v2 = lod_xml.damping_angular_v2
    # archetype properties
    lod_obj.lod_properties.archetype_name = lod_xml.archetype.name
    lod_obj.lod_properties.archetype_mass = lod_xml.archetype.mass
    lod_obj.lod_properties.archetype_unknown_48 = lod_xml.archetype.unknown_48
    lod_obj.lod_properties.archetype_unknown_4c = lod_xml.archetype.unknown_4c
    lod_obj.lod_properties.archetype_unknown_50 = lod_xml.archetype.unknown_50
    lod_obj.lod_properties.archetype_unknown_54 = lod_xml.archetype.unknown_54
    lod_obj.lod_properties.archetype_inertia_tensor = lod_xml.archetype.inertia_tensor


def set_group_properties(group_xml: Group, group_obj: bpy.types.Object):
    group_obj.group_properties.name = group_xml.name
    group_obj.group_properties.glass_window_index = group_xml.glass_window_index
    group_obj.group_properties.glass_flags = group_xml.glass_flags
    group_obj.group_properties.strength = group_xml.strength
    group_obj.group_properties.force_transmission_scale_up = group_xml.force_transmission_scale_up
    group_obj.group_properties.force_transmission_scale_down = group_xml.force_transmission_scale_down
    group_obj.group_properties.joint_stiffness = group_xml.joint_stiffness
    group_obj.group_properties.min_soft_angle_1 = group_xml.min_soft_angle_1
    group_obj.group_properties.max_soft_angle_1 = group_xml.max_soft_angle_1
    group_obj.group_properties.max_soft_angle_2 = group_xml.max_soft_angle_2
    group_obj.group_properties.max_soft_angle_3 = group_xml.max_soft_angle_3
    group_obj.group_properties.rotation_speed = group_xml.rotation_speed
    group_obj.group_properties.rotation_strength = group_xml.rotation_strength
    group_obj.group_properties.restoring_max_torque = group_xml.restoring_max_torque
    group_obj.group_properties.latch_strength = group_xml.latch_strength
    group_obj.group_properties.mass = group_xml.mass
    group_obj.group_properties.min_damage_force = group_xml.min_damage_force
    group_obj.group_properties.damage_health = group_xml.damage_health
    group_obj.group_properties.unk_float_5c = group_xml.unk_float_5c
    group_obj.group_properties.unk_float_60 = group_xml.unk_float_60
    group_obj.group_properties.unk_float_64 = group_xml.unk_float_64
    group_obj.group_properties.unk_float_68 = group_xml.unk_float_68
    group_obj.group_properties.unk_float_6c = group_xml.unk_float_6c
    group_obj.group_properties.unk_float_70 = group_xml.unk_float_70
    group_obj.group_properties.unk_float_74 = group_xml.unk_float_74
    group_obj.group_properties.unk_float_78 = group_xml.unk_float_78
    group_obj.group_properties.unk_float_a8 = group_xml.unk_float_a8


def set_child_properties(child_xml: Children, child_obj: bpy.types.Object, group_obj: bpy.types.Object):
    child_obj.child_properties.group = group_obj
    child_obj.child_properties.bone_tag = child_xml.bone_tag
    child_obj.child_properties.pristine_mass = child_xml.pristine_mass
    child_obj.child_properties.damaged_mass = child_xml.damaged_mass
    child_obj.child_properties.unk_vec = child_xml.unk_vec
    child_obj.child_properties.inertia_tensor = child_xml.inertia_tensor


def set_veh_window_properties(window_xml: Window, window_obj: bpy.types.Object):
    window_obj.vehicle_window_properties.unk_float_17 = window_xml.unk_float_17
    window_obj.vehicle_window_properties.unk_float_18 = window_xml.unk_float_18
    window_obj.vehicle_window_properties.cracks_texture_tiling = window_xml.cracks_texture_tiling
