import math
from collections import Counter, defaultdict

import bpy
import numpy as np
from bpy.types import (
    Depsgraph,
    Object,
)
from bpy_extras.mesh_utils import mesh_linked_triangles
from mathutils import Quaternion, Vector
from szio.gta5 import (
    AssetMapData,
    Entity,
    EntityFlags,
    EntityLodLevel,
    EntityMloInstance,
    EntityMloInstanceFlags,
    EntityPriorityLevel,
    MapBlockDescription,
    MapBoxOccluder,
    MapCarGenerator,
    MapCarGeneratorCreationRule,
    MapCarGeneratorFlags,
    MapContentFlags,
    MapFlags,
    MapGrassInstanceList,
    MapLodLightCategory,
    MapModelOccluder,
    MapModelOccluderFlags,
)
from szio.gta5 import (
    MapDistantLodLights as IOMapDistantLodLights,
)
from szio.gta5 import (
    MapLodLights as IOMapLodLights,
)
from szio.gta5 import (
    MapTimeCycleModifier as IOMapTimeCycleModifier,
)
from szio.gta5.maps import MAP_DISTANT_LOD_LIGHT_DTYPE, MAP_GRASS_INSTANCES_UNPACKED_DTYPE, MAP_LOD_LIGHT_DTYPE

from ..iecontext import ExportBundle, export_context
from ..shared.game_assets.asset_info import AssetInfoCache
from ..tools.blenderhelper import remove_number_suffix
from .extents import calc_map_data_extents
from .grass import evaluated_grass_batch_instances_from_object, partition_grass_batch_instances
from .grass.geonodes import disable_grass_batch_modifier_preview
from .occluders.box import box_island_is_valid, recover_box_occluder
from .properties.map import (
    MAP_CARGEN_FLAG_PROPS,
    MapCarGen,
    MapData,
    MapEntity,
    MapGrassBatch,
    MapGroup,
    MapLodLights,
    MapOccluder,
    MapPartitionMode,
    MapTimecycleModifier,
)


def export_ymap(map_group: MapGroup) -> list[ExportBundle]:
    _ensure_auto_partitions_generated(map_group)
    return create_map_data_assets(map_group)


def _ensure_auto_partitions_generated(map_group: MapGroup):
    """Generate partitions for any AUTO map datas that have items assigned directly to them.

    This handles the case where the user added new items to an AUTO parent but didn't
    explicitly run "Generate Partitions" before exporting.
    """
    from .partitioning import PartitioningSettings, generate_partitions

    settings = PartitioningSettings()

    # First pass collects UUIDs only; generate_partitions mutates map_group.maps,
    # which would invalidate the iterator and map_data references
    pending_auto_uuids = []
    for map_data in map_group.maps:
        if map_data.partition_mode != MapPartitionMode.AUTO.name:
            continue

        if map_data.incomplete_lod_hierarchy_lock:
            # Just in case, locked maps cannot be switched to AUTO via the UI. Regenerating partitions creates new
            # map UUIDs and re-buckets entities, breaking the frozen hierarchy.
            continue

        # Check if there are any non-LOD/SLOD items still assigned to the AUTO parent
        # (i.e., items that should have been distributed to leaves)
        has_pending = False
        map_uuid = map_data.uuid
        for entity in map_group.entities:
            if entity.map_data_uuid == map_uuid and entity.lod_level not in ("LOD", "SLOD1", "SLOD2", "SLOD3", "SLOD4"):
                has_pending = True
                break

        if not has_pending:
            for cargen in map_group.cargens:
                if cargen.map_data_uuid == map_uuid:
                    has_pending = True
                    break

        if not has_pending:
            for batch in map_group.grass_batches:
                if batch.map_data_uuid == map_uuid:
                    has_pending = True
                    break

        if has_pending:
            pending_auto_uuids.append(map_uuid)

    for map_uuid in pending_auto_uuids:
        map_data = map_group.find_map(map_uuid)
        if map_data is not None:
            generate_partitions(map_group, map_data, settings)


