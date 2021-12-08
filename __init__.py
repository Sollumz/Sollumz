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
    "name": "Sollumz",
    "author": "Skylumz",
    "description": "This plugins allows you to import/export codewalker xml files.",
    "blender": (2, 92, 0),
    "version": (1, 3),
    "location": "",
    "warning": "",
    "category": "Import-Export"
}


auto_load.init()


# sollumz settings
class SollumzSettings(bpy.types.AddonPreferences):
    bl_idname = __name__

    shared_texture_folder: bpy.props.StringProperty(
        name="Shared Texture Folder Path",
        description="Path to the folder containing the textures to try to import",
        default=os.path.dirname(__file__) + "\\resources\\textures",
        subtype='DIR_PATH'
    )

    def draw(self, context):
        layout = self.layout
        layout.prop(self, "shared_texture_folder")


def register():
    auto_load.register()
    bpy.utils.register_class(SollumzSettings)


def unregister():
    auto_load.unregister()
    bpy.utils.unregister_class(SollumzSettings)
