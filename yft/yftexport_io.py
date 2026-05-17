import bpy
from bpy.types import (
    Object,
    Material,
    Image,
    Bone,
    ShaderNodeTexImage,
)
from bpy_extras.mesh_utils import mesh_linked_triangles
import numpy as np
from sys import float_info
from typing import Optional
from collections import defaultdict
from itertools import combinations, zip_longest
from dataclasses import replace
from mathutils import Vector, Matrix

from szio.gta5 import (
    create_asset_fragment,
    create_asset_drawable,
    create_asset_bound,
    is_provider_available,
    AssetFormat,
    AssetVersion,
    AssetTarget,
    LodLevel as IOLodLevel,
    BoundType,
    AssetBound,
    AssetDrawable,
    AssetFragment,
    FragmentTemplateAsset,
    PhysLod,
    PhysLodGroup,
    PhysArchetype,
    PhysChild,
    PhysGroup,
    MatrixSet,
    SkelBone,
    Skeleton,
    Model,
    EmbeddedTexture,
    FragGlassWindow,
    FragVehicleWindow,
)
from ..tools.blenderhelper import remove_number_suffix, get_evaluated_obj, get_child_of_bone
from ..tools.meshhelper import flip_uvs
from ..tools.utils import vector_inv, reshape_mat_3x4
from ..sollumz_helper import get_sollumz_materials, GetSollumzMaterialsMode, get_parent_inverse
from ..sollumz_properties import BOUND_TYPES, SollumType, MaterialType, LODLevel
from ..ybn.ybnexport_io import create_bound_composite_asset, has_collision_materials, has_bvh_collision_materials
from ..ybn.ybnexport import get_scale_to_apply_to_bound
from ..ydr.ydrexport_io import (
    create_drawable_asset,
    create_model,
    get_bone_index,
)
from ..ydr.lights_io import export_lights
from ..ydr.cloth_env_io import cloth_env_export, cloth_env_find_mesh_objects

from ..iecontext import export_context, ExportBundle
from .. import logger

from .properties import (
    LODProperties,
    FragArchetypeProperties,
    GroupFlagBit,
    GroupProperties,
    get_glass_type_index,
)
from .yftexport import locate_fragment_objects, FragmentObjects


def export_yft(obj: Object) -> ExportBundle:
    embedded_tex = []
    frag, hi_frag = create_fragment_asset(obj, out_embedded_textures=embedded_tex)
    return export_context().make_bundle(frag, ("_hi", hi_frag), extra_files=[t.data for t in embedded_tex])


def create_fragment_asset(
    frag_obj: Object,
    out_embedded_textures: list[EmbeddedTexture] | None = None,
) -> tuple[AssetFragment | None, AssetFragment | None]:
    """Create the export asset for a fragment. Returns a tuple with non-hi and hi (optional) assets. If non-hi is None,
    the export failed.
    """
    frag_objs = locate_fragment_objects(frag_obj)
    if frag_objs is None:
        return None, None

    return create_fragment_asset_core(
        frag_objs, export_context().settings.apply_transforms, out_embedded_textures
    )


def create_fragment_asset_core(
    frag_objs: FragmentObjects,
    apply_transforms: bool = False,
    out_embedded_textures: list[EmbeddedTexture] | None = None,
) -> tuple[AssetFragment | None, AssetFragment | None]:
    """Create an XML parsable Fragment object. Returns the XML object and the hi XML object (if hi lods are present)."""
    frag_obj = frag_objs.fragment

    has_hi = has_hi_lods(frag_obj)

    materials = get_sollumz_materials(frag_obj, GetSollumzMaterialsMode.BASE)
    hi_materials = get_sollumz_materials(frag_obj, GetSollumzMaterialsMode.HI) if has_hi else None

    targets = export_context().settings.targets

    # Check if we going to automatically generate vehicle windows
    has_vehglass_material = any("vehicle_vehglass" in mat.shader_properties.name for mat in materials)
    has_manual_shattermaps = (
        any(bound.child_properties.is_veh_window for bound in frag_objs.composite.children)
        if frag_objs.composite
        else False
    )
    gen_vehicle_windows = has_vehglass_material and not has_manual_shattermaps
    # If we are generating vehicle windows, we need a NATIVE asset as the CWXML backend does not support it directly
    extra_targets = (
        (AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),)
        if gen_vehicle_windows and all(t.format == AssetFormat.CWXML for t in targets) and is_provider_available(AssetFormat.NATIVE)
        else ()
    )
    export_context().settings.targets = targets + extra_targets

    frag = create_asset_fragment(export_context().settings.targets)
    frag.name = f"pack:/{remove_number_suffix(frag_obj.name)}"
    frag.flags = 1  # all fragments need this flag (uses cache entry)
    frag.template_asset = FragmentTemplateAsset[frag_obj.fragment_properties.template_asset]
    frag.unbroken_elasticity = frag_obj.fragment_properties.unbroken_elasticity
    frag.gravity_factor = frag_obj.fragment_properties.gravity_factor
    frag.buoyancy_factor = frag_obj.fragment_properties.buoyancy_factor

    hi_frag = create_asset_fragment(export_context().settings.targets) if has_hi else None
    if hi_frag:
        hi_frag.name = f"{frag.name}_hi"
        hi_frag.flags = frag.flags
        hi_frag.template_asset = frag.template_asset
        hi_frag.unbroken_elasticity = frag.unbroken_elasticity
        hi_frag.gravity_factor = frag.gravity_factor
        hi_frag.buoyancy_factor = frag.buoyancy_factor

    frag_armature = frag_obj.data
    original_pose = frag_armature.pose_position
    frag_armature.pose_position = "REST"

    drawable = create_frag_drawable(frag_objs, materials, out_embedded_textures=out_embedded_textures)
    hi_drawable = create_frag_drawable(
        frag_objs, hi_materials, out_embedded_textures=out_embedded_textures, hi=True,
    ) if hi_frag else None

    frag.drawable = drawable
    if hi_frag:
        hi_frag.drawable = hi_drawable

    if frag_objs.damaged_drawable is not None:
        frag.extra_drawables = [create_frag_damaged_drawable(frag_objs, drawable, materials)]

    if frag_armature.bones:
        matrix_set = create_bone_transforms_set(drawable)
        frag.matrix_set = matrix_set
        if hi_frag:
            hi_frag.matrix_set = matrix_set

    # Physics data doesn't do anything if no collisions are present and will cause crashes
    if frag_objs.has_collisions and frag_armature.bones:
        physics, hi_physics, frag_flags, glass_windows = create_frag_physics(
            frag_objs, drawable, hi_drawable, matrix_set.matrices, materials, hi_materials
        )
        frag.physics = physics
        frag.flags |= frag_flags
        frag.glass_windows = glass_windows
        if hi_frag:
            hi_frag.physics = hi_physics
            hi_frag.flags |= frag_flags

        vehicle_windows = (
            generate_frag_vehicle_windows(frag)
            if gen_vehicle_windows
            else create_frag_vehicle_windows(frag_obj, drawable, physics.lod1.children, materials)
        )
        frag.vehicle_windows = vehicle_windows
    else:
        frag.physics = None
        if hi_frag:
            hi_frag.physics = None

    frag.lights = export_lights(frag_obj)

    env_cloth = cloth_env_export(frag_obj, drawable, materials)
    if env_cloth is not None:
        main_drawable_is_empty = all(not v for v in drawable.models.values())
        if main_drawable_is_empty:
            # Remove the main drawable if there isn't any models other than the cloth. The drawable inside the cloth
            # will become the main drawable
            frag.drawable = None

        frag.cloths = [env_cloth]  # cloths is an array but game only supports 1 cloth

        if frag.physics is None:
            # No collisions, create some dummy physics data for the cloth to work
            frag.physics = create_dummy_frag_physics_for_cloth(frag_objs, materials)
        else:
            # Cloths seem to always have an extra null bound in the composite
            # Doesn't seem to be needed, but do it for consistency with original assets
            composite = frag.physics.lod1.archetype.bounds
            bounds = composite.children
            bounds.append(None)
            if len(bounds) == 1:
                # ... and at least 2 children in the composite
                bounds.append(None)
            composite.children = bounds

    frag_armature.pose_position = original_pose

    if extra_targets:
        frag.discard_targets(extra_targets)
        if hi_frag:
            hi_frag.discard_targets(extra_targets)
        export_context().settings.targets = targets

    return frag, hi_frag


