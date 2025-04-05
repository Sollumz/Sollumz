import bpy
from ...sollumz_operators import SOLLUMZ_OT_base
from ...sollumz_properties import ArchetypeType
from ...tools.meshhelper import get_extents, get_min_vector_list, get_max_vector_list
from ...tools.blenderhelper import get_selected_vertices
from ..utils import get_selected_archetype, get_selected_room, validate_dynamic_enums, validate_dynamic_enum


class SOLLUMZ_OT_create_room(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a room to the selected archetype"""
    bl_idname = "sollumz.createroom"
    bl_label = "Create Room"

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype and selected_archetype.type == ArchetypeType.MLO

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.new_room()

        return True


class SOLLUMZ_OT_create_limbo_room(SOLLUMZ_OT_base, bpy.types.Operator):
    """Automatically create a limbo room for the selected archetype (requires linked object to be specified)"""
    bl_idname = "sollumz.createlimboroom"
    bl_label = "Create Limbo Room"

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype and selected_archetype.type == ArchetypeType.MLO and selected_archetype.asset is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        room = selected_archetype.new_room()
        bbmin, bbmax = get_extents(selected_archetype.asset)
        room.bb_min = bbmin
        room.bb_max = bbmax
        room.name = "limbo"
        room.timecycle = ""

        return True


class SOLLUMZ_OT_set_bounds_from_selection(SOLLUMZ_OT_base, bpy.types.Operator):
    """Set room bounds from selection (must be in edit mode)"""
    bl_idname = "sollumz.setroomboundsfromselection"
    bl_label = "Set Bounds From Selection"

    @classmethod
    def poll(cls, context):
        return (
            get_selected_room(context) is not None and
            not get_selected_archetype(context).rooms.has_multiple_selection and
            context.active_object and
            context.active_object.mode == "EDIT"
        )

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_room = get_selected_room(context)
        selected_verts = []
        for obj in context.objects_in_mode:
            selected_verts.extend(get_selected_vertices(obj))
        if not len(selected_verts) > 1:
            self.message("You must select at least 2 vertices!")
            return False
        if not selected_archetype.asset:
            self.message("You must set an asset for the archetype.")
            return False

        pos = selected_archetype.asset.location

        selected_room.bb_max = get_max_vector_list(
            selected_verts) - pos
        selected_room.bb_min = get_min_vector_list(
            selected_verts) - pos
        return True


class SOLLUMZ_OT_delete_room(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete selected room(s)"""
    bl_idname = "sollumz.deleteroom"
    bl_label = "Delete Room"

    @classmethod
    def poll(cls, context):
        return get_selected_room(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)

        indices_to_remove = selected_archetype.rooms.selected_items_indices
        indices_to_remove.sort(reverse=True)
        new_active_index = max(indices_to_remove[-1] - 1, 0) if indices_to_remove else 0
        for index_to_remove in indices_to_remove:
            selected_archetype.rooms.remove(index_to_remove)
        selected_archetype.rooms.select(new_active_index)

        # Force redraw of gizmos
        context.space_data.show_gizmo = context.space_data.show_gizmo

        validate_dynamic_enums(selected_archetype.portals, "room_from_id", selected_archetype.rooms)
        validate_dynamic_enums(selected_archetype.portals, "room_to_id", selected_archetype.rooms)
        validate_dynamic_enums(selected_archetype.entities, "attached_room_id", selected_archetype.rooms)
        validate_dynamic_enum(context.scene, "sollumz_add_entity_room", selected_archetype.rooms)
        validate_dynamic_enum(context.scene, "sollumz_entity_filter_room", selected_archetype.rooms)
        validate_dynamic_enum(context.scene, "sollumz_entity_filter_entity_set_room", selected_archetype.rooms)
        validate_dynamic_enum(context.scene, "sollumz_add_portal_room_from", selected_archetype.rooms)
        validate_dynamic_enum(context.scene, "sollumz_add_portal_room_to", selected_archetype.rooms)

        return True
