from genericpath import exists
import bpy
from Sollumz.sollumz_properties import BoundType, PolygonType, SOLLUMZ_UI_NAMES, is_sollum_type
from Sollumz.meshhelper import *
from .collision_materials import create_collision_material_from_index, create_collision_material_from_type
from .properties import BoundFlags, load_flag_presets, flag_presets
from Sollumz.resources.flag_preset import FlagPreset
import os, traceback


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
    obj.data.materials.append(create_collision_material_from_index(0))
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
        create_capsule(gobj)
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

        if not (aobj and (aobj.sollum_type == BoundType.GEOMETRY or aobj.sollum_type == BoundType.GEOMETRYBVH)):
            self.report({'INFO'}, f"Please select a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} to add a {SOLLUMZ_UI_NAMES[type]} to.")
            return {'CANCELLED'}
        
        pobj = create_mesh(type)

        if type == PolygonType.BOX:
            create_box(pobj.data)
        elif type == PolygonType.SPHERE:
            create_sphere(pobj.data)
        elif type == PolygonType.CAPSULE:
            create_capsule(pobj)
        elif type == PolygonType.CYLINDER:
            create_cylinder(pobj.data)

        pobj.parent = aobj
        #bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name] if you enable this you wont be able to stay selecting the composite obj... 

        return {'FINISHED'}


class SOLLUMZ_OT_create_collision_material(bpy.types.Operator):
    """Create a sollumz collision material"""
    bl_idname = "sollumz.createcollisionmaterial"
    bl_label = "Create Collision Material"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            return {'CANCELLED'}
        
        if is_sollum_type(aobj, PolygonType):
            mat = create_collision_material_from_index(context.scene.collision_material_index)
            aobj.data.materials.append(mat)
        
        return {'FINISHED'}


class SOLLUMZ_OT_delete_flag_preset(bpy.types.Operator):
    """Delete a flag preset"""
    bl_idname = "sollumz.delete_flag_preset"
    bl_label = "Delete Flag Preset"

    preset_blacklist = ['Default']

    def execute(self, context):
        index = context.scene.flag_preset_index
        load_flag_presets()

        try:
            preset = flag_presets.presets[index]
            if preset.name in self.preset_blacklist:
                self.report({'INFO'}, f"Cannot delete a default preset!")
                return {'CANCELLED'}

            filepath = os.path.abspath('./ybn/flag_presets.xml')
            flag_presets.presets.remove(preset)

            try:
                flag_presets.write_xml(filepath)
                load_flag_presets()

                return {'FINISHED'}
            except:
                self.report({'ERROR'}, traceback.format_exc())
                return {'CANCELLED'}

        except IndexError:
            self.report({'ERROR'}, f"Flag preset does not exist! Ensure the preset file is present in the 'Sollumz/ybn/flag_presets' directory.")
            return {'CANCELLED'}


class SOLLUMZ_OT_save_flag_preset(bpy.types.Operator):
    """Save a flag preset"""
    bl_idname = "sollumz.save_flag_preset"
    bl_label = "Save Flag Preset"

    def execute(self, context):
        obj = context.active_object
        load_flag_presets()

        if not obj:
            self.report({'INFO'}, 'No object selected!')
            return {'CANCELLED'}

        if obj.sollum_type and not (obj.sollum_type == BoundType.GEOMETRY or obj.sollum_type == BoundType.GEOMETRYBVH):
            self.report({'INFO'}, f'Selected object must be either a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}!')
            return {'CANCELLED'}
        
        name = context.scene.new_flag_preset_name
        if len(name) < 1:
            self.report({'INFO'}, f'Please specify a name for the new flag preset.')
            return {'CANCELLED'}

        flag_preset = FlagPreset()
        flag_preset.name = name

        for prop in dir(obj.composite_flags1):
            value = getattr(obj.composite_flags1, prop)
            if value == True:
                flag_preset.flags1.append(prop) 

        for prop in dir(obj.composite_flags2):
            value = getattr(obj.composite_flags2, prop)
            if value == True:
                flag_preset.flags2.append(prop) 

        filepath = os.path.abspath('./ybn/flag_presets.xml')
        
        for preset in flag_presets.presets:
            if preset.name == name:
                self.report({'INFO'}, f'A preset with that name already exists! If you wish to overwrite this preset, delete the original.')
                return {'CANCELLED'}

        try: 
            flag_presets.presets.append(flag_preset)
            flag_presets.write_xml(filepath)
            load_flag_presets()

            return {'FINISHED'}
        except:
            self.report({'ERROR'}, traceback.format_exc())
            return {'CANCELLED'}
        


class SOLLUMZ_OT_load_flag_preset(bpy.types.Operator):
    """Load a flag preset to the selected Geometry bounds"""
    bl_idname = "sollumz.load_flag_preset"
    bl_label = "Apply Flags Preset"
    bl_context = 'object'
    bl_options = {'REGISTER', 'UNDO'}


    def execute(self, context):
        index = context.scene.flag_preset_index
        selected = context.selected_objects
        if len(selected) < 1:
            self.report({'INFO'}, 'No objects selected!')
            return {'CANCELLED'}
        
        load_flag_presets()
        
        for obj in selected:
            if obj.sollum_type and not (obj.sollum_type == BoundType.GEOMETRY or obj.sollum_type == BoundType.GEOMETRYBVH):
                self.report({'INFO'}, f'Selected objects must be either a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}!')
                return {'CANCELLED'}
            
            try:
                preset = flag_presets.presets[index]

                for flag_name in BoundFlags.__annotations__.keys():
                    if flag_name in preset.flags1:
                        obj.composite_flags1[flag_name] = True
                    else:
                        obj.composite_flags1[flag_name] = False

                    if flag_name in preset.flags2:
                        obj.composite_flags2[flag_name] = True
                    else:
                        obj.composite_flags2[flag_name] = False
                
                # Hacky way to force the UI to redraw. For some reason setting custom properties will not cause the object properties panel to redraw, so we have to do this.
                obj.location = obj.location

            except IndexError:
                self.report({'ERROR'}, f"Flag preset does not exist! Ensure the preset file is present in the 'Sollumz/ybn/flag_presets' directory.")
                return {'CANCELLED'}
        
        return {'FINISHED'}


