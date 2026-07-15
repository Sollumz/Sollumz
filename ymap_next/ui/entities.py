from bpy.types import (
    Menu,
    Panel,
    UIList,
)

from ...icons import icon
from ...shared.multiselection import (
    MultiSelectUIFlagsPanel,
    MultiSelectUIListMixin,
    multiselect_ui_draw_list,
)
from ...sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ...tabbed_panels import TabbedPanelHelper, TabPanel
from ...ytyp.gta5.presets.extension import HOST_MAP_ENTITY
from ...ytyp.ui.extensions import ExtensionsListHelper, ExtensionsPanelHelper
from ..context import active_entity_from_active_object
from ..gta5.presets.entity import SOLLUMZ_PT_entity_presets
from ..map_index import (
    CACHE_NOT_READY,
    MAP_INDEX,
    find_entity_by_object,
)
from ..operators import (
    instancing as instancing_ops,
)
from ..operators import (
    map as map_ops,
)
from ..operators import (
    selection as map_select_ops,
)
from ..properties.filters import (
    get_map_entity_filter,
)
from ..properties.map import (
    get_maps,
)
from .common import draw_cache_result
from .map import MapChildTabPanel


class SOLLUMZ_PT_map_entities(MapChildTabPanel, Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_map_entities"
    bl_order = 0

    icon = "CUBE"

    @classmethod
    def get_label(cls, context) -> str:
        maps = get_maps(context)
        if not maps:
            return cls.bl_label
        groups = maps.groups
        active_group = groups.active_item
        return cls.bl_label + f" ({len(active_group.entities)})"

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        maps = get_maps(context)
        if not maps:
            return

        groups = maps.groups
        active_group = groups.active_item
        layout.enabled = not groups.has_multiple_selection

        entities = active_group.entities
        list_col, side_col = multiselect_ui_draw_list(
            layout,
            entities,
            map_ops.SOLLUMZ_OT_map_group_new_entity.bl_idname,
            map_ops.SOLLUMZ_OT_map_group_delete_entity.bl_idname,
            SOLLUMZ_UL_map_group_entity_list,
            SOLLUMZ_MT_map_group_entity_list_context_menu,
            "tool_panel",
        )

        flt = get_map_entity_filter(context)
        row = list_col.row()
        col = row.column()
        col_row = col.row()
        col_row.label(text="Filter By", icon="FILTER")
        col_row.prop(flt, "filter_type", text="")
        if flt.filter_type == "lod_level":
            row.prop(flt, "lod_level", text="")
        elif flt.filter_type == "kind":
            row.prop(flt, "kind", text="")
        elif flt.filter_type == "container":
            row.prop(flt, "container_name", text="", icon_value=icon("map_container"))

        list_col.separator(factor=2)

        row = layout.row()
        row.operator(map_ops.SOLLUMZ_OT_map_add_obj_as_entity.bl_idname, icon="OUTLINER_OB_MESH")
        row = layout.row()
        row.operator(map_ops.SOLLUMZ_OT_map_go_to_entity.bl_idname)

        row = layout.row(align=True)
        row.operator(instancing_ops.SOLLUMZ_OT_map_instance_entities.bl_idname, icon="LINKED")
        row.operator(instancing_ops.SOLLUMZ_OT_map_remove_entity_instances.bl_idname, icon="UNLINKED")


class SOLLUMZ_PT_map_entity_tabs(TabbedPanelHelper, Panel):
    bl_label = "Entities"
    bl_idname = "SOLLUMZ_PT_map_entity_tabs"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_map_entities.bl_idname
    bl_category = SOLLUMZ_PT_map_entities.bl_category

    default_tab = "SOLLUMZ_PT_map_entity_properties"

    bl_order = 3

    @classmethod
    def poll(cls, context):
        maps = get_maps(context)
        return maps.groups and maps.groups.active_item.entities

    def draw(self, context):
        maps = get_maps(context)
        self.layout.enabled = not maps.groups.has_multiple_selection
        super().draw(context)


class MapEntityChildTabPanel(TabPanel):
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_map_entity_tabs.bl_idname
    bl_category = SOLLUMZ_PT_map_entity_tabs.bl_category

    parent_tab_panel = SOLLUMZ_PT_map_entity_tabs


class SOLLUMZ_PT_map_entity_properties(MapEntityChildTabPanel, Panel):
    bl_label = "Entity"
    bl_idname = "SOLLUMZ_PT_map_entity_properties"

    icon = "OBJECT_DATA"

    bl_order = 0

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        maps = get_maps(context)
        if not maps:
            return

        groups = maps.groups
        active_group = groups.active_item
        layout.enabled = not groups.has_multiple_selection

        entities = active_group.entities
        if not entities:
            return

        has_multiple_selection = entities.has_multiple_selection
        selection = entities.selection
        active = entities.active_item

        row = layout.row()
        row.alignment = "RIGHT"
        SOLLUMZ_PT_entity_presets.draw_panel_header(row)

        layout.prop(active, "uuid_str")
        layout.prop(selection.owner, selection.propnames.map_data_name, icon_value=icon("map_container"))
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "linked_object")

        layout.separator()

        layout.prop(selection.owner, selection.propnames.archetype_name)
        layout.prop(selection.owner, selection.propnames.is_mlo)
        layout.separator()

        active_map_locked = active_group.is_map_locked(active.map_data_uuid)
        if active.is_mlo:
            # On MLO instances we hide the following properties because they are unused:
            #  - priority_level (MLO instances are always REQUIRED)
            #  - lod_level (MLO instances are always HD or ORPHANHD)
            #  - child_lod_dist
            #  - ambient_occlusion_multiplier
            #  - artificial_ambient_occlusion
            #  - tint_value
            #  - mlo_floor_id
            if active_map_locked:
                layout.prop(selection.owner, selection.propnames.parent_index)
            else:
                layout.prop(selection.owner, selection.propnames.parent_name)
            layout.prop(selection.owner, selection.propnames.lod_dist)

            layout.prop(selection.owner, selection.propnames.mlo_group_id)
            layout.prop(selection.owner, selection.propnames.mlo_default_entity_sets)
            col = layout.column(heading="Flags")
            col.prop(selection.owner, selection.propnames.mlo_turn_on_gps)
            col.prop(selection.owner, selection.propnames.mlo_cap_entities_alpha)
            col.prop(selection.owner, selection.propnames.mlo_short_fade_distance)

            row = layout.row()
            row.prop(selection.owner, selection.propnames.mlo_num_exit_portals)
            row.operator(
                map_ops.SOLLUMZ_OT_map_mlo_instance_calc_num_exit_portals.bl_idname, text="", icon="FILE_REFRESH"
            )
        else:
            if active_map_locked:
                layout.prop(selection.owner, selection.propnames.parent_index)
                layout.prop(selection.owner, selection.propnames.num_children_missing)
            else:
                layout.prop(selection.owner, selection.propnames.parent_name)
            layout.prop(selection.owner, selection.propnames.lod_level, expand=True)
            layout.prop(selection.owner, selection.propnames.lod_dist)
            layout.prop(selection.owner, selection.propnames.child_lod_dist)
            row = layout.row()
            row.active = active.is_orphan_hd  # priority level only used by ORPHANHD entities
            row.prop(selection.owner, selection.propnames.priority_level)
            layout.separator()
            layout.prop(selection.owner, selection.propnames.ambient_occlusion_multiplier)
            layout.prop(selection.owner, selection.propnames.artificial_ambient_occlusion)
            layout.prop(selection.owner, selection.propnames.tint_value)
            layout.prop(selection.owner, selection.propnames.is_critical)

        if not active.linked_object:
            col = layout.column()
            col.enabled = not has_multiple_selection
            col.prop(active, "position")
            col.prop(active, "rotation")
            col.prop(active, "scale_xy")
            col.prop(active, "scale_z")


