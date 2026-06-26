import math
from collections import defaultdict
from collections.abc import Iterator, Sequence
from typing import NamedTuple

import bpy
import numpy as np
from bpy.types import (
    Material,
)
from mathutils import Euler, Quaternion, Vector
from szio.gta5 import (
    AssetMapData,
    Entity,
    EntityFlags,
    EntityLodLevel,
    EntityMloInstance,
    EntityMloInstanceFlags,
    EntityPriorityLevel,
    Extension,
    ExtensionLightEffect,
    MapBoxOccluder,
    MapCarGeneratorCreationRule,
    MapCarGeneratorFlags,
    MapContentFlags,
    MapDistantLodLights,
    MapFlags,
    MapGrassInstanceList,
    MapLodLights,
    MapModelOccluder,
)
from szio.gta5 import (
    MapCarGenerator as IOMapCarGen,
)
from szio.gta5 import (
    MapTimeCycleModifier as IOMapTimeCycleModifier,
)

from .. import logger
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_blender_object
from .properties.map import (
    MAP_CARGEN_FLAG_PROPS,
    MapCarGen,
    MapData,
    MapEntity,
    MapGrassBatch,
    MapGroup,
    MapOccluder,
    MapTimecycleModifier,
    get_maps,
)
from .instancing import batch_add_map_entity, batch_instance_map_entities
from .occluders.box import box_occluder_world_geometry

_import_maps = []
_import_instance_entities = None


class MapKey(NamedTuple):
    map_index: int


class EntityKey(NamedTuple):
    map_key: MapKey
    entity_index: int


