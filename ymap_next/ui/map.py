import bpy
from bpy.props import (
    CollectionProperty,
    IntProperty,
)
from bpy.types import (
    ID,
    Menu,
    Panel,
    UIList,
    WindowManager,
)

from ...icons import icon
from ...shared.multiselection import (
    MultiSelectUIListMixin,
    multiselect_ui_draw_list,
)
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ..gta5.presets.timecycle_modifier import SOLLUMZ_PT_timecycle_modifier_presets
from ..operators import (
    import_export as map_ie_ops,
)
from ..operators import (
    lod_lights as map_lod_lights_ops,
)
from ..operators import (
    map as map_ops,
)
from ..operators import (
    selection as map_select_ops,
)
from ..properties.map import (
    MapGroup,
    MapPartitionMode,
    get_maps,
)


class SOLLUMZ_PT_maps_tool_panel(TabbedPanelHelper, Panel):
    bl_label = "Maps"
    bl_idname = "SOLLUMZ_PT_maps_tool_panel"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_category = "Sollumz Tools"
    bl_order = 7

    default_tab = "SOLLUMZ_PT_map_entities"

    def draw_header(self, context):
        self.layout.label(text="", icon="OBJECT_ORIGIN")

    def draw_before(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        maps = get_maps(context)
        if not maps:
            wm = context.window_manager
            from ...sollumz_ui import draw_list_with_add_remove

            # fake list just so the UI stays consistent with no maps
            list_col, _ = draw_list_with_add_remove(
                layout,
                map_ops.SOLLUMZ_OT_maps_new_group.bl_idname,
                map_ops.SOLLUMZ_OT_maps_delete_group.bl_idname,
                SOLLUMZ_UL_maps_group_list.bl_idname,
                "",
                wm,
                "sz_ui_map_groups_fake_list",
                wm,
                "sz_ui_map_groups_fake_list_index",
                rows=3,
            )
        else:
            groups = maps.groups

            list_col, _ = multiselect_ui_draw_list(
                layout,
                groups,
                map_ops.SOLLUMZ_OT_maps_new_group.bl_idname,
                map_ops.SOLLUMZ_OT_maps_delete_group.bl_idname,
                SOLLUMZ_UL_maps_group_list,
                SOLLUMZ_MT_maps_group_list_context_menu,
                "tool_panel",
            )

        row = list_col.row()
        col = row.column(align=True)
        col.operator(map_ie_ops.SOLLUMZ_OT_import_ymap.bl_idname, icon="IMPORT")
        col.operator(map_ie_ops.SOLLUMZ_OT_import_ymap_from_directory.bl_idname, icon="IMPORT")
        row.operator(map_ie_ops.SOLLUMZ_OT_export_ymap.bl_idname, icon="EXPORT")

        if not maps:
            return

        if groups and (active_group := groups.active_item):
            if active_group.has_incomplete_lod_hierarchy:
                box = layout.box()
                box.alert = True
                col = box.column(align=True)
                col.label(text="Incomplete LOD hierarchy", icon="ERROR")
                col.label(text="Some containers were imported without related YMAP")
                col.label(text="files. Their hierarchy values are kept as-is on export")
                col.label(text="and editing them is limited.")

            layout.prop(active_group, "scripted")

            if bpy.app.version >= (4, 1, 0):
                header, body = layout.panel("map_group_containers", default_closed=True)
            else:
                # Good enough to always display the panel contents when UILayout.panel is not available
                header, body = layout, layout
            header.label(text="Containers", icon_value=icon("map_container"))
            if body:
                maps = active_group.maps
                multiselect_ui_draw_list(
                    body,
                    maps,
                    map_ops.SOLLUMZ_OT_map_group_new_map_data.bl_idname,
                    map_ops.SOLLUMZ_OT_map_group_delete_map_data.bl_idname,
                    SOLLUMZ_UL_map_group_map_data_list,
                    SOLLUMZ_MT_map_group_map_data_list_context_menu,
                    "tool_panel",
                )

                body.operator(map_ops.SOLLUMZ_OT_map_highlight_map_data_entities.bl_idname, icon="LIGHT_SUN")

                if not maps:
                    return

                has_multiple_selection = maps.has_multiple_selection
                selection = maps.selection
                active = maps.active_item

                active_locked = active.incomplete_lod_hierarchy_lock
                any_selected_locked = any(m.incomplete_lod_hierarchy_lock for m in maps.iter_selected_items())

                row = body.row()
                # A locked container cannot be re-linked: its entities' parent_index values are
                # relative to the original parent map's entity list (the setter is also guarded).
                row.enabled = not active_locked
                row.prop(selection.owner, selection.propnames.parent_name, icon_value=icon("map_container"))
                if active_locked:
                    col = body.column(align=True)
                    col.alert = True
                    col.label(text="Incomplete LOD hierarchy (locked)", icon="LOCKED")
                    body.operator(map_ops.SOLLUMZ_OT_map_data_unlock_lod_hierarchy.bl_idname, icon="UNLOCKED")
                elif active.is_auto_generated:
                    body.label(text="Auto-generated")
                elif not any_selected_locked:
                    # partition_mode propagates to the whole selection, which may include locked maps
                    row = body.row()
                    row.prop(selection.owner, selection.propnames.partition_mode, expand=True)

                # Partitioning mutates the LOD hierarchy, so it is disabled for incomplete (locked) maps.
                if not active_locked:
                    if active.partition_mode == MapPartitionMode.AUTO.name:
                        row = body.row(align=True)
                        row.operator(map_ops.SOLLUMZ_OT_map_generate_partitions.bl_idname, icon="FILE_REFRESH")
                        row.operator(map_ops.SOLLUMZ_OT_map_convert_to_manual.bl_idname, text="", icon="X")
                    elif not active.is_auto_generated:
                        row = body.row(align=True)
                        row.operator(map_ops.SOLLUMZ_OT_map_collapse_to_auto.bl_idname)
                        row.operator(
                            map_ops.SOLLUMZ_OT_map_auto_assign_unassigned.bl_idname, text="", icon="BRUSH_DATA"
                        )

                body.separator()

                if bpy.app.version >= (4, 1, 0):
                    ext_header, ext_body = body.panel("map_data_extents", default_closed=True)
                else:
                    ext_header, ext_body = body, body
                ext_header.label(text="Extents")
                if ext_body:
                    ext_body.prop(selection.owner, selection.propnames.extents_manual)
                    col = ext_body.column()
                    col.enabled = active.extents_manual
                    col.prop(selection.owner, selection.propnames.entities_extents_min)
                    col.prop(selection.owner, selection.propnames.entities_extents_max)
                    col.prop(selection.owner, selection.propnames.streaming_extents_min)
                    col.prop(selection.owner, selection.propnames.streaming_extents_max)
                    ext_body.operator(map_ops.SOLLUMZ_OT_map_calculate_extents.bl_idname, icon="SHADING_BBOX")

                if bpy.app.version >= (4, 1, 0):
                    desc_header, desc_body = body.panel("map_data_description", default_closed=True)
                else:
                    desc_header, desc_body = body, body
                desc_header_row = desc_header.row()
                desc_header_row.use_property_split = False
                desc_header_row.prop(selection.owner, selection.propnames.desc_enabled, text="Description")
                if desc_body:
                    desc_body.active = active.desc_enabled
                    desc_body.prop(selection.owner, selection.propnames.desc_name)
                    desc_body.prop(selection.owner, selection.propnames.desc_exported_by)
                    desc_body.prop(selection.owner, selection.propnames.desc_owner)
                    desc_body.prop(selection.owner, selection.propnames.desc_time)
                    desc_body.prop(selection.owner, selection.propnames.desc_version)
                    desc_body.prop(selection.owner, selection.propnames.desc_flags)


class MapChildTabPanel(TabPanel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_maps_tool_panel.bl_idname
    bl_category = SOLLUMZ_PT_maps_tool_panel.bl_category

    parent_tab_panel = SOLLUMZ_PT_maps_tool_panel

    @classmethod
    def poll_tab(cls, context):
        maps = get_maps(context)
        if not maps:
            return False
        groups = maps.groups
        return groups and groups.active_item


class SOLLUMZ_PT_map_tcms(MapChildTabPanel, Panel):
    bl_label = "Timecycle Modifiers"
    bl_idname = "SOLLUMZ_PT_map_tcms"
    bl_order = 2

    icon = "MOD_TIME"

    @classmethod
    def get_label(cls, context) -> str:
        maps = get_maps(context)
        if not maps:
            return cls.bl_label
        groups = maps.groups
        active_group = groups.active_item
        return cls.bl_label + f" ({len(active_group.timecycle_modifiers)})"

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
        timecycle_modifiers = active_group.timecycle_modifiers
        multiselect_ui_draw_list(
            self.layout,
            timecycle_modifiers,
            map_ops.SOLLUMZ_OT_map_group_new_tcm.bl_idname,
            map_ops.SOLLUMZ_OT_map_group_delete_tcm.bl_idname,
            SOLLUMZ_UL_map_group_tcm_list,
            SOLLUMZ_MT_map_group_tcm_list_context_menu,
            "tool_panel",
        )

        if not timecycle_modifiers:
            return

        has_multiple_selection = timecycle_modifiers.has_multiple_selection
        selection = timecycle_modifiers.selection
        active = timecycle_modifiers.active_item

        row = layout.row()
        row.alignment = "RIGHT"
        SOLLUMZ_PT_timecycle_modifier_presets.draw_panel_header(row)

        layout.prop(active, "uuid_str")
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "map_data_name", icon_value=icon("map_container"))

        layout.prop(selection.owner, selection.propnames.name)
        layout.prop(selection.owner, selection.propnames.location)
        layout.prop(selection.owner, selection.propnames.size)
        layout.prop(selection.owner, selection.propnames.percentage)
        layout.prop(selection.owner, selection.propnames.range)
        layout.prop(selection.owner, selection.propnames.start_hour)
        layout.prop(selection.owner, selection.propnames.end_hour)


class SOLLUMZ_PT_map_occluders(MapChildTabPanel, Panel):
    bl_label = "Occluders"
    bl_idname = "SOLLUMZ_PT_map_occluders"
    bl_order = 4

    @classmethod
    def get_tab_icon(cls) -> int:
        return icon("mesh_occlusion")

    @classmethod
    def get_label(cls, context) -> str:
        maps = get_maps(context)
        if not maps:
            return cls.bl_label
        groups = maps.groups
        active_group = groups.active_item
        return cls.bl_label + f" ({len(active_group.occluders)})"

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
        occluders = active_group.occluders
        multiselect_ui_draw_list(
            layout,
            occluders,
            map_ops.SOLLUMZ_OT_map_group_new_occluder.bl_idname,
            map_ops.SOLLUMZ_OT_map_group_delete_occluder.bl_idname,
            SOLLUMZ_UL_map_group_occluder_list,
            SOLLUMZ_MT_map_group_occluder_list_context_menu,
            "tool_panel",
        )

        if not occluders:
            return

        has_multiple_selection = occluders.has_multiple_selection
        selection = occluders.selection
        active = occluders.active_item

        layout.prop(active, "uuid_str")
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "map_data_name", icon_value=icon("map_container"))
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "linked_object")


