import os
import bpy
from bpy.types import (
    Object,
    Material,
    Image,
    Bone,
    ArmatureBones,
)
import numpy as np
from mathutils import Matrix, Vector, Quaternion
from typing import Optional
from ..tools.blenderhelper import add_child_of_bone_constraint, create_empty_object, material_from_image, create_blender_object
from ..tools.meshhelper import create_uv_attr
from ..tools.utils import multiply_homogeneous, get_filename
from ..sollumz_properties import BOUND_TYPES, SollumType, MaterialType
from szio.gta5 import (
    AssetWithDependencies,
    SkelBone,
    AssetFragment,
    AssetDrawable,
    PhysGroup,
    FragVehicleWindow,
    try_load_asset,
    AssetFormat,
    LodLevel,
)
from ..ydr.ydrimport_io import create_drawable, create_drawable_models, shader_group_to_materials_with_hi, create_armature_obj_from_skel
from ..ybn.ybnimport_io import create_bound_object, create_bound_composite
from ..ydr.lights_io import create_light_objs
from .properties import LODProperties, GroupFlagBit, GlassTypes
from ..tools.blenderhelper import get_child_of_bone
from ..iecontext import import_context
from .. import logger


def find_yft_external_dependencies(asset: AssetFragment, name: str) -> AssetWithDependencies | None:
    prefers_xml = asset.ASSET_FORMAT == AssetFormat.CWXML
    if is_hi_frag(name):
        # User selected a _hi.yft, look for the base .yft file
        non_hi_frag = try_load_non_hi_frag(name, prefers_xml)
        hi_frag = asset
        name = make_frag_base_name(name)

        if not non_hi_frag:
            logger.error("Trying to import a _hi.yft without its base .yft! Please, make sure the non-hi "
                         f"{name}.yft is in the same folder as {name}_hi.yft.")
            return None
    else:
        # User selected the base .yft.xml, optionally look for the _hi.yft.xml
        non_hi_frag = asset
        hi_frag = try_load_hi_frag(name, prefers_xml)

    return AssetWithDependencies(name, non_hi_frag, {"hi": hi_frag} if hi_frag else {})


def import_yft(asset: AssetWithDependencies, name: str) -> Object | None:
    non_hi_frag = asset.main_asset
    hi_frag = asset.dependencies.get("hi", None)

    if import_context().settings.import_as_asset:
        return create_fragment_as_asset(non_hi_frag, hi_frag, name)

    return create_fragment(non_hi_frag, hi_frag, name)


def is_hi_frag(name: str) -> bool:
    """Is this a _hi.yft file?"""
    return name.endswith("_hi")


def make_frag_base_name(name: str) -> str:
    if name.endswith("_hi"):
        name = name[:-3]  # trim '_hi'
    return name


def try_load_non_hi_frag(name: str, prefers_xml: bool) -> AssetFragment | None:
    name = make_frag_base_name(name)
    d = import_context().directory
    non_hi_frag = None

    possible_exts = (".yft", ".yft.xml")
    if prefers_xml:
        possible_exts = possible_exts[::-1]

    for ext in possible_exts:
        non_hi_path = d / f"{name}{ext}"
        if non_hi_path.is_file():
            non_hi_frag = try_load_asset(non_hi_path)
            if non_hi_frag:
                break

    return non_hi_frag


def try_load_hi_frag(name: str, prefers_xml: bool) -> AssetFragment | None:
    name = make_frag_base_name(name)
    d = import_context().directory
    hi_frag = None

    possible_exts = (".yft", ".yft.xml")
    if prefers_xml:
        possible_exts = possible_exts[::-1]

    for ext in possible_exts:
        hi_path = d / f"{name}_hi{ext}"
        if hi_path.is_file():
            hi_frag = try_load_asset(hi_path)
            if hi_frag:
                break

    return hi_frag


