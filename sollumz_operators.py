import bpy
import traceback, os
from Sollumz.sollumz_properties import ObjectType, BoundType
#from Sollumz.resources.drawable import YDR, YDD
from Sollumz.resources.bound import YBN
from Sollumz.ybn.ybnimport import composite_to_obj
from Sollumz.ybn.ybnexport import ybn_from_object, NoGeometryError
from Sollumz.ydr.ydrexport import drawable_from_object
from Sollumz.ydr.ydrimport import drawable_to_obj
from Sollumz.ydd.yddimport import drawable_dict_to_obj
from Sollumz.ydd.yddexport import drawable_dict_from_object
from bpy_extras.io_utils import ImportHelper

class ImportYbnXml(bpy.types.Operator, ImportHelper):
    """Imports .ybn.xml file exported from codewalker."""
    bl_idname = "sollumz.importybn" 
    bl_label = "Import ybn.xml"
    filename_ext = ".ybn.xml"
    bl_options = {'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.ybn.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def execute(self, context):
        
        try:
            ybn_xml = YBN.from_xml_file(self.filepath)
            composite_to_obj(ybn_xml.bounds, os.path.basename(self.filepath.replace('.ybn.xml', '')))
            self.report({'INFO'}, 'YBN Successfully imported.')
        except Exception as e:
            #self.report({'ERROR'}, f"YBN failed to import: {e}")
            self.report({'ERROR'}, traceback.format_exc())
            
        return {'FINISHED'}

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
        
        try:
            ydr_xml = YDR.from_xml_file(self.filepath)
            drawable_to_obj(ydr_xml, self.filepath, os.path.basename(self.filepath.replace(self.filename_ext, '')))
            self.report({'INFO'}, 'YDR Successfully imported.')
        except Exception as e:
            self.report({'ERROR'}, traceback.format_exc())

        return {'FINISHED'}

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
        
        try:
            ydd_xml = YDD.from_xml_file(self.filepath)
            drawable_dict_to_obj(ydd_xml, self.filepath)
            self.report({'INFO'}, 'YDD Successfully imported.')
        except Exception as e:
            self.report({'ERROR'}, traceback.format_exc())

        return {'FINISHED'}

class SollumzExportHelper():
    bl_options = {"REGISTER"}
    
    filename_ext = ""

    directory : bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
    )

    export_type : bpy.props.EnumProperty(
        items = [("export_all", "Export All", "This option lets you export all objects in the scene of your choosen export type to be exported."),
        ("export_selected", "Export Selected", "This option lets you export the selected objects of your choosen export type to be exported."),
        ("export_first", "Export First", "This option lets you export the first found object of your choosen export type to be exported.")],
        description = "The method in which you want to export your scene.",
        name = "Export Type",
        default = "export_first"
    )

    def get_filepath(self, obj):
        return f"{self.directory}\{obj.name}{self.filename_ext}"
    
    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def export_ybn(self, obj):
        try:
            ybn_from_object(obj).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'YBN Successfully exported.')
        except NoGeometryError:
            self.report({'WARNING'}, f'{obj.name} was not exported: {NoGeometryError.message}')
        except:
            self.report({'ERROR'}, traceback.format_exc())

    def export_ydr(self, obj):
        try:
            drawable_from_object(obj).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'Ydr Successfully exported.')
        except Exception as e:
            #self.report({'ERROR'}, f"Composite {obj.name} failed to export: {e}")
            self.report({'ERROR'}, traceback.format_exc())

    def export_ydd(self, obj):
        try:
            drawable_dict_from_object(obj).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'Ydd Successfully exported.')
        except Exception as e:
            #self.report({'ERROR'}, f"Composite {obj.name} failed to export: {e}")
            self.report({'ERROR'}, traceback.format_exc())

    def export(self, context):
        if(self.export_type == "export_all"):
            self.export_all(context)
        elif(self.export_type == "export_selected"):
            self.export_selected(context)
        else:
            self.export_first(context)

    def export_all(self, context):
        objects = context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == BoundType.COMPOSITE and obj.enable_export:
                    found = True
                    self.export_ybn(obj)
                if obj.sollum_type == ObjectType.DRAWABLE and obj.enable_export:
                    found = True
                    self.export_ydr(obj)
                if obj.sollum_type == ObjectType.DRAWABLE_DICTIONARY and obj.enable_export:
                    found = True
                    self.export_ydd(obj)

        if not found:
            self.report({'INFO'}, "No bound object types in scene for Sollumz export")

    def export_selected(self, context):
        objects = context.selected_objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == BoundType.COMPOSITE and obj.enable_export:
                    found = True
                    self.export_ybn(obj)
                if obj.sollum_type == ObjectType.DRAWABLE and obj.enable_export:
                    found = True
                    self.export_ydr(obj)
                if obj.sollum_type == ObjectType.DRAWABLE_DICTIONARY and obj.enable_export:
                    found = True
                    self.export_ydd(obj)

        if not found:
            self.report({'INFO'}, "No bound object types in scene for Sollumz export")

    def export_first(self, context):
        objects = context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == BoundType.COMPOSITE and obj.enable_export:
                    found = True
                    self.export_ybn(obj)
                    break
                if obj.sollum_type == ObjectType.DRAWABLE and obj.enable_export:
                    found = True
                    self.export_ydr(obj)
                    break
                if obj.sollum_type == ObjectType.DRAWABLE_DICTIONARY and obj.enable_export:
                    found = True
                    self.export_ydd(obj)
                    break

        if not found:
            self.report({'INFO'}, "No bound object types in scene for Sollumz export")

class ExportYbnXml(bpy.types.Operator, SollumzExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ybn" 
    bl_label = "Export Ybn Xml (.ybn.xml)"
    
    filename_ext = '.ybn.xml'

    def execute(self, context):

        self.export(context)

        return {'FINISHED'}
    
class ExportYdrXml(bpy.types.Operator, SollumzExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ydr" 
    bl_label = "Export Ydr Xml (.ydr.xml)"

    filename_ext = ".ydr.xml"

    def execute(self, context):

        self.export(context)

        return {'FINISHED'}

class ExportYddXml(bpy.types.Operator, SollumzExportHelper):
    """This appears in the tooltip of the operator and in the generated docs"""
    bl_idname = "exportxml.ydd" 
    bl_label = "Export Ydd Xml (.ydd.xml)"

    filename_ext = ".ydd.xml"

    def execute(self, context):

        self.export(context)

        return {'FINISHED'}

def ydd_menu_func_import(self, context):
    self.layout.operator(ImportYddXml.bl_idname, text="Import .ydd.xml")

def ybn_menu_func_import(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Import .ybn.xml")

def ydr_menu_func_import(self, context):
    self.layout.operator(ImportYdrXml.bl_idname, text="Import .ydr.xml")

def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname, text="Export .ybn.xml")

def ydr_menu_func_export(self, context):
    self.layout.operator(ExportYdrXml.bl_idname, text="Export .ydr.xml")

def ydd_menu_func_export(self, context):
    self.layout.operator(ExportYddXml.bl_idname, text="Export .ydd.xml")

def register():
    bpy.types.TOPBAR_MT_file_import.append(ydr_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(ydd_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(ybn_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(ydr_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(ydd_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(ybn_menu_func_export)
    

def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(ydr_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(ydd_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(ybn_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(ydr_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(ydd_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(ybn_menu_func_export)
    