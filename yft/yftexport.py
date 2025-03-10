import bpy
from bpy.types import (
    Object
)
from typing import Optional, Tuple, NamedTuple
from collections import defaultdict
from itertools import combinations, zip_longest
from mathutils import Matrix, Vector
from bpy_extras.mesh_utils import mesh_linked_triangles
from sys import float_info
import numpy as np

from ..ybn.ybnexport import create_composite_xml, get_scale_to_apply_to_bound
from ..cwxml.bound import Bound, BoundComposite
from ..cwxml.fragment import (
    Fragment, PhysicsLOD, Archetype, PhysicsChild, PhysicsGroup, Transform, Physics, BoneTransform, Window,
    GlassWindow, GlassWindows,
)
from ..cwxml.drawable import Bone, Drawable, VertexLayoutList
from ..tools.blenderhelper import get_evaluated_obj, remove_number_suffix, delete_hierarchy, get_child_of_bone
from ..tools.fragmenthelper import image_to_shattermap
from ..tools.meshhelper import flip_uvs
from ..tools.utils import prop_array_to_vector, reshape_mat_4x3, vector_inv, reshape_mat_3x4
from ..sollumz_helper import get_parent_inverse, get_sollumz_materials
from ..sollumz_properties import BOUND_TYPES, SollumType, MaterialType, LODLevel
from ..sollumz_preferences import get_export_settings
from ..ybn.ybnexport import has_col_mats, bound_geom_has_mats
from ..ydr.ydrexport import create_drawable_xml, write_embedded_textures, get_bone_index, create_model_xml, append_model_xml, set_drawable_xml_extents
from ..ydr.lights import create_xml_lights
from .. import logger
from .properties import (
    LODProperties, FragArchetypeProperties, GroupProperties,
    GroupFlagBit, get_glass_type_index,
    FragmentTemplateAsset,
)


def export_yft(frag_obj: Object, filepath: str) -> bool:
    export_settings = get_export_settings()

    frag = locate_fragment_objects(frag_obj)
    if frag is None:
        return False

    frag_xml = create_fragment_xml(frag, export_settings.apply_transforms)
    if frag_xml is None:
        return False

    if export_settings.export_non_hi:
        frag_xml.write_xml(filepath)
        write_embedded_textures(frag_obj, filepath)

    if export_settings.export_hi and has_hi_lods(frag_obj):
        hi_filepath = filepath.replace(".yft.xml", "_hi.yft.xml")

        hi_frag_xml = create_hi_frag_xml(frag, frag_xml, export_settings.apply_transforms)
        hi_frag_xml.write_xml(hi_filepath)

        write_embedded_textures(frag_obj, hi_filepath)
        logger.info(f"Exported Very High LODs to '{hi_filepath}'")
    elif export_settings.export_hi and not export_settings.export_non_hi:
        logger.warning(f"Only Very High LODs selected to export but fragment '{frag_obj.name}' does not have Very High"
                       " LODs. Nothing was exported.")
        return False

    return True


class FragmentObjects(NamedTuple):
    """Contains the important Blender objects in a fragment hierarchy."""
    fragment: Object
    drawable: Object
    composite: Optional[Object]
    damaged_drawable: Optional[Object]
    damaged_composite: Optional[Object]

    @property
    def has_collisions(self) -> bool:
        return self.composite is not None


def locate_fragment_objects(frag: Object) -> Optional[FragmentObjects]:
    """Explore the fragment hierarchy looking for the important objects (drawables, bound composites). Returns ``None``
    if there are missing objects such that the export process would not be able to continue.
    """
    assert frag.sollum_type == SollumType.FRAGMENT
    if frag.type != "ARMATURE":
        logger.warning(f"Fragment '{frag.name}' must have an armature!")
        return None

    drawables = []
    damaged_drawables = []
    composites = []
    damaged_composites = []

    for obj in frag.children:
        match obj.sollum_type:
            case SollumType.DRAWABLE:
                if ".damaged" in obj.name:
                    damaged_drawables.append(obj)
                else:
                    drawables.append(obj)
            case SollumType.BOUND_COMPOSITE:
                if ".damaged" in obj.name:
                    damaged_composites.append(obj)
                else:
                    composites.append(obj)
            case _:
                continue

    if not drawables:
        logger.warning(f"Fragment '{frag.name}' must have a Drawable!")
        return None

    drawable, *bad_drawables = drawables
    if bad_drawables:
        bad_drawables_names = (f"'{d.name}'" for d in bad_drawables)
        logger.warning(
            f"Fragment '{frag.name}' has multiple Drawables! Fragments only support a single drawable. Only "
            f"'{drawable.name}' will be exported, other drawables will be ignored ({', '.join(bad_drawables_names)}). "
            f"Please, remove them or combine their meshes."
        )

    if damaged_drawables:
        damaged_drawable, *bad_damaged_drawables = damaged_drawables
        if bad_damaged_drawables:
            bad_damaged_drawables_names = (f"'{d.name}'" for d in bad_damaged_drawables)
            logger.warning(
                f"Fragment '{frag.name}' has multiple damaged Drawables! Fragments only support a single damaged "
                f"drawable. Only '{damaged_drawable.name}' will be exported, other damaged drawables will be ignored "
                f"({', '.join(bad_damaged_drawables_names)}). Please, remove them or combine their meshes."
            )
    else:
        damaged_drawable = None

    if composites:
        composite, *bad_composites = composites
        if bad_composites:
            bad_composites_names = (f"'{d.name}'" for d in bad_composites)
            logger.warning(
                f"Fragment '{frag.name}' has multiple Bound Composites! Fragments only support a single bound "
                f"composite. Only '{composite.name}' will be exported, other bound composites will be ignored "
                f"({', '.join(bad_composites_names)}). Please, remove them or combine their child bounds."
            )
    else:
        composite = None

    if damaged_composites:
        damaged_composite, *bad_damaged_composites = damaged_composites
        if bad_damaged_composites:
            bad_damaged_composites_names = (f"'{d.name}'" for d in bad_damaged_composites)
            logger.warning(
                f"Fragment '{frag.name}' has multiple damaged Bound Composites! Fragments only support a single "
                f"damaged bound composite. Only '{damaged_composite.name}' will be exported, other damaged bound "
                f"composites will be ignored ({', '.join(bad_damaged_composites_names)}). Please, remove them or "
                f"combine their child bounds."
            )
    else:
        damaged_composite = None

    return FragmentObjects(frag, drawable, composite, damaged_drawable, damaged_composite)