def has_hi_lods(frag_obj: Object) -> bool:
    for child in frag_obj.children_recursive:
        if child.sollum_type != SollumType.DRAWABLE_MODEL:
            continue

        very_high_lod = child.sz_lods.get_lod(LODLevel.VERYHIGH)
        if very_high_lod.mesh is not None:
            return True

    return False


def create_frag_drawable(
    frag_objs: FragmentObjects,
    materials: list[Material],
    out_embedded_textures: list[EmbeddedTexture] | None = None,
    hi: bool = False,
) -> Optional[AssetDrawable]:
    drawable = create_drawable_asset(
        frag_objs.drawable, frag_objs.fragment,
        materials,
        is_frag=True,
        out_embedded_textures=out_embedded_textures,
        hi=hi
    )
    if drawable is None:
        return None

    drawable.name = "skel"
    return drawable


def create_frag_damaged_drawable(frag_objs: FragmentObjects, main_drawable: AssetDrawable, materials: list[Material]) -> Optional[AssetDrawable]:
    assert frag_objs.damaged_drawable is not None, "Caller must ensure that there is a damaged drawable"
    drawable = create_drawable_asset(frag_objs.damaged_drawable, frag_objs.fragment, materials,
                                     is_frag=True, parent_drawable=main_drawable)
    if drawable is None:
        return None

    drawable.name = "damaged"
    # uses shader group and skeleton of the main drawable
    drawable.shader_group = None
    drawable.skeleton = None
    return drawable


def create_bone_transforms_set(drawable: AssetDrawable) -> MatrixSet:
    def _get_bone_transforms(bone: SkelBone) -> Matrix:
        return Matrix.LocRotScale(bone.position, bone.rotation, bone.scale)

    bones = drawable.skeleton.bones
    bones_transforms = []
    for bone in bones:

        transforms = _get_bone_transforms(bone)

        if bone.parent_index != -1:
            parent_transforms = bones_transforms[bone.parent_index]
            transforms = parent_transforms @ transforms

        transforms = reshape_mat_3x4(transforms)

        bones_transforms.append(transforms)

    is_skinned = any(m.has_skin for ml in drawable.models.values() for m in ml)
    return MatrixSet(is_skinned, bones_transforms)


def create_frag_physics(
    frag_objs: FragmentObjects,
    main_drawable: AssetDrawable,
    main_hi_drawable: AssetDrawable | None,
    bone_transforms_set: list[Matrix],
    materials: list[Material],
    hi_materials: list[Material] | None,
) -> tuple[PhysLodGroup, PhysLodGroup | None, int, list[FragGlassWindow]]:
    lod, hi_lod, frag_flags, glass_windows = create_frag_phys_lod(
        frag_objs,
        main_drawable, main_hi_drawable,
        bone_transforms_set,
        materials, hi_materials,
    )
    return PhysLodGroup(lod), PhysLodGroup(hi_lod) if hi_lod else None, frag_flags, glass_windows


def create_frag_phys_lod(
    frag_objs: FragmentObjects,
    main_drawable: AssetDrawable,
    main_hi_drawable: AssetDrawable | None,
    bone_transforms_set: list[Matrix],
    materials: list[Material],
    hi_materials: list[Material] | None,
) -> tuple[PhysLod, PhysLod | None, int, list[FragGlassWindow]]:
    frag_obj = frag_objs.fragment
    lod_props = frag_obj.fragment_properties.lod_properties
    skeleton = main_drawable.skeleton
    col_obj_to_bound_index = {}
    composite, damaged_composite = create_frag_phys_collisions(frag_objs, col_obj_to_bound_index)
    groups, glass_windows = create_frag_phys_groups(frag_objs, materials)
    children, hi_children, has_child_meshes = create_frag_phys_children(
        frag_objs,
        main_drawable, main_hi_drawable,
        skeleton,
        groups,
        composite, damaged_composite,
        materials, hi_materials,
        col_obj_to_bound_index,
    )

    frag_flags = 0
    if has_child_meshes:
        # flag for vehicles (only thing that has children with drawables), seems unused at runtime though
        frag_flags |= 64

    unbroken_cg_offset = Vector(lod_props.unbroken_cg_offset)
    if groups and children:
        calculate_frag_phys_groups_total_masses(groups, children)
        calculate_frag_phys_child_drawable_matrices(
            children, composite, damaged_composite, skeleton, bone_transforms_set
        )

        sort_frag_phys_children_and_collisions_inplace(children, hi_children, composite, damaged_composite)

        is_articulated, root_cg_offset, link_attachments = calculate_frag_phys_link_attachments(
            skeleton,
            groups,
            children,
            composite.children,
            unbroken_cg_offset,
        )

        if is_articulated:
            frag_flags |= 2  # set 'is articulated' flag

        composite.cg = root_cg_offset  # the physics LOD CG overrides the composite CG
    else:
        root_cg_offset = Vector((0.0, 0.0, 0.0))
        link_attachments = []

    archetype, damaged_archetype = create_frag_phys_archetypes(
        frag_objs, children, composite, damaged_composite, root_cg_offset
    )

    smallest_inertia, largest_inertia = calculate_frag_phys_inertia_limits(children)
    lod = PhysLod(
        archetype=archetype,
        damaged_archetype=damaged_archetype,
        children=children,
        groups=groups,
        smallest_ang_inertia=smallest_inertia,
        largest_ang_inertia=largest_inertia,
        min_move_force=lod_props.min_move_force,
        root_cg_offset=root_cg_offset,
        original_root_cg_offset=root_cg_offset,  # same as root CG offset in all game .yfts
        unbroken_cg_offset=unbroken_cg_offset,
        damping_linear_c=Vector(lod_props.damping_linear_c),
        damping_linear_v=Vector(lod_props.damping_linear_v),
        damping_linear_v2=Vector(lod_props.damping_linear_v2),
        damping_angular_c=Vector(lod_props.damping_angular_c),
        damping_angular_v=Vector(lod_props.damping_angular_v),
        damping_angular_v2=Vector(lod_props.damping_angular_v2),
        link_attachments=link_attachments,
    )

    hi_lod = replace(lod, children=hi_children)

    return lod, hi_lod, frag_flags, glass_windows


