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
import os
from . import auto_load


bl_info = {
    "name": "SollumzX Reloaded 🕊️",
    "author": "MrVicho13 - and one one else 🧢",
    "description": "This plugins allows you to import/export CodeWalker XML files.",
    "blender": (3, 0, 0),
    "version": (1, 0),
    "location": "",
    "warning": "This is a work-in-progress",
    "category": "Import-Export"
}


auto_load.init()


def register():
    auto_load.register()


def unregister():
    auto_load.unregister()
