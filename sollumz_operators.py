import traceback
import os
from typing import Optional
import bpy
import time
from collections import defaultdict
import re
from bpy_extras.io_utils import ImportHelper
from mathutils import Matrix, Quaternion
from .sollumz_helper import SOLLUMZ_OT_base, find_sollumz_parent
from .sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, BOUND_TYPES, TimeFlagsMixin, ArchetypeType, LODLevel
from .sollumz_preferences import get_export_settings
from .cwxml.drawable import YDR, YDD
from .cwxml.fragment import YFT
from .cwxml.bound import YBN
from .cwxml.navmesh import YNV
from .cwxml.clipdictionary import YCD
from .cwxml.ytyp import YTYP
from .cwxml.ymap import YMAP
from .ydr.ydrimport import import_ydr
from .ydr.ydrexport import export_ydr
from .ydd.yddimport import import_ydd
from .ydd.yddexport import export_ydd
from .yft.yftimport import import_yft
from .yft.yftexport import export_yft
from .ybn.ybnimport import import_ybn
from .ybn.ybnexport import export_ybn
from .ynv.ynvimport import import_ynv
from .ycd.ycdimport import import_ycd
from .ycd.ycdexport import export_ycd
from .ymap.ymapimport import import_ymap
from .ymap.ymapexport import export_ymap
from .ytyp.ytypimport import import_ytyp
from .tools.blenderhelper import add_child_of_bone_constraint, get_child_of_pose_bone, apply_terrain_brush_setting_to_current_brush, remove_number_suffix, create_blender_object, join_objects
from .tools.ytyphelper import ytyp_from_objects
from .ybn.properties import BoundFlags

from . import logger


class TimedOperator:
    @property
    def time_elapsed(self) -> float:
        """Get time elapsed since execution"""
        return round(time.time() - self._start, 3)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._start: float = 0.0

    def execute(self, context: bpy.types.Context):
        self._start = time.time()
        return self.execute_timed(context)

    def execute_timed(self, context: bpy.types.Context):
        ...


