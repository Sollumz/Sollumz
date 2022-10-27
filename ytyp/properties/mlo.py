import bpy
from typing import Union
from mathutils import Vector
from ...sollumz_properties import EntityProperties
from ...tools.utils import get_list_item
from ..utils import get_selected_ytyp
from .flags import EntityFlags, RoomFlags, PortalFlags
from .extensions import ExtensionsContainer


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
        name="Timecycle", default="int_GasStation")
    secondary_timecycle: bpy.props.StringProperty(
        name="Secondary Timecycle")
    flags: bpy.props.PointerProperty(type=RoomFlags, name="Flags")
    floor_id: bpy.props.IntProperty(name="Floor ID")
    exterior_visibility_depth: bpy.props.IntProperty(
        name="Exterior Visibility Depth", default=-1)

    # Blender usage only
    id: bpy.props.IntProperty(name="Id")


class PortalProperties(bpy.types.PropertyGroup, MloArchetypeChild):
    def get_room_index(self, room_from):
        selected_ytyp = bpy.context.scene.ytyps[bpy.context.scene.ytyp_index]
        selected_archetype = selected_ytyp.archetypes[selected_ytyp.archetype_index]
        for index, room in enumerate(selected_archetype.rooms):
            if room_from:
                if room.id == self.room_from_id:
                    return index
            else:
                if room.id == self.room_to_id:
                    return index
        return 0

    def get_room_from_index(self):
        return self.get_room_index(True)

    def get_room_to_index(self):
        return self.get_room_index(False)

    def get_room_name(self, room_from):
        selected_ytyp = bpy.context.scene.ytyps[bpy.context.scene.ytyp_index]
        selected_archetype = selected_ytyp.archetypes[selected_ytyp.archetype_index]
        if len(selected_archetype.rooms) < 1:
            return ""

        index = self.room_from_index if room_from else self.room_to_index

        if index < len(selected_archetype.rooms) and index >= 0:
            return selected_archetype.rooms[index].name
        else:
            return selected_archetype.rooms[0].name

    def get_room_from_name(self):
        return self.get_room_name(True)

    def get_room_to_name(self):
        return self.get_room_name(False)

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
    room_from_id: bpy.props.IntProperty(name="Room From Id")
    room_from_index: bpy.props.IntProperty(
        name="Room From Index", get=get_room_from_index)
    room_from_name: bpy.props.StringProperty(
        name="Room From", get=get_room_from_name)
    room_to_id: bpy.props.IntProperty(name="Room To Id")
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
    def update_linked_object(self, context):
        linked_obj = self.linked_object
        if linked_obj:
            linked_obj.location = self.position
            linked_obj.rotation_euler = self.rotation.to_euler()
            linked_obj.scale = Vector(
                (self.scale_xy, self.scale_xy, self.scale_z))

    def get_portal_index(self):
        selected_archetype = self.get_mlo_archetype()
        for index, portal in enumerate(selected_archetype.portals):
            if portal.id == self.attached_portal_id:
                return index
        return -1

    def get_portal_name(self):
        selected_archetype = self.get_mlo_archetype()
        portal = get_list_item(selected_archetype.portals,
                               self.attached_portal_index)
        if portal:
            return portal.name
        return ""

    def get_room_index(self):
        selected_archetype = self.get_mlo_archetype()
        for index, room in enumerate(selected_archetype.rooms):
            if room.id == self.attached_room_id:
                return index
        return -1

    def get_room_name(self):
        selected_archetype = self.get_mlo_archetype()
        room = get_list_item(selected_archetype.rooms,
                             self.attached_room_index)
        if room:
            return room.name
        return ""

    # Transforms unused if no linked object
    position: bpy.props.FloatVectorProperty(name="Position")
    rotation: bpy.props.FloatVectorProperty(
        name="Rotation", subtype="QUATERNION", size=4, default=(1, 0, 0, 0))
    scale_xy: bpy.props.FloatProperty(name="Scale XY", default=1)
    scale_z: bpy.props.FloatProperty(name="Scale Z", default=1)

    attached_portal_index: bpy.props.IntProperty(
        name="Attached Portal Index", get=get_portal_index)
    attached_portal_id: bpy.props.IntProperty(
        name="Attached Portal Id", default=-1)
    attached_portal_name: bpy.props.StringProperty(
        name="Attached Portal Name", get=get_portal_name)

    attached_room_index: bpy.props.IntProperty(
        name="Attached Room Index", get=get_room_index)
    attached_room_id: bpy.props.IntProperty(
        name="Attached Room Id", default=-1)
    attached_room_name: bpy.props.StringProperty(
        name="Attached Room Name", get=get_room_name)
    flags: bpy.props.PointerProperty(type=EntityFlags, name="Flags")

    linked_object: bpy.props.PointerProperty(
        type=bpy.types.Object, name="Linked Object", update=update_linked_object)
