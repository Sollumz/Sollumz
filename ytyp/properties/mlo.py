import bpy
from typing import Union
from mathutils import Vector
from ...sollumz_properties import EntityProperties
from ...tools.utils import get_list_item
from ..utils import get_selected_ytyp, get_selected_archetype
from .flags import EntityFlags, RoomFlags, PortalFlags
from .extensions import ExtensionsContainer


def get_portal_items(self, context: bpy.types.Context):
    selected_archetype = get_selected_archetype(context)

    items = [("-1", "None", "", -1)]

    if not selected_archetype:
        return items

    for portal in selected_archetype.portals:
        items.append((str(portal.id), portal.name, ""))

    return items


def get_room_items(self, context: bpy.types.Context):
    selected_archetype = get_selected_archetype(context)

    items = [("-1", "None", "", -1)]

    if not selected_archetype:
        return items

    for room in selected_archetype.rooms:
        items.append((str(room.id), room.name, ""))

    return items


class MloArchetypeChild:
    def get_mlo_archetype(self):
        selected_ytyp = get_selected_ytyp(bpy.context)

        if self.mlo_archetype_id == -1:
            selected_ytyp.update_mlo_archetype_ids()
        for archetype in selected_ytyp.archetypes:
            if archetype.id == self.mlo_archetype_id:
                return archetype

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

        for index, room in enumerate(archetype.rooms):
            if not self.room_from_id:
                continue

            if room.id == int(self.room_from_id):
                return index

        return 0

    def get_room_to_index(self):
        archetype = self.get_mlo_archetype()

        for index, room in enumerate(archetype.rooms):
            if not self.room_to_id:
                continue

            if room.id == int(self.room_to_id):
                return index

        return 0

    def get_room_name(self, room_index: int):
        archetype = self.get_mlo_archetype()

        if not archetype.rooms:
            return ""

        if room_index < len(archetype.rooms) and room_index >= 0:
            return archetype.rooms[room_index].name

        return archetype.rooms[0].name

    def get_room_from_name(self):
        return self.get_room_name(self.room_from_index)

    def get_room_to_name(self):
        return self.get_room_name(self.room_to_index)

    def get_name(self):
        return f"{self.room_from_name} to {self.room_to_name}"

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
        name="Room From", items=get_room_items, default=-1)
    room_from_index: bpy.props.IntProperty(
        name="Room From Index", get=get_room_from_index)
    room_from_name: bpy.props.StringProperty(
        name="Room From", get=get_room_from_name)

    room_to_id: bpy.props.EnumProperty(
        name="Room To", items=get_room_items, default=-1)
    room_to_index: bpy.props.IntProperty(
        name="Room To Index", get=get_room_to_index)
    room_to_name: bpy.props.StringProperty(
        name="Room To", get=get_room_to_name)

    flags: bpy.props.PointerProperty(type=PortalFlags, name="Flags")
    mirror_priority: bpy.props.IntProperty(name="Mirror Priority")
    opacity: bpy.props.IntProperty(name="Opacity")
    audio_occlusion: bpy.props.StringProperty(
        name="Audio Occlusion", update=update_audio_occlusion, default="0")

    # Blender use only
    name: bpy.props.StringProperty(name="Name", get=get_name)
    id: bpy.props.IntProperty(name="Id")


class TimecycleModifierProperties(bpy.types.PropertyGroup, MloArchetypeChild):
    name: bpy.props.StringProperty(name="Name")
    sphere: bpy.props.FloatVectorProperty(
        name="Sphere", subtype="QUATERNION", size=4)
    percentage: bpy.props.IntProperty(name="Percentage")
    range: bpy.props.FloatProperty(name="Range")
    start_hour: bpy.props.IntProperty(name="Start Hour")
    end_hour: bpy.props.IntProperty(name="End Hour")


class MloEntityProperties(bpy.types.PropertyGroup, EntityProperties, MloArchetypeChild, ExtensionsContainer):
    def get_portal_index(self):
        selected_archetype = self.get_mlo_archetype()
        for index, portal in enumerate(selected_archetype.portals):
            if portal.id == int(self.attached_portal_id):
                return index
        return -1

    def get_portal_name(self):
        selected_archetype = self.get_mlo_archetype()
        portal = get_list_item(selected_archetype.portals,
                               self.portal_index)

        if portal:
            return portal.name
        return ""

    def get_room_index(self):
        selected_archetype = self.get_mlo_archetype()
        for index, room in enumerate(selected_archetype.rooms):
            if room.id == int(self.attached_room_id):
                return index
        return -1

    def get_room_name(self):
        selected_archetype = self.get_mlo_archetype()
        room = get_list_item(selected_archetype.rooms,
                             self.room_index)
        if room:
            return room.name
        return ""

    # Transforms unused if no linked object
    position: bpy.props.FloatVectorProperty(name="Position")
    rotation: bpy.props.FloatVectorProperty(
        name="Rotation", subtype="QUATERNION", size=4, default=(1, 0, 0, 0))
    scale_xy: bpy.props.FloatProperty(name="Scale XY", default=1)
    scale_z: bpy.props.FloatProperty(name="Scale Z", default=1)

    attached_portal_id: bpy.props.EnumProperty(
        name="Portal", items=get_portal_items, default=-1)
    portal_index: bpy.props.IntProperty(
        name="Attached Portal Index", get=get_portal_index)
    portal_name: bpy.props.StringProperty(
        name="Attached Portal Name", get=get_portal_name)

    attached_room_id: bpy.props.EnumProperty(
        name="Room", items=get_room_items, default=-1)
    room_index: bpy.props.IntProperty(
        name="Attached Room Index", get=get_room_index)
    room_name: bpy.props.StringProperty(
        name="Attached Room Name", get=get_room_name)

    flags: bpy.props.PointerProperty(type=EntityFlags, name="Flags")

    linked_object: bpy.props.PointerProperty(
        type=bpy.types.Object, name="Linked Object")


def register():
    bpy.types.Scene.sollumz_add_entity_portal = bpy.props.EnumProperty(
        name="Portal", items=get_portal_items, default=-1)
    bpy.types.Scene.sollumz_add_entity_room = bpy.props.EnumProperty(
        name="Room", items=get_room_items, default=-1)


def unregister():
    del bpy.types.Scene.sollumz_add_entity_portal
    del bpy.types.Scene.sollumz_add_entity_room