def create_frag_phys_collisions(
    frag_objs: FragmentObjects,
    col_obj_to_bound_index: dict[Object, int]
) -> tuple[AssetBound, Optional[AssetBound]]:
    assert frag_objs.composite is not None, "Caller must ensure that there is a composite"

    composite = create_bound_composite_asset(frag_objs.composite, col_obj_to_bound_index)

    if frag_objs.damaged_composite is not None:
        damaged_col_obj_to_bound_index = {}
        damaged_composite = create_bound_composite_asset(frag_objs.damaged_composite, damaged_col_obj_to_bound_index)

        # With damaged fragments we have to make space in both composites to fit all bounds (both damaged and undamaged)
        # so indices remain consistent between them. Extra spaces are just left empty (none)
        num_children = len(composite.children)
        num_damaged_children = len(damaged_composite.children)
        composite.children = composite.children + [None] * num_damaged_children
        damaged_composite.children = [None] * num_children + damaged_composite.children

        # Include the damaged bounds in the output obj->index mapping
        for damaged_col_obj, bound_index in damaged_col_obj_to_bound_index.items():
            col_obj_to_bound_index[damaged_col_obj] = bound_index + num_children
    else:
        damaged_composite = None

    return composite, damaged_composite


def create_frag_phys_groups(
    frag_objs: FragmentObjects,
    materials: list[Material]
) -> tuple[list[PhysGroup], list[FragGlassWindow]]:
    frag_obj = frag_objs.fragment
    group_ind_by_name: dict[str, int] = {}
    groups_by_bone: dict[int, list[PhysGroup]] = defaultdict(list)
    glass_windows = []

    for bone in frag_obj.data.bones:
        if not bone.sollumz_use_physics:
            continue

        if not does_bone_have_collision(bone.name, frag_obj) and not does_bone_have_cloth(bone.name, frag_obj):
            logger.warning(
                f"Bone '{bone.name}' has physics enabled, but no associated collision! A collision must be linked to the bone for physics to work.")
            continue

        bone_index = get_bone_index(frag_obj.data, bone)
        group = init_frag_phys_group(bone.name, bone.group_properties)
        groups_by_bone[bone_index].append(group)

        if bone.group_properties.flags[GroupFlagBit.USE_GLASS_WINDOW]:
            w = create_frag_glass_window(frag_obj, bone, materials)
            if w is not None:
                group.glass_window_index = len(glass_windows)
                glass_windows.append(w)

    # Sort by bone index
    groups_by_bone = dict(sorted(groups_by_bone.items()))

    for groups in groups_by_bone.values():
        for group in groups:
            i = len(group_ind_by_name)

            group_ind_by_name[group.name] = i

    def _get_group_parent_index(group_bone: bpy.types.Bone) -> int:
        """Returns parent group index or 255 if there is no parent."""
        parent_bone = group_bone.parent
        if parent_bone is None:
            return 255

        if not parent_bone.sollumz_use_physics or parent_bone.name not in group_ind_by_name:
            # Parent has no frag group, try with grandparent
            return _get_group_parent_index(parent_bone)

        return group_ind_by_name[parent_bone.name]

    # Set group parent indices
    final_groups = []
    for bone_index, groups in groups_by_bone.items():
        parent_index = _get_group_parent_index(frag_obj.data.bones[bone_index])

        for group in groups:
            group.parent_group_index = parent_index

            group_ind_by_name[group.name] = len(final_groups)

            final_groups.append(group)

    return final_groups, glass_windows


def init_frag_phys_group(name: str, group_props: GroupProperties) -> PhysGroup:
    flags = 0
    for i in range(len(group_props.flags)):
        flags |= (1 << i) if group_props.flags[i] else 0

    return PhysGroup(
        name=name,
        parent_group_index=255,
        flags=flags,
        total_mass=0.0,
        strength=group_props.strength,
        force_transmission_scale_up=group_props.force_transmission_scale_up,
        force_transmission_scale_down=group_props.force_transmission_scale_down,
        joint_stiffness=group_props.joint_stiffness,
        min_soft_angle_1=group_props.min_soft_angle_1,
        max_soft_angle_1=group_props.max_soft_angle_1,
        max_soft_angle_2=group_props.max_soft_angle_2,
        max_soft_angle_3=group_props.max_soft_angle_3,
        rotation_speed=group_props.rotation_speed,
        rotation_strength=group_props.rotation_strength,
        restoring_strength=group_props.restoring_strength,
        restoring_max_torque=group_props.restoring_max_torque,
        latch_strength=group_props.latch_strength,
        min_damage_force=group_props.min_damage_force,
        damage_health=group_props.damage_health,
        weapon_health=group_props.weapon_health,
        weapon_scale=group_props.weapon_scale,
        vehicle_scale=group_props.vehicle_scale,
        ped_scale=group_props.ped_scale,
        ragdoll_scale=group_props.ragdoll_scale,
        explosion_scale=group_props.explosion_scale,
        object_scale=group_props.object_scale,
        ped_inv_mass_scale=group_props.ped_inv_mass_scale,
        melee_scale=group_props.melee_scale,
        glass_window_index=0,
    )