def create_fragment_xml(frag: FragmentObjects, apply_transforms: bool = False) -> Optional[Fragment]:
    """Create an XML parsable Fragment object. Returns the XML object and the hi XML object (if hi lods are present)."""
    frag_obj = frag.fragment

    frag_xml = Fragment()
    frag_xml.name = f"pack:/{remove_number_suffix(frag_obj.name)}"
    frag_xml.flags = 1  # all fragments need this flag (uses cache entry)

    set_frag_xml_properties(frag_obj, frag_xml)

    materials = get_sollumz_materials(frag_obj)
    drawable_xml = create_frag_drawable_xml(frag, materials, apply_transforms)

    frag_armature = frag_obj.data
    original_pose = frag_armature.pose_position
    frag_armature.pose_position = "REST"

    frag_xml.bounding_sphere_center = drawable_xml.bounding_sphere_center
    frag_xml.bounding_sphere_radius = drawable_xml.bounding_sphere_radius

    frag_xml.drawable = drawable_xml

    if frag.damaged_drawable is not None:
        frag_xml.extra_drawables = [create_frag_damaged_drawable_xml(frag, materials, apply_transforms)]

    if frag_armature.bones:
        create_bone_transforms_xml(frag_xml)

    # Physics data doesn't do anything if no collisions are present and will cause crashes
    if frag.has_collisions and frag_armature.bones:
        create_frag_physics_xml(frag, frag_xml, materials)
        create_vehicle_windows_xml(frag_obj, frag_xml, materials)
    else:
        frag_xml.physics = None

    frag_xml.lights = create_xml_lights(frag_obj)

    frag_armature.pose_position = original_pose

    return frag_xml


def create_frag_drawable_xml(frag: FragmentObjects, materials: list[bpy.types.Material], apply_transforms: bool = False) -> Drawable:
    drawable_xml = create_drawable_xml(
        frag.drawable, materials=materials, armature_obj=frag.fragment, apply_transforms=apply_transforms
    )
    drawable_xml.name = "skel"
    return drawable_xml


def create_frag_damaged_drawable_xml(frag: FragmentObjects, materials: list[bpy.types.Material], apply_transforms: bool = False) -> Drawable:
    assert frag.damaged_drawable is not None, "Caller must ensure that there is a damaged drawable"
    drawable_xml = create_drawable_xml(
        frag.damaged_drawable, materials=materials, armature_obj=frag.fragment, apply_transforms=apply_transforms
    )
    drawable_xml.name = "damaged"
    # uses the shader group and skeleton of the main drawable
    drawable_xml.shader_group = None
    drawable_xml.skeleton = None
    return drawable_xml


def create_hi_frag_xml(frag: FragmentObjects, frag_xml: Fragment, apply_transforms: bool = False):
    hi_obj = frag.fragment.copy()
    hi_obj.name = f"{remove_number_suffix(hi_obj.name)}_hi"
    bpy.context.collection.objects.link(hi_obj)

    drawable_obj = copy_hierarchy(frag.drawable, hi_obj)
    drawable_obj.parent = hi_obj
    remove_non_hi_lods(drawable_obj)
    hi_frag = FragmentObjects(hi_obj, drawable_obj, None, None, None)

    materials = get_sollumz_materials(hi_obj)
    hi_drawable = create_frag_drawable_xml(hi_frag, materials, apply_transforms)

    hi_frag_xml = Fragment()
    hi_frag_xml.__dict__ = frag_xml.__dict__.copy()
    hi_frag_xml.drawable = hi_drawable
    hi_frag_xml.vehicle_glass_windows = None

    if hi_frag_xml.physics is not None:
        # Physics children drawables are copied over from non-hi to the hi frag. Therefore, they have high, med and low
        # lods but we need the very high lods in the hi frag XML. Here we remove the existing lods and recreate the
        # drawables with the very high lods.
        # NOTE: we are doing a shallow copy, so we are modifying the original physics children here. This is fine
        # because`frag_xml` is not used after this call during YFT export, but if eventually we need to use it,
        # we should change to a deep copy.
        bones = hi_frag_xml.drawable.skeleton.bones
        child_meshes = get_child_meshes(hi_frag)
        groups_with_child_mesh = set()
        for child_xml in hi_frag_xml.physics.lod1.children:
            drawable = child_xml.drawable
            drawable.drawable_models_high.clear()
            drawable.drawable_models_med.clear()
            drawable.drawable_models_low.clear()
            drawable.drawable_models_vlow.clear()

            bone_tag = child_xml.bone_tag
            bone_name = None
            for bone in bones:
                if bone.tag == bone_tag:
                    bone_name = bone.name
                    break

            group_index = child_xml.group_index
            mesh_objs = None
            if bone_name in child_meshes and group_index not in groups_with_child_mesh:
                mesh_objs = child_meshes[bone_name]
                groups_with_child_mesh.add(group_index)  # only one child per group should have the mesh

            create_phys_child_drawable(child_xml, materials, mesh_objs)

    delete_hierarchy(hi_obj)

    return hi_frag_xml