def create_map_data_assets(map_group: MapGroup) -> list[ExportBundle]:
    # Pre-compute which maps are parents (have children pointing to them)
    parent_map_uuids = set()
    for map_data in map_group.maps:
        if map_data.parent_uuid:
            parent_map_uuids.add(map_data.parent_uuid)

    # Maps with an incomplete LOD hierarchy: their entities' unresolved parent_index values are
    # exported verbatim instead of recomputed (see _export_entity)
    locked_map_uuids = {m.uuid for m in map_group.maps if m.incomplete_lod_hierarchy_lock}

    # Group entities, cargens, tcms, and grass batches by map_data_uuid
    entities_by_map: dict[bytes, list[MapEntity]] = defaultdict(list)
    for entity in map_group.entities:
        entities_by_map[entity.map_data_uuid].append(entity)

    cargens_by_map: dict[bytes, list[MapCarGenerator]] = defaultdict(list)
    cargen_objs_by_map: dict[bytes, list[Object]] = defaultdict(list)
    for cargen in map_group.cargens:
        for map_uuid, exported in _export_cargens(map_group, cargen).items():
            cargens_by_map[map_uuid].extend(exported)
        for map_uuid, objs in cargen.objects_by_map_data(map_group).items():
            cargen_objs_by_map[map_uuid].extend(objs)

    tcms_by_map: dict[bytes, list[MapTimecycleModifier]] = defaultdict(list)
    for tcm in map_group.timecycle_modifiers:
        tcms_by_map[tcm.map_data_uuid].append(tcm)

    grass_by_map: dict[bytes, list[MapGrassBatch]] = defaultdict(list)
    for grass_batch in map_group.grass_batches:
        grass_by_map[grass_batch.map_data_uuid].append(grass_batch)

        if obj := grass_batch.linked_object:
            disable_grass_batch_modifier_preview(obj, grass_batch)

    occl_by_map: dict[bytes, list[MapOccluder]] = defaultdict(list)
    for occl in map_group.occluders:
        occl_by_map[occl.map_data_uuid].append(occl)

    # Pre-compute lod_lights export data. Each item produces both an IOMapLodLights (for the child map)
    # and an IOMapDistantLodLights (for the parent map). The property items are also bucketed for the
    # extents computation (list-valued, so multiple children contribute to a parent's extents).
    lod_lights_by_child: dict[bytes, IOMapLodLights] = {}
    distant_lod_lights_by_parent: dict[bytes, IOMapDistantLodLights] = {}
    lls_by_map: dict[bytes, list[MapLodLights]] = defaultdict(list)
    distant_lls_by_parent: dict[bytes, list[MapLodLights]] = defaultdict(list)
    for ll in map_group.lod_lights:
        if not ll.map_data_uuid:
            continue
        lls_by_map[ll.map_data_uuid].append(ll)
        lod_lights, distant_lod_lights = _export_lod_lights(ll)
        lod_lights_by_child[ll.map_data_uuid] = lod_lights
        child_map = map_group.find_map(ll.map_data_uuid)
        if child_map is not None and child_map.parent_uuid:
            distant_lls_by_parent[child_map.parent_uuid].append(ll)
            distant_lod_lights_by_parent[child_map.parent_uuid] = distant_lod_lights

    # Pre-compute entity indices for parent_index recomputation.
    # For each entity, compute its index within its map data's entity list (preserving insertion order
    # for stable round-trips) and which map data it belongs to.
    entity_index_in_map: dict[bytes, int] = {}
    entity_map_data_uuid: dict[bytes, bytes] = {}
    entity_num_children = Counter()
    for map_uuid, entities in entities_by_map.items():
        for i, entity in enumerate(entities):
            entity_index_in_map[entity.uuid] = i
            entity_map_data_uuid[entity.uuid] = map_uuid
            if parent_uuid := entity.parent_uuid:
                entity_num_children[parent_uuid] += 1

    depsgraph = bpy.context.evaluated_depsgraph_get()
    asset_info_cache = AssetInfoCache()

    bundles = []
    for map_data in map_group.maps:
        map_data: MapData
        map_data_asset = AssetMapData()

        map_uuid = map_data.uuid

        # Grass maps have a special naming convention: <name> is the parent map name
        # and <parent> is empty. The actual filename is the leaf name (e.g. hw1_01_grass_0).
        is_grass_leaf = map_data.is_auto_generated and map_data.parent_uuid and "_grass_" in map_data.name

        if is_grass_leaf:
            parent_map_data = map_group.find_map(map_data.parent_uuid)
            map_data_asset.name = parent_map_data.name if parent_map_data else map_data.name
            # parent_name left empty (default)
        else:
            map_data_asset.name = map_data.name
            parent_map_data = map_group.find_map(map_data.parent_uuid) if map_data.parent_uuid else None
            if parent_map_data is not None:
                map_data_asset.parent_name = parent_map_data.name
            elif map_data.orig_parent_name:
                # Parent map was not imported (incomplete hierarchy): re-emit the original <parent>.
                map_data_asset.parent_name = map_data.orig_parent_name

        # Extents. Unless set manually, recalculate them from the map's items and store them back in
        # the map data so the UI and partitioning see the up-to-date values
        if not map_data.extents_manual:
            extents = calc_map_data_extents(
                map_group,
                depsgraph,
                entities=entities_by_map[map_uuid],
                cargen_objects=cargen_objs_by_map[map_uuid],
                tcms=tcms_by_map[map_uuid],
                grass_batches=grass_by_map[map_uuid],
                occluders=occl_by_map[map_uuid],
                lod_lights=lls_by_map[map_uuid],
                distant_lod_lights=distant_lls_by_parent[map_uuid],
                asset_info_cache=asset_info_cache,
            )
            if extents is not None:
                map_data.entities_extents, map_data.streaming_extents = extents

        map_data_asset.streaming_extents = (
            Vector(map_data.streaming_extents_min),
            Vector(map_data.streaming_extents_max),
        )
        map_data_asset.entities_extents = (
            Vector(map_data.entities_extents_min),
            Vector(map_data.entities_extents_max),
        )

        if map_data.desc_enabled:

            def _safe_int(v: str) -> int:
                try:
                    return int(v)
                except ValueError:
                    return 0

            map_data_asset.description = MapBlockDescription(
                name=map_data.desc_name,
                exported_by=map_data.desc_exported_by,
                owner=map_data.desc_owner,
                time=map_data.desc_time,
                version=_safe_int(map_data.desc_version),
                flags=_safe_int(map_data.desc_flags),
            )

        # Entities
        if map_entities := entities_by_map[map_uuid]:
            map_data_asset.entities = [
                _export_entity(e, entity_index_in_map, entity_map_data_uuid, entity_num_children, locked_map_uuids)
                for e in map_entities
            ]

        # Cargens
        if map_cargens := cargens_by_map[map_uuid]:
            map_data_asset.car_generators = map_cargens

        # Timecycle Modifiers
        if map_tcms := tcms_by_map[map_uuid]:
            map_data_asset.timecycle_modifiers = [_export_tcm(tcm) for tcm in map_tcms]

        # Grass Batches
        if map_grass := grass_by_map[map_uuid]:
            exported_grass = []
            for grass_batch in map_grass:
                exported_grass.extend(_export_grass_batch(grass_batch, depsgraph))
            map_data_asset.grass_instance_lists = exported_grass

        # Occluders
        box_occluders, model_occluders = [], []
        if map_occl := occl_by_map[map_uuid]:
            for occl in map_occl:
                b, m = _export_occluders(occl, depsgraph)
                box_occluders.extend(b)
                model_occluders.extend(m)
            map_data_asset.box_occluders = box_occluders
            map_data_asset.model_occluders = model_occluders

        # LOD Lights (on child map)
        if map_uuid in lod_lights_by_child:
            map_data_asset.lod_lights = lod_lights_by_child[map_uuid]

        # Distant LOD Lights (on parent map)
        if map_uuid in distant_lod_lights_by_parent:
            map_data_asset.distant_lod_lights = distant_lod_lights_by_parent[map_uuid]

        # Flags
        map_data_asset.flags = _compute_map_flags(map_group, map_uuid, parent_map_uuids)
        map_data_asset.content_flags = _compute_content_flags(
            map_entities,
            map_grass,
            has_occluders=bool(box_occluders or model_occluders),
            has_lod_lights=map_uuid in lod_lights_by_child,
            has_distant_lod_lights=map_uuid in distant_lod_lights_by_parent,
            has_block_description=map_data.desc_enabled,
        )

        bundle = export_context().make_bundle(map_data_asset, name_override=map_data.name)
        bundles.append(bundle)

    return bundles