def create_frag_phys_children(
    frag_objs: FragmentObjects,
    main_drawable: AssetDrawable,
    main_hi_drawable: AssetDrawable | None,
    skeleton: Skeleton,
    groups: list[PhysGroup],
    bound_composite: AssetBound,
    damaged_bound_composite: AssetBound | None,
    materials: list[Material],
    hi_materials: list[Material] | None,
    col_obj_to_bound_index: dict[Object, int],
) -> tuple[list[PhysChild], list[PhysChild] | None, bool]:
    """Creates the physics children for each collision object.

    Additionally, makes sure that ``bound_composite.children`` order matches the returned children order so
    the same indices can be used with both collections.

    Returns a tuple with the list of children, an optional list of children with very-high LOD drawables, and a bool
    indicating whether any children has drawable models.
    """
    frag_obj = frag_objs.fragment
    frag_armature = frag_obj.data
    bones = skeleton.bones
    child_meshes = find_frag_phys_children_meshes(frag_objs)
    child_cols = find_frag_phys_children_collisions(frag_objs)
    damaged_child_cols = (
        find_frag_phys_children_collisions(frag_objs, damaged=True) if frag_objs.damaged_composite else {}
    )

    children = []
    hi_children = [] if main_hi_drawable else None
    has_child_meshes = False
    groups_with_child_mesh = set()
    bound_index_to_child_index = []
    damaged_bound_index_to_child_index = []
    for bone_name, col_objs in child_cols.items():
        damaged_col_objs = damaged_child_cols.get(bone_name, [])
        for col_obj, damaged_col_obj in zip_longest(col_objs, damaged_col_objs, fillvalue=None):
            child_index = len(children)
            if col_obj:
                bound_index = col_obj_to_bound_index[col_obj]
                bound_index_to_child_index.append((bound_index, child_index))
            else:
                bound_index = None
            if damaged_col_obj:
                damaged_bound_index = col_obj_to_bound_index[damaged_col_obj]
                damaged_bound_index_to_child_index.append((damaged_bound_index, child_index))
            else:
                damaged_bound_index = None

            bone = frag_armature.bones.get(bone_name)
            bone_index = get_bone_index(frag_armature, bone) or 0
            group_index = find_phys_group_index_by_name(groups, bone_name)

            mesh_objs = None
            if bone_name in child_meshes and group_index not in groups_with_child_mesh:
                mesh_objs = child_meshes[bone_name]
                groups_with_child_mesh.add(group_index)  # only one child per group should have the mesh
                has_child_meshes = True

            drawable = create_frag_phys_child_drawable(main_drawable, materials, mesh_objs)

            if main_hi_drawable:
                hi_drawable = create_frag_phys_child_drawable(main_hi_drawable, hi_materials, mesh_objs, hi=True)
            else:
                hi_drawable = None

            if damaged_col_obj:
                # Need an empty drawable
                damaged_drawable = create_frag_phys_child_drawable(main_drawable, materials)
            else:
                damaged_drawable = None

            pristine_mass = col_obj.child_properties.mass if col_obj else 0.0
            damaged_mass = damaged_col_obj.child_properties.mass if damaged_col_obj else pristine_mass
            inertia = \
                calculate_frag_phys_child_inertia(bound_composite, pristine_mass, bound_index) \
                if col_obj else Vector((0.0, 0.0, 0.0, 0.0))
            damaged_inertia = \
                calculate_frag_phys_child_inertia(damaged_bound_composite, damaged_mass, damaged_bound_index) \
                if damaged_col_obj else Vector((0.0, 0.0, 0.0, 0.0))
            child = PhysChild(
                bone_tag=bones[bone_index].tag,
                group_index=group_index,
                pristine_mass=pristine_mass,
                damaged_mass=damaged_mass,
                drawable=drawable,
                damaged_drawable=damaged_drawable,
                min_breaking_impulse=0.0,
                inertia=inertia,
                damaged_inertia=damaged_inertia,
            )

            if hi_drawable:
                hi_child = replace(child, drawable=hi_drawable)
                hi_children.append(hi_child)

            children.append(child)

    # reorder bounds children based on physics children order
    for comp, index_map in (
        (bound_composite, bound_index_to_child_index),
        (damaged_bound_composite, damaged_bound_index_to_child_index)
    ):
        if comp is None:
            continue

        bounds = comp.children
        new_bounds = [None] * len(children)
        for bound_index, child_index in index_map:
            new_bounds[child_index] = bounds[bound_index]

        comp.children = new_bounds

    return children, hi_children, has_child_meshes


def calculate_frag_phys_child_inertia(bound_composite: AssetBound, mass: float, bound_index: int) -> Vector:
    bounds = bound_composite.children
    if not bounds or bound_index >= len(bounds):
        return Vector((0.0, 0.0, 0.0, 0.0))

    bound = bounds[bound_index]
    inertia = bound.inertia * mass
    # volume*mass in the original files is probably not important and just a side-effect of SIMD operations, still do it just in case
    return Vector((inertia.x, inertia.y, inertia.z, bound.volume * mass))


def calculate_frag_phys_groups_total_masses(groups: list[PhysGroup], children: list[PhysChild]):
    """Calculate the mass of all groups in based on child masses."""
    for child in children:
        groups[child.group_index].total_mass += child.pristine_mass


def sort_frag_phys_children_and_collisions_inplace(
    children: list[PhysChild],
    hi_children: list[PhysChild] | None,
    bound_composite: AssetBound,
    damaged_bound_composite: Optional[AssetBound],
):
    children_by_group: dict[int, list[int]] = defaultdict(list)
    if not children:
        return

    for i, child in enumerate(children):
        children_by_group[child.group_index].append(i)

    children_by_group = dict(sorted(children_by_group.items()))

    # Map old indices to new ones
    indices: dict[int, int] = {}
    unsorted_children = list(children)
    unsorted_hi_children = list(hi_children) if hi_children else None

    new_child_index = 0
    for group_index, children_indices in children_by_group.items():
        for child_index in children_indices:
            indices[child_index] = new_child_index
            children[new_child_index] = unsorted_children[child_index]
            if hi_children:
                hi_children[new_child_index] = unsorted_hi_children[child_index]
            new_child_index += 1

    # Apply sorting to collisions
    for composite in (bound_composite, damaged_bound_composite):
        if composite is None:
            continue

        bounds = composite.children
        sorted_collisions: list[AssetBound] = [None] * len(indices)

        for old_index, new_index in indices.items():
            sorted_collisions[new_index] = bounds[old_index]

        composite.children = sorted_collisions


def calculate_frag_phys_child_drawable_matrices(
    children: list[PhysChild],
    bound_composite: AssetBound,
    damaged_bound_composite: Optional[AssetBound],
    skeleton: Skeleton,
    bone_transforms_set: list[Matrix],
):
    """Calculate the matrix for each physics child Drawable from bone transforms
    and composite transforms. Each matrix represents the transformation of the
    child relative to the bone."""
    bones = skeleton.bones
    collisions = bound_composite.children
    damaged_collisions = damaged_bound_composite.children if damaged_bound_composite else None

    bone_transform_by_tag: dict[str, Matrix] = {b.tag: bone_transforms_set[i] for i, b in enumerate(bones)}

    for cols in (collisions, damaged_collisions):
        if not cols:
            continue

        for i, child in enumerate(children):
            bone_transform = bone_transform_by_tag[child.bone_tag]

            col = cols[i]
            if not col:
                continue

            bone_inv = bone_transform.to_4x4().inverted()

            matrix = col.composite_transform @ bone_inv.transposed()
            drawable = child.damaged_drawable if cols is damaged_collisions else child.drawable
            drawable.frag_bound_matrix = matrix

    create_child_mat_arrays(children, bound_composite, damaged_bound_composite)