class LodHierarchy:
    __slots__ = (
        "maps",
        "map_by_name",
        "name_by_map",
        "entities_by_map",
        "root_maps",
        "children_maps_by_map",
        "parent_map_by_map",
        "children_entities_by_entity",
        "parent_entity_by_entity",
        "_maps_to_link",
        "_entities_to_link",
        "occluder_maps",
        "incomplete_maps",
    )

    def __init__(self):
        # Contents
        self.maps: list[AssetMapData] = []
        self.name_by_map: list[str] = []
        self.map_by_name: dict[str, MapKey] = {}
        self.entities_by_map: list[list[Entity]] = []

        # Hierarchy collections
        self.root_maps: list[MapKey] = []
        self.children_maps_by_map: list[list[MapKey]] = []
        self.parent_map_by_map: list[MapKey | None] = []
        self.children_entities_by_entity: dict[EntityKey, list[EntityKey]] = {}
        self.parent_entity_by_entity: dict[EntityKey, EntityKey | None] = {}

        self._maps_to_link: list[(MapKey, str)] = []
        self._entities_to_link: list[EntityKey] = []

        self.occluder_maps: list[MapKey] = []

        # Maps whose LOD hierarchy could not be fully reconstructed because related .ymap files
        # were not imported (missing parent map, missing parent entity, or child-count mismatch).
        # Their groups are locked so their hierarchy values are preserved as-is on export.
        self.incomplete_maps: set[MapKey] = set()

    def get_entity(self, key: EntityKey) -> Entity:
        return self.get_map_entities(key.map_key)[key.entity_index]

    def get_entity_parent(self, key: EntityKey) -> EntityKey | None:
        return self.parent_entity_by_entity[key]

    def get_map(self, key: MapKey) -> AssetMapData:
        return self.maps[key.map_index]

    def get_map_name(self, key: MapKey) -> str:
        return self.name_by_map[key.map_index]

    def get_map_entities(self, key: MapKey) -> list[Entity]:
        return self.entities_by_map[key.map_index]

    def get_map_parent(self, key: MapKey) -> MapKey | None:
        return self.parent_map_by_map[key.map_index]

    def get_map_children(self, key: MapKey) -> list[MapKey]:
        return self.children_maps_by_map[key.map_index]

    def get_map_children_recursive(self, key: MapKey) -> list[MapKey]:
        result: list[MapKey] = []
        stack = list(self.get_map_children(key))

        while stack:
            current = stack.pop()
            result.append(current)
            stack.extend(self.get_map_children(current))

        return result

    def iter_map_children_recursive(self, key: MapKey) -> Iterator[MapKey]:
        for child in self.get_map_children(key):
            yield child
            yield from self.iter_map_children_recursive(child)

    def add_map(self, map_asset: AssetMapData, name: str) -> MapKey:
        assert name not in self.map_by_name

        map_idx = len(self.maps)
        map_key = MapKey(map_idx)
        self.maps.append(map_asset)
        self.name_by_map.append(name)
        self.map_by_name[name] = map_key
        self.entities_by_map.append(map_asset.entities)

        self.children_maps_by_map.append([])
        self.parent_map_by_map.append(None)

        if MapContentFlags.HAS_OCCLUDERS in map_asset.content_flags:
            self.occluder_maps.append(map_key)
        else:
            parent_name = map_asset.parent_name
            if MapContentFlags.HAS_INSTANCED_DATA in map_asset.content_flags:
                # grass maps are not actually part of the LOD hierarchy so they don't really have parent but its name
                # contains the map they "belong" to, not the actual grass map filename (at least on vanilla maps)
                if map_asset.name != name:
                    parent_name = map_asset.name

            if parent_name:
                self._maps_to_link.append((map_key, parent_name))
            else:
                self.root_maps.append(map_key)

        for entity_idx, entity in enumerate(self.entities_by_map[map_idx]):
            entity_key = EntityKey(map_key, entity_idx)
            self.children_entities_by_entity[entity_key] = []
            self.parent_entity_by_entity[entity_key] = None

            if entity.parent_index != -1:
                self._entities_to_link.append(entity_key)

        return map_key

    def link(self) -> bool:
        # Both passes must run; do NOT short-circuit with `and`. _link_maps() must run first: it
        # populates parent_map_by_map and appends promoted (missing-parent) maps to root_maps, both
        # of which _link_entities() and get_map_children_recursive() rely on.
        ok_maps = self._link_maps()
        ok_entities = self._link_entities()
        return ok_maps and ok_entities

    def _link_maps(self) -> bool:
        if not self._maps_to_link:
            return True

        success = True
        for map_key, parent_map_name in self._maps_to_link:
            parent_map_key = self.map_by_name.get(parent_map_name, None)
            if parent_map_key is None:
                map = self.get_map(map_key)
                if MapContentFlags.HAS_INSTANCED_DATA in map.content_flags:
                    # it is okay for grass maps not to be imported with the other maps
                    self.root_maps.append(map_key)
                    continue

                map_name = self.get_map_name(map_key)
                logger.warning(
                    f"Map '{map_name}' is missing its parent map '{parent_map_name}' in LOD "
                    f"hierarchy. Have you imported all related .ymap files?"
                )
                # Keep the map: promote it to a root so it is still imported (instead of being
                # silently dropped), and mark it incomplete so its LOD hierarchy values are
                # preserved as-is on export.
                self.root_maps.append(map_key)
                self.incomplete_maps.add(map_key)
                success = False
                continue

            self.children_maps_by_map[parent_map_key.map_index].append(map_key)
            self.parent_map_by_map[map_key.map_index] = parent_map_key

        return success

    def _link_entities(self) -> bool:
        if not self._entities_to_link:
            return True

        success = True
        for entity_key in self._entities_to_link:
            entity = self.get_entity(entity_key)

            if EntityFlags.LOD_IN_PARENT_MAP in entity.flags:
                parent_map_key = self.parent_map_by_map[entity_key.map_key.map_index]
                if parent_map_key is None:
                    map_name = self.get_map_name(entity_key.map_key)
                    logger.warning(
                        f"Map '{map_name}', entity #{entity_key.entity_index} ({entity.archetype_name}) is missing its parent in LOD "
                        f"hierarchy. Have you imported all related .ymap files?"
                    )
                    self.incomplete_maps.add(entity_key.map_key)
                    success = False
                    continue
                possible_parents = self.get_map_entities(parent_map_key)
            else:
                parent_map_key = entity_key.map_key
                possible_parents = self.get_map_entities(entity_key.map_key)

            if 0 <= entity.parent_index < len(possible_parents):
                parent_entity_key = EntityKey(parent_map_key, entity.parent_index)
                self.children_entities_by_entity[parent_entity_key].append(entity_key)
                self.parent_entity_by_entity[entity_key] = parent_entity_key
            else:
                map_name = self.get_map_name(entity_key.map_key)
                logger.warning(
                    f"Map '{map_name}', entity #{entity_key.entity_index} ({entity.archetype_name}) is missing its parent in LOD "
                    f"hierarchy. Have you imported all related .ymap files?"
                )
                self.incomplete_maps.add(entity_key.map_key)
                success = False
                continue

        return success

    def validate(self) -> bool:
        success = True

        # Check that there aren't missing entities in the LOD hierarchy
        for map_idx, map in enumerate(self.maps):
            map_key = MapKey(map_idx)
            for entity_idx, entity in enumerate(self.entities_by_map[map_idx]):
                entity_key = EntityKey(map_key, entity_idx)
                expected_num_children = entity.num_children
                found_num_children = len(self.children_entities_by_entity[entity_key])
                if expected_num_children != found_num_children:
                    map_name = self.get_map_name(map_key)
                    # TODO: if there are more than 5 or so entities missing children, show a different error log, this can be too spammy
                    logger.warning(
                        f"Map '{map_name}', entity #{entity_idx} ({entity.archetype_name}) is missing children in LOD "
                        f"hierarchy (found {found_num_children}, expected {expected_num_children}). Have you imported "
                        f"all related .ymap files?"
                    )
                    self.incomplete_maps.add(map_key)
                    success = False

        # Check for scripted flag mismatches
        for root_map_key in self.root_maps:
            root_map = self.get_map(root_map_key)
            root_map_is_scripted = MapFlags.SCRIPTED in root_map.flags
            for child_map_key in self.iter_map_children_recursive(root_map_key):
                child_map = self.get_map(child_map_key)
                child_map_is_scripted = MapFlags.SCRIPTED in child_map.flags
                if root_map_is_scripted != child_map_is_scripted:
                    root_map_name = self.get_map_name(root_map_key)
                    child_map_name = self.get_map_name(child_map_key)
                    root_map_is_scripted_str = "scripted" if root_map_is_scripted else "non-scripted"
                    child_map_is_scripted_str = "scripted" if child_map_is_scripted else "non-scripted"
                    logger.error(
                        f"Scripted flag mismatch between map '{root_map_name}' ({root_map_is_scripted_str}) and "
                        f"its child map '{child_map_name}' ({child_map_is_scripted_str})."
                    )
                    success = False

        return success

    def hierarchy_to_text(
        self, root_map_key: MapKey, map_group_name: str, map_group_uuid: bytes, entities_ids: dict[EntityKey, bytes]
    ):
        root_entities = []
        for map_key in [root_map_key] + self.get_map_children_recursive(root_map_key):
            for entity_idx, entity in enumerate(self.get_map_entities(map_key)):
                entity_key = EntityKey(map_key, entity_idx)
                if entity.parent_index == -1 and entity.lod_level != EntityLodLevel.ORPHANHD:
                    root_entities.append(entity_key)

        s = ""

        def traverse(entity_key, depth):
            nonlocal s
            entity = self.get_entity(entity_key)
            indent = "  " * depth
            s += f"{entity.lod_level.name:>5} {indent}{entity.archetype_name}\n"

            for child_key in self.children_entities_by_entity[entity_key]:
                traverse(child_key, depth + 1)

        for root_entity_key in root_entities:
            traverse(root_entity_key, 0)
            s += "==========================\n"

        text = bpy.data.texts.new(f"{map_group_name}.lod_hierarchy")
        text.write(s)

    def hierarchy_to_db(
        self, root_map_key: MapKey, map_group_name: str, map_group_uuid: bytes, entities_ids: dict[EntityKey, bytes]
    ):
        import sqlite3
        import time

        t0 = time.perf_counter()
        entities = []
        for map_key in [root_map_key] + self.get_map_children_recursive(root_map_key):
            for entity_idx, entity in enumerate(self.get_map_entities(map_key)):
                entity_key = EntityKey(map_key, entity_idx)
                if entity.parent_index == -1 and entity.lod_level != EntityLodLevel.ORPHANHD:
                    root_entity_uuid = entities_ids[entity_key]
                    entities.append((root_entity_uuid, None))
                    stack = [(root_entity_uuid, self.children_entities_by_entity[entity_key])]
                    while stack:
                        parent_entity_uuid, children_keys = stack.pop()
                        for child_entity_key in children_keys:
                            child_entity_uuid = entities_ids[child_entity_key]

                            if grandchildren_keys := self.children_entities_by_entity[child_entity_key]:
                                stack.append((child_entity_uuid, grandchildren_keys))

                            entities.append((child_entity_uuid, parent_entity_uuid))

        t1 = time.perf_counter()
        conn = sqlite3.connect(f"D:\\re\\gta5\\sollumz\\maps\\country_06\\New folder\\{map_group_name}.db")
        try:
            conn.execute("PRAGMA foreign_keys = ON")

            conn.execute("""
            CREATE TABLE entities (
                uuid        BLOB(16) PRIMARY KEY,
                parent_uuid BLOB(16) REFERENCES entities(uuid) ON DELETE SET NULL
            )
            """)

            conn.execute("CREATE INDEX idx_entities_parent_uuid ON entities(parent_uuid)")
            conn.executemany("INSERT INTO entities (uuid, parent_uuid) VALUES (?, ?)", entities)
            conn.commit()
            t2 = time.perf_counter()
        finally:
            conn.close()
        t3 = time.perf_counter()

        print("Build entities list", t1 - t0)
        print("Create DB", t2 - t1)
        print("Create DB + close", t3 - t1)


