import bpy
from Sollumz.resources.bound import BoundType, PolygonType
from .meshhelper import * 

class SOLLUMZ_OT_create_composite_bound(bpy.types.Operator):
    """Create a sollumz composite bound"""
    bl_idname = "sollumz.createcompositebound"
    bl_label = "Create Composite"

    def execute(self, context):
        
        mesh = bpy.data.meshes.new("none")
        cobj = bpy.data.objects.new("Composite", mesh)
        cobj.sollum_type = BoundType.COMPOSITE.value
        bpy.context.collection.objects.link(cobj)

        bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_geometrybvh_bound(bpy.types.Operator):
    """Create a sollumz geometry bvh bound"""
    bl_idname = "sollumz.creategeometrybvhbound"
    bl_label = "Create Geometry BVH"

    def execute(self, context):
        
        mesh = bpy.data.meshes.new("none")
        gobj = bpy.data.objects.new("GeometryBVH", mesh)
        gobj.sollum_type = BoundType.GEOMETRYBVH.value

        aobj = bpy.context.active_object
        if(aobj != None):
            if("composite" in aobj.sollum_type):   
                gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_poly_bound(bpy.types.Operator):
    """Create a sollumz poly bound"""
    bl_idname = "sollumz.createpolybound"
    bl_label = "Create Poly"

    def execute(self, context):

        type = context.scene.poly_bound_type
        
        mesh = bpy.data.meshes.new("mesh")
        pobj = bpy.data.objects.new("Poly", mesh)

        if(type == PolygonType.BOX.value):
            pobj.name = "box Poly"
            create_box(pobj.data)
            pobj.sollum_type = PolygonType.BOX.value
        elif(type == PolygonType.SPHERE.value):
            pobj.name = "Sphere Poly"
            create_sphere(pobj.data)
            pobj.sollum_type = PolygonType.SPHERE.value
        elif(type == PolygonType.CAPSULE.value):
            pobj.name = "Capsule Poly"
            create_capsule(pobj.data)
            pobj.sollum_type = PolygonType.CAPSULE.value
        elif(type == PolygonType.CYLINDER.value):
            pobj.name = "Cylinder Poly"
            create_cylinder(pobj.data)
            pobj.sollum_type = PolygonType.CYLINDER.value
        elif(type == PolygonType.DISC.value):
            pobj.name = "Disc Poly"
            create_disc(pobj.data)
            pobj.sollum_type = PolygonType.DISC.value
        elif(type == PolygonType.CLOTH.value):
            pobj.name = "Cloth Poly"
            pobj.sollum_type = PolygonType.DISC.value
        elif(type == PolygonType.TRIANGLE.value):
            pobj.name = "Triangle Poly Object"
            pobj.sollum_type = PolygonType.TRIANGLE.value


        aobj = bpy.context.active_object
        if(aobj != None):
            if("geometry" in aobj.sollum_type):   
                pobj.parent = aobj
        bpy.context.collection.objects.link(pobj)
        #bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name] if you enable this you wont be able to stay selecting the composite obj... 

        return {'FINISHED'}