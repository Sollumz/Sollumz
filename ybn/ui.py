import bpy
from .properties import BoundFlags, CollisionProperties, CollisionMatFlags, BoundProperties
from Sollumz.sollumz_properties import MaterialType
from .collision_materials import collisionmats
from .operators import *

def draw_collision_material_properties(layout, mat):
    grid = layout.grid_flow(columns=2, even_columns=True, even_rows=True)
    for prop in CollisionProperties.__annotations__:
        if prop == 'collision_index':
            continue
        grid.prop(mat.collision_properties, prop)

def generate_flags(layout, prop):
    grid = layout.grid_flow(columns=4, even_columns=True, even_rows=True)
    for prop_name in BoundFlags.__annotations__:
        grid.prop(prop, prop_name)

def draw_bound_properties(layout, obj):
    row = layout.row()
    # grid = layout.grid_flow(columns=2, even_columns=True, even_rows=True)
    grid = layout.grid_flow(columns=2, row_major=True)
    for prop in BoundProperties.__annotations__:
        grid.prop(obj.bound_properties, prop)
    # row.prop(obj.bound_properties, "procedural_id")
    # row.prop(obj.bound_properties, "room_id")
    # row = layout.row()
    # row.prop(obj.bound_properties, "ped_density")
    # row.prop(obj.bound_properties, "poly_flags")
    # row = layout.row()
    # row.prop(obj.bound_properties, "inertia")
    # row = layout.row()
    # row.prop(obj.bound_properties, "margin")
    # row.prop(obj.bound_properties, "volume")


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
        return obj and (obj.sollum_type == BoundType.GEOMETRY or obj.sollum_type == BoundType.GEOMETRYBVH)

    def draw(self, context):
        obj = context.active_object
        layout = self.layout
        layout.label(text = "Composite Flags 1")
        # layout.separator(factor=0.5)
        generate_flags(layout, obj.composite_flags1)
        layout.separator_spacer()
        layout.label(text = "Composite Flags 2")
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
        return mat and (is_sollum_type(mat, MaterialType) and mat.sollum_type != MaterialType.NONE)

    def draw(self, context):
        mat = context.active_object.active_material
        layout = self.layout
        # box.use_property_split = False
        layout.label(text = "Flags")
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
    bl_label = "Static Collision Tools"
    bl_idname = "SOLLUMZ_PT_COLLISION_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}


    def draw(self, context):
        layout = self.layout
        row = layout.row()
        if context.active_object and context.active_object.sollum_type == BoundType.COMPOSITE:
            row.operator(SOLLUMZ_OT_center_composite.bl_idname)

class SOLLUMZ_PT_CREATE_BOUND_PANEL(bpy.types.Panel):
    bl_label = "Create Bounds"
    bl_idname = 'SOLLUMZ_PT_CREATE_BOUND_PANEL'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_COLLISION_TOOL_PANEL.bl_idname
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_bound_composite.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_geometry_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_geometrybvh_bound.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_box_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_sphere_bound.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_capsule_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_cylinder_bound.bl_idname)
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_disc_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_cloth_bound.bl_idname)
        layout.separator()
        row = layout.row()
        row.operator(SOLLUMZ_OT_create_polygon_bound.bl_idname)
        row.prop(context.scene, "poly_bound_type", text="")

class SOLLUMZ_PT_CREATE_MATERIAL_PANEL(bpy.types.Panel):
    bl_label = "Create Material"
    bl_idname = "SOLLUMZ_PT_CREATE_MATERIAL_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_COLLISION_TOOL_PANEL.bl_idname
    bl_order = 1

    def draw(self, context):
        layout = self.layout
        layout.template_list(
            SOLLUMZ_UL_COLLISION_MATERIALS_LIST.bl_idname, "", context.scene, "collision_materials", context.scene, "collision_material_index"
        )
        layout.operator(SOLLUMZ_OT_create_collision_material.bl_idname)


class SOLLUMZ_PT_BOUND_CONVERSION_PANEL(bpy.types.Panel):
    bl_label = "Conversion"
    bl_idname = 'SOLLUMZ_PT_BOUND_CONVERSION_PANEL'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_COLLISION_TOOL_PANEL.bl_idname
    bl_order = 2

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.alignment = 'LEFT'
        row.operator(SOLLUMZ_OT_convert_mesh_to_collision.bl_idname)
        row.prop(context.scene, 'multiple_ybns')
        row.prop(context.scene, 'convert_ybn_use_mesh_names')
        row = layout.row()
        if context.active_object and context.active_object.mode == 'EDIT':
            row.operator(SOLLUMZ_OT_mesh_to_polygon_bound.bl_idname)
            row.prop(context.scene, "convert_poly_bound_type", text="")
            row.prop(context.scene, "convert_poly_parent", expand=True)

class SOLLUMZ_PT_FLAG_PRESETS_PANEL(bpy.types.Panel):
    bl_label = "Flag Presets"
    bl_idname = 'SOLLUMZ_PT_FLAG_PRESETS_PANEL'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    # bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_BOUND_FLAGS_PANEL.bl_idname

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
        

class SOLLUMZ_MT_bound_objects_create(bpy.types.Menu):
    bl_label = "Bound Objects"
    bl_idname = "SOLLUMZ_MT_bound_objects_create"

    def draw(self, context):
        layout = self.layout
        layout.operator(SOLLUMZ_OT_create_bound_composite.bl_idname)
        layout.operator(SOLLUMZ_OT_create_geometry_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_geometrybvh_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_box_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_sphere_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_capsule_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_cylinder_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_disc_bound.bl_idname)
        layout.operator(SOLLUMZ_OT_create_cloth_bound.bl_idname)

def SollumzBoundContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_bound_objects_create.bl_idname)

class SOLLUMZ_MT_polygon_bound_create(bpy.types.Menu):
    bl_label = "Polygon Bound Objects"
    bl_idname = "SOLLUMZ_MT_polygon_bound_create"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "poly_bound_type")
        layout.operator(SOLLUMZ_OT_create_polygon_bound.bl_idname) 

class SOLLUMZ_MT_polygon_bound_convert(bpy.types.Menu):
    bl_label = "Convert Polygon Bound Objects"
    bl_idname = "SOLLUMZ_MT_polygon_bound_convert"

    def draw(self, context):
        layout = self.layout
        layout.prop(context.scene, "convert_poly_bound_type")
        layout.operator(SOLLUMZ_OT_mesh_to_polygon_bound.bl_idname) 

def SollumzPolygonBoundContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_polygon_bound_create.bl_idname)

def register():
    bpy.types.SOLLUMZ_MT_create.append(SollumzBoundContextMenu)
    bpy.types.SOLLUMZ_MT_create.append(SollumzPolygonBoundContextMenu)

def unregister():
    bpy.types.SOLLUMZ_MT_create.remove(SollumzBoundContextMenu)
    bpy.types.SOLLUMZ_MT_create.remove(SollumzPolygonBoundContextMenu)