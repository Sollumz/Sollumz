import bpy
import traceback, os
from Sollumz.sollumz_properties import ObjectType, BoundType
from Sollumz.resources.drawable import YDR, YDD
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
    sollum_type = bpy.props.StringProperty(name='Sollum Type')
    filename_ext = bpy.props.StringProperty(name='File Extension', description='File extension to be appended to exported file')

    # Define this to tell 'fileselect_add' that we want a directoy
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


    # def export_ydr(self, obj):
    #     try:
    #         drawable_from_object(obj).write_xml(self.get_filepath(obj))
    #         self.report({'INFO'}, 'Ydr Successfully exported.')
    #     except Exception as e:
    #         #self.report({'ERROR'}, f"Composite {obj.name} failed to export: {e}")
    #         self.report({'ERROR'}, traceback.format_exc())

    # def export_ydd(self, obj):
    #     try:
    #         drawable_dict_from_object(obj).write_xml(self.get_filepath(obj))
    #         self.report({'INFO'}, 'Ydd Successfully exported.')
    #     except Exception as e:
    #         #self.report({'ERROR'}, f"Composite {obj.name} failed to export: {e}")
    #         self.report({'ERROR'}, traceback.format_exc())

    def no_objects_message(self):
        return f"No {self.sollum_type} object types in scene for Sollumz export"

    def execute(self, context):
        if(self.export_type == "export_all"):
            return self.export_all(context)
        elif(self.export_type == "export_selected"):
            self.export_selected(context)
        else:
            self.export_first(context)
        return {'CANCELLED'}


    def export_all(self, context):
        objects = context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == self.sollum_type and obj.enable_export:
                    found = True
                    self.export(obj)

        if not found:
            self.report({'INFO'}, self.no_objects_message())
            return {'CANCELLED'}
        
        return {'FINISHED'}
    

    def export_selected(self, context):
        objects = context.selected_objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == self.sollum_type and obj.enable_export:
                    found = True
                    self.export(obj)

        if not found:
            self.report({'INFO'}, self.no_objects_message())

    def export_first(self, context):
        objects = context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == self.sollum_type and obj.enable_export:
                    found = True
                    self.export(obj)
                    break

        if not found:
            self.report({'INFO'}, self.no_objects_message())


class ExportYbnXml(bpy.types.Operator, SollumzExportHelper):
    """Export static collisions (.ybn)"""
    bl_idname = "exportxml.ybn" 
    bl_label = "Export Ybn Xml (.ybn.xml)"
    sollum_type = BoundType.COMPOSITE.value
    
    filename_ext = '.ybn.xml'

    def export(self, obj):
        try:
            ybn_from_object(obj).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'YBN Successfully exported.')
        except NoGeometryError:
            self.report({'WARNING'}, f'{obj.name} was not exported: {NoGeometryError.message}')
        except:
            self.report({'ERROR'}, traceback.format_exc())


class ExportYdrXml(bpy.types.Operator, SollumzExportHelper):
    """Export drawable (.ydr)"""
    bl_idname = "exportxml.ydr"
    bl_label = "Export Ydr Xml (.ydr.xml)"
    sollum_type = ObjectType.DRAWABLE

    filename_ext = ".ydr.xml"

    def export(self, obj):
        try:
            drawable_from_object(obj).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'YDR Successfully exported.')
        except:
            self.report({'ERROR'}, traceback.format_exc())


class ExportYddXml(bpy.types.Operator, SollumzExportHelper):
    """Export drawable dictionary (.ydd)"""
    bl_idname = "exportxml.ydd" 
    bl_label = "Export Ydd Xml (.ydd.xml)"
    sollum_type = ObjectType.DRAWABLE_DICTIONARY

    filename_ext = ".ydd.xml"

    def export(self, obj):
        try:
            drawable_dict_from_object(obj).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'Ydd Successfully exported.')
        except:
            self.report({'ERROR'}, traceback.format_exc())


def ydr_menu_func_export(self, context):
    self.layout.operator(ExportYdrXml.bl_idname, text="Export .ydr.xml")

def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname, text="Export .ybn.xml")

def ydd_menu_func_export(self, context):
    self.layout.operator(ExportYddXml.bl_idname, text="Export .ydd.xml")

def register():
    bpy.types.TOPBAR_MT_file_export.append(ybn_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(ydr_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(ydd_menu_func_export)

def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(ybn_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(ydr_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(ydd_menu_func_export)