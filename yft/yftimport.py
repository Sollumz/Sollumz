import os
import bpy
import numpy as np
from traceback import format_exc
from mathutils import Matrix, Vector
from typing import Optional
from ..tools.blenderhelper import create_empty_object, material_from_image, create_blender_object, remove_number_suffix
from ..tools.meshhelper import create_uv_attr
from ..tools.utils import multiply_homogeneous, get_filename
from ..sollumz_properties import BOUND_TYPES, SollumType, LODLevel, MaterialType, VehiclePaintLayer
from ..sollumz_helper import get_sollumz_materials
from ..sollumz_preferences import get_import_settings
from ..cwxml.fragment import YFT, Fragment, PhysicsLOD, PhysicsGroup, PhysicsChild, Window, Archetype
from ..cwxml.drawable import Drawable, Bone, ShaderGroup, Shader
from ..ydr.ydrimport import shader_item_to_material, create_drawable_skel, apply_rotation_limits, create_light_objs, create_drawable_obj, create_drawable_as_asset, shadergroup_to_materials, add_armature_constraint, create_rigged_drawable_models, create_drawable_models
from ..ybn.ybnimport import create_bound_object, set_bound_properties
from ..ydr.ydrexport import calculate_bone_tag
from .. import logger
from .properties import LODProperties, FragArchetypeProperties, PAINT_LAYER_VALUES
from .yftexport import get_armature_constraint_bone


def import_yft(filepath: str):
    import_settings = get_import_settings()

    yft_xml = YFT.from_xml_file(filepath)

    if import_settings.import_as_asset:
        return create_drawable_as_asset(yft_xml.drawable, yft_xml.name.replace("pack:/", ""), filepath)

    hi_xml = parse_hi_yft(
        filepath) if import_settings.import_with_hi else None

    return create_fragment_obj(yft_xml, filepath,
                               split_by_group=import_settings.split_by_group, hi_xml=hi_xml)


def parse_hi_yft(yft_filepath: str) -> Fragment | None:
    """Parse hi_yft at the provided non_hi yft filepath (if it exists)."""
    yft_dir = os.path.dirname(yft_filepath)
    yft_name = get_filename(yft_filepath)

    hi_path = os.path.join(yft_dir, f"{yft_name}_hi.yft.xml")

    if os.path.exists(hi_path):
        return YFT.from_xml_file(hi_path)
    else:
        logger.warning(
            f"Could not find _hi yft for {os.path.basename(yft_filepath)}! Make sure there is a file named '{os.path.basename(hi_path)}' in the same directory!")


def create_fragment_obj(frag_xml: Fragment, filepath: str, split_by_group: bool = False, hi_xml: Optional[Fragment] = None):
    frag_obj = create_frag_armature(frag_xml)
    set_fragment_properties(frag_xml, frag_obj)

    drawable_obj, materials, hi_materials = create_fragment_drawable(
        frag_xml, frag_obj, filepath, split_by_group, hi_xml)

    create_frag_collisions(frag_xml, frag_obj)

    create_phys_lod(frag_xml, frag_obj)
    set_all_bone_physics_properties(frag_obj.data, frag_xml)

    create_phys_child_meshes(
        frag_xml, frag_obj, drawable_obj, materials, hi_materials, hi_xml)

    if frag_xml.vehicle_glass_windows:
        create_vehicle_windows(frag_xml, frag_obj, materials)

    if frag_xml.lights:
        lights_parent = create_light_objs(frag_xml.lights, frag_obj)
        lights_parent.name = f"{frag_obj.name}.lights"
        lights_parent.parent = frag_obj

    return frag_obj


def create_frag_armature(frag_xml: Fragment):
    """Create the fragment armature along with the bones and rotation limits."""
    name = frag_xml.name.replace("pack:/", "")
    skel = bpy.data.armatures.new(f"{name}.skel")
    frag_obj = create_blender_object(SollumType.FRAGMENT, name, skel)

    create_drawable_skel(frag_xml.drawable.skeleton, frag_obj)
    apply_rotation_limits(frag_xml.drawable.joints.rotation_limits, frag_obj)

    return frag_obj


