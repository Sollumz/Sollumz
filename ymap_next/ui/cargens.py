import bpy
from bpy.types import (
    Menu,
    Panel,
    UILayout,
    UIList,
)

from ...shared.multiselection import (
    MultiSelectUIListMixin,
    multiselect_ui_draw_list,
)
from ...sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL
from ..context import active_cargen_from_active_object, active_group
from ..gta5.presets.cargen import SOLLUMZ_PT_cargen_presets
from ..operators import (
    cargens as map_cargens_ops,
)
from ..operators import (
    map as map_ops,
)
from ..operators import (
    selection as map_select_ops,
)
from ..properties.map import (
    MAP_CARGEN_FLAG_PROPS,
    get_maps,
)
from .common import draw_cache_result
from .map import MapChildTabPanel
from ...icons import icon


class SOLLUMZ_PT_map_cargens(MapChildTabPanel, Panel):
    bl_label = "Car Generators"
    bl_idname = "SOLLUMZ_PT_map_cargens"
    bl_order = 1

    @classmethod
    def get_tab_icon(cls) -> int:
        return icon("cargen")

    @classmethod
    def get_label(cls, context) -> str:
        agroup = active_group(context)
        return cls.bl_label + (f" ({len(agroup.cargens)})" if agroup else "")

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
        cargens = active_group.cargens
        multiselect_ui_draw_list(
            self.layout,
            cargens,
            map_ops.SOLLUMZ_OT_map_group_new_cargen.bl_idname,
            map_ops.SOLLUMZ_OT_map_group_delete_cargen.bl_idname,
            SOLLUMZ_UL_map_group_cargen_list,
            SOLLUMZ_MT_map_group_cargen_list_context_menu,
            "tool_panel",
        )

        if not cargens:
            return

        layout.operator(map_cargens_ops.SOLLUMZ_OT_map_cargen_create_object.bl_idname)
        layout.operator(map_cargens_ops.SOLLUMZ_OT_map_cargen_select_all_objects.bl_idname)

        layout.separator()

        has_multiple_selection = cargens.has_multiple_selection
        selection = cargens.selection
        active = cargens.active_item

        row = layout.row()
        row.alignment = "RIGHT"
        SOLLUMZ_PT_cargen_presets.draw_panel_header(row)

        layout.prop(active, "uuid_str")
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "map_data_name", icon_value=icon("map_container"))
        row = layout.row()
        row.enabled = not has_multiple_selection
        row.prop(active, "linked_collection")

        layout.separator()

        layout.prop(selection.owner, selection.propnames.name)
        layout.prop(selection.owner, selection.propnames.model)
        layout.prop(selection.owner, selection.propnames.model_set)
        layout.prop(selection.owner, selection.propnames.creation_rule)

        split = layout.split(factor=0.4)
        row = split.row()
        row.alignment = "RIGHT"
        row.label(text="Flags")
        col = split.column_flow(align=True, columns=2)
        col.use_property_split = False
        for prop_name, _ in MAP_CARGEN_FLAG_PROPS:
            col.prop(selection.owner, getattr(selection.propnames, prop_name))

        layout.prop(selection.owner, selection.propnames.livery)
        split = layout.split(factor=0.4)
        row = split.row()
        row.alignment = "RIGHT"
        row.label(text="Body Color Remap")
        row = split.row(align=True)
        for i in range(4):
            row.prop(selection.owner, selection.propnames.body_color_remap, index=i, text="")


class SOLLUMZ_UL_map_group_cargen_list(MultiSelectUIListMixin, UIList):
    bl_idname = "SOLLUMZ_UL_map_group_cargen_list"
    multiselect_operator = map_select_ops.SOLLUMZ_OT_map_group_select_cargen.bl_idname
    name_prop = "ui_label"
    name_editable = False

    def get_item_icon(self, item) -> int:
        return icon("cargen")


class SOLLUMZ_MT_map_group_cargen_list_context_menu(Menu):
    bl_label = "Map Car Generators Specials"
    bl_idname = "SOLLUMZ_MT_map_group_cargen_list_context_menu"

    def draw(self, _context):
        layout = self.layout
        op0 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_all_cargens.bl_idname, text="Select All")
        op1 = layout.operator(map_select_ops.SOLLUMZ_OT_map_group_select_invert_cargens.bl_idname, text="Invert")
        if filter_opts := SOLLUMZ_UL_map_group_cargen_list.last_filter_options.get("cargens_tool_panel", None):
            filter_opts.apply_to_operator(op0)
            filter_opts.apply_to_operator(op1)


class SOLLUMZ_PT_map_object_cargen_properties(Panel):
    """Panel in the object properties showing the cargen collection it is linked to"""

    bl_label = "Map Cargen Properties"
    bl_idname = "SOLLUMZ_PT_map_object_cargen_properties"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname
    bl_order = 2

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj is not None

    def draw(self, context):
        layout = self.layout

        acargen = active_cargen_from_active_object(context)
        if not draw_cache_result(layout, acargen, "Car generator not found"):
            return

        map_group, cargen = acargen
        collection = cargen.linked_collection

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
        row.label(text="Car Generator")
        split.row().label(text=cargen.ui_label)

        split = col.split(factor=0.4)
        row = split.row()
        row.alignment = "RIGHT"
        row.label(text="Collection")
        n = len(collection.objects)
        split.row().label(text=f"{collection.name} ({n} cargen{'s' if n != 1 else ''})")
        layout.operator(map_cargens_ops.SOLLUMZ_OT_map_cargen_move_to_new_collection.bl_idname)

        layout.separator()

        layout.prop(cargen, "name")
        layout.prop(cargen, "model")
        layout.prop(cargen, "model_set")
        layout.prop(cargen, "creation_rule")

        split = layout.split(factor=0.4)
        row = split.row()
        row.alignment = "RIGHT"
        row.label(text="Flags")
        col = split.column_flow(align=True, columns=2)
        col.use_property_split = False
        for prop_name, _ in MAP_CARGEN_FLAG_PROPS:
            col.prop(cargen, prop_name)

        layout.prop(cargen, "livery")
        split = layout.split(factor=0.4)
        row = split.row()
        row.alignment = "RIGHT"
        row.label(text="Body Color Remap")
        row = split.row(align=True)
        for i in range(4):
            row.prop(cargen, "body_color_remap", index=i, text="")
