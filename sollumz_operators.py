import bpy
import traceback, os
from Sollumz.sollumz_properties import DrawableType, BoundType, LodType, SOLLUMZ_UI_NAMES
from Sollumz.resources.drawable import YDR, YDD
from Sollumz.resources.fragment import YFT
from Sollumz.resources.bound import YBN
from Sollumz.resources.ymap import YMAP, EntityItem
from Sollumz.ybn.ybnimport import composite_to_obj
from Sollumz.ybn.ybnexport import bounds_from_object, NoGeometryError
from Sollumz.ydr.ydrexport import drawable_from_object
from Sollumz.ydr.ydrimport import drawable_to_obj
from Sollumz.yft.yftimport import fragment_to_obj
from Sollumz.ydd.yddimport import drawable_dict_to_obj
from Sollumz.ydd.yddexport import drawable_dict_from_object
from bpy_extras.io_utils import ImportHelper, ExportHelper

class SollumzImportHelper(ImportHelper):
    bl_options = {'REGISTER'}
    filename_ext = None

    import_directory : bpy.props.BoolProperty(
        name = "Import Directory",
        default = False,
    )

    def execute(self, context):
        if(self.import_directory):
            folderpath = os.path.dirname(self.filepath)
            for file in os.listdir(folderpath):
                 if file.endswith(self.filename_ext):
                    filepath = os.path.join(folderpath, file)
                    self.importfile(filepath)
        else:
            self.importfile(self.filepath)

        return {'FINISHED'}

class ImportYmapXml(bpy.types.Operator, SollumzImportHelper):
    """Imports .ymap.xml file exported from codewalker."""
    bl_idname = "sollumz.importymap" 
    bl_label = "Import ymap.xml"
    filename_ext = ".ymap.xml"
    bl_options = {'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.ymap.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def importfile(self, filepath):
        ymap = YMAP.from_xml_file(filepath)

        names = []

        for obj in bpy.context.collection.objects:
            for entity in ymap.entities:
                if entity.archetype_name not in names:
                    names.append(entity.archetype_name)
                if(entity.archetype_name == obj.name):
                    obj.location = entity.position

        return {'FINISHED'}

class ImportYbnXml(bpy.types.Operator, SollumzImportHelper):
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
    
    def importfile(self, context):
        try:
            ybn_xml = YBN.from_xml_file(self.filepath)
            composite_to_obj(ybn_xml, os.path.basename(self.filepath.replace('.ybn.xml', '')))
            self.report({'INFO'}, 'YBN Successfully imported.')
        except Exception as e:
            #self.report({'ERROR'}, f"YBN failed to import: {e}")
            self.report({'ERROR'}, traceback.format_exc())

class ImportYdrXml(bpy.types.Operator, SollumzImportHelper):
    """Imports .ydr.xml file exported from codewalker."""
    bl_idname = "sollumz.importydr" 
    bl_label = "Import ydr.xml"
    filename_ext = ".ydr.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ydr.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def importfile(self, filepath):
        try:
            ydr_xml = YDR.from_xml_file(filepath)
            drawable_to_obj(ydr_xml, filepath, os.path.basename(filepath.replace(self.filename_ext, '')))
            self.report({'INFO'}, 'YDR Successfully imported.')
        except Exception as e:
            self.report({'ERROR'}, traceback.format_exc())

class ImportYftXml(bpy.types.Operator, SollumzImportHelper):
    """Imports .yft.xml file exported from codewalker."""
    bl_idname = "sollumz.importyft" 
    bl_label = "Import yft.xml"
    filename_ext = ".yft.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.yft.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def importfile(self, filepath):
        try:
            yft_xml = YFT.from_xml_file(filepath)
            fragment_to_obj(yft_xml, filepath)
            self.report({'INFO'}, 'YFT Successfully imported.')
        except Exception as e:
            self.report({'ERROR'}, traceback.format_exc())

class ImportYddXml(bpy.types.Operator, SollumzImportHelper):
    """Imports .ydd.xml file exported from codewalker."""
    bl_idname = "sollumz.importydd" 
    bl_label = "Import ydd.xml"
    filename_ext = ".ydd.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ydd.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def importfile(self, context):
        try:
            ydd_xml = YDD.from_xml_file(self.filepath)
            drawable_dict_to_obj(ydd_xml, self.filepath)
            self.report({'INFO'}, 'YDD Successfully imported.')
        except Exception as e:
            self.report({'ERROR'}, traceback.format_exc())


class SollumzExportHelper():
    bl_options = {"REGISTER"}
    sollum_type = None
    filename_ext = None

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
        default = "export_all"
    )

    def get_filepath(self, obj):
        return f"{self.directory}\{obj.name}{self.filename_ext}"
    

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


    def no_objects_message(self):
        return f"No {SOLLUMZ_UI_NAMES[self.sollum_type]} object types in scene for Sollumz export"

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
                if obj.sollum_type == self.sollum_type:
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
                if obj.sollum_type == self.sollum_type:
                    found = True
                    self.export(obj)

        if not found:
            self.report({'INFO'}, self.no_objects_message())

    def export_first(self, context):
        objects = context.collection.objects

        found = False
        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == self.sollum_type:
                    found = True
                    self.export(obj)
                    break

        if not found:
            self.report({'INFO'}, self.no_objects_message())

