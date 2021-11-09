import bpy
from Sollumz.sollumz_helper import *
from Sollumz.sollumz_properties import BoundType, PolygonType, DrawableType, FragmentType, MaterialType
from Sollumz.ybn.ui import draw_bound_properties, draw_collision_material_properties
from Sollumz.ydr.ui import draw_drawable_properties, draw_geometry_properties, draw_shader, draw_light_properties
from Sollumz.yft.ui import draw_fragment_properties, draw_archetype_properties, draw_lod_properties, draw_child_properties

SOLLUMZ_UI_NAMES = {
    BoundType.BOX: 'Bound Box',
    BoundType.SPHERE: 'Bound Sphere',
    BoundType.CAPSULE: 'Bound Capsule',
    BoundType.CYLINDER: 'Bound Cylinder',
    BoundType.DISC: 'Bound Disc',
    BoundType.CLOTH: 'Bound Cloth',
    BoundType.GEOMETRY: 'Bound Geometry',
    BoundType.GEOMETRYBVH: 'GeometryBVH',
    BoundType.COMPOSITE: 'Composite',

    PolygonType.BOX: 'Bound Poly Box',
    PolygonType.SPHERE: 'Bound Poly Sphere',
    PolygonType.CAPSULE: 'Bound Poly Capsule',
    PolygonType.CYLINDER: 'Bound Poly Cylinder',
    PolygonType.TRIANGLE: 'Bound Poly Mesh',
}


class SOLLUMZ_PT_TOOL_PANEL(bpy.types.Panel):
    bl_label = "General Tools"
    bl_idname = "SOLLUMZ_PT_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_order = 0

    def draw(self, context):
        layout = self.layout
        layout.label(text="View")
        layout.prop(context.scene, "hide_collision")
        layout.prop(context.scene, "hide_high_lods")
        layout.prop(context.scene, "hide_medium_lods")
        layout.prop(context.scene, "hide_low_lods")
        layout.prop(context.scene, "hide_very_low_lods")


class SOLLUMZ_PT_VERTEX_TOOL_PANELL(bpy.types.Panel):
    bl_label = "Vertex Painter"
    bl_idname = "SOLLUMZ_PT_VERTEX_TOOL_PANELL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.prop(context.scene, "vert_paint_color")
        row.operator("sollumz.paint_vertices")


class SOLLUMZ_PT_YMAP_TOOL_PANEL(bpy.types.Panel):
    bl_label = "Ymap Tools"
    bl_idname = "SOLLUMZ_PT_YMAP_TOOL_PANEL"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_TOOL_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        row = layout.row()
        row.operator("sollumz.importymap")
        row.operator("sollumz.exportymap")


class SOLLUMZ_PT_ENTITY_PANEL(bpy.types.Panel):
    bl_label = "Entity"
    bl_idname = 'SOLLUMZ_PT_ENTITY_PANEL'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_options = {'DEFAULT_CLOSED'}
    bl_parent_id = SOLLUMZ_PT_YMAP_TOOL_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        aobj = context.active_object
        if(aobj == None or aobj.sollum_type != DrawableType.DRAWABLE):
            # have to put this outside of text = or it wont work?
            layout.label(
                text="Please select a valid object.")
            return
        layout.label(text="Entity Fields")
        #box.prop(aobj.ymap_properties, "archetype_name")
        layout.prop(aobj, "name", text="Archetype Name")
        #box.prop(aobj.ymap_properties, "position")
        row = layout.row()
        row.prop(aobj, "location", text="Position")
        #box.prop(aobj.ymap_properties, "rotation")
        row = layout.row()
        row.prop(aobj, "rotation_euler", text="Rotation")
        #box.prop(aobj.ymap_properties, "scale_xy")
        #box.prop(aobj.ymap_properties, "scale_z")
        row = layout.row()
        row.prop(aobj, "scale", text="ScaleXYZ")
        row = layout.row()
        row.prop(aobj.entity_properties, "flags")
        row.prop(aobj.entity_properties, "guid")
        row = layout.row()
        row.prop(aobj.entity_properties, "parent_index")
        row = layout.row()
        row.prop(aobj.entity_properties, "lod_dist")
        row.prop(aobj.entity_properties, "child_lod_dist")
        row.prop(aobj.entity_properties, "num_children")
        row = layout.row()
        row.prop(aobj.entity_properties, "ambient_occlusion_multiplier")
        row.prop(aobj.entity_properties, "artificial_ambient_occlusion")
        row.prop(aobj.entity_properties, "tint_value")
        row = layout.row()
        row.prop(aobj.entity_properties, "lod_level")
        row.prop(aobj.entity_properties, "priority_level")


class SOLLUMZ_PT_MAT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAT_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'material'
    bl_options = {'DEFAULT_CLOSED'}

    def draw(self, context):
        layout = self.layout
        # layout.use_property_split = True
        aobj = context.active_object
        if(context.active_object == None):
            return

        mat = context.active_object.active_material

        if(mat == None):
            return

        if mat.sollum_type == MaterialType.SHADER:
            draw_shader(layout, mat)
        elif mat.sollum_type == MaterialType.COLLISION and is_sollum_type(aobj, PolygonType):
            draw_collision_material_properties(layout, mat)


class SOLLUMZ_PT_OBJECT_PANEL(bpy.types.Panel):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_PT_MAIN_PANEL"
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'object'
    bl_options = {'DEFAULT_CLOSED'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.sollum_type != DrawableType.NONE

    def draw_drawable_model_properties(self, context, layout, obj):
        layout.prop(obj.drawable_model_properties, "render_mask")
        layout.prop(obj.drawable_model_properties, "flags")
        layout.prop(obj.drawable_model_properties, "sollum_lod")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True

        obj = context.active_object

        row = layout.row()
        row.enabled = False
        row.prop(obj, "sollum_type")

        if obj.sollum_type == DrawableType.DRAWABLE:
            draw_drawable_properties(layout, obj)
        elif obj.sollum_type == DrawableType.GEOMETRY:
            draw_geometry_properties(layout, obj)
        elif(obj.sollum_type == DrawableType.DRAWABLE_MODEL):
            self.draw_drawable_model_properties(context, layout, obj)
        elif(obj.sollum_type == FragmentType.FRAGMENT):
            draw_fragment_properties(layout, obj)
        elif(obj.sollum_type == FragmentType.LOD):
            draw_lod_properties(layout, obj)
        elif(obj.sollum_type == FragmentType.ARCHETYPE):
            draw_archetype_properties(layout, obj)
        elif(obj.sollum_type == FragmentType.CHILD):
            draw_child_properties(layout, obj)
        elif(obj.sollum_type == DrawableType.LIGHT):
            draw_light_properties(layout, obj)
        elif is_sollum_type(obj, BoundType):
            draw_bound_properties(layout, obj)


class SOLLUMZ_MT_sollumz(bpy.types.Menu):
    bl_label = "Sollumz"
    bl_idname = "SOLLUMZ_MT_sollumz"

    def draw(self, context):
        layout = self.layout


def DrawSollumzMenu(self, context):
    self.layout.separator()
    self.layout.menu(SOLLUMZ_MT_sollumz.bl_idname, icon="BLENDER")


def register():
    bpy.types.VIEW3D_MT_add.append(DrawSollumzMenu)


def unregister():
    bpy.types.VIEW3D_MT_add.remove(DrawSollumzMenu)
