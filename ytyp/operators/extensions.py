import bpy
from ..properties.extensions import ExtensionsContainer
from ..utils import get_selected_archetype, get_selected_entity, get_selected_ytyp


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


class SOLLUMZ_OT_update_offset_and_top_from_selected(bpy.types.Operator):
    """Update extension property from selection."""
    bl_idname = "sollumz.updateoffsetandtopfromselectextension"
    bl_options = {"UNDO"}
    bl_label = "Update Offset and Top from selected"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        selected_archetype = get_selected_archetype(context)
        active_object = context.active_object
        context.scene.ytyps[selected_archetype.id].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].ladder_extension_properties.offset_position = active_object.location
        context.scene.ytyps[selected_archetype.id].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].ladder_extension_properties.top = active_object.location
        return {"FINISHED"}


class SOLLUMZ_OT_update_bottom_from_selected(bpy.types.Operator):
    """Update extension property from selection."""
    bl_idname = "sollumz.updatebottomfromselectextension"
    bl_options = {"UNDO"}
    bl_label = "Update Bottom from selected"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        selected_archetype = get_selected_archetype(context)
        active_object = context.active_object

        context.scene.ytyps[selected_archetype.id].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].ladder_extension_properties.bottom = active_object.location
        return {"FINISHED"}