def import_ymap(asset: AssetMapData, name: str):
    # Import is delayed because we need to know all the .ymaps we are importing first to build the LOD hierarchy
    # TODO: we can replace _import_maps with the LOD hierarchy directly
    _import_maps.append((asset, name))

    from ..iecontext import import_context

    global _import_instance_entities
    _import_instance_entities = import_context().settings.map_instance_entities


def begin_import_ymap_group():
    _import_maps.clear()


def end_import_ymap_group():
    if _import_maps:
        import_ymap_group(_import_maps)


def build_lod_hierarchy(maps: Sequence[tuple[AssetMapData, str]]) -> LodHierarchy:
    lod_hierarchy = LodHierarchy()
    for m, name in maps:
        lod_hierarchy.add_map(m, name)
    lod_hierarchy.link()
    lod_hierarchy.validate()
    return lod_hierarchy


def import_ymap_group(maps: Sequence[tuple[AssetMapData, str]]):
    lod_hierarchy = build_lod_hierarchy(maps)
    for root_map_key in lod_hierarchy.root_maps:
        children_maps = lod_hierarchy.get_map_children_recursive(root_map_key)
        all_maps = [root_map_key] + children_maps
        map_group: MapGroup = get_maps(create_if_missing=True).new_group()
        map_group_name = _longest_common_prefix([lod_hierarchy.get_map_name(map_key) for map_key in all_maps]).strip(
            "_"
        )
        if not map_group_name:
            # TODO(ymap): when there is no common prefix, find some better group name
            map_group_name = lod_hierarchy.get_map_name(root_map_key)
        map_group.name = map_group_name
        map_group.scripted = any(MapFlags.SCRIPTED in lod_hierarchy.get_map(map_key).flags for map_key in all_maps)
        # Lock the group if any of its maps has an incomplete LOD hierarchy, so its hierarchy values
        # are preserved as-is on export instead of being recomputed from the partial in-memory graph.
        map_group.incomplete_lod_hierarchy_lock = any(
            map_key in lod_hierarchy.incomplete_maps for map_key in all_maps
        )

        map_data_ids = {map_key: map_group.new_map().uuid for map_key in all_maps}

        entities_to_instance = defaultdict(list)
        entities_to_parent = []
        entities_ids = {}
        for map_key in all_maps:
            m = lod_hierarchy.get_map(map_key)
            name = lod_hierarchy.get_map_name(map_key)
            map_data = map_group.find_map(map_data_ids[map_key])
            map_data.name = name
            # Preserve the original map header <parent> string so a map whose parent .ymap was not
            # imported can re-emit it on export (parent_uuid stays empty in that case).
            map_data.orig_parent_name = m.parent_name
            parent_map_key = lod_hierarchy.get_map_parent(map_key)
            parent_map_data_uuid = map_data_ids.get(parent_map_key, None) if parent_map_key else None
            if parent_map_data_uuid:
                map_data.parent_uuid = parent_map_data_uuid
            map_data.streaming_extents = m.streaming_extents
            map_data.entities_extents = m.entities_extents
            # Keep the original extents on re-export instead of recalculating them
            map_data.extents_manual = True

            if m.description is not None and MapContentFlags.HAS_BLOCK_DESCRIPTION in m.content_flags:
                map_data.desc_enabled = True
                map_data.desc_name = m.description.name
                map_data.desc_exported_by = m.description.exported_by
                map_data.desc_owner = m.description.owner
                map_data.desc_time = m.description.time
                map_data.desc_version = str(m.description.version)
                map_data.desc_flags = str(m.description.flags)

            is_critical = MapContentFlags.HAS_ENTITIES_CRITICAL in m.content_flags
            for entity_idx, entity in enumerate(lod_hierarchy.get_map_entities(map_key)):
                entity_key = EntityKey(map_key, entity_idx)
                e = _create_map_entity(map_group, map_data, entity, is_critical)
                entities_ids[entity_key] = e.uuid

                if parent_entity_key := lod_hierarchy.get_entity_parent(entity_key):
                    entities_to_parent.append((entity_key, parent_entity_key))

                entity_data_idx = len(map_group.entities) - 1
                batch_add_map_entity(entities_to_instance, entity_data_idx, entity)

            if cargens := m.car_generators:
                _create_map_cargens(map_group, map_data, cargens)

            for tcm in m.timecycle_modifiers:
                _create_map_tcm(map_group, map_data, tcm)

            if grass_instance_lists := m.grass_instance_lists:
                _create_map_grass_batch(map_group, map_data, grass_instance_lists)

            if lod_lights := m.lod_lights:
                # TODO(ymap): include these checks in LodHierarchy
                assert parent_map_key is not None, "LodLights without parent DistantLodLights"
                parent = lod_hierarchy.get_map(parent_map_key)
                distant_lod_lights = parent.distant_lod_lights
                assert distant_lod_lights is not None, "LodLights without parent DistantLodLights"

                _create_map_lod_lights(map_group, map_data, lod_lights, distant_lod_lights)

        if entities_to_parent:
            for entity_key, parent_entity_key in entities_to_parent:
                entity_id = entities_ids[entity_key]
                parent_entity_id = entities_ids[parent_entity_key]
                entity = map_group.find_entity(entity_id)
                entity.parent_uuid = parent_entity_id

        # Link game assets from the shared asset library, if configured
        from ..sollumz_preferences import get_addon_preferences

        prefs = get_addon_preferences(bpy.context)
        if _import_instance_entities and prefs.shared_assets_directories:
            batch_instance_map_entities(map_group, entities_to_instance)

        _organize_map_in_collections(map_group)

        map_group.refresh_ui()

        # lod_hierarchy.hierarchy_to_text(root_map_key, map_group.name, map_group.uuid, entities_ids)
        # lod_hierarchy.hierarchy_to_db(root_map_key, map_group.name, map_group.uuid, entities_ids)

    # TODO(ymap): combine occluder maps with main hierarchy if possible
    for occl_map_key in lod_hierarchy.occluder_maps:
        occl_map = lod_hierarchy.get_map(occl_map_key)
        map_group = get_maps(create_if_missing=True).new_group()
        map_group.name = occl_map.name
        map_data = map_group.new_map()
        map_data.name = occl_map.name
        box_occluders = occl_map.box_occluders
        model_occluders = occl_map.model_occluders
        if box_occluders or model_occluders:
            _create_map_occluder(map_group, map_data, box_occluders, model_occluders)

        map_group.refresh_ui()

    if lod_hierarchy.incomplete_maps:
        logger.warning(
            "Imported an incomplete LOD hierarchy: some related .ymap files (parent or child maps) "
            "were not imported. The affected map group(s) have been locked - their LOD hierarchy "
            "values (parent index, number of children, parent map) are preserved as-is on export "
            "and some editing is disabled."
        )

    from .map_index import MAP_INDEX

    MAP_INDEX.invalidate_and_rebuild()