def create_child_mat_arrays(
    children: list[PhysChild],
    bound_composite: AssetBound,
    damaged_bound_composite: Optional[AssetBound],
):
    """Create the matrix arrays for each child. This appears to be in the first child of multiple children that
    share the same group. Each matrix in the array is just the matrix for each child in that group."""
    bounds = bound_composite.children
    damaged_bounds = damaged_bound_composite.children if damaged_bound_composite else None
    group_inds = set(child.group_index for child in children)

    for i in group_inds:
        group_children = [(child_index, child) for child_index, child in enumerate(children) if child.group_index == i]

        if len(group_children) <= 1:
            continue

        _, first = group_children[0]

        extra_matrices = []
        damaged_extra_matrices = []
        for child_index, child in group_children[1:]:
            if bounds[child_index]:
                extra_matrices.append(child.drawable.frag_bound_matrix)
            if damaged_bounds and damaged_bounds[child_index]:
                damaged_extra_matrices.append(child.damaged_drawable.frag_bound_matrix)

        first.drawable.frag_extra_bound_matrices = extra_matrices
        if first.damaged_drawable:
            first.damaged_drawable.frag_extra_bound_matrices = damaged_extra_matrices


def create_frag_phys_archetypes(
    frag_objs: FragmentObjects,
    phys_children: list[PhysChild],
    composite: AssetBound,
    damaged_composite: AssetBound | None,
    root_cg_offset: Vector,
) -> tuple[PhysArchetype, PhysArchetype | None]:
    frag_obj = frag_objs.fragment
    archetype_props = frag_obj.fragment_properties.lod_properties.archetype_properties
    archetype_name = remove_number_suffix(frag_obj.name)

    archetype = create_frag_phys_archetype(archetype_props, archetype_name, phys_children, composite, root_cg_offset)

    if frag_objs.damaged_composite is not None:
        assert damaged_composite is not None
        damaged_archetype = create_frag_phys_archetype(
            archetype_props, archetype_name, phys_children, damaged_composite, root_cg_offset, damaged=True
        )
    else:
        damaged_archetype = None

    return archetype, damaged_archetype


def create_frag_phys_archetype(
    archetype_props: FragArchetypeProperties,
    frag_name: str,
    phys_children: list[PhysChild],
    bound_composite: AssetBound,
    root_cg_offset: Vector,
    damaged: bool = False
) -> PhysArchetype:
    assert bound_composite.bound_type == BoundType.COMPOSITE
    mass, inertia = calculate_frag_phys_archetype_mass_inertia(
        phys_children, bound_composite.children, root_cg_offset, damaged
    )
    mass_inv = (1 / mass) if mass != 0 else 0
    inertia_inv = vector_inv(inertia)
    return PhysArchetype(
        name=frag_name,
        bounds=bound_composite,
        gravity_factor=archetype_props.gravity_factor,
        max_speed=archetype_props.max_speed,
        max_ang_speed=archetype_props.max_ang_speed,
        buoyancy_factor=archetype_props.buoyancy_factor,
        mass=mass,
        mass_inv=mass_inv,
        inertia=inertia,
        inertia_inv=inertia_inv,
    )


def calculate_frag_phys_archetype_mass_inertia(
    phys_children: list[PhysChild],
    bounds: list[AssetBound],
    root_cg_offset: Vector,
    damaged: bool = False
) -> tuple[float, Vector]:
    """Set archetype mass and inertia based on children mass and bounds. Expects physics children and collisions to
    exist, and the physics LOD root CG to have already been calculted.
    """
    if not phys_children:
        return 0.0, Vector((0.0, 0.0, 0.0))

    assert len(phys_children) == len(bounds)

    from ..shared.geometry import calculate_composite_inertia
    # Filter out children with null bounds
    phys_children, bounds = zip(*((c, b) for c, b in zip(phys_children, bounds) if b is not None))
    masses = [child.damaged_mass if damaged else child.pristine_mass for child in phys_children]
    inertias = [(child.damaged_inertia if damaged else child.inertia).xyz for child in phys_children]
    cgs = [bound.composite_transform.transposed() @ bound.cg for bound in bounds]
    mass = sum(masses)
    inertia = calculate_composite_inertia(root_cg_offset, cgs, masses, inertias)
    return mass, inertia


def calculate_frag_phys_inertia_limits(phys_children: list[PhysChild]) -> tuple[float, float]:
    """Calculates the physics LOD smallest and largest angular inertia from its children."""
    if not phys_children:
        return 0.0, 0.0

    inertia_values = [
        value
        for c in phys_children
        for inertia in (c.inertia, c.damaged_inertia)
        for value in inertia.xyz
    ]
    largest_inertia = max(inertia_values)
    smallest_inertia = largest_inertia / 10000.0  # game assets always have same value as largest divided by 10000
    return smallest_inertia, largest_inertia


def does_bone_have_collision(bone_name: str, frag_obj: Object):
    col_objs = [obj for obj in frag_obj.children_recursive if obj.sollum_type in BOUND_TYPES]

    for obj in col_objs:
        bone = get_child_of_bone(obj)

        if bone is not None and bone.name == bone_name:
            return True

    return False


def does_bone_have_cloth(bone_name: str, frag_obj: bpy.types.Object) -> bool:
    cloth_objs = cloth_env_find_mesh_objects(frag_obj, silent=True)

    for obj in cloth_objs:
        bone = get_child_of_bone(obj)

        if bone is not None and bone.name == bone_name:
            return True

    return False


def calculate_frag_phys_link_attachments(
    skeleton: Skeleton,
    groups: list[PhysGroup],
    children: list[PhysChild],
    bounds: list[AssetBound],
    unbroken_cg_offset: Vector
) -> tuple[bool, Vector, list[Matrix]]:
    """Calculate ``frag_xml.physics.lod1.transforms``. A transformation matrix per physics child that represents
    the offset from the child collision bound to its link center of gravity (aka "link attachment"). A link is
    formed by physics groups that act as a rigid body together, a group with a joint creates a new link.
    Also calculates the physics LOD root CG offset.
    """

    bones = skeleton.bones

    children_by_group: list[list[tuple[int, PhysChild]]] = [[] for _ in range(len(groups))]
    for child_index, child in enumerate(children):
        children_by_group[child.group_index].append((child_index, child))

    # Array of links (i.e. array of arrays of groups)
    links = [[]]  # the root link is at index 0
    link_index_by_group = [-1] * len(groups)

    # Determine the groups that form each link
    for group_index, group in enumerate(groups):
        link_index = 0  # by default add to root link

        if group.parent_group_index != 255:
            _, first_child = children_by_group[group_index][0]
            bone = next(b for b in bones if b.tag == first_child.bone_tag)
            creates_new_link = bone.rotation_limit is not None or bone.translation_limit is not None
            if creates_new_link:
                # There is a joint, create a new link
                link_index = len(links)
                links.append([])
            else:
                # Add to link of parent group
                link_index = link_index_by_group[group.parent_group_index]

        links[link_index].append(group)
        link_index_by_group[group_index] = link_index

    is_articulated = len(links) > 1

    # Calculate center of gravity of each link. This is the weighted mean of the center of gravity of all physics
    # children that form the link.
    links_center_of_gravity = [Vector((0.0, 0.0, 0.0)) for _ in range(len(links))]
    for link_index, groups in enumerate(links):
        link_total_mass = 0.0
        for group_index, group in enumerate(groups):
            for child_index_rel, (child_index, child) in enumerate(children_by_group[group_index]):
                bound = bounds[child_index]
                if bound is not None:
                    center = bound.composite_transform.transposed() @ bound.cg
                else:
                    center = Vector((0.0, 0.0, 0.0))

                child_mass = child.pristine_mass
                links_center_of_gravity[link_index] += center * child_mass
                link_total_mass += child_mass

        if link_total_mass > 0.0:
            links_center_of_gravity[link_index] /= link_total_mass

    # add the user-defined unbroken CG offset to the root CG offset
    links_center_of_gravity[0] += unbroken_cg_offset

    # Calculate child transforms (aka "link attachments", offset from bound to link CG)
    link_attachments = []
    for child_index, child in enumerate(children):
        # print(f"#{child_index} ({child.bone_tag}) link_index={link_index_by_group[child.group_index]}")
        link_center = links_center_of_gravity[link_index_by_group[child.group_index]]
        bound = bounds[child_index]
        if bound is not None:
            offset = Matrix.Translation(-link_center) @ bound.composite_transform.transposed()
            offset.transpose()
        else:
            offset = Matrix.Identity(4)

        # It is a 3x4 matrix, so zero out the 4th column to be consistent with original matrices
        # (doesn't really matter but helps with equality checks in our tests)
        offset.col[3].zero()

        link_attachments.append(offset)

    root_cg_offset = links_center_of_gravity[0]
    return is_articulated, root_cg_offset, link_attachments


