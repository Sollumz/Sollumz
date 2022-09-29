import bpy

from ..sollumz_properties import SollumType
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL


def draw_ymap_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.YMAP:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.prop(obj.ymap_properties, "name")
        layout.prop(obj.ymap_properties, "parent")

        layout.label(text="Map Flags")
        layout.prop(obj.ymap_properties, "flags")

        row = layout.row()
        row.prop(obj.ymap_properties.flags_toggle, "script_loaded", toggle=1)
        row.prop(obj.ymap_properties.flags_toggle, "has_lod", toggle=1)

        layout.prop(obj.ymap_properties, "content_flags")
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle, "has_hd", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle, "has_lod", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle, "has_slod2", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle, "has_int", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle, "has_slod", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle, "has_occl", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle, "has_physics", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle, "has_lod_lights", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle, "has_dis_lod_lights", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle, "has_critical", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle, "has_grass", toggle=1)

def draw_ymap_model_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.YMAP_MODEL_OCCLUDER:
        layout = self.layout
        layout.prop(obj.ymap_properties, 'flags')

class OBJECT_PT_ymap_block(bpy.types.Panel):
    bl_label = "Block"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 0

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if obj and obj.sollum_type == SollumType.YMAP:
            return True
        return None

    def draw(self, context):
        obj = context.active_object
        if obj and obj.sollum_type == SollumType.YMAP:
            layout = self.layout
            layout.prop(obj.ymap_properties.block, "version")
            layout.prop(obj.ymap_properties.block, "flags")
            layout.prop(obj.ymap_properties.block, "name")
            layout.prop(obj.ymap_properties.block, "exported_by")
            layout.prop(obj.ymap_properties.block, "owner")
            layout.prop(obj.ymap_properties.block, "time")


def register():
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_ymap_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_ymap_model_properties)

def unregister():
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_ymap_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_ymap_model_properties)