class ExportYmapXml(bpy.types.Operator, ExportHelper):
    """Exports .ymap.xml file exported from codewalker."""
    bl_idname = "sollumz.exportymap" 
    bl_label = "Export ymap.xml"
    filename_ext = ".ymap.xml"
    bl_options = {'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.ymap.xml",
        options={'HIDDEN'},
        maxlen=255,  
    )

    def entity_from_obj(obj):
        ent = EntityItem()

    def execute(self, context):



        return {'FINISHED'}

class ExportYbnXml(bpy.types.Operator, SollumzExportHelper):
    """Export static collisions (.ybn)"""
    bl_idname = "exportxml.ybn" 
    bl_label = "Export Ybn Xml (.ybn.xml)"
    sollum_type = BoundType.COMPOSITE.value
    
    filename_ext = '.ybn.xml'

    def export(self, obj):
        try:
            bounds_from_object(obj).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'YBN Successfully exported.')
        except NoGeometryError:
            self.report({'WARNING'}, f'{obj.name} was not exported: {NoGeometryError.message}')
        except:
            self.report({'ERROR'}, traceback.format_exc())


class ExportYdrXml(bpy.types.Operator, SollumzExportHelper):
    """Export drawable (.ydr)"""
    bl_idname = "exportxml.ydr"
    bl_label = "Export Ydr Xml (.ydr.xml)"
    sollum_type = DrawableType.DRAWABLE

    filename_ext = ".ydr.xml"

    def export(self, obj):
        try:
            drawable_from_object(obj, None, self.directory).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'YDR Successfully exported.')
        except:
            self.report({'ERROR'}, traceback.format_exc())


class ExportYddXml(bpy.types.Operator, SollumzExportHelper):
    """Export drawable dictionary (.ydd)"""
    bl_idname = "exportxml.ydd" 
    bl_label = "Export Ydd Xml (.ydd.xml)"
    sollum_type = DrawableType.DRAWABLE_DICTIONARY

    filename_ext = ".ydd.xml"

    def export(self, obj):
        try:
            drawable_dict_from_object(obj).write_xml(self.get_filepath(obj))
            self.report({'INFO'}, 'Ydd Successfully exported.')
        except:
            self.report({'ERROR'}, traceback.format_exc())

def ydr_menu_func_import(self, context):
    self.layout.operator(ImportYdrXml.bl_idname, text="Codewalker XML (.ydr.xml)")

def yft_menu_func_import(self, context):
    self.layout.operator(ImportYftXml.bl_idname, text="Codewalker XML (.yft.xml)")

def ybn_menu_func_import(self, context):
    self.layout.operator(ImportYbnXml.bl_idname, text="Codewalker XML (.ybn.xml)")

def ydd_menu_func_import(self, context):
    self.layout.operator(ImportYddXml.bl_idname, text="Codewalker XML (.ydd.xml)")

def ydr_menu_func_export(self, context):
    self.layout.operator(ExportYdrXml.bl_idname, text="Codewalker XML (.ydr.xml)")

def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname, text="Codewalker XML (.ybn.xml)")

def ydd_menu_func_export(self, context):
    self.layout.operator(ExportYddXml.bl_idname, text="Codewalker XML (.ydd.xml)")

def register():
    bpy.types.TOPBAR_MT_file_import.append(ydr_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(yft_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(ybn_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.append(ydd_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(ydr_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(ybn_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(ydd_menu_func_export)
    
def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(ydr_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(yft_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(ybn_menu_func_import)
    bpy.types.TOPBAR_MT_file_import.remove(ydd_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(ydr_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(ybn_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(ydd_menu_func_export)
    