def calc_map_entity_transforms_from_object(entity: MapEntity) -> tuple[Vector, Quaternion, float, float]:
    """Get the transforms of an entity based on its linked Blender object."""
    transform = entity.linked_object.matrix_world
    location, rotation, scale = transform.decompose()

    # Update entity transform from object transform
    entity.position = location
    entity.rotation = rotation
    entity.scale_xy = scale.x
    entity.scale_z = scale.z

    return location, rotation if entity.is_mlo else rotation.inverted(), scale.x, scale.z


def calc_map_entity_transforms(entity: MapEntity) -> tuple[Vector, Quaternion, float, float]:
    if entity.linked_object is not None:
        return calc_map_entity_transforms_from_object(entity)

    return (
        Vector(entity.position),
        Quaternion(entity.rotation if entity.is_mlo else entity.rotation.inverted()),
        entity.scale_xy,
        entity.scale_z,
    )


def _export_entity(
    e: MapEntity,
    entity_index_in_map: dict[bytes, int],
    entity_map_data_uuid: dict[bytes, bytes],
    entity_num_children: dict[bytes, int],
    locked_map_uuids: set[bytes],
) -> Entity | EntityMloInstance:
    entity_flags = EntityFlags(int(e.flags.total))

    # Children found via parent_uuid links (tracks edits in unlocked containers)
    num_children = entity_num_children.get(e.uuid, 0)
    if e.map_data_uuid in locked_map_uuids:
        # ...plus children known to be in non-imported .ymap files.
        num_children += e.num_children_missing

    if e.parent_uuid:
        # Resolved parent: always recompute, even in locked containers. The parent may live in an
        # unlocked, editable container; when nothing was edited this equals the imported values
        # because a locked container's own entity list is frozen.
        parent_index = entity_index_in_map.get(e.parent_uuid, -1)

        parent_map_uuid = entity_map_data_uuid.get(e.parent_uuid, None)
        if parent_map_uuid is not None and parent_map_uuid != e.map_data_uuid:
            # Parent is in a different map data (cross-map LOD reference)
            entity_flags |= EntityFlags.LOD_IN_PARENT_MAP
        else:
            # Parent is in the same map data, ensure flag is not set
            entity_flags &= ~EntityFlags.LOD_IN_PARENT_MAP
        lod_level = EntityLodLevel[e.lod_level]
    elif e.map_data_uuid in locked_map_uuids and e.parent_index != -1:
        # Unresolvable parent in a non-imported .ymap: preserve parent_index verbatim, flags
        # untouched so LOD_IN_PARENT_MAP round-trips.
        parent_index = e.parent_index
        lod_level = EntityLodLevel[e.lod_level]
    else:
        # No parent. An HD entity without a parent is ORPHANHD.
        parent_index = -1
        lod_level = EntityLodLevel.ORPHANHD if e.lod_level == "HD" else EntityLodLevel[e.lod_level]

    if e.linked_object is not None:
        archetype_name = remove_number_suffix(e.linked_object.name).lower()
        e.archetype_name = archetype_name
    else:
        archetype_name = e.archetype_name

    pos, rot, scale_xy, scale_z = calc_map_entity_transforms(e)
    common = dict(
        archetype_name=archetype_name,
        position=pos,
        rotation=rot,
        scale_xy=scale_xy,
        scale_z=scale_z,
        flags=entity_flags,
        guid=0,
        parent_index=parent_index,
        lod_dist=e.lod_dist,
        child_lod_dist=e.child_lod_dist,
        lod_level=lod_level,
        priority_level=EntityPriorityLevel[e.priority_level],
        num_children=num_children,
        ambient_occlusion_multiplier=e.ambient_occlusion_multiplier,
        artificial_ambient_occlusion=e.artificial_ambient_occlusion,
        tint_value=e.tint_value,
        extensions=[],
    )

    if e.is_mlo:
        mlo_flags = EntityMloInstanceFlags(0)
        if e.mlo_turn_on_gps:
            mlo_flags |= EntityMloInstanceFlags.TURN_ON_GPS
        if e.mlo_cap_entities_alpha:
            mlo_flags |= EntityMloInstanceFlags.CAP_ENTITIES_ALPHA
        if e.mlo_short_fade_distance:
            mlo_flags |= EntityMloInstanceFlags.SHORT_FADE_DISTANCE

        return EntityMloInstance(
            **common,
            group_id=e.mlo_group_id,
            floor_id=e.mlo_floor_id,
            default_entity_sets=[s.strip() for s in e.mlo_default_entity_sets.split(",") if s.strip()],
            num_exit_portals=e.mlo_num_exit_portals,
            mlo_inst_flags=mlo_flags,
        )

    return Entity(**common)