class SOLLUMZ_OT_import_assets(bpy.types.Operator, ImportHelper, TimedOperator):
    """Import XML files exported by CodeWalker"""
    bl_idname = "sollumz.import_assets"
    bl_label = "Import CodeWalker XML"
    bl_options = {"UNDO"}

    directory: bpy.props.StringProperty(subtype="FILE_PATH", options={"HIDDEN", "SKIP_SAVE"})
    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    filter_glob: bpy.props.StringProperty(
        default="".join(f"*{filetype.file_extension};" for filetype in (YDR, YDD, YFT, YBN, YNV, YCD, YMAP, YTYP)),
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    def draw(self, context):
        pass

    def execute_timed(self, context):
        with logger.use_operator_logger(self):
            if not self.directory or len(self.files) == 0 or self.files[0].name == "":
                logger.info("No file selected for import!")
                return {"CANCELLED"}

            self.directory = bpy.path.abspath(self.directory)

            filenames = [f.name for f in self.files]
            filenames, ytyp_filenames = self._separate_ytyp_filenames(filenames)
            filenames = self._dedupe_hi_yft_filenames(filenames)

            for filename in filenames:
                filepath = os.path.join(self.directory, filename)

                try:

                    if YDR.file_extension in filepath:
                        import_ydr(filepath)
                    elif YDD.file_extension in filepath:
                        import_ydd(filepath)
                    elif YFT.file_extension in filepath:
                        import_yft(filepath)
                    elif YBN.file_extension in filepath:
                        import_ybn(filepath)
                    elif YNV.file_extension in filepath:
                        import_ynv(filepath)
                    elif YCD.file_extension in filepath:
                        import_ycd(filepath)
                    elif YMAP.file_extension in filepath:
                        import_ymap(filepath)
                    else:
                        continue

                    logger.info(f"Successfully imported '{filepath}'")
                except:
                    logger.error(f"Error importing: {filepath} \n {traceback.format_exc()}")
                    return {"CANCELLED"}

            # Import the .ytyps after all the assets to ensure that the archetypes get linked to their object in case
            # they are imported together
            for filename in ytyp_filenames:
                filepath = os.path.join(self.directory, filename)
                try:
                    import_ytyp(filepath)
                    logger.info(f"Successfully imported '{filepath}'")
                except:
                    logger.error(f"Error importing: {filepath} \n {traceback.format_exc()}")
                    return {"CANCELLED"}

            logger.info(f"Imported in {self.time_elapsed} seconds")
            return {"FINISHED"}

    def invoke(self, context, event):
        if self.directory and len(self.files) > 0 and self.files[0].name != "":
            # Already have a list of files, don't open the import window and do the import directly.
            # Invoked by the FileHandler below (or a manual operator call, but we don't currently do that).
            return self.execute(context)

        return super().invoke(context, event)

    def _dedupe_hi_yft_filenames(self, filenames: list[str]) -> list[str]:
        """If the user selected both a non-hi .yft.xml and its _hi.yft.xml, remove the _hi.yft.xml one to prevent
        importing the same model twice.
        """
        return [f for f in filenames if not f.endswith("_hi.yft.xml") or f"{f[:-11]}.yft.xml" not in filenames]

    def _separate_ytyp_filenames(self, filenames: list[str]) -> tuple[list[str], list[str]]:
        """Separate the filenames list into two lists, one with all the assets and another one only with .ytyps."""
        asset_filenames, ytyp_filenames = [], []
        for f in filenames:
            dest = ytyp_filenames if f.endswith(YTYP.file_extension) else asset_filenames
            dest.append(f)
        return asset_filenames, ytyp_filenames


if bpy.app.version >= (4, 1, 0):
    class SOLLUMZ_FH_import(bpy.types.FileHandler):
        # TODO: needs a new operator if we want to support .ytyp import as well (or also allow the normal import to
        # import .ytyps)
        bl_idname = "SOLLUMZ_FH_import"
        bl_label = "File handler for CodeWalker XML import"
        bl_import_operator = SOLLUMZ_OT_import_assets.bl_idname
        # Supports handling multiple extensions, but doesn't support multi-dot extensions like .yft.xml. Should be fine
        # because the operator checks the extension, but it is a bit broad.
        bl_file_extensions = ".xml"

        @classmethod
        def poll_drop(cls, context):
            a = context.area
            return a is not None and (a.type == "VIEW_3D" or a.type == "OUTLINER")


class SOLLUMZ_OT_export_assets(bpy.types.Operator, TimedOperator):
    """Export CodeWalker XML files"""
    bl_idname = "sollumz.export_assets"
    bl_label = "Export CodeWalker XML"

    filter_glob: bpy.props.StringProperty(
        default=f"*{YDR.file_extension};*{YDD.file_extension};*{YFT.file_extension};*{YBN.file_extension};*{YCD.file_extension};*{YMAP.file_extension};",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    directory: bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
        options={"HIDDEN"}
    )

    direct_export: bpy.props.BoolProperty(
        name="Direct Export",
        description="Export directly to the output directory without opening the directory selection dialog",
        options={"HIDDEN", "SKIP_SAVE"}
    )

    def draw(self, context):
        pass

    def invoke(self, context, event):
        if self.direct_export:
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

    def execute_timed(self, context: bpy.types.Context):
        with logger.use_operator_logger(self) as op_log:
            logger.info("Starting export...")
            objs = self.collect_objects(context)
            export_settings = get_export_settings()

            self.directory = bpy.path.abspath(self.directory)

            if not objs:
                if export_settings.limit_to_selected:
                    logger.info("No Sollumz objects selected for export!")
                else:
                    logger.info("No Sollumz objects in the scene to export!")
                return {"CANCELLED"}

            any_warnings_or_errors = False
            for obj in objs:
                op_log.clear_log_counts()
                filepath = None
                try:
                    success = False
                    if obj.sollum_type == SollumType.DRAWABLE:
                        filepath = self.get_filepath(obj, YDR.file_extension)
                        success = export_ydr(obj, filepath)
                    elif obj.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                        filepath = self.get_filepath(obj, YDD.file_extension)
                        success = export_ydd(obj, filepath)
                    elif obj.sollum_type == SollumType.FRAGMENT:
                        filepath = self.get_filepath(obj, YFT.file_extension)
                        success = export_yft(obj, filepath)
                    elif obj.sollum_type == SollumType.CLIP_DICTIONARY:
                        filepath = self.get_filepath(obj, YCD.file_extension)
                        success = export_ycd(obj, filepath)
                    elif obj.sollum_type == SollumType.BOUND_COMPOSITE:
                        filepath = self.get_filepath(obj, YBN.file_extension)
                        success = export_ybn(obj, filepath)
                    elif obj.sollum_type == SollumType.YMAP:
                        filepath = self.get_filepath(obj, YMAP.file_extension)
                        success = export_ymap(obj, filepath)
                    else:
                        continue

                    if success:
                        if op_log.has_warnings_or_errors:
                            logger.info(f"Exported '{filepath}' with WARNINGS or ERRORS! Please check the Info Log for details.")
                            any_warnings_or_errors = True
                        else:
                            logger.info(f"Successfully exported '{filepath}'")
                    else:
                        if op_log.has_warnings_or_errors:
                            logger.info(f"Failed to export '{obj.name}', ERRORS found! Please check the Info Log for details.")
                            any_warnings_or_errors = True
                except:
                    logger.error(f"Error exporting: {filepath or obj.name} \n {traceback.format_exc()}")
                    any_warnings_or_errors = True
                    return {"CANCELLED"}

            if export_settings.export_with_ytyp:
                ytyp = ytyp_from_objects(objs)
                filepath = os.path.join(
                    self.directory, f"{ytyp.name}.ytyp.xml")
                ytyp.write_xml(filepath)
                logger.info(f"Successfully exported '{filepath}' (auto-generated)")

            logger.info(f"Exported in {self.time_elapsed} seconds")
            if any_warnings_or_errors:
                bpy.ops.screen.info_log_show()
            return {"FINISHED"}

    def collect_objects(self, context: bpy.types.Context) -> list[bpy.types.Object]:
        export_settings = get_export_settings()

        objs = context.scene.objects

        if export_settings.limit_to_selected:
            objs = context.selected_objects

        return self.get_only_parent_objs(objs)

    def get_only_parent_objs(self, objs: list[bpy.types.Object]):
        parent_objs = set()
        objs = set(objs)

        for obj in objs:
            parent_obj = find_sollumz_parent(obj)

            if parent_obj is None or parent_obj in parent_objs:
                continue

            parent_objs.add(parent_obj)

        return list(parent_objs)

    def get_filepath(self, obj: bpy.types.Object, extension: str):
        name = remove_number_suffix(obj.name.lower())

        return os.path.join(self.directory, name + extension)


class SOLLUMZ_OT_paint_vertices(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint All Vertices Of Selected Object"""
    bl_idname = "sollumz.paint_vertices"
    bl_label = "Paint"
    bl_action = "Paint Vertices"

    color: bpy.props.FloatVectorProperty(
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    def paint_map(self, color_attr, color):
        for datum in color_attr.data:
            # Uses color_srgb to match the behavior of the old
            # vertex_colors code. Requires 3.4+.
            datum.color_srgb = color

    def paint_mesh(self, mesh, color):
        if not mesh.color_attributes:
            mesh.color_attributes.new("Color", 'BYTE_COLOR', 'CORNER')
        self.paint_map(mesh.attributes.active_color, color)

    def run(self, context):
        objs = context.selected_objects

        if len(objs) > 0:
            for obj in objs:
                if obj.sollum_type == SollumType.DRAWABLE_MODEL:
                    self.paint_mesh(obj.data, self.color)
                    self.messages.append(
                        f"{obj.name} was successfully painted.")
                else:
                    self.messages.append(
                        f"{obj.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_MODEL]} type.")
        else:
            self.message("No objects selected to paint.")
            return False

        return True


class SOLLUMZ_OT_paint_terrain_tex1(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 1 On Selected Object"""
    bl_idname = "sollumz.paint_tex1"
    bl_label = "Paint Texture 1"

    def run(self, context):
        apply_terrain_brush_setting_to_current_brush(1)
        return True


class SOLLUMZ_OT_paint_terrain_tex2(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 2 On Selected Object"""
    bl_idname = "sollumz.paint_tex2"
    bl_label = "Paint Texture 2"

    def run(self, context):
        apply_terrain_brush_setting_to_current_brush(2)
        return True


class SOLLUMZ_OT_paint_terrain_tex3(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 3 On Selected Object"""
    bl_idname = "sollumz.paint_tex3"
    bl_label = "Paint Texture 3"

    def run(self, context):
        apply_terrain_brush_setting_to_current_brush(3)
        return True


class SOLLUMZ_OT_paint_terrain_tex4(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Texture 4 On Selected Object"""
    bl_idname = "sollumz.paint_tex4"
    bl_label = "Paint Texture 4"

    def run(self, context):
        apply_terrain_brush_setting_to_current_brush(4)
        return True


class SOLLUMZ_OT_paint_terrain_alpha(SOLLUMZ_OT_base, bpy.types.Operator):
    """Paint Lookup Sampler Alpha On Selected Object"""
    bl_idname = "sollumz.paint_a"
    bl_label = "Paint Alpha"

    alpha: bpy.props.FloatProperty(name="Alpha", min=-1.0, max=1.0)

    def run(self, context):
        apply_terrain_brush_setting_to_current_brush(5, self.alpha)
        return True


class SelectTimeFlagsRange(SOLLUMZ_OT_base):
    """Select range of time flags"""
    bl_label = "Select"

    def get_flags(self, context):
        return None

    def run(self, context):
        flags = self.get_flags(context)
        return SelectTimeFlagsRange._process_one(flags, context)

    @staticmethod
    def _process_one(flags, context) -> bool:
        if not flags:
            return False
        start = int(flags.time_flags_start)
        end = int(flags.time_flags_end)
        index = 0
        for prop in TimeFlagsMixin.flag_names:
            if index < 24:
                if start < end:
                    if index >= start and index < end:
                        flags[prop] = True
                elif start > end:
                    if index < end or index >= start:
                        flags[prop] = True
                elif start == 0 and end == 0:
                    flags[prop] = True
            index += 1
        flags.update_flag(context)
        return True


class SelectTimeFlagsRangeMultiSelect(SOLLUMZ_OT_base):
    """Select range of time flags"""
    bl_label = "Select"

    def iter_selection_flags(self, context):
        if False: # empty generator
            yield

    def run(self, context):
        for flags in self.iter_selection_flags(context):
            if not SelectTimeFlagsRange._process_one(flags, context):
                return False
        return True


class ClearTimeFlags(SOLLUMZ_OT_base):
    """Clear all time flags"""
    bl_label = "Clear Selection"

    def get_flags(self, context):
        return None

    def run(self, context):
        flags = self.get_flags(context)
        return ClearTimeFlags._process_one(flags, context)

    @staticmethod
    def _process_one(flags, context) -> bool:
        if not flags:
            return False
        for prop in TimeFlagsMixin.flag_names:
            flags[prop] = False
        flags.update_flag(context)
        return True


class ClearTimeFlagsMultiSelect(SOLLUMZ_OT_base):
    """Clear all time flags"""
    bl_label = "Clear Selection"

    def iter_selection_flags(self, context):
        if False: # empty generator
            yield

    def run(self, context):
        for flags in self.iter_selection_flags(context):
            if not ClearTimeFlags._process_one(flags, context):
                return False
        return True


def sollumz_menu_func_import(self, context):
    self.layout.operator(SOLLUMZ_OT_import_assets.bl_idname,
                         text=f"CodeWalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension}, {YCD.file_extension})")


def sollumz_menu_func_export(self, context):
    self.layout.operator(SOLLUMZ_OT_export_assets.bl_idname,
                         text=f"CodeWalker XML({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension}, {YCD.file_extension})")


class SOLLUMZ_OT_debug_hierarchy(bpy.types.Operator):
    """Debug: Fix incorrect Sollum Type after update. Must set correct type for top-level object first"""
    bl_idname = "sollumz.debug_hierarchy"
    bl_label = "Fix Hierarchy"
    bl_options = {"UNDO"}
    bl_order = 100

    def execute(self, context):
        sollum_type = context.scene.debug_sollum_type
        for obj in context.selected_objects:
            if len(obj.children) < 1:
                self.report(
                    {"INFO"}, f"{obj.name} has no children! Skipping...")
                continue

            obj.sollum_type = sollum_type
            if sollum_type == SollumType.DRAWABLE:
                self.fix_drawable(obj)
            elif sollum_type == SollumType.DRAWABLE_DICTIONARY:
                self.fix_drawable_dict(obj)
            elif sollum_type == SollumType.BOUND_COMPOSITE:
                self.fix_composite(obj)

        self.report({"INFO"}, "Hierarchy successfuly set.")

        return {"FINISHED"}

    def fix_drawable(self, obj: bpy.types.Object):
        for model in obj.children:
            if model.type != "MESH":
                continue

            model.sollum_type = SollumType.DRAWABLE_MODEL

    def fix_drawable_dict(self, obj: bpy.types.Object):
        for draw in obj.children:
            if draw.type != "EMPTY":
                continue

            draw.sollum_type = SollumType.DRAWABLE
            self.fix_drawable(draw)

    def fix_composite(self, obj: bpy.types.Object):
        for bound in obj.children:
            if bound.type == "EMPTY":
                if "cloth" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_PLANE
                    continue

                if "bvh" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_GEOMETRYBVH
                else:
                    bound.sollum_type = SollumType.BOUND_GEOMETRY
                for geom in bound.children:
                    if geom.type == "MESH":
                        if "Box" in geom.name:
                            geom.sollum_type = SollumType.BOUND_POLY_BOX
                        elif "Sphere" in geom.name:
                            geom.sollum_type = SollumType.BOUND_POLY_SPHERE
                        elif "Capsule" in geom.name:
                            geom.sollum_type = SollumType.BOUND_POLY_CAPSULE
                        elif "Cylinder" in geom.name:
                            geom.sollum_type = SollumType.BOUND_POLY_CYLINDER
                        else:
                            geom.sollum_type = SollumType.BOUND_POLY_TRIANGLE
            if bound.type == "MESH":
                if "box" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_POLY_BOX
                elif "sphere" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_POLY_SPHERE
                elif "capsule" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_POLY_CAPSULE
                elif "cylinder" in bound.name.lower():
                    bound.sollum_type = SollumType.BOUND_POLY_CYLINDER
                else:
                    bound.sollum_type = SollumType.BOUND_POLY_TRIANGLE


class SOLLUMZ_OT_debug_fix_light_intensity(bpy.types.Operator):
    bl_idname = "sollumz.debug_fix_light_intensity"
    bl_label = "Re-adjust Light Intensity"
    bl_description = "Multiply light intensity by a factor of 500 to make older projects compatible with the light intensity change"
    bl_options = {"UNDO"}

    def execute(self, context):
        only_selected = context.scene.debug_lights_only_selected

        objects = context.selected_objects if only_selected else context.scene.objects
        light_objs = [obj for obj in objects if obj.type ==
                      "LIGHT" and obj.sollum_type == SollumType.LIGHT]

        if not light_objs:
            self.report(
                {"INFO"}, "No Sollumz lights selected" if only_selected else "No Sollumz lights in the scene.")
            return {"CANCELLED"}

        lights: list[bpy.types.Light] = []
        for light_obj in light_objs:
            if light_obj.data not in lights:
                lights.append(light_obj.data)

        for light in lights:
            light.energy = light.energy * 500

        return {"FINISHED"}


class SOLLUMZ_OT_copy_location(bpy.types.Operator):
    """Copy the location of an object to the clipboard"""
    bl_idname = "wm.sollumz_copy_location"
    bl_label = ""
    location: bpy.props.StringProperty()

    def execute(self, context):
        bpy.context.window_manager.clipboard = self.location
        self.report(
            {'INFO'}, "Location copied to clipboard: {}".format(self.location))
        return {'FINISHED'}


class SOLLUMZ_OT_copy_rotation(bpy.types.Operator):
    """Copy the quaternion rotation of an object to the clipboard"""
    bl_idname = "wm.sollumz_copy_rotation"
    bl_label = ""
    rotation: bpy.props.StringProperty()

    def execute(self, context):
        rotation = self.rotation.strip('[]')
        bpy.context.window_manager.clipboard = rotation
        self.report(
            {'INFO'}, "Rotation copied to clipboard: {}".format(rotation))
        return {'FINISHED'}


class SOLLUMZ_OT_paste_location(bpy.types.Operator):
    """Paste the location of an object from the clipboard"""
    bl_idname = "wm.sollumz_paste_location"
    bl_label = ""

    def execute(self, context):
        def parse_location_string(location_string):
            pattern = r"(-?\d+\.\d+)"
            matches = re.findall(pattern, location_string)
            if len(matches) == 3:
                return float(matches[0]), float(matches[1]), float(matches[2])
            else:
                return None

        location_string = bpy.context.window_manager.clipboard

        location = parse_location_string(location_string)
        if location is not None:
            selected_object = bpy.context.object

            selected_object.location = location
            self.report({'INFO'}, "Location set successfully.")
        else:
            self.report({'ERROR'}, "Invalid location string.")

        return {'FINISHED'}
    
class SOLLUMZ_OT_paste_rotation(bpy.types.Operator):
    """Paste the rotation (as quaternion) of an object from the clipboard and apply it"""
    bl_idname = "wm.sollumz_paste_rotation"
    bl_label = "Paste Rotation"

    def execute(self, context):

        rotation_string = bpy.context.window_manager.clipboard

        rotation_quaternion = parse_rotation_string(rotation_string)
        if rotation_quaternion is not None:
            selected_object = bpy.context.object

            prev_rotation_mode = selected_object.rotation_mode
            selected_object.rotation_mode = "QUATERNION"
            selected_object.rotation_quaternion = rotation_quaternion
            selected_object.rotation_mode = prev_rotation_mode

            self.report({"INFO"}, "Rotation set successfully.")
        else:
            self.report({"ERROR"}, "Invalid rotation quaternion string.")
        return {"FINISHED"}

def parse_rotation_string(rotation_string):
    values = rotation_string.split(",")
    if len(values) == 4:
        try:
            x = float(values[0].strip())
            y = float(values[1].strip())
            z = float(values[2].strip())
            w = float(values[3].strip())
            return Quaternion((w, x, y, z))
        except ValueError:
            pass
    return None


class SOLLUMZ_OT_debug_migrate_drawable_models(bpy.types.Operator):
    """Convert old drawable model to use new LOD system"""
    bl_idname = "sollumz.migratedrawable"
    bl_label = "Migrate Drawable Model(s)"
    bl_options = {"UNDO"}

    def execute(self, context):
        selected_models = [
            obj for obj in context.selected_objects if obj.sollum_type == SollumType.DRAWABLE_MODEL]

        if not selected_models:
            self.report({"INFO"}, "No drawable models selected!")
            return {"CANCELLED"}

        parent = selected_models[0].parent

        models_by_lod: dict[LODLevel,
                            list[bpy.types.Object]] = defaultdict(list)

        for obj in selected_models:
            models_by_lod[obj.drawable_model_properties.sollum_lod].extend(
                obj.children)
            bpy.data.objects.remove(obj)

        model_obj = create_blender_object(SollumType.DRAWABLE_MODEL)
        model_lods = model_obj.sz_lods
        old_mesh = model_obj.data

        for lod_level, geometries in models_by_lod.items():

            if len(geometries) > 1:
                joined_obj = join_objects(geometries)
            else:
                joined_obj = geometries[0]

            model_lods.get_lod(lod_level).mesh = joined_obj.data
            model_lods.active_lod_level = lod_level

            context.view_layer.objects.active = joined_obj
            model_obj.select_set(True)

            bpy.ops.object.make_links_data(type='MODIFIERS')
            bpy.data.objects.remove(joined_obj)

        bpy.data.meshes.remove(old_mesh)

        model_obj.parent = parent

        model_lods.set_highest_lod_active()

        return {"FINISHED"}


class SOLLUMZ_OT_debug_migrate_bound_geometries(bpy.types.Operator):
    """Convert old bound geometries to new hiearchy using shape keys for damaged layers"""
    bl_idname = "sollumz.migrateboundgeoms"
    bl_label = "Migrate Bound Geometry(s)"
    bl_options = {"UNDO"}

    def execute(self, context):
        selected = [
            obj for obj in context.selected_objects if obj.sollum_type == SollumType.BOUND_GEOMETRY]

        if not selected:
            self.report({"INFO"}, "No bound geometries selected!")
            return {"CANCELLED"}

        for obj in selected:
            bound_meshes = []

            for child in obj.children:
                if child.type != "MESH":
                    continue

                child.data.transform(child.matrix_basis)
                child.matrix_basis.identity()

                if child.sollum_type == SollumType.BOUND_POLY_TRIANGLE:
                    bound_meshes.append(child)

            joined_obj = join_objects(bound_meshes)
            joined_obj.sollum_type = SollumType.BOUND_GEOMETRY
            joined_obj.name = obj.name
            joined_obj.parent = obj.parent

            self.set_composite_flags(obj, joined_obj)

            joined_obj.matrix_basis = obj.matrix_basis

            bpy.data.objects.remove(obj)

        return {"FINISHED"}

    def set_composite_flags(self, old_obj: bpy.types.Object, new_obj: bpy.types.Object):
        def set_flags(prop_name: str):
            flags_props = getattr(old_obj, prop_name)
            new_flags_props = getattr(new_obj, prop_name)

            for flag_name in BoundFlags.__annotations__.keys():
                value = getattr(flags_props, flag_name)
                setattr(new_flags_props, flag_name, value)

        set_flags("composite_flags1")
        set_flags("composite_flags2")


class SOLLUMZ_OT_debug_replace_armature_constraints(bpy.types.Operator):
    """Replace the Armature constraints in all selected objects for Child Of constraints (for migrating pre version 0.3 projects)"""
    bl_idname = "sollumz.replace_armature_constraints"
    bl_label = "Replace Armature Constraints"
    bl_options = {"REGISTER", "UNDO"}

    def execute(self, context):
        if not context.selected_objects:
            self.report({"INFO"}, "No objects selected!")
            return {"CANCELLED"}

        for obj in context.selected_objects:
            constraint = self.get_armature_constraint(obj)

            if constraint is None or not constraint.targets:
                continue

            target = constraint.targets[0]
            armature_obj = target.target
            target_bone = target.subtarget

            obj.constraints.remove(constraint)

            add_child_of_bone_constraint(obj, armature_obj, target_bone)
            self.set_obj_child_of_bone_inverse(obj)

        return {"FINISHED"}

    @staticmethod
    def get_armature_constraint(obj: bpy.types.Object) -> Optional[bpy.types.ArmatureConstraint]:
        for constraint in obj.constraints:
            if constraint.type == "ARMATURE":
                return constraint

    @staticmethod
    def set_obj_child_of_bone_inverse(obj: bpy.types.Object):
        """Invert the transformations of the Child Of constraint bone on obj
        so that the object doesn't get double transformed"""
        # bone = get_child_of_bone(obj)
        bone = get_child_of_pose_bone(obj)

        if bone is None:
            return

        obj.matrix_local = bone.matrix.inverted() @ obj.matrix_local


class SOLLUMZ_OT_set_sollum_type(bpy.types.Operator):
    """Set the sollum type of all selected objects"""
    bl_idname = "sollumz.setsollumtype"
    bl_label = "Set Sollum Type"

    def execute(self, context):
        sollum_type = context.scene.all_sollum_type

        for obj in context.selected_objects:
            obj.sollum_type = sollum_type

        self.report(
            {"INFO"}, f"Sollum Type successfuly set to {SOLLUMZ_UI_NAMES[sollum_type]}.")

        return {"FINISHED"}


class SearchEnumHelper:
    """Helper class for searching and setting enums"""
    bl_label = "Search"

    def get_data_block(self, context):
        """Get the data-block containing the enum property"""
        ...

    def execute(self, context):
        data_block = self.get_data_block(context)
        prop_name = getattr(self, "bl_property")
        enum_value = getattr(self, prop_name)

        setattr(data_block, prop_name, enum_value)

        return {'FINISHED'}

    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)

        return {'FINISHED'}


def register():
    bpy.types.TOPBAR_MT_file_import.append(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.append(sollumz_menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_import.remove(sollumz_menu_func_import)
    bpy.types.TOPBAR_MT_file_export.remove(sollumz_menu_func_export)