def _create_map_entity(map_group: MapGroup, map_data: MapData, entity: Entity, is_critical: bool) -> MapEntity:
    is_mlo = isinstance(entity, EntityMloInstance)
    e = map_group.new_entity()
    e.map_data_uuid = map_data.uuid
    e.archetype_name = entity.archetype_name
    e.position = entity.position
    e.rotation = entity.rotation if is_mlo else entity.rotation.inverted()
    e.scale_xy = entity.scale_xy
    e.scale_z = entity.scale_z
    e.flags.total = str(entity.flags.value)
    e.parent_index = entity.parent_index
    e.lod_dist = entity.lod_dist
    e.child_lod_dist = entity.child_lod_dist
    e.lod_level = "HD" if entity.lod_level == EntityLodLevel.ORPHANHD else entity.lod_level.name
    e.priority_level = entity.priority_level.name
    e.num_children = entity.num_children
    e.ambient_occlusion_multiplier = entity.ambient_occlusion_multiplier
    e.artificial_ambient_occlusion = entity.artificial_ambient_occlusion
    e.tint_value = entity.tint_value
    e.is_critical = is_critical

    if is_mlo:
        e.is_mlo = True
        e.mlo_group_id = entity.group_id
        e.mlo_floor_id = entity.floor_id
        e.mlo_default_entity_sets = ",".join(entity.default_entity_sets)
        e.mlo_num_exit_portals = entity.num_exit_portals
        e.mlo_turn_on_gps = EntityMloInstanceFlags.TURN_ON_GPS in entity.mlo_inst_flags
        e.mlo_cap_entities_alpha = EntityMloInstanceFlags.CAP_ENTITIES_ALPHA in entity.mlo_inst_flags
        e.mlo_short_fade_distance = EntityMloInstanceFlags.SHORT_FADE_DISTANCE in entity.mlo_inst_flags

    from ..ytyp.ytypimport_io import create_extension

    for extension in entity.extensions:
        create_extension(extension, e)

    return e


