from copy import copy
from tokenize import group
import bpy
from typing import Optional
from collections import defaultdict
from mathutils import Matrix, Vector

from ..ydr.ydrimport import shadergroup_to_materials

from ..ybn.ybnexport import create_composite_xml, get_scale_to_apply_to_bound
from ..cwxml.bound import Bound
from ..cwxml.fragment import Fragment, PhysicsLOD, Archetype, PhysicsChild, PhysicsGroup, Transform, Physics, BoneTransform, Window
from ..cwxml.drawable import Bone, Drawable, ShaderGroup, VectorShaderParameter
from ..tools.blenderhelper import get_bone_pose_matrix, remove_number_suffix, delete_hierarchy, get_child_of_bone
from ..tools.fragmenthelper import image_to_shattermap
from ..tools.meshhelper import calculate_inertia
from ..tools.utils import prop_array_to_vector, reshape_mat_4x3, vector_inv, reshape_mat_3x4
from ..sollumz_helper import get_parent_inverse, get_sollumz_materials
from ..sollumz_properties import BOUND_TYPES, SollumType, MaterialType, LODLevel, VehiclePaintLayer
from ..sollumz_preferences import get_export_settings
from ..ybn.ybnexport import has_col_mats, bound_geom_has_mats
from ..ydr.ydrexport import create_drawable_xml, write_embedded_textures, get_bone_index, create_model_xml, append_model_xml, set_drawable_xml_extents
from ..ydr.lights import create_xml_lights
from .. import logger
from .properties import LODProperties, FragArchetypeProperties, GroupProperties, PAINT_LAYER_VALUES


def export_yft(frag_obj: bpy.types.Object, filepath: str):
    export_settings = get_export_settings()
    frag_xml = create_fragment_xml(frag_obj, export_settings.auto_calculate_inertia,
                                   export_settings.auto_calculate_volume, export_settings.auto_calculate_bone_tag, export_settings.apply_transforms)

    if frag_xml is None:
        return

    if export_settings.export_non_hi:
        frag_xml.write_xml(filepath)
        write_embedded_textures(frag_obj, filepath)

    if export_settings.export_hi and has_hi_lods(frag_obj):
        hi_filepath = filepath.replace(".yft.xml", "_hi.yft.xml")

        hi_frag_xml = create_hi_frag_xml(
            frag_obj, frag_xml, export_settings.auto_calculate_bone_tag, export_settings.apply_transforms)
        hi_frag_xml.write_xml(hi_filepath)

        write_embedded_textures(frag_obj, hi_filepath)
        logger.info(f"Exported Very High LODs to '{hi_filepath}'")


def create_fragment_xml(frag_obj: bpy.types.Object, auto_calc_inertia: bool = False, auto_calc_volume: bool = False, auto_calc_bone_tag: bool = False, apply_transforms: bool = False):
    """Create an XML parsable Fragment object. Returns the XML object and the hi XML object (if hi lods are present)."""
    frag_xml = Fragment()
    frag_xml.name = f"pack:/{remove_number_suffix(frag_obj.name)}"

    if frag_obj.type != "ARMATURE":
        logger.warning(
            f"Failed to create Fragment XML: {frag_obj.name} must be an armature with a skeleton!")
        return

    set_frag_xml_properties(frag_obj, frag_xml)

    materials = get_sollumz_materials(frag_obj)
    drawable_xml = create_frag_drawable_xml(
        frag_obj, auto_calc_bone_tag, materials, apply_transforms)

    if drawable_xml is None:
        logger.warning(
            f"Failed to create Fragment XML: {frag_obj.name} has no Drawable!")
        return

    original_pose = frag_obj.data.pose_position
    frag_obj.data.pose_position = "REST"

    set_paint_layer_shader_params(materials, drawable_xml.shader_group)

    frag_xml.bounding_sphere_center = drawable_xml.bounding_sphere_center
    frag_xml.bounding_sphere_radius = drawable_xml.bounding_sphere_radius

    frag_xml.drawable = drawable_xml

    if frag_obj.data.bones:
        create_bone_transforms_xml(frag_xml)

    # Physics data doesn't do anything if no collisions are present and will cause crashes
    if frag_has_collisions(frag_obj) and frag_obj.data.bones:
        create_frag_physics_xml(
            frag_obj, frag_xml, materials, auto_calc_inertia, auto_calc_volume)
        create_vehicle_windows_xml(frag_obj, frag_xml, materials)
    else:
        frag_xml.physics = None

    frag_xml.lights = create_xml_lights(frag_obj, frag_obj)

    frag_obj.data.pose_position = original_pose

    return frag_xml


