import bpy
from mathutils import Vector
from ...tools.blenderhelper import remove_number_suffix
from ...sollumz_helper import SOLLUMZ_OT_base
from ..utils import get_selected_archetype, get_selected_entity, get_selected_entity_set, get_selected_entity_set_entity, get_selected_entity_set_id, get_selected_ytyp
from ...sollumz_operators import SearchEnumHelper
from ..properties.mlo import get_room_items


class SOLLUMZ_OT_search_entityset_rooms(SearchEnumHelper, bpy.types.Operator):
    """Search for room"""
    bl_idname = "sollumz.search_entitysets_rooms"
    bl_property = "attached_entity_set_room_id"

    attached_entity_set_room_id: bpy.props.EnumProperty(
        items=get_room_items, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_data_block(self, context):
        return get_selected_entity(context)


class SOLLUMZ_OT_add_obj_as_entity_set_entity(bpy.types.Operator):
    bl_idname = "sollumz.addobjas_entity_set_entity"
    bl_label = "Add object(s) as EntitySet entity"
    bl_description = "Create Entities for EntitySet from selected objects (auto-sets linked object)"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None and len(context.selected_objects) > 0

    def execute(self, context: bpy.types.Context):
        selected_objects = context.selected_objects

        selected_archetype = get_selected_archetype(context)
        selected_entity_set = get_selected_entity_set(context)
        entity_set_id = get_selected_entity_set_id(context)
        entity_set_room_id = context.scene.sollumz_add_entity_entityset_room
        attachable_objects = list(selected_objects)

        for entity_set in selected_archetype.entity_sets:
            for entity in entity_set.entities:
                entity_obj = entity.linked_object

                if entity_obj is None or entity_obj not in attachable_objects:
                    continue

                if entity_set_id and entity_set_id != "-1" and entity.attached_entity_set_id != '-1':
                    self.report(
                        {"WARNING"}, f"{entity_obj.name} already attached to {entity_set.name} EntitySet. Skipping...")
                    attachable_objects.remove(entity_obj)
                elif entity_set_room_id and entity_set_room_id != "-1" and entity.attached_entity_set_room_id != '-1':
                    self.report(
                        {"WARNING"}, f"{entity_obj.name} already attached to {entity_set.name} EntitySet. Skipping...")
                    attachable_objects.remove(entity_obj)

        for obj in attachable_objects:
            entity = selected_entity_set.new_entity_set_entity()
            entity.archetype_name = remove_number_suffix(obj.name)

            entity.linked_object = obj

            entity.attached_entity_set_id = entity_set_id or "-1"
            entity.attached_entity_set_room_id = entity_set_room_id or "-1"

        return {"FINISHED"}


class SOLLUMZ_OT_set_obj_entity_set_entity_transforms(bpy.types.Operator):
    """Set the transforms of the selected object(s) to that of the EntitySet's Entity"""
    bl_idname = "sollumz.setobj_entity_set_entitytransforms"
    bl_label = "Set Object Transforms to EntitySet Entity"

    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return get_selected_entity_set_entity(context) is not None and len(context.selected_objects) > 0

    def execute(self, context):
        entity = get_selected_entity_set_entity(context)
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


class SOLLUMZ_OT_create_entityset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a Entity Set to the selected archetype"""
    bl_idname = "sollumz.createentityset"
    bl_label = "Create Entity Set"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        item = selected_archetype.new_entity_set()
        item.name = f"EntitySet_{len(selected_archetype.entity_sets)}"
        return True


class SOLLUMZ_OT_delete_entityset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete Entity Set from selected archetype"""
    bl_idname = "sollumz.deleteentityset"
    bl_label = "Delete Entity Set"

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype is not None and selected_archetype.entity_sets

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.entity_sets.remove(
            selected_archetype.entity_set_index)
        selected_archetype.entity_set_index = max(
            selected_archetype.entity_set_index - 1, 0)
        return True


class SOLLUMZ_OT_create_entityset_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add an entity to the selected mlo archetype"""
    bl_idname = "sollumz.create_entityset_entity"
    bl_label = "Create EntitySet Entity"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_entityset = get_selected_entity_set(context)
        selected_entityset.new_entity_set_entity()
        return True


class SOLLUMZ_OT_delete_entity_set_entity(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete an entity from the selected mlo archetype"""
    bl_idname = "sollumz.delete_entityset_entity"
    bl_label = "Delete EntitySet Entity"

    @classmethod
    def poll(cls, context):
        return get_selected_entity_set(context) is not None

    def run(self, context):
        selected_entityset = get_selected_entity_set(context)
        selected_entityset.entities.remove(
            selected_entityset.entity_set_entity_index)
        selected_entityset.entity_set_entity_index = max(
            selected_entityset.entity_set_entity_index - 1, 0)
        return True
