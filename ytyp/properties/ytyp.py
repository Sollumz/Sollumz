import bpy
from bpy.props import (
    BoolProperty,
)
from enum import IntEnum
from typing import Union
from ...tools.blenderhelper import get_children_recursive
from ...sollumz_properties import SollumType, items_from_enums, ArchetypeType, AssetType, TimeFlagsMixin, SOLLUMZ_UI_NAMES
from ...tools.utils import get_list_item
from .mlo import EntitySetProperties, RoomProperties, PortalProperties, MloEntityProperties, TimecycleModifierProperties
from .flags import ArchetypeFlags, MloFlags
from .extensions import ExtensionsContainer, ExtensionType


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
    IS_LADDER = 2, # set by the ladder extension at runtime
    IS_TREE_DEPRECATED = 31, # same as double-sided rendering flag


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


class ArchetypeProperties(bpy.types.PropertyGroup, ExtensionsContainer):
    IS_ARCHETYPE = True
    DEFAULT_EXTENSION_TYPE = ExtensionType.PARTICLE

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
            elif self.asset.sollum_type == AssetType.FRAGMENT:
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
        self.portal_index = len(self.portals) - 1

        item.id = item_id

        if len(self.rooms) > 0:
            room_id = self.rooms[0].id
            item.room_to_id = str(room_id)
            item.room_from_id = str(room_id)

        item.mlo_archetype_id = self.id

        return item

    def new_room(self) -> RoomProperties:
        item_id = self.get_new_item_id(self.rooms)

        item = self.rooms.add()
        self.room_index = len(self.rooms) - 1

        item.id = item_id
        item.mlo_archetype_id = self.id

        item.name = f"Room.{item.id}"

        return item

    def new_entity(self) -> MloEntityProperties:
        item_id = self.get_new_item_id(self.entities)

        item = self.entities.add()
        self.entity_index = len(self.entities) - 1

        item.id = item_id

        item.mlo_archetype_id = self.id

        item.archetype_name = f"Entity.{item_id}"

        return item

    def new_tcm(self) -> TimecycleModifierProperties:
        item = self.timecycle_modifiers.add()
        item.mlo_archetype_id = self.id

        return item

    def new_entity_set(self) -> EntitySetProperties:
        item_id = self.get_new_item_id(self.entity_sets)

        item = self.entity_sets.add()
        self.entity_set_index = len(self.entity_sets) - 1

        item.id = item_id
        item.mlo_archetype_id = self.id

        item.name = f"EntitySet.{item.id}"

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

    bb_min: bpy.props.FloatVectorProperty(name="Bound Min")
    bb_max: bpy.props.FloatVectorProperty(name="Bound Max")
    bs_center: bpy.props.FloatVectorProperty(name="Bound Center")
    bs_radius: bpy.props.FloatProperty(name="Bound Radius")
    type: bpy.props.EnumProperty(
        items=items_from_enums(ArchetypeType), name="Type")
    lod_dist: bpy.props.FloatProperty(name="Lod Distance", default=60, min=-1)
    flags: bpy.props.PointerProperty(
        type=ArchetypeFlags, name="Flags")
    special_attribute: bpy.props.EnumProperty(
        name="Special Attribute", items=SpecialAttributeEnumItems, default=SpecialAttribute.NOTHING_SPECIAL.name)
    hd_texture_dist: bpy.props.FloatProperty(
        name="HD Texture Distance", default=40, min=0)
    name: bpy.props.StringProperty(name="Name")
    texture_dictionary: bpy.props.StringProperty(name="Texture Dictionary")
    clip_dictionary: bpy.props.StringProperty(name="Clip Dictionary")
    drawable_dictionary: bpy.props.StringProperty(name="Drawable Dictionary")
    physics_dictionary: bpy.props.StringProperty(
        name="Physics Dictionary")
    asset_type: bpy.props.EnumProperty(
        items=items_from_enums(AssetType), name="Asset Type")
    asset: bpy.props.PointerProperty(
        name="Asset", type=bpy.types.Object, update=update_asset)
    asset_name: bpy.props.StringProperty(
        name="Asset Name")
    # Time archetype
    time_flags: bpy.props.PointerProperty(type=ArchetypeTimeFlags, name="Time Flags")
    # Mlo archetype
    mlo_flags: bpy.props.PointerProperty(type=MloFlags, name="MLO Flags")
    rooms: bpy.props.CollectionProperty(type=RoomProperties, name="Rooms")
    portals: bpy.props.CollectionProperty(
        type=PortalProperties, name="Portals")
    entities: bpy.props.CollectionProperty(
        type=MloEntityProperties, name="Entities")
    timecycle_modifiers: bpy.props.CollectionProperty(
        type=TimecycleModifierProperties, name="Timecycle Modifiers")
    entity_sets: bpy.props.CollectionProperty(
        type=EntitySetProperties, name="EntitySets")

    # Selected room index
    room_index: bpy.props.IntProperty(name="Room")
    # Selected portal index
    portal_index: bpy.props.IntProperty(name="Portal")
    # Selected entity index
    entity_index: bpy.props.IntProperty(name="Entity")
    # Selected timecycle modifier index
    tcm_index: bpy.props.IntProperty(
        name="Timecycle Modifier")
    # Selected entityset
    entity_set_index: bpy.props.IntProperty(
        name="Entity Set")

    all_entity_lod_dist: bpy.props.FloatProperty(name="Entity Lod Distance: ")

    id: bpy.props.IntProperty(default=-1)

    @property
    def non_entity_set_entities(self) -> list[MloEntityProperties]:
        return [entity for entity in self.entities if entity.attached_entity_set_id == "-1"]

    @property
    def selected_room(self) -> Union[RoomProperties, None]:
        return get_list_item(self.rooms, self.room_index)

    @property
    def selected_portal(self) -> Union[PortalProperties, None]:
        return get_list_item(self.portals, self.portal_index)

    @property
    def selected_entity(self) -> Union[MloEntityProperties, None]:
        return get_list_item(self.entities, self.entity_index)

    @property
    def selected_tcm(self) -> Union[TimecycleModifierProperties, None]:
        return get_list_item(self.timecycle_modifiers, self.tcm_index)

    @property
    def selected_entity_set(self) -> Union[EntitySetProperties, None]:
        return get_list_item(self.entity_sets, self.entity_set_index)

    @property
    def selected_entity_set_id(self):
        return self.entity_set_index


