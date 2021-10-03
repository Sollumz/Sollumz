import os
import bpy
from bpy_extras.io_utils import ImportHelper
from Sollumz.codewalker_xml.bound_xml import YBN_XML
from Sollumz.game_objects.bound import YBN

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
        
        ybn_xml = YBN_XML.from_xml_file(self.filepath)
        ybn_obj = YBN(ybn_xml).to_obj(os.path.basename(self.filepath))
        bpy.context.collection.objects.link(ybn_obj)

        return {'FINISHED'}

def ybn_menu_func_import(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Import .ybn.xml")
