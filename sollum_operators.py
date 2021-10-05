import bpy
from Sollumz.resources.bound import BoundType, PolygonType
from Sollumz.sollumz_ui import SOLLUMZ_UI_NAMES
from Sollumz.ybnimport import composite_to_obj, geometry_to_obj
from Sollumz.resources.bound import BoundsComposite, BoundGeometryBVH
from .meshhelper import * 

class SOLLUMZ_OT_create_composite_bound(bpy.types.Operator):
    """Create a sollumz composite bound"""
    bl_idname = "sollumz.createcompositebound"
    bl_label = "Create Composite"

    def execute(self, context):
        
        cobj = composite_to_obj(BoundsComposite(), SOLLUMZ_UI_NAMES[BoundType.COMPOSITE])

        bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_geometrybvh_bound(bpy.types.Operator):
    """Create a sollumz geometry bvh bound"""
    bl_idname = "sollumz.creategeometrybvhbound"
    bl_label = "Create Geometry BVH"

    def execute(self, context):
        
        gobj = geometry_to_obj(BoundGeometryBVH(), BoundType.GEOMETRYBVH)

        aobj = bpy.context.active_object
        if(aobj != None):
            if(aobj.sollum_type == BoundType.COMPOSITE):   
                gobj.parent = aobj

        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_poly_bound(bpy.types.Operator):
    """Create a sollumz poly bound"""
    bl_idname = "sollumz.createpolybound"
    bl_label = "Create Poly"

    def execute(self, context):

        type = context.scene.poly_bound_type
        
        name = SOLLUMZ_UI_NAMES[type]
        mesh = bpy.data.meshes.new(name)
        pobj = bpy.data.objects.new(name, mesh)

        if(type == PolygonType.BOX):
            create_box(pobj.data)
            pobj.sollum_type = PolygonType.BOX
        elif(type == PolygonType.SPHERE):
            create_sphere(pobj.data)
            pobj.sollum_type = PolygonType.SPHERE
        elif(type == PolygonType.CAPSULE):
            create_capsule(pobj.data)
            pobj.sollum_type = PolygonType.CAPSULE
        elif(type == PolygonType.CYLINDER):
            create_cylinder(pobj.data)
            pobj.sollum_type = PolygonType.CYLINDER
        elif(type == PolygonType.TRIANGLE):
            pobj.sollum_type = PolygonType.TRIANGLE


        aobj = bpy.context.active_object
        if(aobj != None):
            if("geometry" in aobj.sollum_type):   
                pobj.parent = aobj
        bpy.context.collection.objects.link(pobj)
        #bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name] if you enable this you wont be able to stay selecting the composite obj... 

        return {'FINISHED'}