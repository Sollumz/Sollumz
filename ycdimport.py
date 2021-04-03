import xml.etree.ElementTree as ET

import bpy
from bpy_extras.io_utils import ImportHelper
from bpy.types import Operator

from .formats.ycd.ClipDictionary import ClipDictionary

class ImportYcdXml(Operator, ImportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "importxml.ycd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Import Ycd"

    # ImportHelper mixin class uses this
    filename_ext = ".ycd.xml"

    def execute(self, context):
        tree = ET.parse(self.filepath) # pylint: disable=no-member
        root = tree.getroot()

        clipDict = ClipDictionary.fromXml(root)
        print('Clip dictionary parsed')
        clipDict.toObject()
        print('Clip dictionary import finished')

        return {'FINISHED'}

# Only needed if you want to add into a dynamic menu
def menu_func_import_ycd(self, context):  # pylint: disable=unused-argument
    self.layout.operator(ImportYcdXml.bl_idname, text="Ycd (.ycd.xml)")

def register():
    bpy.utils.register_class(ImportYcdXml)
    bpy.types.TOPBAR_MT_file_import.append(menu_func_import_ycd)

def unregister():
    bpy.utils.unregister_class(ImportYcdXml)
    bpy.types.TOPBAR_MT_file_import.remove(menu_func_import_ycd)
