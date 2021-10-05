import os
import bpy
from bpy_extras.io_utils import ImportHelper
from Sollumz.resources.drawable import *


class ImportYdrXml(bpy.types.Operator, ImportHelper):
    """Imports .ydr.xml file exported from codewalker."""
    bl_idname = "sollumz.importydr" 
    bl_label = "Import ydr.xml"
    filename_ext = ".ydr.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ydr.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def execute(self, context):
        
        #try:
        ydr_xml = Drawable.from_xml_file(self.filepath)
            #ybn_obj = composite_to_obj(ybn_xml.bounds, os.path.basename(self.filepath))
            #bpy.context.collection.objects.link(ybn_obj)
            #self.report({'INFO'}, 'YDR Successfully imported.')
        #except Exception as e:
            #self.report({'ERROR'}, f"YDR failed to import: {e}")

        print(ydr_xml.lod_dist_high)

        return {'FINISHED'}

def ydr_menu_func_import(self, context):
    self.layout.operator(ImportYdrXml.bl_idname, text="Import .ydr.xml")

def register():
    bpy.types.TOPBAR_MT_file_import.append(ydr_menu_func_import)

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(ydr_menu_func_import)
