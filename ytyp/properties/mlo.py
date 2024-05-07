from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .ytyp import ArchetypeProperties

import bpy
from ...sollumz_properties import EntityProperties
from ...tools.utils import get_list_item
from ..utils import get_selected_ytyp, get_selected_archetype
from .flags import EntityFlags, RoomFlags, PortalFlags
from .extensions import ExtensionsContainer


def get_portal_items_for_archetype(archetype: Optional["ArchetypeProperties"]):
    items = [("-1", "None", "", -1)]

    if archetype is None:
        return items

    for portal in archetype.portals:
        items.append((str(portal.id), portal.name, "", portal.id))

    return items


def get_room_items_for_archetype(archetype: Optional["ArchetypeProperties"]):
    items = [("-1", "None", "", -1)]

    if archetype is None:
        return items

    for room in archetype.rooms:
        items.append((str(room.id), room.name, "", room.id))

    return items


def get_entityset_items_for_archetype(archetype: Optional["ArchetypeProperties"]):
    items = [("-1", "None", "", -1)]

    if archetype is None:
        return items

    for entitySet in archetype.entity_sets:
        items.append((str(entitySet.id), entitySet.name, "", entitySet.id))

    return items


def get_room_items_for_selected_archetype(self, context: Optional[bpy.types.Context]):
    archetype = get_selected_archetype(context)
    return get_room_items_for_archetype(archetype)


def get_portal_items_for_selected_archetype(self, context: Optional[bpy.types.Context]):
    archetype = get_selected_archetype(context)
    return get_portal_items_for_archetype(archetype)


def get_entityset_items_for_selected_archetype(self, context: Optional[bpy.types.Context]):
    archetype = get_selected_archetype(context)
    return get_entityset_items_for_archetype(archetype)


class MloArchetypeChild:
    def get_mlo_archetype(self):
        selected_ytyp = get_selected_ytyp(bpy.context)

        if self.mlo_archetype_id == -1:
            selected_ytyp.update_mlo_archetype_ids()
        for archetype in selected_ytyp.archetypes:
            if archetype.id == self.mlo_archetype_id:
                return archetype

    def get_room_items(self, context: Optional[bpy.types.Context]):
        archetype = self.get_mlo_archetype()
        return get_room_items_for_archetype(archetype)

    def get_portal_items(self, context: Optional[bpy.types.Context]):
        archetype = self.get_mlo_archetype()
        return get_portal_items_for_archetype(archetype)

    def get_entityset_items(self, context: Optional[bpy.types.Context]):
        archetype = self.get_mlo_archetype()
        return get_entityset_items_for_archetype(archetype)

    mlo_archetype_id: bpy.props.IntProperty(default=-1)


class RoomProperties(bpy.types.PropertyGroup, MloArchetypeChild):
    name: bpy.props.StringProperty(name="Name")
    bb_min: bpy.props.FloatVectorProperty(name="Bounds Min", subtype="XYZ")
    bb_max: bpy.props.FloatVectorProperty(name="Bounds Max", subtype="XYZ")
    blend: bpy.props.FloatProperty(name="Blend", default=1)
    timecycle: bpy.props.StringProperty(
        name="Timecycle", default="int_gasstation")
    secondary_timecycle: bpy.props.StringProperty(
        name="Secondary Timecycle")
    flags: bpy.props.PointerProperty(type=RoomFlags, name="Flags")
    floor_id: bpy.props.IntProperty(name="Floor ID")
    exterior_visibility_depth: bpy.props.IntProperty(
        name="Exterior Visibility Depth", default=-1)

    # Blender usage only
    id: bpy.props.IntProperty(name="Id")


