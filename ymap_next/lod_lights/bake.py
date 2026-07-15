import re
from dataclasses import dataclass, field, fields
from typing import TYPE_CHECKING

import bpy
import numpy as np
from bpy.types import (
    Mesh,
    Object,
)
from mathutils import Matrix, Quaternion, Vector
from szio.gta5 import LightType

from ...shared.game_assets.asset_info import (
    AssetInfoCache,
    try_get_asset_metadata_archetype_info,
    try_get_asset_metadata_collisions,
    try_get_asset_metadata_lights,
    try_get_asset_metadata_skeleton,
)
from ...shared.geometry import KDTreeSplitStrategy, kdtree_build, kdtree_merge_leaves
from ...sollumz_properties import SollumType
from ...tools.blenderhelper import create_blender_object

if TYPE_CHECKING:
    from ..properties.map import MapGroup


def _transform_aabbs(
    world_matrices: np.ndarray, aabb_mins: np.ndarray, aabb_maxs: np.ndarray
) -> tuple[np.ndarray, np.ndarray]:
    """Transform batched local AABBs into world space."""
    M = np.asarray(world_matrices, dtype=np.float32)
    mins = np.asarray(aabb_mins, dtype=np.float32)
    maxs = np.asarray(aabb_maxs, dtype=np.float32)

    assert mins.shape == maxs.shape, f"aabb_mins/aabb_maxs shape mismatch: {mins.shape} vs {maxs.shape}"
    assert M.shape[:-2] == mins.shape[:-1], (
        f"world_matrices/aabb leading dims mismatch: {M.shape[:-2]} vs {mins.shape[:-1]}"
    )

    center_local = (mins + maxs) * np.float32(0.5)
    extent_local = (maxs - mins) * np.float32(0.5)

    rot = M[..., :3, :3]
    trans = M[..., :3, 3]

    center_world = np.einsum("...ij,...j->...i", rot, center_local) + trans
    extent_world = np.einsum("...ij,...j->...i", np.abs(rot), extent_local)

    return center_world - extent_world, center_world + extent_world


def _rot32(x: np.ndarray, k: int) -> np.ndarray:
    return ((x << np.uint32(k)) | (x >> np.uint32(32 - k))) & np.uint32(0xFFFFFFFF)