def copy_hierarchy(obj: Object, armature_obj: Object):
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


def remove_non_hi_lods(drawable_obj: Object):
    for model_obj in drawable_obj.children:
        if model_obj.sollum_type != SollumType.DRAWABLE_MODEL:
            continue

        lods = model_obj.sz_lods
        very_high_lod = lods.get_lod(LODLevel.VERYHIGH)

        if very_high_lod.mesh is None:
            bpy.data.objects.remove(model_obj)
            continue

        lods.get_lod(LODLevel.HIGH).mesh = very_high_lod.mesh
        lods.active_lod_level = LODLevel.HIGH

        for lod_level in LODLevel:
            if lod_level == LODLevel.HIGH:
                continue
            lod = lods.get_lod(lod_level)
            if lod.mesh is not None:
                lod.mesh = None


def has_hi_lods(frag_obj: Object):
    for child in frag_obj.children_recursive:
        if child.sollum_type != SollumType.DRAWABLE_MODEL and not child.sollumz_is_physics_child_mesh:
            continue

        very_high_lod = child.sz_lods.get_lod(LODLevel.VERYHIGH)
        if very_high_lod.mesh is not None:
            return True

    return False


def sort_cols_and_children(lod_xml: PhysicsLOD):
    children_by_group: dict[int, list[int]] = defaultdict(list)

    children = lod_xml.children

    if not children:
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
    for composite in (
        lod_xml.archetype.bounds,
        lod_xml.damaged_archetype.bounds if lod_xml.damaged_archetype else None
    ):
        if composite is None:
            continue

        bounds = composite.children
        sorted_collisions: list[Bound] = [None] * len(indices)

        for old_index, new_index in indices.items():
            sorted_collisions[new_index] = bounds[old_index]

        composite.children = sorted_collisions


def create_frag_physics_xml(frag: FragmentObjects, frag_xml: Fragment, materials: list[bpy.types.Material]):
    frag_obj = frag.fragment
    lod_props: LODProperties = frag_obj.fragment_properties.lod_properties
    drawable_xml = frag_xml.drawable

    lod_xml = create_phys_lod_xml(frag_xml.physics, lod_props)
    arch_xml, damaged_arch_xml = create_archetype_xml(lod_xml, frag)
    col_obj_to_bound_index = dict()
    composite_xml, damaged_composite_xml = create_collision_xml(frag, lod_xml, col_obj_to_bound_index)

    create_phys_xml_groups(frag_obj, lod_xml, frag_xml.glass_windows, materials)
    create_phys_child_xmls(frag, frag_xml, drawable_xml.skeleton.bones, materials, col_obj_to_bound_index)
    if not lod_xml.children:
        # The operations after this expect to have at least one physics child, so don't continue if we couldn't
        # create any children to avoid errors like division by zero. Previous functions should have already reported
        # any errors/warnings that caused them not to create the children so don't need to report anything here, just
        # exit early.
        return

    calculate_group_masses(lod_xml)
    calculate_child_drawable_matrices(frag_xml)

    sort_cols_and_children(lod_xml)

    calculate_physics_lod_transforms(frag_xml)
    calculate_archetype_mass_inertia(lod_xml)
    if damaged_composite_xml:
        calculate_archetype_mass_inertia(lod_xml, damaged=True)
    calculate_physics_lod_inertia_limits(lod_xml)


def create_phys_lod_xml(phys_xml: Physics, lod_props: LODProperties):
    set_lod_xml_properties(lod_props, phys_xml.lod1)
    phys_xml.lod2 = None
    phys_xml.lod3 = None

    return phys_xml.lod1


def calculate_physics_lod_inertia_limits(lod_xml: PhysicsLOD):
    """Calculates the physics LOD smallest and largest angular inertia from its children."""
    phys_children = lod_xml.children
    inertia_values = [
        value
        for c in phys_children
        for inertia in (c.inertia_tensor, c.damaged_inertia_tensor)
        for value in inertia.xyz
    ]
    largest_inertia = max(inertia_values)
    smallest_inertia = largest_inertia / 10000.0  # game assets always have same value as largest divided by 10000

    # unknown_14 = smallest angular inertia
    # unknown_18 = largest angular inertia
    lod_xml.unknown_14 = smallest_inertia
    lod_xml.unknown_18 = largest_inertia


