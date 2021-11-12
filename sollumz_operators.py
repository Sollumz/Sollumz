import traceback
import os
import pathlib
from abc import abstractmethod
import bpy
from .sollumz_helper import *
from .sollumz_properties import FragmentType, DrawableType, BoundType, SOLLUMZ_UI_NAMES
from .resources.drawable import YDR, YDD
from .resources.fragment import YFT
from .resources.bound import YBN
from .ydr.ydrimport import import_ydr
from .ydr.ydrexport import export_ydr
from .ydd.yddimport import import_ydd
from .ydd.yddexport import export_ydd
from .yft.yftimport import import_yft
from .yft.yftexport import export_yft
from .ybn.ybnimport import import_ybn
from .ybn.ybnexport import export_ybn
from .resources.ymap import YMAP, EntityItem, CMapData
from .tools.meshhelper import *
from .tools.utils import VectorHelper
from bpy_extras.io_utils import ImportHelper, ExportHelper


class SOLLUMZ_OT_import(SOLLUMZ_OT_base, bpy.types.Operator, ImportHelper):
    """Imports xml files exported by codewalker."""
    bl_idname = "sollumz.import"
    bl_label = "Import Codewalker XML"
    bl_action = "import"
    bl_showtime = True

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};",
        options={"HIDDEN"},
        maxlen=255,
    )

    filename_exts = [YDR.file_extension, YDD.file_extension,
                     YFT.file_extension, YBN.file_extension]

    import_directory: bpy.props.BoolProperty(
        name="Import Directory",
        description="Import the entire directory.",
        default=False,
    )

    def import_file(self, filepath, ext):
        try:
            valid_type = False
            if ext == YDR.file_extension:
                import_ydr(filepath)
                valid_type = True
            elif ext == YDD.file_extension:
                import_ydd(filepath)
                valid_type = True
            elif ext == YFT.file_extension:
                import_yft(filepath)
                valid_type = True
            elif ext == YBN.file_extension:
                import_ybn(filepath)
                valid_type = True

            if valid_type:
                self.message(f"Succesfully imported: {filepath}")
        except:
            self.error(
                f"Error importing: {filepath} \n {traceback.format_exc()}")
            return False

        return True

    def run(self, context):
        result = False
        if self.import_directory:
            folderpath = os.path.dirname(self.filepath)
            for file in os.listdir(folderpath):
                ext = ''.join(pathlib.Path(file).suffixes)
                if ext in self.filename_exts:
                    filepath = os.path.join(folderpath, file)
                    result = self.import_file(filepath, ext)
        else:
            ext = ''.join(pathlib.Path(self.filepath).suffixes)
            result = self.import_file(self.filepath, ext)

        if not result:
            self.bl_showtime = False

        return True


class SOLLUMZ_OT_export(SOLLUMZ_OT_base, bpy.types.Operator):
    """Exports codewalker xml files."""
    bl_idname = "sollumz.export"
    bl_label = "Export Codewalker XML"
    bl_action = "export"
    bl_showtime = True

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};",
        options={'HIDDEN'},
        maxlen=255,
    )

    directory: bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
    )

    export_type: bpy.props.EnumProperty(
        items=[("export_all", "Export All", "Export all objects in the scene."),
               ("export_selected", "Export Selected",
                "Export selected objects in the scene.")],
        description="The method in which you want to export your scene.",
        name="Export Type",
        default="export_all"
    )

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def get_filepath(self, filename):
        return os.path.join(self.directory, filename)

    def export_object(self, obj):
        try:
            valid_type = False
            filepath = None
            if obj.sollum_type == DrawableType.DRAWABLE:
                filepath = self.get_filepath(obj.name + YDR.file_extension)
                export_ydr(self, obj, filepath)
                valid_type = True
            elif obj.sollum_type == DrawableType.DRAWABLE_DICTIONARY:
                filepath = self.get_filepath(obj.name + YDD.file_extension)
                export_ydd(self, obj, filepath)
                valid_type = True
            elif obj.sollum_type == FragmentType.FRAGMENT:
                filepath = self.get_filepath(obj.name + YFT.file_extension)
                export_yft(obj, filepath)
                valid_type = True
            elif obj.sollum_type == BoundType.COMPOSITE:
                filepath = self.get_filepath(obj.name + YBN.file_extension)
                export_ybn(obj, filepath)
                valid_type = True
            if valid_type:
                self.message(f"Succesfully exported: {filepath}")
        except:
            self.error(
                f"Error exporting: {filepath} \n {traceback.format_exc()}")
            return False
        return True

    def get_only_parent_objs(self, objs):
        pobjs = []
        for obj in objs:
            if obj.parent == None:
                pobjs.append(obj)
        return pobjs

    def run(self, context):
        objects = []

        if(self.export_type == "export_all"):
            objects = self.get_only_parent_objs(context.collection.objects)
        else:
            objects = context.selected_objects

        if not is_sollum_object_in_objects(objects):
            self.warning("No sollum objects selected or in scene to export.")
            return False

        if len(objects) > 0:
            for obj in objects:
                mode = obj.mode
                # Switch to object mode during export
                if mode != 'OBJECT':
                    bpy.ops.object.mode_set(mode='OBJECT')
                result = self.export_object(obj)
                if obj.mode != mode:
                    bpy.ops.object.mode_set(mode=mode)
                # Dont show time on failure
                if not result:
                    self.bl_showtime = False

        return True


