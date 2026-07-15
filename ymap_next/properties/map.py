from collections.abc import Iterator
from enum import Enum, auto
from pathlib import Path
from uuid import uuid4

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    IntVectorProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Collection,
    Context,
    GeometryNodeTree,
    Object,
    PropertyGroup,
    Scene,
    Text,
)
from mathutils import Vector
from szio.gta5 import MapCarGeneratorCreationRule, MapCarGeneratorFlags

from ...shared.multiselection import (
    MultiSelectAccess,
    MultiSelectCollection,
    MultiSelectNestedAccess,
    MultiSelectPointerProperty,
    MultiSelectProperty,
    define_multiselect_collection,
)
from ...tools.blenderhelper import tag_redraw
from ...ytyp.properties.extensions import ExtensionsContainer, ExtensionType
from ...ytyp.properties.flags import EntityFlags
from ..lod_lights.bake import LodLightBakeSettings


def UUIDProperty(*, name: str = "UUID", description: str = ""):
    return StringProperty(name=name, description=description, maxlen=16, subtype="BYTE_STRING")


class MapLodLevel(Enum):
    HD = auto()  # includes ORPHANHD (HD with no parent)
    LOD = auto()
    SLOD1 = auto()
    SLOD2 = auto()
    SLOD3 = auto()
    SLOD4 = auto()

    @property
    def parent_level(self) -> "MapLodLevel | None":
        match self:
            case MapLodLevel.HD:
                return MapLodLevel.LOD
            case MapLodLevel.LOD:
                return MapLodLevel.SLOD1
            case MapLodLevel.SLOD1:
                return MapLodLevel.SLOD2
            case MapLodLevel.SLOD2:
                return MapLodLevel.SLOD3
            case MapLodLevel.SLOD3:
                return MapLodLevel.SLOD4
            case MapLodLevel.SLOD4:
                return None
            case _:
                raise AssertionError(f"Unknown LOD level '{self}'")

    @property
    def child_level(self) -> "MapLodLevel | None":
        match self:
            case MapLodLevel.HD:
                return None
            case MapLodLevel.LOD:
                return MapLodLevel.HD
            case MapLodLevel.SLOD1:
                return MapLodLevel.LOD
            case MapLodLevel.SLOD2:
                return MapLodLevel.SLOD1
            case MapLodLevel.SLOD3:
                return MapLodLevel.SLOD2
            case MapLodLevel.SLOD4:
                return MapLodLevel.SLOD3
            case _:
                raise AssertionError(f"Unknown LOD level '{self}'")


MapLodLevelEnumItems = tuple((enum.name, enum.name, "", enum.value) for enum in MapLodLevel)
MapLodLevelEnumFlagItems = tuple((enum.name, enum.name, "", 1 << enum.value) for enum in MapLodLevel)


class MapPriorityLevel(Enum):
    REQUIRED = auto()
    OPTIONAL_HIGH = auto()
    OPTIONAL_MEDIUM = auto()
    OPTIONAL_LOW = auto()


MapPriorityLevelEnumItems = tuple((enum.name, enum.name.replace("_", " "), "", enum.value) for enum in MapPriorityLevel)
MapPriorityLevelEnumFlagItems = tuple(
    (enum.name, enum.name.replace("_", " "), "", 1 << enum.value) for enum in MapPriorityLevel
)


class MapPartitionMode(Enum):
    NONE = auto()  # Manual: items export in this map data as-is
    AUTO = auto()  # Auto: items classified into auto-generated child map datas


MapPartitionModeEnumItems = (
    (MapPartitionMode.NONE.name, "Manual", "Items export in this map data as-is"),
    (MapPartitionMode.AUTO.name, "Auto", "Items are classified into auto-generated child map datas"),
)


