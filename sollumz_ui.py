import bpy
from Sollumz.sollumz_properties import BoundType, PolygonType, ObjectType, MaterialType, is_sollum_type
from Sollumz.ybn.ui import draw_bound_properties, draw_collision_material_properties
from Sollumz.ydr.ui import draw_drawable_properties, draw_geometry_properties, draw_material_properties


class SOLLUMZ_PT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz Material Panel"
    bl_idname = "SOLLUMZ_PT_MAT_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = "material"

    def draw(self, context):
        layout = self.layout

        mat = None

        if(bpy.context.active_object.data != None and len(bpy.context.active_object.data.materials) > 0):
            mat = bpy.context.active_object.active_material
        else:
            return

        if(mat == None):
            return 

        if mat.sollum_type == MaterialType.MATERIAL:
            draw_material_properties(layout, mat)
        elif mat.sollum_type == MaterialType.COLLISION:
            box = layout.box()
            draw_collision_material_properties(box, mat)
            
        else:
            box = layout.box()

    
class SOLLUMZ_PT_MAIN_PANEL(bpy.types.Panel):
    bl_label = "Object Properties"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_category = "Sollumz"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    
    def draw(self, context):
        layout = self.layout

        obj = bpy.context.active_object

        if(obj == None):
            return

        box = layout.box()
        row = box.row()
        row.enabled = False
        row.prop(obj, "sollum_type")

        if obj.sollum_type == ObjectType.DRAWABLE:
            draw_drawable_properties(box, obj)
        elif obj.sollum_type == ObjectType.GEOMETRY:
            draw_geometry_properties(box, obj)
        elif is_sollum_type(obj, BoundType) or is_sollum_type(obj, PolygonType):
            draw_bound_properties(box, obj)