def create_fragment(frag: AssetFragment, hi_frag: Optional[AssetFragment], name: Optional[str]) -> Object:
    shader_group = frag.base_drawable.shader_group
    hi_shader_group = hi_frag.base_drawable.shader_group if hi_frag else None

    materials, hi_materials = shader_group_to_materials_with_hi(shader_group, hi_shader_group)

    # Need to append [PAINT_LAYER] extension at the end of the material names
    for mat in set(materials) | set(hi_materials):
        if "matDiffuseColor" in mat.node_tree.nodes:
            from .properties import _update_mat_paint_name
            _update_mat_paint_name(mat)

    frag_obj = create_frag_armature(frag, name)

    drawable_obj = create_frag_drawable(frag, hi_frag, frag_obj,  materials, hi_materials)
    damaged_drawable_obj = create_frag_drawable(frag, hi_frag, frag_obj, materials, hi_materials, damaged=True)

    if frag.physics:
        create_frag_collisions(frag, frag_obj)
        if damaged_drawable_obj is not None:
            create_frag_collisions(frag, frag_obj, damaged=True)

        create_phys_lod(frag, frag_obj)
        apply_phys_groups_to_bones(frag, frag_obj)

        create_phys_child_meshes(frag, hi_frag, frag_obj, drawable_obj, materials, hi_materials)

    create_frag_env_cloth(frag, frag_obj, drawable_obj, materials)

    if import_context().settings.frag_import_vehicle_windows:
        create_frag_vehicle_windows(frag, frag_obj, materials)

    if (lights := frag.lights):
        lights_obj = create_light_objs(lights, frag_obj, f"{frag_obj.name}.lights")
        lights_obj.parent = frag_obj

    return frag_obj


def create_frag_armature(frag: AssetFragment, name: Optional[str] = None) -> Object:
    """Create the fragment armature along with the bones and rotation limits."""
    name = name or frag.name.replace("pack:/", "")
    drawable = frag.base_drawable
    frag_obj = create_armature_obj_from_skel(drawable.skeleton, name, SollumType.FRAGMENT)
    frag_obj.fragment_properties.template_asset = frag.template_asset.name
    frag_obj.fragment_properties.unbroken_elasticity = frag.unbroken_elasticity
    frag_obj.fragment_properties.gravity_factor = frag.gravity_factor
    frag_obj.fragment_properties.buoyancy_factor = frag.buoyancy_factor
    return frag_obj


def create_frag_drawable(
    frag: AssetFragment,
    hi_frag: Optional[AssetFragment],
    frag_obj: Object,
    materials: list[Material],
    hi_materials: list[Material],
    damaged: bool = False
) -> Optional[Object]:
    skip_models = False
    if damaged:
        extra_drawables = frag.extra_drawables
        if not extra_drawables:
            return None

        drawable = extra_drawables[0]
        assert hi_frag is None, "Only vehicles have _hi and they shouldn't have a damaged model"
        hi_drawable = None
        drawable_name = f"{frag_obj.name}.damaged.mesh"
        external_skeleton = frag.base_drawable.skeleton
    else:
        drawable = frag.base_drawable
        hi_drawable = hi_frag.base_drawable if hi_frag else None
        drawable_name = f"{frag_obj.name}.mesh"
        external_skeleton = None

        # If we have a fragment without a main drawable, so base_drawable is the cloth drawable. Don't create cloth
        # models here (skip_models=True). Creating the cloth drawable model will be handled by `create_frag_env_cloth`
        skip_models = frag.drawable is None

    drawable_obj = create_drawable(
        drawable,
        hi_drawable,
        drawable_name,
        materials,
        hi_materials,
        external_armature=frag_obj,
        external_skeleton=external_skeleton,
        skip_models=skip_models,
    )
    drawable_obj.parent = frag_obj

    return drawable_obj