def create_archetype_xml(lod_xml: PhysicsLOD, frag: FragmentObjects) -> tuple[Archetype, Optional[Archetype]]:
    frag_obj = frag.fragment
    archetype_props: FragArchetypeProperties = frag_obj.fragment_properties.lod_properties.archetype_properties
    archetype_name = remove_number_suffix(frag_obj.name)

    set_archetype_xml_properties(archetype_props, lod_xml.archetype, archetype_name)

    if frag.damaged_composite is not None:
        set_archetype_xml_properties(archetype_props, lod_xml.damaged_archetype, archetype_name)
    else:
        lod_xml.damaged_archetype = None

    return lod_xml.archetype, lod_xml.damaged_archetype


def calculate_archetype_mass_inertia(lod_xml: PhysicsLOD, damaged: bool = False):
    """Set archetype mass and inertia based on children mass and bounds. Expects physics children and collisions to
    exist, and the physics LOD root CG to have already been calculted.
    """

    from ..shared.geometry import calculate_composite_inertia
    arch_xml = lod_xml.damaged_archetype if damaged else lod_xml.archetype
    phys_children = lod_xml.children
    bounds = arch_xml.bounds.children
    # Filter out children with null bounds
    phys_children, bounds = zip(*((c, b) for c, b in zip(phys_children, bounds) if b is not None))
    masses = [child_xml.damaged_mass if damaged else child_xml.pristine_mass for child_xml in phys_children]
    inertias = [(child_xml.damaged_inertia_tensor if damaged else child_xml.inertia_tensor).xyz for child_xml in phys_children]
    cgs = [bound_xml.composite_transform.transposed() @ bound_xml.sphere_center for bound_xml in bounds]
    mass = sum(masses)
    inertia = calculate_composite_inertia(lod_xml.position_offset, cgs, masses, inertias)

    arch_xml.mass = mass
    arch_xml.mass_inv = (1 / mass) if mass != 0 else 0
    arch_xml.inertia_tensor = inertia
    arch_xml.inertia_tensor_inv = vector_inv(inertia)


def create_collision_xml(
    frag: FragmentObjects,
    lod_xml: PhysicsLOD,
    col_obj_to_bound_index: dict[Object, int]
) -> tuple[BoundComposite, Optional[BoundComposite]]:
    assert frag.composite is not None, "Caller must ensure that there is a composite"

    composite_xml = create_composite_xml(frag.composite, col_obj_to_bound_index)
    lod_xml.archetype.bounds = composite_xml
    all_bounds = (composite_xml, *composite_xml.children)

    if frag.damaged_composite is not None:
        assert lod_xml.damaged_archetype is not None, "Caller must ensure that the damaged archetype already exists"
        damaged_col_obj_to_bound_index = {}
        damaged_composite_xml = create_composite_xml(frag.damaged_composite, damaged_col_obj_to_bound_index)
        lod_xml.damaged_archetype.bounds = damaged_composite_xml
        all_bounds = (*all_bounds, damaged_composite_xml, *damaged_composite_xml.children)

        # With damaged fragments we have to make space in both composites to fit all bounds (both damaged and undamaged)
        # so indices remain consistent between them. Extra spaces are just left empty (none)
        composite_xml.children = composite_xml.children + [None] * len(damaged_composite_xml.children)
        damaged_composite_xml.children = [None] * len(composite_xml.children) + damaged_composite_xml.children

        # Include the damaged bounds in the output obj->index mapping
        for damaged_col_obj, bound_index in damaged_col_obj_to_bound_index.items():
            col_obj_to_bound_index[damaged_col_obj] = bound_index + len(composite_xml.children)
    else:
        damaged_composite_xml = None

    # In fragments, every bound is referenced twice:
    # - Composite: in the physics LOD and the archetype
    # - Damaged composite: only in the damaged archetype, but the game still expects 2 refs (and does indeed release it
    #                      twice in the physics LOD destructor)
    # - All child bounds: in the composite and in the physics child drawable
    for bound_xml in all_bounds:
        bound_xml.ref_count = 2

    return composite_xml, damaged_composite_xml


def create_phys_xml_groups(
    frag_obj: bpy.types.Object,
    lod_xml: PhysicsLOD,
    glass_windows_xml: GlassWindows,
    materials: list[bpy.types.Material]
):
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
        group_xml.name = bone.name
        bone_index = get_bone_index(frag_obj.data, bone)

        groups_by_bone[bone_index].append(group_xml)
        set_group_xml_properties(bone.group_properties, group_xml)

        if bone.group_properties.flags[GroupFlagBit.USE_GLASS_WINDOW]:
            add_frag_glass_window_xml(frag_obj, bone, materials, group_xml, glass_windows_xml)

    # Sort by bone index
    groups_by_bone = dict(sorted(groups_by_bone.items()))

    for groups in groups_by_bone.values():
        for group_xml in groups:
            i = len(group_ind_by_name)

            group_ind_by_name[group_xml.name] = i

    def get_group_parent_index(group_bone: bpy.types.Bone) -> int:
        """Returns parent group index or 255 if there is no parent."""
        parent_bone = group_bone.parent
        if parent_bone is None:
            return 255

        if not parent_bone.sollumz_use_physics or parent_bone.name not in group_ind_by_name:
            # Parent has no frag group, try with grandparent
            return get_group_parent_index(parent_bone)

        return group_ind_by_name[parent_bone.name]

    # Set group parent indices
    for bone_index, groups in groups_by_bone.items():
        parent_index = get_group_parent_index(frag_obj.data.bones[bone_index])

        for group_xml in groups:
            group_xml.parent_index = parent_index

            group_ind_by_name[group_xml.name] = len(lod_xml.groups)

            lod_xml.groups.append(group_xml)

    return lod_xml.groups