def create_frag_drawable_xml(frag_obj: bpy.types.Object, auto_calc_bone_tag: bool, materials: list[bpy.types.Material], apply_transforms: bool = False):
    for obj in frag_obj.children:
        if obj.sollum_type != SollumType.DRAWABLE:
            continue

        drawable_xml = create_drawable_xml(
            obj, auto_calc_bone_tag=auto_calc_bone_tag, materials=materials, armature_obj=frag_obj, apply_transforms=apply_transforms)
        drawable_xml.name = "skel"

        return drawable_xml


def set_paint_layer_shader_params(materials: list[bpy.types.Material], shader_group: ShaderGroup):
    """Set matDiffuseColor shader params based off of paint layer selection (expects materials to be ordered by shader)"""
    for i, mat in enumerate(materials):
        paint_layer = mat.sollumz_paint_layer
        if paint_layer == VehiclePaintLayer.NOT_PAINTABLE:
            continue

        for param in shader_group.shaders[i].parameters:
            if not isinstance(param, VectorShaderParameter) or param.name != "matDiffuseColor":
                continue

            value = PAINT_LAYER_VALUES[paint_layer]
            param.x, param.y, param.z, param.w = (2, value, value, 0)


def create_hi_frag_xml(frag_obj: bpy.types.Object, frag_xml: Fragment, auto_calc_bone_tag: bool = False, apply_transforms: bool = False):
    hi_obj = frag_obj.copy()
    hi_obj.name = f"{remove_number_suffix(hi_obj.name)}_hi"
    drawable_obj = None

    bpy.context.collection.objects.link(hi_obj)

    for child in frag_obj.children:
        if child.sollum_type == SollumType.DRAWABLE:
            drawable_obj = copy_hierarchy(child, hi_obj)
            drawable_obj.parent = hi_obj
            break

    if drawable_obj is not None:
        remove_non_hi_lods(drawable_obj)

    materials = get_sollumz_materials(hi_obj)
    hi_drawable = create_frag_drawable_xml(
        hi_obj, auto_calc_bone_tag, materials, apply_transforms)

    hi_frag_xml = Fragment()
    hi_frag_xml.__dict__ = frag_xml.__dict__.copy()
    hi_frag_xml.drawable = hi_drawable
    hi_frag_xml.vehicle_glass_windows = None

    delete_hierarchy(hi_obj)

    return hi_frag_xml


def copy_hierarchy(obj: bpy.types.Object, armature_obj: bpy.types.Object):
    obj_copy = obj.copy()

    bpy.context.collection.objects.link(obj_copy)

    for constraint in obj_copy.constraints:
        if constraint.type != "ARMATURE":
            continue

        for constraint_target in constraint.targets:
            constraint_target.target = armature_obj

    for modifier in obj_copy.modifiers:
        if modifier.type != "ARMATURE":
            continue

        modifier.object = armature_obj

    for child in obj.children:
        child_copy = copy_hierarchy(child, armature_obj)
        child_copy.parent = obj_copy

    return obj_copy


def remove_non_hi_lods(drawable_obj: bpy.types.Object):
    for model_obj in drawable_obj.children:
        if model_obj.sollum_type != SollumType.DRAWABLE_MODEL:
            continue

        very_high_lod = model_obj.sollumz_lods.get_lod(LODLevel.VERYHIGH)

        if very_high_lod is None or very_high_lod.mesh is None:
            bpy.data.objects.remove(model_obj)
            continue

        lod_props = model_obj.sollumz_lods

        lod_props.set_lod_mesh(LODLevel.HIGH, very_high_lod.mesh)
        lod_props.set_active_lod(LODLevel.HIGH)

        for lod in lod_props.lods:
            if lod.level != LODLevel.HIGH and lod.mesh is not None:
                lod.mesh = None


