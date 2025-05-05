# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTIBILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
# General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.


bl_info = {
    "name": "Sollumz",
    "author": "Skylumz, Colton and alexguirre",
    "description": "Grand Theft Auto V modding suite for Blender",
    "blender": (4, 0, 0),
    "version": (2, 7, 1),
    "category": "Import-Export",
    "doc_url": "https://docs.sollumz.org/",
    "tracker_url": "https://github.com/Sollumz/Sollumz/issues",
}


def reload_sollumz_modules():
    import sys

    print("Reloading Sollumz modules")

    # Remove the packages imported in this module from the scope, so they are loaded again when imported below
    global auto_load, sollumz_tool, sollumz_debug, bpy
    del sollumz_tool
    del sollumz_debug
    del auto_load
    del bpy

    # Remove from `sys.modules` all Sollumz modules, so they are loaded again by auto_load
    sz_module_prefix = f"{__package__}."
    module_names = list(sys.modules.keys())
    for name in module_names:
        if name.startswith(sz_module_prefix):
            del sys.modules[name]


if "auto_load" in locals():
    # If an imported name already exists before imports, it means that the addon has been reloaded by Blender.
    # Blender only reloads the main __init__.py file, so we reload all our modules now.
    reload_sollumz_modules()


# These need to be here, not at the top of the file, to handle reload
from . import sollumz_tool  # noqa: E402, F811
from . import sollumz_debug  # noqa: E402, F811
from . import auto_load  # noqa: E402, F811
import bpy  # noqa: E402, F811


sollumz_debug.init_debug()  # first in case we need to debug initialization code
auto_load.init()


def register():
    check_blender_version()
    check_single_sollumz_instance()

    auto_load.register()

    # WorkSpaceTools need to be registered after normal modules so the keymaps
    # detect the registed operators
    sollumz_tool.register_tools()


def unregister():
    sollumz_tool.unregister_tools()

    auto_load.unregister()


def check_blender_version():
    if "bl_info" not in globals():
        # When installed as extension Blender deletes the `bl_info` variable.
        # For extensions, Blender already checks the required minimum version specified in the manifest and doesn't
        # allow enabling the extension if it isn't compatible. Don't need to check again.
        return

    required_version = bl_info["blender"]

    if bpy.app.version < required_version:
        required_version_str = ".".join(map(str, required_version))
        raise_fatal_error(
            title="Incompatible Blender Version",
            message=f"Sollumz requires Blender {required_version_str} or newer. Please update your Blender version."
        )


def check_single_sollumz_instance():
    if hasattr(bpy.types.Object, "sollum_type"):
        raise_fatal_error(
            title="Conflicting Sollumz Versions",
            message="Only one version of Sollumz can be active at a time. Please disable any other installed versions in 'Preferences > Add-ons'."
        )


def raise_fatal_error(title: str, message: str):
    """Fatal error that doesn't allow the add-on to be initialized."""

    def _draw_error_popup(self, context):
        self.layout.label(text=message)

    def _show_error_popup():
        bpy.context.window_manager.popup_menu(_draw_error_popup, title=title, icon="ERROR")

    bpy.app.timers.register(_show_error_popup, first_interval=0.0)

    # Raise an error so Blender doesn't actually enable the add-on
    raise ImportError(f"{title}. \n{message}")
