import os
import bpy
from traceback import format_exc
from mathutils import Matrix, Vector
from typing import Optional
from ..tools.blenderhelper import create_empty_object, material_from_image, create_mesh_object, remove_number_suffix
from ..tools.meshhelper import create_uv_layer
from ..tools.drawablehelper import drawable_to_asset
from ..tools.utils import multiply_homogeneous
from ..sollumz_properties import SollumType, SollumzImportSettings, LODLevel
from ..cwxml.fragment import YFT, Fragment, LOD, Group, Children, Window
from ..cwxml.drawable import Drawable, Bone, ShaderGroup
from ..ydr.ydrimport import shadergroup_to_materials, shader_item_to_material, skeleton_to_obj, rotation_limits_to_obj, create_lights
from ..ybn.ybnimport import create_bound_object
from ..ydr.ydrexport import calculate_bone_tag
from .. import logger
from .properties import LODProperties
from .create_drawable_meshes import create_drawable_meshes, create_drawable_meshes_split_by_group, add_armature_constraint, create_joined_mesh


def import_yft(filepath: str, import_settings: SollumzImportSettings):
    yft_xml: YFT = YFT.from_xml_file(filepath)

    hi_xml: YFT | None = parse_hi_yft(
        filepath) if import_settings.import_with_hi else None

    create_fragment_obj(yft_xml, filepath,
                        split_by_group=import_settings.split_by_group, hi_xml=hi_xml)


def parse_hi_yft(yft_filepath: str) -> Fragment | None:
    """Parse hi_yft at the provided non_hi yft filepath (if it exists)."""
    yft_dir = os.path.dirname(yft_filepath)
    yft_name = os.path.basename(yft_filepath).split(".")[0]

    hi_path = os.path.join(yft_dir, f"{yft_name}_hi.yft.xml")

    if os.path.exists(hi_path):
        # Only the drawable is needed
        return YFT.from_xml_file(hi_path)
    else:
        logger.warning(
            f"Could not find _hi yft for {os.path.basename(yft_filepath)}! Make sure there is a file named '{os.path.basename(hi_path)}' in the same directory!")


def create_fragment_obj(frag_xml: Fragment, filepath: str, split_by_group: bool = False, hi_xml: Optional[Fragment] = None):
    frag_obj = create_frag_armature(frag_xml)
    set_fragment_properties(frag_xml, frag_obj)

    mesh_objs, materials, hi_materials = create_fragment_meshes(
        frag_xml, frag_obj, filepath, split_by_group, hi_xml)
    mesh_parent = parent_mesh_objects(mesh_objs, frag_obj)

    create_frag_collisions(frag_xml, frag_obj)

    create_phys_lods(frag_xml, frag_obj)
    set_all_bone_physics_properties(frag_obj.data, frag_xml)

    create_phys_child_meshes(
        frag_xml, frag_obj, mesh_parent, materials, hi_materials, hi_xml)

    if frag_xml.vehicle_glass_windows:
        create_vehicle_windows(frag_xml, frag_obj, materials)

    if frag_xml.lights:
        lights_parent = create_lights(frag_xml.lights, frag_obj, frag_obj)
        lights_parent.name = f"{frag_obj.name}.lights"


def create_frag_armature(frag_xml: Fragment):
    """Create the fragment armature along with the bones and rotation limits."""
    name = frag_xml.name.replace("pack:/", "")
    skel = bpy.data.armatures.new(f"{name}.skel")
    frag_obj = create_mesh_object(SollumType.FRAGMENT, name, skel)

    skeleton_to_obj(frag_xml.drawable.skeleton, frag_obj)
    rotation_limits_to_obj(frag_xml.drawable.joints.rotation_limits, frag_obj)

    return frag_obj


def create_fragment_meshes(frag_xml: Fragment, frag_obj: bpy.types.Object, filepath: str, split_by_group: bool = False, hi_xml: Optional[Fragment] = None):
    """Create all fragment mesh objects. Returns a list of mesh objects, a list of materials, and a list of hi_materials."""
    materials: list[bpy.types.Material] = shadergroup_to_materials(
        frag_xml.drawable.shader_group, filepath)
    rename_materials(materials)

    drawable_xml = frag_xml.drawable

    mesh_objs = (
        create_drawable_meshes(drawable_xml, materials, frag_obj)
        if not split_by_group
        else create_drawable_meshes_split_by_group(drawable_xml, materials, frag_obj)
    )

    hi_materials = []

    if hi_xml is not None:
        hi_materials = create_hi_materials(
            materials, frag_xml.drawable.shader_group, hi_xml.drawable.shader_group, filepath)

        hi_mesh_objs = (
            create_drawable_meshes(hi_xml.drawable, hi_materials, frag_obj)
            if not split_by_group
            else create_drawable_meshes_split_by_group(hi_xml.drawable, hi_materials, frag_obj)
        )
        set_hi_lods(mesh_objs, hi_mesh_objs)

    return mesh_objs, materials, hi_materials


