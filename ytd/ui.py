from bpy.types import (
    Menu,
    Panel,
    UILayout,
    UIList,
)

from ..shared.multiselection import MultiSelectUIListMixin, multiselect_ui_draw_list
from .operators import (
    selection as txd_select_ops,
)
from .operators import (
    txd as txd_ops,
)
from .utils import (
    get_selected_txd,
    get_selected_txd_texture,
)


class SOLLUMZ_UL_txd_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_txd_list"
    multiselect_operator = txd_select_ops.SOLLUMZ_OT_txd_select_one.bl_idname
    default_item_icon = "TEXTURE"


class SOLLUMZ_UL_txd_texture_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_txd_texture_list"
    multiselect_operator = txd_select_ops.SOLLUMZ_OT_txd_texture_select_one.bl_idname
    default_item_icon = "IMAGE_DATA"
    name_prop = "name"
    name_editable = False

    def draw_item(self, context, layout: UILayout, data, item, icon, active_data, active_propname, index):
        from ..shared.multiselection import MultiSelectCollection, MultiSelectFilterOptions

        multiselect_collection_name = active_propname[:-21]  # remove '_active_index_for_ui_' suffix

        filter_opts = MultiSelectFilterOptions(
            self.filter_name,
            self.use_filter_sort_reverse,
            self.use_filter_sort_alpha,
            self.use_filter_invert,
        )
        self_cls = type(self)
        if f"{multiselect_collection_name}_{self.list_id}" not in self_cls.last_filter_options:
            self_cls.last_filter_options[f"{multiselect_collection_name}_{self.list_id}"] = filter_opts

        collection: MultiSelectCollection = getattr(data, multiselect_collection_name)
        icon = self.get_item_icon(item)
        match icon:
            case str():
                icon_str, icon_value = icon, 0
            case int():
                icon_str, icon_value = "NONE", icon
            case _:
                raise ValueError(f"Invalid item icon. Only str or int supported, got '{icon}'")

        selection_indices = collection.selection_indices
        is_selected = len(selection_indices) > 1 and any(i.index == index for i in selection_indices)
        is_active = index == collection.active_index
        layout.active = len(selection_indices) <= 1 or is_selected

        if is_active:
            layout.label(text="", icon=icon_str, icon_value=icon_value)
        else:
            row = layout.row(align=True)
            row.alignment = "LEFT"
            op = row.operator(
                self.multiselect_operator,
                text="",
                icon=icon_str,
                icon_value=icon_value,
                emboss=is_selected or is_active,
            )
            op.index = index
            filter_opts.apply_to_operator(op)

        self.draw_item_extra(context, layout, data, item, icon, active_data, active_propname, index)

    def draw_item_extra(self, context, layout: UILayout, data, item, icon, active_data, active_propname, index):
        layout.template_ID(item, "image", open="image.open")

    def get_item_icon(self, item) -> str | int:
        return UILayout.icon(item.image) if item.image is not None else "ERROR"
        # "IMAGE_DATA"


class SOLLUMZ_MT_txd_list_context_menu(Menu):
    bl_label = "Texture Dictionaries Specials"
    bl_idname = "SOLLUMZ_MT_txd_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(txd_select_ops.SOLLUMZ_OT_txd_select_all.bl_idname, text="Select All")
        op1 = layout.operator(txd_select_ops.SOLLUMZ_OT_txd_select_invert.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_txd_list.last_filter_options.get("texture_dictionaries_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_MT_txd_texture_list_context_menu(Menu):
    bl_label = "Textures Specials"
    bl_idname = "SOLLUMZ_MT_txd_texture_list_context_menu"

    def draw(self, _context):
        layout = self.layout

        layout.operator(txd_ops.SOLLUMZ_OT_txd_add_textures_from_dds.bl_idname)
        layout.separator()
        op0 = layout.operator(txd_select_ops.SOLLUMZ_OT_txd_texture_select_all.bl_idname, text="Select All")
        op1 = layout.operator(txd_select_ops.SOLLUMZ_OT_txd_texture_select_invert.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_txd_texture_list.last_filter_options.get("textures_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_PT_txd_tool_panel(Panel):
    bl_label = "Texture Dictionaries"
    bl_idname = "SOLLUMZ_PT_txd_tool_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"
    bl_order = 7

    def draw_header(self, context):
        self.layout.label(text="", icon="TEXTURE")

    def draw(self, context): ...


class TxdToolChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_txd_tool_panel.bl_idname
    bl_category = SOLLUMZ_PT_txd_tool_panel.bl_category


class SOLLUMZ_PT_txd_list_panel(TxdToolChildPanel, Panel):
    bl_label = "Texture Dictionaries"
    bl_idname = "SOLLUMZ_PT_txd_list_panel"
    bl_options = {"HIDE_HEADER"}
    bl_order = 0

    def draw(self, context):
        list_col, _ = multiselect_ui_draw_list(
            self.layout,
            context.scene.sz_txds.texture_dictionaries,
            txd_ops.SOLLUMZ_OT_txd_create.bl_idname,
            txd_ops.SOLLUMZ_OT_txd_delete.bl_idname,
            SOLLUMZ_UL_txd_list,
            SOLLUMZ_MT_txd_list_context_menu,
            "tool_panel",
        )

        row = list_col.row()
        row.operator(txd_ops.SOLLUMZ_OT_import_ytd.bl_idname, icon="IMPORT")
        row.operator(txd_ops.SOLLUMZ_OT_export_ytd.bl_idname, icon="EXPORT")


class SOLLUMZ_PT_txd_textures_panel(TxdToolChildPanel, Panel):
    bl_label = "Textures"
    bl_idname = "SOLLUMZ_PT_txd_textures_panel"
    bl_order = 1

    @classmethod
    def poll(cls, context):
        return get_selected_txd(context) is not None

    def draw(self, context):
        layout = self.layout
        txd = get_selected_txd(context)

        multiselect_ui_draw_list(
            layout,
            txd.textures,
            txd_ops.SOLLUMZ_OT_txd_create_texture.bl_idname,
            txd_ops.SOLLUMZ_OT_txd_delete_texture.bl_idname,
            SOLLUMZ_UL_txd_texture_list,
            SOLLUMZ_MT_txd_texture_list_context_menu,
            "tool_panel",
        )

        tex = get_selected_txd_texture(context)
        if tex is None:
            return

        box = layout.box()
        if tex.image is not None:
            tex_icon = UILayout.icon(tex.image)
            box.template_icon(tex_icon, scale=10.0)
        box.template_ID(tex, "image", open="image.open")

        img = tex.image
        if img is None:
            return

        col = box.column(align=True)

        is_packed = bool(img.packed_files)
        row = col.row(align=True)
        row.context_pointer_set("edit_image", img)
        if is_packed:
            row.operator("image.unpack", text="", icon="PACKAGE")
        else:
            row.operator("image.pack", text="", icon="UGLYPACKAGE")

        subrow = row.row(align=True)
        subrow.enabled = not is_packed
        subrow.prop(img, "filepath", text="")
        subrow.operator("image.reload", text="", icon="FILE_REFRESH")

        w, h = img.size
        row = col.row(align=True)
        row.alignment = "RIGHT"
        row.label(text=f"{w} \u00d7 {h}")
