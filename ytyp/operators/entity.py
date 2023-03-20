import bpy
from mathutils import Vector
from ...sollumz_operators import SOLLUMZ_OT_base, SearchEnumHelper
from ...tools.blenderhelper import remove_number_suffix
from ..utils import get_selected_archetype, get_selected_room, get_selected_entity, get_selected_portal
from ..properties.mlo import get_portal_items, get_room_items, get_entityset_items


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


class SOLLUMZ_OT_add_obj_as_entity(bpy.types.Operator):
    bl_idname = "sollumz.addobjasentity"
    bl_label = "Add object(s) as entity"
    bl_description = "Create Entities from selected objects (auto-sets linked object)"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None and len(context.selected_objects) > 0

    def execute(self, context: bpy.types.Context):
        selected_objects = context.selected_objects

        selected_archetype = get_selected_archetype(context)
        portal_id = context.scene.sollumz_add_entity_portal
        room_id = context.scene.sollumz_add_entity_room
        attachable_objects = list(selected_objects)

        for entity in selected_archetype.entities:
            entity_obj = entity.linked_object

            if entity_obj is None or entity_obj not in attachable_objects:
                continue

            if room_id and room_id != "-1" and entity.attached_room_id == room_id:
                self.report(
                    {"WARNING"}, f"{entity_obj.name} already attached to {entity.get_room_name()}. Skipping...")
                attachable_objects.remove(entity_obj)
            elif portal_id and portal_id != "-1" and entity.attached_portal_id == portal_id:
                self.report(
                    {"WARNING"}, f"{entity_obj.name} already attached to {entity.get_portal_name()}. Skipping...")
                attachable_objects.remove(entity_obj)
                attachable_objects.remove(entity_obj)

        for obj in attachable_objects:
            entity = selected_archetype.new_entity()
            entity.archetype_name = remove_number_suffix(obj.name)

            entity.linked_object = obj

            entity.attached_portal_id = portal_id or "-1"
            entity.attached_room_id = room_id or "-1"

        return {"FINISHED"}


class SOLLUMZ_OT_set_obj_entity_transforms(bpy.types.Operator):
    """Set the transforms of the selected object(s) to that of the Entity"""
    bl_idname = "sollumz.setobjentitytransforms"
    bl_label = "Set Object Transforms to Entity"

    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None and len(context.selected_objects) > 0

    def execute(self, context):
        entity = get_selected_entity(context)
        selected_objects = context.selected_objects

        location = entity.position
        rotation_euler = entity.rotation.to_euler()
        scale = Vector((entity.scale_xy, entity.scale_xy, entity.scale_z))

        if entity.linked_object:
            location = entity.linked_object.location
            rotation_euler = entity.linked_object.rotation_euler
            scale = entity.linked_object.scale

        for obj in selected_objects:
            obj.location = location
            obj.rotation_euler = rotation_euler
            obj.scale = scale

        return {"FINISHED"}


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
    bl_property = "attached_portal_id"

    attached_portal_id: bpy.props.EnumProperty(
        items=get_portal_items, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_data_block(self, context):
        return get_selected_entity(context)


class SOLLUMZ_OT_search_entity_rooms(SearchEnumHelper, bpy.types.Operator):
    """Search for room"""
    bl_idname = "sollumz.search_entity_rooms"
    bl_property = "attached_room_id"

    attached_room_id: bpy.props.EnumProperty(items=get_room_items, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_data_block(self, context):
        return get_selected_entity(context)

