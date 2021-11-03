import xml.etree.ElementTree as ET

import bpy
from bpy_extras.io_utils import ExportHelper
from bpy.types import Operator

from .formats.ycd.ClipDictionary import ClipDictionary
from .ydrexport import prettify

def findClipDictionary(context):
    objects = context.scene.objects
    for obj in objects:
        if obj.sollumtype == 'Clip Dictionary':
            return obj

    return None

def write_ycd_xml(context, filepath):

    clipDictObj = findClipDictionary(context)

    if clipDictObj is None:
        return "Clip Dictionary not found!"

    clipDict = ClipDictionary.fromObject(clipDictObj)
    clipDictNode = clipDict.toXml()

    print("*** Complete ***")

    xmlstr = prettify(clipDictNode)

    with open(filepath, "w") as f:
        f.write(xmlstr)
        return "Sollumz Clip Dictionary was succesfully exported to " + filepath


class ExportYcdXml(Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ycd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ycd"

    # ImportHelper mixin class uses this
    filename_ext = ".ycd.xml"

    def execute(self, context):
        write_ycd_xml(context, self.filepath) # pylint: disable=no-member

        return {'FINISHED'}

# Only needed if you want to add into a dynamic menu
def menu_func_export_ycd(self, context):  # pylint: disable=unused-argument
    self.layout.operator(ExportYcdXml.bl_idname, text="Ycd Xml Export (.ycd.xml)")

def register():
    bpy.utils.register_class(ExportYcdXml)
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export_ycd)

def unregister():
    bpy.utils.unregister_class(ExportYcdXml)
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export_ycd)
