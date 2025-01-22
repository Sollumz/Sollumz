import bpy
from bpy.props import (
    BoolProperty
)
import os
from .properties import BoundFlags, CollisionMatFlags
from ..sollumz_properties import MaterialType, SollumType, BOUND_TYPES, BOUND_POLYGON_TYPES
from .collision_materials import collisionmats
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL, SOLLUMZ_PT_MAT_PANEL
from . import operators as ybn_ops


def generate_flags(layout, prop):
    grid = layout.grid_flow(columns=4, even_columns=True, even_rows=True)
    for prop_name in BoundFlags.__annotations__:
        grid.prop(prop, prop_name)


class SOLLUMZ_PT_COL_MAT_PROPERTIES_PANEL(bpy.types.Panel):
    bl_label = "Collision Material Properties"
    bl_idname = "SOLLUMZ_PT_COL_MAT_PROPERTIES_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_MAT_PANEL.bl_idname

    bl_order = 0

    @classmethod
    def poll(cls, context):
        aobj = context.active_object

        if aobj is None:
            return False

        active_mat = aobj.active_material
        return active_mat is not None and active_mat.sollum_type == MaterialType.COLLISION

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        mat = context.active_object.active_material

        grid = self.layout.grid_flow(columns=2, even_columns=True, even_rows=True)
        grid.prop(mat.collision_properties, "procedural_id")
        grid.prop(mat.collision_properties, "room_id")
        grid.prop(mat.collision_properties, "ped_density")
        grid.prop(mat.collision_properties, "material_color_index")


class SOLLUMZ_PT_BOUND_PROPERTIES_PANEL(bpy.types.Panel):
    bl_label = "Bound Properties"
    bl_idname = "SOLLUMZ_PT_BOUND_PROPERTIES_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_OBJECT_PANEL.bl_idname

    bl_order = 0

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and (obj.sollum_type in BOUND_TYPES or obj.sollum_type in BOUND_POLYGON_TYPES)

    def draw(self, context):
        # nothing here currently
        pass


class SOLLUMZ_PT_BOUND_SHAPE_PANEL(bpy.types.Panel):
    bl_label = "Shape"
    bl_idname = "SOLLUMZ_PT_BOUND_SHAPE_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BOUND_PROPERTIES_PANEL.bl_idname

    bl_order = 0

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj and (obj.sollum_type != SollumType.BOUND_COMPOSITE and obj.sollum_type != SollumType.BOUND_GEOMETRY and obj.sollum_type != SollumType.BOUND_GEOMETRYBVH and obj.sollum_type != SollumType.BOUND_CLOTH and obj.sollum_type != SollumType.BOUND_POLY_TRIANGLE)

    def draw(self, context):
        obj = context.active_object
        shape = obj.sz_bound_shape

        self.layout.use_property_split = True
        self.layout.use_property_decorate = False

        grid = self.layout.grid_flow(columns=2, row_major=True)

        match obj.sollum_type:
            case SollumType.BOUND_BOX | SollumType.BOUND_POLY_BOX:
                grid.prop(shape, "box_extents")
            case SollumType.BOUND_SPHERE | SollumType.BOUND_POLY_SPHERE:
                grid.prop(shape, "sphere_radius")
            case SollumType.BOUND_CAPSULE | SollumType.BOUND_POLY_CAPSULE:
                grid.prop(shape, "capsule_radius")
                grid.prop(shape, "capsule_length")
            case SollumType.BOUND_CYLINDER | SollumType.BOUND_POLY_CYLINDER | SollumType.BOUND_DISC:
                grid.prop(shape, "cylinder_radius")
                grid.prop(shape, "cylinder_length")
            case _:
                pass

class SOLLUMZ_PT_BOUND_FLAGS_PANEL(bpy.types.Panel):
    bl_label = "Composite Flags"
    bl_idname = "SOLLUMZ_PT_BOUND_FLAGS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_BOUND_PROPERTIES_PANEL.bl_idname

    bl_order = 1

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj is not None and obj.parent is not None and obj.parent.sollum_type == SollumType.BOUND_COMPOSITE and obj.sollum_type in BOUND_TYPES

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        layout.label(text="Type Flags")
        generate_flags(layout, obj.composite_flags1)
        layout.separator_spacer()
        layout.label(text="Include Flags")
        generate_flags(layout, obj.composite_flags2)