class MapData(PropertyGroup):
    """A map."""

    uuid: UUIDProperty()
    map_group_uuid: UUIDProperty(name="Map Group UUID")
    name: StringProperty(name="Name")
    parent_uuid: UUIDProperty(name="Parent UUID")
    # Original map header <parent> string, stored at import. When the parent .ymap is not imported
    # (incomplete LOD hierarchy), parent_uuid stays empty, so this preserves the original parent
    # reference for re-export. Only used as a fallback when parent_uuid is empty/unresolvable.
    orig_parent_name: StringProperty(name="Original Parent Name", default="")
    partition_mode: EnumProperty(
        items=MapPartitionModeEnumItems,
        name="Partitioning",
        default=MapPartitionMode.NONE.name,
    )
    is_auto_generated: BoolProperty(name="Auto-Generated", default=False)
    incomplete_lod_hierarchy_lock: BoolProperty(
        name="Incomplete LOD Hierarchy",
        description=(
            "This container was imported without some related YMAP files. Its entity list and LOD hierarchy "
            "values are preserved as-is on export and editing is limited"
        ),
        default=False,
    )

    streaming_extents_min: FloatVectorProperty(name="Streaming Extents Min", default=(0, 0, 0), size=3, subtype="XYZ")
    streaming_extents_max: FloatVectorProperty(name="Streaming Extents Max", default=(0, 0, 0), size=3, subtype="XYZ")
    entities_extents_min: FloatVectorProperty(name="Entities Extents Min", default=(0, 0, 0), size=3, subtype="XYZ")
    entities_extents_max: FloatVectorProperty(name="Entities Extents Max", default=(0, 0, 0), size=3, subtype="XYZ")
    extents_manual: BoolProperty(
        name="Manual Extents",
        description=(
            "Keep the stored extents as-is. When disabled, extents are recalculated from the items assigned "
            "to this container during export"
        ),
        default=False,
    )

    desc_enabled: BoolProperty(
        name="Has Description",
        description="Write a block description when exporting this map",
        default=False,
    )
    desc_name: StringProperty(name="Name")
    desc_exported_by: StringProperty(name="Exported By")
    desc_owner: StringProperty(name="Owner")
    desc_time: StringProperty(name="Time")
    # Version and flags as strings because they are 32-bit unsigned integers, which can end up out of range since
    # IntProperty only supports 32-bit signed integers
    desc_version: StringProperty(name="Version", default="0")
    desc_flags: StringProperty(name="Flags", default="0")

    def get_uuid_str(self) -> str:
        return self.uuid.hex()

    uuid_str: StringProperty(name="UUID", get=get_uuid_str)

    ui_tree_depth: IntProperty(min=0)
    ui_tree_sort_id: IntProperty()

    def get_ui_label(self):
        return " " * (4 * self.ui_tree_depth) + self.name

    def set_ui_label(self, s: str):
        self.name = s.strip()

    ui_label: StringProperty(get=get_ui_label, set=set_ui_label)

    def get_parent_name(self) -> str:
        parent_uuid = self.parent_uuid
        if not parent_uuid:
            return ""
        group = get_maps().find_group(self.map_group_uuid)
        if not group:
            return ""
        map_data = group.find_map(parent_uuid)
        if not map_data:
            return ""

        return map_data.name

    def set_parent_by_name(self, map_data_name: str):
        if self.incomplete_lod_hierarchy_lock:
            # This map's entities keep their imported parent_index values, which are relative to
            # the original parent map's entity list, so it cannot be re-linked elsewhere.
            return

        group = get_maps().find_group(self.map_group_uuid)
        if group:
            map_data_name = map_data_name.strip()
            for m in group.maps:
                if m.name == map_data_name:
                    self.parent_uuid = m.uuid
                    break
            else:
                self.parent_uuid = b""

            group.refresh_ui()

    def search_parents(self, context: Context, edit_text: str) -> Iterator[str]:
        group = get_maps(context).find_group(self.map_group_uuid)
        if group:
            uuid = self.uuid
            for m in sorted(group.maps, key=lambda m: m.ui_tree_sort_id):
                if m.uuid != uuid:
                    yield m.ui_label
                else:
                    yield m.ui_label + "*"

    parent_name: StringProperty(
        name="Parent",
        get=get_parent_name,
        set=set_parent_by_name,
        search=search_parents,
    )

    @property
    def has_parent(self) -> bool:
        return bool(self.parent_uuid)

    @property
    def streaming_extents(self) -> tuple[Vector, Vector]:
        return self.streaming_extents_min, self.streaming_extents_max

    @streaming_extents.setter
    def streaming_extents(self, v: tuple[Vector, Vector]):
        self.streaming_extents_min, self.streaming_extents_max = v

    @property
    def entities_extents(self) -> tuple[Vector, Vector]:
        return self.entities_extents_min, self.entities_extents_max

    @entities_extents.setter
    def entities_extents(self, v: tuple[Vector, Vector]):
        self.entities_extents_min, self.entities_extents_max = v


class MapDataSelectionAccess(MultiSelectAccess):
    name: MultiSelectProperty()
    parent_name: MultiSelectProperty()
    ui_label: MultiSelectProperty()
    partition_mode: MultiSelectProperty()
    streaming_extents_min: MultiSelectProperty()
    streaming_extents_max: MultiSelectProperty()
    entities_extents_min: MultiSelectProperty()
    entities_extents_max: MultiSelectProperty()
    extents_manual: MultiSelectProperty()
    desc_enabled: MultiSelectProperty()
    desc_version: MultiSelectProperty()
    desc_flags: MultiSelectProperty()
    desc_name: MultiSelectProperty()
    desc_exported_by: MultiSelectProperty()
    desc_owner: MultiSelectProperty()
    desc_time: MultiSelectProperty()


class MapItemMixin:
    uuid: UUIDProperty()
    map_data_uuid: UUIDProperty(name="Map Data UUID")
    map_group_uuid: UUIDProperty(name="Map Group UUID")

    def get_uuid_str(self) -> str:
        return self.uuid.hex()

    uuid_str: StringProperty(name="UUID", get=get_uuid_str)

    def get_map_data_name(self) -> str:
        map_data_uuid = self.map_data_uuid
        if not map_data_uuid:
            return ""
        group = get_maps().find_group(self.map_group_uuid)
        if not group:
            return ""
        map_data = group.find_map(map_data_uuid)
        if not map_data:
            return ""

        return map_data.name

    def _allow_map_data_change(self, _group: "MapGroup", _new_map_data_uuid: bytes) -> bool:
        # NOTE: the map_data_name set= callback uses this function, so subclasses customize behavior by overriding this
        # function, not the setter.
        return True

    def set_map_data_by_name(self, map_data_name: str):
        group = get_maps().find_group(self.map_group_uuid)
        new_uuid = b""
        if group:
            map_data_name = map_data_name.strip()
            for m in group.maps:
                if m.name == map_data_name:
                    new_uuid = m.uuid
                    break

            if not self._allow_map_data_change(group, new_uuid):
                return

        self.map_data_uuid = new_uuid

    def search_map_datas(self, context: Context, _edit_text: str) -> Iterator[str]:
        group = get_maps(context).find_group(self.map_group_uuid)
        if group:
            for m in sorted(group.maps, key=lambda m: m.ui_tree_sort_id):
                yield m.ui_label

    map_data_name: StringProperty(
        name="Container",
        get=get_map_data_name,
        set=set_map_data_by_name,
        search=search_map_datas,
    )


class MapGrassTemplate(PropertyGroup):
    archetype_name: StringProperty(name="Archetype Name")
    scale_range: FloatVectorProperty(
        name="Scale Range",
        description=(
            "Defines the minimum and maximum scale applied to instances.\n\n"
            "An instance's scale factor of 0 maps to the Min and 1 maps to the Max, with values in between interpolated. Set both equal to give every instance the same scale."
        ),
        default=(0.7, 1.0),
        size=2,
        min=0.0,
        subtype="XYZ",
    )
    scale_randomness: FloatProperty(
        name="Scale Randomness",
        description=(
            "Adds random size variation to each instance on top of the scale range. Each instance is randomly scaled "
            "up or down by up to this fraction of the Scale Range Max (e.g. 0.2 = ±20% of the maximum).\n\n"
            "Set to 0 for no random variation (each instance still uses its assigned scale factor)."
        ),
        default=0.2,
        min=0.0,
    )
    lod_dist: IntProperty(name="LOD Distance", default=100, min=0)
    lod_fade_start_dist: FloatProperty(name="LOD Fade Start Distance", default=20.0, min=0.0)
    lod_inst_fade_range: FloatProperty(name="LOD Instance Fade Range", default=0.75, min=0.0)
    orient_to_terrain: FloatProperty(name="Orient To Terrain", default=1.0, min=0.0, max=1.0, subtype="FACTOR")

    spawn_weight: FloatProperty(name="Spawn Weight", default=1.0, min=0.0, soft_max=1.0, subtype="FACTOR")


