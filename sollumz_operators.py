import traceback
import os
import bpy
from bpy.types import (
    Context,
    Object,
    PropertyGroup,
    Operator,
)
from bpy.props import (
    BoolProperty,
    PointerProperty,
)
import time
import re
from mathutils import Quaternion
from .sollumz_helper import SOLLUMZ_OT_base, find_sollumz_parent
from .sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, TimeFlagsMixin
from .sollumz_preferences import get_addon_preferences, get_import_settings, get_export_settings, ImportSettingsBase, ExportSettingsBase
from szio.gta5.cwxml import (
    YDR,
    YDD,
    YFT,
    YBN,
    YNV,
    YCD,
    YTYP,
    YMAP,
)
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
from .tools.blenderhelper import remove_number_suffix
from .meta import DEV_MODE
from .dependencies import IS_SZIO_NATIVE_AVAILABLE, PYMATERIA_REQUIRED_MSG

from . import logger


class TimedOperator:
    @property
    def time_elapsed(self) -> float:
        """Get time elapsed since execution"""
        return round(time.time() - self._start, 3)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._start: float = 0.0

    def execute(self, context: Context):
        self._start = time.time()
        return self.execute_timed(context)

    def execute_timed(self, context: Context):
        ...


class ExportSettingsOverride(ExportSettingsBase, PropertyGroup):
    ...


class ImportSettingsOverride(ImportSettingsBase, PropertyGroup):
    ...


class SOLLUMZ_OT_import_assets_legacy(TimedOperator, Operator):
    """Import XML files exported by CodeWalker"""
    bl_idname = "sollumz.import_assets_legacy"
    bl_label = "Import CodeWalker XML"
    bl_options = {"UNDO"}

    directory: bpy.props.StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})
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

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

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