def does_bone_have_collision(bone_name: str, frag_obj: Object):
    col_objs = [obj for obj in frag_obj.children_recursive if obj.sollum_type in BOUND_TYPES]

    for obj in col_objs:
        bone = get_child_of_bone(obj)

        if bone is not None and bone.name == bone_name:
            return True

    return False


def calculate_group_masses(lod_xml: PhysicsLOD):
    """Calculate the mass of all groups in ``lod_xml`` based on child masses. Expects physics children to exist."""
    for child in lod_xml.children:
        lod_xml.groups[child.group_index].mass += child.pristine_mass


def calculate_physics_lod_transforms(frag_xml: Fragment):
    """Calculate ``frag_xml.physics.lod1.transforms``. A transformation matrix per physics child that represents
    the offset from the child collision bound to its link center of gravity (aka "link attachment"). A link is
    formed by physics groups that act as a rigid body together, a group with a joint creates a new link.
    Also calculates the physics LOD root CG offset.
    """

    lod_xml = frag_xml.physics.lod1
    bones_xml = frag_xml.drawable.skeleton.bones
    rotation_limits = frag_xml.drawable.joints.rotation_limits
    translation_limits = frag_xml.drawable.joints.translation_limits

    children_by_group: dict[PhysicsGroup, list[tuple[int, PhysicsChild]]] = defaultdict(list)
    for child_index, child in enumerate(lod_xml.children):
        group = lod_xml.groups[child.group_index]
        children_by_group[group].append((child_index, child))

    # Array of links (i.e. array of arrays of groups)
    links = [[]]  # the root link is at index 0
    link_index_by_group = [-1] * len(lod_xml.groups)

    # Determine the groups that form each link
    for group_index, group in enumerate(lod_xml.groups):
        link_index = 0  # by default add to root link

        if group.parent_index != 255:
            _, first_child = children_by_group[group][0]
            bone = next(b for b in bones_xml if b.tag == first_child.bone_tag)
            creates_new_link = (
                ("LimitRotation" in bone.flags and any(rl.bone_id == bone.tag for rl in rotation_limits)) or
                ("LimitTranslation" in bone.flags and any(tl.bone_id == bone.tag for tl in translation_limits))
            )
            if creates_new_link:
                # There is a joint, create a new link
                link_index = len(links)
                links.append([])
            else:
                # Add to link of parent group
                link_index = link_index_by_group[group.parent_index]

        links[link_index].append(group)
        link_index_by_group[group_index] = link_index

    if len(links) > 1:
        frag_xml.flags |= 2  # set 'is articulated' flag

    # Calculate center of gravity of each link. This is the weighted mean of the center of gravity of all physics
    # children that form the link.
    links_center_of_gravity = [Vector((0.0, 0.0, 0.0)) for _ in range(len(links))]
    for link_index, groups in enumerate(links):
        link_total_mass = 0.0
        for group_index, group in enumerate(groups):
            for child_index_rel, (child_index, child) in enumerate(children_by_group[group]):
                bound = lod_xml.archetype.bounds.children[child_index]
                if bound is not None:
                    # sphere_center is the center of gravity
                    center = bound.composite_transform.transposed() @ bound.sphere_center
                else:
                    center = Vector((0.0, 0.0, 0.0))

                child_mass = child.pristine_mass
                links_center_of_gravity[link_index] += center * child_mass
                link_total_mass += child_mass

        if link_total_mass > 0.0:
            links_center_of_gravity[link_index] /= link_total_mass

    # add the user-defined unbroken CG offset to the root CG offset
    links_center_of_gravity[0] += lod_xml.unknown_50

    lod_xml.position_offset = links_center_of_gravity[0]  # aka "root CG offset"
    lod_xml.unknown_40 = lod_xml.position_offset  # aka "original root CG offset", same as root CG offset in all game .yfts
    lod_xml.archetype.bounds.sphere_center = lod_xml.position_offset  # the physics LOD CG overrides the composite CG

    # Calculate child transforms (aka "link attachments", offset from bound to link CG)
    for child_index, child in enumerate(lod_xml.children):
        # print(f"#{child_index} ({child.bone_tag}) link_index={link_index_by_group[child.group_index]}")
        link_center = links_center_of_gravity[link_index_by_group[child.group_index]]
        bound = lod_xml.archetype.bounds.children[child_index]
        if bound is not None:
            offset = Matrix.Translation(-link_center) @ bound.composite_transform.transposed()
            offset.transpose()
        else:
            offset = Matrix.Identity(4)

        # It is a 3x4 matrix, so zero out the 4th column to be consistent with original matrices
        # (doesn't really matter but helps with equality checks in our tests)
        offset.col[3].zero()

        lod_xml.transforms.append(Transform("Item", offset))


