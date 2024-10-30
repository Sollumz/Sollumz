import bpy

from ..sollumz_properties import SollumType
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..sollumz_ui import BasicListHelper, SollumzFileSettingsPanel, draw_list_with_add_remove


def draw_ymap_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.YMAP:
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
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
        row.prop(obj.ymap_properties.content_flags_toggle,
                 "has_slod2", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle, "has_int", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle, "has_slod", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle, "has_occl", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle,
                 "has_physics", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle,
                 "has_lod_lights", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle,
                 "has_dis_lod_lights", toggle=1)
        row.prop(obj.ymap_properties.content_flags_toggle,
                 "has_critical", toggle=1)
        row = layout.row()
        row.prop(obj.ymap_properties.content_flags_toggle,
                 "has_grass", toggle=1)

        layout.label(text="Extents")
        layout.prop(obj.ymap_properties, "entities_extents_min")
        layout.prop(obj.ymap_properties, "entities_extents_max")
        layout.prop(obj.ymap_properties, "streaming_extents_min")
        layout.prop(obj.ymap_properties, "streaming_extents_max")

        layout.separator()
        layout.operator("sollumz.generate_ymap_extents", icon="FILE_REFRESH")



def draw_ymap_model_occluder_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.YMAP_MODEL_OCCLUDER:
        layout = self.layout
        layout.prop(obj.ymap_model_occl_properties, 'model_occl_flags')


def draw_ymap_car_generator_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type == SollumType.YMAP_CAR_GENERATOR:
        layout = self.layout
        layout.separator()
        layout.prop(obj.ymap_cargen_properties, 'car_model')
        layout.prop(obj.ymap_cargen_properties, 'cargen_flags')
        layout.prop(obj.ymap_cargen_properties, 'pop_group')
        layout.prop(obj.ymap_cargen_properties, 'perpendicular_length')
        layout.prop(obj.ymap_cargen_properties, 'body_color_remap_1')
        layout.prop(obj.ymap_cargen_properties, 'body_color_remap_2')
        layout.prop(obj.ymap_cargen_properties, 'body_color_remap_3')
        layout.prop(obj.ymap_cargen_properties, 'body_color_remap_4')
        layout.prop(obj.ymap_cargen_properties, 'livery')


class SOLLUMZ_UL_YMAP_LIST(BasicListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_YMAP_LIST"
    item_icon = "PRESET"


class SOLLUMZ_PT_YMAP_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Map Data"
    bl_idname = "SOLLUMZ_PT_YMAP_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 5

    def draw_header(self, context):
        self.layout.label(text="", icon="OBJECT_ORIGIN")

    def draw(self, context):
        ...


class YmapToolChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_YMAP_TOOL_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_YMAP_TOOL_PANEL.bl_category


class SOLLUMZ_PT_YMAP_LIST_PANEL(YmapToolChildPanel, bpy.types.Panel):
    bl_label = "YMAPS"
    bl_idname = "SOLLUMZ_PT_YMAP_LIST_PANEL"
    bl_order = 0

    def draw(self, context):
        list_col, _ = draw_list_with_add_remove(self.layout, "sollumz.createymap", "sollumz.deleteymap",
                                                SOLLUMZ_UL_YMAP_LIST.bl_idname, "", context.scene, "ymaps", context.scene, "ymap_index", rows=3)
        row = list_col.row()
        row.operator("sollumz.importymap", icon="IMPORT")
        row.operator("sollumz.exportymap", icon="EXPORT")


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
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_ymap_model_occluder_properties)
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_ymap_car_generator_properties)


def unregister():
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_ymap_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_ymap_model_occluder_properties)
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_ymap_car_generator_properties)