class CarGenTemplate(NamedTuple):
    model: str
    model_set: str
    flags: MapCarGeneratorFlags
    creation_rule: MapCarGeneratorCreationRule
    body_color_remap: tuple[int, int, int, int]
    livery: int

    @staticmethod
    def from_cargen(cargen: IOMapCarGen) -> "CarGenTemplate":
        return CarGenTemplate(
            model=cargen.car_model,
            model_set=cargen.pop_group,
            body_color_remap=cargen.body_color_remap,
            livery=cargen.livery,
            flags=cargen.flags,
            creation_rule=cargen.creation_rule,
        )


def _create_map_cargens(map_group: MapGroup, map_data: MapData, cargens: list[IOMapCarGen]):
    template_cargens: dict[CarGenTemplate, list[IOMapCarGen]] = defaultdict(list)
    for cargen in cargens:
        template = CarGenTemplate.from_cargen(cargen)
        template_cargens[template].append(cargen)

    cargen_ref_mesh = MapCarGen.get_cargen_mesh()

    for template, cargens in template_cargens.items():
        g = map_group.new_cargen()
        g.map_data_uuid = map_data.uuid
        g.model = template.model
        g.model_set = template.model_set
        g.body_color_remap = template.body_color_remap
        g.livery = template.livery
        for prop_name, flag in MAP_CARGEN_FLAG_PROPS:
            setattr(g, prop_name, flag in template.flags)
        g.creation_rule = template.creation_rule.name

        coll = bpy.data.collections.new(f"{map_data.name}.cargen.{g.ui_label}")
        for cargen in cargens:
            length = Vector((cargen.orient_x, cargen.orient_y)).length
            width = cargen.perpendicular_length

            angle = math.atan2(cargen.orient_x, cargen.orient_y)
            rot = Euler((0.0, 0.0, angle * -1))
            pos = cargen.position

            obj = create_blender_object(SollumType.NONE, "CarGen", cargen_ref_mesh, link_to_context_collection=False)
            obj.location = pos
            obj.rotation_euler = rot
            # cargen mesh has 1x1 XY dimensions, so scale matches the width/length in meters
            obj.scale = width, length, 1.0

            coll.objects.link(obj)

        g.linked_collection = coll


def _create_map_tcm(map_group: MapGroup, map_data: MapData, tcm: IOMapTimeCycleModifier) -> MapTimecycleModifier:
    m = map_group.new_tcm()
    m.map_data_uuid = map_data.uuid
    m.name = tcm.name
    m.extents = tcm.extents
    m.percentage = tcm.percentage
    m.range = tcm.range
    m.start_hour = tcm.start_hour
    m.end_hour = tcm.end_hour
    return m


