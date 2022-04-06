import bpy
from .properties import BoundFlags, CollisionProperties, CollisionMatFlags, BoundProperties
from ..sollumz_properties import MaterialType, SollumType, BOUND_TYPES, BOUND_POLYGON_TYPES
from .collision_materials import collisionmats
from .operators import *
from ..sollumz_ui import SOLLUMZ_PT_OBJECT_PANEL, SOLLUMZ_PT_MAT_PANEL


def draw_collision_material_properties(self, context):
    obj = context.active_object
    if not obj:
        return
    mat = obj.active_material
    if mat and mat.sollum_type == MaterialType.COLLISION:
        grid = self.layout.grid_flow(
            columns=2, even_columns=True, even_rows=True)
        for prop in CollisionProperties.__annotations__:
            if prop == 'collision_index':
                continue
            grid.prop(mat.collision_properties, prop)


def generate_flags(layout, prop):
    grid = layout.grid_flow(columns=4, even_columns=True, even_rows=True)
    for prop_name in BoundFlags.__annotations__:
        grid.prop(prop, prop_name)


def draw_bound_properties(self, context):
    obj = context.active_object
    if obj and obj.sollum_type in BOUND_TYPES:
        grid = self.layout.grid_flow(columns=2, row_major=True)
        for prop in BoundProperties.__annotations__:
            if "unk_float" in prop:
                continue
            grid.prop(obj.bound_properties, prop)
        if obj.sollum_type == SollumType.BOUND_GEOMETRY:
            grid.prop(obj.bound_properties, "unk_float_1")
            grid.prop(obj.bound_properties, "unk_float_2")


class SOLLUMZ_PT_BOUND_SHAPE_PANEL(bpy.types.Panel):
    bl_label = 'Shape'
    bl_idname = "SOLLUMZ_PT_BOUND_SHAPE_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "SOLLUMZ_PT_MAIN_PANEL"

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj and ((obj.sollum_type in BOUND_TYPES or obj.sollum_type in BOUND_POLYGON_TYPES) and obj.sollum_type != SollumType.BOUND_COMPOSITE and obj.sollum_type != SollumType.BOUND_POLY_BOX and obj.sollum_type != SollumType.BOUND_POLY_TRIANGLE)

    def draw(self, context):
        obj = context.active_object
        self.layout.use_property_split = True
        grid = self.layout.grid_flow(columns=2, row_major=True)
        # if obj.sollum_type != SollumType.BOUND_GEOMETRY and obj.sollum_type != SollumType.BOUND_GEOMETRYBVH and obj.sollum_type != SollumType.BOUND_BOX:
        if not obj.sollum_type in [SollumType.BOUND_GEOMETRY, SollumType.BOUND_GEOMETRYBVH, SollumType.BOUND_BOX, SollumType.BOUND_POLY_BOX, SollumType.BOUND_POLY_TRIANGLE]:
            grid.prop(obj, 'bound_radius',
                      text='SphereRadius' if obj.sollum_type in BOUND_TYPES else 'Radius')
        if obj.sollum_type == SollumType.BOUND_CYLINDER or obj.sollum_type == SollumType.BOUND_POLY_CYLINDER or obj.sollum_type == SollumType.BOUND_POLY_CAPSULE:
            grid.prop(obj, 'bound_length')
        if obj.sollum_type == SollumType.BOUND_BOX:
            grid.prop(obj, 'bound_dimensions')
        if obj.sollum_type in BOUND_TYPES:
            grid.prop(obj, 'margin')


class SOLLUMZ_PT_BOUND_FLAGS_PANEL(bpy.types.Panel):
    bl_label = 'Collision Flags'
    bl_idname = "SOLLUMZ_PT_BOUND_FLAGS_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "SOLLUMZ_PT_MAIN_PANEL"

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj and (obj.sollum_type == SollumType.BOUND_GEOMETRY or obj.sollum_type == SollumType.BOUND_GEOMETRYBVH)

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        layout.label(text="Composite Flags 1")
        # layout.separator(factor=0.5)
        generate_flags(layout, obj.composite_flags1)
        layout.separator_spacer()
        layout.label(text="Composite Flags 2")
        # layout.separator(factor=0.5)
        generate_flags(layout, obj.composite_flags2)


class SOLLUMZ_PT_MATERIAL_COL_FLAGS_PANEL(bpy.types.Panel):
    bl_label = 'Collision Flags'
    bl_idname = "SOLLUMZ_PT_MATERIAL_COL_FLAGS_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {"DEFAULT_CLOSED"}
    bl_parent_id = "SOLLUMZ_PT_MAT_PANEL"

    @classmethod
    def poll(cls, context):
        mat = context.active_object.active_material
        return mat and mat.sollum_type == MaterialType.COLLISION

    def draw(self, context):
        mat = context.active_object.active_material
        layout = self.layout
        # box.use_property_split = False
        layout.label(text="Flags")
        grid = layout.grid_flow(columns=4, even_columns=True, even_rows=True)
        for prop_name in CollisionMatFlags.__annotations__:
            grid.prop(mat.collision_flags, prop_name)