def create_fragment_drawable(frag_xml: Fragment, frag_obj: bpy.types.Object, filepath: str, split_by_group: bool = False, hi_xml: Optional[Fragment] = None):
    """Create the fragment drawable along with the _hi lods if present. Returns the drawable object, list of materials, and list of hi_materials."""
    drawable_xml = frag_xml.drawable
    materials = shadergroup_to_materials(drawable_xml.shader_group, filepath)
    drawable_obj = create_drawable_obj(
        drawable_xml, filepath, name=f"{frag_obj.name}.mesh", split_by_group=split_by_group, external_armature=frag_obj, materials=materials
    )
    drawable_obj.matrix_basis = drawable_xml.matrix

    hi_materials = []

    if hi_xml is not None:
        hi_materials = create_hi_materials(
            materials, drawable_xml.shader_group, hi_xml.drawable.shader_group, filepath)

        hi_mesh_objs = create_rigged_drawable_models(
            hi_xml.drawable, hi_materials, drawable_obj, frag_obj, split_by_group)

        set_hi_lods(drawable_obj, hi_mesh_objs)

    drawable_obj.parent = frag_obj
    update_mat_paint_layers(frag_obj)

    return drawable_obj, materials, hi_materials


def create_hi_materials(non_hi_materials: list[bpy.types.Material], shader_group: ShaderGroup, hi_shader_group: ShaderGroup, filepath: str):
    """Create the _hi materials. Returns a list with the hi materials and non_hi_materials merged."""
    hi_materials: list[bpy.types.Material] = []

    non_hi_mat_by_shader: dict[Shader, bpy.types.Material] = {}

    for i, shader in enumerate(shader_group.shaders):
        # Pre-hash to avoid hashing multiple times
        non_hi_mat_by_shader[hash(shader)] = non_hi_materials[i]

    for shader in hi_shader_group.shaders:
        # Pre-hash to avoid hashing multiple times
        shader_hash = hash(shader)

        if shader_hash in non_hi_mat_by_shader:
            hi_mat = non_hi_mat_by_shader[shader_hash]
        else:
            hi_mat = shader_item_to_material(shader, hi_shader_group, filepath)

        hi_materials.append(hi_mat)

    return hi_materials


def set_hi_lods(drawable_obj: bpy.types.Object, hi_mesh_objs: list[bpy.types.Object]):
    """Add the hi_meshes to the very high LOD level of each corresponding non_hi_mesh. Deletes all hi_mesh_objs."""
    hi_meshes_by_name: dict[str, bpy.types.Object] = {
        remove_number_suffix(obj.name): obj for obj in hi_mesh_objs}

    for obj in drawable_obj.children:
        if obj.sollum_type != SollumType.DRAWABLE_MODEL:
            continue

        obj_name = remove_number_suffix(obj.name)

        if obj_name not in hi_meshes_by_name:
            continue

        hi_mesh = hi_meshes_by_name[obj_name]
        hi_mesh.data.name = f"{obj_name}_very_high"
        obj.sollumz_lods.set_lod_mesh(LODLevel.VERYHIGH, hi_mesh.data)
        obj.sollumz_lods.set_active_lod(LODLevel.VERYHIGH)

        bpy.data.objects.remove(hi_mesh)

        # In case a .00# suffix got added
        obj.name = obj_name


def update_mat_paint_layers(frag_obj: bpy.types.Object):
    for mat in get_sollumz_materials(frag_obj):
        mat.sollumz_paint_layer = get_mat_paint_layer(mat)


def get_mat_paint_layer(mat: bpy.types.Material):
    """Get material paint layer (i.e Primary, Secondary) based on the value of matDiffuseColor"""
    x = -1
    y = -1
    z = -1
    w = -1

    for node in mat.node_tree.nodes:
        if isinstance(node, bpy.types.ShaderNodeValue) and node.is_sollumz and "matDiffuseColor" in node.name:
            if "x" in node.name:
                x = node.outputs[0].default_value
            elif "y" in node.name:
                y = node.outputs[0].default_value
            elif "z" in node.name:
                z = node.outputs[0].default_value
            elif "w" in node.name:
                w = node.outputs[0].default_value

    for paint_layer, value in PAINT_LAYER_VALUES.items():
        if x == 2 and y == value and z == value and w == 0:
            return paint_layer

    return VehiclePaintLayer.NOT_PAINTABLE