def _export_cargens(map_group: MapGroup, cargen: MapCarGen) -> dict[bytes, list[MapCarGenerator]]:
    """Exported car generator instances grouped by the container UUID each object is assigned to."""
    flags = MapCarGeneratorFlags(0)
    for prop_name, flag in MAP_CARGEN_FLAG_PROPS:
        if getattr(cargen, prop_name):
            flags |= flag
    creation_rule = MapCarGeneratorCreationRule[cargen.creation_rule]

    results = {}
    for map_uuid, objs in cargen.objects_by_map_data(map_group).items():
        exported = []
        for obj in objs:
            angle = -obj.rotation_euler.z
            width, length, _ = obj.dimensions
            orient_x = math.sin(angle) * length
            orient_y = math.cos(angle) * length

            exported.append(
                MapCarGenerator(
                    position=Vector(obj.location),
                    orient_x=orient_x,
                    orient_y=orient_y,
                    perpendicular_length=width,
                    car_model=cargen.model,
                    flags=flags,
                    creation_rule=creation_rule,
                    body_color_remap_1=cargen.body_color_remap[0],
                    body_color_remap_2=cargen.body_color_remap[1],
                    body_color_remap_3=cargen.body_color_remap[2],
                    body_color_remap_4=cargen.body_color_remap[3],
                    pop_group=cargen.model_set,
                    livery=cargen.livery,
                )
            )
        results[map_uuid] = exported

    return results