def copy_phys_xml(phys_xml: Physics, lod_props: LODProperties):
    new_phys_xml = Physics()
    lod_xml = PhysicsLOD("LOD1")
    new_phys_xml.lod1 = lod_xml
    new_phys_xml.lod2 = None
    new_phys_xml.lod3 = None

    lod_xml.archetype = phys_xml.lod1.archetype
    lod_xml.groups = phys_xml.lod1.groups
    lod_xml.archetype2 = None

    set_lod_xml_properties(lod_props, lod_xml)

    return new_phys_xml


def has_hi_lods(frag_obj: bpy.types.Object):
    for child in frag_obj.children_recursive:
        if child.sollum_type != SollumType.DRAWABLE_MODEL and not child.sollumz_is_physics_child_mesh:
            continue

        for lod in child.sollumz_lods.lods:
            if lod.level == LODLevel.VERYHIGH and lod.mesh is not None:
                return True

    return False


def sort_cols_and_children(lod_xml: PhysicsLOD):
    children_by_group: dict[int, list[int]] = defaultdict(list)

    bounds = lod_xml.archetype.bounds.children
    children = lod_xml.children

    if not bounds or not children:
        return

    for i, child in enumerate(children):
        children_by_group[child.group_index].append(i)

    children_by_group = dict(sorted(children_by_group.items()))

    # Map old indices to new ones
    indices: dict[int, int] = {}
    sorted_children: list[PhysicsChild] = []

    for group_index, children_indices in children_by_group.items():
        for child_index in children_indices:
            new_child_index = len(sorted_children)
            indices[child_index] = new_child_index

            sorted_children.append(children[child_index])

    lod_xml.children = sorted_children
    # Apply sorting to collisions
    sorted_collisions: list[Bound] = [None] * len(indices)
    sorted_transforms: list[Transform] = [None] * len(indices)

    for old_index, new_index in indices.items():
        sorted_collisions[new_index] = bounds[old_index]
        sorted_transforms[new_index] = lod_xml.transforms[old_index]

    lod_xml.archetype.bounds.children = sorted_collisions
    lod_xml.transforms = sorted_transforms


def frag_has_collisions(frag_obj: bpy.types.Object):
    return any(child.sollum_type == SollumType.BOUND_COMPOSITE for child in frag_obj.children)


def create_frag_physics_xml(frag_obj: bpy.types.Object, frag_xml: Fragment, materials: list[bpy.types.Material], auto_calc_inertia: bool = False, auto_calc_volume: bool = False):
    lod_props: LODProperties = frag_obj.fragment_properties.lod_properties
    drawable_xml = frag_xml.drawable

    lod_xml = create_phys_lod_xml(frag_xml.physics, lod_props)
    arch_xml = create_archetype_xml(lod_xml, frag_obj)
    create_collision_xml(frag_obj, arch_xml,
                         auto_calc_inertia, auto_calc_volume)

    create_phys_xml_groups(frag_obj, lod_xml)
    create_phys_child_xmls(
        frag_obj, lod_xml, drawable_xml.skeleton.bones, materials)

    set_arch_mass_inertia(frag_obj, arch_xml,
                          lod_xml.children, auto_calc_inertia)
    calculate_group_masses(lod_xml)
    calculate_child_drawable_matrices(frag_xml)

    sort_cols_and_children(lod_xml)


def create_phys_lod_xml(phys_xml: Physics, lod_props: LODProperties):
    set_lod_xml_properties(lod_props, phys_xml.lod1)
    phys_xml.lod2 = None
    phys_xml.lod3 = None

    return phys_xml.lod1


def create_archetype_xml(lod_xml: PhysicsLOD, frag_obj: bpy.types.Object):
    archetype_props: FragArchetypeProperties = frag_obj.fragment_properties.lod_properties.archetype_properties

    set_archetype_xml_properties(
        archetype_props, lod_xml.archetype, remove_number_suffix(frag_obj.name))
    lod_xml.archetype2 = None

    return lod_xml.archetype


def set_arch_mass_inertia(frag_obj: bpy.types.Object, arch_xml: Archetype, phys_children: list[PhysicsChild], auto_calc_inertia: bool = False):
    """Set archetype mass based on children mass. Expects physics children and collisions to exist."""
    mass = calculate_arch_mass(phys_children)
    arch_xml.mass = mass
    arch_xml.mass_inv = (1 / mass) if mass != 0 else 0

    archetype_props: FragArchetypeProperties = frag_obj.fragment_properties.lod_properties.archetype_properties

    if auto_calc_inertia:
        inertia = calculate_inertia(
            arch_xml.bounds.box_min, arch_xml.bounds.box_max) * mass
    else:
        inertia = prop_array_to_vector(archetype_props.inertia_tensor)

    arch_xml.inertia_tensor = inertia
    arch_xml.inertia_tensor_inv = vector_inv(inertia)