def create_frag_collisions(frag: AssetFragment, frag_obj: Object, damaged: bool = False) -> Optional[Object]:
    lod1 = frag.physics.lod1
    bounds = None
    if damaged:
        bounds = lod1.damaged_archetype.bounds if lod1.damaged_archetype else None
    else:
        bounds = lod1.archetype.bounds

    if bounds is None:
        return None

    bounds_children = bounds.children
    if not bounds_children:
        return None

    col_name_suffix = ".damaged.col" if damaged else ".col"
    composite_name = f"{frag_obj.name}{col_name_suffix}"
    composite_obj = create_empty_object(SollumType.BOUND_COMPOSITE, name=composite_name)
    composite_obj.parent = frag_obj

    for i, bound in enumerate(bounds_children):
        if bound is None:
            continue

        bound_obj = create_bound_object(bound)
        bound_obj.parent = composite_obj

        bone = find_bound_bone(i, frag)
        if bone is None:
            continue

        bound_obj.name = f"{bone.name}{col_name_suffix}"

        if bound_obj.data is not None:
            bound_obj.data.name = bound_obj.name

        phys_child = lod1.children[i]
        bound_obj.child_properties.mass = phys_child.damaged_mass if damaged else phys_child.pristine_mass
        # NOTE: we currently lose damaged mass or pristine mass if the phys child only has a pristine bound or damaged
        # bound, but archetype still use this mass. Is this important?

        add_child_of_bone_constraint(bound_obj, frag_obj, bone.name)
        drawable = phys_child.damaged_drawable if damaged else phys_child.drawable
        bound_obj.matrix_local = drawable.frag_bound_matrix.transposed()


def find_bound_bone(bound_index: int, frag: AssetFragment) -> SkelBone | None:
    """Get corresponding bound bone based on children"""
    children = frag.physics.lod1.children

    if bound_index >= len(children):
        return None

    corresponding_child = children[bound_index]
    for bone in frag.base_drawable.skeleton.bones:
        if bone.tag != corresponding_child.bone_tag:
            continue

        return bone

    return None


def create_phys_lod(frag: AssetFragment, frag_obj: Object):
    """Create the Fragment.Physics.LOD1 data-block. (Currently LOD1 is only supported)"""
    lod = frag.physics.lod1

    if not lod.groups:
        return

    lod_props: LODProperties = frag_obj.fragment_properties.lod_properties
    lod_props.min_move_force = lod.min_move_force
    lod_props.unbroken_cg_offset = lod.unbroken_cg_offset
    lod_props.damping_linear_c = lod.damping_linear_c
    lod_props.damping_linear_v = lod.damping_linear_v
    lod_props.damping_linear_v2 = lod.damping_linear_v2
    lod_props.damping_angular_c = lod.damping_angular_c
    lod_props.damping_angular_v = lod.damping_angular_v
    lod_props.damping_angular_v2 = lod.damping_angular_v2

    arch = lod.archetype
    arch_props = lod_props.archetype_properties
    arch_props.gravity_factor = arch.gravity_factor
    arch_props.max_speed = arch.max_speed
    arch_props.max_ang_speed = arch.max_ang_speed
    arch_props.buoyancy_factor = arch.buoyancy_factor


def apply_phys_groups_to_bones(frag: AssetFragment, frag_obj: Object):
    """Set the physics group properties for all bones in the armature."""
    armature = frag_obj.data
    groups = frag.physics.lod1.groups

    for group in groups:
        bone = armature.bones.get(group.name, None)
        if bone is None:
            # Bone not found, try a case-insensitive search
            group_name_lower = group.name.lower()
            for armature_bone in armature.bones:
                if group_name_lower == armature_bone.name.lower():
                    bone = armature_bone
                    break
            else:
                # Still no bone found
                logger.warning(f"No bone exists for the physics group {group.name}! Skipping...")
                continue

        bone.sollumz_use_physics = True
        apply_phys_group_to_bone(frag, group, bone)


