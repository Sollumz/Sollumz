import bpy
from bpy.props import PointerProperty

from ..sollumz_properties import items_from_enums, ArchetypeType, AssetType, EntityProperties, FlagPropertyGroup
from mathutils import Vector
from ..tools.utils import get_list_item


class RoomFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 10

    flag1: bpy.props.BoolProperty(
        name="Unknown 1", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Disables wanted level", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Disable exterior shadows", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Reduces vehicle population", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Reduces ped population", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Disable limbo portals", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Unknown 10", update=FlagPropertyGroup.update_flag)


class RoomProperties(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    bb_min: bpy.props.FloatVectorProperty(name="Bounds Min", subtype="XYZ")
    bb_max: bpy.props.FloatVectorProperty(name="Bounds Max", subtype="XYZ")
    blend: bpy.props.IntProperty(name="Blend", default=1)
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


class PortalFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    size = 14

    flag1: bpy.props.BoolProperty(
        name="Disables exterior rendering", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Disables interior rendering", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Mirror", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Extra bloom", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Use exterior LOD", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Hide when door closed", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Mirror exterior portals", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Unknown 10", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Mirror limbo entities", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Unknown 12", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Unknown 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Disable farclipping", update=FlagPropertyGroup.update_flag)


class PortalProperties(bpy.types.PropertyGroup):
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
    audio_occlusion: bpy.props.IntProperty(name="Audio Occlusion")

    # Blender use only
    name: bpy.props.StringProperty(name="Name", get=get_name)
    id: bpy.props.IntProperty(name="Id")


class TimecycleModifierProperties(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    sphere: bpy.props.FloatVectorProperty(
        name="Sphere", subtype="QUATERNION", size=4)
    percentage: bpy.props.IntProperty(name="Percentage")
    range: bpy.props.FloatProperty(name="Range")
    start_hour: bpy.props.IntProperty(name="Start Hour")
    end_hour: bpy.props.IntProperty(name="End Hour")


class EntityFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="Allow full rotation", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Unknown 2", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Disable embedded collisions", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Static entity", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Object isn't dark at night", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Unknown 9", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Disable embedded light sources", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Unknown 11", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Unknown 12", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Unknown 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Unknown 14", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Unknown 15", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="Unknown 16", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Unknown 17", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Unknown 18", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(name="Disable archetype extensions",
                                   update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Unknown 20", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Unknown 21", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Unknown 22", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Disable shadow for entity", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Disable entity, shadow casted", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Object will not cast reflections", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Interior proxy", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Unknown 27", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Reflection proxy", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Unknown 29", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Mirror proxy", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Unknown 31", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Unknown 32", update=FlagPropertyGroup.update_flag)


class UnlinkedEntityProperties(bpy.types.PropertyGroup, EntityProperties):
    def update_linked_object(self, context):
        linked_obj = self.linked_object
        if linked_obj:
            linked_obj.location = self.position
            linked_obj.rotation_euler = self.rotation.to_euler()
            linked_obj.scale = Vector(
                (self.scale_xy, self.scale_xy, self.scale_z))

    def get_portal_index(self):
        selected_archetype = get_selected_archetype(bpy.context)
        for index, portal in enumerate(selected_archetype.portals):
            if portal.id == self.attached_portal_id:
                return index
        return -1

    def get_portal_name(self):
        selected_archetype = get_selected_archetype(bpy.context)
        portal = get_list_item(selected_archetype.portals,
                               self.attached_portal_index)
        if portal:
            return portal.name
        return ""

    def get_room_index(self):
        selected_archetype = get_selected_archetype(bpy.context)
        for index, room in enumerate(selected_archetype.rooms):
            if room.id == self.attached_room_id:
                return index
        return -1

    def get_room_name(self):
        selected_archetype = get_selected_archetype(bpy.context)
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


class ArchetypeFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="Unknown 1", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Unknown 2", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Unknown 3", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Static", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Unknown 7", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Instance", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Unknown 9", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Bone anims (YCD)", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Unknown 11", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Unknown 12", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Unknown 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Object won't cast shadow", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Unknown 15", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="Unknown 16", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Double-sided rendering", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Dynamic", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(
        name="Unknown 19", update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Unknown 20", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Unknown 21", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Unknown 22", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Unknown 23", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Unknown 24", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Unknown 25", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Unknown 26", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Enables special attribute", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Unknown 28", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Disable red vertex channel", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Disable green vertex channel", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Disable blue vertex channel", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Disable alpha vertex channel", update=FlagPropertyGroup.update_flag)


class TimeFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    hour1: bpy.props.BoolProperty(
        name="12:00 AM - 1:00 AM", update=FlagPropertyGroup.update_flag)
    hour2: bpy.props.BoolProperty(
        name="1:00 AM - 2:00 AM", update=FlagPropertyGroup.update_flag)
    hour3: bpy.props.BoolProperty(
        name="2:00 AM - 3:00 AM", update=FlagPropertyGroup.update_flag)
    hour4: bpy.props.BoolProperty(
        name="3:00 AM - 4:00 AM", update=FlagPropertyGroup.update_flag)
    hour5: bpy.props.BoolProperty(
        name="4:00 AM - 5:00 AM", update=FlagPropertyGroup.update_flag)
    hour6: bpy.props.BoolProperty(
        name="5:00 AM - 6:00 AM", update=FlagPropertyGroup.update_flag)
    hour7: bpy.props.BoolProperty(
        name="6:00 AM - 7:00 AM", update=FlagPropertyGroup.update_flag)
    hour8: bpy.props.BoolProperty(
        name="7:00 AM - 8:00 AM", update=FlagPropertyGroup.update_flag)
    hour9: bpy.props.BoolProperty(
        name="8:00 AM - 9:00 AM", update=FlagPropertyGroup.update_flag)
    hour10: bpy.props.BoolProperty(
        name="9:00 AM - 10:00 AM", update=FlagPropertyGroup.update_flag)
    hour11: bpy.props.BoolProperty(
        name="10:00 AM - 11:00 AM", update=FlagPropertyGroup.update_flag)
    hour12: bpy.props.BoolProperty(
        name="11:00 AM - 12:00 PM", update=FlagPropertyGroup.update_flag)
    hour13: bpy.props.BoolProperty(
        name="12:00 PM - 1:00 PM", update=FlagPropertyGroup.update_flag)
    hour14: bpy.props.BoolProperty(
        name="1:00 PM - 2:00 PM", update=FlagPropertyGroup.update_flag)
    hour15: bpy.props.BoolProperty(
        name="2:00 PM - 3:00 PM", update=FlagPropertyGroup.update_flag)
    hour16: bpy.props.BoolProperty(
        name="3:00 PM - 4:00 PM", update=FlagPropertyGroup.update_flag)
    hour17: bpy.props.BoolProperty(
        name="4:00 PM - 5:00 PM", update=FlagPropertyGroup.update_flag)
    hour18: bpy.props.BoolProperty(
        name="5:00 PM - 6:00 PM", update=FlagPropertyGroup.update_flag)
    hour19: bpy.props.BoolProperty(
        name="6:00 PM - 7:00 PM", update=FlagPropertyGroup.update_flag)
    hour20: bpy.props.BoolProperty(
        name="7:00 PM - 8:00 PM", update=FlagPropertyGroup.update_flag)
    hour21: bpy.props.BoolProperty(
        name="8:00 PM - 9:00 PM", update=FlagPropertyGroup.update_flag)
    hour22: bpy.props.BoolProperty(
        name="9:00 PM - 10:00 PM", update=FlagPropertyGroup.update_flag)
    hour23: bpy.props.BoolProperty(
        name="10:00 PM - 11:00 PM", update=FlagPropertyGroup.update_flag)
    hour24: bpy.props.BoolProperty(
        name="11:00 PM - 12:00 AM", update=FlagPropertyGroup.update_flag)
    unk1: bpy.props.BoolProperty(
        name="Unknown 1", update=FlagPropertyGroup.update_flag)
    unk2: bpy.props.BoolProperty(
        name="Unknown 2", update=FlagPropertyGroup.update_flag)
    unk3: bpy.props.BoolProperty(
        name="Unknown 3", update=FlagPropertyGroup.update_flag)
    unk4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    unk5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    unk6: bpy.props.BoolProperty(
        name="Unknown 6", update=FlagPropertyGroup.update_flag)
    unk7: bpy.props.BoolProperty(
        name="Unknown 7", update=FlagPropertyGroup.update_flag)
    unk8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)


class UnknownFlags(FlagPropertyGroup, bpy.types.PropertyGroup):
    flag1: bpy.props.BoolProperty(
        name="Unknown 1", update=FlagPropertyGroup.update_flag)
    flag2: bpy.props.BoolProperty(
        name="Unknown 2", update=FlagPropertyGroup.update_flag)
    flag3: bpy.props.BoolProperty(
        name="Unknown 3", update=FlagPropertyGroup.update_flag)
    flag4: bpy.props.BoolProperty(
        name="Unknown 4", update=FlagPropertyGroup.update_flag)
    flag5: bpy.props.BoolProperty(
        name="Unknown 5", update=FlagPropertyGroup.update_flag)
    flag6: bpy.props.BoolProperty(
        name="Unknown 6", update=FlagPropertyGroup.update_flag)
    flag7: bpy.props.BoolProperty(
        name="Unknown 7", update=FlagPropertyGroup.update_flag)
    flag8: bpy.props.BoolProperty(
        name="Unknown 8", update=FlagPropertyGroup.update_flag)
    flag9: bpy.props.BoolProperty(
        name="Unknown 9", update=FlagPropertyGroup.update_flag)
    flag10: bpy.props.BoolProperty(
        name="Unknown 10", update=FlagPropertyGroup.update_flag)
    flag11: bpy.props.BoolProperty(
        name="Unknown 11", update=FlagPropertyGroup.update_flag)
    flag12: bpy.props.BoolProperty(
        name="Unknown 12", update=FlagPropertyGroup.update_flag)
    flag13: bpy.props.BoolProperty(
        name="Unknown 13", update=FlagPropertyGroup.update_flag)
    flag14: bpy.props.BoolProperty(
        name="Unknown 14", update=FlagPropertyGroup.update_flag)
    flag15: bpy.props.BoolProperty(
        name="Unknown 15", update=FlagPropertyGroup.update_flag)
    flag16: bpy.props.BoolProperty(
        name="Unknown 16", update=FlagPropertyGroup.update_flag)
    flag17: bpy.props.BoolProperty(
        name="Unknown 17", update=FlagPropertyGroup.update_flag)
    flag18: bpy.props.BoolProperty(
        name="Unknown 18", update=FlagPropertyGroup.update_flag)
    flag19: bpy.props.BoolProperty(
        name="Unknown 19", update=FlagPropertyGroup.update_flag)
    flag20: bpy.props.BoolProperty(
        name="Unknown 20", update=FlagPropertyGroup.update_flag)
    flag21: bpy.props.BoolProperty(
        name="Unknown 21", update=FlagPropertyGroup.update_flag)
    flag22: bpy.props.BoolProperty(
        name="Unknown 22", update=FlagPropertyGroup.update_flag)
    flag23: bpy.props.BoolProperty(
        name="Unknown 23", update=FlagPropertyGroup.update_flag)
    flag24: bpy.props.BoolProperty(
        name="Unknown 24", update=FlagPropertyGroup.update_flag)
    flag25: bpy.props.BoolProperty(
        name="Unknown 25", update=FlagPropertyGroup.update_flag)
    flag26: bpy.props.BoolProperty(
        name="Unknown 26", update=FlagPropertyGroup.update_flag)
    flag27: bpy.props.BoolProperty(
        name="Unknown 27", update=FlagPropertyGroup.update_flag)
    flag28: bpy.props.BoolProperty(
        name="Unknown 28", update=FlagPropertyGroup.update_flag)
    flag29: bpy.props.BoolProperty(
        name="Unknown 29", update=FlagPropertyGroup.update_flag)
    flag30: bpy.props.BoolProperty(
        name="Unknown 30", update=FlagPropertyGroup.update_flag)
    flag31: bpy.props.BoolProperty(
        name="Unknown 31", update=FlagPropertyGroup.update_flag)
    flag32: bpy.props.BoolProperty(
        name="Unknown 32", update=FlagPropertyGroup.update_flag)


class ArchetypeProperties(bpy.types.PropertyGroup):
    def update_asset(self, context):
        if self.asset:
            self.asset_name = self.asset.name
        else:
            self.asset_name = ""

    def set_asset_name(self, value):
        self["asset_name"] = value

    def new_portal(self):
        item = self.portals.add()
        self.portal_index = len(self.portals) - 1
        item.id = self.last_portal_id + 1
        self.last_portal_id = item.id
        return item

    def new_room(self):
        item = self.rooms.add()
        self.room_index = len(self.rooms) - 1
        item.name = f"Room.{self.room_index}"
        item.id = self.last_room_id + 1
        self.last_room_id = item.id
        return item

    bb_min: bpy.props.FloatVectorProperty(name="Bound Min")
    bb_max: bpy.props.FloatVectorProperty(name="Bound Max")
    bs_center: bpy.props.FloatVectorProperty(name="Bound Center")
    bs_radius: bpy.props.FloatProperty(name="Bound Radius")
    type: bpy.props.EnumProperty(
        items=items_from_enums(ArchetypeType), name="Type")
    lod_dist: bpy.props.FloatProperty(name="Lod Distance", default=100)
    flags: bpy.props.PointerProperty(
        type=ArchetypeFlags, name="Flags")
    special_attribute: bpy.props.IntProperty(name="Special Attribute")
    hd_texture_dist: bpy.props.FloatProperty(
        name="HD Texture Distance", default=100)
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
    time_flags: bpy.props.PointerProperty(type=TimeFlags, name="Time Flags")
    # Mlo archetype
    mlo_flags: bpy.props.PointerProperty(type=UnknownFlags, name="MLO Flags")
    rooms: bpy.props.CollectionProperty(type=RoomProperties, name="Rooms")
    portals: bpy.props.CollectionProperty(
        type=PortalProperties, name="Portals")
    entities: bpy.props.CollectionProperty(
        type=UnlinkedEntityProperties, name="Entities")
    timecycle_modifiers: bpy.props.CollectionProperty(
        type=TimecycleModifierProperties, name="Timecycle Modifiers")
    # Selected room index
    room_index: bpy.props.IntProperty(name="Room Index")
    # Selected portal index
    portal_index: bpy.props.IntProperty(name="Portal Index")
    # Unique portal id
    last_portal_id: bpy.props.IntProperty(name="")
    # Selected entity index
    entity_index: bpy.props.IntProperty(name="Entity Index")
    # Unique room id
    last_room_id: bpy.props.IntProperty(name="")
    # Selected timecycle modifier index
    tcm_index: bpy.props.IntProperty(
        name="Timecycle Modifier Index")

    @property
    def selected_room(self):
        return get_list_item(self.rooms, self.room_index)

    @property
    def selected_portal(self):
        return get_list_item(self.portals, self.portal_index)

    @property
    def selected_entity(self):
        return get_list_item(self.entities, self.entity_index)

    @property
    def selected_tcm(self):
        return get_list_item(self.timecycle_modifiers, self.tcm_index)


class CMapTypesProperties(bpy.types.PropertyGroup):
    name: bpy.props.StringProperty(name="Name")
    # extensions
    archetypes: bpy.props.CollectionProperty(
        type=ArchetypeProperties, name="Archetypes")
    # Selected archetype index
    archetype_index: bpy.props.IntProperty(
        name="Archetype Index")

    @property
    def selected_archetype(self):
        return get_list_item(self.archetypes, self.archetype_index)


def get_selected_ytyp(context):
    scene = context.scene
    return get_list_item(scene.ytyps, scene.ytyp_index)


def get_selected_archetype(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        return ytyp.selected_archetype


def get_selected_room(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_room


def get_selected_portal(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_portal


def get_selected_entity(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_entity


def get_selected_tcm(context):
    ytyp = get_selected_ytyp(context)
    if ytyp:
        archetype = ytyp.selected_archetype
        if archetype:
            return archetype.selected_tcm


def register():
    bpy.types.Scene.ytyps = bpy.props.CollectionProperty(
        type=CMapTypesProperties, name="YTYPs")
    bpy.types.Scene.ytyp_index = bpy.props.IntProperty(name="YTYP Index")
    bpy.types.Scene.show_room_gizmo = bpy.props.BoolProperty(
        name="Show Room Gizmo")
    bpy.types.Scene.show_portal_gizmo = bpy.props.BoolProperty(
        name="Show Portal Gizmo")

    bpy.types.Scene.create_archetype_type = bpy.props.EnumProperty(
        items=items_from_enums(ArchetypeType), name="Type")


def unregister():
    del bpy.types.Scene.ytyps
    del bpy.types.Scene.ytyp_index
    del bpy.types.Scene.show_room_gizmo
    del bpy.types.Scene.show_portal_gizmo
    del bpy.types.Scene.create_archetype_type
