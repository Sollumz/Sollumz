import bpy
from Sollumz.resources.bound import BoundType, PolygonType
from Sollumz.sollumz_ui import SOLLUMZ_UI_NAMES
from .meshhelper import * 
from .sollumz_shaders import create_collision_material_from_index

def create_empty(sollum_type):
    empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
    empty.empty_display_size = 0
    empty.sollum_type = sollum_type
    bpy.context.collection.objects.link(empty)
    bpy.context.view_layer.objects.active = bpy.data.objects[empty.name]

    return empty

def create_mesh(sollum_type):
    name = SOLLUMZ_UI_NAMES[sollum_type]
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    obj.sollum_type = sollum_type
    bpy.context.collection.objects.link(obj)

    return obj


def aobj_is_composite(self, sollum_type):
    aobj = bpy.context.active_object
    if not (aobj and aobj.sollum_type == BoundType.COMPOSITE):
        self.report({'INFO'}, f"Please select a {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]} to add a {SOLLUMZ_UI_NAMES[sollum_type]} to.")
        return False
    return True

class SOLLUMZ_OT_create_bound_composite(bpy.types.Operator):
    """Create a sollumz bound composite"""
    bl_idname = "sollumz.createboundcomposite"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]}"

    def execute(self, context):
        
        create_empty(BoundType.COMPOSITE)

        return {'FINISHED'}


class SOLLUMZ_OT_create_geometry_bound(bpy.types.Operator):
    """Create a sollumz geometry bound"""
    bl_idname = "sollumz.creategeometrybound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]}"

    def execute(self, context):
        if not aobj_is_composite(self, BoundType.GEOMETRY):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = create_empty(BoundType.GEOMETRY)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_geometrybvh_bound(bpy.types.Operator):
    """Create a sollumz geometry bound bvh"""
    bl_idname = "sollumz.creategeometryboundbvh"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}"

    def execute(self, context):
        if not aobj_is_composite(self, BoundType.GEOMETRYBVH):
            return {'CANCELLED'}
        
        aobj = bpy.context.active_object
        gobj = create_empty(BoundType.GEOMETRYBVH) 
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_box_bound(bpy.types.Operator):
    """Create a sollumz box bound"""
    bl_idname = "sollumz.createboxbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.BOX]}"

    def execute(self, context):
        if not aobj_is_composite(self, BoundType.BOX):
            return {'CANCELLED'}
        
        aobj = bpy.context.active_object
        gobj = create_mesh(BoundType.BOX)
        create_box(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_sphere_bound(bpy.types.Operator):
    """Create a sollumz sphere bound"""
    bl_idname = "sollumz.createspherebound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.SPHERE]}"

    def execute(self, context):
        if not aobj_is_composite(self, BoundType.SPHERE):
            return {'CANCELLED'}
        
        aobj = bpy.context.active_object
        gobj = create_mesh(BoundType.SPHERE)
        create_sphere(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]
            

        return {'FINISHED'}


class SOLLUMZ_OT_create_capsule_bound(bpy.types.Operator):
    """Create a sollumz capsule bound"""
    bl_idname = "sollumz.createcapsulebound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CAPSULE]}"

    def execute(self, context):
        if not aobj_is_composite(self, BoundType.CAPSULE):
            return {'CANCELLED'}
        
        aobj = bpy.context.active_object
        gobj = create_mesh(BoundType.CAPSULE)
        create_capsule(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_cylinder_bound(bpy.types.Operator):
    """Create a sollumz cylinder bound"""
    bl_idname = "sollumz.createcylinderbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CYLINDER]}"

    def execute(self, context):
        if not aobj_is_composite(self, BoundType.CYLINDER):
            return {'CANCELLED'}
        
        aobj = bpy.context.active_object
        gobj = create_mesh(BoundType.CYLINDER)
        create_cylinder(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_disc_bound(bpy.types.Operator):
    """Create a sollumz disc bound"""
    bl_idname = "sollumz.creatediscbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.DISC]}"

    def execute(self, context):
        if not aobj_is_composite(self, BoundType.DISC):
            return {'CANCELLED'}
        
        aobj = bpy.context.active_object
        gobj = create_mesh(BoundType.DISC)
        create_disc(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_cloth_bound(bpy.types.Operator):
    """Create a sollumz cloth bound"""
    bl_idname = "sollumz.createclothbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CLOTH]}"

    def execute(self, context):
        if not aobj_is_composite(self, BoundType.CLOTH):
            return {'CANCELLED'}
        
        aobj = bpy.context.active_object
        gobj = create_empty(BoundType.CLOTH)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_polygon_bound(bpy.types.Operator):
    """Create a sollumz polygon bound"""
    bl_idname = "sollumz.createpolygonbound"
    bl_label = "Create Polygon Bound"

    def execute(self, context):
        aobj = bpy.context.active_object
        type = context.scene.poly_bound_type

        print(aobj.sollum_type)
        if not (aobj and (aobj.sollum_type == BoundType.GEOMETRY or aobj.sollum_type == BoundType.GEOMETRYBVH)):
            self.report({'INFO'}, f"Please select a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} to add a {SOLLUMZ_UI_NAMES[type]} to.")
            return {'CANCELLED'}
        
        pobj = create_mesh(type)

        if type == PolygonType.BOX:
            create_box(pobj.data)
        elif type == PolygonType.SPHERE:
            create_sphere(pobj.data)
        elif type == PolygonType.CAPSULE:
            create_capsule(pobj.data)
        elif type == PolygonType.CYLINDER:
            create_cylinder(pobj.data)

        pobj.parent = aobj
        #bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name] if you enable this you wont be able to stay selecting the composite obj... 

        return {'FINISHED'}


class SOLLUMZ_OT_create_collision_material(bpy.types.Operator):
    """Create a sollumz collision material"""
    bl_idname = "sollumz.createcollisionmaterial"
    bl_label = "Create Collision Material"

    index : bpy.props.IntProperty(name = "Index")

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            return {'CANCELLED'}
        
        # Check if acitve object is of PolygonType
        if aobj.sollum_type in PolygonType._value2member_map_:
            mat = create_collision_material_from_index(self.index)
            aobj.data.materials.append(mat)
        
        return {'FINISHED'}