def rename_materials(materials: list[bpy.types.Material]):
    """Rename materials to use texture name."""
    for material in materials:
        for node in material.node_tree.nodes:
            if not isinstance(node, bpy.types.ShaderNodeTexImage) or not node.is_sollumz or node.name != "DiffuseSampler":
                continue

            material.name = node.sollumz_texture_name
            break


def create_hi_materials(non_hi_materials: list[bpy.types.Material], shader_group: ShaderGroup, hi_shader_group: ShaderGroup, filepath: str):
    """Create the _hi materials. Returns a list with the hi materials and non_hi_materials merged."""
    hi_materials: list[bpy.types.Material] = []
    non_hi_index = 0

    # Loop through hi shaders and compare with non_hi shaders each iteration. If the hi_shader and non_hi shader are the same,
    # add the already created non_hi material to hi_materials. Otherwise create the hi material and add it to hi_materials.
    for shader in hi_shader_group.shaders:
        if non_hi_index >= len(shader_group.shaders) or shader_group.shaders[non_hi_index].name != shader.name:
            hi_mat = shader_item_to_material(shader, hi_shader_group, filepath)
            hi_materials.append(hi_mat)

            continue

        hi_materials.append(non_hi_materials[non_hi_index])
        non_hi_index += 1

    return hi_materials


def set_hi_lods(mesh_objs: list[bpy.types.Object], hi_mesh_objs: list[bpy.types.Object]):
    """Add the hi_meshes to the very high LOD level of each corresponding non_hi_mesh. Deletes all hi_mesh_objs."""
    hi_meshes_by_name: dict[str, bpy.types.Object] = {
        remove_number_suffix(obj.name): obj for obj in hi_mesh_objs}

    for obj in mesh_objs:
        obj_name = remove_number_suffix(obj.name)

        if obj_name not in hi_meshes_by_name:
            continue

        hi_mesh = hi_meshes_by_name[obj_name]
        hi_mesh.data.name = f"{obj_name}_very_high"
        obj.sollumz_object_lods.set_lod_mesh(LODLevel.VERYHIGH, hi_mesh.data)
        obj.sollumz_object_lods.set_active_lod(LODLevel.VERYHIGH)

        bpy.data.objects.remove(hi_mesh)

        # In case a .00# suffix got added
        obj.name = obj_name


def parent_mesh_objects(mesh_objs: list[bpy.types.Object], frag_obj: bpy.types.Object):
    """Parent all mesh objects to an empty which is parented to the fragment object."""
    mesh_empty = create_empty_object(
        SollumType.NONE, f"{frag_obj.name}.mesh")
    mesh_empty.parent = frag_obj

    for obj in mesh_objs:
        obj.parent = mesh_empty

    return mesh_empty


def create_phys_lods(frag_xml: Fragment, frag_obj: bpy.types.Object):
    """Create the Fragment.Physics.LOD1 data-block. (Currently LOD1 is only supported)"""
    for i, lod_xml in frag_xml.get_lods_by_id().items():
        if not lod_xml.groups:
            continue

        lod_props: LODProperties = frag_obj.sollumz_fragment_lods.add()
        set_lod_properties(lod_xml, lod_props)
        lod_props.number = i


def set_all_bone_physics_properties(armature: bpy.types.Armature, frag_xml: Fragment):
    """Set the physics group properties for all bones in the armature."""
    groups_xml: list[Group] = frag_xml.physics.lod1.groups

    for group_xml in groups_xml:
        if group_xml.name not in armature.bones:
            logger.warning(
                f"No bone exists for the physics group {group_xml.name}! Skipping...")
            continue

        bone = armature.bones[group_xml.name]
        bone.sollumz_use_physics = True
        set_group_properties(group_xml, bone)


def drawable_is_empty(drawable: Drawable):
    return len(drawable.all_models) == 0


