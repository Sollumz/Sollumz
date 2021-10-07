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
    "name" : "sollumz",
    "author" : "skylumz",
    "description" : "",
    "blender" : (2, 80, 0),
    "version" : (0, 0, 1),
    "location" : "",
    "warning" : "",
    "category" : "Import-Export"
}

import bpy
 
# Development: Reload submodules
import importlib
from . import resources
import Sollumz
packages = [Sollumz, resources]

for package in packages:
    importlib.reload(package)

from .ydrimport import ImportYdrXml, ydr_menu_func_import
from .ybnimport import ImportYbnXml, ybn_menu_func_import
from .ybnexport import ExportYbnXml, ybn_menu_func_export
from .sollumz_properties import *
from .sollumz_ui import *
from .sollum_operators import *

classes = (
SOLLUMZ_PT_MAIN_PANEL, SOLLUMZ_PT_MAT_PANEL, SOLLUMZ_PT_SHADER_PANEL, SOLLUMZ_PT_COLLISION_TOOL_PANEL, 
SOLLUMZ_OT_create_bound_composite,
SOLLUMZ_OT_create_geometry_bound,
SOLLUMZ_OT_create_geometrybvh_bound,
SOLLUMZ_OT_create_box_bound,
SOLLUMZ_OT_create_sphere_bound,
SOLLUMZ_OT_create_capsule_bound,
SOLLUMZ_OT_create_cylinder_bound,
SOLLUMZ_OT_create_disc_bound,
SOLLUMZ_OT_create_cloth_bound,
SOLLUMZ_OT_create_polygon_bound,
SOLLUMZ_OT_create_collision_material,
DrawableProperties, GeometryProperties, TextureProperties, ShaderProperties, CollisionProperties, CollisionFlags, BoundProperties, BoundFlags, 
ImportYdrXml, ImportYbnXml, ExportYbnXml)


def register():
    for c in classes:
        bpy.utils.register_class(c)
    bpy.types.TOPBAR_MT_file_import.append(ydr_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(ybn_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(ybn_menu_func_export)
    assign_properties()

def unregister():
    for c in classes:
        bpy.utils.unregister_class(c)
    bpy.types.TOPBAR_MT_file_import.remove(ydr_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(ybn_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(ybn_menu_func_export)