class ImportAssetsOperatorImpl(TimedOperator):
    """Import RAGE asset files"""
    directory: bpy.props.StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})
    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    filter_glob: bpy.props.StringProperty(
        default="".join(f"*{ext};" for ext in (
            ".ybn", ".ydr", ".ydd", ".yft", ".ytyp",
            ".ybn.xml", ".ydr.xml", ".ydd.xml", ".yft.xml", ".ytyp.xml", ".ymap.xml", ".ycd.xml", ".ynv.xml"
        )),
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    # These are for scripts that use these operators to override the settings and avoid messing with the user preferences.
    use_custom_settings: BoolProperty(name="Use Custom Settings", default=False, options={"HIDDEN", "SKIP_SAVE"})
    custom_settings: PointerProperty(type=ImportSettingsOverride,
                                     name="Custom Settings", options={"HIDDEN", "SKIP_SAVE"})

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

            from pathlib import Path
            from szio.gta5 import try_load_asset, AssetType, AssetWithDependencies
            from .ybn.ybnimport_io import import_ybn as import_ybn_asset
            from .ydr.ydrimport_io import import_ydr as import_ydr_asset
            from .ydd.yddimport_io import import_ydd as import_ydd_asset, find_ydd_external_dependencies
            from .yft.yftimport_io import import_yft as import_yft_asset, find_yft_external_dependencies
            from .ytyp.ytypimport_io import import_ytyp as import_ytyp_asset
            from .iecontext import import_context_scope, ImportContext

            prefs_import_settings = self.custom_settings if self.use_custom_settings else get_import_settings()
            import_settings = prefs_import_settings.to_import_context_settings()

            directory = Path(self.directory)

            def _import_asset_legacy(filename: str) -> bool:
                filepath = directory / filename
                if filename.endswith(YCD.file_extension):
                    import_ycd(str(filepath))
                elif filename.endswith(YMAP.file_extension):
                    import_ymap(str(filepath))
                elif filename.endswith(YNV.file_extension):
                    import_ynv(str(filepath))
                elif filepath.suffix in {".ycd", ".ymap", ".ynv"}:
                    logger.warning(
                        f"Binary resource format '{filepath.suffix}' is not supported yet. "
                        f"Export them to XML with CodeWalker first."
                    )
                else:
                    return False

                return True

            def _import_asset(filename: str) -> bool:
                filepath = directory / filename

                try:
                    if _import_asset_legacy(str(filepath)):
                        return True

                    asset = try_load_asset(filepath)
                    if asset is None:
                        if not IS_SZIO_NATIVE_AVAILABLE and filepath.suffix in {".ybn", ".ydr", ".ydd", ".yft", ".ytyp"}:
                            logger.warning(f"Could not import '{filepath}'. {PYMATERIA_REQUIRED_MSG}")
                        else:
                            logger.warning(f"Could not import '{filepath}'. Unsupported file format.")
                        return False

                    name = filepath.name
                    i = name.find('.')
                    if 0 < i < len(name) - 1:
                        name = name[:i]

                    # Search asset external dependencies
                    with import_context_scope(ImportContext(name, directory, import_settings)):
                        match asset.ASSET_TYPE:
                            case AssetType.DRAWABLE_DICTIONARY:
                                asset_with_deps = find_ydd_external_dependencies(asset, name)
                            case AssetType.FRAGMENT:
                                asset_with_deps = find_yft_external_dependencies(asset, name)
                            case _:
                                asset_with_deps = AssetWithDependencies(name, asset, {})

                        if asset_with_deps is not None:
                            # find dependencies can potentially change the main asset we are
                            # exporting, e.g. _hi to non-hi .yft
                            asset = asset_with_deps.main_asset
                            name = asset_with_deps.name

                    if asset_with_deps is None:
                        # Failed to find required dependencies, finder functions should have logged the error already
                        return False

                    # Import asset into Blender
                    with import_context_scope(ImportContext(name, directory, import_settings)):
                        match asset.ASSET_TYPE:
                            case AssetType.BOUND:
                                import_ybn_asset(asset, name)
                            case AssetType.DRAWABLE:
                                import_ydr_asset(asset, name)
                            case AssetType.DRAWABLE_DICTIONARY:
                                import_ydd_asset(asset_with_deps, name)
                            case AssetType.FRAGMENT:
                                import_yft_asset(asset_with_deps, name)
                            case AssetType.MAP_TYPES:
                                import_ytyp_asset(asset, name)
                            case _:
                                assert False, f"Unsupported asset type '{asset.ASSET_TYPE}'"

                    logger.info(f"Successfully imported '{filepath}'")
                    return True
                except:
                    logger.error(f"Error importing: {filepath} \n {traceback.format_exc()}")
                    return False

            for filename in filenames:
                _import_asset(filename)

            # Import the .ytyps after all the assets to ensure that the archetypes get linked to their object in case
            # they are imported together
            for filename in ytyp_filenames:
                _import_asset(filename)

            logger.info(f"Imported in {self.time_elapsed} seconds")
            return {"FINISHED"}

    def invoke(self, context, event):
        if self.directory and len(self.files) > 0 and self.files[0].name != "":
            # Already have a list of files, don't open the import window and do the import directly.
            # Invoked by the FileHandler below (or a manual operator call, but we don't currently do that).
            return self.execute(context)

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def _dedupe_hi_yft_filenames(self, filenames: list[str]) -> list[str]:
        """If the user selected both a non-hi .yft[.xml] and its _hi.yft[.xml], remove the _hi.yft[.xml] one to prevent
        importing the same model twice.
        """
        return [
            f for f in filenames
            if (
                (not f.endswith("_hi.yft.xml") or (f"{f[:-11]}.yft.xml" not in filenames and f"{f[:-11]}.yft" not in filenames)) and
                (not f.endswith("_hi.yft") or (
                    f"{f[:-7]}.yft.xml" not in filenames and f"{f[:-7]}.yft" not in filenames))
            )
        ]

    def _separate_ytyp_filenames(self, filenames: list[str]) -> tuple[list[str], list[str]]:
        """Separate the filenames list into two lists, one with all the assets and another one only with .ytyps."""
        asset_filenames, ytyp_filenames = [], []
        for f in filenames:
            dest = ytyp_filenames if f.endswith(".ytyp") or f.endswith(".ytyp.xml") else asset_filenames
            dest.append(f)
        return asset_filenames, ytyp_filenames


class SOLLUMZ_OT_import_assets(ImportAssetsOperatorImpl, Operator):
    """Import RAGE asset files"""
    bl_idname = "sollumz.import_assets"
    bl_label = "Import RAGE Assets"
    bl_options = {"UNDO"}


if bpy.app.version >= (4, 1, 0):
    class SOLLUMZ_FH_import(bpy.types.FileHandler):
        bl_idname = "SOLLUMZ_FH_import"
        bl_label = "File handler for RAGE assets import"
        bl_import_operator = SOLLUMZ_OT_import_assets.bl_idname
        # Supports handling multiple extensions, but doesn't support multi-dot extensions like .yft.xml. `.xml` should
        # be fine because the operator checks the extension, but it is a bit broad.
        bl_file_extensions = ".ybn;.ydr;.ydd;.yft;.ytyp;.xml;"

        @classmethod
        def poll_drop(cls, context):
            a = context.area
            return a is not None and not get_addon_preferences(context).legacy_import_export and (a.type == "VIEW_3D" or a.type == "OUTLINER")

    class SOLLUMZ_FH_import_legacy(bpy.types.FileHandler):
        bl_idname = "SOLLUMZ_FH_import_legacy"
        bl_label = "File handler for CodeWalker XML import"
        bl_import_operator = SOLLUMZ_OT_import_assets_legacy.bl_idname
        bl_file_extensions = ".xml"

        @classmethod
        def poll_drop(cls, context):
            a = context.area
            return a is not None and get_addon_preferences(context).legacy_import_export and (a.type == "VIEW_3D" or a.type == "OUTLINER")


def _collect_objects_for_export(context, limit_to_selected: bool) -> list[Object]:

    objs = context.scene.objects

    if limit_to_selected:
        objs = context.selected_objects

    return _get_only_parent_objs(objs)


def _get_only_parent_objs(objs: list[Object]) -> list[Object]:
    parent_objs = set()
    objs = set(objs)

    for obj in objs:
        parent_obj = find_sollumz_parent(obj)

        if parent_obj is None or parent_obj in parent_objs:
            continue

        parent_objs.add(parent_obj)

    return list(parent_objs)


class SOLLUMZ_OT_export_assets_legacy(TimedOperator, Operator):
    """Export CodeWalker XML files"""
    bl_idname = "sollumz.export_assets_legacy"
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

    def execute_timed(self, context: Context):
        with logger.use_operator_logger(self) as op_log:
            logger.info("Starting export...")
            export_settings = get_export_settings()
            objs = _collect_objects_for_export(context, export_settings.limit_to_selected)

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
                            logger.info(
                                f"Exported '{filepath}' with WARNINGS or ERRORS! Please check the Info Log for details.")
                            any_warnings_or_errors = True
                        else:
                            logger.info(f"Successfully exported '{filepath}'")
                    else:
                        if op_log.has_warnings_or_errors:
                            logger.info(
                                f"Failed to export '{obj.name}', ERRORS found! Please check the Info Log for details.")
                            any_warnings_or_errors = True
                except:
                    logger.error(f"Error exporting: {filepath or obj.name} \n {traceback.format_exc()}")
                    any_warnings_or_errors = True
                    return {"CANCELLED"}

            logger.info(f"Exported in {self.time_elapsed} seconds")
            if any_warnings_or_errors:
                bpy.ops.screen.info_log_show()
            return {"FINISHED"}

    def get_filepath(self, obj: Object, extension: str):
        name = remove_number_suffix(obj.name.lower())

        return os.path.join(self.directory, name + extension)


class SOLLUMZ_OT_export_assets(TimedOperator, Operator):
    """Export RAGE asset files"""
    bl_idname = "sollumz.export_assets"
    bl_label = "Export RAGE Assets"

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

    # These are for scripts that use these operators to override the settings and avoid messing with the user preferences.
    use_custom_settings: BoolProperty(name="Use Custom Settings", default=False, options={"HIDDEN", "SKIP_SAVE"})
    custom_settings: PointerProperty(type=ExportSettingsOverride,
                                     name="Custom Settings", options={"HIDDEN", "SKIP_SAVE"})

    def draw(self, context):
        prefs = get_addon_preferences(context)
        if prefs.legacy_import_export:
            return

        export_prefs = prefs.export_settings
        from szio.gta5 import AssetFormat, is_provider_available
        row = self.layout.row(align=False)
        col = row.column(align=True, heading="Format")
        for f in ("NATIVE", "CWXML"):
            subrow = col.row(align=True)
            subrow.enabled = is_provider_available(AssetFormat[f])
            subrow.prop_enum(export_prefs, "target_formats", f)

        col = row.column(align=True, heading="Version")
        for f in ("GEN8", "GEN9"):
            col.prop_enum(export_prefs, "target_versions", f)

    def invoke(self, context, event):
        if self.direct_export:
            return self.execute(context)
        else:
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

    def execute_timed(self, context: Context):
        with logger.use_operator_logger(self) as op_log:
            logger.info("Starting export...")
            prefs_export_settings = self.custom_settings if self.use_custom_settings else get_export_settings()
            objs = _collect_objects_for_export(context, prefs_export_settings.limit_to_selected)

            self.directory = bpy.path.abspath(self.directory)

            if not objs:
                if prefs_export_settings.limit_to_selected:
                    logger.info("No Sollumz objects selected for export!")
                else:
                    logger.info("No Sollumz objects in the scene to export!")
                return {"CANCELLED"}

            from pathlib import Path
            from .ybn.ybnexport_io import export_ybn as export_ybn_asset
            from .ydr.ydrexport_io import export_ydr as export_ydr_asset
            from .ydd.yddexport_io import export_ydd as export_ydd_asset
            from .yft.yftexport_io import export_yft as export_yft_asset
            from .iecontext import export_context_scope, ExportContext

            export_settings = prefs_export_settings.to_export_context_settings()
            if not export_settings.targets:
                from szio.gta5 import AssetFormat, AssetVersion, AssetTarget
                export_settings.targets = (AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8),)
                logger.warning(
                    "No export target found. Make sure you select both Format and Version in the export settings. "
                    "Defaulting to CW XML / Gen 8."
                )

            directory = Path(self.directory)

            any_warnings_or_errors = False
            for obj in objs:
                op_log.clear_log_counts()
                try:
                    asset_name = remove_number_suffix(obj.name.lower())
                    export_bundle = None
                    legacy_success = False
                    with export_context_scope(ExportContext(asset_name, export_settings)):
                        match obj.sollum_type:
                            case SollumType.BOUND_COMPOSITE:
                                export_bundle = export_ybn_asset(obj)
                            case SollumType.DRAWABLE:
                                export_bundle = export_ydr_asset(obj)
                            case SollumType.DRAWABLE_DICTIONARY:
                                export_bundle = export_ydd_asset(obj)
                            case SollumType.FRAGMENT:
                                export_bundle = export_yft_asset(obj)

                            # These assets still need legacy export
                            case SollumType.CLIP_DICTIONARY:
                                filepath = SOLLUMZ_OT_export_assets_legacy.get_filepath(self, obj, YCD.file_extension)
                                legacy_success = export_ycd(obj, filepath)
                            case SollumType.YMAP:
                                filepath = SOLLUMZ_OT_export_assets_legacy.get_filepath(self, obj, YMAP.file_extension)
                                legacy_success = export_ymap(obj, filepath)

                            case _:
                                assert False, f"Unsupported asset type '{obj.sollum_type}'"

                    success = export_bundle or legacy_success

                    if success:
                        if export_bundle:
                            export_bundle.save(directory)

                        if op_log.has_warnings_or_errors:
                            logger.info(
                                f"Exported '{obj.name}' with WARNINGS or ERRORS! Please check the Info Log for details."
                            )
                            any_warnings_or_errors = True
                        else:
                            logger.info(f"Successfully exported '{obj.name}'")
                    else:
                        if op_log.has_warnings_or_errors:
                            logger.info(
                                f"Failed to export '{obj.name}', ERRORS found! Please check the Info Log for details."
                            )
                            any_warnings_or_errors = True
                except:
                    logger.error(f"Error exporting: {obj.name} \n {traceback.format_exc()}")
                    any_warnings_or_errors = True
                    return {"CANCELLED"}

            logger.info(f"Exported in {self.time_elapsed} seconds")
            if any_warnings_or_errors:
                bpy.ops.screen.info_log_show()
            return {"FINISHED"}