def find_frag_phys_children_collisions(frag_objs: FragmentObjects, damaged: bool = False) -> dict[str, list[Object]]:
    """Get collisions that are linked to a child. Returns a dict mapping each collision to a bone name."""
    composite_obj = frag_objs.damaged_composite if damaged else frag_objs.composite
    assert composite_obj is not None, "Caller must ensure that there is a composite"

    child_cols_by_bone: dict[str, list[Object]] = defaultdict(list)
    for bound_obj in composite_obj.children:
        if bound_obj.sollum_type not in BOUND_TYPES:
            continue
        if (bound_obj.type == "MESH" and not has_collision_materials(bound_obj)) or (bound_obj.type == "EMPTY" and not has_bvh_collision_materials(bound_obj)):
            continue

        bone = get_child_of_bone(bound_obj)

        if bone is None or not bone.sollumz_use_physics:
            continue

        child_cols_by_bone[bone.name].append(bound_obj)

    return child_cols_by_bone


def find_frag_phys_children_meshes(frag_objs: FragmentObjects) -> dict[str, list[Object]]:
    """Get meshes that are linked to a child. Returns a dict mapping child meshes to bone name."""
    drawable_obj = frag_objs.drawable
    child_meshes_by_bone: dict[str, list[Object]] = defaultdict(list)
    for model_obj in drawable_obj.children:
        if model_obj.sollum_type != SollumType.DRAWABLE_MODEL or not model_obj.sollumz_is_physics_child_mesh:
            continue

        bone = get_child_of_bone(model_obj)

        if bone is None or not bone.sollumz_use_physics:
            continue

        child_meshes_by_bone[bone.name].append(model_obj)

    return child_meshes_by_bone


def find_phys_group_index_by_name(groups: list[PhysGroup], name: str) -> int:
    for i, group in enumerate(groups):
        if group.name == name:
            return i

    return -1


def create_frag_phys_child_drawable(main_drawable: AssetDrawable | None, materials: list[Material], model_objs: Optional[list[Object]] = None, hi: bool = False) -> AssetDrawable:
    drawable = create_asset_drawable(export_context().settings.targets, is_frag=True, parent_drawable=main_drawable)
    drawable.shader_group = None
    drawable.skeleton = None

    if not model_objs:
        return drawable

    lod_levels = (LODLevel.VERYHIGH,) if hi else (LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW)

    models: dict[IOLodLevel, list[Model]] = defaultdict(list)
    for model_obj in model_objs:
        scale = get_scale_to_apply_to_bound(model_obj)
        transforms_to_apply = Matrix.Diagonal(scale).to_4x4()

        lods = model_obj.sz_lods
        for lod_level in lod_levels:
            lod_mesh = lods.get_lod(lod_level).mesh
            if lod_mesh is None:
                continue

            model: Model = create_model(model_obj, lod_level, materials, transforms_to_apply=transforms_to_apply)
            if not model.geometries:
                continue

            model.bone_index = 0
            models[lod_level.to_io()].append(model)

    drawable.models = models
    return drawable


def generate_frag_vehicle_windows(frag: AssetFragment) -> list[FragVehicleWindow]:
    """Automatically generate all the vehicle windows found in ``frag``."""
    if not is_provider_available(AssetFormat.NATIVE):
        logger.warning("PyMateria is not installed. Cannot automatically generate vehicle window shattermaps.")
        return []

    # Only NATIVE assets implement generate_vehicle_windows()
    native_frag = (
        frag.with_format(AssetFormat.NATIVE)
        if frag.ASSET_FORMAT == AssetFormat.MULTI_TARGET
        else frag
    )
    assert native_frag and native_frag.ASSET_FORMAT == AssetFormat.NATIVE
    return native_frag.generate_vehicle_windows()


def create_frag_vehicle_windows(frag_obj: Object, main_drawable: AssetDrawable, phys_children: list[PhysChild], materials: list[Material]) -> list[FragVehicleWindow]:
    """Exports all the manually defined vehicle windows found in ``frag_obj`` hierarchy."""
    child_id_by_bone_tag: dict[str, int] = {c.bone_tag: i for i, c in enumerate(phys_children)}
    mat_ind_by_name: dict[str, int] = {mat.name: i for i, mat in enumerate(materials)}
    bones = main_drawable.skeleton.bones

    vehicle_windows = []
    for obj in frag_obj.children_recursive:
        if not obj.child_properties.is_veh_window:
            continue

        bone = get_child_of_bone(obj)
        if bone is None or not bone.sollumz_use_physics:
            logger.warning(
                f"Vehicle window '{obj.name}' is not attached to a bone, or the attached bone does not have physics "
                "enabled! Attach the bone via a Copy Transforms constraint."
            )
            continue

        bone_index = get_bone_index(frag_obj.data, bone)
        bone_tag = bones[bone_index].tag
        if bone_tag not in child_id_by_bone_tag:
            logger.warning(f"No physics child for the vehicle window '{obj.name}'!")
            continue

        window_mat = obj.child_properties.window_mat
        if window_mat is None:
            logger.warning(f"Vehicle window '{obj.name}' has no material with the vehicle_vehglass shader!")
            continue

        if window_mat.name not in mat_ind_by_name:
            logger.warning(
                f"Vehicle window '{obj.name}' is using a vehicle_vehglass material '{window_mat.name}' that is not "
                f"used in the Drawable! This material should be added to the mesh object attached to the bone '{bone.name}'."
            )
            continue

        shattermap, basis = create_frag_vehicle_window_shattermap(obj)
        height, width = shattermap.shape
        vehicle_windows.append(FragVehicleWindow(
            basis=basis,
            component_id=child_id_by_bone_tag[bone_tag],
            geometry_index=get_frag_vehicle_window_geometry_index(main_drawable, mat_ind_by_name[window_mat.name]),
            width=width,
            height=height,
            scale=obj.vehicle_window_properties.cracks_texture_tiling,
            flags=0,
            data_min=obj.vehicle_window_properties.data_min,
            data_max=obj.vehicle_window_properties.data_max,
            shattermap=shattermap,
        ))

    vehicle_windows.sort(key=lambda w: w.component_id)
    return vehicle_windows


