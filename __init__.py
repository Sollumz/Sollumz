# ##### BEGIN GPL LICENSE BLOCK #####
#
#  This program is free software; you can redistribute it and/or
#  modify it under the terms of the GNU General Public License
#  as published by the Free Software Foundation; either version 2
#  of the License, or (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software Foundation,
#  Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ##### END GPL LICENSE BLOCK #####

bl_info = {
    "name": "Sollumz",
    "author": "Skylumz",
    "version": (0, 0, 0),
    "blender":  (2, 80, 0),
    "location": "File > Import, Export",
    "description": "Import .ydr.xml",
    "wiki_url": "None",
    "category": "Import",
}


if "bpy" in locals():
    import importlib
    importlib.reload(properties)
    importlib.reload(shaderoperators)
    importlib.reload(ydrimport)
    importlib.reload(ydrexport)
    importlib.reload(ybnimport)
    importlib.reload(ybnexport)
    importlib.reload(yftimport)
    importlib.reload(ycdimport)
    importlib.reload(sollumz_ui)
    importlib.reload(collisionmatoperators)
    importlib.reload(tools)
else:
    from . import properties
    from . import shaderoperators
    from . import ydrimport
    from . import ydrexport 
    from . import ybnimport 
    from . import ybnexport 
    from . import yftimport 
    from . import ycdimport 
    from . import sollumz_ui
    from . import collisionmatoperators
    from . import tools
    
import bpy

def register():
    properties.register()
    shaderoperators.register()
    ydrimport.register()
    ydrexport.register()
    sollumz_ui.register()
    collisionmatoperators.register()
    ybnimport.register()
    ybnexport.register()
    yftimport.register()
    ycdimport.register()
    
def unregister():
    properties.unregister()
    shaderoperators.unregister()
    ydrimport.unregister()
    ydrexport.unregister()
    sollumz_ui.unregister()
    collisionmatoperators.unregister()
    ybnimport.unregister()
    ybnexport.unregister()
    yftimport.unregister()
    ycdimport.unregister()

if __name__ == "__main__":
    register() 
