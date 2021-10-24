import bpy
import traceback
import os
import pathlib
from Sollumz.sollumz_properties import DrawableType, BoundType, SOLLUMZ_UI_NAMES
from Sollumz.resources.drawable import YDR, YDD
from Sollumz.resources.fragment import YFT
from Sollumz.resources.bound import YBN
from Sollumz.resources.ymap import YMAP, EntityItem, CMapData
from Sollumz.ybn.ybnimport import composite_to_obj
from Sollumz.ybn.ybnexport import bounds_from_object, NoGeometryError
from Sollumz.ydr.ydrexport import drawable_from_object
from Sollumz.ydr.ydrimport import drawable_to_obj
from Sollumz.yft.yftimport import fragment_to_obj
from Sollumz.ydd.yddimport import drawable_dict_to_obj
from Sollumz.ydd.yddexport import drawable_dict_from_object
from Sollumz.meshhelper import *
from Sollumz.tools.utils import VectorHelper
from bpy_extras.io_utils import ImportHelper, ExportHelper


class SollumzImporter():

    def import_ydr(filepath):
        try:
            ydr_xml = YDR.from_xml_file(filepath)
            drawable_to_obj(ydr_xml, filepath, os.path.basename(
                filepath.replace(".ydr.xml", '')))
            # self.report({'INFO'}, 'YDR Successfully imported.')
        except Exception as e:
            print(e)
            # self.report({'ERROR'}, traceback.format_exc())

    def import_ybn(filepath):
        try:
            ybn_xml = YBN.from_xml_file(filepath)
            composite_to_obj(ybn_xml, os.path.basename(
                filepath.replace('.ybn.xml', '')))
            # self.report({'INFO'}, 'YBN Successfully imported.')
        except Exception as e:
            print(e)
            # self.report({'ERROR'}, traceback.format_exc())

    def import_yft(filepath):
        try:
            yft_xml = YFT.from_xml_file(filepath)
            fragment_to_obj(yft_xml, filepath)
            # self.report({'INFO'}, 'YFT Successfully imported.')
        except Exception as e:
            print(e)
            # self.report({'ERROR'}, traceback.format_exc())

    def import_ydd(filepath):
        try:
            ydd_xml = YDD.from_xml_file(filepath)
            drawable_dict_to_obj(ydd_xml, filepath)
            # self.report({'INFO'}, 'YDD Successfully imported.')
        except Exception as e:
            print(e)
            # self.report({'ERROR'}, traceback.format_exc())


class SollumzImportHelper(bpy.types.Operator, ImportHelper):
    """Imports xml files exported by codewalker."""
    bl_idname = "sollumz.import"
    bl_label = "Import Codewalker XML"
    bl_options = {'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default="*.ydr.xml;*.ydd.xml;*.yft.xml;*.ybn.xml",
        options={'HIDDEN'},
        maxlen=255,
    )

    filename_exts = [".ydr.xml", ".ydd.xml", ".yft.xml", ".ybn.xml"]

    import_directory: bpy.props.BoolProperty(
        name="Import Directory",
        default=False,
    )

    def import_file(self, filepath, ext):
        if "ydr" in ext:
            SollumzImporter.import_ydr(filepath)
        elif "ydd" in ext:
            SollumzImporter.import_ydd(filepath)
        elif "yft" in ext:
            SollumzImporter.import_yft(filepath)
        elif "ybn" in ext:
            SollumzImporter.import_ybn(filepath)
        else:
            print(f"Error unknown filetype: {filepath}")  # should never happen

    def execute(self, context):

        filepaths = []

        if(self.import_directory):
            folderpath = os.path.dirname(self.filepath)
            for file in os.listdir(folderpath):
                ext = ''.join(pathlib.Path(file).suffixes)
                if ext in self.filename_exts:
                    filepath = os.path.join(folderpath, file)
                    self.import_file(filepath, ext)
        else:
            ext = ''.join(pathlib.Path(self.filepath).suffixes)
            self.import_file(self.filepath, ext)

        return {'FINISHED'}


class ImportYmapXml(bpy.types.Operator, ImportHelper):
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

    def apply_entity_properties(self, obj, entity):
        obj.entity_properties.archetype_name = entity.archetype_name
        obj.entity_properties.flags = entity.flags
        obj.entity_properties.guid = entity.guid
        obj.entity_properties.position = entity.position
        obj.entity_properties.rotation = entity.rotation
        obj.entity_properties.scale_xy = entity.scale_xy
        obj.entity_properties.scale_z = entity.scale_z
        obj.entity_properties.parent_index = entity.parent_index
        obj.entity_properties.lod_dist = entity.lod_dist
        obj.entity_properties.child_lod_dist = entity.child_lod_dist
        obj.entity_properties.lod_level = "sollumz_" + entity.lod_level.lower()
        obj.entity_properties.num_children = entity.num_children
        obj.entity_properties.priority_level = "sollumz_" + entity.priority_level.lower()
        obj.entity_properties.ambient_occlusion_multiplier = entity.ambient_occlusion_multiplier
        obj.entity_properties.artificial_ambient_occlusion = entity.artificial_ambient_occlusion
        obj.entity_properties.tint_value = entity.tint_value

    def execute(self, context):

        ymap = YMAP.from_xml_file(self.filepath)

        for obj in bpy.context.collection.objects:
            for entity in ymap.entities:
                if(entity.archetype_name == obj.name):
                    obj.location = entity.position
                    self.apply_entity_properties(obj, entity)

        return {'FINISHED'}