class MapGrassTemplateSelectionAccess(MultiSelectAccess):
    archetype_name: MultiSelectProperty()
    scale_range: MultiSelectProperty()
    scale_randomness: MultiSelectProperty()
    lod_dist: MultiSelectProperty()
    lod_fade_start_dist: MultiSelectProperty()
    lod_inst_fade_range: MultiSelectProperty()
    orient_to_terrain: MultiSelectProperty()
    spawn_weight: MultiSelectProperty()


@define_multiselect_collection("templates", {"name": "Templates"})
class MapGrassBatch(MapItemMixin, PropertyGroup):
    __sz_preset_capture__ = ("templates",)

    name: StringProperty(name="Name")
    templates: MultiSelectCollection[MapGrassTemplate, MapGrassTemplateSelectionAccess]
    linked_object: PointerProperty(type=Object, name="Linked Object")
    modifier_ng: PointerProperty(type=GeometryNodeTree, name="Modifier Nodes")


class MapGrassBatchSelectionAccess(MultiSelectAccess):
    name: MultiSelectProperty()


class MapOccluder(MapItemMixin, PropertyGroup):
    name: StringProperty(name="Name")
    linked_object: PointerProperty(type=Object, name="Linked Object")


class MapOccluderSelectionAccess(MultiSelectAccess):
    name: MultiSelectProperty()


class MapLodLights(MapItemMixin, PropertyGroup):
    name: StringProperty(name="Name")
    linked_object: PointerProperty(type=Object, name="Linked Object")
    category: EnumProperty(
        items=(
            ("SMALL", "Small", "", 0),
            ("MEDIUM", "Medium", "", 1),
            ("LARGE", "Large", "", 2),
        ),
        name="Category",
        default="MEDIUM",
    )


class MapLodLightsSelectionAccess(MultiSelectAccess):
    name: MultiSelectProperty()
    category: MultiSelectProperty()


_defaults = LodLightBakeSettings()


class MapLodLightBakePropertiesBase:
    lod_levels: EnumProperty(
        items=MapLodLevelEnumFlagItems,
        name="LOD Levels",
        description="LOD levels of entities to include in LOD lights",
        default=_defaults.lod_levels,
        options={"ENUM_FLAG"},
    )
    priority_levels: EnumProperty(
        items=MapPriorityLevelEnumFlagItems,
        name="Priority Levels",
        description="Priority levels of entities to include in LOD lights",
        default=_defaults.priority_levels,
        options={"ENUM_FLAG"},
    )
    is_streetlight_pattern: StringProperty(
        name="'Is Streetlight' Pattern",
        description="Regular expression to match entities whose lights are considered 'streetlights'",
        default=_defaults.is_streetlight_pattern,
    )
    skip_pattern: StringProperty(
        name="Skip Pattern",
        description="Regular expression to match entities whose lights are excluded from LOD lights",
        default=_defaults.skip_pattern,
    )
    min_falloff_small: FloatProperty(
        name="Min Falloff (Small)",
        description="Minimum falloff distance for a light to qualify as Small",
        default=_defaults.min_falloff_small,
        min=0.0,
    )
    min_intensity_small: FloatProperty(
        name="Min Intensity (Small)",
        description="Minimum intensity for a light to qualify as Small",
        default=_defaults.min_intensity_small,
        min=0.0,
    )
    min_falloff_medium: FloatProperty(
        name="Min Falloff (Medium)",
        description="Minimum falloff distance for a light to qualify as Medium",
        default=_defaults.min_falloff_medium,
        min=0.0,
    )
    min_intensity_medium: FloatProperty(
        name="Min Intensity (Medium)",
        description="Minimum intensity for a light to qualify as Medium",
        default=_defaults.min_intensity_medium,
        min=0.0,
    )
    partition: BoolProperty(
        name="Partition",
        description="Split LOD lights across multiple map containers",
        default=_defaults.partition,
    )
    partition_max_lights_small: IntProperty(
        name="Partition Max Lights (Small)",
        description="Maximum Small LOD lights per partition",
        default=_defaults.partition_max_lights_small,
        min=1,
    )
    partition_max_lights_medium: IntProperty(
        name="Partition Max Lights (Medium)",
        description="Maximum Medium LOD lights per partition",
        default=_defaults.partition_max_lights_medium,
        min=1,
    )
    partition_max_lights_large: IntProperty(
        name="Partition Max Lights (Large)",
        description="Maximum Large LOD lights per partition",
        default=_defaults.partition_max_lights_large,
        min=1,
    )
    visibility_range_small: FloatProperty(
        name="Visibility Range (Small)",
        description="Extra distance added to the streaming extents of Small LOD lights",
        default=_defaults.visibility_range_small,
        min=0.0,
    )
    visibility_range_medium: FloatProperty(
        name="Visibility Range (Medium)",
        description="Extra distance added to the streaming extents of Medium LOD lights",
        default=_defaults.visibility_range_medium,
        min=0.0,
    )
    visibility_range_large: FloatProperty(
        name="Visibility Range (Large)",
        description="Extra distance added to the streaming extents of Large LOD lights",
        default=_defaults.visibility_range_large,
        min=0.0,
    )
    distant_visibility_range_small: FloatProperty(
        name="Distant Visibility Range (Small)",
        description="Extra distance added to the streaming extents of Small distant LOD lights",
        default=_defaults.distant_visibility_range_small,
        min=0.0,
    )
    distant_visibility_range_medium: FloatProperty(
        name="Distant Visibility Range (Medium)",
        description="Extra distance added to the streaming extents of Medium distant LOD lights",
        default=_defaults.distant_visibility_range_medium,
        min=0.0,
    )
    distant_visibility_range_large: FloatProperty(
        name="Distant Visibility Range (Large)",
        description="Extra distance added to the streaming extents of Large distant LOD lights",
        default=_defaults.distant_visibility_range_large,
        min=0.0,
    )
    name_prefix: StringProperty(
        name="Name Prefix",
        description="Name prefix for new map containers",
        default=_defaults.name_prefix,
    )

    def get_settings(self) -> LodLightBakeSettings:
        return LodLightBakeSettings(
            lod_levels=self.lod_levels,
            priority_levels=self.priority_levels,
            is_streetlight_pattern=self.is_streetlight_pattern,
            skip_pattern=self.skip_pattern,
            min_falloff_small=self.min_falloff_small,
            min_falloff_medium=self.min_falloff_medium,
            min_intensity_small=self.min_intensity_small,
            min_intensity_medium=self.min_intensity_medium,
            partition=self.partition,
            partition_max_lights_small=self.partition_max_lights_small,
            partition_max_lights_medium=self.partition_max_lights_medium,
            partition_max_lights_large=self.partition_max_lights_large,
            visibility_range_small=self.visibility_range_small,
            visibility_range_medium=self.visibility_range_medium,
            visibility_range_large=self.visibility_range_large,
            distant_visibility_range_small=self.distant_visibility_range_small,
            distant_visibility_range_medium=self.distant_visibility_range_medium,
            distant_visibility_range_large=self.distant_visibility_range_large,
            name_prefix=self.name_prefix,
        )