class GrassTemplate(NamedTuple):
    scale_range: tuple[float, float, float]
    archetype_name: str
    lod_dist: int
    lod_fade_start_dist: float
    lod_inst_fade_range: float
    orient_to_terrain: float

    @staticmethod
    def from_instance_list(instance_list: MapGrassInstanceList) -> "GrassTemplate":
        return GrassTemplate(
            scale_range=tuple(instance_list.scale_range),
            archetype_name=instance_list.archetype_name,
            lod_dist=instance_list.lod_dist,
            lod_fade_start_dist=instance_list.lod_fade_start_dist,
            lod_inst_fade_range=instance_list.lod_inst_fade_range,
            orient_to_terrain=instance_list.orient_to_terrain,
        )


def _create_map_grass_batch(
    map_group: MapGroup, map_data: MapData, grass_instance_lists: list[MapGrassInstanceList]
) -> MapGrassBatch:
    b = map_group.new_grass_batch()
    b.map_data_uuid = map_data.uuid
    b.name = map_data.name

    templates = []
    template_to_index = {}

    instances = []
    instances_template_index = []
    instances_partition_index = []
    for partition_index, grass_instance_list in enumerate(grass_instance_lists):
        template = GrassTemplate.from_instance_list(grass_instance_list)
        template_index = template_to_index.get(template, None)
        if template_index is None:
            template_index = len(templates)
            templates.append(template)
            template_to_index[template] = template_index

        instances.append(grass_instance_list.unpack_instances())
        instances_template_index.append(np.full(len(grass_instance_list.instances), template_index, dtype=np.int32))
        instances_partition_index.append(np.full(len(grass_instance_list.instances), partition_index, dtype=np.int32))

    # Sort templates by archetype name
    templates_reorder = list(range(len(templates)))
    templates_reorder.sort(key=lambda i: templates[i].archetype_name)

    for template_index in templates_reorder:
        template = templates[template_index]
        t = b.templates.add()
        t.archetype_name = template.archetype_name
        t.scale_range = template.scale_range[:2]
        t.scale_randomness = template.scale_range[2]
        t.lod_dist = template.lod_dist
        t.lod_fade_start_dist = template.lod_fade_start_dist
        t.lod_inst_fade_range = template.lod_inst_fade_range
        t.orient_to_terrain = template.orient_to_terrain

    if instances:
        templates_reorder = np.array(templates_reorder)
        templates_reorder_inverse = np.empty_like(templates_reorder)
        templates_reorder_inverse[templates_reorder] = np.arange(len(templates_reorder))

        instances = np.concatenate(instances)
        instances_template_index = templates_reorder_inverse[np.concatenate(instances_template_index)]
        instances_partition_index = np.concatenate(instances_partition_index)

        verts = instances["Position"]
        name = f"{map_data.name}.instances"
        mesh = bpy.data.meshes.new(name)
        mesh.from_pydata(verts, [], [])

        from .grass import GrassBatchAttr, mesh_add_grass_batch_attribute

        color_ao = np.empty((len(instances), 4), dtype=np.float32)
        color_ao[:, :3] = instances["Color"]
        color_ao[:, 3] = instances["Ao"]
        mesh_attr = mesh_add_grass_batch_attribute(mesh, GrassBatchAttr.COLOR_AO)
        mesh_attr.data.foreach_set("color_srgb", color_ao.ravel())

        normal_scale = np.empty((len(instances), 3), dtype=np.float32)
        normal_scale[:, :2] = instances["Normal"]
        normal_scale[:, 2] = instances["Scale"]
        mesh_attr = mesh_add_grass_batch_attribute(mesh, GrassBatchAttr.NORMAL_SCALE)
        mesh_attr.data.foreach_set("vector", normal_scale.ravel())

        mesh_attr = mesh_add_grass_batch_attribute(mesh, GrassBatchAttr.TEMPLATE_INDEX)
        mesh_attr.data.foreach_set("value", instances_template_index.ravel())

        mesh_attr = mesh_add_grass_batch_attribute(mesh, GrassBatchAttr.PARTITION_INDEX)
        mesh_attr.data.foreach_set("value", instances_partition_index.ravel())

        obj = create_blender_object(SollumType.NONE, name, mesh)
        b.linked_object = obj

    from .grass.geonodes import add_grass_batch_modifier, create_grass_batch_geonodes, is_grass_batch_geonodes_supported

    if is_grass_batch_geonodes_supported():
        create_grass_batch_geonodes(b)
        if b.linked_object:
            add_grass_batch_modifier(b.linked_object, b)

    return b


def _get_occluder_material() -> Material:
    """Get occluder material or create it if not exist."""

    mat_name = ".sz.occluder"
    material = bpy.data.materials.get(mat_name)
    if material is None:
        from ..tools.blenderhelper import find_bsdf_and_material_output

        mat_transparency = 0.5
        mat_color = (1, 0, 0, mat_transparency)

        material = bpy.data.materials.new(mat_name)
        material.blend_method = "BLEND"
        if bpy.app.version < (5, 0, 0):
            material.use_nodes = True
        bsdf, _ = find_bsdf_and_material_output(material)
        bsdf.inputs["Alpha"].default_value = mat_transparency
        bsdf.inputs["Base Color"].default_value = mat_color
        bsdf.inputs["Specular IOR Level"].default_value = 0
        bsdf.inputs["Roughness"].default_value = 1
        bsdf.inputs["Metallic"].default_value = 0

        # For display in solid mode
        material.diffuse_color = mat_color
        material.roughness = 1

    return material


