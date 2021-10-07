import bpy
from Sollumz.resources.bound import BoundType, PolygonType
from .meshhelper import * 
from .sollumz_shaders import create_collision_material_from_type

class SOLLUMZ_OT_create_bound_composite(bpy.types.Operator):
    """Create a sollumz bound composite"""
    bl_idname = "sollumz.createboundcomposite"
    bl_label = "Create Bound Composite"

    def execute(self, context):
        
        mesh = bpy.data.meshes.new("none")
        cobj = bpy.data.objects.new("Composite", mesh)
        cobj.sollum_type = BoundType.COMPOSITE.value
        bpy.context.collection.objects.link(cobj)

        bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_geometry_bound(bpy.types.Operator):
    """Create a sollumz geometry bound"""
    bl_idname = "sollumz.creategeometrybound"
    bl_label = "Create Geometry Bound"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Composite to add a Geometry Bound to.")
            return {'CANCELLED'}
        if("composite" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Composite to add a Geometry Bound to.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("none")
        gobj = bpy.data.objects.new("GeometryBound", mesh)
        gobj.sollum_type = BoundType.GEOMETRYBVH.value
            
        gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_geometrybvh_bound(bpy.types.Operator):
    """Create a sollumz geometry bound bvh"""
    bl_idname = "sollumz.creategeometryboundbvh"
    bl_label = "Create Geometry Bound BVH"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Composite to add a GeometryBoundBVH to.")
            return {'CANCELLED'}
        if("composite" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Composite to add a GeometryBoundBVH to.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("none")
        gobj = bpy.data.objects.new("GeometryBoundBVH", mesh)
        gobj.sollum_type = BoundType.GEOMETRYBVH.value
            
        gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_box_bound(bpy.types.Operator):
    """Create a sollumz box bound"""
    bl_idname = "sollumz.createboxbound"
    bl_label = "Create Box Bound"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Composite to add a Bound Box to.")
            return {'CANCELLED'}
        if("composite" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Composite to add a Box Bound to.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("box")
        gobj = bpy.data.objects.new("BoxBound", mesh)
        create_box(gobj.data)
        gobj.sollum_type = BoundType.BOX.value
            
        gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_sphere_bound(bpy.types.Operator):
    """Create a sollumz sphere bound"""
    bl_idname = "sollumz.createspherebound"
    bl_label = "Create Sphere Bound"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Composite to add a Sphere Bound to.")
            return {'CANCELLED'}
        if("composite" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Composite to add a Sphere Bound to.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("sphere")
        gobj = bpy.data.objects.new("SphereBound", mesh)
        create_sphere(gobj.data)
        gobj.sollum_type = BoundType.BOX.value
            
        gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_capsule_bound(bpy.types.Operator):
    """Create a sollumz capsule bound"""
    bl_idname = "sollumz.createcapsulebound"
    bl_label = "Create Capsule Bound"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Composite to add a Capsule Bound to.")
            return {'CANCELLED'}
        if("composite" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Composite to add a Capsule Bound to.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("capsule")
        gobj = bpy.data.objects.new("CapsuleBound", mesh)
        create_capsule(gobj.data)
        gobj.sollum_type = BoundType.BOX.value
            
        gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_cylinder_bound(bpy.types.Operator):
    """Create a sollumz cylinder bound"""
    bl_idname = "sollumz.createcylinderbound"
    bl_label = "Create Cylinder Bound"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Composite to add a Cylinder Bound to.")
            return {'CANCELLED'}
        if("composite" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Composite to add a Cylinder Bound to.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("cylinder")
        gobj = bpy.data.objects.new("CylinderBound", mesh)
        create_cylinder(gobj.data)
        gobj.sollum_type = BoundType.BOX.value
            
        gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_disc_bound(bpy.types.Operator):
    """Create a sollumz disc bound"""
    bl_idname = "sollumz.creatediscbound"
    bl_label = "Create Disc Bound"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Composite to add a Disc Bound to.")
            return {'CANCELLED'}
        if("composite" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Composite to add a Disc Bound to.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("disc")
        gobj = bpy.data.objects.new("DiscBound", mesh)
        create_disc(gobj.data)
        gobj.sollum_type = BoundType.BOX.value
            
        gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_cloth_bound(bpy.types.Operator):
    """Create a sollumz cloth bound"""
    bl_idname = "sollumz.createclothbound"
    bl_label = "Create Cloth Bound"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Composite to add a Cloth Bound to.")
            return {'CANCELLED'}
        if("composite" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Composite to add a Cloth Bound to.")
            return {'CANCELLED'}

        mesh = bpy.data.meshes.new("cloth")
        gobj = bpy.data.objects.new("ClothBound", mesh)
        #create_cloth(gobj.data)
        gobj.sollum_type = BoundType.BOX.value
            
        gobj.parent = aobj
        bpy.context.collection.objects.link(gobj)
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}

class SOLLUMZ_OT_create_polygon_bound(bpy.types.Operator):
    """Create a sollumz polygon bound"""
    bl_idname = "sollumz.createpolygonbound"
    bl_label = "Create Polygon Bound"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            self.report({'INFO'}, "Please select a Bound Geometry to add a Polygon Bound to.")
            return {'CANCELLED'}
        if("geometry" not in aobj.sollum_type):
            self.report({'INFO'}, "Please select a Bound Geometry to add a Polygon Bound to.")
            return {'CANCELLED'}

        type = context.scene.poly_bound_type
        
        mesh = bpy.data.meshes.new("mesh")
        pobj = bpy.data.objects.new("Polygon", mesh)

        if(type == PolygonType.BOX.value):
            pobj.name = "Box Polygon"
            create_box(pobj.data)
            pobj.sollum_type = PolygonType.BOX.value
        elif(type == PolygonType.SPHERE.value):
            pobj.name = "Sphere Polygon"
            create_sphere(pobj.data)
            pobj.sollum_type = PolygonType.SPHERE.value
        elif(type == PolygonType.CAPSULE.value):
            pobj.name = "Capsule Polygon"
            create_capsule(pobj.data)
            pobj.sollum_type = PolygonType.CAPSULE.value
        elif(type == PolygonType.CYLINDER.value):
            pobj.name = "Cylinder Polygon"
            create_cylinder(pobj.data)
            pobj.sollum_type = PolygonType.CYLINDER.value
        elif(type == PolygonType.TRIANGLE.value):
            pobj.name = "Triangle Polygon Object"
            pobj.sollum_type = PolygonType.TRIANGLE.value

        pobj.parent = aobj
        bpy.context.collection.objects.link(pobj)
        #bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name] if you enable this you wont be able to stay selecting the composite obj... 

        return {'FINISHED'}

class SOLLUMZ_OT_create_collision_material(bpy.types.Operator):
    """Create a sollumz collision material"""
    bl_idname = "sollumz.createcollisionmaterial"
    bl_label = "Create Collision Material"

    material_type : bpy.props.StringProperty(default = "sollumz_default")

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            return {'CANCELLED'}
        
        if("poly" in aobj.sollum_type):
            parent = aobj.parent
            material_type = ""
            split = self.material_type.replace("sollumz_", "").upper().split('_')
            for w in split:
                material_type += w + "_"
            material_type = material_type[:-1]
            mat = create_collision_material_from_type(material_type)
            aobj.data.materials.append(mat)
            parent.data.materials.append(mat)
        
        return {'FINISHED'}

class SOLLUMZ_OT_BONE_FLAGS_NewItem(bpy.types.Operator): 
    bl_idname = "sollumz.bone_flags_new_item" 
    bl_label = "Add a new item"
    def execute(self, context): 
        bone = context.active_pose_bone.bone
        bone.bone_properties.flags.add() 
        return {'FINISHED'}

class SOLLUMZ_OT_BONE_FLAGS_DeleteItem(bpy.types.Operator): 
    bl_idname = "sollumz.bone_flags_delete_item" 
    bl_label = "Deletes an item" 
    @classmethod 
    def poll(cls, context): 
        return context.active_pose_bone.bone.bone_properties.flags

    def execute(self, context): 
        bone = context.active_pose_bone.bone

        list = bone.bone_properties.flags
        index = bone.bone_properties.ul_index
        list.remove(index) 
        bone.bone_properties.ul_index = min(max(0, index - 1), len(list) - 1) 
        return {'FINISHED'}