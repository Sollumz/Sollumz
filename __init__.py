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

from . import auto_load
from . import sollumz_debug
from . import sollumz_tool


bl_info = {
    "name": "Sollumz",
    "author": "Skylumz and Colton",
    "description": "This plugins allows you to import/export codewalker xml files.",
    "blender": (4, 0, 0),
    "version": (2, 3, 1),
    "category": "Import-Export"
}


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