class SollumzExportHelper():
    bl_options = {"REGISTER"}
    sollum_type = None
    filename_ext = None

    # Define this to tell 'fileselect_add' that we want a directoy
    directory: bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
    )

    export_type: bpy.props.EnumProperty(
        items=[("export_all", "Export All", "This option lets you export all objects in the scene of your choosen export type to be exported."),
               ("export_selected", "Export Selected",
                "This option lets you export the selected objects of your choosen export type to be exported."),
               ("export_first", "Export First", "This option lets you export the first found object of your choosen export type to be exported.")],
        description="The method in which you want to export your scene.",
        name="Export Type",
        default="export_all"
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

    def entity_from_obj(self, obj):
        entity = EntityItem()

        # entity.archetype_name = obj.entity_properties.archetype_name
        entity.archetype_name = obj.name
        entity.flags = int(obj.entity_properties.flags)
        entity.guid = int(obj.entity_properties.guid)
        # entity.position = obj.entity_properties.position
        entity.position = obj.location
        # entity.rotation = obj.entity_properties.rotation
        entity.rotation = obj.rotation_quaternion
        # entity.scale_xy = obj.entity_properties.scale_xy
        entity.scale_xy = 1
        # entity.scale_z = obj.entity_properties.scale_z
        entity.scale_z = 1
        entity.parent_index = int(obj.entity_properties.parent_index)
        entity.lod_dist = obj.entity_properties.lod_dist
        entity.child_lod_dist = obj.entity_properties.child_lod_dist
        entity.lod_level = obj.entity_properties.lod_level.upper().replace("SOLLUMZ_", "")
        entity.num_children = int(obj.entity_properties.num_children)
        entity.priority_level = obj.entity_properties.priority_level.upper().replace("SOLLUMZ_", "")
        entity.ambient_occlusion_multiplier = int(
            obj.entity_properties.ambient_occlusion_multiplier)
        entity.artificial_ambient_occlusion = int(
            obj.entity_properties.artificial_ambient_occlusion)
        entity.tint_value = int(obj.entity_properties.tint_value)

        return entity

    def calculate_extents(self, objs):
        emin = Vector((0, 0, 0))
        emax = Vector((0, 0, 0))
        smin = Vector((0, 0, 0))
        smax = Vector((0, 0, 0))

        for obj in objs:
            loddist = obj.entity_properties.lod_dist
            radius = get_obj_radius(obj)

            bbmin = VectorHelper.subtract_from_vector(obj.location, radius)
            bbmax = VectorHelper.add_to_vector(obj.location, radius)
            sbmin = VectorHelper.subtract_from_vector(bbmin, loddist)
            sbmax = VectorHelper.add_to_vector(bbmax, loddist)

            emin = VectorHelper.get_min_vector(emin, bbmin)
            emax = VectorHelper.get_max_vector(emax, bbmax)
            smin = VectorHelper.get_min_vector(smin, sbmin)
            smax = VectorHelper.get_max_vector(smax, sbmax)

        return emin, emax, smin, smax

    def execute(self, context):

        try:
            ymap = CMapData()
            ymap.name = os.path.splitext(
                os.path.basename(context.blend_data.filepath))[0]  # use blender files name ? idk
            ymap.parent = ""  # add a property ? if so how?
            ymap.flags = 0
            ymap.content_flags = 0

            objs = []
            for obj in context.collection.objects:
                if(obj.sollum_type == DrawableType.DRAWABLE):
                    ent = self.entity_from_obj(obj)
                    ymap.entities.append(ent)
                    objs.append(obj)

            emin, emax, smin, smax = self.calculate_extents(objs)
            ymap.streaming_extents_min = emin
            ymap.streaming_extents_max = emax
            ymap.entities_extents_min = smin
            ymap.entities_extents_max = smax

            ymap.write_xml(self.filepath)

            self.report({'INFO'}, 'YMAP Successfully exported.')
        except:
            self.report({'INFO'}, 'YMAP failed to export.')

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
            self.report(
                {'WARNING'}, f'{obj.name} was not exported: {NoGeometryError.message}')
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
            drawable_from_object(obj, None, self.directory).write_xml(
                self.get_filepath(obj))
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


def sollumz_menu_func_import(self, context):
    self.layout.operator(SollumzImportHelper.bl_idname,
                         text="Codewalker XML (.ydr.xml, .ydd.xml, .yft.xml, .ybn.xml)")


def ydr_menu_func_export(self, context):
    self.layout.operator(ExportYdrXml.bl_idname,
                         text="Codewalker XML (.ydr.xml)")


def ybn_menu_func_export(self, context):
    self.layout.operator(ExportYbnXml.bl_idname,
                         text="Codewalker XML (.ybn.xml)")


def ydd_menu_func_export(self, context):
    self.layout.operator(ExportYddXml.bl_idname,
                         text="Codewalker XML (.ydd.xml)")


def register():
    bpy.types.TOPBAR_MT_file_import.append(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(ydr_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(ybn_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.append(ydd_menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(ydr_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(ybn_menu_func_export)
    bpy.types.TOPBAR_MT_file_export.remove(ydd_menu_func_export)