def create_frag_collisions(frag_xml: Fragment, frag_obj: bpy.types.Object) -> bpy.types.Object | None:
    bounds_xml = frag_xml.physics.lod1.archetype.bounds

    if bounds_xml is None:
        logger.warn(
            "Fragment has no collisions! (Make sure the yft file has not been damaged) Skipping...")
        return None

    collisions_empty = create_empty_object(
        SollumType.NONE, f"{frag_obj.name}.col")
    collisions_empty.parent = frag_obj

    for i, bound_xml in enumerate(bounds_xml.children):
        bound_obj = create_bound_object(bound_xml)
        bound_obj.parent = collisions_empty

        bone = find_bound_bone(i, frag_xml)
        if bone is None:
            continue

        bound_obj.name = f"{bone.name}.col"
        add_armature_constraint(bound_obj, frag_obj, bone.name, False)
        bound_obj.child_properties.mass = frag_xml.physics.lod1.children[i].pristine_mass


def find_bound_bone(bound_index: int, frag_xml: Fragment) -> Bone | None:
    """Get corresponding bound bone based on children"""
    children = frag_xml.physics.lod1.children

    if bound_index >= len(children):
        return

    corresponding_child = children[bound_index]
    for bone in frag_xml.drawable.skeleton.bones:
        if bone.tag != corresponding_child.bone_tag:
            continue

        return bone


def create_phys_child_meshes(frag_xml: Fragment, frag_obj: bpy.types.Object, mesh_parent: bpy.types.Object, materials: list[bpy.types.Material], hi_materials: Optional[list[bpy.types.Material]] = None, hi_xml: Optional[Fragment] = None):
    """Create all Fragment.Physics.LOD1.Children meshes. (Only LOD1 currently supported)"""
    lod_xml = frag_xml.physics.lod1
    children_xml: list[Children] = lod_xml.children
    bones = frag_xml.drawable.skeleton.bones

    bone_name_by_tag: dict[str, Bone] = {
        bone.tag: bone.name for bone in bones}

    child_meshes: list[bpy.types.Object] = []

    for i, child_xml in enumerate(children_xml):
        if drawable_is_empty(child_xml.drawable):
            continue

        if child_xml.bone_tag not in bone_name_by_tag:
            logger.warning(
                "A fragment child has an invalid bone tag! Skipping...")
            continue

        bone_name = bone_name_by_tag[child_xml.bone_tag]

        child_obj = create_phys_child_mesh(
            child_xml.drawable, frag_obj, materials, bone_name)

        if hi_xml is not None and hi_materials is not None:
            hi_children: list[Children] = hi_xml.physics.lod1.children
            hi_drawable = hi_children[i].drawable
            create_frag_child_hi_lod(
                bone_name, child_obj, hi_drawable, hi_materials)

        child_obj.parent = mesh_parent

    return child_meshes


def create_phys_child_mesh(drawable_xml: Drawable, frag_obj: bpy.types.Object, materials: list[bpy.types.Material], bone_name: str):
    """Create a single physics child mesh"""
    child_obj = create_joined_mesh(drawable_xml, materials)
    add_armature_constraint(child_obj, frag_obj, bone_name)
    child_obj.name = f"{bone_name}.child"
    child_obj.is_physics_child_mesh = True

    return child_obj


def create_frag_child_hi_lod(name: str, child_obj: bpy.types.Object, hi_drawable: Drawable, hi_materials: list[bpy.types.Material]):
    """Create hi lod for a physics child mesh"""
    child_hi_obj = create_joined_mesh(hi_drawable, hi_materials)
    child_hi_obj.data.name = f"{name}_very_high"

    child_obj.sollumz_object_lods.set_lod_mesh(
        LODLevel.VERYHIGH, child_hi_obj.data)
    child_obj.sollumz_object_lods.set_active_lod(LODLevel.VERYHIGH)

    bpy.data.objects.remove(child_hi_obj)


