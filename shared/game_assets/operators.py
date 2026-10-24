import os
import functools
import posixpath
import time
from collections.abc import Iterable, Iterator
from contextlib import contextmanager
from pathlib import Path

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    StringProperty,
    IntProperty,
)
from bpy.types import (
    AssetRepresentation,
    Operator,
    PropertyGroup,
)
from szio.jenkhash import name_to_hash

from ... import logger
from ...dependencies import IS_SZIO_NATIVE_AVAILABLE, PYMATERIA_REQUIRED_MSG
from ...sollumz_preferences import (
    ImportSettingsBase,
    get_addon_preferences,
    get_import_settings,
    invoke_with_game_directory,
    save_game_directory,
)
from ...sollumz_operators import SOLLUMZ_OT_import_assets
from ...tools.blenderhelper import remove_number_suffix
from .asset_info import (
    AssetArchetypeInfo,
    try_get_asset_representation_archetype_info,
)
from .game_files import ArchetypeFiles, find_game_asset_files, is_game_installation
from .library import (
    asset_cache_path,
    build_library,
    build_library_cache,
)

NEW_TAG = "<<NEW>>"


def _output_directory_choice_items(self, context):
    prefs = get_addon_preferences(context)
    items = []
    for d in prefs.shared_assets_directories:
        if not d.path:
            continue
        items.append((d.path, f"{d.name} | {d.path}", ""))
    items.append((NEW_TAG, "New...", "Save it to a new asset library directory"))
    return items


_build_library_progress = None


def temporary_ui(layout):
    op = layout.operator(SOLLUMZ_OT_import_assets.bl_idname, text="Import To Asset Library", icon="IMPORT")
    op.import_as_asset = True
    layout.operator(SOLLUMZ_OT_build_game_asset_library.bl_idname)
    if _build_library_progress is not None:
        completed, total = _build_library_progress
        layout.progress(
            text=f"Creating Asset Libraries ({completed}/{total})...",
            factor=completed / total if total > 0 else 0,
        )
    layout.operator(SOLLUMZ_OT_rebuild_game_asset_cache.bl_idname)