def _mix(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized port of the `mix(a,b,c)` macro from Jenkins lookup3."""
    mask = np.uint32(0xFFFFFFFF)
    # fmt: off
    a = (a - c) & mask; a = a ^ _rot32(c, 4);  c = (c + b) & mask
    b = (b - a) & mask; b = b ^ _rot32(a, 6);  a = (a + c) & mask
    c = (c - b) & mask; c = c ^ _rot32(b, 8);  b = (b + a) & mask
    a = (a - c) & mask; a = a ^ _rot32(c, 16); c = (c + b) & mask
    b = (b - a) & mask; b = b ^ _rot32(a, 19); a = (a + c) & mask
    c = (c - b) & mask; c = c ^ _rot32(b, 4);  b = (b + a) & mask
    # fmt: on
    return a, b, c


def _final(a: np.ndarray, b: np.ndarray, c: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Vectorized port of the `final(a,b,c)` macro from Jenkins lookup3."""
    mask = np.uint32(0xFFFFFFFF)
    # fmt: off
    c = c ^ b; c = (c - _rot32(b, 14)) & mask
    a = a ^ c; a = (a - _rot32(c, 11)) & mask
    b = b ^ a; b = (b - _rot32(a, 25)) & mask
    c = c ^ b; c = (c - _rot32(b, 16)) & mask
    a = a ^ c; a = (a - _rot32(c, 4))  & mask
    b = b ^ a; b = (b - _rot32(a, 14)) & mask
    c = c ^ b; c = (c - _rot32(b, 24)) & mask
    # fmt: on
    return a, b, c


def _lookup3_uint32x7(k: np.ndarray, initval: int = 0) -> np.ndarray:
    """Jenkins lookup3 hash function, vectorized and specialized for length-7 uint32 key.
    See: https://www.burtleburtle.net/bob/c/lookup3.c
    """
    mask = np.uint32(0xFFFFFFFF)
    k = np.ascontiguousarray(k, dtype=np.uint32)
    init = np.uint32((0xDEADBEEF + (7 << 2) + initval) & 0xFFFFFFFF)
    a = np.full(k.shape[0], init, dtype=np.uint32)
    b = a.copy()
    c = a.copy()

    a = (a + k[:, 0]) & mask
    b = (b + k[:, 1]) & mask
    c = (c + k[:, 2]) & mask
    a, b, c = _mix(a, b, c)

    a = (a + k[:, 3]) & mask
    b = (b + k[:, 4]) & mask
    c = (c + k[:, 5]) & mask
    a, b, c = _mix(a, b, c)

    a = (a + k[:, 6]) & mask
    a, b, c = _final(a, b, c)
    return c


def generate_lod_light_hash_multiple(
    entity_world_matrices,
    entity_aabb_mins,
    entity_aabb_maxs,
    light_entity_indices,
    light_ids,
) -> np.ndarray:
    """Compute LOD-light hashes."""
    world_mins, world_maxs = _transform_aabbs(entity_world_matrices, entity_aabb_mins, entity_aabb_maxs)

    snapped_mins = (world_mins * np.float32(10.0)).astype(np.int32).view(np.uint32)
    snapped_maxs = (world_maxs * np.float32(10.0)).astype(np.int32).view(np.uint32)

    ent_idx = np.asarray(light_entity_indices, dtype=np.intp)
    ids = np.asarray(light_ids, dtype=np.int32).view(np.uint32)

    assert ent_idx.shape == ids.shape, f"light_entity_indices/light_ids shape mismatch: {ent_idx.shape} vs {ids.shape}"

    keys = np.empty((ent_idx.shape[0], 7), dtype=np.uint32)
    keys[:, 0:3] = snapped_mins[ent_idx]
    keys[:, 3:6] = snapped_maxs[ent_idx]
    keys[:, 6] = ids

    return _lookup3_uint32x7(keys, initval=0)


def generate_lod_light_hash_single(obj: Object, aabb_min, aabb_max, light_id: int) -> int:
    """Compute the LOD-light hash for a single light on a single Blender object."""
    hashes = generate_lod_light_hash_multiple([obj.matrix_world], [aabb_min], [aabb_max], [0], [light_id])
    return int(hashes[0])


@dataclass(slots=True)
class LodLightBakeSettings:
    lod_levels: set[str] = field(default_factory=lambda: {"HD"})
    priority_levels: set[str] = field(default_factory=lambda: {"REQUIRED"})
    is_streetlight_pattern: str = r"street[_]?light"
    skip_pattern: str = r"prop_dock_bouy"
    min_falloff_small: float = 0.0
    min_falloff_medium: float = 10.0
    min_intensity_small: float = 0.0
    min_intensity_medium: float = 1.0
    partition: bool = True
    partition_max_lights_small: int = 1000
    partition_max_lights_medium: int = 3500
    partition_max_lights_large: int = 100
    visibility_range_small: float = 450.0
    visibility_range_medium: float = 950.0
    visibility_range_large: float = 2700.0
    distant_visibility_range_small: float = 450.0
    distant_visibility_range_medium: float = 300.0
    distant_visibility_range_large: float = 2700.0
    name_prefix: str = "new_"


CAT_SMALL = 0
CAT_MEDIUM = 1
CAT_LARGE = 2
CAT_SKIP = 255


@dataclass(slots=True)
class LodLights:
    position: np.ndarray
    direction: np.ndarray
    aabb_min: np.ndarray
    aabb_max: np.ndarray
    falloff: np.ndarray
    falloff_exponent: np.ndarray
    light_fade_distance: np.ndarray
    hash: np.ndarray
    rgbi: np.ndarray
    cone_inner_angle: np.ndarray
    cone_outer_angle: np.ndarray
    corona_size: np.ndarray
    corona_intensity: np.ndarray
    capsule_extent: np.ndarray
    flags: np.ndarray
    flags_time: np.ndarray
    flags_is_streetlight: np.ndarray
    flags_type: np.ndarray

    @property
    def empty(self) -> bool:
        return len(self.position) == 0

    @property
    def flags_packed(self) -> np.ndarray:
        FLAG_DONT_USE_IN_CUTSCENE = np.uint32(1 << 2)
        FLAG_CORONA_ONLY = np.uint32(1 << 15)
        FLAG_CORONA_ONLY_LOD_LIGHT = np.uint32(1 << 29)
        flags_is_corona_only = (self.flags & (FLAG_CORONA_ONLY | FLAG_CORONA_ONLY_LOD_LIGHT)) != 0
        flags_dont_use_in_cutscene = (self.flags & FLAG_DONT_USE_IN_CUTSCENE) != 0

        return (
            self.flags_time
            | (self.flags_is_streetlight.astype(np.uint32) << 24)
            | (flags_is_corona_only.astype(np.uint32) << 25)
            | (self.flags_type << 26)
            | (flags_dont_use_in_cutscene.astype(np.uint32) << 31)
        )

    def to_mesh(self, name: str) -> Mesh:
        from ..lod_lights import LodLightAttr, mesh_add_lod_light_attribute

        MAX_INTENSITY = 48.0
        MAX_CONE_ANGLE = 180.0
        MAX_CORONA_INTENSITY = 32.0
        MAX_CAPSULE_EXTENT = 140.0

        corona_intensity = np.where(self.corona_size < 0.05, 0.0, self.corona_intensity)

        packed_flags = self.flags_packed
        packed_rgbi = self.rgbi.copy()
        packed_rgbi[:, 3] = (packed_rgbi[:, 3] / MAX_INTENSITY).clip(0.0, 1.0)
        packed_cone_inner_angle = (self.cone_inner_angle / MAX_CONE_ANGLE * 255).astype(np.int32).clip(0, 255)
        packed_cone_outer_angle = (self.cone_outer_angle / MAX_CONE_ANGLE * 255).astype(np.int32).clip(0, 255)
        packed_corona_intensity = (corona_intensity / MAX_CORONA_INTENSITY * 255).astype(np.int32).clip(0, 255)
        packed_capsule_extent = (self.capsule_extent / MAX_CAPSULE_EXTENT * 255).astype(np.int32).clip(0, 255)

        # Capsule extent is stored in the same array as the cone outer angle
        is_capsule = self.flags_type == LightType.CAPSULE.value
        packed_cone_outer_angle[is_capsule] = packed_capsule_extent[is_capsule]

        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(self.position, [], [])

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.RGBI)
        mesh_attr.data.foreach_set("color_srgb", self.rgbi.ravel())

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.DIRECTION)
        mesh_attr.data.foreach_set("vector", self.direction.ravel())

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.FALLOFF)
        mesh_attr.data.foreach_set("value", self.falloff)

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.FALLOFF_EXP)
        mesh_attr.data.foreach_set("value", self.falloff_exponent)

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.FLAGS)
        mesh_attr.data.foreach_set("value", packed_flags.view(np.int32))

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.HASH)
        mesh_attr.data.foreach_set("value", self.hash.view(np.int32))

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.CONE_INNER_ANGLE)
        mesh_attr.data.foreach_set("value", packed_cone_inner_angle)

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.CONE_OUTER_ANGLE)
        mesh_attr.data.foreach_set("value", packed_cone_outer_angle)

        mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.CORONA_INTENSITY)
        mesh_attr.data.foreach_set("value", packed_corona_intensity)

        return mesh

    def remove_skipped(self, settings: LodLightBakeSettings) -> "LodLights":
        category = self.categorize(settings)
        field_names = [f.name for f in fields(self)]
        keep_mask = category != CAT_SKIP
        return LodLights(**{n: getattr(self, n)[keep_mask] for n in field_names})

    def split_by_category(self, settings: LodLightBakeSettings) -> tuple["LodLights", "LodLights", "LodLights"]:
        """Split into (small, medium, large) by category value."""
        category = self.categorize(settings)
        field_names = [f.name for f in fields(self)]
        category_mask = [category == c for c in (0, 1, 2)]
        return tuple(LodLights(**{n: getattr(self, n)[category_mask[c]] for n in field_names}) for c in (0, 1, 2))

    def categorize(self, settings: LodLightBakeSettings) -> np.ndarray:
        FLAG_FAR_LOD_LIGHT = np.uint32(1 << 22)
        FLAG_FORCE_MEDIUM_LOD_LIGHT = np.uint32(1 << 28)

        n = len(self.position)

        flags_far_lod_light = (self.flags & FLAG_FAR_LOD_LIGHT) != 0
        flags_force_medium_lod_light = (self.flags & FLAG_FORCE_MEDIUM_LOD_LIGHT) != 0

        is_capsule = self.flags_type == LightType.CAPSULE.value
        falloff = np.where(
            is_capsule,
            2.0 * self.falloff + self.capsule_extent,
            self.falloff,
        )

        intensity = self.rgbi[:, 3]

        category = np.full(n, CAT_SKIP, dtype=np.uint8)

        is_skip = self.light_fade_distance > 0
        is_small = (falloff >= settings.min_falloff_small) | (intensity >= settings.min_intensity_small)
        is_medium = flags_force_medium_lod_light | (
            (falloff >= settings.min_falloff_medium) & (intensity >= settings.min_intensity_medium)
        )
        is_large = flags_far_lod_light

        category[~is_skip & is_small] = CAT_SMALL
        category[~is_skip & is_medium] = CAT_MEDIUM
        category[~is_skip & is_large] = CAT_LARGE

        return category

    def partition(self, max_lights_in_partition: int) -> list["LodLights"]:
        position_2d = self.position[:, :2]
        tree = kdtree_build(position_2d, KDTreeSplitStrategy.LONGEST_AXIS, max_points_in_leaf=max_lights_in_partition)
        tree = kdtree_merge_leaves(tree, position_2d, max_points_in_leaf=max_lights_in_partition)
        partioned = []
        field_names = [f.name for f in fields(self)]
        for leaf in tree.iter_leaves():
            p = LodLights(**{n: getattr(self, n)[leaf.indices] for n in field_names})
            partioned.append(p)

        return partioned

    def calculate_entities_extents(self) -> tuple[Vector, Vector]:
        entities_extents_min = np.min(self.aabb_min, axis=0)
        entities_extents_max = np.max(self.aabb_max, axis=0)
        return Vector(entities_extents_min), Vector(entities_extents_max)

    def calculate_streaming_extents(self, visibility_range: float) -> tuple[Vector, Vector]:
        streaming_extents_min = np.min(self.position - visibility_range, axis=0)
        streaming_extents_max = np.max(self.position + visibility_range, axis=0)
        return Vector(streaming_extents_min), Vector(streaming_extents_max)


