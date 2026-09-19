import os
from time import perf_counter
from typing import ClassVar

import bpy
from bpy.props import StringProperty
from bpy.types import Operator


class SOLLUMZ_OT_find_missing_textures(Operator):
    """Search a folder and its subfolders once to relink missing textures by filename"""

    bl_idname = "sollumz.find_missing_textures"
    bl_label = "Find Missing Textures"
    bl_options: ClassVar[set[str]] = {"REGISTER", "UNDO"}

    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})
    filter_folder: bpy.props.BoolProperty(default=True, options={"HIDDEN"})

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        start = perf_counter()
        directory = bpy.path.abspath(self.directory)
        if not self.directory or not os.path.isdir(directory):
            self.report({"ERROR"}, "Select an existing texture folder.")
            return {"CANCELLED"}

        missing = {}
        exists = {}
        for image in bpy.data.images:
            if image.source != "FILE" or image.packed_files or not image.is_editable:
                continue
            path = bpy.path.abspath(image.filepath, library=image.library)
            if path not in exists:
                exists[path] = os.path.isfile(path)
            if exists[path]:
                continue
            name = os.path.basename(path.replace("\\", "/")).casefold()
            if name:
                missing.setdefault(name, []).append(image)

        matches = {}
        errors = []
        if missing:
            for root, _, files in os.walk(directory, onerror=errors.append):
                for filename in files:
                    name = filename.casefold()
                    if name in missing:
                        matches[name] = None if name in matches else os.path.join(root, filename)

        found = 0
        failed = 0
        for name, images in missing.items():
            path = matches.get(name)
            if path is None:
                continue
            for image in images:
                previous_path = image.filepath_raw
                try:
                    image.filepath_raw = path
                    image.reload()
                except RuntimeError:
                    image.filepath_raw = previous_path
                    failed += 1
                    continue
                found += 1

        ambiguous = sum(len(missing[name]) for name, path in matches.items() if path is None)
        remaining = sum(map(len, missing.values())) - found
        self.report(
            {"WARNING"} if remaining or errors else {"INFO"},
            f"Relinked {found} texture(s) in {perf_counter() - start:.2f}s; "
            f"{remaining} unresolved ({ambiguous} ambiguous, {failed} failed); "
            f"{len(errors)} folder error(s).",
        )
        return {"FINISHED"}