if DEV_MODE:
    class SOLLUMZ_OT_dev_test_export_assets(Operator):
        bl_idname = "sollumz.dev_test_export_assets"
        bl_label = "[DEV] Test Export"

        directory: bpy.props.StringProperty(
            name="Output directory",
            description="Select export output directory",
            subtype="DIR_PATH",
            options={"HIDDEN"}
        )

        def draw(self, context):
            export_prefs = get_addon_preferences(context).export_settings
            self.layout.prop(export_prefs, "formats")

        def invoke(self, context, event):
            context.window_manager.fileselect_add(self)
            return {"RUNNING_MODAL"}

        def execute(self, context: Context):
            from pathlib import Path
            d = Path(self.directory)
            io_dir = d / "io"
            io_dir.mkdir(exist_ok=True)
            legacy_dir = d / "legacy"
            legacy_dir.mkdir(exist_ok=True)
            bpy.ops.sollumz.export_assets(directory=str(io_dir), direct_export=True)
            bpy.ops.sollumz.export_assets_legacy(directory=str(legacy_dir), direct_export=True)

            io_files = list(io_dir.iterdir())
            legacy_files = list(legacy_dir.iterdir())
            self.report({"INFO"}, f"{io_files=}")
            self.report({"INFO"}, f"{legacy_files=}")

            for legacy_file in legacy_dir.iterdir():
                if not legacy_file.is_file():
                    continue

                io_file = io_dir / legacy_file.name
                legacy_size = legacy_file.stat().st_size
                io_size = io_file.stat().st_size
                self.report({"INFO"}, f"=============== {legacy_file.name} ===============")
                self.report({"INFO"}, f"  legacy {legacy_size}  bytes")
                self.report({"INFO"}, f"      io {io_size}  bytes   ({io_size - legacy_size} bytes)")

            return {"FINISHED"}