def _bone_armature_matrix(skeleton: dict | None, bone_id: int) -> Matrix | None:
    """Return the bone's armature-space matrix for the bone whose `tag == bone_id`, by walking up the parent chain.
    Returns None if the skeleton metadata is missing, `bone_id` is 0, or no bone with that tag exists.
    """
    if not skeleton or bone_id == 0:
        return None

    bones = skeleton.get("bones", [])
    target = next((i for i, b in enumerate(bones) if b.get("tag", 0) == bone_id), -1)
    if target == -1:
        return None

    chain = []
    idx = target
    while idx != -1:
        chain.append(bones[idx])
        idx = bones[idx].get("parent_index", -1)

    mat = Matrix.Identity(4)
    for b in reversed(chain):
        loc = Matrix.Translation(Vector(b.get("position", (0.0, 0.0, 0.0))))
        rot = Quaternion(b.get("rotation", (1.0, 0.0, 0.0, 0.0))).to_matrix().to_4x4()
        sca = Matrix.Diagonal(Vector((*b.get("scale", (1.0, 1.0, 1.0)), 1.0)))
        mat = mat @ loc @ rot @ sca
    return mat


def collect_lod_lights(map_group: "MapGroup", settings: LodLightBakeSettings) -> LodLights | None:
    is_streetlight_re = re.compile(settings.is_streetlight_pattern, re.IGNORECASE)
    skip_re = re.compile(settings.skip_pattern, re.IGNORECASE)

    entity_world_matrices = []
    entity_aabb_mins = []
    entity_aabb_maxs = []
    light_entity_indices = []
    light_ids = []
    light_positions = []
    light_directions = []
    light_rgbi = []
    light_falloffs = []
    light_falloff_exponents = []
    light_cone_inner_angles = []
    light_cone_outer_angles = []
    light_corona_sizes = []
    light_corona_intensities = []
    light_capsule_extents = []
    light_fade_distances = []
    light_flags = []
    light_flags_time = []
    light_flags_is_streetlight = []
    light_flags_type = []
    asset_info_cache = AssetInfoCache()
    for ent in map_group.entities:
        if ent.lod_level not in settings.lod_levels:
            continue

        if ent.priority_level not in settings.priority_levels:
            continue

        obj = ent.linked_object
        if not obj:
            continue

        if skip_re.search(obj.name):
            continue

        # TODO(ymap): consider LightEffect extension that overrides light settings
        lights = try_get_asset_metadata_lights(obj, cache=asset_info_cache)
        if not lights:
            continue

        archetype_info = try_get_asset_metadata_archetype_info(obj, cache=asset_info_cache)
        if archetype_info is None:
            print("missing archetype info " + obj.name)
            continue

        cols = try_get_asset_metadata_collisions(obj, cache=asset_info_cache) or {}
        skeleton = try_get_asset_metadata_skeleton(obj, cache=asset_info_cache)

        arch_bb_min = archetype_info.bb_min
        arch_bb_max = archetype_info.bb_max
        cols_bb_min = cols.get("bb_min", (0.0, 0.0, 0.0))
        cols_bb_max = cols.get("bb_max", (0.0, 0.0, 0.0))
        bb_min = np.minimum(arch_bb_min, cols_bb_min)
        bb_max = np.maximum(arch_bb_max, cols_bb_max)

        entity_idx = len(entity_world_matrices)
        entity_world_matrices.append(obj.matrix_world)
        entity_aabb_mins.append(bb_min)
        entity_aabb_maxs.append(bb_max)

        obj_world = obj.matrix_world
        obj_world_rot = obj_world.to_3x3()
        is_streetlight = bool(is_streetlight_re.search(obj.name))
        for light_idx, light in enumerate(lights):
            light_id = archetype_info.num_extensions + light_idx
            light_entity_indices.append(entity_idx)
            light_ids.append(light_id)
            local_pos = Vector(light.get("position", (0.0, 0.0, 0.0)))
            local_dir = Vector(light.get("direction", (0.0, 0.0, 0.0)))
            bone_mat = _bone_armature_matrix(skeleton, light.get("bone_id", 0))
            if bone_mat is not None:
                light_positions.append(obj_world @ bone_mat @ local_pos)
                light_directions.append(obj_world_rot @ bone_mat.to_3x3() @ local_dir)
            else:
                light_positions.append(obj_world @ local_pos)
                light_directions.append(obj_world_rot @ local_dir)
            r, g, b = [channel / 255 for channel in light.get("color", (255, 255, 255))]
            i = light.get("intensity", 0.0)
            light_rgbi.append((r, g, b, i))
            light_falloffs.append(light.get("falloff", 0.0))
            light_falloff_exponents.append(light.get("falloff_exponent", 0.0))
            light_cone_inner_angles.append(light.get("cone_inner_angle", 0.0))
            light_cone_outer_angles.append(light.get("cone_outer_angle", 0.0))
            light_corona_sizes.append(light.get("corona_size", 0.0))
            light_corona_intensities.append(light.get("corona_intensity", 0.0))
            light_capsule_extents.append(light.get("extent", (0.0, 0.0, 0.0))[0])
            light_fade_distances.append(light.get("light_fade_distance", 0))
            light_flags.append(light.get("flags", 0))
            light_flags_time.append(light.get("time_flags", 0))
            light_flags_is_streetlight.append(is_streetlight)
            light_flags_type.append(LightType[light.get("light_type", "POINT")].value)

    if not light_positions:
        return None

    entity_world_aabb_mins, entity_world_aabb_maxs = _transform_aabbs(
        entity_world_matrices, entity_aabb_mins, entity_aabb_maxs
    )

    light_positions = np.array(light_positions, dtype=np.float32)
    light_directions = np.array(light_directions, dtype=np.float32)
    light_aabb_mins = entity_world_aabb_mins[light_entity_indices]
    light_aabb_maxs = entity_world_aabb_maxs[light_entity_indices]
    light_falloffs = np.array(light_falloffs, dtype=np.float32)
    light_falloff_exponents = np.array(light_falloff_exponents, dtype=np.float32)
    light_fade_distances = np.array(light_fade_distances, dtype=np.uint32)
    light_hashes = generate_lod_light_hash_multiple(
        entity_world_matrices, entity_aabb_mins, entity_aabb_maxs, light_entity_indices, light_ids
    )
    light_rgbi = np.array(light_rgbi, dtype=np.float32)
    light_cone_inner_angles = np.array(light_cone_inner_angles, dtype=np.float32)
    light_cone_outer_angles = np.array(light_cone_outer_angles, dtype=np.float32)
    light_corona_sizes = np.array(light_corona_sizes, dtype=np.float32)
    light_corona_intensities = np.array(light_corona_intensities, dtype=np.float32)
    light_capsule_extents = np.array(light_capsule_extents, dtype=np.float32)
    light_flags = np.array(light_flags, dtype=np.uint32)
    light_flags_time = np.array(light_flags_time, dtype=np.uint32)
    light_flags_is_streetlight = np.array(light_flags_is_streetlight, dtype=bool)
    light_flags_type = np.array(light_flags_type, dtype=np.uint32)

    return LodLights(
        position=light_positions,
        direction=light_directions,
        aabb_min=light_aabb_mins,
        aabb_max=light_aabb_maxs,
        falloff=light_falloffs,
        falloff_exponent=light_falloff_exponents,
        light_fade_distance=light_fade_distances,
        hash=light_hashes,
        rgbi=light_rgbi,
        cone_inner_angle=light_cone_inner_angles,
        cone_outer_angle=light_cone_outer_angles,
        corona_size=light_corona_sizes,
        corona_intensity=light_corona_intensities,
        capsule_extent=light_capsule_extents,
        flags=light_flags,
        flags_time=light_flags_time,
        flags_is_streetlight=light_flags_is_streetlight,
        flags_type=light_flags_type,
    )