def create_phys_child_xmls(
    frag: FragmentObjects,
    frag_xml: Fragment,
    bones_xml: list[Bone],
    materials: list[bpy.types.Material],
    col_obj_to_bound_index: dict[Object, int]
):
    """Creates the physics children XML objects for each collision object and adds them to ``lod_xml.children``.

    Additionally, makes sure that ``lod_xml.archetype.bounds.children`` order matches ``lod_xml.children`` order so
    the same indices can be used with both collections.
    """
    frag_obj = frag.fragment
    frag_armature = frag_obj.data
    lod_xml = frag_xml.physics.lod1
    child_meshes = get_child_meshes(frag)
    child_cols = get_child_cols(frag)
    damaged_child_cols = get_child_cols(frag, damaged=True) if frag.damaged_composite else {}

    groups_with_child_mesh = set()
    bound_index_to_child_index = []
    damaged_bound_index_to_child_index = []
    for bone_name, col_objs in child_cols.items():
        damaged_col_objs = damaged_child_cols.get(bone_name, [])
        for col_obj, damaged_col_obj in zip_longest(col_objs, damaged_col_objs, fillvalue=None):
            child_index = len(lod_xml.children)
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
            group_index = get_bone_group_index(lod_xml, bone_name)

            child_xml = PhysicsChild()
            child_xml.group_index = group_index
            child_xml.pristine_mass = col_obj.child_properties.mass if col_obj else 0.0
            child_xml.damaged_mass = damaged_col_obj.child_properties.mass if damaged_col_obj else child_xml.pristine_mass
            child_xml.bone_tag = bones_xml[bone_index].tag
            child_xml.inertia_tensor = \
                calc_child_inertia(lod_xml, child_xml, bound_index) \
                if col_obj else Vector((0.0, 0.0, 0.0, 0.0))
            child_xml.damaged_inertia_tensor = \
                calc_child_inertia(lod_xml, child_xml, damaged_bound_index, damaged=True) \
                if damaged_col_obj else Vector((0.0, 0.0, 0.0, 0.0))

            mesh_objs = None
            if bone_name in child_meshes and group_index not in groups_with_child_mesh:
                mesh_objs = child_meshes[bone_name]
                groups_with_child_mesh.add(group_index)  # only one child per group should have the mesh

            create_phys_child_drawable(child_xml, materials, mesh_objs)
            if damaged_col_obj:
                create_phys_child_drawable(child_xml, materials, damaged=True)
            else:
                child_xml.damaged_drawable = None

            if child_xml.drawable.all_models:
                frag_xml.flags |= 64  # flag for vehicles, seems unused at runtime though

            lod_xml.children.append(child_xml)

    # reorder bounds children based on physics children order
    composite = lod_xml.archetype.bounds
    damaged_composite = lod_xml.damaged_archetype.bounds if lod_xml.damaged_archetype else None
    for comp, index_map in (
        (composite, bound_index_to_child_index),
        (damaged_composite, damaged_bound_index_to_child_index)
    ):
        if comp is None:
            continue

        bounds = comp.children
        new_bounds = [None] * len(lod_xml.children)
        for bound_index, child_index in index_map:
            new_bounds[child_index] = bounds[bound_index]

        comp.children = new_bounds


def calc_child_inertia(lod_xml: PhysicsLOD, child_xml: PhysicsChild, bound_index: int, damaged: bool = False):
    arch_xml = lod_xml.damaged_archetype if damaged else lod_xml.archetype
    if not arch_xml.bounds or bound_index >= len(arch_xml.bounds.children):
        return Vector()

    bound_xml = arch_xml.bounds.children[bound_index]
    mass = child_xml.damaged_mass if damaged else child_xml.pristine_mass
    inertia = bound_xml.inertia * mass
    return Vector((inertia.x, inertia.y, inertia.z, bound_xml.volume * mass))


def get_child_cols(frag: FragmentObjects, damaged: bool = False) -> dict[str, list[Object]]:
    """Get collisions that are linked to a child. Returns a dict mapping each collision to a bone name."""
    composite_obj = frag.damaged_composite if damaged else frag.composite
    assert composite_obj is not None, "Caller must ensure that there is a composite"

    child_cols_by_bone: dict[str, list[Object]] = defaultdict(list)
    for bound_obj in composite_obj.children:
        if bound_obj.sollum_type not in BOUND_TYPES:
            continue

        if (bound_obj.type == "MESH" and not has_col_mats(bound_obj)) or (bound_obj.type == "EMPTY" and not bound_geom_has_mats(bound_obj)):
            continue

        bone = get_child_of_bone(bound_obj)

        if bone is None or not bone.sollumz_use_physics:
            continue

        child_cols_by_bone[bone.name].append(bound_obj)

    return child_cols_by_bone


def get_child_meshes(frag: FragmentObjects) -> dict[str, list[Object]]:
    """Get meshes that are linked to a child. Returns a dict mapping child meshes to bone name."""
    drawable_obj = frag.drawable
    child_meshes_by_bone: dict[str, list[Object]] = defaultdict(list)
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


