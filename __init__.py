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

import bpy

bl_info = {
    "name": "Sollumz",
    "author": "Skylumz, Colton and alexguirre",
    "description": "Grand Theft Auto V modding suite for Blender",
    "blender": (4, 0, 0),
    "version": (2, 4, 2),
    "category": "Import-Export",
    "doc_url": "https://docs.sollumz.org/",
    "tracker_url": "https://github.com/Sollumz/Sollumz/issues",
}


def check_blender_version():
    try:
        required_version = bl_info.get("blender", (0, 0, 0))
    except NameError:
        # If bl_info is not accessible, fall back to a default version.
        # Unexpected behavior in 4.2, might also occur in lower versions.
        required_version = (4, 0, 0)

    if bpy.app.version < required_version:
        error_message = f"Sollumz requires Blender {'.'.join(map(str, required_version))} or newer. Please update your Blender version."
        raise ImportError(error_message)


class SOLLUMZ_OT_version_error(bpy.types.Operator):
    bl_idname = "sollumz.version_error"
    bl_label = "Sollumz Version Error"
    bl_description = "Sollumz version error"
    bl_options = {'INTERNAL'}

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self, width=400)

    def draw(self, context):
        layout = self.layout
        layout.label(text="Sollumz could not be loaded due to an incompatible Blender version.", icon='ERROR')
        layout.label(text="Please check the System Console for more information.")
        layout.label(text="Update Blender or use a compatible version to use Sollumz.")


def show_version_error_popup():
    bpy.ops.sollumz.version_error('INVOKE_DEFAULT')


def reload_sollumz_modules():
    import sys

    print("Reloading Sollumz modules")

    # Remove the packages imported in this module from the scope, so they are loaded again when imported below
    global auto_load, sollumz_tool, sollumz_debug
    del sollumz_tool
    del sollumz_debug
    del auto_load

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
from . import sollumz_tool  # noqa: E402
from . import sollumz_debug  # noqa: E402
from . import auto_load  # noqa: E402


sollumz_debug.init_debug()  # first in case we need to debug initialization code
auto_load.init()


def register():
    try:
        check_blender_version()
    except ImportError as e:
        print(f"Sollumz Error: {str(e)}")
        bpy.utils.register_class(SOLLUMZ_OT_version_error)
        bpy.app.timers.register(show_version_error_popup, first_interval=0.1)
        return

    auto_load.register()

    # WorkSpaceTools need to be registered after normal modules so the keymaps
    # detect the registed operators
    sollumz_tool.register_tools()


def unregister():
    # Unregister add-on components with error handling on incompatible Blender versions to prevent error messages
    if "SOLLUMZ_OT_version_error" in dir(bpy.types):
        bpy.utils.unregister_class(SOLLUMZ_OT_version_error)

    if "sollumz_tool" in globals() and hasattr(sollumz_tool, "sollumz_tools"):
        for tool in sollumz_tool.sollumz_tools:
            try:
                bpy.utils.unregister_tool(tool.cls)
            except (AttributeError, RuntimeError, ValueError):
                pass

    if "sollumz_tool" in globals() and hasattr(sollumz_tool, "unregister_tools"):
        try:
            sollumz_tool.unregister_tools()
        except Exception:
            pass

    if "auto_load" in globals() and hasattr(auto_load, "unregister"):
        try:
            auto_load.unregister()
        except Exception:
            pass