def build_lod_light_maps(map_group: "MapGroup", lod_lights: LodLights, settings: LodLightBakeSettings):
    if lod_lights.empty:
        return

    visibility_range_per_category = {
        "SMALL": settings.visibility_range_small,
        "MEDIUM": settings.visibility_range_medium,
        "LARGE": settings.visibility_range_large,
    }
    distant_visibility_range_per_category = {
        "SMALL": settings.distant_visibility_range_small,
        "MEDIUM": settings.distant_visibility_range_medium,
        "LARGE": settings.distant_visibility_range_large,
    }
    partition_max_lights_per_category = {
        "SMALL": settings.partition_max_lights_small,
        "MEDIUM": settings.partition_max_lights_medium,
        "LARGE": settings.partition_max_lights_large,
    }

    name_prefix = settings.name_prefix
    scripted = map_group.scripted
    if scripted:
        # When scripted place all lights in a single category
        all = lod_lights.remove_skipped(settings)
        categories = (("MEDIUM", all),)
    else:
        small, medium, large = lod_lights.split_by_category(settings)
        categories = (
            ("SMALL", small),
            ("MEDIUM", medium),
            ("LARGE", large),
        )

    for category, lights_for_category in categories:
        if lights_for_category.empty:
            continue

        category_label = category.lower()

        if settings.partition:
            lights_partitioned = lights_for_category.partition(partition_max_lights_per_category[category])
        else:
            lights_partitioned = [lights_for_category]

        has_multiple_partitions = len(lights_partitioned) > 1

        base_name_distant = f"{name_prefix}distantlights" if scripted else f"{name_prefix}distlodlights"
        base_name = f"{name_prefix}lodlights"
        if not scripted:
            base_name_distant += f"_{category_label}"
            base_name += f"_{category_label}"

        vis_range = visibility_range_per_category[category]
        vis_range_distant = distant_visibility_range_per_category[category]

        for i, lights_partition in enumerate(lights_partitioned):
            name_distant = base_name_distant
            name = base_name
            if has_multiple_partitions:
                idx_suffix = f"{i:03d}"
                name_distant += idx_suffix
                name += idx_suffix

            entities_extents = lights_partition.calculate_entities_extents()
            streaming_extents = lights_partition.calculate_streaming_extents(vis_range)
            streaming_extents_distant = lights_partition.calculate_streaming_extents(vis_range_distant)

            mesh = lights_partition.to_mesh(name)
            mesh_obj = create_blender_object(SollumType.NONE, name, mesh)
            map_data_distant = map_group.new_map()
            map_data_distant.name = name_distant
            map_data_distant.entities_extents = entities_extents
            map_data_distant.streaming_extents = streaming_extents_distant
            map_data_distant.extents_manual = True
            # Snapshot before the next new_map(); adding to the maps collection
            # invalidates the map_data_distant reference
            map_data_distant_uuid = map_data_distant.uuid
            map_data = map_group.new_map()
            map_data.name = name
            map_data.entities_extents = entities_extents
            map_data.streaming_extents = streaming_extents
            map_data.extents_manual = True
            map_data.parent_uuid = map_data_distant_uuid
            ll = map_group.new_lod_lights()
            ll.map_data_uuid = map_data.uuid
            ll.name = name
            ll.category = category
            ll.linked_object = mesh_obj

    map_group.refresh_ui()
