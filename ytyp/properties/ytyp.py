import bpy
from bpy.types import (
    PropertyGroup,
)
from bpy.props import (
    BoolProperty,
)
from enum import IntEnum
from typing import Union, Optional
from uuid import uuid4
from ...tools.blenderhelper import get_children_recursive
from ...sollumz_properties import SollumType, items_from_enums, ArchetypeType, AssetType, TimeFlagsMixin, SOLLUMZ_UI_NAMES
from ...tools.utils import get_list_item
from .mlo import EntitySetProperties, RoomProperties, PortalProperties, MloEntityProperties, TimecycleModifierProperties
from .flags import ArchetypeFlags, MloFlags, RoomFlags, PortalFlags, EntityFlags
from .extensions import ExtensionsContainer, ExtensionType
from ...shared.multiselection import (
    MultiSelectProperty,
    MultiSelectPointerProperty,
    define_multiselect_access,
    MultiSelectAccessMixin,
    MultiSelectNestedAccessMixin,
    define_multiselect_collection,
    MultiSelectCollection,
)


class SpecialAttribute(IntEnum):
    NOTHING_SPECIAL = 0
    IS_TRAFFIC_LIGHT = 3
    UNKNOWN4 = 4
    IS_GARAGE_DOOR = 5
    MLO_WATER_LEVEL = 6
    IS_NORMAL_DOOR = 7
    IS_SLIDING_DOOR = 8
    IS_BARRIER_DOOR = 9
    IS_SLIDING_DOOR_VERTICAL = 10
    NOISY_BUSH = 11
    IS_RAIL_CROSSING_DOOR = 12
    NOISY_AND_DEFORMABLE_BUSH = 13
    SINGLE_AXIS_ROTATION = 14
    HAS_DYNAMIC_COVER_BOUND = 15
    RUMBLE_ON_LIGHT_COLLISION_WITH_VEHICLE = 16
    IS_RAIL_CROSSING_LIGHT = 17
    CLOCK = 30
    IS_STREET_LIGHT = 32

    # These don't need to be set by the user but some game files still have them, define them to prevent import errors
    UNUSED1 = 1,
    IS_LADDER = 2,  # set by the ladder extension at runtime
    IS_TREE_DEPRECATED = 31,  # same as double-sided rendering flag


SpecialAttributeEnumItems = tuple(None if enum is None else (enum.name, f"{label} ({enum.value})", desc, enum.value)
                                  for enum, label, desc in (
    (SpecialAttribute.NOTHING_SPECIAL, "None", ""),
    (None, "", ""),
    (SpecialAttribute.IS_NORMAL_DOOR, "Normal Door", ""),
    (SpecialAttribute.IS_GARAGE_DOOR, "Garage Door", ""),
    (SpecialAttribute.IS_SLIDING_DOOR, "Sliding Door", ""),
    (SpecialAttribute.IS_SLIDING_DOOR_VERTICAL, "Sliding Vertical Door", ""),
    (SpecialAttribute.IS_BARRIER_DOOR, "Barrier Door", ""),
    (SpecialAttribute.IS_RAIL_CROSSING_DOOR, "Rail Crossing Barrier Door", ""),
    (None, "", ""),
    (SpecialAttribute.IS_TRAFFIC_LIGHT, "Traffic Light", ""),
    (SpecialAttribute.IS_RAIL_CROSSING_LIGHT, "Rail Crossing Light", ""),
    (SpecialAttribute.IS_STREET_LIGHT, "Street Light", ""),
    (None, "", ""),
    (SpecialAttribute.NOISY_BUSH, "Bush", ""),
    (SpecialAttribute.NOISY_AND_DEFORMABLE_BUSH, "Deformable Bush", ""),
    (None, "", ""),
    (SpecialAttribute.SINGLE_AXIS_ROTATION, "Single Axis Rotation", "Enable single axis rotation procedural animation"),
    (SpecialAttribute.CLOCK, "Clock", "Enable animated clock hands"),
    (None, "", ""),
    (SpecialAttribute.MLO_WATER_LEVEL, "MLO Water Level", "Defines water level for a MLO"),
    (SpecialAttribute.HAS_DYNAMIC_COVER_BOUND, "Dynamic Cover Bound", "Has dynamic cover bounds"),
    (SpecialAttribute.RUMBLE_ON_LIGHT_COLLISION_WITH_VEHICLE, "Rumble On Vehicle Collision", ""),
    (None, "", ""),
    (SpecialAttribute.UNUSED1, "Deprecated - Unused",
     "Does nothing. Here for compatibility with original game files"),
    (SpecialAttribute.UNKNOWN4, "Unknown 4", ""),
    (SpecialAttribute.IS_LADDER, "Deprecated - Ladder",
     "Add a Ladder extension instead. Here for compatibility with original game files"),
    (SpecialAttribute.IS_TREE_DEPRECATED, "Deprecated - Tree",
     "Set 'Double-sided rendering' flag instead. Here for compatibility with original game files"),

))