del _defaults


class MapLodLightBakeProperties(MapLodLightBakePropertiesBase, PropertyGroup):
    pass


class MapTimecycleModifier(MapItemMixin, PropertyGroup):
    __sz_preset_capture__ = (
        "name",
        "percentage",
        "range",
        "start_hour",
        "end_hour",
    )

    name: StringProperty(name="Name")
    location: FloatVectorProperty(name="Location", default=(0, 0, 0), size=3, subtype="XYZ")
    size: FloatVectorProperty(name="Size", default=(0, 0, 0), size=3, min=0.0, subtype="XYZ")
    percentage: FloatProperty(name="Percentage", default=100.0, min=0.0, max=100.0, step=100)
    range: FloatProperty(name="Range", default=1.0, min=0.0)
    start_hour: IntProperty(name="Start Hour", default=0, min=0, max=23)
    end_hour: IntProperty(name="End Hour", default=23, min=0, max=23)

    @property
    def extents(self) -> tuple[Vector, Vector]:
        location = Vector(self.location)
        half_size = Vector(self.size) * 0.5
        return location - half_size, location + half_size

    @extents.setter
    def extents(self, v: tuple[Vector, Vector]):
        extents_min, extents_max = v
        self.location = (Vector(extents_min) + Vector(extents_max)) * 0.5
        self.size = Vector(extents_max) - Vector(extents_min)


class MapTimecycleModifierSelectionAccess(MultiSelectAccess):
    name: MultiSelectProperty()
    location: MultiSelectProperty()
    size: MultiSelectProperty()
    percentage: MultiSelectProperty()
    range: MultiSelectProperty()
    start_hour: MultiSelectProperty()
    end_hour: MultiSelectProperty()


CARGEN_MESH_NAME = ".sz.cargen_mesh"

MapCarGenCreationRuleEnumItems = (
    (MapCarGeneratorCreationRule.ALL.name, "All", ""),
    (MapCarGeneratorCreationRule.ONLY_SPORTS.name, "Only Sports", ""),
    (MapCarGeneratorCreationRule.NO_SPORTS.name, "No Sports", ""),
    (MapCarGeneratorCreationRule.ONLY_BIG.name, "Only Big", ""),
    (MapCarGeneratorCreationRule.NO_BIG.name, "No Big", ""),
    (MapCarGeneratorCreationRule.ONLY_BIKES.name, "Only Bikes", ""),
    (MapCarGeneratorCreationRule.NO_BIKES.name, "No Bikes", ""),
    (MapCarGeneratorCreationRule.ONLY_DELIVERY.name, "Only Delivery", ""),
    (MapCarGeneratorCreationRule.NO_DELIVERY.name, "No Delivery", ""),
    (MapCarGeneratorCreationRule.BOATS.name, "Boats", ""),
    (MapCarGeneratorCreationRule.ONLY_POOR.name, "Only Poor", ""),
    (MapCarGeneratorCreationRule.NO_POOR.name, "No Poor", ""),
    (MapCarGeneratorCreationRule.CAN_BE_BROKEN_DOWN.name, "Can Be Broken Down", ""),
)

# Maps MapCarGen BoolProperty name -> szio MapCarGeneratorFlags bit. Order matches the enum.
MAP_CARGEN_FLAG_PROPS: tuple[tuple[str, MapCarGeneratorFlags], ...] = (
    ("flag_force_spawn", MapCarGeneratorFlags.FORCE_SPAWN),
    ("flag_ignore_density", MapCarGeneratorFlags.IGNORE_DENSITY),
    ("flag_police", MapCarGeneratorFlags.POLICE),
    ("flag_firetruck", MapCarGeneratorFlags.FIRETRUCK),
    ("flag_ambulance", MapCarGeneratorFlags.AMBULANCE),
    ("flag_during_day", MapCarGeneratorFlags.DURING_DAY),
    ("flag_at_night", MapCarGeneratorFlags.AT_NIGHT),
    ("flag_align_left", MapCarGeneratorFlags.ALIGN_LEFT),
    ("flag_align_right", MapCarGeneratorFlags.ALIGN_RIGHT),
    ("flag_single_player", MapCarGeneratorFlags.SINGLE_PLAYER),
    ("flag_network_player", MapCarGeneratorFlags.NETWORK_PLAYER),
    ("flag_low_priority", MapCarGeneratorFlags.LOW_PRIORITY),
    ("flag_prevent_entry", MapCarGeneratorFlags.PREVENT_ENTRY),
)

