from bpy.types import Operator

from ...shared.multiselection import (
    MultiSelectAllOperator,
    MultiSelectInvertOperator,
    MultiSelectOneOperator,
)
from ..utils import (
    get_selected_txd,
    get_selected_txd_source,
)


class TxdsSelectMixin:
    def get_collection(self, context):
        return context.scene.sz_txds.texture_dictionaries


class SOLLUMZ_OT_txd_select_one(TxdsSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.txd_select_one"
    bl_label = "Select Texture Dictionary"


class SOLLUMZ_OT_txd_select_all(TxdsSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.txd_select_all"
    bl_label = "Select All Texture Dictionaries"


class SOLLUMZ_OT_txd_select_invert(TxdsSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.txd_select_invert"
    bl_label = "Invert Selected Texture Dictionaries"


class TxdTexturesSelectMixin:
    def get_collection(self, context):
        txd = get_selected_txd(context)
        return txd.textures if txd is not None else None


class SOLLUMZ_OT_txd_texture_select_one(TxdTexturesSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.txd_texture_select_one"
    bl_label = "Select Texture"


class SOLLUMZ_OT_txd_texture_select_all(TxdTexturesSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.txd_texture_select_all"
    bl_label = "Select All Textures"


class SOLLUMZ_OT_txd_texture_select_invert(TxdTexturesSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.txd_texture_select_invert"
    bl_label = "Invert Selected Textures"


class TxdSourcesSelectMixin:
    def get_collection(self, context):
        txd = get_selected_txd(context)
        return txd.sources if txd is not None else None


class SOLLUMZ_OT_txd_source_select_one(TxdSourcesSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.txd_source_select_one"
    bl_label = "Select Source"


class SOLLUMZ_OT_txd_source_select_all(TxdSourcesSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.txd_source_select_all"
    bl_label = "Select All Sources"


class SOLLUMZ_OT_txd_source_select_invert(TxdSourcesSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.txd_source_select_invert"
    bl_label = "Invert Selected Sources"


class TxdSourceImagesSelectMixin:
    def get_collection(self, context):
        src = get_selected_txd_source(context)
        return src.images if src is not None else None


class SOLLUMZ_OT_txd_source_image_select_one(TxdSourceImagesSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.txd_source_image_select_one"
    bl_label = "Select Image"


class SOLLUMZ_OT_txd_source_image_select_all(TxdSourceImagesSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.txd_source_image_select_all"
    bl_label = "Select All Images"


class SOLLUMZ_OT_txd_source_image_select_invert(TxdSourceImagesSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.txd_source_image_select_invert"
    bl_label = "Invert Selected Images"