class ArchetypeTimeFlags(TimeFlagsMixin, bpy.types.PropertyGroup):
    size = 25
    flag_names = TimeFlagsMixin.flag_names + ["swap_while_visible"]

    swap_while_visible: BoolProperty(
        name="Allow Swap While Visible",
        description=(
            "If enabled, the model may become visible or hidden while the player is looking at it; otherwise, waits "
            "until the player faces the camera away"
        ),
        update=TimeFlagsMixin.update_flag,
    )


@define_multiselect_access(RoomFlags)
class RoomFlagsSelectionAccess(MultiSelectNestedAccessMixin, PropertyGroup):
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


@define_multiselect_access(RoomProperties)
class RoomSelectionAccess(MultiSelectAccessMixin, PropertyGroup):
    name: MultiSelectProperty()
    bb_min: MultiSelectProperty()
    bb_max: MultiSelectProperty()
    blend: MultiSelectProperty()
    timecycle: MultiSelectProperty()
    secondary_timecycle: MultiSelectProperty()
    floor_id: MultiSelectProperty()
    exterior_visibility_depth: MultiSelectProperty()
    flags: MultiSelectPointerProperty(RoomFlagsSelectionAccess)


@define_multiselect_access(PortalFlags)
class PortalFlagsSelectionAccess(MultiSelectNestedAccessMixin, PropertyGroup):
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


@define_multiselect_access(PortalProperties)
class PortalSelectionAccess(MultiSelectAccessMixin, PropertyGroup):
    corner1: MultiSelectProperty()
    corner2: MultiSelectProperty()
    corner3: MultiSelectProperty()
    corner4: MultiSelectProperty()

    room_from_id: MultiSelectProperty()
    room_to_id: MultiSelectProperty()

    mirror_priority: MultiSelectProperty()
    opacity: MultiSelectProperty()
    audio_occlusion: MultiSelectProperty()
    flags: MultiSelectPointerProperty(PortalFlagsSelectionAccess)


@define_multiselect_access(EntityFlags)
class MloEntityFlagsSelectionAccess(MultiSelectNestedAccessMixin, PropertyGroup):
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


@define_multiselect_access(MloEntityProperties)
class MloEntitySelectionAccess(MultiSelectAccessMixin, PropertyGroup):
    # from EntityProperties
    archetype_name: MultiSelectProperty()
    guid: MultiSelectProperty()
    parent_index: MultiSelectProperty()
    lod_dist: MultiSelectProperty()
    child_lod_dist: MultiSelectProperty()
    lod_level: MultiSelectProperty()
    num_children: MultiSelectProperty()
    priority_level: MultiSelectProperty()
    ambient_occlusion_multiplier: MultiSelectProperty()
    artificial_ambient_occlusion: MultiSelectProperty()
    tint_value: MultiSelectProperty()

    # from MloEntityProperties
    attached_portal_id: MultiSelectProperty()
    attached_room_id: MultiSelectProperty()
    attached_entity_set_id: MultiSelectProperty()

    flags: MultiSelectPointerProperty(MloEntityFlagsSelectionAccess)


@define_multiselect_access(TimecycleModifierProperties)
class TimecycleModifierSelectionAccess(MultiSelectAccessMixin, PropertyGroup):
    name: MultiSelectProperty()
    sphere: MultiSelectProperty()
    percentage: MultiSelectProperty()
    range: MultiSelectProperty()
    start_hour: MultiSelectProperty()
    end_hour: MultiSelectProperty()


@define_multiselect_access(EntitySetProperties)
class EntitySetSelectionAccess(MultiSelectAccessMixin, PropertyGroup):
    name: MultiSelectProperty()