def apply_phys_group_to_bone(frag: AssetFragment, group: PhysGroup, bone: Bone):
    group_props = bone.group_properties
    for i in range(len(group_props.flags)):
        group_props.flags[i] = (group.flags & (1 << i)) != 0
    group_props.strength = group.strength
    group_props.force_transmission_scale_up = group.force_transmission_scale_up
    group_props.force_transmission_scale_down = group.force_transmission_scale_down
    group_props.joint_stiffness = group.joint_stiffness
    group_props.min_soft_angle_1 = group.min_soft_angle_1
    group_props.max_soft_angle_1 = group.max_soft_angle_1
    group_props.max_soft_angle_2 = group.max_soft_angle_2
    group_props.max_soft_angle_3 = group.max_soft_angle_3
    group_props.rotation_speed = group.rotation_speed
    group_props.rotation_strength = group.rotation_strength
    group_props.restoring_strength = group.restoring_strength
    group_props.restoring_max_torque = group.restoring_max_torque
    group_props.latch_strength = group.latch_strength
    group_props.min_damage_force = group.min_damage_force
    group_props.damage_health = group.damage_health
    group_props.weapon_health = group.weapon_health
    group_props.weapon_scale = group.weapon_scale
    group_props.vehicle_scale = group.vehicle_scale
    group_props.ped_scale = group.ped_scale
    group_props.ragdoll_scale = group.ragdoll_scale
    group_props.explosion_scale = group.explosion_scale
    group_props.object_scale = group.object_scale
    group_props.ped_inv_mass_scale = group.ped_inv_mass_scale
    group_props.melee_scale = group.melee_scale

    if (group.flags & 2) != 0:  # flag 2 indicates that the group has a glass window
        glass_windows = frag.glass_windows
        if 0 <= group.glass_window_index < len(glass_windows):
            glass_window = glass_windows[group.glass_window_index]
            glass_type_idx = glass_window.glass_type
            if 0 <= glass_type_idx < len(GlassTypes):
                group_props.glass_type = GlassTypes[glass_type_idx][0]
            else:
                logger.warning(
                    f"Bone '{bone.name}' has breakable glass but is using unknown glass type {glass_type_idx}."
                )
                group_props.flags[GroupFlagBit.USE_GLASS_WINDOW] = False
        else:
            logger.warning(
                f"Bone '{bone.name}' has breakable glass but its glass entry is missing "
                f"(index {group.glass_window_index}, num. entries {len(glass_windows)})."
            )
            group_props.flags[GroupFlagBit.USE_GLASS_WINDOW] = False


def create_phys_child_meshes(
    frag: AssetFragment,
    hi_frag: Optional[AssetFragment],
    frag_obj: Object,
    drawable_obj: Object,
    materials: list[Material],
    hi_materials: list[Material],
):
    """Create all Fragment.Physics.LOD1.Children meshes. (Only LOD1 currently supported)"""
    lod = frag.physics.lod1
    children = lod.children
    hi_children = hi_frag.physics.lod1.children if hi_frag else []
    bones = frag.base_drawable.skeleton.bones

    bone_name_by_tag: dict[str, SkelBone] = {bone.tag: bone.name for bone in bones}

    for i, child in enumerate(children):
        if not child.drawable.models:
            continue

        if child.bone_tag not in bone_name_by_tag:
            logger.warning("A fragment child has an invalid bone tag! Skipping...")
            continue

        bone_name = bone_name_by_tag[child.bone_tag]

        child_drawable = child.drawable
        hi_child_drawable = None
        if hi_children:
            hi_child = hi_children[i]
            hi_child_drawable = hi_child.drawable

        create_phys_child_models(
            child_drawable, hi_child_drawable, frag_obj,
            materials, hi_materials, bone_name, drawable_obj
        )


def create_phys_child_models(
    drawable: AssetDrawable,
    hi_drawable: Optional[AssetDrawable],
    frag_obj: Object,
    materials: list[Material],
    hi_materials: list[Material],
    bone_name: str,
    drawable_obj: Object
):
    """Create a single physics child mesh"""
    # There is usually only one drawable model in each frag child
    child_objs = create_drawable_models(drawable, hi_drawable, materials, hi_materials, f"{bone_name}.child")

    for child_obj in child_objs:
        add_child_of_bone_constraint(child_obj, frag_obj, bone_name)

        child_obj.sollumz_is_physics_child_mesh = True
        child_obj.parent = drawable_obj

    return child_objs