def create_child_mat_arrays(lod_xml: PhysicsLOD):
    """Create the matrix arrays for each child. This appears to be in the first child of multiple children that
    share the same group. Each matrix in the array is just the matrix for each child in that group."""
    children = lod_xml.children
    bounds = lod_xml.archetype.bounds.children
    damaged_bounds = lod_xml.damaged_archetype.bounds.children if lod_xml.damaged_archetype else None
    group_inds = set(child.group_index for child in children)

    for i in group_inds:
        group_children = [(child_index, child) for child_index, child in enumerate(children) if child.group_index == i]

        if len(group_children) <= 1:
            continue

        _, first = group_children[0]

        for child_index, child in group_children[1:]:
            if bounds[child_index]:
                first.drawable.frag_extra_bound_matrices.append(child.drawable.frag_bound_matrix)
            if damaged_bounds and damaged_bounds[child_index]:
                first.damaged_drawable.frag_extra_bound_matrices.append(child.damaged_drawable.frag_bound_matrix)


def create_phys_child_drawable(child_xml: PhysicsChild, materials: list[bpy.types.Object], mesh_objs: Optional[list[bpy.types.Object]] = None, damaged: bool = False):
    drawable_xml = child_xml.damaged_drawable if damaged else child_xml.drawable
    drawable_xml.shader_group = None
    drawable_xml.skeleton = None
    drawable_xml.joints = None

    if not mesh_objs:
        return drawable_xml

    for obj in mesh_objs:
        scale = get_scale_to_apply_to_bound(obj)
        transforms_to_apply = Matrix.Diagonal(scale).to_4x4()

        lods = obj.sz_lods
        for lod_level in LODLevel:
            if lod_level == LODLevel.VERYHIGH:
                continue
            lod_mesh = lods.get_lod(lod_level).mesh
            if lod_mesh is None:
                continue

            model_xml = create_model_xml(obj, lod_level, materials, transforms_to_apply=transforms_to_apply)
            model_xml.bone_index = 0
            append_model_xml(drawable_xml, model_xml, lod_level)

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
        window_xml.shattermap = image_to_shattermap(shattermap_img)
        window_xml.projection_matrix = calculate_shattermap_projection(shattermap_obj, shattermap_img)


def set_veh_window_xml_properties(window_xml: Window, window_obj: bpy.types.Object):
    window_xml.unk_float_17 = window_obj.vehicle_window_properties.data_min
    window_xml.unk_float_18 = window_obj.vehicle_window_properties.data_max
    window_xml.cracks_texture_tiling = window_obj.vehicle_window_properties.cracks_texture_tiling


def calculate_shattermap_projection(obj: bpy.types.Object, img: bpy.types.Image):
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

    # Create projection matrix relative to parent
    parent_inverse = get_parent_inverse(obj)
    matrix = parent_inverse @ obj.matrix_world @ matrix

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
    damaged_collisions = lod_xml.damaged_archetype.bounds.children if lod_xml.damaged_archetype else None

    bone_transform_by_tag: dict[str, Matrix] = {b.tag: bone_transforms[i].value for i, b in enumerate(bones)}

    for cols in (collisions, damaged_collisions):
        if not cols:
            continue

        for i, child in enumerate(lod_xml.children):
            bone_transform = bone_transform_by_tag[child.bone_tag]

            col = cols[i]
            if not col:
                continue

            bone_inv = bone_transform.to_4x4().inverted()

            matrix = col.composite_transform @ bone_inv.transposed()
            drawable = child.damaged_drawable if cols is damaged_collisions else child.drawable
            drawable.frag_bound_matrix = reshape_mat_4x3(matrix)

    create_child_mat_arrays(lod_xml)


def set_lod_xml_properties(lod_props: LODProperties, lod_xml: PhysicsLOD):
    lod_xml.unknown_1c = lod_props.min_move_force
    lod_xml.unknown_50 = prop_array_to_vector(lod_props.unbroken_cg_offset)
    lod_xml.damping_linear_c = prop_array_to_vector(lod_props.damping_linear_c)
    lod_xml.damping_linear_v = prop_array_to_vector(lod_props.damping_linear_v)
    lod_xml.damping_linear_v2 = prop_array_to_vector(lod_props.damping_linear_v2)
    lod_xml.damping_angular_c = prop_array_to_vector(lod_props.damping_angular_c)
    lod_xml.damping_angular_v = prop_array_to_vector(lod_props.damping_angular_v)
    lod_xml.damping_angular_v2 = prop_array_to_vector(lod_props.damping_angular_v2)


def set_archetype_xml_properties(archetype_props: FragArchetypeProperties, arch_xml: Archetype, frag_name: str):
    arch_xml.name = frag_name
    arch_xml.unknown_48 = archetype_props.gravity_factor
    arch_xml.unknown_4c = archetype_props.max_speed
    arch_xml.unknown_50 = archetype_props.max_ang_speed
    arch_xml.unknown_54 = archetype_props.buoyancy_factor


