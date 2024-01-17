import bpy
from ...tabbed_panels import TabPanel
from ...sollumz_ui import BasicListHelper, draw_list_with_add_remove
from ..properties.extensions import ExtensionsContainer, ExtensionType
from ..operators.extensions import (
    SOLLUMZ_OT_update_bottom_from_selected,
    SOLLUMZ_OT_update_corner_a_location,
    SOLLUMZ_OT_update_corner_b_location,
    SOLLUMZ_OT_update_corner_c_location,
    SOLLUMZ_OT_update_corner_d_location,
    SOLLUMZ_OT_update_light_shaft_offeset_location,
    SOLLUMZ_OT_update_offset_and_top_from_selected,
    SOLLUMZ_OT_update_particle_effect_location,
    SOLLUMZ_OT_calculate_light_shaft_center_offset_location,
    SOLLUMZ_OT_update_light_shaft_direction,
)
from ..utils import get_selected_archetype, get_selected_extension
from .archetype import SOLLUMZ_PT_ARCHETYPE_TABS_PANEL


class ExtensionsListHelper:
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon="CON_TRACKTO")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="CON_TRACKTO")


class ExtensionsPanelHelper:
    ADD_OPERATOR_ID = ""
    DELETE_OPERATOR_ID = ""
    DUPLICATE_OPERATOR_ID = ""
    EXTENSIONS_LIST_ID = ""

    @classmethod
    def get_extensions_container(self, context) -> ExtensionsContainer:
        """Get data-block that contains all of the extensions."""
        raise NotImplementedError

    @classmethod
    def poll(cls, context):
        return cls.get_extensions_container(context) is not None

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        extensions_container = self.get_extensions_container(context)

        _, side_col = draw_list_with_add_remove(layout, self.ADD_OPERATOR_ID, self.DELETE_OPERATOR_ID,
                                             self.EXTENSIONS_LIST_ID, "", extensions_container, "extensions",
                                             extensions_container, "extension_index")
        side_col.separator()
        side_col.operator(self.DUPLICATE_OPERATOR_ID, text="", icon="DUPLICATE")

        selected_extension = extensions_container.selected_extension
        if selected_extension is not None:

            layout.separator()

            row = layout.row()
            row.prop(selected_extension, "extension_type")
            row = layout.row()
            row.prop(selected_extension, "name")

            layout.separator()

            is_light_shaft = selected_extension.extension_type == ExtensionType.LIGHT_SHAFT
            if is_light_shaft:
                row = layout.row()
                row.operator(
                    SOLLUMZ_OT_update_light_shaft_offeset_location.bl_idname)
                row = layout.row()
                row.operator(SOLLUMZ_OT_update_corner_a_location.bl_idname)
                row.operator(SOLLUMZ_OT_update_corner_b_location.bl_idname)
                row = layout.row()
                row.operator(SOLLUMZ_OT_update_corner_d_location.bl_idname)
                row.operator(SOLLUMZ_OT_update_corner_c_location.bl_idname)
                row = layout.row()
                row.operator(SOLLUMZ_OT_update_light_shaft_direction.bl_idname)
                layout.separator()
                row = layout.row()
                row.operator(
                    SOLLUMZ_OT_calculate_light_shaft_center_offset_location.bl_idname)
                layout.separator()

            extension_properties = selected_extension.get_properties()

            row = layout.row()
            row.prop(extension_properties, "offset_position")
            for prop_name in extension_properties.__class__.__annotations__:
                if is_light_shaft and prop_name == "flags":
                    # draw individual checkboxes for the bits instead of the flags IntProperty
                    col = layout.column(heading="Flags")
                    col.prop(extension_properties, "flag_0")
                    col.prop(extension_properties, "flag_1")
                    col.prop(extension_properties, "flag_4")
                    col.prop(extension_properties, "flag_5")
                    col.prop(extension_properties, "flag_6")
                elif is_light_shaft and (prop_name.startswith("flag_") or prop_name == "scale_by_sun_intensity"):
                    # skip light shaft flag props, drawn above
                    # and skip scale_by_sun_intensity because it is the same as flag_5
                   continue
                else:
                    if prop_name in {'direction_amount', 'cornerA'}:
                        layout.separator()
                    row = layout.row()
                    row.prop(extension_properties, prop_name)


class SOLLUMZ_UL_ARCHETYPE_EXTENSIONS_LIST(BasicListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ARCHETYPE_EXTENSIONS_LIST"
    icon = "CON_TRACKTO"


class SOLLUMZ_PT_ARCHETYPE_EXTENSIONS_PANEL(TabPanel, ExtensionsPanelHelper, bpy.types.Panel):
    bl_label = "Extensions"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_EXTENSIONS_PANEL"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL.bl_idname

    bl_order = 1

    parent_tab_panel = SOLLUMZ_PT_ARCHETYPE_TABS_PANEL
    icon = "CON_TRACKTO"

    ADD_OPERATOR_ID = "sollumz.addarchetypeextension"
    DELETE_OPERATOR_ID = "sollumz.deletearchetypeextension"
    DUPLICATE_OPERATOR_ID = "sollumz.duplicatearchetypeextension"
    EXTENSIONS_LIST_ID = SOLLUMZ_UL_ARCHETYPE_EXTENSIONS_LIST.bl_idname

    @classmethod
    def get_extensions_container(self, context):
        return get_selected_archetype(context)

    def draw(self, context):
        super().draw(context)

        layout = self.layout
        selected_extension = get_selected_extension(context)

        if selected_extension is None:
            return

        layout.separator()

        if selected_extension.extension_type == ExtensionType.LADDER:
            row = layout.row()
            row.operator(
                SOLLUMZ_OT_update_offset_and_top_from_selected.bl_idname)
            row.operator(SOLLUMZ_OT_update_bottom_from_selected.bl_idname)

        if selected_extension.extension_type == ExtensionType.PARTICLE:
            row = layout.row()
            row.operator(SOLLUMZ_OT_update_particle_effect_location.bl_idname)