class SOLLUMZ_PT_MATERIAL_COL_FLAGS_PANEL(bpy.types.Panel):
    bl_label = "Collision Flags"
    bl_idname = "SOLLUMZ_PT_MATERIAL_COL_FLAGS_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "object"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_COL_MAT_PROPERTIES_PANEL.bl_idname

    bl_order = 1

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        mat = obj.active_material
        return mat and mat.sollum_type == MaterialType.COLLISION

    def draw(self, context):
        mat = context.active_object.active_material
        layout = self.layout
        layout.label(text="Flags")
        grid = layout.grid_flow(columns=4, even_columns=True, even_rows=True)
        for prop_name in CollisionMatFlags.__annotations__:
            grid.prop(mat.collision_flags, prop_name)


class SOLLUMZ_UL_COLLISION_MATERIALS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_COLLISION_MATERIALS_LIST"

    use_filter_favorites: BoolProperty(name="Filter Favorites")

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        name = collisionmats[item.index].ui_name
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=name, icon="MATERIAL")
            favorite_icon = "SOLO_ON" if item.favorite else "SOLO_OFF"
            row.prop(item, "favorite", text="", toggle=True, emboss=False, icon=favorite_icon)
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=name, emboss=False, icon="MATERIAL")

    def draw_filter(self, context, layout):
        row = layout.row()

        subrow = row.row(align=True)
        subrow.prop(self, "filter_name", text="")
        subrow.prop(self, "use_filter_invert", text="", toggle=True, icon="ARROW_LEFTRIGHT")

        subrow = row.row(align=True)
        subrow.prop(self, "use_filter_sort_alpha", text="", toggle=True, icon="SORTALPHA")
        icon = "SORT_DESC" if self.use_filter_sort_reverse else "SORT_ASC"
        subrow.prop(self, "use_filter_sort_reverse", text="", toggle=True, icon=icon)

        subrow = row.row(align=True)
        subrow.prop(self, "use_filter_favorites", text="", toggle=True, icon="SOLO_ON")

    def filter_items(self, context, data, propname):
        collision_materials = getattr(data, propname)
        helper_funcs = bpy.types.UI_UL_list

        # Default return values.
        flt_flags = []
        flt_neworder = []

        # Filtering by name
        if self.filter_name:
            filter_name = self.filter_name.replace(" ", "").replace("_", "")
            flt_flags = helper_funcs.filter_items_by_name(
                filter_name, self.bitflag_filter_item, collision_materials, "search_name",
                reverse=self.use_filter_sort_reverse
            )

        # Filter favorites.
        if self.use_filter_favorites:
            if not flt_flags:
                flt_flags = [self.bitflag_filter_item] * len(collision_materials)

            for idx, collision_material in enumerate(collision_materials):
                if not collision_material.favorite:
                    flt_flags[idx] &= ~self.bitflag_filter_item

        # Reorder by name or average weight.
        if self.use_filter_sort_alpha:
            flt_neworder = helper_funcs.sort_items_by_name(collision_materials, "search_name")

        return flt_flags, flt_neworder


class SOLLUMZ_UL_FLAG_PRESET_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_FLAG_PRESET_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon="BOOKMARKS")
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon="BOOKMARKS")


class SOLLUMZ_PT_COLLISION_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Collisions"
    bl_idname = "SOLLUMZ_PT_COLLISION_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 2

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="MESH_CYLINDER")

    def draw(self, context):
        pass


class CollisionToolChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = SOLLUMZ_PT_COLLISION_TOOL_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_COLLISION_TOOL_PANEL.bl_category