_CARGEN_CREATION_RULE_LABELS = {item[0]: item[1] for item in MapCarGenCreationRuleEnumItems}

# Subset of flags shown in the cargen UI label
_CARGEN_UI_LABEL_FLAGS: tuple[tuple[str, str], ...] = (
    ("flag_police", "Police"),
    ("flag_firetruck", "Firetruck"),
    ("flag_ambulance", "Ambulance"),
    ("flag_force_spawn", "Force Spawn"),
    ("flag_during_day", "Day"),
    ("flag_at_night", "Night"),
)


class MapCarGen(MapItemMixin, PropertyGroup):
    name: StringProperty(name="Name")
    linked_collection: PointerProperty(type=Collection, name="Linked Collection")
    model: StringProperty(name="Model", description="Use a specific vehicle model.")
    model_set: StringProperty(
        name="Model Set",
        description="Use any vehicle model found in the specified model set. Model sets are defined in vehiclemodelsets.meta",
    )
    body_color_remap: IntVectorProperty(name="Body Color Remap", size=4, default=(-1, -1, -1, -1))
    livery: IntProperty(name="Livery", default=-1)
    flag_force_spawn: BoolProperty(name="Force Spawn")
    flag_ignore_density: BoolProperty(name="Ignore Density")
    flag_police: BoolProperty(name="Police")
    flag_firetruck: BoolProperty(name="Firetruck")
    flag_ambulance: BoolProperty(name="Ambulance")
    flag_during_day: BoolProperty(name="During Day")
    flag_at_night: BoolProperty(name="At Night")
    flag_align_left: BoolProperty(name="Align Left")
    flag_align_right: BoolProperty(name="Align Right")
    flag_single_player: BoolProperty(name="SP")
    flag_network_player: BoolProperty(name="MP")
    flag_low_priority: BoolProperty(name="Low Priority")
    flag_prevent_entry: BoolProperty(name="Prevent Entry")
    creation_rule: EnumProperty(
        items=MapCarGenCreationRuleEnumItems, name="Creation Rule", default=MapCarGeneratorCreationRule.ALL.name
    )

    def get_ui_label(self):
        if self.name:
            # If user gave it a name, use that name
            return self.name

        if self.model:
            subject = self.model
        elif self.model_set:
            subject = f"{self.model_set} (set)"
        elif self.creation_rule != MapCarGeneratorCreationRule.ALL.name:
            subject = _CARGEN_CREATION_RULE_LABELS.get(self.creation_rule, "Any")
        else:
            subject = "Any"

        # Day and Night together mean "any time", cancel them out so neither tag appears.
        day_night_cancel = self.flag_during_day and self.flag_at_night
        flags = [
            display
            for prop_name, display in _CARGEN_UI_LABEL_FLAGS
            if getattr(self, prop_name) and not (day_night_cancel and prop_name in ("flag_during_day", "flag_at_night"))
        ]
        if flags:
            return f"{subject} [{', '.join(flags)}]"
        return subject

    ui_label: StringProperty(get=get_ui_label)

    @staticmethod
    def get_cargen_mesh() -> bpy.types.Mesh:
        from ...shared.obj_reader import obj_read_from_file

        mesh = bpy.data.meshes.get(CARGEN_MESH_NAME, None)
        if mesh is None:
            file_path = Path(__file__).parent.joinpath("cargen_model.obj")
            cargen_obj_mesh = obj_read_from_file(file_path)
            mesh = cargen_obj_mesh.as_bpy_mesh(CARGEN_MESH_NAME)

        return mesh


class MapCarGenSelectionAccess(MultiSelectAccess):
    name: MultiSelectProperty()
    model: MultiSelectProperty()
    model_set: MultiSelectProperty()
    creation_rule: MultiSelectProperty()
    body_color_remap: MultiSelectProperty()
    livery: MultiSelectProperty()
    flag_force_spawn: MultiSelectProperty()
    flag_ignore_density: MultiSelectProperty()
    flag_police: MultiSelectProperty()
    flag_firetruck: MultiSelectProperty()
    flag_ambulance: MultiSelectProperty()
    flag_during_day: MultiSelectProperty()
    flag_at_night: MultiSelectProperty()
    flag_align_left: MultiSelectProperty()
    flag_align_right: MultiSelectProperty()
    flag_single_player: MultiSelectProperty()
    flag_network_player: MultiSelectProperty()
    flag_low_priority: MultiSelectProperty()
    flag_prevent_entry: MultiSelectProperty()