def _create_map_occluder(
    map_group: MapGroup,
    map_data: MapData,
    box_occluders: list[MapBoxOccluder],
    model_occluders: list[MapModelOccluder],
) -> MapOccluder:
    all_verts = []
    all_faces_quads = []
    all_faces_tris = []
    num_box_faces = 0
    offset = 0
    dropped_boxes = 0

    for box in box_occluders:
        c, s = box.cos_sin_z
        verts, quads = box_occluder_world_geometry(box.center, box.size, c, s)
        vert_count = len(verts)
        if vert_count == 0:
            # Didn't generate any geometry, >= 2 zero dimensions (only 1 case in vanilla game files, see sp1_occl_01.ymap)
            dropped_boxes += 1
            continue

        all_verts.append(verts)
        all_faces_quads.append(quads + offset)
        num_box_faces += len(quads)
        offset += vert_count

    if dropped_boxes:
        logger.warning(
            f"Map '{map_data.name}' has {dropped_boxes} degenerate line/point box occluder(s) "
            "(two or more zero dimensions). These occlude nothing and were skipped."
        )

    # Box occluders cannot have flags, always 0
    box_face_flags = np.zeros(num_box_faces, dtype=np.int32)

    if model_occluders:
        sizes = [len(m.vertices) for m in model_occluders]
        model_offsets = np.cumsum([0] + sizes[:-1])
        verts = np.concatenate([m.vertices for m in model_occluders])
        tris = np.concatenate([m.indices.astype(np.int32) + off for m, off in zip(model_occluders, model_offsets)])
        tri_flags = np.repeat(
            np.array([m.flags.value for m in model_occluders], dtype=np.int32),
            [len(m.indices) for m in model_occluders],
        )

        # Dedupe vertices across all models
        unique_verts, unique_inverse_index = np.unique(verts, axis=0, return_inverse=True)
        tris = unique_inverse_index[tris]

        # Remove triangles using the same vertex 2+ times, not valid in Blender meshes
        valid_tris_mask = (tris[:, 0] != tris[:, 1]) & (tris[:, 0] != tris[:, 2]) & (tris[:, 1] != tris[:, 2])
        tris = tris[valid_tris_mask]
        tri_flags = tri_flags[valid_tris_mask]

        all_verts.append(unique_verts)
        all_faces_tris.append(tris + offset)
        offset += len(unique_verts)
        model_face_flags = tri_flags
    else:
        model_face_flags = np.empty(0, dtype=np.int32)

    vertices = np.concatenate(all_verts) if all_verts else np.empty((0, 3), dtype=np.float32)
    faces = (np.concatenate(all_faces_quads).tolist() if all_faces_quads else []) + (
        np.concatenate(all_faces_tris).tolist() if all_faces_tris else []
    )
    face_flags = np.concatenate([box_face_flags, model_face_flags])

    occl_mesh = bpy.data.meshes.new(map_data.name)
    occl_mesh.from_pydata(vertices, [], faces)
    mesh_attr = occl_mesh.attributes.new(".occl.flags", "INT", "FACE")
    mesh_attr.data.foreach_set("value", face_flags)

    occl_obj = create_blender_object(SollumType.NONE, map_data.name, occl_mesh)
    occl_obj.active_material = _get_occluder_material()
    occl_obj.show_wire = True

    occl = map_group.new_occluder()
    occl.map_data_uuid = map_data.uuid
    occl.name = map_data.name
    occl.linked_object = occl_obj
    return occl


def _create_map_lod_lights(
    map_group: MapGroup, map_data: MapData, lod_lights: MapLodLights, distant_lod_lights: MapDistantLodLights
):
    assert len(lod_lights.lights) == len(distant_lod_lights.lights)

    ll = map_group.new_lod_lights()
    ll.map_data_uuid = map_data.uuid
    ll.name = map_data.name
    ll.category = distant_lod_lights.category.name

    verts = distant_lod_lights.lights["Position"]
    mesh = bpy.data.meshes.new(map_data.name)
    mesh.from_pydata(verts, [], [])

    from .lod_lights import LodLightAttr, mesh_add_lod_light_attribute

    rgbi = np.empty((len(verts), 4), dtype=np.float32)
    rgbi[:] = distant_lod_lights.lights["RGBI"] / 255.0
    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.RGBI)
    mesh_attr.data.foreach_set("color_srgb", rgbi.ravel())

    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.DIRECTION)
    mesh_attr.data.foreach_set("vector", lod_lights.lights["Direction"].ravel())

    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.FALLOFF)
    mesh_attr.data.foreach_set("value", lod_lights.lights["Falloff"])

    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.FALLOFF_EXP)
    mesh_attr.data.foreach_set("value", lod_lights.lights["FalloffExponent"])

    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.FLAGS)
    mesh_attr.data.foreach_set("value", lod_lights.lights["TimeAndStateFlags"].view(np.int32))

    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.HASH)
    mesh_attr.data.foreach_set("value", lod_lights.lights["Hash"].view(np.int32))

    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.CONE_INNER_ANGLE)
    mesh_attr.data.foreach_set("value", lod_lights.lights["ConeInnerAngle"].astype(np.int32))

    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.CONE_OUTER_ANGLE)
    mesh_attr.data.foreach_set("value", lod_lights.lights["ConeOuterAngleOrCapExt"].astype(np.int32))

    mesh_attr = mesh_add_lod_light_attribute(mesh, LodLightAttr.CORONA_INTENSITY)
    mesh_attr.data.foreach_set("value", lod_lights.lights["CoronaIntensity"].astype(np.int32))

    obj = create_blender_object(SollumType.NONE, map_data.name, mesh)
    ll.linked_object = obj
    return ll


