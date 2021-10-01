import bpy
from bpy_extras.io_utils import ExportHelper
import os, sys
sys.path.append(os.path.dirname(__file__))
from resources.bound import YBN

class ExportYbnXml(bpy.types.Operator, ExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ybn"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ybn Xml (.ybn.xml)"

    # ExportHelper mixin class uses this
    filename_ext = ".ybn.xml"
    check_extension = False

    def execute(self, context):

        objects = bpy.context.collection.objects

        if(len(objects) == 0):
            return "No objects in scene for Sollumz export"

        for obj in objects:
            if(obj.sollum_type == "sollumz_bound_composite"):
                YBN().load_obj(obj).write_xml(self.filepath)

        return {'FINISHED'}

def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname, text="Export .ybn.xml")