class SOLLUMZ_UL_COLLISION_MATERIALS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_COLLISION_MATERIALS_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        name = collisionmats[item.index].ui_name
        # If the object is selected
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=name, icon='MATERIAL')
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=name, emboss=False, icon='MATERIAL')


class SOLLUMZ_UL_FLAG_PRESET_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_FLAG_PRESET_LIST"

    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        # If the object is selected
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon='BOOKMARKS')
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon='BOOKMARKS')


class SOLLUMZ_PT_COLLISION_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Collision Tools"
    bl_idname = "SOLLUMZ_PT_COLLISION_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 2

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="MESH_CYLINDER")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.enabled = context.active_object is not None and context.active_object.sollum_type == SollumType.BOUND_COMPOSITE
        row.operator(SOLLUMZ_OT_center_composite.bl_idname,
                     icon="PIVOT_CURSOR")
        row = layout.row()
        row.operator(SOLLUMZ_OT_split_collision.bl_idname,
                     icon="SCULPTMODE_HLT")
        row.prop(context.scene, "split_collision_count")


class SOLLUMZ_PT_CREATE_BOUND_PANEL(bpy.types.Panel):
    bl_label = "Create Bounds"
    bl_idname = 'SOLLUMZ_PT_CREATE_BOUND_PANEL'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_COLLISION_TOOL_PANEL.bl_idname
    bl_order = 0

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="MOD_WIREFRAME")

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_bound.bl_idname)
        row.prop(context.scene, "create_bound_type")
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_polygon_bound.bl_idname)
        if context.active_object and context.active_object.mode == 'EDIT':
            row.prop(context.scene, "poly_bound_type_verts")
            row.prop(context.scene, "poly_parent", expand=True)
        else:
            row.prop(context.scene, "create_poly_bound_type")
        grid = layout.grid_flow(columns=3, even_columns=True, even_rows=True)
        grid.prop(context.scene, "use_mesh_name")
        grid.prop(context.scene, "create_seperate_objects")
        grid.prop(context.scene, "composite_replace_original")
        grid.prop(context.scene, "composite_create_bvh")
        grid.prop(context.scene, "create_center_to_selection")


class SOLLUMZ_PT_CREATE_MATERIAL_PANEL(bpy.types.Panel):
    bl_label = "Create Collision Material"
    bl_idname = "SOLLUMZ_PT_CREATE_MATERIAL_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_COLLISION_TOOL_PANEL.bl_idname
    bl_order = 1

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="NODE_MATERIAL")

    def draw(self, context):
        layout = self.layout
        layout.template_list(
            SOLLUMZ_UL_COLLISION_MATERIALS_LIST.bl_idname, "", context.scene, "collision_materials", context.scene, "collision_material_index"
        )
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_collision_material.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_convert_to_collision_material.bl_idname)
        row.operator(SOLLUMZ_OT_clear_and_create_collision_material.bl_idname)


class SOLLUMZ_PT_FLAG_PRESETS_PANEL(bpy.types.Panel):
    bl_label = "Flag Presets"
    bl_idname = 'SOLLUMZ_PT_FLAG_PRESETS_PANEL'
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_COLLISION_TOOL_PANEL.bl_idname

    def draw_header(self, context):
        # Example property to display a checkbox, can be anything
        self.layout.label(text="", icon="ALIGN_TOP")

    def draw(self, context):
        layout = self.layout
        layout.template_list(
            SOLLUMZ_UL_FLAG_PRESET_LIST.bl_idname, "", context.scene, "flag_presets", context.scene, "flag_preset_index"
        )
        row = layout.row()
        row.operator(SOLLUMZ_OT_save_flag_preset.bl_idname)
        row.prop(context.scene, 'new_flag_preset_name', text='Name')
        row = layout.row()
        row.operator(SOLLUMZ_OT_delete_flag_preset.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_load_flag_preset.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_clear_col_flags.bl_idname)


def register():
    SOLLUMZ_PT_OBJECT_PANEL.append(draw_bound_properties)
    SOLLUMZ_PT_MAT_PANEL.append(draw_collision_material_properties)


def unregister():
    SOLLUMZ_PT_OBJECT_PANEL.remove(draw_bound_properties)
    SOLLUMZ_PT_MAT_PANEL.remove(draw_collision_material_properties)
