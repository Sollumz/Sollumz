import bpy
from ...sollumz_helper import SOLLUMZ_OT_base
from ..utils import get_selected_archetype, get_selected_entity, validate_dynamic_enums, validate_dynamic_enum
from ...sollumz_operators import SearchEnumHelper
from ..properties.mlo import get_entityset_items_for_selected_archetype


class SOLLUMZ_OT_search_entityset(SearchEnumHelper, bpy.types.Operator):
    """Search for Entity Set"""
    bl_idname = "sollumz.search_entityset"
    bl_property = "attached_entity_set_id"

    attached_entity_set_id: bpy.props.EnumProperty(items=get_entityset_items_for_selected_archetype, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def get_data_block(self, context):
        return get_selected_archetype(context).entities.selection


class SOLLUMZ_OT_create_entityset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a Entity Set to the selected archetype"""
    bl_idname = "sollumz.createentityset"
    bl_label = "Create Entity Set"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.new_entity_set()

        return True


class SOLLUMZ_OT_delete_entityset(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete selected entity set(s)"""
    bl_idname = "sollumz.deleteentityset"
    bl_label = "Delete Entity Set"

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype is not None and selected_archetype.entity_sets

    def run(self, context):
        selected_archetype = get_selected_archetype(context)

        indices_to_remove = selected_archetype.entity_sets.selected_items_indices
        indices_to_remove.sort(reverse=True)
        new_active_index = max(indices_to_remove[-1] - 1, 0) if indices_to_remove else 0
        for index_to_remove in indices_to_remove:
            selected_archetype.entity_sets.remove(index_to_remove)
        selected_archetype.entity_sets.select(new_active_index)

        validate_dynamic_enums(selected_archetype.entities, "attached_entity_set_id", selected_archetype.entity_sets)
        validate_dynamic_enum(context.scene, "sollumz_add_entity_entityset", selected_archetype.entity_sets)
        validate_dynamic_enum(context.scene, "sollumz_entity_filter_entity_set", selected_archetype.entity_sets)

        return True