class SOLLUMZ_PT_map_lod_lights(MapChildTabPanel, Panel):
    bl_label = "LOD Lights"
    bl_idname = "SOLLUMZ_PT_map_lod_lights"
    bl_order = 5

    @classmethod
    def get_tab_icon(cls) -> int:
        return icon("lod_lights")

    @classmethod
    def get_label(cls, context) -> str:
        maps = get_maps(context)
        if not maps:
            return cls.bl_label
        groups = maps.groups
        active_group = groups.active_item
        return cls.bl_label + f" ({len(active_group.lod_lights)})"

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

        box = layout.box()
        if bpy.app.version >= (4, 1, 0):
            header, body = box.panel("prefs_general_advanced", default_closed=True)
        else:
            # Good enough to always display the panel contents when UILayout.panel is not available
            header, body = box, box
        header.label(text="Bake", icon="LIGHT_DATA")
        if body:
            props = active_group.lod_lights_bake_props
            col = body.column()
            col.prop(props, "name_prefix")

            col.separator()

            col.row().prop(props, "lod_levels")
            col.row().prop(props, "priority_levels")

            col.separator()

            col.prop(props, "is_streetlight_pattern")
            col.prop(props, "skip_pattern")

            col.separator()

            split = col.split(factor=0.4)
            row = split.row()
            row.alignment = "RIGHT"
            row.label(text="Small Min Thresholds")
            row = split.row(align=True)
            row.use_property_split = False
            row.prop(props, "min_falloff_small", text="Falloff")
            row.prop(props, "min_intensity_small", text="Intensity")

            split = col.split(factor=0.4)
            row = split.row()
            row.alignment = "RIGHT"
            row.label(text="Medium Min Thresholds")
            row = split.row(align=True)
            row.use_property_split = False
            row.prop(props, "min_falloff_medium", text="Falloff")
            row.prop(props, "min_intensity_medium", text="Intensity")

            col.separator()

            col.prop(props, "partition")
            split = col.split(factor=0.4)
            split.active = props.partition
            row = split.row()
            row.alignment = "RIGHT"
            row.label(text="Max Lights in Partition")
            row = split.row(align=True)
            row.use_property_split = False
            row.prop(props, "partition_max_lights_small", text="Small")
            row.prop(props, "partition_max_lights_medium", text="Medium")
            row.prop(props, "partition_max_lights_large", text="Large")

            col.separator()

            split = col.split(factor=0.4)
            row = split.row()
            row.alignment = "RIGHT"
            row.label(text="Visibility Range")
            row = split.row(align=True)
            row.use_property_split = False
            row.prop(props, "visibility_range_small", text="Small")
            row.prop(props, "visibility_range_medium", text="Medium")
            row.prop(props, "visibility_range_large", text="Large")

            split = col.split(factor=0.4)
            row = split.row()
            row.alignment = "RIGHT"
            row.label(text="Distant Visibility Range")
            row = split.row(align=True)
            row.use_property_split = False
            row.prop(props, "distant_visibility_range_small", text="Small")
            row.prop(props, "distant_visibility_range_medium", text="Medium")
            row.prop(props, "distant_visibility_range_large", text="Large")

            col.separator()

            row = body.row(align=True)
            row.scale_y = 1.3
            op = row.operator(map_lod_lights_ops.SOLLUMZ_OT_map_bake_lod_lights.bl_idname)
            op.lod_levels = props.lod_levels
            op.priority_levels = props.priority_levels
            op.is_streetlight_pattern = props.is_streetlight_pattern
            op.skip_pattern = props.skip_pattern
            op.min_falloff_small = props.min_falloff_small
            op.min_intensity_small = props.min_intensity_small
            op.min_falloff_medium = props.min_falloff_medium
            op.min_intensity_medium = props.min_intensity_medium
            op.partition = props.partition
            op.partition_max_lights_small = props.partition_max_lights_small
            op.partition_max_lights_medium = props.partition_max_lights_medium
            op.partition_max_lights_large = props.partition_max_lights_large
            op.visibility_range_small = props.visibility_range_small
            op.visibility_range_medium = props.visibility_range_medium
            op.visibility_range_large = props.visibility_range_large
            op.distant_visibility_range_small = props.distant_visibility_range_small
            op.distant_visibility_range_medium = props.distant_visibility_range_medium
            op.distant_visibility_range_large = props.distant_visibility_range_large
            op.name_prefix = props.name_prefix

        lod_lights = active_group.lod_lights
        multiselect_ui_draw_list(
            layout,
            lod_lights,
            map_ops.SOLLUMZ_OT_map_group_new_lod_lights.bl_idname,
            map_ops.SOLLUMZ_OT_map_group_delete_lod_lights.bl_idname,
            SOLLUMZ_UL_map_group_lod_lights_list,
            SOLLUMZ_MT_map_group_lod_lights_list_context_menu,
            "tool_panel",
        )

        if not lod_lights:
            return

        has_multiple_selection = lod_lights.has_multiple_selection
        selection = lod_lights.selection
        active = lod_lights.active_item

        layout.prop(active, "uuid_str")
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "map_data_name", icon_value=icon("map_container"))
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "linked_object")

        layout.prop(selection.owner, selection.propnames.category, expand=True)