class SOLLUMZ_OT_paint_vertices(SOLLUMZ_OT_base, Operator):
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
        if False:  # empty generator
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
        if False:  # empty generator
            yield

    def run(self, context):
        for flags in self.iter_selection_flags(context):
            if not ClearTimeFlags._process_one(flags, context):
                return False
        return True


_MENU_LABEL = "RAGE Asset (.ydr, .ydd, .yft, .ybn, .ytyp, .ymap, .ycd, .y*.xml)"
_MENU_LABEL_LEGACY = f"CodeWalker XML ({YDR.file_extension}, {YDD.file_extension}, {YFT.file_extension}, {YBN.file_extension}, {YCD.file_extension})"


def sollumz_menu_func_import(self, context):
    if get_addon_preferences(context).legacy_import_export:
        op = SOLLUMZ_OT_import_assets_legacy
        label = _MENU_LABEL_LEGACY
    else:
        op = SOLLUMZ_OT_import_assets
        label = _MENU_LABEL

    self.layout.operator(op.bl_idname, text=label)


def sollumz_menu_func_export(self, context):
    if get_addon_preferences(context).legacy_import_export:
        op = SOLLUMZ_OT_export_assets_legacy
        label = _MENU_LABEL_LEGACY
    else:
        op = SOLLUMZ_OT_export_assets
        label = _MENU_LABEL

    self.layout.operator(op.bl_idname, text=label)


class SOLLUMZ_OT_copy_location(Operator):
    """Copy the location of an object to the clipboard"""
    bl_idname = "wm.sollumz_copy_location"
    bl_label = ""
    location: bpy.props.StringProperty()

    def execute(self, context):
        bpy.context.window_manager.clipboard = self.location
        self.report(
            {'INFO'}, "Location copied to clipboard: {}".format(self.location))
        return {'FINISHED'}


class SOLLUMZ_OT_copy_rotation(Operator):
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


class SOLLUMZ_OT_paste_location(Operator):
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


class SOLLUMZ_OT_paste_rotation(Operator):
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


class SOLLUMZ_OT_set_sollum_type(Operator):
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