def create_vehicle_windows(frag_xml: Fragment, frag_obj: bpy.types.Object, materials: list[bpy.types.Material]):
    veh_windows_empty = create_empty_object(
        SollumType.NONE, f"{frag_obj.name}.glass_shards")
    veh_windows_empty.parent = frag_obj

    window_xml: Window
    for window_xml in frag_xml.vehicle_glass_windows:
        window_bone = get_window_bone(
            window_xml, frag_xml, frag_obj.data.bones)

        window_name = f"{window_bone.name}_glass_shard"

        try:
            mesh = create_vehicle_window_mesh(
                window_xml, window_name, window_bone.matrix_local.translation)
        except:
            logger.error(
                f"Error during creation of vehicle window mesh:\n{format_exc()}")
            continue

        if window_xml.shattermap:
            shattermap_mat = shattermap_to_material(
                window_xml.shattermap, mesh.name + "_shattermap.bmp")
            mesh.materials.append(shattermap_mat)

        add_veh_window_material(window_xml, frag_xml.drawable, materials, mesh)

        window_obj = create_veh_window_object(
            frag_obj, window_xml, window_bone, mesh)
        window_obj.parent = veh_windows_empty


def add_veh_window_material(window_xml: Window, drawable_xml: Drawable, materials: list[bpy.types.Material], mesh: bpy.types.Mesh):
    """Add material to vehicle window based on UnkUShort1."""
    # UnkUShort1 indexes the geometry that the window uses.
    # The VehicleGlassWindow uses the same material that the geometry uses.
    geometry_index = window_xml.unk_ushort_1
    window_mat = get_geometry_material(drawable_xml, materials, geometry_index)
    mesh.materials.append(window_mat)


def create_veh_window_object(frag_obj: bpy.types.Object, window_xml: Window, window_bone: bpy.types.Bone, mesh: bpy.types.Mesh):
    window_obj = bpy.data.objects.new(mesh.name, mesh)
    window_obj.sollum_type = SollumType.FRAGVEHICLEWINDOW

    window_obj.location = window_bone.matrix_local.translation
    add_armature_constraint(window_obj, frag_obj,
                            window_bone.name, set_transforms=False)
    set_veh_window_properties(window_xml, window_obj)

    bpy.context.collection.objects.link(window_obj)

    return window_obj


def get_window_bone(window_xml: Window, frag_xml: Fragment, bpy_bones: bpy.types.ArmatureBones) -> bpy.types.Bone:
    """Get bone connected to window based on the bone tag of the physics child associated with the window."""
    children_xml: list[Children] = frag_xml.physics.lod1.children

    child_id: int = window_xml.item_id

    if child_id < 0 or child_id >= len(children_xml):
        return bpy_bones[0]

    child_xml = children_xml[child_id]

    for bone in bpy_bones:
        if calculate_bone_tag(bone.name) != child_xml.bone_tag:
            continue

        return bone

    # Return root bone if no bone is found
    return bpy_bones[0]


def create_vehicle_window_mesh(window_xml: Window, name: str, window_location: Vector):
    verts = calculate_window_verts(window_xml)
    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.transform(Matrix.Translation(-window_location))

    texcoords = [[0, 1], [0, 0], [1, 0], [1, 1]]
    create_uv_layer(mesh, 0, texcoords, flip_uvs=False)

    return mesh


def calculate_window_verts(window_xml: Window):
    """Calculate the 4 vertices of the window from the projection matrix."""
    proj_mat = get_window_projection_matrix(window_xml)

    min = Vector((0, 0, 0))
    max = Vector((window_xml.width / 2, window_xml.height, 1))

    v0 = multiply_homogeneous(proj_mat, Vector((min.x, min.y, 0)))
    v1 = multiply_homogeneous(proj_mat, Vector((min.x, max.y, 0)))
    v2 = multiply_homogeneous(proj_mat, Vector((max.x, max.y, 0)))
    v3 = multiply_homogeneous(proj_mat, Vector((max.x, min.y, 0)))

    return v0, v1, v2, v3


def get_window_projection_matrix(window_xml: Window):
    proj_mat: Matrix = window_xml.projection_matrix
    # proj_mat[3][3] is currently an unknown value so it is set to 1 (CW does the same)
    proj_mat[3][3] = 1

    return proj_mat.transposed().inverted_safe()


def get_rgb(value):
    if value == "##":
        return [0, 0, 0, 1]
    elif value == "--":
        return [1, 1, 1, 1]
    else:
        value = int(value, 16)
        return [value / 255, value / 255, value / 255, 1]


def shattermap_to_image(shattermap, name):
    width = int(len(shattermap[0]) / 2)
    height = int(len(shattermap))

    img = bpy.data.images.new(name, width, height)

    pixels = []
    i = 0
    for row in reversed(shattermap):
        frow = [row[x:x + 2] for x in range(0, len(row), 2)]
        for value in frow:
            pixels.append(get_rgb(value))
            i += 1

    pixels = [chan for px in pixels for chan in px]
    img.pixels = pixels
    return img