def create_frag_vehicle_window_shattermap(col_obj: Object) -> tuple[np.ndarray, Matrix]:
    """Create window shattermap (if it exists) and calculate projection"""
    shattermap_obj = find_frag_vehicle_window_shattermap_obj(col_obj)
    if shattermap_obj is not None:
        shattermap_img = find_frag_vehicle_window_shattermap_image(shattermap_obj)
        if shattermap_img is not None:
            shattermap = image_to_shattermap(shattermap_img)
            basis = calculate_frag_vehicle_shattermap_basis(shattermap_obj, shattermap_img)
            return shattermap, basis

    return np.empty((0, 0), dtype=np.float32), Matrix()


def image_to_shattermap(img: Image) -> np.ndarray:
    width, height = img.size
    pixels = np.array(img.pixels, dtype=np.float32).reshape((height, width, 4))
    shattermap = pixels[:, :, 0]
    return shattermap


def calculate_frag_vehicle_shattermap_basis(obj: Object, img: Image) -> Matrix:
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

    resx, resy = img.size
    thickness = 0.01

    edge1 = (v2 - v1) / resx
    edge2 = (v3 - v1) / resy
    edge3 = edge1.normalized().cross(edge2.normalized()) * thickness

    matrix = Matrix()
    matrix[0] = edge1.x, edge2.x, edge3.x, v1.x
    matrix[1] = edge1.y, edge2.y, edge3.y, v1.y
    matrix[2] = edge1.z, edge2.z, edge3.z, v1.z

    # Create projection matrix relative to parent
    parent_inverse = get_parent_inverse(obj)
    matrix = parent_inverse @ obj.matrix_world @ matrix

    try:
        matrix.invert()
    except ValueError:
        logger.warning(
            f"Failed to create shattermap projection matrix for '{obj.name}'. Ensure the object is a flat plane with 4 vertices."
        )
        return Matrix()

    return matrix


def find_frag_vehicle_window_shattermap_obj(col_obj: Object) -> Object | None:
    for child in col_obj.children:
        if child.sollum_type == SollumType.SHATTERMAP:
            return child

    return None


def find_frag_vehicle_window_shattermap_image(obj: Object) -> Image | None:
    """Find shattermap material on ``obj`` and get the image attached to the base color node."""
    for mat in obj.data.materials:
        for node in mat.node_tree.nodes:
            if isinstance(node, ShaderNodeTexImage):
                return node.image

    return None


def get_frag_vehicle_window_geometry_index(drawable: AssetDrawable, window_shader_index: int) -> int:
    """Get index of the geometry using the window material."""
    models = drawable.models.get(IOLodLevel.HIGH, [])
    if not models:
        return 0

    model = models[0]
    for (index, geometry) in enumerate(model.geometries):
        if geometry.shader_index == window_shader_index:
            return index

    return 0


def create_frag_glass_window(
    frag_obj: Object,
    glass_window_bone: Bone,
    materials: list[Material],
) -> FragGlassWindow | None:
    mesh_obj, col_obj = find_frag_glass_window_mesh_and_col(frag_obj, glass_window_bone)
    if mesh_obj is None or col_obj is None:
        logger.warning(f"Glass window '{glass_window_bone.name}' is missing the mesh and/or collision. Skipping...")
        return None

    # calculate properties from the mesh
    mesh_obj_eval = get_evaluated_obj(mesh_obj)
    mesh = mesh_obj_eval.to_mesh()
    mesh_planes = mesh_linked_triangles(mesh)
    if len(mesh_planes) != 2:
        logger.warning(f"Glass window '{glass_window_bone.name}' requires 2 separate planes in mesh.")
        if len(mesh_planes) < 2:
            return None  # need at least 2 planes to continue

    plane_a, plane_b = mesh_planes[:2]
    if len(plane_a) != 2 or len(plane_b) != 2:
        logger.warning(f"Glass window '{glass_window_bone.name}' mesh planes need to be made up of 2 triangles each.")
        if len(plane_a) < 2 or len(plane_b) < 2:
            return None  # need at least 2 tris in each plane to continue

    normals = (plane_a[0].normal, plane_a[1].normal, plane_b[0].normal, plane_b[1].normal)
    if any(a.cross(b).length_squared > float_info.epsilon for a, b in combinations(normals, 2)):
        logger.warning(f"Glass window '{glass_window_bone.name}' mesh planes are not parallel.")

    # calculate UV min/max (unused by the game)
    uvs = np.empty((len(mesh.loops), 2), dtype=np.float32)
    mesh.uv_layers[0].data.foreach_get("uv", uvs.ravel())
    flip_uvs(uvs)
    uv_min = uvs.min(axis=0)
    uv_max = uvs.max(axis=0)

    # calculate glass thickness
    center_a = (plane_a[0].center + plane_a[1].center) * 0.5
    center_b = (plane_b[0].center + plane_b[1].center) * 0.5
    thickness = (center_a - center_b).length

    # calculate tangent (unused by the game)
    tangent = normals[0].cross(Vector((0.0, 0.0, 1.0)))

    # calculate projection matrix
    #   get plane vertices sorted by normalized UV distance to (0, 0)
    plane_loops = {loop for tri in plane_a for loop in tri.loops}
    plane_loops = sorted(plane_loops, key=lambda loop: np.linalg.norm((uvs[loop] - uv_min) / (uv_max - uv_min)))
    plane_verts_and_uvs = [(mesh.loops[loop].vertex_index, uvs[loop]) for loop in plane_loops]

    #   get vertices needed to build the projection (top-left, top-right and bottom-left)
    v0_idx, v0_uv = plane_verts_and_uvs[0]  # vertex at UV min
    v1_idx = next(vert_idx for vert_idx, uv in plane_verts_and_uvs
                  if abs(uv[0] - v0_uv[0]) > abs(uv[1] - v0_uv[1]))  # vertex to the right of v0
    v2_idx = next(vert_idx for vert_idx, uv in plane_verts_and_uvs
                  if abs(uv[1] - v0_uv[1]) > abs(uv[0] - v0_uv[0]))  # vertex below v0
    v0 = mesh.vertices[v0_idx].co
    v1 = mesh.vertices[v1_idx].co
    v2 = mesh.vertices[v2_idx].co

    #   build projection and apply object transform
    transform = get_parent_inverse(mesh_obj_eval) @ mesh_obj_eval.matrix_world
    transform.invert()
    T = v0 @ transform
    V = (v1 - v0) @ transform
    U = (v2 - v0) @ transform

    # calculate shader index
    material = mesh.materials[0] if len(mesh.materials) > 0 else None
    if material is not None:
        shader_index = next((i for i, mat in enumerate(materials) if mat == material.original), -1)
    else:
        shader_index = -1

    if shader_index == -1:
        logger.warning(f"Glass window '{glass_window_bone.name}' mesh is missing a material.")

    # calculate bounds offset front/back
    world_transform = mesh_obj_eval.matrix_world
    center_a_world = world_transform @ center_a
    normal_a_world = normals[0].copy()
    normal_a_world.rotate(world_transform)
    bounds_offset_front, bounds_offset_back = calculate_frag_glass_window_bounds_offset(
        col_obj, center_a_world, normal_a_world
    )

    mesh_obj_eval.to_mesh_clear()

    glass_type = glass_window_bone.group_properties.glass_type
    glass_type_index = get_glass_type_index(glass_type)

    return FragGlassWindow(
        glass_type=glass_type_index & 0xFF,
        shader_index=shader_index & 0xFF,
        pos_base=T,
        pos_width=V,
        pos_height=U,
        uv_min=Vector(uv_min),
        uv_max=Vector(uv_max),
        thickness=thickness,
        bounds_offset_front=bounds_offset_front,
        bounds_offset_back=bounds_offset_back,
        tangent=tangent,
    )