class PortalProperties(bpy.types.PropertyGroup, MloArchetypeChild):
    def get_room_from_index(self):
        archetype = self.get_mlo_archetype()
        room_from_id = self.room_from_id

        if archetype is None:
            return 0

        for index, room in enumerate(archetype.rooms):
            if not room_from_id:
                continue

            if room.id == int(room_from_id):
                return index

        return 0

    def get_room_to_index(self):
        archetype = self.get_mlo_archetype()
        room_to_id = self.room_to_id

        if archetype is None:
            return 0

        for index, room in enumerate(archetype.rooms):
            if not room_to_id:
                continue

            if room.id == int(room_to_id):
                return index

        return 0

    def get_room_name(self, room_index: int):
        archetype = self.get_mlo_archetype()

        if archetype is None or not archetype.rooms:
            return ""

        if room_index < len(archetype.rooms) and room_index >= 0:
            return archetype.rooms[room_index].name

        return archetype.rooms[0].name

    def get_portal_index(self):
        archetype = self.get_mlo_archetype()

        for index, portal in enumerate(archetype.portals):
            if portal.id == self.id:
                return index

        return 0

    def update_room_names(self, context):
        self.room_from_name = self.get_room_name(self.room_from_index)
        self.room_to_name = self.get_room_name(self.room_to_index)

    def get_name(self):
        if not self.room_from_name or not self.room_to_name:
            self.update_room_names(bpy.context)

        return f"{self.get_portal_index() + 1} | {self.room_from_name} to {self.room_to_name}"

    # Work around to store audio_occlusion as a string property since blender int property cant store 32 bit unsigned integers
    def update_audio_occlusion(self, context):
        try:
            int(self.audio_occlusion)
        except ValueError:
            self.audio_occlusion = "0"

        value = int(self.audio_occlusion)
        max_val = (2**32) - 1

        if value < 0:
            self.audio_occlusion = str(max_val)
        elif value > max_val:
            self.audio_occlusion = "0"

    corner1: bpy.props.FloatVectorProperty(name="Corner 1", subtype="XYZ")
    corner2: bpy.props.FloatVectorProperty(name="Corner 2", subtype="XYZ")
    corner3: bpy.props.FloatVectorProperty(name="Corner 3", subtype="XYZ")
    corner4: bpy.props.FloatVectorProperty(name="Corner 4", subtype="XYZ")

    room_from_id: bpy.props.EnumProperty(
        name="Room From", items=MloArchetypeChild.get_room_items, update=update_room_names, default=-1)
    room_from_index: bpy.props.IntProperty(
        name="Room From Index", get=get_room_from_index)
    room_from_name: bpy.props.StringProperty(name="Room From")

    room_to_id: bpy.props.EnumProperty(
        name="Room To", items=MloArchetypeChild.get_room_items, update=update_room_names, default=-1)
    room_to_index: bpy.props.IntProperty(
        name="Room To Index", get=get_room_to_index)
    room_to_name: bpy.props.StringProperty(name="Room To")

    flags: bpy.props.PointerProperty(type=PortalFlags, name="Flags")
    mirror_priority: bpy.props.IntProperty(name="Mirror Priority")
    opacity: bpy.props.IntProperty(name="Opacity")
    audio_occlusion: bpy.props.StringProperty(
        name="Audio Occlusion", update=update_audio_occlusion, default="0")

    # Blender use only
    name: bpy.props.StringProperty(name="Name", default="Portal", get=get_name)
    id: bpy.props.IntProperty(name="Id")


class TimecycleModifierProperties(bpy.types.PropertyGroup, MloArchetypeChild):
    name: bpy.props.StringProperty(name="Name")
    sphere: bpy.props.FloatVectorProperty(name="Sphere", subtype="QUATERNION", size=4)
    percentage: bpy.props.FloatProperty(name="Percentage", min=0.0, max=100.0, step=100)
    range: bpy.props.FloatProperty(name="Range")
    start_hour: bpy.props.IntProperty(name="Start Hour")
    end_hour: bpy.props.IntProperty(name="End Hour")


class MloEntityProperties(bpy.types.PropertyGroup, EntityProperties, MloArchetypeChild, ExtensionsContainer):
    def get_portal_index(self):
        selected_archetype = self.get_mlo_archetype()
        attached_portal_id = self.attached_portal_id

        if selected_archetype is None:
            return -1

        if attached_portal_id:
            for index, portal in enumerate(selected_archetype.portals):
                if portal.id == int(attached_portal_id):
                    return index

        return -1

    def get_portal_name(self):
        selected_archetype = self.get_mlo_archetype()
        portal = get_list_item(selected_archetype.portals,
                               self.portal_index)

        if selected_archetype is None:
            return -1

        if portal:
            return portal.name
        return ""

    def get_room_index(self):
        selected_archetype = self.get_mlo_archetype()
        attached_room_id = self.attached_room_id

        if selected_archetype is None:
            return -1

        if attached_room_id:
            for index, room in enumerate(selected_archetype.rooms):
                if room.id == int(attached_room_id):
                    return index

        return -1

    def get_entityset_name(self):
        selected_archetype = self.get_mlo_archetype()
        entity_set = get_list_item(selected_archetype.entity_sets,
                                   self.entity_set_index)
        if entity_set and selected_archetype is not None:
            return entity_set.name
        return ""

    def get_entityset_index(self):
        selected_archetype = self.get_mlo_archetype()
        attached_entity_set_id = self.attached_entity_set_id

        if attached_entity_set_id and selected_archetype is not None:
            for index, room in enumerate(selected_archetype.entity_sets):
                if room.id == int(attached_entity_set_id):
                    return index

        return -1

    def get_room_name(self):
        selected_archetype = self.get_mlo_archetype()
        room = get_list_item(selected_archetype.rooms,
                             self.room_index)
        if room and selected_archetype is not None:
            return room.name
        return ""

    # Transforms unused if no linked object
    position: bpy.props.FloatVectorProperty(name="Position")
    rotation: bpy.props.FloatVectorProperty(
        name="Rotation", subtype="QUATERNION", size=4, default=(1, 0, 0, 0))
    scale_xy: bpy.props.FloatProperty(name="Scale XY", default=1)
    scale_z: bpy.props.FloatProperty(name="Scale Z", default=1)

    attached_portal_id: bpy.props.EnumProperty(
        name="Portal", items=MloArchetypeChild.get_portal_items, default=-1)
    portal_index: bpy.props.IntProperty(
        name="Attached Portal Index", get=get_portal_index)
    portal_name: bpy.props.StringProperty(
        name="Attached Portal Name", get=get_portal_name)

    attached_room_id: bpy.props.EnumProperty(
        name="Room", items=MloArchetypeChild.get_room_items, default=-1)
    room_index: bpy.props.IntProperty(
        name="Attached Room Index", get=get_room_index)
    room_name: bpy.props.StringProperty(
        name="Attached Room Name", get=get_room_name)

    attached_entity_set_id: bpy.props.EnumProperty(
        name="EntitySet", items=MloArchetypeChild.get_entityset_items, default=-1)
    entity_set_index: bpy.props.IntProperty(
        name="Attached EntitySet Index", get=get_entityset_index)

    flags: bpy.props.PointerProperty(type=EntityFlags, name="Flags")

    linked_object: bpy.props.PointerProperty(
        type=bpy.types.Object, name="Linked Object")

    # Blender usage only
    id: bpy.props.IntProperty(name="Id")


