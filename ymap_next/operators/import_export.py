from pathlib import Path

import bpy
from bpy.props import (
    BoolProperty,
    StringProperty,
)
from bpy.types import (
    Operator,
)

from ... import logger
from ...sollumz_operators import ExportAssetsOperatorImpl, ImportAssetsOperatorImpl
from ...sollumz_preferences import ImportSettingsBase
from ..properties.map import get_maps


class SOLLUMZ_OT_import_ymap(ImportAssetsOperatorImpl, Operator):
    """Import YMAPs"""

    bl_idname = "sollumz.import_ymap"
    bl_label = "Import YMAP"
    bl_options = {"UNDO"}

    filter_glob: StringProperty(
        default="*.ymap;*.ymap.xml",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )


class SOLLUMZ_OT_import_ymap_from_directory(ImportSettingsBase, Operator):
    """Import all YMAPs found in a directory"""

    bl_idname = "sollumz.import_ymap_from_directory"
    bl_label = "Import YMAP from Directory"
    bl_options = {"UNDO"}

    directory: StringProperty(
        name="Input directory",
        description="Select directory to search for .ymap in",
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    filter_glob: StringProperty(
        default="*.ymap;*.ymap.xml",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    # These are for scripts that use these operators to override the settings and avoid messing with the user preferences.
    use_custom_settings: BoolProperty(
        name="Use Custom Settings",
        description="Use the settings defined in this operator instead of user preferences",
        default=False,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def draw(self, context):
        pass

    def execute(self, context):
        with logger.use_operator_logger(self):
            directory = Path(bpy.path.abspath(self.directory))
            if not directory.is_dir():
                return {"CANCELLED"}

            ext_ymap = [".ymap"]
            ext_ymap_xml = [".ymap", ".xml"]
            files = []
            for map_file_path in directory.glob("**/*.ymap*"):
                ext = map_file_path.suffixes
                if ext != ext_ymap and ext != ext_ymap_xml:
                    continue

                files.append({"name": str(map_file_path.relative_to(directory))})

            if not files:
                logger.warning(f"No .ymap files found in '{directory}'")
                return {"CANCELLED"}

        logger.info(f"Found {len(files)} YMAP(s), importing...")
        return bpy.ops.sollumz.import_assets(
            directory=str(directory),
            files=files,
            use_custom_settings=self.use_custom_settings,
            ymap_instance_entities=self.ymap_instance_entities,
        )

    def invoke(self, context, event):
        if self.directory:
            # Already have a directory, don't open the import window and do the import directly.
            return self.execute(context)

        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}


class SOLLUMZ_OT_export_ymap(ExportAssetsOperatorImpl, Operator):
    """Export the selected map groups as YMAPs"""

    bl_idname = "sollumz.export_ymap"
    bl_label = "Export YMAP"
    sz_export_types = {"YMAP"}

    @classmethod
    def poll(cls, context):
        return (maps := get_maps(context)) and maps.groups