class SOLLUMZ_UL_maps_group_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_maps_group_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_maps_select_group.bl_idname

    def get_item_icon(self, item) -> str:
        return "HOME"


class SOLLUMZ_MT_maps_group_list_context_menu(Menu):
    bl_label = "Map Group Specials"
    bl_idname = "SOLLUMZ_MT_maps_group_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(map_select_ops.SOLLUMZ_OT_maps_select_all_groups.bl_idname, text="Select All")
        op1 = layout.operator(map_select_ops.SOLLUMZ_OT_maps_select_invert_groups.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_maps_group_list.last_filter_options.get("groups_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_UL_map_group_map_data_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_map_group_map_data_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_map_group_select_map.bl_idname
    name_prop = "ui_label"

    def get_item_icon(self, item) -> str | int:
        if item.incomplete_lod_hierarchy_lock:
            item_icon = "LOCKED"
        elif item.partition_mode == MapPartitionMode.AUTO.name:
            item_icon = icon("map_container_auto")
        elif item.is_auto_generated:
            item_icon = icon("map_container_auto_generated")
        else:
            item_icon = icon("map_container")
        return item_icon

    def filter_items(self, context, data, propname):
        multiselect_collection_name = propname[:-1]  # remove '_' suffix
        collection = getattr(data, multiselect_collection_name)
        # return entities_filter_items(collection, self.filter_name, self.use_filter_sort_reverse, self.use_filter_sort_alpha)

        return [], [m.ui_tree_sort_id for m in collection]


class SOLLUMZ_MT_map_group_map_data_list_context_menu(Menu):
    bl_label = "Map Containers Specials"
    bl_idname = "SOLLUMZ_MT_map_group_map_data_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_all_maps.bl_idname, text="Select All")
        op1 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_invert_maps.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_map_group_map_data_list.last_filter_options.get("maps_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_UL_map_group_tcm_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_map_group_tcm_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_map_group_select_tcm.bl_idname
    name_prop = "name"

    def get_item_icon(self, item) -> str:
        return "MOD_TIME"


class SOLLUMZ_MT_map_group_tcm_list_context_menu(Menu):
    bl_label = "Map Timecycle Modifiers Specials"
    bl_idname = "SOLLUMZ_MT_map_group_tcm_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_all_tcms.bl_idname, text="Select All")
        op1 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_invert_tcms.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_map_group_tcm_list.last_filter_options.get("timecycle_modifiers_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_UL_map_group_occluder_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_map_group_occluder_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_map_group_select_occluder.bl_idname
    name_prop = "name"

    def get_item_icon(self, item) -> int:
        return icon("mesh_occlusion")


class SOLLUMZ_MT_map_group_occluder_list_context_menu(Menu):
    bl_label = "Map Occluders Specials"
    bl_idname = "SOLLUMZ_MT_map_group_occluder_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_all_occluders.bl_idname, text="Select All")
        op1 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_invert_occluders.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_map_group_occluder_list.last_filter_options.get("occluder_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_UL_map_group_lod_lights_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_map_group_lod_lights_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_map_group_select_lod_lights.bl_idname
    name_prop = "name"

    def get_item_icon(self, item) -> int:
        return icon("lod_lights")


class SOLLUMZ_MT_map_group_lod_lights_list_context_menu(Menu):
    bl_label = "Map LOD Lights Specials"
    bl_idname = "SOLLUMZ_MT_map_group_lod_lights_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_all_lod_lights.bl_idname, text="Select All")
        op1 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_invert_lod_lights.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_map_group_lod_lights_list.last_filter_options.get("lod_lights_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


def register():
    WindowManager.sz_ui_map_groups_fake_list = CollectionProperty(type=MapGroup)
    WindowManager.sz_ui_map_groups_fake_list_index = IntProperty()


def unregister():
    del WindowManager.sz_ui_map_groups_fake_list
    del WindowManager.sz_ui_map_groups_fake_list_index