def _export_tcm(tcm: MapTimecycleModifier) -> IOMapTimeCycleModifier:
    return IOMapTimeCycleModifier(
        name=tcm.name,
        extents=tcm.extents,
        percentage=tcm.percentage,
        range=tcm.range,
        start_hour=tcm.start_hour,
        end_hour=tcm.end_hour,
    )


def _export_grass_batch(batch: MapGrassBatch, depsgraph: Depsgraph) -> list[MapGrassInstanceList]:
    obj = batch.linked_object
    if obj is None or obj.data is None:
        return []

    positions, color_ao, normal_scale, template_indices, _partition_indices = (
        evaluated_grass_batch_instances_from_object(obj, depsgraph)
    )
    partition_indices = partition_grass_batch_instances(positions, template_indices)
    num_verts = len(positions)

    # Build unpacked instances array
    unpacked = np.empty(num_verts, dtype=MAP_GRASS_INSTANCES_UNPACKED_DTYPE)
    unpacked["Position"] = positions
    unpacked["Normal"] = normal_scale[:, :2]
    unpacked["Color"] = color_ao[:, :3]
    unpacked["Scale"] = normal_scale[:, 2]
    unpacked["Ao"] = color_ao[:, 3]

    # Group by partition_index and create one MapGrassInstanceList per partition
    unique_partitions = np.unique(partition_indices)
    results = []

    for partition_idx in unique_partitions:
        mask = partition_indices == partition_idx
        partition_instances = unpacked[mask]
        partition_template_indices = template_indices[mask]

        # All instances in a partition share the same template
        tidx = partition_template_indices[0]
        if tidx < 0 or tidx >= len(batch.templates):
            continue

        template = batch.templates[tidx]

        grass_list = MapGrassInstanceList(
            extents=(Vector((0, 0, 0)), Vector((0, 0, 0))),  # pack_instances will compute
            scale_range=Vector((template.scale_range.x, template.scale_range.y, template.scale_randomness)),
            archetype_name=template.archetype_name,
            lod_dist=template.lod_dist,
            lod_fade_start_dist=template.lod_fade_start_dist,
            lod_inst_fade_range=template.lod_inst_fade_range,
            orient_to_terrain=template.orient_to_terrain,
            instances=np.empty(0),  # pack_instances will fill
        )
        grass_list.pack_instances(partition_instances)
        results.append(grass_list)

    return results