def calculate_arch_mass(phys_children: list[PhysicsChild]) -> float:
    """Calculate archetype mass based on mass of physics children."""
    total_mass = 0

    for child_xml in phys_children:
        total_mass += child_xml.pristine_mass

    return total_mass


def create_collision_xml(frag_obj: bpy.types.Object, arch_xml: Archetype, auto_calc_inertia: bool = False, auto_calc_volume: bool = False):
    for child in frag_obj.children:
        if child.sollum_type != SollumType.BOUND_COMPOSITE:
            continue

        composite_xml = create_composite_xml(
            child, auto_calc_inertia, auto_calc_volume)
        arch_xml.bounds = composite_xml

        composite_xml.unk_type = 2
        composite_xml.inertia = Vector((1, 1, 1))

        for bound_xml in composite_xml.children:
            bound_xml.unk_type = 2

        return composite_xml


def create_phys_xml_groups(frag_obj: bpy.types.Object, lod_xml: PhysicsLOD):
    group_ind_by_name: dict[str, int] = {}
    groups_by_bone: dict[int, list[PhysicsGroup]] = defaultdict(list)

    for bone in frag_obj.data.bones:
        if not bone.sollumz_use_physics:
            continue

        if not does_bone_have_collision(bone.name, frag_obj):
            logger.warning(
                f"Bone '{bone.name}' has physics enabled, but no associated collision! A collision must be linked to the bone for physics to work.")
            continue

        group_xml = PhysicsGroup()
        group_xml.name = remove_number_suffix(bone.name)
        bone_index = get_bone_index(frag_obj.data, bone)

        groups_by_bone[bone_index].append(group_xml)
        set_group_xml_properties(bone.group_properties, group_xml)

    # Sort by bone index
    groups_by_bone = dict(sorted(groups_by_bone.items()))

    for groups in groups_by_bone.values():
        for group_xml in groups:
            i = len(group_ind_by_name)

            group_ind_by_name[group_xml.name] = i

    def get_group_parent_index(group_bone: bpy.types.Bone):
        if group_bone.parent is None or group_bone.parent.name not in group_ind_by_name:
            return 255

        if not group_bone.parent.sollumz_use_physics:
            return get_group_parent_index(group_bone.parent)

        return group_ind_by_name[group_bone.parent.name]

    # Set group parent indices
    for bone_index, groups in groups_by_bone.items():
        parent_index = get_group_parent_index(frag_obj.data.bones[bone_index])

        for group_xml in groups:
            group_xml.parent_index = parent_index

            group_ind_by_name[group_xml.name] = len(lod_xml.groups)

            lod_xml.groups.append(group_xml)

    return lod_xml.groups


def does_bone_have_collision(bone_name: str, frag_obj: bpy.types.Object):
    col_objs = [
        obj for obj in frag_obj.children_recursive if obj.sollum_type in BOUND_TYPES]

    for obj in col_objs:
        bone = get_child_of_bone(obj)

        if bone is not None and bone.name == bone_name:
            return True

    return False


def calculate_group_masses(lod_xml: PhysicsLOD):
    """Calculate the mass of all groups in ``lod_xml`` based on child masses. Expects physics children to exist."""
    for child in lod_xml.children:
        lod_xml.groups[child.group_index].mass += child.pristine_mass