def set_group_xml_properties(group_props: GroupProperties, group_xml: PhysicsGroup):
    group_xml.glass_window_index = 0
    group_xml.glass_flags = 0
    for i in range(len(group_props.flags)):
        group_xml.glass_flags |= (1 << i) if group_props.flags[i] else 0
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
    group_xml.restoring_strength = group_props.restoring_strength
    group_xml.restoring_max_torque = group_props.restoring_max_torque
    group_xml.latch_strength = group_props.latch_strength
    group_xml.min_damage_force = group_props.min_damage_force
    group_xml.damage_health = group_props.damage_health
    group_xml.unk_float_5c = group_props.weapon_health
    group_xml.unk_float_60 = group_props.weapon_scale
    group_xml.unk_float_64 = group_props.vehicle_scale
    group_xml.unk_float_68 = group_props.ped_scale
    group_xml.unk_float_6c = group_props.ragdoll_scale
    group_xml.unk_float_70 = group_props.explosion_scale
    group_xml.unk_float_74 = group_props.object_scale
    group_xml.unk_float_78 = group_props.ped_inv_mass_scale
    group_xml.unk_float_a8 = group_props.melee_scale


def set_frag_xml_properties(frag_obj: bpy.types.Object, frag_xml: Fragment):
    frag_xml.unknown_b0 = 0  # estimated cache sizes, these are set by the game when the fragCacheEntry is initialized
    frag_xml.unknown_b8 = 0
    frag_xml.unknown_bc = 0
    frag_xml.unknown_c0 = (FragmentTemplateAsset[frag_obj.fragment_properties.template_asset] & 0xFF) << 8
    frag_xml.unknown_cc = frag_obj.fragment_properties.unbroken_elasticity
    frag_xml.gravity_factor = frag_obj.fragment_properties.gravity_factor
    frag_xml.buoyancy_factor = frag_obj.fragment_properties.buoyancy_factor


def add_frag_glass_window_xml(
    frag_obj: bpy.types.Object,
    glass_window_bone: bpy.types.Bone,
    materials: list[bpy.types.Material],
    group_xml: PhysicsGroup,
    glass_windows_xml: GlassWindows
):
    mesh_obj, col_obj = get_frag_glass_window_mesh_and_col(frag_obj, glass_window_bone)
    if mesh_obj is None or col_obj is None:
        logger.warning(f"Glass window '{group_xml.name}' is missing the mesh and/or collision. Skipping...")
        return

    group_xml.glass_window_index = len(glass_windows_xml)

    glass_type = glass_window_bone.group_properties.glass_type
    glass_type_index = get_glass_type_index(glass_type)

    glass_window_xml = GlassWindow()
    glass_window_xml.flags = glass_type_index & 0xFF
    glass_window_xml.layout = VertexLayoutList(type="GTAV4",
                                               value=["Position", "Normal", "Colour0", "TexCoord0", "TexCoord1"])

    glass_windows_xml.append(glass_window_xml)

    # calculate properties from the mesh
    mesh_obj_eval = get_evaluated_obj(mesh_obj)
    mesh = mesh_obj_eval.to_mesh()
    mesh_planes = mesh_linked_triangles(mesh)
    if len(mesh_planes) != 2:
        logger.warning(f"Glass window '{group_xml.name}' requires 2 separate planes in mesh.")
        if len(mesh_planes) < 2:
            return  # need at least 2 planes to continue

    plane_a, plane_b = mesh_planes[:2]
    if len(plane_a) != 2 or len(plane_b) != 2:
        logger.warning(f"Glass window '{group_xml.name}' mesh planes need to be made up of 2 triangles each.")
        if len(plane_a) < 2 or len(plane_b) < 2:
            return  # need at least 2 tris in each plane to continue

    normals = (plane_a[0].normal, plane_a[1].normal, plane_b[0].normal, plane_b[1].normal)
    if any(a.cross(b).length_squared > float_info.epsilon for a, b in combinations(normals, 2)):
        logger.warning(f"Glass window '{group_xml.name}' mesh planes are not parallel.")

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
    projection = Matrix((T, V, U))

    # calculate shader index
    material = mesh.materials[0] if len(mesh.materials) > 0 else None
    if material is not None:
        shader_index = next((i for i, mat in enumerate(materials) if mat == material.original), -1)
    else:
        shader_index = -1

    if shader_index == -1:
        logger.warning(f"Glass window '{group_xml.name}' mesh is missing a material.")

    # calculate bounds offset front/back
    world_transform = mesh_obj_eval.matrix_world
    center_a_world = world_transform @ center_a
    normal_a_world = normals[0].copy()
    normal_a_world.rotate(world_transform)
    bounds_offset_front, bounds_offset_back = calc_frag_glass_window_bounds_offset(col_obj,
                                                                                   center_a_world, normal_a_world)

    mesh_obj_eval.to_mesh_clear()

    glass_window_xml.flags |= (shader_index & 0xFF) << 8
    glass_window_xml.projection_matrix = projection
    glass_window_xml.unk_float_13, glass_window_xml.unk_float_14 = uv_min
    glass_window_xml.unk_float_15, glass_window_xml.unk_float_16 = uv_max
    glass_window_xml.thickness = thickness
    glass_window_xml.unk_float_18 = bounds_offset_front
    glass_window_xml.unk_float_19 = bounds_offset_back
    glass_window_xml.tangent = tangent


def get_frag_glass_window_mesh_and_col(
    frag_obj: bpy.types.Object,
    glass_window_bone: bpy.types.Bone
) -> Tuple[Optional[bpy.types.Object], Optional[bpy.types.Object]]:
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


def calc_frag_glass_window_bounds_offset(
    col_obj: bpy.types.Object,
    point: Vector,
    point_normal: Vector
) -> Tuple[float, float]:
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
