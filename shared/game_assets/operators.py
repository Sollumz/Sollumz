import functools
from pathlib import Path

import bpy
from bpy.props import (
    EnumProperty,
    StringProperty,
)
from bpy.types import (
    Operator,
)

from ...sollumz_preferences import get_addon_preferences
from .library import (
    asset_cache_path,
    build_library,
    build_library_cache,
)


def _output_directory_choice_items(self, context):
    prefs = get_addon_preferences(context)
    items = []
    for d in prefs.shared_assets_directories:
        if not d.path:
            continue
        items.append((d.path, f"{d.name} | {d.path}", ""))
    return items or [("", "", "")]


_build_library_progress = None

# TODO(ymap): remove 'Import To Asset Library' from regular import settings and make a special operator here
#             Should help with people accidentally toggling it on


def temporary_ui(layout):
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
        description="Which configured Shared Assets directory to write the .blend libraries into",
        items=_output_directory_choice_items,
        options={"SKIP_SAVE"},
    )

    pattern: StringProperty(name="Pattern")

    @classmethod
    def poll(cls, context):
        if bpy.app.version < (4, 2, 0):
            # Currently, we use Blender CLI commands to spawn the subprocess workers which were added in 4.2.
            cls.poll_message_set("Cannot build library on this Blender version. Update to Blender 4.2 or newer.")
            return False

        prefs = get_addon_preferences(context)
        if len(prefs.shared_assets_directories) == 0:
            cls.poll_message_set("No Game Asset Library directory set in preferences.")
            return False

        return True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        prefs = get_addon_preferences(context)
        if len(prefs.shared_assets_directories) > 1:
            layout.prop(self, "output_directory_choice")

        layout.prop(self, "pattern")

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if not prefs.shared_assets_directories:
            self.report({"ERROR"}, "No Shared Assets directory configured. Add one in Preferences > Sollumz.")
            return {"CANCELLED"}

        if not self.output_directory:
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
            source_directory, output_directory, game_catalog="GTA5", typ_pattern=self.pattern, report_progress_cb=_report_build_library_progress
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
