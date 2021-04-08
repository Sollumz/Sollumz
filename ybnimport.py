import bpy
import xml.etree.ElementTree as ET
import os
import sys
sys.path.append(os.path.dirname(__file__))
from bpy_extras.io_utils import ImportHelper
from .resources.bound import Bound

def bound_poly_cylinder_to_blender(cylinder):
    raise NotImplementedError

def bound_poly_box_to_blender(box):
    raise NotImplementedError

def bound_poly_capsule_to_blender(capsule):
    raise NotImplementedError

def bound_poly_sphere_to_blender(sphere):
    raise NotImplementedError

def bound_poly_triangle_to_blender(triangle):
    raise NotImplementedError

def bound_geometry_to_blender(geometry):
    raise NotImplementedError

def bound_cloth_to_blender(cloth):
    raise NotImplementedError

def bound_disc_to_blender(disc):
    raise NotImplementedError

def bound_cylinder_to_blender(cylinder):
    raise NotImplementedError

def bound_capsule_to_blender(capsule):
    raise NotImplementedError

def bound_sphere_to_blender(sphere):
    raise NotImplementedError

def bound_box_to_blender(box):
    raise NotImplementedError

def bound_composite_to_blender(composite):
    raise NotImplementedError

class ImportYbnXml(bpy.types.Operator, ImportHelper):
    """Imports .ybn.xml file exported from codewalker."""
    bl_idname = "sollumz.importybn" 
    bl_label = "Import ybn.xml"
    filename_ext = ".ybn.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ybn.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def execute(self, context):
        b = Bound()
        b.read_xml(ET.parse(self.filepath).getroot()[0])
        
        bound_composite_to_blender(b)

        return {'FINISHED'}

def ybn_menu_func_import(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Import .ybn.xml")