class CMapTypesProperties(bpy.types.PropertyGroup):
    def update_mlo_archetype_ids(self):
        for archetype in self.archetypes:
            if archetype.type == ArchetypeType.MLO:
                archetype.id = self.last_archetype_id
                self.last_archetype_id += 1

                for entity in archetype.entities:
                    entity.mlo_archetype_id = archetype.id

                for portal in archetype.portals:
                    portal.mlo_archetype_id = archetype.id

                for room in archetype.rooms:
                    room.mlo_archetype_id = archetype.id

                for tcm in archetype.timecycle_modifiers:
                    tcm.mlo_archetype_id = archetype.id

    def new_archetype(self):
        item = self.archetypes.add()
        index = len(self.archetypes)
        item.name = f"{SOLLUMZ_UI_NAMES[ArchetypeType.BASE]}.{index}"
        self.archetype_index = index - 1
        item.id = self.last_archetype_id + 1
        self.last_archetype_id += 1

        return item

    name: bpy.props.StringProperty(name="Name")
    all_texture_dictionary: bpy.props.StringProperty(
        name="Texture Dictionary: ")
    all_lod_dist: bpy.props.FloatProperty(name="Lod Distance: ")
    all_hd_tex_dist: bpy.props.FloatProperty(name="HD Texture Distance: ")
    all_flags: bpy.props.IntProperty(name="Flags: ")
    # extensions
    archetypes: bpy.props.CollectionProperty(
        type=ArchetypeProperties, name="Archetypes")
    # Selected archetype index
    archetype_index: bpy.props.IntProperty(
        name="Archetype Index")
    # Unique archetype id
    last_archetype_id: bpy.props.IntProperty()

    @property
    def selected_archetype(self) -> Union[ArchetypeProperties, None]:
        return get_list_item(self.archetypes, self.archetype_index)


def register():
    bpy.types.Scene.ytyps = bpy.props.CollectionProperty(
        type=CMapTypesProperties, name="YTYPs")
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
