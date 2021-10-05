import bpy
from Sollumz.sollumz_properties import PolygonType, is_sollum_type
from .properties import BoundProperties, BoundFlags, CollisionProperties, CollisionFlags

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
        row.prop(mat.collision_properties, prop)
        index += 1

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
        row.operator("sollumz.createcollisionmaterial")
        row.template_list(
            "SOLLUMZ_UL_COLLISION_MATERIALS_LIST", "", context.scene, "collision_materials", context.scene, "collision_material_index"
        )
        # row.prop(context.scene, "collision_material")
        box = layout.box()
        box.label(text = "Create Collision Objects")
        row = box.row()
        row.operator("sollumz.createboundcomposite")
        row.operator("sollumz.creategeometrybound")
        row = box.row()
        row.operator("sollumz.creategeometryboundbvh")
        row.operator("sollumz.createboxbound")
        row = box.row()
        row.operator("sollumz.createspherebound")
        row.operator("sollumz.createcapsulebound")
        row = box.row()
        row.operator("sollumz.createcylinderbound")
        row.operator("sollumz.creatediscbound")
        row = box.row()
        row.operator("sollumz.createclothbound")
        row = box.row()
        row.operator("sollumz.createpolygonbound")
        row.prop(context.scene, "poly_bound_type")


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
    elif is_poly:
        generate_flags(layout.box(), obj.composite_flags1)
        generate_flags(layout.box(), obj.composite_flags2)
        
        