@define_multiselect_collection("rooms", {"name": "Rooms"})
@define_multiselect_collection("portals", {"name": "Portals"})
@define_multiselect_collection("entities", {"name": "Entities"})
@define_multiselect_collection("timecycle_modifiers", {"name": "Timecycle Modifiers"})
@define_multiselect_collection("entity_sets", {"name": "Entity Sets"})
class ArchetypeProperties(bpy.types.PropertyGroup, ExtensionsContainer):
    IS_ARCHETYPE = True
    DEFAULT_EXTENSION_TYPE = ExtensionType.PARTICLE

    __portal_enum_items_cache: dict[str, list] = {}
    __room_enum_items_cache: dict[str, list] = {}
    __entity_set_enum_items_cache: dict[str, list] = {}

    def update_asset(self, context):
        if self.asset:
            self.asset_name = self.asset.name
            # Automatically determine asset type
            if self.asset.sollum_type == SollumType.BOUND_COMPOSITE:
                self.asset_type = AssetType.ASSETLESS
                self.drawable_dictionary = ""
                self.physics_dictionary = ""
                self.texture_dictionary = ""
            elif self.asset.sollum_type == SollumType.DRAWABLE:
                self.asset_type = AssetType.DRAWABLE
                # Check if in a drawable dictionary
                if self.asset.parent and hasattr(self.asset.parent, "sollum_type") and self.asset.parent.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                    self.drawable_dictionary = self.asset.parent.name
            elif self.asset.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                self.asset_type = AssetType.DRAWABLE_DICTIONARY
            elif self.asset.sollum_type == SollumType.FRAGMENT:
                self.asset_type = AssetType.FRAGMENT
            # Check for embedded collisions
            if self.asset_type in [AssetType.DRAWABLE, AssetType.FRAGMENT]:
                for child in get_children_recursive(self.asset):
                    if child.sollum_type == SollumType.BOUND_COMPOSITE:
                        self.physics_dictionary = self.asset_name
                    # Check for embedded textures
                    if child.sollum_type == SollumType.DRAWABLE_GEOMETRY:
                        for mat in child.data.materials:
                            if not mat.use_nodes:
                                continue
                            for node in mat.node_tree.nodes:
                                if isinstance(node, bpy.types.ShaderNodeTexImage):
                                    if node.texture_properties.embedded == True:
                                        self.texture_dictionary = self.asset_name
                                        break

    def new_portal(self) -> PortalProperties:
        item_id = self.get_new_item_id(self.portals)

        item = self.portals.add()
        self.portals.select(len(self.portals) - 1)

        item.id = item_id
        item.uuid = str(uuid4())

        if len(self.rooms) > 0:
            room_id = self.rooms[0].id
            item.room_to_id = str(room_id)
            item.room_from_id = str(room_id)

        item.mlo_archetype_id = self.id
        item.mlo_archetype_uuid = self.uuid

        ArchetypeProperties.update_cached_portal_enum_items(self.uuid)

        return item

    def new_room(self) -> RoomProperties:
        item_id = self.get_new_item_id(self.rooms)

        item = self.rooms.add()
        self.rooms.select(len(self.rooms) - 1)

        item.id = item_id
        item.uuid = str(uuid4())

        item.mlo_archetype_id = self.id
        item.mlo_archetype_uuid = self.uuid

        item.name = f"Room.{item.id}"

        ArchetypeProperties.update_cached_room_enum_items(self.uuid)

        return item

    def new_entity(self) -> MloEntityProperties:
        item_id = self.get_new_item_id(self.entities)

        item = self.entities.add()
        self.entities.select(len(self.entities) - 1)

        item.id = item_id
        item.uuid = str(uuid4())

        item.mlo_archetype_id = self.id
        item.mlo_archetype_uuid = self.uuid

        item.archetype_name = f"Entity.{item_id}"

        return item

    def new_tcm(self) -> TimecycleModifierProperties:
        item = self.timecycle_modifiers.add()
        self.timecycle_modifiers.select(len(self.timecycle_modifiers) - 1)

        item.mlo_archetype_id = self.id
        item.mlo_archetype_uuid = self.uuid

        return item

    def new_entity_set(self) -> EntitySetProperties:
        item_id = self.get_new_item_id(self.entity_sets)

        item = self.entity_sets.add()
        self.entity_sets.select(len(self.entity_sets) - 1)

        item.id = item_id
        item.uuid = str(uuid4())

        item.mlo_archetype_id = self.id
        item.mlo_archetype_uuid = self.uuid

        item.name = f"EntitySet.{item.id}"

        ArchetypeProperties.update_cached_entity_set_enum_items(self.uuid)

        return item

    def get_new_item_id(self, collection: bpy.types.bpy_prop_collection) -> int:
        """Gets unique ID for a new item in ``collection``"""
        ids = sorted({item.id for item in collection})

        if not ids:
            return 1

        for i, item_id in enumerate(ids):
            new_id = item_id + 1

            if new_id in ids:
                continue

            if i + 1 >= len(ids):
                return new_id

            next_item = ids[i + 1]

            if next_item > new_id:
                return new_id

        # Max id + 1
        return ids[-1] + 1

    def select_entity_linked_object(self):
        entity = self.entities.active_item
        if entity.linked_object:
            bpy.context.view_layer.objects.active = entity.linked_object
            bpy.ops.object.select_all(action="DESELECT")
            entity.linked_object.select_set(True)

    def on_entities_active_index_update_from_ui(self, context):
        self.select_entity_linked_object()

    bb_min: bpy.props.FloatVectorProperty(name="Bound Min")
    bb_max: bpy.props.FloatVectorProperty(name="Bound Max")
    bs_center: bpy.props.FloatVectorProperty(name="Bound Center")
    bs_radius: bpy.props.FloatProperty(name="Bound Radius")
    type: bpy.props.EnumProperty(items=items_from_enums(ArchetypeType), name="Type")
    lod_dist: bpy.props.FloatProperty(name="Lod Distance", default=200, min=-1)
    flags: bpy.props.PointerProperty(type=ArchetypeFlags, name="Flags")
    special_attribute: bpy.props.EnumProperty(
        name="Special Attribute", items=SpecialAttributeEnumItems, default=SpecialAttribute.NOTHING_SPECIAL.name)
    hd_texture_dist: bpy.props.FloatProperty(name="HD Texture Distance", default=100, min=0)
    name: bpy.props.StringProperty(name="Name")
    texture_dictionary: bpy.props.StringProperty(name="Texture Dictionary")
    clip_dictionary: bpy.props.StringProperty(name="Clip Dictionary")
    drawable_dictionary: bpy.props.StringProperty(name="Drawable Dictionary")
    physics_dictionary: bpy.props.StringProperty(name="Physics Dictionary")
    asset_type: bpy.props.EnumProperty(items=items_from_enums(AssetType), name="Asset Type")
    asset: bpy.props.PointerProperty(name="Asset", type=bpy.types.Object, update=update_asset)
    asset_name: bpy.props.StringProperty(name="Asset Name")
    # Time archetype
    time_flags: bpy.props.PointerProperty(type=ArchetypeTimeFlags, name="Time Flags")
    # Mlo archetype
    mlo_flags: bpy.props.PointerProperty(type=MloFlags, name="MLO Flags")
    rooms: MultiSelectCollection[RoomProperties, RoomSelectionAccess]
    portals: MultiSelectCollection[PortalProperties, PortalSelectionAccess]
    entities: MultiSelectCollection[MloEntityProperties, MloEntitySelectionAccess]
    timecycle_modifiers: MultiSelectCollection[TimecycleModifierProperties, TimecycleModifierSelectionAccess]
    entity_sets: MultiSelectCollection[EntitySetProperties, EntitySetSelectionAccess]

    id: bpy.props.IntProperty(default=-1)
    uuid: bpy.props.StringProperty(name="UUID", maxlen=36)  # unique within the whole .blend

    @property
    def non_entity_set_entities(self) -> list[MloEntityProperties]:
        return [entity for entity in self.entities if entity.attached_entity_set_id == "-1"]

    @property
    def selected_room(self) -> Union[RoomProperties, None]:
        return get_list_item(self.rooms, self.rooms.active_index)

    @property
    def selected_portal(self) -> Union[PortalProperties, None]:
        return get_list_item(self.portals, self.portals.active_index)

    @property
    def selected_entity(self) -> Union[MloEntityProperties, None]:
        return get_list_item(self.entities, self.entities.active_index)

    @property
    def selected_tcm(self) -> Union[TimecycleModifierProperties, None]:
        return get_list_item(self.timecycle_modifiers, self.timecycle_modifiers.active_index)

    @property
    def selected_entity_set(self) -> Union[EntitySetProperties, None]:
        return get_list_item(self.entity_sets, self.entity_sets.active_index)

    @property
    def selected_entity_set_id(self):
        return self.entity_sets.active_index

    def get_portal_enum_items(self) -> list:
        if items := ArchetypeProperties.__portal_enum_items_cache.get(self.uuid, None):
            return items

        items = [("-1", "None", "", -1)]
        for portal in self.portals:
            items.append((str(portal.id), portal.name, "", portal.id))
        ArchetypeProperties.__portal_enum_items_cache[self.uuid] = items
        return items

    def get_room_enum_items(self) -> list:
        if items := ArchetypeProperties.__room_enum_items_cache.get(self.uuid, None):
            return items

        items = [("-1", "None", "", -1)]
        for room in self.rooms:
            items.append((str(room.id), room.name, "", room.id))
        ArchetypeProperties.__room_enum_items_cache[self.uuid] = items
        return items

    def get_entity_set_enum_items(self) -> list:
        if items := ArchetypeProperties.__entity_set_enum_items_cache.get(self.uuid, None):
            return items

        items = [("-1", "None", "", -1)]
        for entity_set in self.entity_sets:
            items.append((str(entity_set.id), entity_set.name, "", entity_set.id))
        ArchetypeProperties.__entity_set_enum_items_cache[self.uuid] = items
        return items

    @staticmethod
    def get_cached_portal_enum_items(archetype_uuid: str) -> Optional[list]:
        return ArchetypeProperties.__portal_enum_items_cache.get(archetype_uuid, None)

    @staticmethod
    def get_cached_room_enum_items(archetype_uuid: str) -> Optional[list]:
        return ArchetypeProperties.__room_enum_items_cache.get(archetype_uuid, None)

    @staticmethod
    def get_cached_entity_set_enum_items(archetype_uuid: str) -> Optional[list]:
        return ArchetypeProperties.__entity_set_enum_items_cache.get(archetype_uuid, None)

    @staticmethod
    def update_cached_portal_enum_items(archetype_uuid: str) -> Optional[list]:
        if archetype_uuid in ArchetypeProperties.__portal_enum_items_cache:
            del ArchetypeProperties.__portal_enum_items_cache[archetype_uuid]

    @staticmethod
    def update_cached_room_enum_items(archetype_uuid: str) -> Optional[list]:
        if archetype_uuid in ArchetypeProperties.__room_enum_items_cache:
            del ArchetypeProperties.__room_enum_items_cache[archetype_uuid]

    @staticmethod
    def update_cached_entity_set_enum_items(archetype_uuid: str) -> Optional[list]:
        if archetype_uuid in ArchetypeProperties.__entity_set_enum_items_cache:
            del ArchetypeProperties.__entity_set_enum_items_cache[archetype_uuid]


