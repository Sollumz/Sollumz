from bpy.types import (
    Menu,
    Panel,
    UIList,
)

from ...shared.multiselection import (
    MultiSelectUIListMixin,
    multiselect_ui_draw_list,
)
from ..operators import (
    grass as map_grass_ops,
)
from ..operators import (
    map as map_ops,
)
from ..operators import (
    selection as map_select_ops,
)
from ..properties.map import (
    get_maps,
)
from .map import MapChildTabPanel
from ...icons import icon


class SOLLUMZ_PT_map_grass_batches(MapChildTabPanel, Panel):
    bl_label = "Grass Batches"
    bl_idname = "SOLLUMZ_PT_map_grass_batches"
    bl_order = 3

    @classmethod
    def get_tab_icon(cls) -> int:
        return icon("grass_batch")

    @classmethod
    def get_label(cls, context) -> str:
        maps = get_maps(context)
        if not maps:
            return cls.bl_label
        groups = maps.groups
        active_group = groups.active_item
        return cls.bl_label + f" ({len(active_group.grass_batches)})"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        maps = get_maps(context)
        if not maps:
            return
        groups = maps.groups
        layout.enabled = not groups.has_multiple_selection

        active_group = groups.active_item
        grass_batches = active_group.grass_batches
        multiselect_ui_draw_list(
            layout,
            grass_batches,
            map_ops.SOLLUMZ_OT_map_group_new_grass_batch.bl_idname,
            map_ops.SOLLUMZ_OT_map_group_delete_grass_batch.bl_idname,
            SOLLUMZ_UL_map_group_grass_batch_list,
            SOLLUMZ_MT_map_group_grass_batch_list_context_menu,
            "tool_panel",
        )

        if not grass_batches:
            return

        has_multiple_selection = grass_batches.has_multiple_selection
        selection = grass_batches.selection
        active = grass_batches.active_item

        layout.operator(map_grass_ops.SOLLUMZ_OT_map_grass_add_modifier.bl_idname)
        layout.operator(map_grass_ops.SOLLUMZ_OT_map_grass_bake_color.bl_idname)
        layout.separator()

        row = layout.row()
        split = row.split(factor=0.4)
        subrow = split.row()
        subrow.alignment = "RIGHT"
        subrow.label(text="Modifier Nodes")
        subrow = split.row(align=True)
        if active.modifier_ng is None:
            subrow.operator(
                map_grass_ops.SOLLUMZ_OT_map_grass_create_geonodes.bl_idname, icon="NODETREE", text="Create"
            )
        else:
            subrow.prop(active, "modifier_ng", text="")
            subrow.operator(map_grass_ops.SOLLUMZ_OT_map_grass_create_geonodes.bl_idname, icon="FILE_REFRESH", text="")

        layout.prop(active, "uuid_str")
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "map_data_name", icon_value=icon("map_container"))
        row = layout.row()
        row.enabled = not has_multiple_selection
        split = row.split(factor=0.4)
        subrow = split.row()
        subrow.alignment = "RIGHT"
        subrow.label(text="Linked Object")
        subrow = split.row(align=True)
        if active.linked_object is None:
            subrow.operator(
                map_grass_ops.SOLLUMZ_OT_map_grass_create_instances_mesh.bl_idname, icon="OBJECT_DATA", text="Create"
            )
        else:
            subrow.prop(active, "linked_object", text="")

        layout.separator()

        split = layout.split(factor=0.2)
        row = split.row()
        row.alignment = "RIGHT"
        row.label(text="Templates")
        row = split.row()
        templates = active.templates
        multiselect_ui_draw_list(
            row,
            templates,
            map_ops.SOLLUMZ_OT_map_group_new_grass_template.bl_idname,
            map_ops.SOLLUMZ_OT_map_group_delete_grass_template.bl_idname,
            SOLLUMZ_UL_map_group_grass_batch_template_list,
            SOLLUMZ_MT_map_group_grass_batch_template_list_context_menu,
            "tool_panel",
            rows=5,
        )

        if not templates:
            return

        has_multiple_selection = templates.has_multiple_selection
        selection = templates.selection
        active = templates.active_item

        # Preset popover for grass template properties.
        row = layout.row()
        row.alignment = "RIGHT"
        from ..gta5.presets.grass_template import SOLLUMZ_PT_grass_template_presets

        SOLLUMZ_PT_grass_template_presets.draw_panel_header(row)

        layout.prop(selection.owner, selection.propnames.archetype_name)
        col = layout.column(align=True)
        col.prop(selection.owner, selection.propnames.scale_range, index=0, text="Scale Range Min")
        col.prop(selection.owner, selection.propnames.scale_range, index=1, text="Max")
        layout.prop(selection.owner, selection.propnames.scale_randomness)
        layout.prop(selection.owner, selection.propnames.lod_dist)
        layout.prop(selection.owner, selection.propnames.lod_fade_start_dist)
        layout.prop(selection.owner, selection.propnames.lod_inst_fade_range)
        layout.prop(selection.owner, selection.propnames.orient_to_terrain)

        layout.separator()
        layout.prop(selection.owner, selection.propnames.spawn_weight)


class SOLLUMZ_UL_map_group_grass_batch_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_map_group_grass_batch_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_map_group_select_grass_batch.bl_idname
    name_prop = "name"

    def get_item_icon(self, item) -> str:
        return icon("grass_batch")


class SOLLUMZ_MT_map_group_grass_batch_list_context_menu(Menu):
    bl_label = "Map Grass Batches Specials"
    bl_idname = "SOLLUMZ_MT_map_group_grass_batch_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_all_grass_batches.bl_idname, text="Select All")
        op1 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_invert_grass_batches.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_map_group_grass_batch_list.last_filter_options.get(
            "grass_batches_tool_panel", None
        ):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_UL_map_group_grass_batch_template_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_map_group_grass_batch_template_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_map_group_select_grass_template.bl_idname
    name_prop = "archetype_name"

    def get_item_icon(self, item) -> str:
        return icon("grass_batch_template")


class SOLLUMZ_MT_map_group_grass_batch_template_list_context_menu(Menu):
    bl_label = "Map Grass Templates Specials"
    bl_idname = "SOLLUMZ_MT_map_group_grass_batch_template_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(
            map_select_ops.SOLLUMZ_OT_map_group_select_all_grass_templates.bl_idname, text="Select All"
        )
        op1 = layout.operator(
            map_select_ops.SOLLUMZ_OT_map_group_select_invert_grass_templates.bl_idname, text="Invert"
        )
        if filter_opts := SOLLUMZ_UL_map_group_grass_batch_template_list.last_filter_options.get(
            "templates_tool_panel", None
        ):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)