def create_phys_lod(frag_xml: Fragment, frag_obj: bpy.types.Object):
    """Create the Fragment.Physics.LOD1 data-block. (Currently LOD1 is only supported)"""
    lod_xml = frag_xml.physics.lod1

    if not lod_xml.groups:
        return

    lod_props: LODProperties = frag_obj.fragment_properties.lod_properties
    set_lod_properties(lod_xml, lod_props)
    set_archetype_properties(lod_xml.archetype, lod_props.archetype_properties)


def set_all_bone_physics_properties(armature: bpy.types.Armature, frag_xml: Fragment):
    """Set the physics group properties for all bones in the armature."""
    groups_xml: list[PhysicsGroup] = frag_xml.physics.lod1.groups

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

    if bounds_xml is None or not bounds_xml.children:
        return None

    composite_obj = create_empty_object(
        SollumType.BOUND_COMPOSITE, name=f"{frag_obj.name}.col")
    set_bound_properties(bounds_xml, composite_obj)
    composite_obj.parent = frag_obj

    for i, bound_xml in enumerate(bounds_xml.children):
        bound_obj = create_bound_object(bound_xml)
        bound_obj.parent = composite_obj

        bone = find_bound_bone(i, frag_xml)
        if bone is None:
            continue

        bound_obj.name = f"{bone.name}.col"

        if bound_obj.data is not None:
            bound_obj.data.name = bound_obj.name

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


def create_phys_child_meshes(frag_xml: Fragment, frag_obj: bpy.types.Object, drawable_obj: bpy.types.Object, materials: list[bpy.types.Material], hi_materials: Optional[list[bpy.types.Material]] = None, hi_xml: Optional[Fragment] = None):
    """Create all Fragment.Physics.LOD1.Children meshes. (Only LOD1 currently supported)"""
    lod_xml = frag_xml.physics.lod1
    children_xml: list[PhysicsChild] = lod_xml.children
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

        child_objs = create_phys_child_mesh(
            child_xml.drawable, frag_obj, materials, bone_name, drawable_obj)

        if hi_xml is not None and hi_materials is not None:
            hi_children: list[PhysicsChild] = hi_xml.physics.lod1.children
            hi_drawable = hi_children[i].drawable
            create_frag_child_hi_lod(
                bone_name, child_objs, hi_drawable, hi_materials)

    return child_meshes


def create_phys_child_mesh(drawable_xml: Drawable, frag_obj: bpy.types.Object, materials: list[bpy.types.Material], bone_name: str, drawable_obj: bpy.types.Object):
    """Create a single physics child mesh"""
    # There is usually only one drawable model in each frag child
    # child_objs = create_drawable_models(drawable_xml, materials, frag_obj)
    child_objs = create_drawable_models(
        drawable_xml, materials, f"{bone_name}.child")

    for child_obj in child_objs:
        add_armature_constraint(child_obj, frag_obj, bone_name)

        child_obj.sollumz_is_physics_child_mesh = True
        child_obj.parent = drawable_obj

        # Rename the lod meshes
        # for lod in child_obj.sollumz_lods.lods:
        #     if lod.mesh is None:
        #         continue
        #     lod.mesh.name = f"{bone_name}_{SOLLUMZ_UI_NAMES[lod.level].lower().replace(' ', '_')}"

    return child_objs


def create_frag_child_hi_lod(name: str, child_objs: list[bpy.types.Object], hi_drawable: Drawable, hi_materials: list[bpy.types.Material]):
    """Create hi lod for a physics child mesh"""
    child_hi_objs = create_drawable_models(hi_drawable, hi_materials)

    for child_obj, child_hi_obj in zip(child_objs, child_hi_objs):
        child_hi_obj.data.name = f"{name}_very_high"

        child_obj.sollumz_lods.set_lod_mesh(
            LODLevel.VERYHIGH, child_hi_obj.data)
        child_obj.sollumz_lods.set_active_lod(LODLevel.VERYHIGH)

        bpy.data.objects.remove(child_hi_obj)