class EntitySetProperties(bpy.types.PropertyGroup, MloArchetypeChild):
    def get_entity_set_name(self, entity_set_index: int):
        archetype = self.get_mlo_archetype()

        if archetype is None or not archetype.entity_sets:
            return ""

        if entity_set_index < len(archetype.entity_sets) and entity_set_index >= 0:
            return archetype.entity_sets[entity_set_index].name

        return archetype.entity_sets[0].name

    name: bpy.props.StringProperty(name="Name")
    entities: bpy.props.CollectionProperty(
        type=MloEntityProperties, name="EntitySet Entities")

    # Blender use obly
    id: bpy.props.IntProperty(name="Id")


def register():
    bpy.types.Scene.sollumz_add_entity_portal = bpy.props.EnumProperty(
        name="Portal", items=get_portal_items_for_selected_archetype, default=-1)
    bpy.types.Scene.sollumz_add_entity_room = bpy.props.EnumProperty(
        name="Room", items=get_room_items_for_selected_archetype, default=-1)
    bpy.types.Scene.sollumz_add_entity_entityset = bpy.props.EnumProperty(
        name="EntitySet", items=get_entityset_items_for_selected_archetype, default=-1)

    bpy.types.Scene.sollumz_add_portal_room_from = bpy.props.EnumProperty(
        name="Room From", description="Room From", items=get_room_items_for_selected_archetype, default=-1)
    bpy.types.Scene.sollumz_add_portal_room_to = bpy.props.EnumProperty(
        name="Room To", description="Room To", items=get_room_items_for_selected_archetype, default=-1)

    bpy.types.Scene.sollumz_entity_filter_type = bpy.props.EnumProperty(name="Filter By", items=(
        ("all", "All", ""),
        ("room", "Room", ""),
        ("portal", "Portal", ""),
        ("entity_set", "EntitySet", "")
    ))

    bpy.types.Scene.sollumz_entity_filter_room = bpy.props.EnumProperty(
        items=get_room_items_for_selected_archetype, default=-1, description="Room")
    bpy.types.Scene.sollumz_entity_filter_portal = bpy.props.EnumProperty(
        items=get_portal_items_for_selected_archetype, default=-1, description="Portal")
    bpy.types.Scene.sollumz_entity_filter_entity_set = bpy.props.EnumProperty(
        items=get_entityset_items_for_selected_archetype, default=-1, description="EntitySet")
    bpy.types.Scene.sollumz_entity_filter_entity_set_room = bpy.props.EnumProperty(
        items=get_room_items_for_selected_archetype, default=-1, description="Room")
    bpy.types.Scene.sollumz_do_entity_filter_entity_set_room = bpy.props.BoolProperty(
        name="Filter EntitySet Room")


def unregister():
    del bpy.types.Scene.sollumz_add_entity_portal
    del bpy.types.Scene.sollumz_add_entity_room
    del bpy.types.Scene.sollumz_add_entity_entityset
    del bpy.types.Scene.sollumz_entity_filter_type
    del bpy.types.Scene.sollumz_entity_filter_room
    del bpy.types.Scene.sollumz_entity_filter_portal
    del bpy.types.Scene.sollumz_entity_filter_entity_set
    del bpy.types.Scene.sollumz_do_entity_filter_entity_set_room
    del bpy.types.Scene.sollumz_add_portal_room_from
    del bpy.types.Scene.sollumz_add_portal_room_to
