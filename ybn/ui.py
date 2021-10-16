import bpy
from Sollumz.sollumz_properties import PolygonType, is_sollum_type
from .properties import BoundProperties, BoundFlags, CollisionProperties, CollisionMatFlags
from .collision_materials import collisionmats
from .operators import *

def draw_collision_material_properties(box, mat):
    row = box.row()
    index = 0
    for prop in CollisionProperties.__annotations__:
        if prop == 'collision_index':
            continue
        if index % 2 == 0 and index > 1:
            row = box.row()
        row.prop(mat.collision_properties, prop)
        index += 1

    box = box.box()
    box.label(text = "Flags")  
    row = box.row()
    index = 0
    for prop in CollisionMatFlags.__annotations__:
        if index % 4 == 0 and index > 1:
            row = box.row()
        row.prop(mat.collision_flags, prop)
        index += 1

def generate_flags(box, prop):
    index = 0
    row = box.row() 
    for prop_name in BoundFlags.__annotations__:
        # 4 rows per box
        if index % 4 == 0 and index > 0:
            row = box.row()
        row.prop(prop, prop_name)
        index += 1

def draw_bound_properties(layout, obj):
    index = 0
    row = layout.row()
    row.prop(obj.bound_properties, "procedural_id")
    row.prop(obj.bound_properties, "room_id")
    row = layout.row()
    row.prop(obj.bound_properties, "ped_density")
    row.prop(obj.bound_properties, "poly_flags")
    row = layout.row()
    row.prop(obj.bound_properties, "inertia")
    row.prop(obj.bound_properties, "margin")
    row.prop(obj.bound_properties, "volume")

    if obj.sollum_type != BoundType.COMPOSITE:
        generate_flags(layout.box(), obj.composite_flags1)
        layout.label(text = "Composite Flags 2")
        generate_flags(layout.box(), obj.composite_flags2)
        row = layout.row()
        row.operator(SOLLUMZ_OT_clear_col_flags.bl_idname)   


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

        box = layout.box()
        box.label(text = "Create Material")
        box.template_list(
            SOLLUMZ_UL_COLLISION_MATERIALS_LIST.bl_idname, "", context.scene, "collision_materials", context.scene, "collision_material_index"
        )
        box.operator(SOLLUMZ_OT_create_collision_material.bl_idname)
        box = layout.box()
        box.label(text = "Flag Presets")
        box.template_list(
            SOLLUMZ_UL_FLAG_PRESET_LIST.bl_idname, "", context.scene, "flag_presets", context.scene, "flag_preset_index"
        )
        row = box.row()
        row.operator(SOLLUMZ_OT_save_flag_preset.bl_idname)
        row.prop(context.scene, 'new_flag_preset_name', text='Name')
        row = box.row()
        row.operator(SOLLUMZ_OT_delete_flag_preset.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_load_flag_preset.bl_idname)
        box = layout.box()
        box.label(text = "Create Bound Objects")
        row = box.row()
        row.operator(SOLLUMZ_OT_create_bound_composite.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_create_geometry_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_geometrybvh_bound.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_create_box_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_sphere_bound.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_create_capsule_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_cylinder_bound.bl_idname)
        row = box.row()
        row.operator(SOLLUMZ_OT_create_disc_bound.bl_idname)
        row.operator(SOLLUMZ_OT_create_cloth_bound.bl_idname)
        box = layout.box()
        box.label(text = "Create Polygon Bound Objects")
        row = box.row()
        row.operator(SOLLUMZ_OT_create_polygon_bound.bl_idname)
        row.prop(context.scene, "poly_bound_type")
        box = layout.box()
        box.label(text = "Conversion Tools")
        row = box.row()
        row.operator(SOLLUMZ_OT_convert_mesh_to_collision.bl_idname)
        row.prop(context.scene, 'multiple_ybns')
        row.prop(context.scene, 'convert_ybn_use_mesh_names')
        row = box.row()
        if context.active_object and context.active_object.mode == 'EDIT':
            row.operator(SOLLUMZ_OT_mesh_to_polygon_bound.bl_idname)
            row.prop(context.scene, "convert_poly_bound_type")
            row.prop(context.scene, "convert_poly_parent")


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