def create_vehicle_windows(frag_xml: Fragment, frag_obj: bpy.types.Object, materials: list[bpy.types.Material]):
    for window_xml in frag_xml.vehicle_glass_windows:
        window_bone = get_window_bone(
            window_xml, frag_xml, frag_obj.data.bones)
        col_obj = get_window_col(frag_obj, window_bone.name)

        window_name = f"{window_bone.name}_shattermap"

        if col_obj is None:
            logger.warning(
                f"Window with ItemID {window_xml.item_id} has no associated collision! Is the file malformed?")
            continue

        col_obj.child_properties.is_veh_window = True

        window_mat = get_veh_window_material(
            window_xml, frag_xml.drawable, materials)

        if window_mat is not None:
            col_obj.child_properties.window_mat = window_mat

        if window_xml.shattermap:
            shattermap_obj = create_shattermap_obj(
                window_xml, window_name, window_bone.matrix_local.translation)
            shattermap_obj.parent = col_obj

        set_veh_window_properties(window_xml, col_obj)


def get_window_col(frag_obj: bpy.types.Object, bone_name: str) -> Optional[bpy.types.Object]:
    for obj in frag_obj.children_recursive:
        if obj.sollum_type in BOUND_TYPES:
            col_bone = get_armature_constraint_bone(obj, frag_obj)

            if col_bone is not None and col_bone.name == bone_name:
                return obj


def get_veh_window_material(window_xml: Window, drawable_xml: Drawable, materials: list[bpy.types.Material]):
    """Get vehicle window material based on UnkUShort1."""
    # UnkUShort1 indexes the geometry that the window uses.
    # The VehicleGlassWindow uses the same material that the geometry uses.
    geometry_index = window_xml.unk_ushort_1
    return get_geometry_material(drawable_xml, materials, geometry_index)


def create_veh_window_object(frag_obj: bpy.types.Object, window_xml: Window, window_bone: bpy.types.Bone, mesh: bpy.types.Mesh):
    window_obj = bpy.data.objects.new(mesh.name, mesh)
    window_obj.sollum_type = SollumType.SHATTERMAP

    window_obj.location = window_bone.matrix_local.translation
    add_armature_constraint(window_obj, frag_obj,
                            window_bone.name, set_transforms=False)
    set_veh_window_properties(window_xml, window_obj)

    bpy.context.collection.objects.link(window_obj)

    return window_obj


def get_window_bone(window_xml: Window, frag_xml: Fragment, bpy_bones: bpy.types.ArmatureBones) -> bpy.types.Bone:
    """Get bone connected to window based on the bone tag of the physics child associated with the window."""
    children_xml: list[PhysicsChild] = frag_xml.physics.lod1.children

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


def create_shattermap_obj(window_xml: Window, name: str, window_location: Vector):
    try:
        mesh = create_shattermap_mesh(window_xml, name, window_location)
    except:
        logger.error(
            f"Error during creation of vehicle window mesh:\n{format_exc()}")
        return

    shattermap_obj = create_blender_object(SollumType.SHATTERMAP, name, mesh)

    if window_xml.shattermap:
        shattermap_mat = shattermap_to_material(
            window_xml.shattermap, f"{name}_shattermap.bmp")
        mesh.materials.append(shattermap_mat)

    return shattermap_obj


def create_shattermap_mesh(window_xml: Window, name: str, window_location: Vector):
    verts = calculate_window_verts(window_xml)
    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.transform(Matrix.Translation(-window_location))

    uvs = np.array([[0.0, 1.0], [0.0, 0.0], [1.0, 0.0],
                   [1.0, 1.0]], dtype=np.float64)
    create_uv_attr(mesh, uvs)

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
    mat = material_from_image(img, name, "ShatterMap")
    mat.sollum_type = MaterialType.SHATTER_MAP

    return mat


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


def set_lod_properties(lod_xml: PhysicsLOD, lod_props: LODProperties):
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


def set_archetype_properties(arch_xml: Archetype, arch_props: FragArchetypeProperties):
    arch_props.name = arch_xml.name
    arch_props.unknown_48 = arch_xml.unknown_48
    arch_props.unknown_4c = arch_xml.unknown_4c
    arch_props.unknown_50 = arch_xml.unknown_50
    arch_props.unknown_54 = arch_xml.unknown_54
    arch_props.inertia_tensor = arch_xml.inertia_tensor


def set_group_properties(group_xml: PhysicsGroup, bone: bpy.types.Bone):
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