_MODEL_OCCLUDER_MAX_VERTS = 255


def _export_occluders(occl: MapOccluder, depsgraph: Depsgraph) -> tuple[list[MapBoxOccluder], list[MapModelOccluder]]:
    obj = occl.linked_object
    if obj is None or obj.data is None:
        return [], []

    obj_eval = obj.evaluated_get(depsgraph)
    mesh_eval = obj_eval.to_mesh()
    try:
        num_verts = len(mesh_eval.vertices)
        if num_verts == 0:
            return [], []

        local_co = np.empty((num_verts, 3), dtype=np.float32)
        mesh_eval.vertices.foreach_get("co", local_co.ravel())
        mw = np.array(obj.matrix_world, dtype=np.float32)
        world_co = local_co @ mw[:3, :3].T + mw[:3, 3]

        face_flags = np.zeros(len(mesh_eval.polygons), dtype=np.int32)
        flags_attr = mesh_eval.attributes.get(".occl.flags", None)
        if flags_attr is not None and flags_attr.domain == "FACE" and flags_attr.data_type == "INT":
            flags_attr.data.foreach_get("value", face_flags)

        mesh_eval.calc_loop_triangles()
        islands = mesh_linked_triangles(mesh_eval)

        boxes = []
        models = []

        # Non-box triangles are pooled by flag (each MapModelOccluder has a single flag), then
        # the pool is combined and greedily split so chunks can pack triangles across original
        # islands and produce fewer occluders than splitting each island in isolation.
        model_pool: dict[int, list[tuple[np.ndarray, np.ndarray]]] = defaultdict(list)

        for island in islands:
            if not island:
                continue

            island_tris = np.array([lt.vertices[:] for lt in island], dtype=np.int32)
            tri_flags = np.fromiter(
                (face_flags[tri.polygon_index] for tri in island), dtype=np.int32, count=len(island)
            )
            uniq_vert_indices_in_island_tris, uniq_inverse = np.unique(island_tris, return_inverse=True)

            # A box occluder is a cube (8 verts) or a plane (4 verts).
            if len(uniq_vert_indices_in_island_tris) in (4, 8) and bool(np.all(tri_flags == 0)):
                box_verts = world_co[uniq_vert_indices_in_island_tris]
                box_tris = uniq_inverse.reshape(-1, 3)  # island_tris remapped to 0..len(uniq)-1
                if box := _try_export_box_occluder(box_verts, box_tris):
                    boxes.append(box)
                    continue

            # A single island may have multiple flag values, split the triangles by flag
            for flag_val in np.unique(tri_flags):
                mask = tri_flags == flag_val
                sub_tris = island_tris[mask]
                sub_tris_uniq, sub_tris_inverse_index = np.unique(sub_tris, return_inverse=True)
                model_pool[int(flag_val)].append((world_co[sub_tris_uniq], sub_tris_inverse_index.reshape(-1, 3)))

        for flag_value, parts in model_pool.items():
            tris_list = []
            offset = 0
            for v, t in parts:
                tris_list.append(t + offset)
                offset += len(v)
            combined_verts = np.concatenate([v for v, _ in parts])
            combined_tris = np.concatenate(tris_list)
            models.extend(_export_model_occluders(combined_verts, combined_tris, flag_value))

        return boxes, models
    finally:
        obj_eval.to_mesh_clear()