def create_frag_env_cloth(frag: AssetFragment, frag_obj: Object, drawable_obj: Object, materials: list[Material]) -> Object | None:
    cloths = frag.cloths
    if not cloths:
        return None

    from ..ydr.cloth import ClothAttr, mesh_add_cloth_attribute

    cloth = cloths[0]  # game only supports a single environment cloth per fragment
    if not cloth.drawable:
        return None

    model_objs = create_drawable_models(cloth.drawable, None, materials, None, f"{frag_obj.name}.cloth")
    assert model_objs and len(model_objs) == 1, "Too many models in cloth drawable!"

    model_obj = model_objs[0]
    model_obj.parent = drawable_obj

    bones = cloth.drawable.skeleton.bones
    bone_index = cloth.drawable.models[LodLevel.HIGH][0].bone_index
    bone_name = bones[bone_index].name
    add_child_of_bone_constraint(model_obj, frag_obj, bone_name)

    mesh = model_obj.data

    # LOD specific data
    # TODO: handle LODs
    pin_radius = cloth.controller.bridge.pin_radius_high
    weights = cloth.controller.bridge.vertex_weights_high
    inflation_scale = cloth.controller.bridge.inflation_scale_high
    mesh_to_cloth_map = np.array(cloth.controller.bridge.display_map_high)
    cloth_to_mesh_map = np.empty_like(mesh_to_cloth_map)
    cloth_to_mesh_map[mesh_to_cloth_map] = np.arange(len(mesh_to_cloth_map))
    pinned_vertices_count = cloth.controller.cloth_high.pinned_vertices_count
    vertices_count = len(cloth.controller.cloth_high.vertex_positions)
    force_transform = cloth.user_data  # np.fromstring(cloth.user_data or "", dtype=int, sep=" ")
    # TODO: store switch distances somewhere or maybe on export can be derived from existing LOD distances
    # switch_distance_up = cloth.controller.cloth_high.switch_distance_up
    # switch_distance_down = cloth.controller.cloth_high.switch_distance_down

    has_pinned = pinned_vertices_count > 0
    has_pin_radius = len(pin_radius) > 0
    num_pin_radius_sets = len(pin_radius) // vertices_count
    has_weights = len(weights) > 0
    has_inflation_scale = len(inflation_scale) > 0
    has_force_transform = len(force_transform) > 0

    if has_pinned:
        mesh_add_cloth_attribute(mesh, ClothAttr.PINNED)
    if has_pin_radius:
        mesh_add_cloth_attribute(mesh, ClothAttr.PIN_RADIUS)
        if num_pin_radius_sets > 4:
            logger.warning(f"Found {num_pin_radius_sets} pin radius sets, only up to 4 sets are supported!")
            num_pin_radius_sets = 4
    if has_weights:
        mesh_add_cloth_attribute(mesh, ClothAttr.VERTEX_WEIGHT)
    if has_inflation_scale:
        mesh_add_cloth_attribute(mesh, ClothAttr.INFLATION_SCALE)
    if has_force_transform:
        mesh_add_cloth_attribute(mesh, ClothAttr.FORCE_TRANSFORM)

    for mesh_vert_index, cloth_vert_index in enumerate(mesh_to_cloth_map):
        if has_pinned:
            pinned = cloth_vert_index < pinned_vertices_count
            mesh.attributes[ClothAttr.PINNED].data[mesh_vert_index].value = 1 if pinned else 0

        if has_pin_radius:
            pin_radii = [
                pin_radius[cloth_vert_index + (set_idx * vertices_count)]
                if set_idx < num_pin_radius_sets else 0.0
                for set_idx in range(4)
            ]
            mesh.attributes[ClothAttr.PIN_RADIUS].data[mesh_vert_index].color = pin_radii

        if has_weights:
            mesh.attributes[ClothAttr.VERTEX_WEIGHT].data[mesh_vert_index].value = weights[cloth_vert_index]

        if has_inflation_scale:
            mesh.attributes[ClothAttr.INFLATION_SCALE].data[mesh_vert_index].value = inflation_scale[cloth_vert_index]

        if has_force_transform:
            mesh.attributes[ClothAttr.FORCE_TRANSFORM].data[mesh_vert_index].value = force_transform[cloth_vert_index]

    custom_edges = [e for e in (cloth.controller.cloth_high.custom_edges or []) if e.vertex0 != e.vertex1]
    if custom_edges:
        next_edge = len(mesh.edges)
        mesh.edges.add(len(custom_edges))
        for custom_edge in custom_edges:
            v0 = custom_edge.vertex0
            v1 = custom_edge.vertex1
            mv0 = int(cloth_to_mesh_map[v0])
            mv1 = int(cloth_to_mesh_map[v1])
            mesh.edges[next_edge].vertices = mv0, mv1
            next_edge += 1

    # Debug code to visualize the verlet cloth edges.
    # debug_edges = [e for e in (cloth.controller.cloth_high.edges or []) if e.vertex0 != e.vertex1]
    # if debug_edges:
    #     debug_mesh = bpy.data.meshes.new(f"{mesh.name}.debug")
    #     debug_obj = bpy.data.objects.new(f"{mesh.name}.debug", debug_mesh)
    #     debug_mesh.vertices.add(len(mesh.vertices))
    #     for v in mesh.vertices:
    #         debug_mesh.vertices[v.index].co = v.co
    #     next_edge = len(debug_mesh.edges)
    #     debug_mesh.edges.add(len(debug_edges))
    #     for edge in debug_edges:
    #         v0 = edge.vertex0
    #         v1 = edge.vertex1
    #         mv0 = int(cloth_to_mesh_map[v0])
    #         mv1 = int(cloth_to_mesh_map[v1])
    #         debug_mesh.edges[next_edge].vertices = mv0, mv1
    #         next_edge += 1
    #
    #     bpy.context.collection.objects.link(debug_obj)

    cloth_props = frag_obj.fragment_properties.cloth
    cloth_props.weight = cloth.controller.cloth_high.cloth_weight
    if (tuning := cloth.tuning):
        cloth_props.enable_tuning = True
        cloth_props.tuning_flags.total = str(tuning.flags)
        cloth_props.extra_force = tuning.extra_force
        cloth_props.weight_override = tuning.weight
        cloth_props.distance_threshold = tuning.distance_threshold
        if cloth_props.tuning_flags.wind_feedback:
            cloth_props.rotation_rate = tuning.rotation_rate
            cloth_props.angle_threshold = tuning.angle_threshold
            cloth_props.pin_vert = cloth_to_mesh_map[tuning.pin_vert]
            cloth_props.non_pin_vert0 = cloth_to_mesh_map[tuning.non_pin_vert0]
            cloth_props.non_pin_vert1 = cloth_to_mesh_map[tuning.non_pin_vert1]

    if (bounds := cloth.controller.cloth_high.bounds):
        cloth_bounds = create_bound_composite(bounds, f"{frag_obj.name}.cloth_world_bounds")
        cloth_props.world_bounds = cloth_bounds

    return model_obj