class SOLLUMZ_OT_build_game_asset_library(Operator):
    bl_idname = "sollumz.build_game_asset_library"
    bl_label = "Build Asset Library"
    bl_description = (
        "Import .ytyp game files from a directory and create .blend asset library files "
        "in the configured Shared Assets directory"
    )

    directory: StringProperty(
        name="Source Directory",
        description="Directory containing .ytyp files and their assets",
        subtype="DIR_PATH",
        options={"HIDDEN"},
    )

    filter_glob: StringProperty(
        default="*.ytyp;*.ytyp.xml",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    output_directory: StringProperty(
        name="Output Directory",
        description="Directory where .blend libraries should be saved",
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    output_directory_choice: EnumProperty(
        name="Output Library",
        description="Which directory to write the .blend libraries into",
        items=_output_directory_choice_items,
        options={"SKIP_SAVE"},
    )
    new_output_directory_name: StringProperty(
        name="Name",
        description="Name of the new asset library",
    )
    new_output_directory_path: StringProperty(
        name="Path",
        description="Path to a directory where to store the new asset library",
    )

    pattern: StringProperty(
        name="Pattern",
        description=(
            "Regular expression matched against .ytyp file names to filter which ones are imported. "
            "Leave empty to import all"
        ),
    )
    num_subprocesses: IntProperty(
        name="Subprocesses",
        description=(
            "Number of Blender subprocesses to spawn for building libraries in parallel. "
            "Each worker runs a separate Blender instance, so higher values build faster but use more memory and CPU"
        ),
        default=max(1, os.cpu_count() // 4),
        min=1,
        max=os.cpu_count(),
    )

    @classmethod
    def poll(cls, context):
        if bpy.app.version < (4, 2, 0):
            # Currently, we use Blender CLI commands to spawn the subprocess workers which were added in 4.2.
            cls.poll_message_set("Cannot build library on this Blender version. Update to Blender 4.2 or newer.")
            return False

        return True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(self, "output_directory_choice")
        if self.output_directory_choice == NEW_TAG:
            col.prop(self, "new_output_directory_name")
            col.prop(self, "new_output_directory_path")

        layout.prop(self, "pattern")
        layout.prop(self, "num_subprocesses")

    def execute(self, context):
        if not self.output_directory:
            prefs = get_addon_preferences(context)
            if self.output_directory_choice == NEW_TAG:
                new_directory = Path(bpy.path.abspath(self.new_output_directory_path))
                try:
                    new_directory.mkdir(parents=True, exist_ok=True)
                except FileExistsError:
                    self.report({"ERROR"}, f"Expected a directory, not a file: {str(new_directory)}")
                    return {"CANCELLED"}

                self.output_directory = self.new_output_directory_path
                bpy.ops.sollumz.prefs_shared_assets_directory_add(
                    name=self.new_output_directory_name, path=self.new_output_directory_path
                )
            else:
                if not prefs.shared_assets_directories:
                    self.report({"ERROR"}, "No Shared Assets directory configured. Add one in Preferences > Sollumz.")
                    return {"CANCELLED"}

                configured_paths = [d.path for d in prefs.shared_assets_directories if d.path]
                if len(configured_paths) > 1:
                    if self.output_directory_choice and self.output_directory_choice in configured_paths:
                        self.output_directory = self.output_directory_choice
                    else:
                        self.report({"WARNING"}, "No output library selected; using the first configured directory.")
                        self.output_directory = configured_paths[0]
                else:
                    self.output_directory = configured_paths[0]

        output_directory = Path(bpy.path.abspath(self.output_directory))
        output_directory.mkdir(parents=True, exist_ok=True)

        source_directory = Path(bpy.path.abspath(self.directory))
        if not source_directory.is_dir():
            self.report({"ERROR"}, f"Source directory does not exist: '{source_directory}'")
            return {"CANCELLED"}

        work_iter = build_library(
            source_directory,
            output_directory,
            game_catalog="GTA5",
            num_subprocesses=self.num_subprocesses,
            typ_pattern=self.pattern,
            report_progress_cb=_report_build_library_progress,
        )
        bpy.app.timers.register(functools.partial(_timer_do_work, work_iter), first_interval=0.0, persistent=True)
        return {"FINISHED"}


def _report_build_library_progress(num_completed: int | None, num_total: int | None):
    global _build_library_progress
    if num_completed is None:
        # finished
        _build_library_progress = None
    else:
        _build_library_progress = num_completed, num_total


def _timer_do_work(work_iter):
    interval = next(work_iter, None)
    return interval


class SOLLUMZ_OT_rebuild_game_asset_cache(Operator):
    bl_idname = "sollumz.rebuild_game_asset_cache"
    bl_label = "Debug - Rebuild Asset Cache"
    bl_description = "Rebuild the SQLite asset cache from existing .blend files in the Shared Assets directory"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return len(prefs.shared_assets_directories) > 0

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if not prefs.shared_assets_directories:
            self.report({"ERROR"}, "No Shared Assets directory configured.")
            return {"CANCELLED"}

        directories = []
        for d in prefs.shared_assets_directories:
            if not d.path:
                continue
            path = Path(bpy.path.abspath(d.path))
            if not path.is_dir():
                self.report({"WARNING"}, f"Shared Assets directory does not exist, skipping: '{path}'")
                continue
            directories.append(path)

        if not directories:
            self.report({"ERROR"}, "No valid Shared Assets directories found.")
            return {"CANCELLED"}

        build_library_cache(directories)
        self.report({"INFO"}, f"Asset cache rebuilt at '{asset_cache_path()}'")
        return {"FINISHED"}


def get_active_game_asset(context) -> AssetArchetypeInfo | None:
    """Return the archetype information of the active asset in the Asset Browser if it is an asset from a game asset
    library, otherwise `None`.
    """
    return try_get_asset_representation_archetype_info(getattr(context, "asset", None))


def iter_selected_game_assets(context) -> Iterator[tuple[AssetRepresentation, AssetArchetypeInfo]]:
    """Iterate the selected assets in the Asset Browser that are from a game asset library, with their archetype
    information.
    """
    assets = getattr(context, "selected_assets", None) or (getattr(context, "asset", None),)
    for asset in assets:
        if (archetype_info := try_get_asset_representation_archetype_info(asset)) is not None:
            yield asset, archetype_info


def _validated_game_directory(operator: Operator, context) -> Path | None:
    """The GTA V installation directory selected in `operator`, which is saved in the preferences. Logs an error and
    returns `None` if it is not a game installation.
    """
    if not operator.directory:
        logger.error("No GTA V installation directory selected.")
        return None

    game_dir = Path(bpy.path.abspath(operator.directory))
    if not is_game_installation(game_dir):
        logger.error(f"'{operator.directory}' is not a GTA V installation directory.")
        return None

    save_game_directory(game_dir, context)
    return game_dir


@contextmanager
def _wait_cursor(context):
    window = context.window
    if window is not None:
        window.cursor_modal_set("WAIT")
    try:
        yield
    finally:
        if window is not None:
            window.cursor_modal_restore()


def _find_game_asset_files_batch(
    context, game_dir: Path, assets: Iterable[tuple[str, str]]
) -> list[ArchetypeFiles | None]:
    # Finding the files needs to index the whole game directory the first time, which takes a while
    with _wait_cursor(context):
        ytyp_cache = {}
        found_files = []
        for asset_name, ytyp_name in assets:
            files = find_game_asset_files(game_dir, asset_name, ytyp_name, ytyp_cache=ytyp_cache)
            if files is None:
                logger.error(f"Could not find the game files of '{asset_name}'.")
            found_files.append(files)
        return found_files


def _import_game_asset_files(files: Iterable[ArchetypeFiles]) -> list[str]:
    """Import the game files of assets with the Import RAGE Assets operator and the user import settings. Files shared
    by multiple assets, such as texture dictionaries, are only imported once, and texture dictionaries already in the
    scene are not imported again. Returns the errors reported by the import.
    """
    import_settings = get_import_settings()
    import_kwargs = {name: getattr(import_settings, name) for name in ImportSettingsBase.__annotations__}
    textures_mode = import_kwargs["textures_mode"]
    has_custom_dir = bool(import_kwargs["textures_extract_custom_directory"])
    if textures_mode == "IMPORT_DIR" or (textures_mode == "CUSTOM_DIR" and not has_custom_dir):
        # Cannot extract textures next to the imported files, they are inside the game archives
        import_kwargs["textures_mode"] = "PACK"

    # Disable external skeleton since drawable dictionaries used in .ytyp don't use external skeletons, only peds do
    import_kwargs["dwd_import_external_skeleton"] = "NO"

    # Import all files in a single call, from their common directory and with their paths relative to it as names. The
    # import operator imports .ytds before the models, so their textures are used by the model materials
    files = list(files)
    scene_txds = {name_to_hash(txd.name) for txd in bpy.context.scene.sz_txds.texture_dictionaries}
    txd_paths = [
        f.txd for f in files if f.txd is not None and name_to_hash(f.txd.name.split(".", 1)[0]) not in scene_txds
    ]
    asset_paths = [f.asset for f in files if f.asset is not None]
    paths = list(dict.fromkeys(str(p) for p in (*txd_paths, *asset_paths)))
    if not paths:
        return []

    directory = posixpath.commonpath([posixpath.dirname(p) for p in paths])
    try:
        bpy.ops.sollumz.import_assets(
            directory=directory,
            files=[{"name": p[len(directory):].lstrip("/")} for p in paths],
            use_custom_settings=True,
            **import_kwargs,
        )
    except RuntimeError as e:
        # Errors reported by the operator are raised as exceptions
        return [str(e).strip()]

    return []


class GameDirectoryOperatorMixin:
    """Operators that read the game files, from the GTA V installation directory saved in the preferences or selected
    with the file browser."""

    # SKIP_SAVE so a directory remembered from a previous run doesn't take priority over the one in the preferences
    directory: StringProperty(
        name="Game Directory",
        description="GTA V installation directory",
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def invoke(self, context, event):
        return invoke_with_game_directory(self, context)

    def draw(self, context):
        self.layout.label(text="Select the GTA V installation directory")


class GameAssetItem(PropertyGroup):
    asset_name: StringProperty()
    ytyp_name: StringProperty()
    is_interior: BoolProperty()


class SOLLUMZ_OT_import_library_asset_from_game_installation(GameDirectoryOperatorMixin, Operator):
    bl_idname = "sollumz.import_library_asset_from_game_installation"
    bl_label = "Import from Game Installation"
    bl_description = (
        "Search the game installation directory for the files of the selected assets and import them with all their "
        "data (LODs, collisions, lights, skeleton, etc.), instead of the simplified models stored in the asset "
        "library"
    )
    bl_options = {"UNDO"}

    # Copied from the selected assets on invoke, the assets are no longer in the context after the file browser closes
    assets: CollectionProperty(
        type=GameAssetItem,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context):
        if not IS_SZIO_NATIVE_AVAILABLE:
            cls.poll_message_set(PYMATERIA_REQUIRED_MSG)
            return False

        any_game_asset = False
        for _, archetype_info in iter_selected_game_assets(context):
            if archetype_info.type != "MLO":
                return True
            any_game_asset = True

        if any_game_asset:
            cls.poll_message_set("Importing interiors from game installation is not supported")
        else:
            cls.poll_message_set("No game asset selected")
        return False

    @classmethod
    def label(cls, context) -> str:
        """Label for the operator buttons, includes the number of assets that will be imported when there are
        multiple."""
        num_assets = sum(1 for _, archetype_info in iter_selected_game_assets(context) if archetype_info.type != "MLO")
        if num_assets > 1:
            return f"Import {num_assets} Assets from Game Installation"
        return cls.bl_label

    def invoke(self, context, event):
        self.assets.clear()
        for asset, archetype_info in iter_selected_game_assets(context):
            item = self.assets.add()
            item.asset_name = asset.name
            item.ytyp_name = archetype_info.ytyp
            item.is_interior = archetype_info.type == "MLO"

        return invoke_with_game_directory(self, context)

    def execute(self, context):
        start_time = time.time()
        with logger.use_operator_logger(self):
            if (game_dir := _validated_game_directory(self, context)) is None:
                return {"CANCELLED"}

            if not self.assets:
                logger.error("No game asset selected.")
                return {"CANCELLED"}

            assets = []
            for item in self.assets:
                asset_name = remove_number_suffix(item.asset_name).lower()
                if item.is_interior:
                    logger.warning(
                        f"Importing interiors from game installation is not supported, skipping '{asset_name}'."
                    )
                    continue
                assets.append((asset_name, item.ytyp_name))

            found_files = [f for f in _find_game_asset_files_batch(context, game_dir, assets) if f is not None]
            if not found_files:
                return {"CANCELLED"}

            any_skipped = len(found_files) < len(self.assets)

        # Outside of the operator logger, the import operator reports its own messages
        errors = _import_game_asset_files(found_files)
        for error in errors:
            self.report({"ERROR"}, error)

        if len(found_files) == 1:
            imported = f"'{found_files[0].asset}'"
        else:
            imported = f"{len(found_files)} assets"
        self.report(
            {"WARNING"} if errors or any_skipped else {"INFO"},
            f"Imported {imported} in {time.time() - start_time:.2f} seconds",
        )
        return {"FINISHED"}