def create_phys_child_xmls(frag_obj: bpy.types.Object, lod_xml: PhysicsLOD, bones_xml: list[Bone], materials: list[bpy.types.Material]):
    child_meshes = get_child_meshes(frag_obj)
    child_cols = get_child_cols(frag_obj)

    for bone_name, objs in child_cols.items():
        for obj in objs:
            child_index = len(lod_xml.children)

            bone: bpy.types.Bone = frag_obj.data.bones.get(bone_name)
            bone_index = get_bone_index(frag_obj.data, bone) or 0

            child_xml = PhysicsChild()
            child_xml.group_index = get_bone_group_index(lod_xml, bone_name)
            child_xml.pristine_mass = obj.child_properties.mass
            child_xml.damaged_mass = child_xml.pristine_mass
            child_xml.bone_tag = bones_xml[bone_index].tag

            inertia_tensor = get_child_inertia(
                lod_xml.archetype, child_xml, child_index)
            child_xml.inertia_tensor = inertia_tensor

            mesh_objs = None
            if bone_name in child_meshes:
                mesh_objs = child_meshes[bone_name]

            bound_xml = lod_xml.archetype.bounds.children[child_index]
            composite_matrix = bound_xml.composite_transform

            create_phys_child_drawable(child_xml, materials, mesh_objs)

            create_child_transforms_xml(composite_matrix, lod_xml)

            lod_xml.children.append(child_xml)


def get_child_inertia(arch_xml: Archetype, child_xml: PhysicsChild, child_index: int):
    if not arch_xml.bounds or child_index >= len(arch_xml.bounds.children):
        return Vector()

    bound_xml = arch_xml.bounds.children[child_index]
    inertia = bound_xml.inertia * child_xml.pristine_mass
    return Vector((inertia.x, inertia.y, inertia.z, bound_xml.volume * child_xml.pristine_mass))


def get_child_cols(frag_obj: bpy.types.Object):
    """Get collisions that are linked to a child. Returns a dict mapping each collision to a bone name."""
    child_cols_by_bone: dict[str, list[bpy.types.Object]] = defaultdict(list)

    for composite_obj in frag_obj.children:
        if composite_obj.sollum_type != SollumType.BOUND_COMPOSITE:
            continue

        for bound_obj in composite_obj.children:
            if not bound_obj.sollum_type in BOUND_TYPES:
                continue

            if (bound_obj.type == "MESH" and not has_col_mats(bound_obj)) or (bound_obj.type == "EMPTY" and not bound_geom_has_mats(bound_obj)):
                continue

            bone = get_child_of_bone(bound_obj)

            if bone is None or not bone.sollumz_use_physics:
                continue

            child_cols_by_bone[bone.name].append(bound_obj)

    return child_cols_by_bone


def get_child_meshes(frag_obj: bpy.types.Object):
    """Get meshes that are linked to a child. Returns a dict mapping child meshes to bone name."""
    child_meshes_by_bone: dict[str, list[bpy.types.Object]] = defaultdict(list)

    for drawable_obj in frag_obj.children:
        if drawable_obj.sollum_type != SollumType.DRAWABLE:
            continue

        for model_obj in drawable_obj.children:
            if model_obj.sollum_type != SollumType.DRAWABLE_MODEL or not model_obj.sollumz_is_physics_child_mesh:
                continue

            bone = get_child_of_bone(model_obj)

            if bone is None or not bone.sollumz_use_physics:
                continue

            child_meshes_by_bone[bone.name].append(model_obj)

    return child_meshes_by_bone


def get_bone_group_index(lod_xml: PhysicsLOD, bone_name: str):
    """Get index of group named ``bone_name`` (expects groups to have already been created in ``lod_xml``)."""
    for i, group in enumerate(lod_xml.groups):
        if group.name == bone_name:
            return i

    return -1


def create_child_mat_arrays(children: list[PhysicsChild]):
    """Create the matrix arrays for each child. This appears to be in the first child of multiple children that
    share the same group. Each matrix in the array is just the matrix for each child in that group."""
    group_inds = set(child.group_index for child in children)

    for i in group_inds:
        group_children = [
            child for child in children if child.group_index == i]

        if len(group_children) <= 1:
            continue

        first = group_children[0]

        for child in group_children[1:]:
            first.drawable.matrices.append(child.drawable.matrix)


def create_phys_child_drawable(child_xml: PhysicsChild, materials: list[bpy.types.Object], mesh_objs: Optional[list[bpy.types.Object]] = None):
    drawable_xml = child_xml.drawable
    drawable_xml.shader_group = None
    drawable_xml.skeleton = None
    drawable_xml.joints = None

    if not mesh_objs:
        return drawable_xml

    for obj in mesh_objs:
        scale = get_scale_to_apply_to_bound(obj)
        transforms_to_apply = Matrix.Diagonal(scale).to_4x4()

        for lod in obj.sollumz_lods.lods:
            if lod.mesh is None or lod.level == LODLevel.VERYHIGH:
                continue

            model_xml = create_model_xml(
                obj, lod.level, materials, transforms_to_apply=transforms_to_apply)
            model_xml.bone_index = 0
            append_model_xml(drawable_xml, model_xml, lod.level)

    set_drawable_xml_extents(drawable_xml)

    return drawable_xml