def create_frag_vehicle_windows(frag: AssetFragment, frag_obj: Object, materials: list[Material]):
    vehicle_windows = frag.vehicle_windows
    if not vehicle_windows:
        return

    for vw in vehicle_windows:
        window_bone = find_frag_vehicle_window_bone(vw, frag, frag_obj.data.bones)
        col_obj = find_frag_vehicle_window_col(frag_obj, window_bone.name)

        if col_obj is None:
            logger.warning(
                f"Window with component ID {vw.component_id} has no associated collision! Is the file malformed?"
            )
            continue

        col_obj.child_properties.is_veh_window = True

        window_mat = find_frag_vehicle_window_material(vw, frag.drawable, materials)

        if window_mat is not None:
            col_obj.child_properties.window_mat = window_mat

        shattermap_name = f"{window_bone.name}_shattermap"
        shattermap_obj = create_frag_vehicle_window_shattermap(vw, shattermap_name, window_bone.matrix_local)
        shattermap_obj.parent = col_obj

        col_obj.vehicle_window_properties.data_min = vw.data_min
        col_obj.vehicle_window_properties.data_max = vw.data_max
        col_obj.vehicle_window_properties.cracks_texture_tiling = vw.scale


def find_frag_vehicle_window_bone(window: FragVehicleWindow, frag: AssetFragment, bones: ArmatureBones) -> Bone:
    """Get bone connected to window based on the bone tag of the physics child associated with the window."""
    children = frag.physics.lod1.children
    child_index = window.component_id

    if not (0 <= child_index < len(children)):
        return bones[0]

    bone_tag = children[child_index].bone_tag

    for bone in bones:
        if bone.bone_properties.tag == bone_tag:
            return bone

    # Return root bone if no bone is found
    return bones[0]