def _try_export_box_occluder(verts: np.ndarray, tris: np.ndarray) -> MapBoxOccluder | None:
    """Build a box occluder from a mesh island if its vertices form a Z-rotated cube or a vertical/horizontal plane."""
    recovered = recover_box_occluder(verts)
    if recovered is None:
        return None

    # Vertices form a valid box, make sure the topology is actually a solid cube/plane
    if not box_island_is_valid(verts, tris, recovered):
        return None

    center, size, cos, sin = recovered
    box = MapBoxOccluder(0, 0, 0, 0, 0, 0, 0, 0)
    box.center = center
    box.size = size
    box.cos_sin_z = (cos, sin)
    return box


def _export_model_occluders(
    verts: np.ndarray,
    tris: np.ndarray,
    flag_value: int,
) -> list[MapModelOccluder]:
    if len(verts) <= _MODEL_OCCLUDER_MAX_VERTS:
        return [
            MapModelOccluder(
                flags=MapModelOccluderFlags(flag_value),
                vertices=verts.astype(np.float32, copy=False),
                indices=tris.astype(np.uint8, copy=False),
            )
        ]

    centroids = verts[tris].mean(axis=1)
    axis = int(np.argmax(centroids.max(axis=0) - centroids.min(axis=0)))
    sorted_tris = tris[np.argsort(centroids[:, axis])]

    chunk_remap: dict[int, int] = {}
    chunk_tris: list[list[int]] = []

    models = []

    def _flush() -> None:
        models.append(
            MapModelOccluder(
                flags=MapModelOccluderFlags(flag_value),
                vertices=verts[list(chunk_remap)].astype(np.float32, copy=False),
                indices=np.array(chunk_tris, dtype=np.uint8),
            )
        )
        chunk_remap.clear()
        chunk_tris.clear()

    for tri in sorted_tris:
        tri_g = (int(tri[0]), int(tri[1]), int(tri[2]))
        new_count = sum(1 for v in set(tri_g) if v not in chunk_remap)
        if chunk_remap and len(chunk_remap) + new_count > _MODEL_OCCLUDER_MAX_VERTS:
            _flush()
        for v in tri_g:
            if v not in chunk_remap:
                chunk_remap[v] = len(chunk_remap)
        chunk_tris.append([chunk_remap[v] for v in tri_g])

    if chunk_tris:
        _flush()

    return models