class SOLLUMZ_OT_import_ymap(SOLLUMZ_OT_base, bpy.types.Operator, ImportHelper):
    """Imports .ymap.xml file exported from codewalker."""
    bl_idname = "sollumz.importymap"
    bl_label = "Import ymap.xml"
    filename_ext = ".ymap.xml"
    bl_action = "Import a YMAP"
    bl_showtime = True

    filter_glob: bpy.props.StringProperty(
        default="*.ymap.xml",
        options={'HIDDEN'},
        maxlen=255,
    )

    def apply_entity_properties(self, obj, entity):
        obj.entity_properties.archetype_name = entity.archetype_name
        obj.entity_properties.flags = entity.flags
        obj.entity_properties.guid = entity.guid
        obj.entity_properties.parent_index = entity.parent_index
        obj.entity_properties.lod_dist = entity.lod_dist
        obj.entity_properties.child_lod_dist = entity.child_lod_dist
        obj.entity_properties.lod_level = "sollumz_" + entity.lod_level.lower()
        obj.entity_properties.num_children = entity.num_children
        obj.entity_properties.priority_level = "sollumz_" + entity.priority_level.lower()
        obj.entity_properties.ambient_occlusion_multiplier = entity.ambient_occlusion_multiplier
        obj.entity_properties.artificial_ambient_occlusion = entity.artificial_ambient_occlusion
        obj.entity_properties.tint_value = entity.tint_value

        if entity.type != 'CMloInstanceDef':
            # Entities in YMAPs need rotation inverted
            entity.rotation.invert()
        obj.matrix_world = entity.rotation.to_matrix().to_4x4()
        obj.location = entity.position
        obj.scale = Vector(
            (entity.scale_xy, entity.scale_xy, entity.scale_z))

    def run(self, context):

        try:
            ymap = YMAP.from_xml_file(self.filepath)
            if ymap.entities:
                for obj in context.collection.objects:
                    for entity in ymap.entities:
                        if(entity.archetype_name == obj.name):
                            self.apply_entity_properties(obj, entity)
                self.message(f"Succesfully imported: {self.filepath}")
                return True
            else:
                self.error(f"{self.filepath} contains no entities to import!")
                return False
        except:
            self.error(f"Error during import: {traceback.format_exc()}")
            return False


class SOLLUMZ_OT_export_ymap(SOLLUMZ_OT_base, bpy.types.Operator, ExportHelper):
    """Exports .ymap.xml file exported from codewalker."""
    bl_idname = "sollumz.exportymap"
    bl_label = "Export ymap.xml"
    bl_action = "Export a YMAP"
    bl_showtime = True

    filename_ext = ".ymap.xml"

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
        entity.position = obj.location
        entity.rotation = obj.rotation_euler.to_quaternion()
        entity.scale_xy = obj.scale.x
        entity.scale_z = obj.scale.z
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

    def run(self, context):

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

            self.message(f"Succesfully exported: {self.filepath}")
            return True
        except:
            self.message(f"Error during export: {traceback.format_exc()}")
            return False


class SOLLUMZ_OT_paint_vertices(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint All Vertices Of Selected Object"""
    bl_idname = "sollumz.paint_vertices"
    bl_label = "Paint"
    bl_action = "Paint Vertices"

    def paint_map(self, mesh, map, color):
        i = 0
        for poly in mesh.polygons:
            for idx in poly.loop_indices:
                map[i].color = color
                i += 1

    def paint_mesh(self, mesh, color):
        if len(mesh.vertex_colors) == 0:
            mesh.vertex_colors.new()
        self.paint_map(mesh, mesh.vertex_colors.active.data, color)

    def run(self, context):
        objs = context.selected_objects

        if len(objs) > 0:
            for obj in objs:
                if(obj.sollum_type == DrawableType.GEOMETRY):
                    self.paint_mesh(obj.data, context.scene.vert_paint_color)
                    self.messages.append(
                        f"{obj.name} was successfully painted.")
                else:
                    self.messages.append(
                        f"{obj.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[DrawableType.GEOMETRY]} type.")
        else:
            self.message("No objects selected to paint.")
            return False

        return True


def sollumz_menu_func_import(self, context):
    self.layout.operator(SOLLUMZ_OT_import.bl_idname,
                         text=f"Codewalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension})")


def sollumz_menu_func_export(self, context):
    self.layout.operator(SOLLUMZ_OT_export.bl_idname,
                         text=f"Codewalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension})")


def register():
    bpy.types.TOPBAR_MT_file_import.append(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(sollumz_menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(sollumz_menu_func_export)
