import bpy
from ..utils import get_selected_archetype, get_selected_entity


class SOLLUMZ_OT_add_archetype_extension(bpy.types.Operator):
    """Add an extension to the archetype."""
    bl_idname = "sollumz.addarchetypeextension"
    bl_options = {"UNDO"}
    bl_label = "Add Extension"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.new_extension()

        return {"FINISHED"}


class SOLLUMZ_OT_delete_archetype_extension(bpy.types.Operator):
    """Delete the selected extension from the archetype."""
    bl_idname = "sollumz.deletearchetypeextension"
    bl_options = {"UNDO"}
    bl_label = "Delete Extension"

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)

        if not selected_archetype:
            return None

        return selected_archetype.selected_extension is not None

    def execute(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.delete_selected_extension()

        return {"FINISHED"}


class SOLLUMZ_OT_add_entity_extension(bpy.types.Operator):
    """Add an extension to the entity."""
    bl_idname = "sollumz.addentityextension"
    bl_options = {"UNDO"}
    bl_label = "Add Extension"

    @classmethod
    def poll(cls, context):
        return get_selected_entity(context) is not None

    def execute(self, context):
        selected_entity = get_selected_entity(context)
        selected_entity.new_extension()

        return {"FINISHED"}


class SOLLUMZ_OT_delete_entity_extension(bpy.types.Operator):
    """Delete the selected extension from the entity."""
    bl_idname = "sollumz.deleteentityextension"
    bl_options = {"UNDO"}
    bl_label = "Delete Extension"

    @classmethod
    def poll(cls, context):
        selected_entity = get_selected_entity(context)

        if not selected_entity:
            return None

        return selected_entity.selected_extension is not None

    def execute(self, context):
        selected_entity = get_selected_entity(context)
        selected_entity.delete_selected_extension()

        return {"FINISHED"}
