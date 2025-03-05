import bpy
from ..sollumz_properties import SollumType

class SOLLUMZ_PT_WATER_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Water Quads"
    bl_idname = "SOLLUMZ_PT_WATER_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 7

    def draw_header(self, context):
        self.layout.label(text="", icon="FCURVE_SNAPSHOT")

    def draw(self, context):
        layout = self.layout
        aobj = context.active_object
        sobj = context.selected_objects[0] if len(context.selected_objects) == 1 else None

        row = layout.row(align=True)
        row.operator("sollumz.createwaterdata")
        row.operator("sollumz.createwaterquad")

        if aobj and aobj == sobj and aobj.sollum_type in [SollumType.WATER_QUAD, SollumType.CALMING_QUAD, SollumType.WAVE_QUAD]:

            prop_box = layout.box()
            prop_box.label(text="Water Quad Properties")

            if aobj.sollum_type == SollumType.WATER_QUAD:
                prop_box.prop(aobj.water_quad_properties, "type")
                prop_box.prop(aobj.water_quad_properties, "invisible")
                prop_box.prop(aobj.water_quad_properties, "limited_depth")
                prop_box.prop(aobj.water_quad_properties, "a1")
                prop_box.prop(aobj.water_quad_properties, "a2")
                prop_box.prop(aobj.water_quad_properties, "a3")
                prop_box.prop(aobj.water_quad_properties, "a4")
                prop_box.prop(aobj.water_quad_properties, "no_stencil")

            elif aobj.sollum_type == SollumType.CALMING_QUAD:
                prop_box.prop(aobj.calming_quad_properties, "dampening")

            elif aobj.sollum_type == SollumType.WAVE_QUAD:
                prop_box.prop(aobj.wave_quad_properties, "amplitude")
                prop_box.prop(aobj.wave_quad_properties, "xdirection")
                prop_box.prop(aobj.wave_quad_properties, "ydirection")