class MapEntity(MapItemMixin, PropertyGroup, ExtensionsContainer):
    IS_ARCHETYPE = False
    DEFAULT_EXTENSION_TYPE = ExtensionType.DOOR

    __sz_preset_capture__ = (
        "flags",
        "lod_dist",
        "child_lod_dist",
        "lod_level",
        "priority_level",
        "ambient_occlusion_multiplier",
        "artificial_ambient_occlusion",
        "tint_value",
        "is_critical",
        "mlo_turn_on_gps",
        "mlo_cap_entities_alpha",
        "mlo_short_fade_distance",
    )

    # Transforms unused if linked object
    position: FloatVectorProperty(name="Position", subtype="XYZ", size=3, default=(0, 0, 0))
    rotation: FloatVectorProperty(name="Rotation", subtype="QUATERNION", size=4, default=(1, 0, 0, 0))
    scale_xy: FloatProperty(name="Scale XY", default=1.0)
    scale_z: FloatProperty(name="Scale Z", default=1.0)

    archetype_name: StringProperty(name="Archetype Name")
    lod_dist: FloatProperty(name="LOD Distance", default=-1.0)
    child_lod_dist: FloatProperty(name="Child LOD Distance", default=0)
    lod_level: EnumProperty(items=MapLodLevelEnumItems, name="LOD Level", default=MapLodLevel.HD.name)
    priority_level: EnumProperty(
        items=MapPriorityLevelEnumItems, name="Priority Level", default=MapPriorityLevel.REQUIRED.name
    )
    ambient_occlusion_multiplier: IntProperty(
        name="Natural AO Multiplier",
        description="Natural Ambient Occlusion Multiplier",
        default=255,
        min=0,
        max=255,
        subtype="FACTOR",
    )
    artificial_ambient_occlusion: IntProperty(
        name="Artificial AO Multiplier",
        description="Artificial Ambient Occlusion Multiplier",
        default=255,
        min=0,
        max=255,
        subtype="FACTOR",
    )
    # TODO(ymap): sync tint_value with tint geonodes
    tint_value: IntProperty(name="Tint Value", default=0, min=0, max=255)
    flags: PointerProperty(type=EntityFlags, name="Flags")

    is_critical: BoolProperty(name="Critical", default=False)

    parent_uuid: UUIDProperty(name="LOD Parent UUID", description="LOD parent of this entity")
    # Only used with incomplete LOD hierarchies, otherwise, recalculated on export
    parent_index: IntProperty(name="LOD Parent Index", default=-1)
    # Number of LOD children living in .ymap files that were not imported (incomplete hierarchy).
    # Export computes numChildren = children found via parent_uuid links + this value.
    num_children_missing: IntProperty(
        name="Number of Missing LOD Children",
        description=(
            "Number of LOD children in YMAP files that were not imported. Added to the number of children "
            "found in the imported containers when exporting"
        ),
        default=0,
        min=0,
    )

    is_mlo: BoolProperty(name="MLO", description="This entity is a MLO instance", default=False)
    mlo_group_id: IntProperty(name="Group ID", default=0, min=0)
    mlo_floor_id: IntProperty(name="Floor ID", default=0, min=0)  # always 0, hidden from the UI
    mlo_default_entity_sets: StringProperty(
        name="Default Entity Sets", description="Comma-separated list of entity sets enabled by default", default=""
    )
    mlo_num_exit_portals: IntProperty(name="Number of Exit Portals", default=0)
    mlo_turn_on_gps: BoolProperty(name="Turn On GPS", default=False)
    mlo_cap_entities_alpha: BoolProperty(name="Cap Entities Alpha", default=False)
    mlo_short_fade_distance: BoolProperty(name="Short Fade Distance", default=False)

    linked_object: PointerProperty(type=Object, name="Linked Object")

    @property
    def is_orphan_hd(self) -> bool:
        return not self.parent_uuid and self.lod_level == MapLodLevel.HD.name

    def _allow_map_data_change(self, group: "MapGroup", new_map_data_uuid: bytes) -> bool:
        # Entities cannot move into or out of a locked container: its entity list order defines
        # the exported indices that non-imported .ymap files reference.
        return not (group.is_map_locked(self.map_data_uuid) or group.is_map_locked(new_map_data_uuid))

    def is_filtered(self) -> bool:
        """Returns true if this entity should be shown on the UI list; false, otherwise."""
        flt = bpy.context.scene.sz_map_entity_filter
        match flt.filter_type:
            case "lod_level":
                return self.lod_level == flt.lod_level
            case "kind":
                if flt.kind == "mlo":
                    return self.is_mlo
                elif flt.kind == "orphan_hd":
                    return self.is_orphan_hd
                else:  # "regular"
                    return not self.is_mlo
            case "container":
                return self.map_data_name == flt.container_name
            case _:  # "all"
                return True

    def get_parent_archetype_name(self):
        parent_uuid = self.parent_uuid
        if not parent_uuid:
            return ""
        group = get_maps().find_group(self.map_group_uuid)
        if not group:
            return ""
        parent_entity = group.find_entity(parent_uuid)
        if not parent_entity:
            return ""

        return parent_entity.archetype_name

    def set_parent_by_archetype_name(self, archetype_name: str):
        group = get_maps().find_group(self.map_group_uuid)
        if group is not None and group.is_map_locked(self.map_data_uuid):
            # This entity's container is locked: its parent link is frozen.
            return

        if " | " in archetype_name:
            # User selected one of the entries from the search below, we have the UUID directly
            _, entity_uuid_str = archetype_name.split(" | ", maxsplit=1)
            entity_uuid = bytes.fromhex(entity_uuid_str.strip())
            self.parent_uuid = entity_uuid
            return
        else:
            # Only have the archetype name, find the first entity with this archetype_name
            archetype_name = archetype_name.strip().lower()
            if archetype_name and group:
                for e in group.entities:
                    if e.archetype_name.lower() == archetype_name:
                        self.parent_uuid = e.uuid
                        return

        # No parent found
        self.parent_uuid = b""

    def search_parent_archetype_names(self, context: Context, edit_text: str) -> Iterator[str]:
        group = get_maps(context).find_group(self.map_group_uuid)
        if group:
            parent_lod_level = MapLodLevel[self.lod_level].parent_level
            if parent_lod_level is not None:
                parent_lod_level_name = parent_lod_level.name
                # Including UUID to differentiate if there are multiple entities using the same archetype
                yield from (
                    e.archetype_name + " | " + e.uuid.hex()
                    for e in group.entities
                    if e.lod_level == parent_lod_level_name
                )

    parent_name: StringProperty(
        name="LOD Parent",
        get=get_parent_archetype_name,
        set=set_parent_by_archetype_name,
        search=search_parent_archetype_names,
    )


class MapEntityFlagsSelectionAccess(MultiSelectNestedAccess):
    total: MultiSelectProperty()
    flag1: MultiSelectProperty()
    flag2: MultiSelectProperty()
    flag3: MultiSelectProperty()
    flag4: MultiSelectProperty()
    flag5: MultiSelectProperty()
    flag6: MultiSelectProperty()
    flag7: MultiSelectProperty()
    flag8: MultiSelectProperty()
    flag9: MultiSelectProperty()
    flag10: MultiSelectProperty()
    flag11: MultiSelectProperty()
    flag12: MultiSelectProperty()
    flag13: MultiSelectProperty()
    flag14: MultiSelectProperty()
    flag15: MultiSelectProperty()
    flag16: MultiSelectProperty()
    flag17: MultiSelectProperty()
    flag18: MultiSelectProperty()
    flag19: MultiSelectProperty()
    flag20: MultiSelectProperty()
    flag21: MultiSelectProperty()
    flag22: MultiSelectProperty()
    flag23: MultiSelectProperty()
    flag24: MultiSelectProperty()
    flag25: MultiSelectProperty()
    flag26: MultiSelectProperty()
    flag27: MultiSelectProperty()
    flag28: MultiSelectProperty()
    flag29: MultiSelectProperty()
    flag30: MultiSelectProperty()
    flag31: MultiSelectProperty()
    flag32: MultiSelectProperty()