def find_frag_glass_window_mesh_and_col(
    frag_obj: Object,
    glass_window_bone: Bone
) -> tuple[Object | None, Object | None]:
    """Finds the mesh and collision object for the glass window bone.
    Returns tuple (mesh_obj, col_obj)
    """
    mesh_obj = None
    col_obj = None
    for obj in frag_obj.children_recursive:
        if obj.sollum_type != SollumType.DRAWABLE_MODEL and obj.sollum_type not in BOUND_TYPES:
            continue

        parent_bone = get_child_of_bone(obj)
        if parent_bone != glass_window_bone:
            continue

        if obj.sollum_type == SollumType.DRAWABLE_MODEL:
            mesh_obj = obj
        else:
            col_obj = obj

        if mesh_obj is not None and col_obj is not None:
            break

    return mesh_obj, col_obj


def calculate_frag_glass_window_bounds_offset(
    col_obj: Object,
    point: Vector,
    point_normal: Vector
) -> tuple[float, float]:
    """Calculates the front and back offset from ``point`` to ``col_obj`` bound box.
    ``point`` and ``point_normal`` must be in world space.

    Returns tuple (offset_front, offset_back).
    """
    from mathutils.geometry import distance_point_to_plane, normal

    def _get_plane(a: Vector, b: Vector, c: Vector, d: Vector):
        plane_no = normal((a, b, c))
        plane_co = a
        return plane_co, plane_no

    bbs = [col_obj.matrix_world @ Vector(corner) for corner in col_obj.bound_box]

    # bound box corners:
    #  [0] = (min.x, min.y, min.z)
    #  [1] = (min.x, min.y, max.z)
    #  [2] = (min.x, max.y, max.z)
    #  [3] = (min.x, max.y, min.z)
    #  [4] = (max.x, min.y, min.z)
    #  [5] = (max.x, min.y, max.z)
    #  [6] = (max.x, max.y, max.z)
    #  [7] = (max.x, max.y, min.z)
    plane_points = (
        (bbs[4], bbs[3], bbs[0], bbs[7]),  # bottom
        (bbs[1], bbs[2], bbs[5], bbs[7]),  # top
        (bbs[2], bbs[1], bbs[0], bbs[3]),  # left
        (bbs[4], bbs[5], bbs[6], bbs[7]),  # right
        (bbs[0], bbs[1], bbs[4], bbs[5]),  # front
        (bbs[2], bbs[3], bbs[6], bbs[7]),  # back
    )
    planes = [_get_plane(Vector(a), Vector(b), Vector(c), Vector(d)) for a, b, c, d in plane_points]

    offset_front = 0.0
    offset_front_dot = 0.0
    offset_back = 0.0
    offset_back_dot = 0.0
    for plane_co, plane_no in planes:
        d = point_normal.dot(plane_no)
        if d > offset_front_dot:  # positive dot product is the plane with same normal as the point (in front)
            offset_front_dot = d
            offset_front = distance_point_to_plane(point, plane_co, plane_no)
        elif d < offset_back_dot:  # negative dot product is the plane with opposite normal as the point (behind)
            offset_back_dot = d
            offset_back = distance_point_to_plane(point, plane_co, plane_no)

    return offset_front, offset_back


def create_dummy_frag_physics_for_cloth(frag_objs: FragmentObjects, materials: list[Material]) -> PhysLodGroup:
    frag_obj = frag_objs.fragment

    vec3_zero = Vector((0.0, 0.0, 0.0))
    vec3_zero.freeze()
    vec4_zero = Vector((0.0, 0.0, 0.0, 0.0))
    vec4_zero.freeze()

    groups, _ = create_frag_phys_groups(frag_objs, materials)
    groups[0].total_mass = 1.0
    child = PhysChild(
        bone_tag=0,
        group_index=0,
        pristine_mass=1.0,
        damaged_mass=1.0,
        drawable=create_frag_phys_child_drawable(None, materials),
        damaged_drawable=None,
        min_breaking_impulse=0.0,
        inertia=vec4_zero,
        damaged_inertia=vec4_zero,
    )

    composite = create_asset_bound(export_context().settings.targets, BoundType.COMPOSITE)
    # Cloths with no bounds seem to always have 2 null bounds in the composite
    # Doesn't seem to be needed, but do it for consistency with original assets
    composite.children = [None, None]
    composite.extent = vec3_zero, vec3_zero
    composite.centroid = vec3_zero
    composite.radius_around_centroid = 0.0
    composite.volume = 1.0
    composite.cg = vec3_zero
    composite.inertia = Vector((1.0, 1.0, 1.0))
    composite.margin = 0.0

    lod_props: LODProperties = frag_obj.fragment_properties.lod_properties
    archetype_props: FragArchetypeProperties = lod_props.archetype_properties
    archetype_name = remove_number_suffix(frag_obj.name)
    archetype = create_frag_phys_archetype(archetype_props, archetype_name, [], composite, vec3_zero)
    lod = PhysLod(
        archetype=archetype,
        damaged_archetype=None,
        children=[child],
        groups=groups,
        smallest_ang_inertia=0.0,
        largest_ang_inertia=0.0,
        min_move_force=lod_props.min_move_force,
        root_cg_offset=vec3_zero,
        original_root_cg_offset=vec3_zero,
        unbroken_cg_offset=vec3_zero,
        damping_linear_c=Vector(lod_props.damping_linear_c),
        damping_linear_v=Vector(lod_props.damping_linear_v),
        damping_linear_v2=Vector(lod_props.damping_linear_v2),
        damping_angular_c=Vector(lod_props.damping_angular_c),
        damping_angular_v=Vector(lod_props.damping_angular_v),
        damping_angular_v2=Vector(lod_props.damping_angular_v2),
        link_attachments=[],
    )

    return PhysLodGroup(lod)
