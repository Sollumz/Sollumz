import bpy
from ...sollumz_operators import SOLLUMZ_OT_base, SearchEnumHelper
from ..utils import get_selected_archetype, get_selected_room, get_selected_entity, get_selected_portal
from ..properties.mlo import get_portal_items, get_room_items


class SOLLUMZ_OT_create_mlo_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add an entity to the selected mlo archetype"""
    bl_idname = "sollumz.createmloentity"
    bl_label = "Create Entity"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.new_entity()
        return True


class SOLLUMZ_OT_add_obj_as_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add an object as an entity to the selected mlo archetype"""
    bl_idname = "sollumz.addobjasmloentity"
    bl_label = "Add Selected Object(s) as Entity to Selected Room"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_objects = context.selected_objects
        selected_archetype = get_selected_archetype(context)
        if len(selected_objects) < 1:
            self.warning("No objects selected")
            return False
        if len(selected_archetype.rooms) < 1:
            self.warning("There're no rooms to attach entities to.")
            return False

        selected_room = get_selected_room(context)

        archetype_entities = selected_archetype.entities
        attachable_objects = selected_objects

        for ent in archetype_entities:
            if ent.linked_object in attachable_objects and str(ent.room_id) == selected_room.id:
                self.warning(
                    "One or more of the selected objects are already attached to the selected room.")
                # remove the entity from attachable objects list
                attachable_objects.remove(ent.linked_object)

        if len(attachable_objects) < 1:
            self.warning(
                "Nothing to attach, make sure your selected objects don't exist in the selected room.")
            return False

        for obj in attachable_objects:
            item = selected_archetype.new_entity()
            # Set entity transforms before linking object so the original object's transforms won't be reset
            item.position = obj.location
            item.rotation = obj.rotation_euler.to_quaternion()
            item.room_id = str(selected_room.id)
            if obj.scale.x != obj.scale.y:
                self.warning(
                    "Failed to add entity. The X and Y scale of the entity must be equal.")
                selected_archetype.entities.remove(
                    len(selected_archetype.entities) - 1)
                return False
            item.scale_xy = obj.scale.x
            item.scale_z = obj.scale.z
            item.linked_object = obj
            name = obj.name
            # Remove number suffix if present
            if name[-4] == ".":
                name = name[0:-4]
            item.archetype_name = name
        return True


class SOLLUMZ_OT_add_obj_as_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Set entity attached portal"""
    bl_idname = "sollumz.addobjasportalentity"
    bl_label = "Add Selected Object(s) as Entity to Selected Portal"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_objects = context.selected_objects
        selected_archetype = get_selected_archetype(context)
        if len(selected_objects) < 1:
            self.warning("No objects selected")
            return False
        if len(selected_archetype.portals) < 1:
            self.warning("There're no portals to attach entities to.")
            return False

        selected_portal = get_selected_portal(context)

        archetype_entities = selected_archetype.entities
        attachable_objects = selected_objects

        for ent in archetype_entities:
            if ent.linked_object in attachable_objects and ent.portal_id == str(selected_portal.id):
                self.warning(
                    "One or more of the selected objects are already attached to the selected portal.")
                # remove the entity from attachable objects list
                attachable_objects.remove(ent.linked_object)

        if len(attachable_objects) < 1:
            self.warning(
                "Nothing to attach, make sure your selected objects don't exist in the selected portal.")
            return False

        for obj in attachable_objects:
            item = selected_archetype.new_entity()
            # Set entity transforms before linking object so the original object's transforms won't be reset
            item.position = obj.location
            item.rotation = obj.rotation_euler.to_quaternion()
            item.portal_id = str(selected_portal.id)
            if obj.scale.x != obj.scale.y:
                self.warning(
                    "Failed to add entity. The X and Y scale of the entity must be equal.")
                selected_archetype.entities.remove(
                    len(selected_archetype.entities) - 1)
                return False
            item.scale_xy = obj.scale.x
            item.scale_z = obj.scale.z
            item.linked_object = obj
            name = obj.name
            # Remove number suffix if present
            if name[-4] == ".":
                name = name[0:-4]
            item.archetype_name = name
        return True


class SOLLUMZ_OT_delete_mlo_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete an entity from the selected mlo archetype"""
    bl_idname = "sollumz.deletemloentity"
    bl_label = "Delete Entity"

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.entities.remove(
            selected_archetype.entity_index)
        selected_archetype.entity_index = max(
            selected_archetype.entity_index - 1, 0)
        return True


class SOLLUMZ_OT_search_entity_portals(SearchEnumHelper, bpy.types.Operator):
    """Search for portal"""
    bl_idname = "sollumz.search_entity_portals"
    bl_property = "portal_id"

    portal_id: bpy.props.EnumProperty(items=get_portal_items)

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_data_block(self, context):
        return get_selected_entity(context)


class SOLLUMZ_OT_search_entity_rooms(SearchEnumHelper, bpy.types.Operator):
    """Search for room"""
    bl_idname = "sollumz.search_entity_rooms"
    bl_property = "room_id"

    room_id: bpy.props.EnumProperty(items=get_room_items)

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_data_block(self, context):
        return get_selected_entity(context)