@define_multiselect_access(ArchetypeFlags)
class ArchetypeFlagsSelectionAccess(MultiSelectNestedAccessMixin, PropertyGroup):
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


@define_multiselect_access(ArchetypeTimeFlags)
class ArchetypeTimeFlagsSelectionAccess(MultiSelectNestedAccessMixin, PropertyGroup):
    total: MultiSelectProperty()
    hour1: MultiSelectProperty()
    hour2: MultiSelectProperty()
    hour3: MultiSelectProperty()
    hour4: MultiSelectProperty()
    hour5: MultiSelectProperty()
    hour6: MultiSelectProperty()
    hour7: MultiSelectProperty()
    hour8: MultiSelectProperty()
    hour9: MultiSelectProperty()
    hour10: MultiSelectProperty()
    hour11: MultiSelectProperty()
    hour12: MultiSelectProperty()
    hour13: MultiSelectProperty()
    hour14: MultiSelectProperty()
    hour15: MultiSelectProperty()
    hour16: MultiSelectProperty()
    hour17: MultiSelectProperty()
    hour18: MultiSelectProperty()
    hour19: MultiSelectProperty()
    hour20: MultiSelectProperty()
    hour21: MultiSelectProperty()
    hour22: MultiSelectProperty()
    hour23: MultiSelectProperty()
    hour24: MultiSelectProperty()
    swap_while_visible: MultiSelectProperty()