def create_vehicle_windows_xml(frag_obj: bpy.types.Object, frag_xml: Fragment, materials: list[bpy.types.Material]):
    """Create all the vehicle windows for ``frag_xml``. Must be ran after the drawable and physics children have been created."""
    child_id_by_bone_tag: dict[str, int] = {
        c.bone_tag: i for i, c in enumerate(frag_xml.physics.lod1.children)}
    mat_ind_by_name: dict[str, int] = {
        mat.name: i for i, mat in enumerate(materials)}
    bones = frag_xml.drawable.skeleton.bones

    for obj in frag_obj.children_recursive:
        if not obj.child_properties.is_veh_window:
            continue

        bone = get_child_of_bone(obj)

        if bone is None or not bone.sollumz_use_physics:
            logger.warning(
                f"Vehicle window '{obj.name}' is not attached to a bone, or the attached bone does not have physics enabled! Attach the bone via an armature constraint.")
            continue

        bone_index = get_bone_index(frag_obj.data, bone)
        window_xml = Window()

        bone_tag = bones[bone_index].tag

        if bone_tag not in child_id_by_bone_tag:
            logger.warning(
                f"No physics child for the vehicle window '{obj.name}'!")
            continue

        window_xml.item_id = child_id_by_bone_tag[bone_tag]
        window_mat = obj.child_properties.window_mat

        if window_mat is None:
            logger.warning(
                f"Vehicle window '{obj.name}' has no material with the vehicle_vehglass shader!")
            continue

        if window_mat.name not in mat_ind_by_name:
            logger.warning(
                f"Vehicle window '{obj.name}' is using a vehicle_vehglass material '{window_mat.name}' that is not used in the Drawable! This material should be added to the mesh object attached to the bone '{bone.name}'.")
            continue

        set_veh_window_xml_properties(window_xml, obj)

        create_window_shattermap(obj, window_xml)

        shader_index = mat_ind_by_name[window_mat.name]
        window_xml.unk_ushort_1 = get_window_geometry_index(
            frag_xml.drawable, shader_index)

        frag_xml.vehicle_glass_windows.append(window_xml)

    frag_xml.vehicle_glass_windows = sorted(
        frag_xml.vehicle_glass_windows, key=lambda w: w.item_id)


def create_window_shattermap(col_obj: bpy.types.Object, window_xml: Window):
    """Create window shattermap (if it exists) and calculate projection"""
    shattermap_obj = get_shattermap_obj(col_obj)

    if shattermap_obj is None:
        return

    shattermap_img = find_shattermap_image(shattermap_obj)

    if shattermap_img is not None:
        pose_matrix = get_bone_pose_matrix(col_obj)

        window_xml.shattermap = image_to_shattermap(shattermap_img)
        window_xml.projection_matrix = calculate_shattermap_projection(
            shattermap_obj, shattermap_img, pose_matrix)


def set_veh_window_xml_properties(window_xml: Window, window_obj: bpy.types.Object):
    window_xml.unk_float_17 = window_obj.vehicle_window_properties.unk_float_17
    window_xml.unk_float_18 = window_obj.vehicle_window_properties.unk_float_18
    window_xml.cracks_texture_tiling = window_obj.vehicle_window_properties.cracks_texture_tiling


