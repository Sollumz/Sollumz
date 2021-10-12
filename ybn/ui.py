import bpy
from Sollumz.sollumz_properties import PolygonType, is_sollum_type
from .properties import BoundProperties, BoundFlags, CollisionProperties, CollisionFlags
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
    for prop in CollisionFlags.__annotations__:
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
    is_poly = is_sollum_type(obj, PolygonType)
    if not is_poly:
        index = 0
        row = layout.row()
        for prop in BoundProperties.__annotations__:
            if index % 2 == 0 and index > 0:
                row = layout.row()
            row.prop(obj.bound_properties, prop)
            index += 1
        generate_flags(layout.box(), obj.composite_flags1)
        generate_flags(layout.box(), obj.composite_flags2)

class SOLLUMZ_UL_COLLISION_FLAGS_LIST(bpy.types.UIList):
    def draw_item(
        self, context, layout, data, item, icon, active_data, active_propname, index
    ):
        # If the object is selected
        if self.layout_type in {"DEFAULT", "COMPACT"}:
            row = layout.row()
            row.label(text=item.name, icon='MATERIAL')
        elif self.layout_type in {"GRID"}:
            layout.alignment = "CENTER"
            layout.prop(item, "name",
                        text=item.name, emboss=False, icon='MATERIAL')


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


class SOLLUMZ_PT_COLLISION_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Ybn Tools"
    bl_idname = "SOLLUMZ_PT_COLLISION_TOOL_PANEL"
    bl_category = "Sollumz"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'

    def draw(self, context):
        layout = self.layout

        box = layout.box()
        box.label(text = "Create Material")
        row = box.row()
        row.template_list(
            SOLLUMZ_UL_COLLISION_MATERIALS_LIST.bl_idname, "", context.scene, "collision_materials", context.scene, "collision_material_index"
        )
        row = box.row()
        row.operator("sollumz.createcollisionmaterial")
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
        box.label(text = "Quick Convert Tools")
        box.operator(SOLLUMZ_OT_quick_convert_mesh_to_collision.bl_idname)


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

def SollumzPolygonBoundContextMenu(self, context):
    self.layout.menu(SOLLUMZ_MT_polygon_bound_create.bl_idname)
        

def register():
    bpy.types.SOLLUMZ_MT_create.append(SollumzBoundContextMenu)
    bpy.types.SOLLUMZ_MT_create.append(SollumzPolygonBoundContextMenu)

def unregister():
    bpy.types.SOLLUMZ_MT_create.remove(SollumzBoundContextMenu)
    bpy.types.SOLLUMZ_MT_create.remove(SollumzPolygonBoundContextMenu)