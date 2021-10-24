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

    @staticmethod
    def import_ydr(filepath):
        try:
            ydr_xml = YDR.from_xml_file(filepath)
            drawable_to_obj(ydr_xml, filepath, os.path.basename(
                filepath.replace(YDR.file_extension, '')))
            # self.report({'INFO'}, 'YDR Successfully imported.')
        except Exception as e:
            print(e)
            # self.report({'ERROR'}, traceback.format_exc())

    @staticmethod
    def import_ybn(filepath):
        try:
            ybn_xml = YBN.from_xml_file(filepath)
            composite_to_obj(ybn_xml, os.path.basename(
                filepath.replace(YBN.file_extension, '')))
            # self.report({'INFO'}, 'YBN Successfully imported.')
        except Exception as e:
            print(e)
            # self.report({'ERROR'}, traceback.format_exc())

    @staticmethod
    def import_yft(filepath):
        try:
            yft_xml = YFT.from_xml_file(filepath)
            fragment_to_obj(yft_xml, filepath)
            # self.report({'INFO'}, 'YFT Successfully imported.')
        except Exception as e:
            print(e)
            # self.report({'ERROR'}, traceback.format_exc())

    @staticmethod
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
    # bl_options = {'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};",
        options={'HIDDEN'},
        maxlen=255,
    )

    filename_exts = [YDR.file_extension, YDD.file_extension,
                     YFT.file_extension, YBN.file_extension]

    import_directory: bpy.props.BoolProperty(
        name="Import Directory",
        default=False,
    )

    def import_file(self, filepath, ext):
        if ext == YDR.file_extension:
            SollumzImporter.import_ydr(filepath)
        elif ext == YDD.file_extension:
            SollumzImporter.import_ydd(filepath)
        elif ext == YFT.file_extension:
            SollumzImporter.import_yft(filepath)
        elif ext == YBN.file_extension:
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


class SollumzExporter():

    @staticmethod
    def export_ydr(obj, filepath):
        try:
            drawable_from_object(obj, None, "").write_xml(filepath)
            # self.report({'INFO'}, 'YDR Successfully exported.')
        except:
            print()
            # self.report({'ERROR'}, traceback.format_exc())

    @staticmethod
    def export_ydd(obj, filepath):
        try:
            drawable_dict_from_object(obj).write_xml(filepath)
            # self.report({'INFO'}, 'Ydd Successfully exported.')
        except:
            print()
            # self.report({'ERROR'}, traceback.format_exc())

    @staticmethod
    def export_yft(obj, filepath):
        raise NotImplementedError

    @staticmethod
    def export_ybn(obj, filepath):
        try:
            bounds_from_object(obj).write_xml(filepath)
            # self.report({'INFO'}, 'YBN Successfully exported.')
        except:
            print()
            # self.report({'ERROR'}, traceback.format_exc())


class SollumzExportHelper(bpy.types.Operator, ExportHelper):
    """Exports codewalker xml files."""
    bl_idname = "sollumz.export"
    bl_label = "Export Codewalker XML"
    # bl_options = {'UNDO'}

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};",
        options={'HIDDEN'},
        maxlen=255,
    )

    export_type: bpy.props.EnumProperty(
        items=[("export_all", "Export All", "This option lets you export all objects in the scene of your choosen export type to be exported."),
               ("export_selected", "Export Selected",
                "This option lets you export the selected objects of your choosen export type to be exported.")],
        description="The method in which you want to export your scene.",
        name="Export Type",
        default="export_selected"
    )

    def get_directory(self):
        return os.path.dirname(self.filepath)

    def get_filepath(self, filename):
        return os.path.join(self.get_directory(), filename)

    def execute(self, context):
        objects = []

        if(self.export_type == "export_all"):
            objects = context.collection.objects
        else:
            objects = context.selected_objects

        if len(objects) > 0:
            for obj in objects:
                if obj.sollum_type == DrawableType.DRAWABLE:
                    SollumzExporter.export_ydr(
                        obj, self.get_filepath(obj.name + YDR.file_extension))
                elif obj.sollum_type == DrawableType.DRAWABLE_DICTIONARY:
                    SollumzExporter.export_ydd(
                        obj, self.get_filepath(obj.name + YDD.file_extension))
                elif obj.sollum_type == DrawableType.FRAGMENT:
                    SollumzExporter.export_yft(
                        obj, self.get_filepath(obj.name + YFT.file_extension))
                elif obj.sollum_type == BoundType.COMPOSITE:
                    SollumzExporter.export_ybn(
                        obj, self.get_filepath(obj.name + YBN.file_extension))

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


def sollumz_menu_func_import(self, context):
    self.layout.operator(SollumzImportHelper.bl_idname,
                         text=f"Codewalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension})")


def sollumz_menu_func_export(self, context):
    self.layout.operator(SollumzExportHelper.bl_idname,
                         text=f"Codewalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension})")


def register():
    bpy.types.TOPBAR_MT_file_import.append(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(sollumz_menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(sollumz_menu_func_export)