class MapEntitySelectionAccess(MultiSelectAccess):
    map_data_name: MultiSelectProperty()

    archetype_name: MultiSelectProperty()
    parent_name: MultiSelectProperty()
    parent_index: MultiSelectProperty()
    lod_dist: MultiSelectProperty()
    child_lod_dist: MultiSelectProperty()
    lod_level: MultiSelectProperty()
    num_children_missing: MultiSelectProperty()
    priority_level: MultiSelectProperty()
    ambient_occlusion_multiplier: MultiSelectProperty()
    artificial_ambient_occlusion: MultiSelectProperty()
    tint_value: MultiSelectProperty()
    flags: MultiSelectPointerProperty(MapEntityFlagsSelectionAccess)
    is_critical: MultiSelectProperty()

    is_mlo: MultiSelectProperty()
    mlo_group_id: MultiSelectProperty()
    mlo_floor_id: MultiSelectProperty()  # always 0, hidden from the UI
    mlo_default_entity_sets: MultiSelectProperty()
    mlo_num_exit_portals: MultiSelectProperty()
    mlo_turn_on_gps: MultiSelectProperty()
    mlo_cap_entities_alpha: MultiSelectProperty()
    mlo_short_fade_distance: MultiSelectProperty()


@define_multiselect_collection("maps", {"name": "Containers"})
@define_multiselect_collection("entities", {"name": "Entities"})
@define_multiselect_collection("cargens", {"name": "Car Generators"})
@define_multiselect_collection("timecycle_modifiers", {"name": "Timecycle Modifiers"})
@define_multiselect_collection("grass_batches", {"name": "Grass Batches"})
@define_multiselect_collection("occluders", {"name": "Occluders"})
@define_multiselect_collection("lod_lights", {"name": "LOD Lights"})
class MapGroup(PropertyGroup):
    """A group of related maps."""

    uuid: UUIDProperty()
    name: StringProperty(name="Name")

    scripted: BoolProperty(name="Scripted", default=False)

    maps: MultiSelectCollection[MapData, MapDataSelectionAccess]
    lod_lights: MultiSelectCollection[MapLodLights, MapLodLightsSelectionAccess]
    occluders: MultiSelectCollection[MapOccluder, MapOccluderSelectionAccess]
    timecycle_modifiers: MultiSelectCollection[MapTimecycleModifier, MapTimecycleModifierSelectionAccess]
    grass_batches: MultiSelectCollection[MapGrassBatch, MapGrassBatchSelectionAccess]
    cargens: MultiSelectCollection[MapCarGen, MapCarGenSelectionAccess]
    entities: MultiSelectCollection[MapEntity, MapEntitySelectionAccess]

    lod_lights_bake_props: PointerProperty(type=MapLodLightBakeProperties)

    def new_map(self) -> MapData:
        from ..map_index import MAP_INDEX

        m = self.maps.add()
        m.uuid = uuid4().bytes
        m.map_group_uuid = self.uuid
        m.name = "Map"
        MAP_INDEX.store_map_data(self.uuid, m.uuid, len(self.maps) - 1)
        return m

    def find_map(self, uuid: bytes) -> MapData | None:
        from ..map_index import MAP_INDEX

        cache = MAP_INDEX.try_get_map_data(uuid)
        if cache is not None:
            if cache.map_group_uuid == self.uuid and cache.index < len(self.maps):
                m = self.maps[cache.index]
                if m.uuid == uuid:
                    return m
            MAP_INDEX.evict_map_data(uuid)

        for i, m in enumerate(self.maps):
            if m.uuid == uuid:
                MAP_INDEX.store_map_data(self.uuid, m.uuid, i)
                return m

        return None

    @property
    def has_incomplete_lod_hierarchy(self) -> bool:
        return any(m.incomplete_lod_hierarchy_lock for m in self.maps)

    def is_map_locked(self, map_data_uuid: bytes) -> bool:
        if not map_data_uuid:
            return False
        m = self.find_map(map_data_uuid)
        return m is not None and m.incomplete_lod_hierarchy_lock

    def new_entity(self) -> MapEntity:
        from ..map_index import MAP_INDEX

        e = self.entities.add()
        e.uuid = uuid4().bytes
        e.map_group_uuid = self.uuid
        MAP_INDEX.store_entity(self.uuid, e.uuid, len(self.entities) - 1)
        return e

    def find_entity(self, uuid: bytes) -> MapEntity | None:
        from ..map_index import MAP_INDEX

        cache = MAP_INDEX.try_get_entity(uuid)
        if cache is not None:
            if cache.map_group_uuid == self.uuid and cache.index < len(self.entities):
                entity = self.entities[cache.index]
                if entity.uuid == uuid:
                    return entity
            MAP_INDEX.evict_entity(uuid)

        for i, e in enumerate(self.entities):
            if e.uuid == uuid:
                MAP_INDEX.store_entity(self.uuid, e.uuid, i)
                return e

        return None

    def set_entity_parent(self, entity: MapEntity, new_parent_uuid: bytes):
        """Reparent `entity`, unless its container is locked."""
        if self.is_map_locked(entity.map_data_uuid):
            # The entity's container is frozen: its parent link may be unresolvable (parent in a
            # non-imported .ymap) and parent_index is the source of truth, so reparenting must be
            # a no-op. Only the child's container matters; entities in unlocked containers may
            # link to parents in locked ones (export counts them via found children + missing).
            return

        entity.parent_uuid = new_parent_uuid

    def find_grass_batch(self, uuid: bytes) -> MapGrassBatch | None:
        for gb in self.grass_batches:
            if gb.uuid == uuid:
                return gb
        return None

    def find_cargen(self, uuid: bytes) -> MapCarGen | None:
        for cg in self.cargens:
            if cg.uuid == uuid:
                return cg
        return None

    def find_occluder(self, uuid: bytes) -> MapOccluder | None:
        for occ in self.occluders:
            if occ.uuid == uuid:
                return occ
        return None

    def new_cargen(self) -> MapCarGen:
        g = self.cargens.add()
        g.uuid = uuid4().bytes
        g.map_group_uuid = self.uuid
        return g

    def new_tcm(self) -> MapTimecycleModifier:
        m = self.timecycle_modifiers.add()
        m.uuid = uuid4().bytes
        m.map_group_uuid = self.uuid
        return m

    def new_grass_batch(self) -> MapGrassBatch:
        m = self.grass_batches.add()
        m.uuid = uuid4().bytes
        m.map_group_uuid = self.uuid
        return m

    def new_occluder(self) -> MapOccluder:
        m = self.occluders.add()
        m.uuid = uuid4().bytes
        m.map_group_uuid = self.uuid
        return m

    def new_lod_lights(self) -> MapLodLights:
        m = self.lod_lights.add()
        m.uuid = uuid4().bytes
        m.map_group_uuid = self.uuid
        return m

    def refresh_ui(self):
        # Index maps
        maps_by_uuid = {m.uuid: m for m in self.maps}

        # Build parent -> children mapping
        children = {}
        roots = []

        for m in self.maps:
            if m.has_parent and m.parent_uuid in maps_by_uuid:
                children.setdefault(m.parent_uuid, []).append(m)
            else:
                roots.append(m)

        # Sort children lists alphabetically
        for child_list in children.values():
            child_list.sort(key=lambda m: m.name.lower())

        # Sort roots alphabetically
        roots.sort(key=lambda m: m.name.lower())

        sort_id = -1

        def _add_to_ui(map_data, depth):
            nonlocal sort_id
            sort_id += 1
            map_data.ui_tree_sort_id = sort_id
            map_data.ui_tree_depth = depth

            for child in children.get(map_data.uuid, []):
                _add_to_ui(child, depth + 1)

        for root in roots:
            _add_to_ui(root, 0)

    def on_timecycle_modifiers_active_index_update_from_ui(self, context):
        from ..ui.map import SOLLUMZ_PT_map_tcms
        if SOLLUMZ_PT_map_tcms.is_active():
            tag_redraw(context, space_type="VIEW_3D", region_type="WINDOW")


