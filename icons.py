import bpy
import bpy.utils.previews
from pathlib import Path
from .sollumz_preferences import get_addon_preferences


ICON_DIR = Path(__file__).parent / "icons"
ICON_EXT = ".png"
PREVIEW_COLLECTION_NAME = "main"


class IconManager:
    def __init__(self, icon_dir: Path):
        self._icons = self._get_custom_icons(icon_dir)
        self._preview_collections = {}
        self._register_icons_from_directory(icon_dir)

    def _get_custom_icons(self, path: Path) -> set:
        """Retrieve all .png files from a directory."""
        return {icon.stem for icon in path.glob(f"*{ICON_EXT}")}

    def _register_icons_from_directory(self, path: Path):
        pcoll = bpy.utils.previews.new()
        for icon_name in self._icons:
            icon_path = path / f"{icon_name}{ICON_EXT}"
            pcoll.load(icon_name, str(icon_path), "IMAGE")
        self._preview_collections[PREVIEW_COLLECTION_NAME] = pcoll

    def load_icon(self, name: str) -> int:
        """Load a specific icon by name."""
        if name in self._icons:
            pcoll = self._preview_collections[PREVIEW_COLLECTION_NAME]
            return pcoll[name].icon_id
        return 0

    def icon_label(self, name: str, panel: bpy.types.Panel):
        """Render an icon label as text layout."""
        if name in self._icons:
            if name != "sollumz_icon":
                return panel.layout.label(text="", icon_value=self.load_icon(name))
            preferences = get_addon_preferences(bpy.context)
            if preferences.sollumz_icon_header:
                return panel.layout.label(text="", icon_value=self.load_icon(name))
        return

    def unregister(self):
        for pcoll in self._preview_collections.values():
            bpy.utils.previews.remove(pcoll)
        self._preview_collections.clear()


# Global icon manager instance
icon_manager = IconManager(ICON_DIR)

ICON_GEOM_TOOL = str(ICON_DIR / "sollumz.tool")


def register():
    pass  # Icons are already loaded during the instantiation of icon_manager


def unregister():
    icon_manager.unregister()
