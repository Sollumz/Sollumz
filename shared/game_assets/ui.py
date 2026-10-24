import bpy
from bpy.types import (
    Panel,
)

from ...icons import icon_manager
from . import operators as ops
from .asset_info import AssetArchetypeInfo


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


def _draw_info(layout, label: str, value: str):
    split = layout.split(factor=0.4)
    col = split.column()
    col.alignment = "RIGHT"
    col.label(text=label)
    split.column().label(text=value)


def _draw_archetype_info(layout, archetype_info: AssetArchetypeInfo):
    _draw_info(layout, "Game", "GTA5")
    _draw_info(layout, "YTYP", archetype_info.ytyp)
    _draw_info(layout, "Type", archetype_info.type.title() if archetype_info.type != "MLO" else "MLO")


class SOLLUMZ_PT_game_asset_info(Panel):
    bl_label = "Game Asset"
    bl_idname = "SOLLUMZ_PT_game_asset_info"
    bl_space_type = "FILE_BROWSER"
    bl_region_type = "TOOL_PROPS"

    # not really needed, only here so Preferences > UI > Panels lists it
    # under "File Browser > Asset Browser" instead of only "File Browser"
    bl_category = "Asset Browser"

    @classmethod
    def poll(cls, context):
        from bpy_extras.asset_utils import SpaceAssetInfo

        return SpaceAssetInfo.is_asset_browser_poll(context) and ops.get_active_game_asset(context) is not None

    def draw_header(self, context):
        icon_manager.icon_label("sollumz_icon", self)

    def draw(self, context):
        layout = self.layout
        _draw_archetype_info(layout, ops.get_active_game_asset(context))

        layout.separator()
        layout.operator(
            ops.SOLLUMZ_OT_import_library_asset_from_game_installation.bl_idname,
            text=ops.SOLLUMZ_OT_import_library_asset_from_game_installation.label(context),
            icon="IMPORT",
        )


def _draw_asset_browser_context_menu(self, context):
    if next(ops.iter_selected_game_assets(context), None) is None:
        return

    layout = self.layout
    layout.separator()
    # Menus in the asset browser use EXEC_REGION_WIN, but we need to invoke the operator to open the file browser
    col = layout.column()
    col.operator_context = "INVOKE_DEFAULT"
    col.operator(
        ops.SOLLUMZ_OT_import_library_asset_from_game_installation.bl_idname,
        text=ops.SOLLUMZ_OT_import_library_asset_from_game_installation.label(context),
        icon="IMPORT",
    )


def register():
    bpy.types.ASSETBROWSER_MT_context_menu.append(_draw_asset_browser_context_menu)


def unregister():
    bpy.types.ASSETBROWSER_MT_context_menu.remove(_draw_asset_browser_context_menu)
