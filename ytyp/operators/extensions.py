import bpy
from mathutils import Vector
from ..properties.extensions import ExtensionsContainer
from ..utils import get_selected_archetype, get_selected_entity, get_selected_ytyp


class SOLLUMZ_OT_add_archetype_extension(bpy.types.Operator):
    """Add an extension to the archetype"""
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
    """Delete the selected extension from the archetype"""
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
    """Add an extension to the entity"""
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
    """Delete the selected extension from the entity"""
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
    """Update ladder offest and top from selection"""
    bl_idname = "sollumz.updateoffsetandtopfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Offset and Top"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        ytyp_index = context.scene.ytyp_index
        selected_ytyp = get_selected_ytyp(context)
        selected_archetype = get_selected_archetype(context)
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)
        
        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].ladder_extension_properties.offset_position = verts_location
        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].ladder_extension_properties.top = verts_location
        return {"FINISHED"}


class SOLLUMZ_OT_update_bottom_from_selected(bpy.types.Operator):
    """Update ladder bottom from selection"""
    bl_idname = "sollumz.updatebottomfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Bottom"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        ytyp_index = context.scene.ytyp_index
        selected_ytyp = get_selected_ytyp(context)
        selected_archetype = get_selected_archetype(context)
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)

        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].ladder_extension_properties.bottom = verts_location
        return {"FINISHED"}


class SOLLUMZ_OT_update_particle_effect_location(bpy.types.Operator):
    """Update particle effect offset from selection"""
    bl_idname = "sollumz.updateptfxoffsetfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Offset location"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        ytyp_index = context.scene.ytyp_index
        selected_archetype = get_selected_archetype(context)
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)

        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].particle_extension_properties.offset_position = verts_location
        return {"FINISHED"}


class SOLLUMZ_OT_update_light_shaft_offeset_location(bpy.types.Operator):
    """Update light shaft offset from selection"""
    bl_idname = "sollumz.updatelightshaftoffsetfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Offset location"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        ytyp_index = context.scene.ytyp_index
        selected_archetype = get_selected_archetype(context)
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)
        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].light_shaft_extension_properties.offset_position = verts_location
        return {"FINISHED"}


class SOLLUMZ_OT_update_corner_a_location(bpy.types.Operator):
    """Update light shaft corner A location from selection"""
    bl_idname = "sollumz.updatecornerafromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Corner A"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        ytyp_index = context.scene.ytyp_index
        selected_archetype = get_selected_archetype(context)
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)

        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].light_shaft_extension_properties.cornerA = verts_location
        return {"FINISHED"}



class SOLLUMZ_OT_update_corner_b_location(bpy.types.Operator):
    """Update light shaft corner B location from selection"""
    bl_idname = "sollumz.updatecornerbfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Corner B"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        ytyp_index = context.scene.ytyp_index
        selected_archetype = get_selected_archetype(context)
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)

        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].light_shaft_extension_properties.cornerB = verts_location
        return {"FINISHED"}


class SOLLUMZ_OT_update_corner_c_location(bpy.types.Operator):
    """Update light shaft corner C location from selection"""
    bl_idname = "sollumz.updatecornercfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Corner C"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        ytyp_index = context.scene.ytyp_index
        selected_archetype = get_selected_archetype(context)
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)

        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].light_shaft_extension_properties.cornerC = verts_location
        return {"FINISHED"}


class SOLLUMZ_OT_update_corner_d_location(bpy.types.Operator):
    """Update light shaft corner D location from selection"""
    bl_idname = "sollumz.updatecornerdfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Corner D"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def execute(self, context):
        selected_ytyp = get_selected_ytyp(context)
        ytyp_index = context.scene.ytyp_index
        selected_archetype = get_selected_archetype(context)
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)

        context.scene.ytyps[ytyp_index].archetypes[selected_ytyp.archetype_index].extensions[selected_archetype.extension_index].light_shaft_extension_properties.cornerD = verts_location
        return {"FINISHED"}