@define_multiselect_access(MloFlags)
class ArchetypeMloFlagsSelectionAccess(MultiSelectNestedAccessMixin, PropertyGroup):
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


@define_multiselect_access(ArchetypeProperties)
class ArchetypeSelectionAccess(MultiSelectAccessMixin, PropertyGroup):
    type: MultiSelectProperty()
    lod_dist: MultiSelectProperty()
    special_attribute: MultiSelectProperty()
    hd_texture_dist: MultiSelectProperty()
    name: MultiSelectProperty()
    texture_dictionary: MultiSelectProperty()
    clip_dictionary: MultiSelectProperty()
    drawable_dictionary: MultiSelectProperty()
    physics_dictionary: MultiSelectProperty()
    asset_type: MultiSelectProperty()
    asset_name: MultiSelectProperty()

    flags: MultiSelectPointerProperty(ArchetypeFlagsSelectionAccess)
    time_flags: MultiSelectPointerProperty(ArchetypeTimeFlagsSelectionAccess)
    mlo_flags: MultiSelectPointerProperty(ArchetypeMloFlagsSelectionAccess)


@define_multiselect_collection("archetypes", {"name": "Archetypes"})
class CMapTypesProperties(PropertyGroup):
    def update_mlo_archetype_ids(self):
        for archetype in self.archetypes:
            if archetype.type == ArchetypeType.MLO:
                archetype.id = self.last_archetype_id
                self.last_archetype_id += 1

                for entity in archetype.entities:
                    entity.mlo_archetype_id = archetype.id
                    entity.mlo_archetype_uuid = archetype.uuid

                for portal in archetype.portals:
                    portal.mlo_archetype_id = archetype.id
                    portal.mlo_archetype_uuid = archetype.uuid

                for room in archetype.rooms:
                    room.mlo_archetype_id = archetype.id
                    room.mlo_archetype_uuid = archetype.uuid

                for tcm in archetype.timecycle_modifiers:
                    tcm.mlo_archetype_id = archetype.id
                    tcm.mlo_archetype_uuid = archetype.uuid

                for entity_set in archetype.entity_sets:
                    entity_set.mlo_archetype_id = archetype.id
                    entity_set.mlo_archetype_uuid = archetype.uuid

    def new_archetype(self):
        item = self.archetypes.add()
        index = len(self.archetypes) - 1
        self.archetypes.select(index)

        item.id = self.last_archetype_id + 1
        item.uuid = str(uuid4())
        item.name = f"{SOLLUMZ_UI_NAMES[ArchetypeType.BASE]}.{index + 1}"

        self.last_archetype_id += 1

        return item

    def select_archetype_linked_object(self):
        archetype = self.archetypes.active_item
        if archetype.asset:
            bpy.context.view_layer.objects.active = archetype.asset
            bpy.ops.object.select_all(action="DESELECT")
            archetype.asset.select_set(True)

    def on_archetypes_active_index_update_from_ui(self, context):
        self.select_archetype_linked_object()

    name: bpy.props.StringProperty(name="Name")
    archetypes: MultiSelectCollection[ArchetypeProperties, ArchetypeSelectionAccess]

    # Unique archetype id
    last_archetype_id: bpy.props.IntProperty()

    @property
    def selected_archetype(self) -> Union[ArchetypeProperties, None]:
        return get_list_item(self.archetypes, self.archetypes.active_index)


def register():
    bpy.types.Scene.ytyps = bpy.props.CollectionProperty(type=CMapTypesProperties, name="YTYPs")
    bpy.types.Scene.ytyp_index = bpy.props.IntProperty(name="YTYP")
    bpy.types.Scene.show_room_gizmo = bpy.props.BoolProperty(
        name="Show Room Gizmo", default=True)
    bpy.types.Scene.show_portal_gizmo = bpy.props.BoolProperty(
        name="Show Portal Gizmo", default=True)

    bpy.types.Scene.create_archetype_type = bpy.props.EnumProperty(
        items=items_from_enums(ArchetypeType), name="Type")

    bpy.types.Scene.ytyp_apply_transforms = bpy.props.BoolProperty(
        name="Apply Parent Transforms", description="Apply transforms to all assets when calculating Archetype extents")


def unregister():
    del bpy.types.Scene.ytyps
    del bpy.types.Scene.ytyp_index
    del bpy.types.Scene.show_room_gizmo
    del bpy.types.Scene.show_portal_gizmo
    del bpy.types.Scene.create_archetype_type
    del bpy.types.Scene.ytyp_apply_transforms