def calculate_shattermap_projection(obj: bpy.types.Object, img: bpy.types.Image, bone_matrix: Matrix):
    mesh = obj.data

    v1 = Vector()
    v2 = Vector()
    v3 = Vector()

    # Get three corner vectors
    for loop in mesh.loops:
        uv = mesh.uv_layers[0].data[loop.index].uv
        vert_pos = mesh.vertices[loop.vertex_index].co

        if uv.x == 0 and uv.y == 1:
            v1 = vert_pos
        elif uv.x == 1 and uv.y == 1:
            v2 = vert_pos
        elif uv.x == 0 and uv.y == 0:
            v3 = vert_pos

    resx = img.size[0]
    resy = img.size[1]
    thickness = 0.01

    edge1 = (v2 - v1) / resx
    edge2 = (v3 - v1) / resy
    edge3 = edge1.normalized().cross(edge2.normalized()) * thickness

    matrix = Matrix()
    matrix[0] = edge1.x, edge2.x, edge3.x, v1.x
    matrix[1] = edge1.y, edge2.y, edge3.y, v1.y
    matrix[2] = edge1.z, edge2.z, edge3.z, v1.z

    # Create projection matrix relative to bone
    mat = bone_matrix.copy()
    parent_inverse = get_parent_inverse(obj)
    mat.translation = Vector()
    matrix = mat.inverted() @ parent_inverse @ obj.matrix_world @ matrix

    try:
        matrix.invert()
    except ValueError:
        logger.warning(
            f"Failed to create shattermap projection matrix for '{obj.name}'. Ensure the object is a flat plane with 4 vertices.")
        return Matrix()

    return matrix


def get_shattermap_obj(col_obj: bpy.types.Object) -> Optional[bpy.types.Object]:
    for child in col_obj.children:
        if child.sollum_type == SollumType.SHATTERMAP:
            return child


def find_shattermap_image(obj: bpy.types.Object) -> Optional[bpy.types.Image]:
    """Find shattermap material on ``obj`` and get the image attached to the base color node."""
    for mat in obj.data.materials:
        if mat.sollum_type != MaterialType.SHATTER_MAP:
            continue

        for node in mat.node_tree.nodes:
            if not isinstance(node, bpy.types.ShaderNodeTexImage):
                continue

            return node.image


def get_window_material(obj: bpy.types.Object) -> Optional[bpy.types.Material]:
    """Get first material with a vehicle_vehglass shader."""
    for mat in obj.data.materials:
        if "vehicle_vehglass" in mat.shader_properties.name:
            return mat


def get_window_geometry_index(drawable_xml: Drawable, window_shader_index: int):
    """Get index of the geometry using the window material."""
    for dmodel_xml in drawable_xml.drawable_models_high:
        for (index, geometry) in enumerate(dmodel_xml.geometries):
            if geometry.shader_index != window_shader_index:
                continue

            return index

    return 0


def create_child_transforms_xml(child_matrix: Matrix, lod_xml: PhysicsLOD):
    offset = lod_xml.position_offset

    matrix = child_matrix.copy()
    a = matrix[3][0] - offset.x
    b = matrix[3][1] - offset.y
    c = matrix[3][2] - offset.z
    matrix[3][0] = a
    matrix[3][1] = b
    matrix[3][2] = c

    transform_xml = Transform("Item", matrix)
    lod_xml.transforms.append(transform_xml)

    return transform_xml


def create_bone_transforms_xml(frag_xml: Fragment):
    def get_bone_transforms(bone: Bone):
        return Matrix.LocRotScale(bone.translation, bone.rotation, bone.scale)

    bones: list[Bone] = frag_xml.drawable.skeleton.bones

    for bone in bones:

        transforms = get_bone_transforms(bone)

        if bone.parent_index != -1:
            parent_transforms = frag_xml.bones_transforms[bone.parent_index].value
            transforms = parent_transforms @ transforms

        # Reshape to 3x4
        transforms_reshaped = reshape_mat_3x4(transforms)

        frag_xml.bones_transforms.append(
            BoneTransform("Item", transforms_reshaped))


def calculate_child_drawable_matrices(frag_xml: Fragment):
    """Calculate the matrix for each physics child Drawable from bone transforms
    and composite transforms. Each matrix represents the transformation of the
    child relative to the bone."""
    bone_transforms = frag_xml.bones_transforms
    bones = frag_xml.drawable.skeleton.bones
    lod_xml = frag_xml.physics.lod1
    collisions = lod_xml.archetype.bounds.children

    bone_transform_by_tag: dict[str, Matrix] = {
        b.tag: bone_transforms[i].value for i, b in enumerate(bones)}

    for i, child in enumerate(lod_xml.children):
        bone_transform = bone_transform_by_tag[child.bone_tag]
        col = collisions[i]

        bone_inv = bone_transform.to_4x4().inverted()

        matrix = col.composite_transform @ bone_inv.transposed()
        child.drawable.matrix = reshape_mat_4x3(matrix)

    create_child_mat_arrays(lod_xml.children)