class SOLLUMZ_UL_map_entity_extensions(ExtensionsListHelper, UIList):
    bl_idname = "SOLLUMZ_UL_map_entity_extensions"


class SOLLUMZ_PT_map_entity_extensions(MapEntityChildTabPanel, ExtensionsPanelHelper, Panel):
    bl_label = "Entity Extensions"
    bl_idname = "SOLLUMZ_PT_map_entity_extensions"

    icon = "CON_TRACKTO"

    bl_order = 1

    extension_host = HOST_MAP_ENTITY

    ADD_OPERATOR_ID = map_ops.SOLLUMZ_OT_map_entity_add_extension.bl_idname
    DELETE_OPERATOR_ID = map_ops.SOLLUMZ_OT_map_entity_delete_extension.bl_idname
    DUPLICATE_OPERATOR_ID = map_ops.SOLLUMZ_OT_map_entity_duplicate_extension.bl_idname
    EXTENSIONS_LIST_ID = SOLLUMZ_UL_map_entity_extensions.bl_idname

    @classmethod
    def get_extensions_container(self, context):
        maps = get_maps(context)
        group = maps.groups.active_item
        return group.entities.active_item

    def draw(self, context):
        maps = get_maps(context)
        self.layout.enabled = (
            not maps.groups.has_multiple_selection and not maps.groups.active_item.entities.has_multiple_selection
        )
        super().draw(context)


class SOLLUMZ_PT_map_entity_flags(MapEntityChildTabPanel, MultiSelectUIFlagsPanel, Panel):
    bl_idname = "SOLLUMZ_PT_map_entity_flags"
    bl_label = "Entity Flags"

    icon = "BOOKMARKS"

    bl_order = 2

    def get_flags_active(self, context):
        maps = get_maps(context)
        group = maps.groups.active_item
        return group.entities.active_item.flags

    def get_flags_selection(self, context):
        maps = get_maps(context)
        group = maps.groups.active_item
        return group.entities.selection.flags

    def draw(self, context):
        layout = self.layout
        maps = get_maps(context)
        layout.enabled = not maps.groups.has_multiple_selection

        row = layout.row()
        row.alignment = "RIGHT"
        SOLLUMZ_PT_entity_presets.draw_panel_header(row)

        super().draw(context)


