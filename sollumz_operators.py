import traceback
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
from pathlib import Path
from typing import Literal
from mathutils import Quaternion
from .sollumz_helper import SOLLUMZ_OT_base, find_sollumz_parent
from .sollumz_properties import SollumType, SOLLUMZ_UI_NAMES, TimeFlagsMixin
from .sollumz_preferences import get_addon_preferences, get_import_settings, get_export_settings, ImportSettingsBase, ExportSettingsBase
from szio.gta5.cwxml import (
    YNV,
    YCD,
    YMAP,
)
from .ynv.ynvimport import import_ynv
from .ycd.ycdimport import import_ycd
from .ycd.ycdexport import export_ycd
from .ymap.ymapexport import export_ymap as deprecated_export_ymap
from .tools.blenderhelper import remove_number_suffix
from .dependencies import IS_SZIO_NATIVE_AVAILABLE, PYMATERIA_REQUIRED_MSG
from .iecontext import (
    export_context_scope,
    ExportContext,
    ExportBundle,
    import_context_scope,
    ImportContext,
)

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


class ImportAssetsOperatorImpl(ImportSettingsBase, TimedOperator):
    """Import RAGE asset files"""
    directory: bpy.props.StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})
    files: bpy.props.CollectionProperty(
        name="File Path",
        type=bpy.types.OperatorFileListElement,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    filter_glob: bpy.props.StringProperty(
        default="".join(f"*{ext};" for ext in (
            ".ybn", ".ydr", ".ydd", ".yft", ".ytyp", ".ytd",
            ".ybn.xml", ".ydr.xml", ".ydd.xml", ".yft.xml", ".ytyp.xml", ".ytd.xml", ".ymap.xml", ".ycd.xml", ".ynv.xml"
        )),
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    # These are for scripts that use these operators to override the settings and avoid messing with the user preferences.
    use_custom_settings: BoolProperty(
        name="Use Custom Settings",
        description="Use the settings defined in this operator instead of user preferences",
        default=False,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    import_as_asset: BoolProperty(
        name="Import To Asset Library",
        description="Import selected files to the current blend file asset library",
        default=False,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    @classmethod
    def description(cls, _context, properties) -> str:
        if properties.import_as_asset:
            return "Import selected files to the current blend file asset library"

        return cls.bl_description

    def draw(self, context):
        pass

    def execute_timed(self, context):
        with logger.use_operator_logger(self):
            if not self.directory or len(self.files) == 0 or self.files[0].name == "":
                logger.info("No file selected for import!")
                return {"CANCELLED"}

            self.directory = bpy.path.abspath(self.directory)

            filenames = [f.name for f in self.files]
            filenames, ytd_filenames = self._separate_ytd_filenames(filenames)
            ytd_filenames = self._dedupe_hi_ytd_filenames(ytd_filenames)
            ytd_filenames = self._dedupe_hd_txd_filenames(ytd_filenames, filenames)
            filenames, ytyp_filenames = self._separate_ytyp_filenames(filenames)
            filenames, ymap_filenames = self._separate_ymap_filenames(filenames)
            filenames = self._dedupe_hi_yft_filenames(filenames)

            from pathlib import Path
            from szio import VPath
            from szio.gta5 import try_load_asset, AssetType, AssetWithDependencies
            from .ybn.ybnimport import import_ybn as import_ybn_asset
            from .ydr.ydrimport import import_ydr as import_ydr_asset, find_ydr_external_dependencies
            from .ydd.yddimport import import_ydd as import_ydd_asset, find_ydd_external_dependencies
            from .yft.yftimport import import_yft as import_yft_asset, find_yft_external_dependencies
            from .ytyp.ytypimport import import_ytyp as import_ytyp_asset
            from .ytd.ytdimport import import_ytd as import_ytd_asset, find_ytd_external_dependencies
            from .ymap_next.ymapimport import import_ymap as import_ymap_asset, begin_import_ymap_group, end_import_ymap_group

            prefs_import_settings = self if self.use_custom_settings else get_import_settings()
            import_settings = prefs_import_settings.to_import_context_settings(import_as_asset=self.import_as_asset)

            directory = Path(self.directory)

            def _import_asset_legacy(filename: str) -> bool:
                filepath = directory / filename
                if filename.endswith(YCD.file_extension):
                    import_ycd(str(filepath))
                elif filename.endswith(YNV.file_extension):
                    import_ynv(str(filepath))
                elif filepath.suffix in {".ycd", ".ynv"}:
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

                    if (load_result := try_load_asset(VPath(filepath), return_target=True)) is None:
                        if not IS_SZIO_NATIVE_AVAILABLE and filepath.suffix in {".ybn", ".ydr", ".ydd", ".yft", ".ytyp", ".ytd", ".ymap"}:
                            logger.warning(f"Could not import '{filepath}'. {PYMATERIA_REQUIRED_MSG}")
                        else:
                            logger.warning(f"Could not import '{filepath}'. Unsupported file format.")
                        return False

                    asset, asset_target = load_result

                    name = filepath.name
                    i = name.find('.')
                    if 0 < i < len(name) - 1:
                        name = name[:i]

                    # Search asset external dependencies
                    with import_context_scope(ImportContext(name, asset_target, directory, import_settings)):
                        match asset.ASSET_TYPE:
                            case AssetType.DRAWABLE:
                                asset_with_deps = find_ydr_external_dependencies(asset, name)
                            case AssetType.DRAWABLE_DICTIONARY:
                                asset_with_deps = find_ydd_external_dependencies(asset, name)
                            case AssetType.FRAGMENT:
                                asset_with_deps = find_yft_external_dependencies(asset, name)
                            case AssetType.TEXTURE_DICTIONARY:
                                asset_with_deps = find_ytd_external_dependencies(asset, name)
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
                    with import_context_scope(ImportContext(name, asset_target, directory, import_settings)):
                        match asset.ASSET_TYPE:
                            case AssetType.BOUND:
                                import_ybn_asset(asset, name)
                            case AssetType.DRAWABLE:
                                import_ydr_asset(asset_with_deps, name)
                            case AssetType.DRAWABLE_DICTIONARY:
                                import_ydd_asset(asset_with_deps, name)
                            case AssetType.FRAGMENT:
                                import_yft_asset(asset_with_deps, name)
                            case AssetType.MAP_TYPES:
                                import_ytyp_asset(asset, name)
                            case AssetType.TEXTURE_DICTIONARY:
                                import_ytd_asset(asset_with_deps, name)
                            case AssetType.MAP_DATA:
                                import_ymap_asset(asset, name)
                            case _:
                                assert False, f"Unsupported asset type '{asset.ASSET_TYPE}'"

                    logger.info(f"Successfully imported '{filepath}'")
                    return True
                except:
                    logger.error(f"Error importing: {filepath} \n {traceback.format_exc()}")
                    return False

            # Import the .ytds before all the assets to ensure that their images are used
            for filename in ytd_filenames:
                _import_asset(filename)

            for filename in filenames:
                _import_asset(filename)

            # Import the .ytyps and .ymaps after all the assets to ensure that the archetypes get linked to their object
            # in case they are imported together
            for filename in ytyp_filenames:
                _import_asset(filename)

            begin_import_ymap_group()
            for filename in ymap_filenames:
                _import_asset(filename)
            end_import_ymap_group()

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

    def _dedupe_hi_ytd_filenames(self, filenames: list[str]) -> list[str]:
        """If the user selected both a base .ytd[.xml] and its +hi.ytd[.xml], remove the +hi.ytd[.xml] one to prevent
        importing the same texture dictionary twice.
        """
        return [
            f for f in filenames
            if (
                (not f.endswith("+hi.ytd.xml") or (
                    f"{f[:-11]}.ytd.xml" not in filenames and f"{f[:-11]}.ytd" not in filenames)) and
                (not f.endswith("+hi.ytd") or (
                    f"{f[:-7]}.ytd.xml" not in filenames and f"{f[:-7]}.ytd" not in filenames))
            )
        ]

    def _dedupe_hd_txd_filenames(self, ytd_filenames: list[str], asset_filenames: list[str]) -> list[str]:
        """If the user selected a model along with its HD textures .ytd[.xml] (e.g. 'foo.ydr' and
        'foo+hidr.ytd'), remove the HD .ytd so it is not also imported as a standalone texture dictionary.
        The model import loads it by itself.
        """
        def _is_hd_txd_of_selected_asset(f: str) -> bool:
            base = f.removesuffix(".xml").removesuffix(".ytd")
            for suffix, asset_exts in (("+hidr", (".ydr",)), ("+hifr", (".yft", "_hi.yft")), ("+hidd", (".ydd",))):
                if base.endswith(suffix):
                    name = base.removesuffix(suffix)
                    return any(f"{name}{e}{x}" in asset_filenames for e in asset_exts for x in ("", ".xml"))
            return False

        return [f for f in ytd_filenames if not _is_hd_txd_of_selected_asset(f)]

    def _separate_filenames_with_extension(self, ext: str, filenames: list[str]) -> tuple[list[str], list[str]]:
        """Separate the filenames list into two lists, one with all the assets and another one only with the specified extension."""
        other_filenames, filenames_with_ext = [], []
        ext_xml = f"{ext}.xml"
        for f in filenames:
            dest = filenames_with_ext if f.endswith(ext) or f.endswith(ext_xml) else other_filenames
            dest.append(f)
        return other_filenames, filenames_with_ext

    def _separate_ytd_filenames(self, filenames: list[str]) -> tuple[list[str], list[str]]:
        """Separate the filenames list into two lists, one with all the assets and another one only with .ytds."""
        return self._separate_filenames_with_extension(".ytd", filenames)

    def _separate_ytyp_filenames(self, filenames: list[str]) -> tuple[list[str], list[str]]:
        """Separate the filenames list into two lists, one with all the assets and another one only with .ytyps."""
        return self._separate_filenames_with_extension(".ytyp", filenames)

    def _separate_ymap_filenames(self, filenames: list[str]) -> tuple[list[str], list[str]]:
        """Separate the filenames list into two lists, one with all the assets and another one only with .ymaps."""
        return self._separate_filenames_with_extension(".ymap", filenames)


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
        bl_file_extensions = ".ybn;.ydr;.ydd;.yft;.ytyp;.ytd;.ymap;.xml;"

        @classmethod
        def poll_drop(cls, context):
            a = context.area
            return a is not None and (a.type == "VIEW_3D" or a.type == "OUTLINER")


def _collect_objects_for_export(context, limit_to_selected: bool) -> list[Object]:

    objs = context.scene.objects

    if limit_to_selected:
        objs = context.view_layer.objects.selected

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


class ExportAssetsOperatorImpl(ExportSettingsBase, TimedOperator):
    """Export RAGE asset files"""

    sz_export_types = {"OBJECT", "YTYP", "YMAP", "YTD"}
    """Types of exports to handle in this operator."""

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
    use_custom_settings: BoolProperty(
        name="Use Custom Settings",
        description="Use the settings defined in this operator instead of user preferences",
        default=False,
        options={"HIDDEN", "SKIP_SAVE"}
    )

    def draw(self, context):
        prefs = get_addon_preferences(context)
        export_prefs = prefs.export_settings
        from szio.gta5 import AssetFormat, is_provider_available
        row = self.layout.row(align=False)
        col = row.column(align=True, heading="Format")
        for f in ("NATIVE", "CWXML"):
            if is_provider_available(AssetFormat[f]):
                col.prop_enum(export_prefs, "target_formats", f)

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
            prefs_export_settings = self if self.use_custom_settings else get_export_settings()
            if "OBJECT" in self.sz_export_types:
                objs = _collect_objects_for_export(context, prefs_export_settings.limit_to_selected)
            else:
                objs = []

            if "YTYP" in self.sz_export_types:
                export_ytyps = (
                    # only consider prefs in the generic export operator, the concrete one for YTYPs always exports them
                    (self.sz_export_types == {"YTYP"} or prefs_export_settings.export_ytyps) and
                    context.scene.ytyps
                )
            else:
                export_ytyps = False

            if "YMAP" in self.sz_export_types:
                from .ymap_next.properties.map import get_maps
                export_ymaps = (
                    # only consider prefs in the generic export operator, the concrete one for YMAPs always exports them
                    (self.sz_export_types == {"YMAP"} or prefs_export_settings.export_ymaps) and
                    (maps := get_maps(context)) and maps.groups
                )
            else:
                export_ymaps = False

            if "YTD" in self.sz_export_types:
                export_ytds = (
                    # only consider prefs in the generic export operator, the concrete one for YTDs always exports them
                    (self.sz_export_types == {"YTD"} or prefs_export_settings.export_ytds) and
                    context.scene.sz_txds.texture_dictionaries
                )
            else:
                export_ytds = False

            self.directory = bpy.path.abspath(self.directory)

            if not objs and not export_ytyps and not export_ymaps and not export_ytds:
                if prefs_export_settings.limit_to_selected:
                    logger.info("No Sollumz objects selected for export!")
                else:
                    logger.info("No Sollumz objects in the scene to export!")
                return {"CANCELLED"}


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

            if objs:
                any_warnings_or_errors = self._export_objects(objs, directory, export_settings, op_log) or any_warnings_or_errors

            if export_ytyps:
                ytyps = self._collect_ytyps_for_export(context, prefs_export_settings.export_ytyps_include)
                any_warnings_or_errors = self._export_ytyps(context, ytyps, directory, export_settings, op_log) or any_warnings_or_errors

            if export_ymaps:
                ymaps = self._collect_ymaps_for_export(context, prefs_export_settings.export_ymaps_include)
                any_warnings_or_errors = self._export_ymaps(context, ymaps, directory, export_settings, op_log) or any_warnings_or_errors

            if export_ytds:
                ytds = self._collect_ytds_for_export(context, prefs_export_settings.export_ytds_include)
                any_warnings_or_errors = self._export_ytds(context, ytds, directory, export_settings, op_log) or any_warnings_or_errors

            logger.info(f"Exported in {self.time_elapsed} seconds")
            if any_warnings_or_errors and bpy.ops.screen.info_log_show.poll():
                bpy.ops.screen.info_log_show()
            return {"FINISHED"}

    def _export_objects(self, objs: list[Object], directory: Path, export_settings, op_log) -> bool:
        from .ybn.ybnexport import export_ybn as export_ybn_asset
        from .ydr.ydrexport import export_ydr as export_ydr_asset
        from .ydd.yddexport import export_ydd as export_ydd_asset
        from .yft.yftexport import export_yft as export_yft_asset

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

                        # These assets are still exported by writing directly to a file instead of through ExportBundle
                        case SollumType.CLIP_DICTIONARY:
                            legacy_success = export_ycd(obj, str(directory / (asset_name + YCD.file_extension)))
                        case SollumType.DEPRECATED__YMAP:
                            legacy_success = deprecated_export_ymap(obj, str(directory / (asset_name + YMAP.file_extension)))

                        case _:
                            assert False, f"Unsupported asset type '{obj.sollum_type}'"


                any_warnings_or_errors = self._save_bundle(obj.name, export_bundle, directory, export_settings, op_log, legacy_success=legacy_success) or any_warnings_or_errors
            except:
                logger.error(f"Error exporting: {obj.name} \n {traceback.format_exc()}")
                any_warnings_or_errors = True

        return any_warnings_or_errors

    def _collect_ytyps_for_export(self, context, include: Literal["ALL", "SELECTED"]) -> list[int]:
        n = len(context.scene.ytyps)
        if include == "SELECTED":
            # no multiselection yet, can only select one
            idx = context.scene.ytyp_index
            return [idx] if 0 <= idx < n else []
        else:
            return list(range(n))

    def _export_ytyps(self, context, ytyp_indices: list[int], directory: Path, export_settings, op_log) -> bool:
        from .ytyp.ytypexport import export_ytyp as export_ytyp_asset

        any_warnings_or_errors = False

        for ytyp_index in ytyp_indices:
            op_log.clear_log_counts()
            ytyp_name = context.scene.ytyps[ytyp_index].name
            try:
                with export_context_scope(ExportContext(ytyp_name, export_settings)):
                    export_bundle = export_ytyp_asset(context.scene, ytyp_index)

                any_warnings_or_errors = self._save_bundle(ytyp_name, export_bundle, directory, export_settings, op_log) or any_warnings_or_errors
            except Exception:
                logger.error(f"Error exporting: {ytyp_name} \n {traceback.format_exc()}")
                any_warnings_or_errors = True

        return any_warnings_or_errors

    def _collect_ymaps_for_export(self, context, include: Literal["ALL", "SELECTED"]) -> list[int]:
        from .ymap_next.properties.map import get_maps

        map_groups = get_maps(context).groups
        if include == "SELECTED":
            return map_groups.selected_items_indices
        else:
            return list(range(len(map_groups)))

    def _export_ymaps(self, context, ymap_indices: list[int], directory: Path, export_settings, op_log) -> bool:
        from .ymap_next.properties.map import get_maps
        from .ymap_next.ymapexport import export_ymap as export_ymap_asset

        any_warnings_or_errors = False
        maps = get_maps(context)
        for map_group_index in ymap_indices:
            op_log.clear_log_counts()
            map_group = maps.groups[map_group_index]
            try:
                asset_name = map_group.name.lower()
                with export_context_scope(ExportContext(asset_name, export_settings)):
                    export_bundles = export_ymap_asset(map_group)

                any_warnings_or_errors = self._save_bundle(map_group.name, export_bundles, directory, export_settings, op_log) or any_warnings_or_errors
            except Exception:
                logger.error(f"Error exporting: {map_group.name} \n {traceback.format_exc()}")
                any_warnings_or_errors = True

        return any_warnings_or_errors

    def _collect_ytds_for_export(self, context, include: Literal["ALL", "SELECTED"]) -> list[int]:
        txds = context.scene.sz_txds.texture_dictionaries
        if include == "SELECTED":
            return txds.selected_items_indices
        else:
            return list(range(len(txds)))

    def _export_ytds(self, context, txd_indices: list[int], directory: Path, export_settings, op_log) -> bool:
        from .ytd.ytdexport import export_ytd as export_ytd_asset

        any_warnings_or_errors = False

        for txd_index in txd_indices:
            op_log.clear_log_counts()
            txd = context.scene.sz_txds.texture_dictionaries[txd_index]
            try:
                asset_name = txd.name.lower()
                with export_context_scope(ExportContext(asset_name, export_settings)):
                    export_bundle = export_ytd_asset(txd)

                any_warnings_or_errors = self._save_bundle(txd.name, export_bundle, directory, export_settings, op_log) or any_warnings_or_errors
            except Exception:
                logger.error(f"Error exporting: {txd.name} \n {traceback.format_exc()}")
                any_warnings_or_errors = True

        return any_warnings_or_errors

    def _save_bundle(self, name: str, export_bundle: ExportBundle | list[ExportBundle] | None, directory: Path, export_settings, op_log, legacy_success=False) -> bool:
        any_warnings_or_errors = False
        export_bundles = export_bundle if isinstance(export_bundle, list) else [export_bundle] if export_bundle else []
        success = legacy_success or (export_bundles and all(b.is_valid() for b in export_bundles))
        if success:
            for b in export_bundles:
                if b:
                    b.save(directory, export_settings.targets)

            if op_log.has_warnings_or_errors:
                logger.info(
                    f"Exported '{name}' with WARNINGS or ERRORS! Please check the Info Log for details."
                )
                any_warnings_or_errors = True
            else:
                logger.info(f"Successfully exported '{name}'")
        else:
            if op_log.has_warnings_or_errors:
                logger.info(
                    f"Failed to export '{name}', ERRORS found! Please check the Info Log for details."
                )
                any_warnings_or_errors = True

        return any_warnings_or_errors


class SOLLUMZ_OT_export_assets(ExportAssetsOperatorImpl, Operator):
    """Export RAGE asset files"""
    bl_idname = "sollumz.export_assets"
    bl_label = "Export RAGE Assets"


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


def sollumz_menu_func_import(self, context):
    self.layout.operator(SOLLUMZ_OT_import_assets.bl_idname, text=_MENU_LABEL)


def sollumz_menu_func_export(self, context):
    self.layout.operator(SOLLUMZ_OT_export_assets.bl_idname, text=_MENU_LABEL)


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

    @classmethod
    def poll(cls, context):
        if context.active_object is None:
            cls.poll_message_set("No active object selected.")
            return False
        return True

    def execute(self, context):
        def parse_location_string(location_string):
            pattern = r"(-?\d+\.\d+)"
            matches = re.findall(pattern, location_string)
            if len(matches) == 3:
                return float(matches[0]), float(matches[1]), float(matches[2])
            else:
                return None

        location_string = context.window_manager.clipboard

        location = parse_location_string(location_string)
        if location is not None:
            context.active_object.location = location
            self.report({'INFO'}, "Location set successfully.")
        else:
            self.report({'ERROR'}, "Invalid location string.")

        return {'FINISHED'}


class SOLLUMZ_OT_paste_rotation(Operator):
    """Paste the rotation (as quaternion) of an object from the clipboard and apply it"""
    bl_idname = "wm.sollumz_paste_rotation"
    bl_label = "Paste Rotation"

    @classmethod
    def poll(cls, context):
        if context.active_object is None:
            cls.poll_message_set("No active object selected.")
            return False
        return True

    def execute(self, context):
        rotation_string = context.window_manager.clipboard

        rotation_quaternion = parse_rotation_string(rotation_string)
        if rotation_quaternion is not None:
            obj = context.active_object
            prev_rotation_mode = obj.rotation_mode
            obj.rotation_mode = "QUATERNION"
            obj.rotation_quaternion = rotation_quaternion
            obj.rotation_mode = prev_rotation_mode

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
            {"INFO"}, f"Sollum Type successfully set to {SOLLUMZ_UI_NAMES[sollum_type]}.")

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
