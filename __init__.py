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
    "description": "This plugins allows you to import/export CodeWalker XML files.",
    "blender": (4, 0, 0),
    "version": (2, 4, 2),
    "category": "Import-Export",
    "doc_url": "https://sollumz.gitbook.io/sollumz-wiki/",
    "tracker_url": "https://github.com/Skylumz/Sollumz/issues",
}


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
    auto_load.register()

    # WorkSpaceTools need to be registered after normal modules so the keymaps
    # detect the registed operators
    sollumz_tool.register_tools()


def unregister():
    sollumz_tool.unregister_tools()

    auto_load.unregister()
