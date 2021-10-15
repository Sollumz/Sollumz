import bpy
from bpy_extras.io_utils import ExportHelper
from Sollumz.resources.drawable import *
from Sollumz.resources.shader import ShaderManager
import os, sys, traceback
from Sollumz.meshhelper import *
from Sollumz.tools.utils import *
from Sollumz.sollumz_operators import SollumzExportHelper
from Sollumz.ydr.ydrexport import drawable_from_object
import Sollumz.tools.jenkhash as Jenkhash

def get_hash(obj):
    return Jenkhash.Generate(obj.name.split(".")[0])

def drawable_dict_from_object(obj):

    drawable_dict = DrawableDictionary()

    bones = None
    for child in obj.children:
        if child.sollum_type == "sollumz_drawable" and child.type == 'ARMATURE' and len(child.pose.bones) > 0:
            bones = child.pose.bones
            break

    for child in obj.children:
        if child.sollum_type == "sollumz_drawable":
            drawable = drawable_from_object(child, bones)
            drawable_dict.value.append(drawable)

    drawable_dict.value.sort(key=get_hash)

    return drawable_dict

class ExportYddXml(bpy.types.Operator, SollumzExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ydd"  # important since its how bpy.ops.import_test.some_data is constructed
    bl_label = "Export Ydd Xml (.ydd.xml)"

    filename_ext = ".ydd.xml"

    def execute(self, context):

        objects = bpy.context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == "sollumz_drawable_dictionary" and obj.enable_export:
                    found = True
                    try:
                        drawable_dict_from_object(obj).write_xml(self.get_filepath(obj))
                        self.report({'INFO'}, 'Ydd Successfully exported.')
                    except Exception as e:
                        #self.report({'ERROR'}, f"Composite {obj.name} failed to export: {e}")
                        self.report({'ERROR'}, traceback.format_exc())
        
        if not found:
            self.report({'INFO'}, "No bound object types in scene for Sollumz export")

        return {'FINISHED'}

def ydd_menu_func_export(self, context):
    self.layout.operator(ExportYddXml.bl_idname, text="Export .ydd.xml")

def register():
    bpy.types.TOPBAR_MT_file_export.append(ydd_menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(ydd_menu_func_export)