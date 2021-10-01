import os
import bpy
from bpy_extras.io_utils import ImportHelper
from .resources.bound import YBN

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
        
        ybn = YBN.from_xml_file(self.filepath)
        ybn.write_xml('./test.ybn.xml')

        print("")
        print("IMPORTING YBN")
        print("")

        ybn.to_obj(os.path.basename(self.filepath))

        return {'FINISHED'}

def ybn_menu_func_import(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Import .ybn.xml")
