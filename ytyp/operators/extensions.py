import bpy
from mathutils import Vector
from ..properties.extensions import ExtensionsContainer, ExtensionType
from ..utils import (
    get_selected_archetype,
    get_selected_entity,
    get_selected_ytyp,
    get_selected_extension,
    get_selected_entity_extension,
)
from ...tools.blenderhelper import tag_redraw


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
        tag_redraw(context, space_type="VIEW_3D", region_type="UI")
        tag_redraw(context, space_type="VIEW_3D", region_type="TOOL_PROPS")
        tag_redraw(context, space_type="VIEW_3D", region_type="TOOL_HEADER")
        return {"FINISHED"}


class SOLLUMZ_OT_delete_archetype_extension(bpy.types.Operator):
    """Delete the selected extension from the archetype"""
    bl_idname = "sollumz.deletearchetypeextension"
    bl_options = {"UNDO"}
    bl_label = "Delete Extension"

    @classmethod
    def poll(cls, context):
        return get_selected_extension(context) is not None

    def execute(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.delete_selected_extension()
        tag_redraw(context, space_type="VIEW_3D", region_type="UI")
        tag_redraw(context, space_type="VIEW_3D", region_type="TOOL_PROPS")
        tag_redraw(context, space_type="VIEW_3D", region_type="TOOL_HEADER")
        return {"FINISHED"}


class SOLLUMZ_OT_duplicate_archetype_extension(bpy.types.Operator):
    """Duplicate the selected extension in the archetype"""
    bl_idname = "sollumz.duplicatearchetypeextension"
    bl_options = {"UNDO"}
    bl_label = "Duplicate Extension"

    @classmethod
    def poll(cls, context):
        return get_selected_extension(context) is not None

    def execute(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.duplicate_selected_extension()
        tag_redraw(context, space_type="VIEW_3D", region_type="UI")
        tag_redraw(context, space_type="VIEW_3D", region_type="TOOL_PROPS")
        tag_redraw(context, space_type="VIEW_3D", region_type="TOOL_HEADER")
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
        return get_selected_entity_extension(context) is not None

    def execute(self, context):
        selected_entity = get_selected_entity(context)
        selected_entity.delete_selected_extension()

        return {"FINISHED"}


class SOLLUMZ_OT_duplicate_entity_extension(bpy.types.Operator):
    """Duplicate the selected extension in the entity"""
    bl_idname = "sollumz.duplicateentityextension"
    bl_options = {"UNDO"}
    bl_label = "Duplicate Extension"

    @classmethod
    def poll(cls, context):
        return get_selected_entity_extension(context) is not None

    def execute(self, context):
        selected_entity = get_selected_entity(context)
        selected_entity.duplicate_selected_extension()
        return {"FINISHED"}


class ExtensionUpdateFromSelectionHelper:
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return get_selected_extension(context) is not None and aobj and aobj.mode == "EDIT"

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        raise NotImplementedError

    def execute(self, context):
        aobj = context.active_object
        aobj.update_from_editmode()

        me = aobj.data
        selected_vertices = [v.co for v in me.vertices if v.select]
        if not selected_vertices:
            self.report({"WARNING"}, "Please select at least one vertex.")
            return {"CANCELLED"}

        verts_location = sum(selected_vertices, Vector()) / len(selected_vertices)

        self.set_extension_props(context, verts_location)

        return {"FINISHED"}


class SOLLUMZ_OT_extension_update_location_from_selected(bpy.types.Operator, ExtensionUpdateFromSelectionHelper):
    """Update extension offset from selection"""
    bl_idname = "sollumz.extension_update_location_from_selected"
    bl_options = {"UNDO"}
    bl_label = "Update Location"

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        ext = get_selected_extension(context)
        props = ext.get_properties()
        offset = verts_location - props.offset_position
        ext.translate(offset)


class SOLLUMZ_OT_update_bottom_from_selected(bpy.types.Operator, ExtensionUpdateFromSelectionHelper):
    """Update ladder bottom from selection"""
    bl_idname = "sollumz.updatebottomfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Bottom"

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        ladder_props = get_selected_extension(context).ladder_extension_properties
        ladder_props.bottom = verts_location


class SOLLUMZ_OT_update_corner_a_location(bpy.types.Operator, ExtensionUpdateFromSelectionHelper):
    """Update light shaft corner A location from selection"""
    bl_idname = "sollumz.updatecornerafromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Corner A"

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        light_shaft_props = get_selected_extension(context).light_shaft_extension_properties
        light_shaft_props.cornerA = verts_location


class SOLLUMZ_OT_update_corner_b_location(bpy.types.Operator, ExtensionUpdateFromSelectionHelper):
    """Update light shaft corner B location from selection"""
    bl_idname = "sollumz.updatecornerbfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Corner B"

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        light_shaft_props = get_selected_extension(context).light_shaft_extension_properties
        light_shaft_props.cornerB = verts_location


class SOLLUMZ_OT_update_corner_c_location(bpy.types.Operator, ExtensionUpdateFromSelectionHelper):
    """Update light shaft corner C location from selection"""
    bl_idname = "sollumz.updatecornercfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Corner C"

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        light_shaft_props = get_selected_extension(context).light_shaft_extension_properties
        light_shaft_props.cornerC = verts_location


class SOLLUMZ_OT_update_corner_d_location(bpy.types.Operator, ExtensionUpdateFromSelectionHelper):
    """Update light shaft corner D location from selection"""
    bl_idname = "sollumz.updatecornerdfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Corner D"

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        light_shaft_props = get_selected_extension(context).light_shaft_extension_properties
        light_shaft_props.cornerD = verts_location


class SOLLUMZ_OT_update_light_shaft_direction(bpy.types.Operator, ExtensionUpdateFromSelectionHelper):
    """Update light shaft direction from selection"""
    bl_idname = "sollumz.updatelightshaftdirectionfromselection"
    bl_options = {"UNDO"}
    bl_label = "Update Lightshaft Direction"

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        aobj = context.active_object

        light_shaft_props = get_selected_extension(context).light_shaft_extension_properties
        start_pos = aobj.matrix_world @ light_shaft_props.offset_position
        end_pos = aobj.matrix_world @ verts_location
        direction = end_pos - start_pos
        light_shaft_props.length = direction.length
        light_shaft_props.direction = direction.normalized()


class SOLLUMZ_OT_calculate_light_shaft_center_offset_location(bpy.types.Operator, ExtensionUpdateFromSelectionHelper):
    """Calculates the center based on the corner coordinates"""
    bl_idname = "sollumz.calculatelightshaftoffsetlocation"
    bl_options = {"UNDO"}
    bl_label = "Calculate Center Offset location"

    def execute(self, context):
        light_shaft_props = get_selected_extension(context).light_shaft_extension_properties
        cornerA = light_shaft_props.cornerA
        cornerB = light_shaft_props.cornerB
        cornerC = light_shaft_props.cornerC
        cornerD = light_shaft_props.cornerD

        verts_location = (cornerA + cornerB + cornerC + cornerD) / 4.0
        self.set_extension_props(context, verts_location)
        return {'FINISHED'}

    @classmethod
    def set_extension_props(cls, context: bpy.types.Context, verts_location: Vector):
        light_shaft_props = get_selected_extension(context).light_shaft_extension_properties
        light_shaft_props.offset_position = verts_location


class SOLLUMZ_OT_light_effect_create_lights_from_entity(bpy.types.Operator):
    """Duplicates the lights found in the entity linked object and links them to this light effect extension"""
    bl_idname = "sollumz.light_effect_create_lights_from_entity"
    bl_options = {"UNDO"}
    bl_label = "Create Lights"

    @classmethod
    def poll(cls, context):
        selected_extension = get_selected_entity_extension(context)
        if selected_extension is None:
            return False

        if selected_extension.extension_type != ExtensionType.LIGHT_EFFECT:
            return False

        selected_entity = get_selected_entity(context)
        if selected_entity.linked_object is None:
            cls.poll_message_set("Selected entity has no linked object")
            return False

        return True

    def execute(self, context):
        selected_entity = get_selected_entity(context)
        selected_extension = get_selected_entity_extension(context)

        from ...ydr.lights import duplicate_lights_for_light_effect
        obj = duplicate_lights_for_light_effect(selected_entity.linked_object)
        obj.name = f"{selected_entity.archetype_name}.light_effect"
        constraint = obj.constraints.new("COPY_TRANSFORMS")
        constraint.target = selected_entity.linked_object
        selected_extension.get_properties().linked_lights_object = obj

        return {"FINISHED"}