class SOLLUMZ_PT_CREATE_BOUND_PANEL(CollisionToolChildPanel, bpy.types.Panel):
    bl_label = "Create Bounds"
    bl_idname = "SOLLUMZ_PT_CREATE_BOUND_PANEL"
    bl_order = 0

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="MOD_WIREFRAME")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.operator(ybn_ops.SOLLUMZ_OT_convert_to_composite.bl_idname,
                     icon="FILE_REFRESH")
        row.prop(context.scene, "bound_child_type")

        row = layout.row()
        row.prop(context.scene, "create_seperate_composites")
        row.prop(context.scene, "center_composite_to_selection")

        layout.separator()

        row = layout.row(align=True)
        row.operator(ybn_ops.SOLLUMZ_OT_create_bound.bl_idname, icon="CUBE")
        row.prop(context.scene, "create_bound_type", text="")

        row = layout.row(align=True)
        row.operator(
            ybn_ops.SOLLUMZ_OT_create_polygon_bound.bl_idname, icon="MESH_CAPSULE")
        row.prop(context.scene, "create_poly_bound_type", text="")

        layout.separator()

        split = layout.split(factor=0.5, align=True)
        row = split.row(align=True)
        box_from_verts_op = row.operator(
            ybn_ops.SOLLUMZ_OT_create_polygon_box_from_verts.bl_idname, icon="GROUP_VERTEX"
        )
        subrow = split.row(align=True)
        subrow.prop(context.scene, "poly_bound_type_verts", text="")
        if bpy.app.version >= (4, 1, 0):
            subrow.prop(context.window_manager, "sz_create_bound_box_parent", text="", placeholder="Parent")
        else:
            subrow.prop(context.window_manager, "sz_create_bound_box_parent", text="")

        box_parent = context.window_manager.sz_create_bound_box_parent
        box_from_verts_op.parent_name = box_parent.name if box_parent else ""
        box_from_verts_op.sollum_type = context.scene.poly_bound_type_verts


class SOLLUMZ_PT_CREATE_MATERIAL_PANEL(CollisionToolChildPanel, bpy.types.Panel):
    bl_label = "Create Collision Material"
    bl_idname = "SOLLUMZ_PT_CREATE_MATERIAL_PANEL"
    bl_order = 1

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="NODE_MATERIAL")

    def draw(self, context):
        layout = self.layout
        layout.template_list(
            SOLLUMZ_UL_COLLISION_MATERIALS_LIST.bl_idname, "",
            context.window_manager, "sz_collision_materials", context.window_manager, "sz_collision_material_index"
        )
        row = layout.row()
        row.operator(ybn_ops.SOLLUMZ_OT_create_collision_material.bl_idname)
        row = layout.row()
        row.operator(
            ybn_ops.SOLLUMZ_OT_convert_to_collision_material.bl_idname)
        row.operator(
            ybn_ops.SOLLUMZ_OT_clear_and_create_collision_material.bl_idname)
        row = layout.row()
        row.operator(
            ybn_ops.SOLLUMZ_OT_convert_non_collision_materials_to_selected.bl_idname)


class SOLLUMZ_PT_FLAG_PRESETS_PANEL(CollisionToolChildPanel, bpy.types.Panel):
    bl_label = "Flag Presets"
    bl_idname = "SOLLUMZ_PT_FLAG_PRESETS_PANEL"
    bl_order = 2

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="ALIGN_TOP")

    def draw(self, context):
        layout = self.layout

        row = layout.row()
        row.template_list(SOLLUMZ_UL_FLAG_PRESET_LIST.bl_idname, "flag_presets",
                          context.window_manager, "sz_flag_presets", context.window_manager, "sz_flag_preset_index")
        col = row.column(align=True)
        col.operator(ybn_ops.SOLLUMZ_OT_save_flag_preset.bl_idname, text="", icon="ADD")
        col.operator(ybn_ops.SOLLUMZ_OT_delete_flag_preset.bl_idname, text="", icon="REMOVE")
        col.separator()
        col.menu(SOLLUMZ_MT_flag_presets_context_menu.bl_idname, icon="DOWNARROW_HLT", text="")

        row = layout.row()
        row.operator(ybn_ops.SOLLUMZ_OT_load_flag_preset.bl_idname, icon='CHECKMARK')

        row = layout.row()
        row.operator(ybn_ops.SOLLUMZ_OT_clear_col_flags.bl_idname, icon='SHADERFX')


class SOLLUMZ_MT_flag_presets_context_menu(bpy.types.Menu):
    bl_label = "Flag Presets Specials"
    bl_idname = "SOLLUMZ_MT_flag_presets_context_menu"

    def draw(self, _context):
        layout = self.layout

        from .properties import get_flag_presets_path
        path = get_flag_presets_path()
        layout.enabled = os.path.exists(path)
        layout.operator("wm.path_open", text="Open Presets File").filepath = path