def find_frag_vehicle_window_col(frag_obj: Object, bone_name: str) -> Object | None:
    for obj in frag_obj.children_recursive:
        if obj.sollum_type in BOUND_TYPES:
            col_bone = get_child_of_bone(obj)

            if col_bone is not None and col_bone.name == bone_name:
                return obj

    return None


def find_frag_vehicle_window_material(window: FragVehicleWindow, drawable: AssetDrawable, materials: list[Material]) -> Material | None:
    """Find the material used by a vehicle window based on its geometry index."""
    models = drawable.models.get(LodLevel.HIGH, [])
    if not models:
        return None

    model = models[0]
    geometries = model.geometries

    if not (0 <= window.geometry_index < len(geometries)):
        return None

    geometry = geometries[window.geometry_index]
    shader_index = geometry.shader_index

    if not (0 <= shader_index < len(materials)):
        return None

    return materials[shader_index]


def create_frag_vehicle_window_shattermap(window: FragVehicleWindow, name: str, transform: Matrix) -> Object:
    proj_mat = Matrix(window.basis)
    proj_mat[3][3] = 1
    proj_mat.transpose()
    proj_mat.invert_safe()

    vw_min = Vector((0, 0, 0))
    vw_max = Vector((window.width, window.height, 1))

    v0 = multiply_homogeneous(proj_mat, Vector((vw_min.x, vw_min.y, 0)))
    v1 = multiply_homogeneous(proj_mat, Vector((vw_min.x, vw_max.y, 0)))
    v2 = multiply_homogeneous(proj_mat, Vector((vw_max.x, vw_max.y, 0)))
    v3 = multiply_homogeneous(proj_mat, Vector((vw_max.x, vw_min.y, 0)))
    verts = v0, v1, v2, v3
    faces = [[0, 1, 2, 3]]

    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(verts, [], faces)
    mesh.transform(transform.inverted())

    uvs = np.array([[0.0, 1.0], [0.0, 0.0], [1.0, 0.0], [1.0, 1.0]], dtype=np.float64)
    create_uv_attr(mesh, 0, initial_values=uvs)

    shattermap_obj = create_blender_object(SollumType.SHATTERMAP, name, mesh)

    if window.shattermap is not None:
        shattermap_mat = shattermap_to_material(window.shattermap, name)
        mesh.materials.append(shattermap_mat)

    return shattermap_obj


def shattermap_to_material(shattermap: np.ndarray, name: str) -> Material:
    img = shattermap_to_image(shattermap, name)
    img.pack()
    mat = material_from_image(img, name, "ShatterMap")
    return mat


def shattermap_to_image(shattermap: np.ndarray, name: str) -> Image:
    """Converts a shattermap 2D array to a Blender image.

    Args:
        shattermap: 2D array of floats, shape (height, width).
        name: name for new image.
    """
    height, width = shattermap.shape
    pixels = np.empty((height, width, 4), dtype=np.float32)
    pixels[:, :, 0] = shattermap
    pixels[:, :, 1] = shattermap
    pixels[:, :, 2] = shattermap
    pixels[:, :, 3] = 1.0

    img = bpy.data.images.new(name, width, height)
    try:
        img.pixels = pixels.ravel()
    except ValueError:
        logger.error("Cannot create shattermap, shattermap data is malformed")

    return img


def create_fragment_as_asset(frag: AssetFragment, hi_frag: Optional[AssetFragment], name: str) -> Object:
    """Create fragment as an asset with all meshes joined together."""
    # frag_xml.drawable.drawable_models_low = []
    # frag_xml.drawable.drawable_models_med = []
    # frag_xml.drawable.drawable_models_vlow = []

    from ..ydr.ydrimport import convert_object_to_asset
    frag_obj = create_fragment(frag, hi_frag, name)
    return convert_object_to_asset(name, frag_obj)
