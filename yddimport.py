import bpy
import xml.etree.ElementTree as ET
import os

import sys
sys.path.append(os.path.dirname(__file__))

from bpy_extras.io_utils import ImportHelper
from .resources.drawable import DrawableDictionary
from .resources.shader import ShaderManager
from .ydrimport import drawable_to_blender, shader_group_to_blender

def drawable_dictionary_to_blender(dictionary, filepath):
    
    drawable_objs = []
    sm = ShaderManager()
    for drawable in dictionary.drawables:
        mats = shader_group_to_blender(sm, drawable.shader_group, filepath)    
        drawable_objs.append(drawable_to_blender(drawable, mats))
    
    dictionary_obj = bpy.data.objects.new(os.path.basename(filepath), None)

    for obj in drawable_objs:
        obj.parent = dictionary_obj

    bpy.context.scene.collection.objects.link(dictionary_obj)

class ImportYddXml(bpy.types.Operator, ImportHelper):
    """Imports .ydd.xml file exported from codewalker."""
    bl_idname = "sollumz.importydd" 
    bl_label = "Import ydd.xml"
    filename_ext = ".ydd.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ydd.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def execute(self, context):

        d = DrawableDictionary()
        d.read_xml(ET.parse(self.filepath))

        drawable_dictionary_to_blender(d, self.filepath)

        return {'FINISHED'}

def ydd_menu_func_import(self, context):
    self.layout.operator(ImportYddXml.bl_idname, text="Import .ydd.xml")