import bpy
from ...sollumz_helper import SOLLUMZ_OT_base
from ..utils import get_selected_ytyp, get_selected_archetype, get_selected_entity, get_selected_entity_set, validate_dynamic_enums, validate_dynamic_enum
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


class SOLLUMZ_OT_entityset_toggle_visibility(bpy.types.Operator):
    bl_idname = "sollumz.entityset_toggle_visibility"
    bl_label = "Toggle Entity Set"

    ytyp_index: bpy.props.IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: bpy.props.IntProperty(name="Archetype Index", min=-1, default=-1)
    index: bpy.props.IntProperty(name="Entity Set Index")

    def _get_archetype(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        )

    def _get_entity_set(self, context):
        return self._get_archetype(context).entity_sets[self.index]

    def execute(self, context):
        entity_set = self._get_entity_set(context)
        entity_set_id = str(entity_set.id)
        entities = self._get_archetype(context).entities

        visibility = entity_set.visible
        entity_set.visible = not visibility
        for entity in entities:
            if not entity.linked_object or entity.attached_entity_set_id != entity_set_id:
                continue

            obj = entity.linked_object
            obj.hide_set(visibility)

        return {"FINISHED"}