def _organize_map_in_collections(map_group: MapGroup):
    """Places all map related objects in collections."""
    from ..ytyp.properties.extensions import ExtensionType

    base_collection_name = map_group.name
    base_collection = bpy.data.collections.new(base_collection_name)
    bpy.context.collection.children.link(base_collection)
    map_collections = {base_collection_name: base_collection}

    def _link_to_collection(obj, coll):
        for c in obj.users_collection:
            c.objects.unlink(obj)
        coll.objects.link(obj)

    def _link_to_collection_recursive(obj, coll):
        _link_to_collection(obj, coll)
        for child_obj in obj.children_recursive:  # could be slow with lots of entities, O(len(bpy.data.objects)) time
            _link_to_collection(child_obj, coll)

    light_effect_objs = []
    # Link entities to a collection per LOD level
    for entity in map_group.entities:
        for ext in entity.extensions:
            if ext.extension_type == ExtensionType.LIGHT_EFFECT:
                props = ext.get_properties()
                if props.linked_lights_object is not None:
                    light_effect_objs.append(props.linked_lights_object)

                    obj = entity.linked_object
                    if obj is not None:
                        # NOTE: this was done in create_extension but at that point the entities objects are not
                        # instanced yet, so do it here instead
                        constraint = props.linked_lights_object.constraints.new("COPY_TRANSFORMS")
                        constraint.target = obj

        obj = entity.linked_object
        if obj is None:
            continue

        entity_collection_name = f"{map_group.name}.{entity.lod_level}"
        entity_collection = map_collections.get(entity_collection_name, None)
        if entity_collection is None:
            entity_collection = bpy.data.collections.new(entity_collection_name)
            map_collections[entity_collection_name] = entity_collection

        _link_to_collection_recursive(obj, entity_collection)

    # Link LOD collections to the base collection in this order
    for ll in ("HD", "LOD", "SLOD1", "SLOD2", "SLOD3", "SLOD4"):
        ll_collection_name = f"{map_group.name}.{ll}"
        ll_collection = map_collections.get(ll_collection_name, None)
        if ll_collection is not None:
            base_collection.children.link(ll_collection)

    if light_effect_objs:
        # Place all light effect objects in their own collection
        light_effect_collection_name = f"{map_group.name}.light_effects"
        light_effect_collection = bpy.data.collections.new(light_effect_collection_name)
        base_collection.children.link(light_effect_collection)
        for lights_parent_obj in light_effect_objs:
            _link_to_collection_recursive(lights_parent_obj, light_effect_collection)

    if map_group.cargens:
        # Link cargen collections to the base collection, inside their own collection
        vehgens_collection_name = f"{map_group.name}.vehicle_gens"
        vehgens_collection = bpy.data.collections.new(vehgens_collection_name)
        base_collection.children.link(vehgens_collection)
        for cargen in map_group.cargens:
            if coll := cargen.linked_collection:
                vehgens_collection.children.link(coll)

    if map_group.grass_batches:
        # Link grass instances objects inside their own collection
        grass_collection_name = f"{map_group.name}.grass"
        grass_collection = bpy.data.collections.new(grass_collection_name)
        base_collection.children.link(grass_collection)
        for grass_batch in map_group.grass_batches:
            if obj := grass_batch.linked_object:
                _link_to_collection_recursive(obj, grass_collection)

    if map_group.occluders:
        # Link grass instances objects inside their own collection
        occluders_collection_name = f"{map_group.name}.occluders"
        occluders_collection = bpy.data.collections.new(occluders_collection_name)
        base_collection.children.link(occluders_collection)
        for occluder in map_group.occluders:
            if obj := occluder.linked_object:
                _link_to_collection_recursive(obj, occluders_collection)

    if map_group.lod_lights:
        # Link grass instances objects inside their own collection
        lod_lights_collection_name = f"{map_group.name}.lod_lights"
        lod_lights_collection = bpy.data.collections.new(lod_lights_collection_name)
        base_collection.children.link(lod_lights_collection)
        for lod_lights in map_group.lod_lights:
            if obj := lod_lights.linked_object:
                _link_to_collection_recursive(obj, lod_lights_collection)


def _longest_common_prefix(strs: Sequence[str]):
    if not strs:
        return ""

    s1 = min(strs)
    s2 = max(strs)

    for i, c in enumerate(s1):
        if c != s2[i]:
            return s1[:i]
    return s1
