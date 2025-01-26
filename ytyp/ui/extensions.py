import bpy
from bpy.types import (
    UILayout
)
from ...sollumz_ui import BasicListHelper, draw_list_with_add_remove
from ..properties.extensions import ExtensionsContainer
from ..utils import get_selected_archetype, get_selected_ytyp
from .archetype import ArchetypeChildTabPanel


class ExtensionsListHelper(BasicListHelper):
    def get_item_icon(self, item) -> str | int:
        return UILayout.enum_item_icon(item, "extension_type", item.extension_type)


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
            if extensions_container.IS_ARCHETYPE:
                row.prop(selected_extension, "extension_type_for_archetypes")
            else:
                row.prop(selected_extension, "extension_type_for_entities")
            row = layout.row()
            row.prop(selected_extension, "name")

            layout.separator()

            extension_properties = selected_extension.get_properties()
            extension_properties.draw_props_pre(layout)
            extension_properties.draw_props(layout)
            extension_properties.draw_props_post(layout)


class SOLLUMZ_UL_ARCHETYPE_EXTENSIONS_LIST(ExtensionsListHelper, bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_ARCHETYPE_EXTENSIONS_LIST"


class SOLLUMZ_PT_ARCHETYPE_EXTENSIONS_PANEL(ArchetypeChildTabPanel, ExtensionsPanelHelper, bpy.types.Panel):
    bl_label = "Extensions"
    bl_idname = "SOLLUMZ_PT_ARCHETYPE_EXTENSIONS_PANEL"

    bl_order = 1

    icon = "CON_TRACKTO"

    ADD_OPERATOR_ID = "sollumz.addarchetypeextension"
    DELETE_OPERATOR_ID = "sollumz.deletearchetypeextension"
    DUPLICATE_OPERATOR_ID = "sollumz.duplicatearchetypeextension"
    EXTENSIONS_LIST_ID = SOLLUMZ_UL_ARCHETYPE_EXTENSIONS_LIST.bl_idname

    @classmethod
    def get_extensions_container(self, context):
        return get_selected_archetype(context)

    def draw(self, context):
        # TODO(multiselect): think how we should manage disabling panels when multiple selection enabled
        ytyp = get_selected_ytyp(context)
        self.layout.enabled = not ytyp.archetypes.has_multiple_selection
        super().draw(context)