def map_entities_filter_items(
    entities,
    filter_name: str,
    use_filter_sort_reverse: bool,
    use_filter_sort_alpha: bool,
) -> tuple[list[int], list[int]]:
    from ...shared.multiselection import _BITFLAG_FILTER_ITEM, _default_filter_items

    filter_flags, filter_order = _default_filter_items(
        entities,
        filter_name,
        use_filter_sort_reverse,
        use_filter_sort_alpha,
        name_prop="archetype_name",
    )

    # After the initial name filtering, remove all entities that are filtered out
    for i, entity in enumerate(entities):
        if not entity.is_filtered():
            if not filter_flags:
                # Empty list is equivalent to all items visible
                filter_flags = [_BITFLAG_FILTER_ITEM] * len(entities)

            filter_flags[i] &= ~_BITFLAG_FILTER_ITEM

    return filter_flags, filter_order


class SOLLUMZ_UL_map_group_entity_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_map_group_entity_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_map_group_select_entity.bl_idname
    name_prop = "archetype_name"

    def get_item_icon(self, item) -> str:
        return "HOME" if item.is_mlo else "OBJECT_DATA"

    def filter_items(self, context, data, propname):
        multiselect_collection_name = propname[:-1]  # remove '_' suffix
        collection = getattr(data, multiselect_collection_name)
        return map_entities_filter_items(
            collection, self.filter_name, self.use_filter_sort_reverse, self.use_filter_sort_alpha
        )


class SOLLUMZ_MT_map_group_entity_list_context_menu(Menu):
    bl_label = "Map Entities Specials"
    bl_idname = "SOLLUMZ_MT_map_group_entity_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_all_entities.bl_idname, text="Select All")
        op1 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_invert_entities.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_map_group_entity_list.last_filter_options.get("entities_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_PT_map_object_entity_properties(Panel):
    """Panel in the object properties showing the entity it is linked to"""

    bl_label = "Map Entity Properties"
    bl_idname = "SOLLUMZ_PT_map_object_entity_properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 1

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj is not None

    def draw(self, context):
        layout = self.layout

        aentity = active_entity_from_active_object(context)
        if not draw_cache_result(layout, aentity, "Entity not found"):
            return

        map_group, entity = aentity

        layout.use_property_split = True
        layout.use_property_decorate = False
        layout.operator(map_ops.SOLLUMZ_OT_map_view_object_in_sidebar.bl_idname)

        col = layout.column(align=True)
        split = col.split(factor=0.4)
        row = split.row()
        row.alignment = "RIGHT"
        row.label(text="Map")
        split.row().label(text=map_group.name)
        split = col.split(factor=0.4)
        row = split.row()
        row.alignment = "RIGHT"
        row.label(text="Archetype Name")
        split.row().label(text=entity.archetype_name)

        layout.separator()

        # See SOLLUMZ_PT_map_entities
        entity_map_locked = map_group.is_map_locked(entity.map_data_uuid)
        layout.prop(entity, "is_mlo")
        if entity.is_mlo:
            if entity_map_locked:
                layout.prop(entity, "parent_index")
            else:
                layout.prop(entity, "parent_name")
            layout.prop(entity, "lod_dist")

            layout.prop(entity, "mlo_group_id")
            layout.prop(entity, "mlo_default_entity_sets")
            col = layout.column(heading="Flags")
            col.prop(entity, "mlo_turn_on_gps")
            col.prop(entity, "mlo_cap_entities_alpha")
            col.prop(entity, "mlo_short_fade_distance")

            row = layout.row()
            row.prop(entity, "mlo_num_exit_portals")
            # TODO(ymap): this operator doesn't work on the active object
            # row.operator(map_ops.SOLLUMZ_OT_map_mlo_instance_calc_num_exit_portals.bl_idname, text="", icon="FILE_REFRESH")
        else:
            if entity_map_locked:
                layout.prop(entity, "parent_index")
                layout.prop(entity, "num_children_missing")
            else:
                layout.prop(entity, "parent_name")
            layout.prop(entity, "lod_level", expand=True)
            layout.prop(entity, "lod_dist")
            layout.prop(entity, "child_lod_dist")
            row = layout.row()
            row.active = entity.is_orphan_hd  # priority level only used by ORPHANHD entities
            row.prop(entity, "priority_level")
            layout.separator()
            layout.prop(entity, "ambient_occlusion_multiplier")
            layout.prop(entity, "artificial_ambient_occlusion")
            layout.prop(entity, "tint_value")
            layout.prop(entity, "is_critical")