class SOLLUMZ_OT_clear_col_flags(bpy.types.Operator):
    """Load commonly used collision flags"""
    bl_idname = "sollumz.clear_col_flags"
    bl_label = "Clear Collision Flags"

    def execute(self, context):
        
        aobj = bpy.context.active_object
        if(aobj == None):
            return {'CANCELLED'}
        
        if is_sollum_type(aobj, BoundType):
            for flag_name in BoundFlags.__annotations__.keys():
                aobj.composite_flags1[flag_name] = False
                aobj.composite_flags2[flag_name] = False
        
        return {'FINISHED'}


class SOLLUMZ_OT_mesh_to_polygon_bound(bpy.types.Operator):
    """Convert selected objects to a poly bound"""
    bl_idname = "sollumz.meshtopolygonbound"
    bl_label = "Convert Object to Poly"
    bl_options = {'UNDO'}

    def execute(self, context):
        aobj = context.active_object
        type = context.scene.convert_poly_bound_type
        parent = context.scene.convert_poly_parent


        if not aobj or (aobj and not aobj.type == 'MESH'):
            self.report({'WARNING'}, 'No object with mesh data selected!')
            return {'CANCELLED'}
        elif aobj and not context.active_object.mode == 'EDIT':
            self.report({'WARNING'}, 'Operator can only be ran in edit mode!')
            return {'CANCELLED'}
        
        if not parent:
            self.report({'WARNING'}, 'Must specify a parent object!')
            return {'CANCELLED'}
        elif parent.sollum_type != BoundType.GEOMETRYBVH and parent.sollum_type != BoundType.GEOMETRY:
            self.report({'WARNING'}, f'Parent must be a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]}!')
            return {'CANCELLED'}

        # We need to switch from Edit mode to Object mode so the vertex selection gets updated (disgusting!)
        bpy.ops.object.mode_set(mode='OBJECT')
        selected_verts = [Vector((v.co.x, v.co.y, v.co.z)) for v in aobj.data.vertices if v.select]
        bpy.ops.object.mode_set(mode='EDIT')


        if len(selected_verts) < 1:
            self.report({'INFO'}, 'No vertices selected.')
            return {'CANCELLED'}

        pobj = create_mesh(type)

        np_array = np.array(selected_verts)
        bbmin_local = Vector(np_array.min(axis=0))
        bbmax_local = Vector(np_array.max(axis=0))
        bbmin = aobj.matrix_world @ bbmin_local
        bbmax = aobj.matrix_world @ bbmax_local

        radius = ((aobj.matrix_local @ bbmax).x - (aobj.matrix_local @ bbmin).x) / 2
        height = get_distance_of_vectors(bbmin, bbmax)
        center = (bbmin + bbmax) / 2
        pobj.location = center

        if type == PolygonType.BOX:
            scale = aobj.matrix_world.to_scale()
            min = (bbmin_local) * scale
            max = (bbmax_local) * scale
            center = (min + max) / 2
            create_box_from_extents(pobj.data, min - center, max - center)
            # pobj.location = Vector()
        elif type == PolygonType.SPHERE:
            create_sphere(pobj.data, height / 2)
        elif type == PolygonType.CAPSULE or type == PolygonType.CYLINDER:
            if type == PolygonType.CAPSULE:
                # height = height - (radius * 2)
                create_capsule(pobj, radius, height)
            elif type == PolygonType.CYLINDER:
                create_cylinder(pobj.data, radius, height, False)
        
        pobj.rotation_euler = aobj.rotation_euler
        
        pobj.parent = parent

        return {'FINISHED'}


class SOLLUMZ_OT_convert_mesh_to_collision(bpy.types.Operator):
    """Setup a gta bound via a mesh object"""
    bl_idname = "sollumz.quickconvertmeshtocollision"
    bl_label = "Convert Mesh To Collision"
    bl_options = {'UNDO'}

    def execute(self, context):
        selected = context.selected_objects
        if len(selected) < 1:
            self.report({'INFO'}, 'No objects selected for conversion!')
            return {'CANCELLED'}

        parent = None
        if not bpy.context.scene.multiple_ybns:
            parent = create_empty(BoundType.COMPOSITE)
        
        for obj in selected:
            #set parents
            dobj = parent or create_empty(BoundType.COMPOSITE)
            dmobj = create_empty(BoundType.GEOMETRYBVH)
            dmobj.parent = dobj
            obj.parent = dmobj

            name = obj.name
            obj.name = name + "_mesh"

            if bpy.context.scene.convert_ybn_use_mesh_names:
                dobj.name = name

                
            #set properties
            obj.sollum_type = PolygonType.TRIANGLE

            #add object to collection
            new_obj = obj.copy()
            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.context.collection.objects.link(new_obj)

        return {'FINISHED'}