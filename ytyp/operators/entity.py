import bpy
from typing import Optional
from mathutils import Vector
from ...sollumz_operators import SOLLUMZ_OT_base, SearchEnumHelper
from ...tools.blenderhelper import remove_number_suffix
from ..utils import get_selected_archetype, get_selected_entity
from ..properties.mlo import (
    MloEntityProperties, get_portal_items_for_selected_archetype, get_room_items_for_selected_archetype
)
from ..properties.ytyp import ArchetypeProperties


def set_entity_properties_from_filter(entity: MloEntityProperties, context: bpy.types.Context):
    scene = context.scene
    filter_type = scene.sollumz_entity_filter_type

    if filter_type == "room":
        entity.attached_room_id = scene.sollumz_entity_filter_room
    elif filter_type == "portal":
        entity.attached_portal_id = scene.sollumz_entity_filter_portal
    elif filter_type == "entity_set":
        entity.attached_entity_set_id = scene.sollumz_entity_filter_entity_set
        if scene.sollumz_do_entity_filter_entity_set_room:
            entity.attached_room_id = scene.sollumz_entity_filter_entity_set_room


class SOLLUMZ_OT_create_mlo_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add an entity to the selected mlo archetype"""
    bl_idname = "sollumz.createmloentity"
    bl_label = "Create Entity"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        entity = selected_archetype.new_entity()
        set_entity_properties_from_filter(entity, context)

        return True


class SOLLUMZ_OT_add_obj_as_entity(bpy.types.Operator):
    bl_idname = "sollumz.addobjasentity"
    bl_label = "Add Object(s) as Entity"
    bl_description = "Create Entities from selected objects (auto-sets linked object)"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None and len(context.selected_objects) > 0

    def execute(self, context: bpy.types.Context):
        selected_archetype = get_selected_archetype(context)

        for obj in context.selected_objects:
            existing_entity = self.get_entity_using_obj(
                obj, selected_archetype)

            if existing_entity is not None:
                self.report(
                    {"INFO"}, f"Object '{obj.name}' already linked to entity '{existing_entity.archetype_name}'! Skipping...")
                continue

            entity = selected_archetype.new_entity()
            entity.archetype_name = remove_number_suffix(obj.name)

            entity.linked_object = obj
            set_entity_properties_from_filter(entity, context)

        return {"FINISHED"}

    def get_entity_using_obj(self, obj: bpy.types.Object, archetype: ArchetypeProperties) -> Optional[MloEntityProperties]:
        for entity in archetype.entities:
            if entity.linked_object == obj:
                return entity

        return None


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

    attached_portal_id: bpy.props.EnumProperty(items=get_portal_items_for_selected_archetype, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_data_block(self, context):
        return get_selected_entity(context)


class SOLLUMZ_OT_search_entity_rooms(SearchEnumHelper, bpy.types.Operator):
    """Search for room"""
    bl_idname = "sollumz.search_entity_rooms"
    bl_property = "attached_room_id"

    attached_room_id: bpy.props.EnumProperty(items=get_room_items_for_selected_archetype, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_data_block(self, context):
        return get_selected_entity(context)