class MapGroupSelectionAccess(MultiSelectAccess):
    pass


@define_multiselect_collection("groups", {"name": "Groups"})
class MapsProperties(PropertyGroup):
    groups: MultiSelectCollection[MapGroup, MapGroupSelectionAccess]

    def new_group(self) -> MapGroup:
        g = self.groups.add()
        index = len(self.groups) - 1
        self.groups.select(index)

        g.uuid = uuid4().bytes
        g.name = "MapGroup"
        return g

    def find_group(self, uuid: bytes) -> MapGroup | None:
        for m in self.groups:
            if m.uuid == uuid:
                return m

        return None

    def find_group_index(self, uuid: bytes) -> int | None:
        for i, m in enumerate(self.groups):
            if m.uuid == uuid:
                return i

        return None


def get_maps(context: Context | None = None, create_if_missing: bool = False) -> MapsProperties | None:
    # return (context or bpy.context).scene.sz_maps
    context = context or bpy.context
    scene = getattr(context, "scene", None)
    c = scene and scene.sz_maps_container
    if not c and create_if_missing:
        c = bpy.data.texts.new(".sz_maps_container.do_not_delete")
        context.scene.sz_maps_container = c

    return c.sz_maps if c else None


def register():
    # Scene.sz_maps = PointerProperty(type=MapsProperties, name="Maps")
    # NOTE: we do not store the maps directly on the scene because with thousands of items (e.g. in entities collections)
    #       UI interactions start to lag a lot, even on unrelated parts, like the archetypes UI. This might due to
    #       dependency-graph or something iterating all structs in the scene data-block, like `bpy_struct.path_from_id()`
    #       does, but at least sollumz is not using this function here.
    #       By moving it to a text data-block there is a still a bit of lag when interacting with large lists, but the rest
    #       of the UI works fine. Unfortunately, this means that the maps instance may not always exist if our dummy text
    #       data-block has not been created yet, so we have to take this into account in UI and operators code.
    #       Text was chosen because it's not as commonly used, so less code or add-ons should be interacting with text
    #       data-blocks.
    #       Use `get_maps()` instead of accessing the properties directly, in case we change how this works in the future.
    Text.sz_maps = PointerProperty(type=MapsProperties, name="Maps")
    Scene.sz_maps_container = PointerProperty(type=Text)


def unregister():
    del Text.sz_maps
    del Scene.sz_maps_container


#
# hw1 (group suggested name):
#  > hw1_lod
#    > hw1_01
#      > hw1_01_long_0
#      > hw1_01_strm_0
#      > hw1_01_strm_1
#      > hw1_01_interior_v_epsilonism_milo_
#    > hw1_02
#      > hw1_02_critical_0.ymap
#      > hw1_02_interior_v_bank_milo_.ymap
#      > hw1_02_interior_v_cinema_milo_.ymap
#      > hw1_02_interior_v_shop_247_milo_.ymap
#      > hw1_02_interior_v_tattoo_milo_.ymap
#      > hw1_02_long_0.ymap
#      > hw1_02_strm_0.ymap
#      > hw1_02_strm_1.ymap
#
# hw1_02_newbill (group suggested name):
#  > hw1_02_newbill_lod.ymap
#    > hw1_02_newbill.ymap
#
# hw1_02_oldbill (group suggested name):
#  > hw1_02_oldbill.ymap
#    > hw1_02_oldbill_lod.ymap
#
#
#
#