def shattermap_to_material(shattermap, name):
    img = shattermap_to_image(shattermap, name)
    return material_from_image(img, name, "ShatterMap")


def get_geometry_material(drawable_xml: Drawable, materials: list[bpy.types.Material], geometry_index: int) -> bpy.types.Material | None:
    """Get the material that the given geometry uses."""
    for dmodel in drawable_xml.drawable_models_high:
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


def set_lod_properties(lod_xml: LOD, lod_props: LODProperties):
    lod_props.unknown_14 = lod_xml.unknown_14
    lod_props.unknown_18 = lod_xml.unknown_18
    lod_props.unknown_1c = lod_xml.unknown_1c
    lod_props.position_offset = lod_xml.position_offset
    lod_props.unknown_40 = lod_xml.unknown_40
    lod_props.unknown_50 = lod_xml.unknown_50
    lod_props.damping_linear_c = lod_xml.damping_linear_c
    lod_props.damping_linear_v = lod_xml.damping_linear_v
    lod_props.damping_linear_v2 = lod_xml.damping_linear_v2
    lod_props.damping_angular_c = lod_xml.damping_angular_c
    lod_props.damping_angular_v = lod_xml.damping_angular_v
    lod_props.damping_angular_v2 = lod_xml.damping_angular_v2
    # archetype properties
    lod_props.archetype_name = lod_xml.archetype.name
    lod_props.archetype_mass = lod_xml.archetype.mass
    lod_props.archetype_unknown_48 = lod_xml.archetype.unknown_48
    lod_props.archetype_unknown_4c = lod_xml.archetype.unknown_4c
    lod_props.archetype_unknown_50 = lod_xml.archetype.unknown_50
    lod_props.archetype_unknown_54 = lod_xml.archetype.unknown_54
    lod_props.archetype_inertia_tensor = lod_xml.archetype.inertia_tensor


def set_group_properties(group_xml: Group, bone: bpy.types.Bone):
    bone.group_properties.name = group_xml.name
    bone.group_properties.glass_window_index = group_xml.glass_window_index
    bone.group_properties.glass_flags = group_xml.glass_flags
    bone.group_properties.strength = group_xml.strength
    bone.group_properties.force_transmission_scale_up = group_xml.force_transmission_scale_up
    bone.group_properties.force_transmission_scale_down = group_xml.force_transmission_scale_down
    bone.group_properties.joint_stiffness = group_xml.joint_stiffness
    bone.group_properties.min_soft_angle_1 = group_xml.min_soft_angle_1
    bone.group_properties.max_soft_angle_1 = group_xml.max_soft_angle_1
    bone.group_properties.max_soft_angle_2 = group_xml.max_soft_angle_2
    bone.group_properties.max_soft_angle_3 = group_xml.max_soft_angle_3
    bone.group_properties.rotation_speed = group_xml.rotation_speed
    bone.group_properties.rotation_strength = group_xml.rotation_strength
    bone.group_properties.restoring_max_torque = group_xml.restoring_max_torque
    bone.group_properties.latch_strength = group_xml.latch_strength
    bone.group_properties.min_damage_force = group_xml.min_damage_force
    bone.group_properties.damage_health = group_xml.damage_health
    bone.group_properties.unk_float_5c = group_xml.unk_float_5c
    bone.group_properties.unk_float_60 = group_xml.unk_float_60
    bone.group_properties.unk_float_64 = group_xml.unk_float_64
    bone.group_properties.unk_float_68 = group_xml.unk_float_68
    bone.group_properties.unk_float_6c = group_xml.unk_float_6c
    bone.group_properties.unk_float_70 = group_xml.unk_float_70
    bone.group_properties.unk_float_74 = group_xml.unk_float_74
    bone.group_properties.unk_float_78 = group_xml.unk_float_78
    bone.group_properties.unk_float_a8 = group_xml.unk_float_a8


def set_veh_window_properties(window_xml: Window, window_obj: bpy.types.Object):
    window_obj.vehicle_window_properties.unk_float_17 = window_xml.unk_float_17
    window_obj.vehicle_window_properties.unk_float_18 = window_xml.unk_float_18
    window_obj.vehicle_window_properties.cracks_texture_tiling = window_xml.cracks_texture_tiling