def set_lod_xml_properties(lod_props: LODProperties, lod_xml: PhysicsLOD):
    lod_xml.unknown_14 = lod_props.unknown_14
    lod_xml.unknown_18 = lod_props.unknown_18
    lod_xml.unknown_1c = lod_props.unknown_1c
    pos_offset = prop_array_to_vector(lod_props.position_offset)
    lod_xml.position_offset = pos_offset
    lod_xml.unknown_40 = prop_array_to_vector(lod_props.unknown_40)
    lod_xml.unknown_50 = prop_array_to_vector(lod_props.unknown_50)
    lod_xml.damping_linear_c = prop_array_to_vector(
        lod_props.damping_linear_c)
    lod_xml.damping_linear_v = prop_array_to_vector(
        lod_props.damping_linear_v)
    lod_xml.damping_linear_v2 = prop_array_to_vector(
        lod_props.damping_linear_v2)
    lod_xml.damping_angular_c = prop_array_to_vector(
        lod_props.damping_angular_c)
    lod_xml.damping_angular_v = prop_array_to_vector(
        lod_props.damping_angular_v)
    lod_xml.damping_angular_v2 = prop_array_to_vector(
        lod_props.damping_angular_v2)


def set_archetype_xml_properties(archetype_props: FragArchetypeProperties, arch_xml: Archetype, frag_name: str):
    arch_xml.name = frag_name
    arch_xml.unknown_48 = archetype_props.unknown_48
    arch_xml.unknown_4c = archetype_props.unknown_4c
    arch_xml.unknown_50 = archetype_props.unknown_50
    arch_xml.unknown_54 = archetype_props.unknown_54


def set_group_xml_properties(group_props: GroupProperties, group_xml: PhysicsGroup):
    group_xml.glass_window_index = group_props.glass_window_index
    group_xml.glass_flags = group_props.glass_flags
    group_xml.strength = group_props.strength
    group_xml.force_transmission_scale_up = group_props.force_transmission_scale_up
    group_xml.force_transmission_scale_down = group_props.force_transmission_scale_down
    group_xml.joint_stiffness = group_props.joint_stiffness
    group_xml.min_soft_angle_1 = group_props.min_soft_angle_1
    group_xml.max_soft_angle_1 = group_props.max_soft_angle_1
    group_xml.max_soft_angle_2 = group_props.max_soft_angle_2
    group_xml.max_soft_angle_3 = group_props.max_soft_angle_3
    group_xml.rotation_speed = group_props.rotation_speed
    group_xml.rotation_strength = group_props.rotation_strength
    group_xml.restoring_max_torque = group_props.restoring_max_torque
    group_xml.latch_strength = group_props.latch_strength
    group_xml.min_damage_force = group_props.min_damage_force
    group_xml.damage_health = group_props.damage_health
    group_xml.unk_float_5c = group_props.unk_float_5c
    group_xml.unk_float_60 = group_props.unk_float_60
    group_xml.unk_float_64 = group_props.unk_float_64
    group_xml.unk_float_68 = group_props.unk_float_68
    group_xml.unk_float_6c = group_props.unk_float_6c
    group_xml.unk_float_70 = group_props.unk_float_70
    group_xml.unk_float_74 = group_props.unk_float_74
    group_xml.unk_float_78 = group_props.unk_float_78
    group_xml.unk_float_a8 = group_props.unk_float_a8


def set_frag_xml_properties(frag_obj: bpy.types.Object, frag_xml: Fragment):
    frag_xml.unknown_b0 = frag_obj.fragment_properties.unk_b0
    frag_xml.unknown_b8 = frag_obj.fragment_properties.unk_b8
    frag_xml.unknown_bc = frag_obj.fragment_properties.unk_bc
    frag_xml.unknown_c0 = frag_obj.fragment_properties.unk_c0
    frag_xml.unknown_c4 = frag_obj.fragment_properties.unk_c4
    frag_xml.unknown_cc = frag_obj.fragment_properties.unk_cc
    frag_xml.gravity_factor = frag_obj.fragment_properties.gravity_factor
    frag_xml.buoyancy_factor = frag_obj.fragment_properties.buoyancy_factor
