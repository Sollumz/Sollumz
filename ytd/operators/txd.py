from pathlib import Path

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    StringProperty,
)
from bpy.types import Operator, OperatorFileListElement
from bpy_extras.io_utils import ImportHelper

from ... import logger
from ...sollumz_operators import ExportAssetsOperatorImpl, ImportAssetsOperatorImpl
from ..utils import (
    get_selected_txd,
    get_selected_txd_source,
)


class SOLLUMZ_OT_txd_create(Operator):
    """Add a texture dictionary to the project"""

    bl_idname = "sollumz.txd_create"
    bl_label = "Create Texture Dictionary"

    def execute(self, context):
        txds = context.scene.sz_txds

        existing_names = {t.name for t in txds.texture_dictionaries}
        name = "txd"
        if name in existing_names:
            n = 1
            while (name := f"txd_{n:02d}") in existing_names:
                n += 1

        txd = txds.new_texture_dictionary()
        txd.name = name
        return {"FINISHED"}


class SOLLUMZ_OT_txd_delete(Operator):
    """Delete the selected texture dictionary from the project"""

    bl_idname = "sollumz.txd_delete"
    bl_label = "Delete Texture Dictionary"

    @classmethod
    def poll(cls, context):
        return len(context.scene.sz_txds.texture_dictionaries) > 0

    def execute(self, context):
        coll = context.scene.sz_txds.texture_dictionaries

        indices_to_remove = sorted(coll.selected_items_indices, reverse=True)
        if not indices_to_remove:
            indices_to_remove = [coll.active_index]

        new_active_index = max(indices_to_remove[-1] - 1, 0)
        for idx in indices_to_remove:
            coll.remove(idx)

        if len(coll) > 0:
            coll.select(min(new_active_index, len(coll) - 1))

        return {"FINISHED"}


class SOLLUMZ_OT_txd_create_texture(Operator):
    """Add a texture slot to the texture dictionary"""

    bl_idname = "sollumz.txd_create_texture"
    bl_label = "Create Texture"

    @classmethod
    def poll(cls, context):
        return get_selected_txd(context) is not None

    def execute(self, context):
        txd = get_selected_txd(context)
        if txd is None:
            return {"CANCELLED"}

        txd.new_texture()
        return {"FINISHED"}


class SOLLUMZ_OT_txd_add_textures_from_dds(Operator, ImportHelper):
    """Add one or more DDS files as textures to the selected texture dictionary"""

    bl_idname = "sollumz.txd_add_textures_from_dds"
    bl_label = "Add Textures from DDS"

    filter_glob: StringProperty(default="*.dds", options={"HIDDEN"}, maxlen=255)

    files: CollectionProperty(type=OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"})
    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})

    @classmethod
    def poll(cls, context):
        return get_selected_txd(context) is not None

    def execute(self, context):
        txd = get_selected_txd(context)

        if not self.directory or len(self.files) == 0 or self.files[0].name == "":
            self.report({"ERROR"}, "No DDS file selected.")
            return {"CANCELLED"}

        directory = Path(bpy.path.abspath(self.directory))
        added = 0
        for f in sorted(self.files, key=lambda f: f.name):
            filepath = directory / f.name
            if not filepath.is_file():
                logger.warning(f"DDS file does not exist: {filepath}")
                continue

            img = bpy.data.images.load(str(filepath), check_existing=True)
            if not img.packed_file:
                img.pack()
            txd.new_texture(img)
            added += 1

        self.report({"INFO"}, f"Added {added} texture(s) to '{txd.name}'.")
        return {"FINISHED"}


class SOLLUMZ_OT_txd_delete_texture(Operator):
    """Delete the selected texture(s) from the texture dictionary"""

    bl_idname = "sollumz.txd_delete_texture"
    bl_label = "Delete Texture"

    @classmethod
    def poll(cls, context):
        txd = get_selected_txd(context)
        return txd is not None and len(txd.textures) > 0

    def execute(self, context):
        txd = get_selected_txd(context)

        indices_to_remove = sorted(txd.textures.selected_items_indices, reverse=True)
        if not indices_to_remove:
            indices_to_remove = [txd.textures.active_index]

        new_active_index = max(indices_to_remove[-1] - 1, 0)
        for idx in indices_to_remove:
            txd.textures.remove(idx)

        if len(txd.textures) > 0:
            txd.textures.select(min(new_active_index, len(txd.textures) - 1))

        return {"FINISHED"}


class SOLLUMZ_OT_txd_create_source(Operator):
    """Add a textures source to the texture dictionary"""

    bl_idname = "sollumz.txd_create_source"
    bl_label = "Create Source"

    @classmethod
    def poll(cls, context):
        return get_selected_txd(context) is not None

    def execute(self, context):
        txd = get_selected_txd(context)
        txd.new_source()
        return {"FINISHED"}


class SOLLUMZ_OT_txd_delete_source(Operator):
    """Delete the selected source(s) from the texture dictionary"""

    bl_idname = "sollumz.txd_delete_source"
    bl_label = "Delete Source"

    @classmethod
    def poll(cls, context):
        txd = get_selected_txd(context)
        return txd is not None and len(txd.sources) > 0

    def execute(self, context):
        txd = get_selected_txd(context)

        indices_to_remove = sorted(txd.sources.selected_items_indices, reverse=True)
        if not indices_to_remove:
            indices_to_remove = [txd.sources.active_index]

        new_active_index = max(indices_to_remove[-1] - 1, 0)
        for idx in indices_to_remove:
            txd.sources.remove(idx)

        if len(txd.sources) > 0:
            txd.sources.select(min(new_active_index, len(txd.sources) - 1))

        return {"FINISHED"}


class SOLLUMZ_OT_txd_source_use_all_images(Operator):
    """Delete the selected source(s) from the texture dictionary"""

    bl_idname = "sollumz.txd_source_use_all_images"
    bl_label = "Use All Images"

    use: BoolProperty(name="Use", default=True)

    @classmethod
    def poll(cls, context):
        src = get_selected_txd_source(context)
        return src is not None and len(src.images) > 0

    def execute(self, context):
        src = get_selected_txd_source(context)
        use = self.use
        for img in src.images:
            img.use = use
        return {"FINISHED"}


class SOLLUMZ_OT_txd_refresh_sources(Operator):
    """Refresh all sources in the texture dictionary"""

    bl_idname = "sollumz.txd_refresh_sources"
    bl_label = "Refresh Sources"

    @classmethod
    def poll(cls, context):
        return get_selected_txd(context) is not None

    def execute(self, context):
        txd = get_selected_txd(context)
        for src in txd.sources:
            src.refresh(context)
        txd.refresh_from_sources()
        return {"FINISHED"}


class SOLLUMZ_OT_import_ytd(ImportAssetsOperatorImpl, Operator):
    """Import texture dictionaries (.ytd)"""

    bl_idname = "sollumz.import_ytd"
    bl_label = "Import YTD"
    bl_options = {"UNDO"}

    filter_glob: StringProperty(
        default="*.ytd;*.ytd.xml",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )


class SOLLUMZ_OT_export_ytd(ExportAssetsOperatorImpl, Operator):
    """Export the selected texture dictionaries"""

    bl_idname = "sollumz.export_ytd"
    bl_label = "Export YTD"
    sz_export_types = {"YTD"}

    @classmethod
    def poll(cls, context):
        return context.scene.sz_txds.texture_dictionaries