def _export_lod_lights(ll: MapLodLights) -> tuple[IOMapLodLights, IOMapDistantLodLights]:
    obj = ll.linked_object
    mesh = obj.data
    num_verts = len(mesh.vertices)

    positions = np.empty((num_verts, 3), dtype=np.float32)
    mesh.vertices.foreach_get("co", positions.ravel())

    from .lod_lights import LodLightAttr, mesh_get_lod_light_attribute_values

    rgbi_float = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.RGBI)
    rgbi_float *= 255.0
    rgbi_float.clip(0.0, 255.0, out=rgbi_float)
    rgbi = rgbi_float.astype(np.uint8)
    direction = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.DIRECTION)
    falloff = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.FALLOFF)
    falloff_exp = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.FALLOFF_EXP)
    flags = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.FLAGS).view(np.uint32)
    hash = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.HASH).view(np.uint32)
    cone_inner = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.CONE_INNER_ANGLE).astype(np.uint8)
    cone_outer = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.CONE_OUTER_ANGLE).astype(np.uint8)
    corona_intensity = mesh_get_lod_light_attribute_values(mesh, LodLightAttr.CORONA_INTENSITY).astype(np.uint8)

    # Sort by streetlight status (bit 24 of flags, streetlights first) then by hash ascending
    is_streetlight = (flags >> 24) & 1
    sort_order = np.lexsort((hash, 1 - is_streetlight))
    num_street_lights = int(np.sum(is_streetlight))

    positions = positions[sort_order]
    rgbi = rgbi[sort_order]
    direction = direction[sort_order]
    falloff = falloff[sort_order]
    falloff_exp = falloff_exp[sort_order]
    flags = flags[sort_order]
    hash = hash[sort_order]
    cone_inner = cone_inner[sort_order]
    cone_outer = cone_outer[sort_order]
    corona_intensity = corona_intensity[sort_order]

    distant_lod_lights = np.empty(num_verts, dtype=MAP_DISTANT_LOD_LIGHT_DTYPE)
    distant_lod_lights["Position"] = positions
    distant_lod_lights["RGBI"] = rgbi

    lod_lights = np.empty(num_verts, dtype=MAP_LOD_LIGHT_DTYPE)
    lod_lights["Direction"] = direction
    lod_lights["Falloff"] = falloff
    lod_lights["FalloffExponent"] = falloff_exp
    lod_lights["TimeAndStateFlags"] = flags
    lod_lights["Hash"] = hash
    lod_lights["ConeInnerAngle"] = cone_inner
    lod_lights["ConeOuterAngleOrCapExt"] = cone_outer
    lod_lights["CoronaIntensity"] = corona_intensity

    return (
        IOMapLodLights(lights=lod_lights),
        IOMapDistantLodLights(
            lights=distant_lod_lights,
            num_street_lights=num_street_lights,
            category=MapLodLightCategory[ll.category],
        ),
    )


def _compute_map_flags(map_group: MapGroup, map_uuid: bytes, parent_map_uuids: set[bytes]) -> MapFlags:
    flags = MapFlags(0)
    if map_group.scripted:
        flags |= MapFlags.SCRIPTED
    if map_uuid in parent_map_uuids:
        flags |= MapFlags.IS_PARENT
    return flags


def _compute_content_flags(
    entities: list[MapEntity],
    grass_batches: list[MapGrassBatch],
    has_occluders: bool = False,
    has_lod_lights: bool = False,
    has_distant_lod_lights: bool = False,
    has_block_description: bool = False,
) -> MapContentFlags:
    flags = MapContentFlags(0)

    for e in entities:
        lod = e.lod_level
        if lod == "HD":
            flags |= MapContentFlags.HAS_ENTITIES_HD
        elif lod in ("LOD", "SLOD1"):
            flags |= MapContentFlags.HAS_ENTITIES_LOD
        elif lod in ("SLOD2", "SLOD3", "SLOD4"):
            flags |= MapContentFlags.HAS_ENTITIES_CONTAINER_LOD
        if e.is_mlo:
            flags |= MapContentFlags.HAS_MLO_INSTANCE
        if e.is_critical:
            flags |= MapContentFlags.HAS_ENTITIES_CRITICAL

    if grass_batches:
        flags |= MapContentFlags.HAS_INSTANCED_DATA

    if has_occluders:
        flags |= MapContentFlags.HAS_OCCLUDERS

    if has_lod_lights:
        flags |= MapContentFlags.HAS_LOD_LIGHTS

    if has_distant_lod_lights:
        flags |= MapContentFlags.HAS_DISTANT_LOD_LIGHTS

    if has_block_description:
        flags |= MapContentFlags.HAS_BLOCK_DESCRIPTION

    return flags
