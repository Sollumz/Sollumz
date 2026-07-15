from bpy.types import (
    Panel,
)

from . import operators as ops


class SOLLUMZ_PT_asset_library_panel(Panel):
    bl_label = "Asset Library"
    bl_idname = "SOLLUMZ_PT_asset_library_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"
    bl_order = 8

    def draw_header(self, context):
        self.layout.label(text="", icon="ASSET_MANAGER")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        ops.temporary_ui(layout)
