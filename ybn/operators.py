import numpy as np
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty
from mathutils import Vector, Matrix
import time
import random
import math
import bmesh
from genericpath import exists
import bpy
from Sollumz.sollumz_properties import BoundType, PolygonType, SOLLUMZ_UI_NAMES, is_sollum_type
from Sollumz.meshhelper import *
from .collision_materials import create_collision_material_from_index, create_collision_material_from_type
from .properties import BoundFlags, load_flag_presets, flag_presets, get_flag_presets_path
from Sollumz.resources.flag_preset import FlagPreset
import os
import traceback
from Sollumz.tools.obb import get_obb, get_obb_dimensions, get_obb_extents


def handle_load_flag_presets(self):
    try:
        load_flag_presets()
    except FileNotFoundError:
        self.report({'ERROR'}, traceback.format_exc())


class BoundHelper:

    @staticmethod
    def create_bound(sollum_type=BoundType.COMPOSITE, with_mesh=False):

        if with_mesh:
            return BoundHelper.create_mesh(sollum_type)

        empty = bpy.data.objects.new(SOLLUMZ_UI_NAMES[sollum_type], None)
        empty.empty_display_size = 0
        empty.sollum_type = sollum_type
        bpy.context.collection.objects.link(empty)
        bpy.context.view_layer.objects.active = bpy.data.objects[empty.name]

        return empty

    @staticmethod
    def create_mesh(sollum_type):
        name = SOLLUMZ_UI_NAMES[sollum_type]
        mesh = bpy.data.meshes.new(name)
        obj = bpy.data.objects.new(name, mesh)
        obj.sollum_type = sollum_type
        obj.data.materials.append(create_collision_material_from_index(0))
        bpy.context.collection.objects.link(obj)

        return obj

    @staticmethod
    def convert_selected_to_bound(objs, use_name=False, multiple=False):
        selected = objs

        parent = None
        if not multiple:
            parent = BoundHelper.create_bound()

        for obj in selected:
            # set parents
            dobj = parent or BoundHelper.create_bound(BoundType.COMPOSITE)
            dmobj = BoundHelper.create_bound(BoundType.GEOMETRYBVH)
            dmobj.parent = dobj
            obj.parent = dmobj

            name = obj.name
            obj.name = name + "_mesh"

            if use_name:
                dobj.name = name

            # set properties
            obj.sollum_type = PolygonType.TRIANGLE

            # add object to collection
            new_obj = obj.copy()

            # Remove materials
            if new_obj.type == 'MESH':
                new_obj.data.materials.clear()

            bpy.data.objects.remove(obj, do_unlink=True)
            bpy.context.collection.objects.link(new_obj)

    # move to blender helper? or maybe make a sollumz heper? call it "is_sollum_type(sollum_type)"
    # this is where a SollumOperator class would come in handy I could see checking this in a
    # bunch of different operators so if we make one common one we could call this
    @staticmethod
    def aobj_is_composite(self, sollum_type):
        aobj = bpy.context.active_object
        if not (aobj and aobj.sollum_type == BoundType.COMPOSITE):
            self.report(
                {'INFO'}, f"Please select a {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]} to add a {SOLLUMZ_UI_NAMES[sollum_type]} to.")
            return False
        return True


class SOLLUMZ_OT_create_bound_composite(bpy.types.Operator):
    """Create a sollumz bound composite"""
    bl_idname = "sollumz.createboundcomposite"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        selected = context.selected_objects
        if len(selected) < 1:
            BoundHelper.create_bound()
        else:
            BoundHelper.convert_selected_to_bound(
                selected, context.scene.use_mesh_name, context.scene.create_seperate_objects)

        return {'FINISHED'}


class SOLLUMZ_OT_create_geometry_bound(bpy.types.Operator):
    """Create a sollumz geometry bound"""
    bl_idname = "sollumz.creategeometrybound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        if not BoundHelper.aobj_is_composite(self, BoundType.GEOMETRY):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = BoundHelper.create_bound(BoundType.GEOMETRY)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_geometrybvh_bound(bpy.types.Operator):
    """Create a sollumz geometry bound bvh"""
    bl_idname = "sollumz.creategeometryboundbvh"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        if not BoundHelper.aobj_is_composite(self, BoundType.GEOMETRYBVH):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = BoundHelper.create_bound(BoundType.GEOMETRYBVH)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_box_bound(bpy.types.Operator):
    """Create a sollumz box bound"""
    bl_idname = "sollumz.createboxbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.BOX]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        if not BoundHelper.aobj_is_composite(self, BoundType.BOX):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = BoundHelper.create_bound(BoundType.BOX, True)
        create_box(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_sphere_bound(bpy.types.Operator):
    """Create a sollumz sphere bound"""
    bl_idname = "sollumz.createspherebound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.SPHERE]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        if not BoundHelper.aobj_is_composite(self, BoundType.SPHERE):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = BoundHelper.create_bound(BoundType.SPHERE, True)
        create_sphere(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_capsule_bound(bpy.types.Operator):
    """Create a sollumz capsule bound"""
    bl_idname = "sollumz.createcapsulebound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CAPSULE]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        if not BoundHelper.aobj_is_composite(self, BoundType.CAPSULE):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = BoundHelper.create_bound(BoundType.CAPSULE, True)
        create_capsule(gobj)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_cylinder_bound(bpy.types.Operator):
    """Create a sollumz cylinder bound"""
    bl_idname = "sollumz.createcylinderbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CYLINDER]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        if not BoundHelper.aobj_is_composite(self, BoundType.CYLINDER):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = BoundHelper.create_bound(BoundType.CYLINDER, True)
        create_cylinder(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_disc_bound(bpy.types.Operator):
    """Create a sollumz disc bound"""
    bl_idname = "sollumz.creatediscbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.DISC]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        if not BoundHelper.aobj_is_composite(self, BoundType.DISC):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = BoundHelper.create_bound(BoundType.DISC, True)
        create_disc(gobj.data)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_cloth_bound(bpy.types.Operator):
    """Create a sollumz cloth bound"""
    bl_idname = "sollumz.createclothbound"
    bl_label = f"Create {SOLLUMZ_UI_NAMES[BoundType.CLOTH]}"
    bl_options = {"UNDO"}

    def execute(self, context):
        if not BoundHelper.aobj_is_composite(self, BoundType.CLOTH):
            return {'CANCELLED'}

        aobj = bpy.context.active_object
        gobj = BoundHelper.create_bound(BoundType.CLOTH, True)
        gobj.parent = aobj
        bpy.context.view_layer.objects.active = bpy.data.objects[gobj.name]

        return {'FINISHED'}


class SOLLUMZ_OT_create_polygon_bound(bpy.types.Operator):
    """Create a sollumz polygon bound"""
    bl_idname = "sollumz.createpolygonbound"
    bl_label = "Create Polygon Bound"
    bl_options = {"UNDO"}

    def create_poly(self, aobj, type):
        if not (aobj and (aobj.sollum_type == BoundType.GEOMETRY or aobj.sollum_type == BoundType.GEOMETRYBVH)):
            self.report(
                {'INFO'}, f"Please select a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} to add a {SOLLUMZ_UI_NAMES[type]} to.")
            return {'CANCELLED'}

        pobj = BoundHelper.create_bound(type, True)

        if type == PolygonType.BOX:
            create_box(pobj.data)
        elif type == PolygonType.SPHERE:
            create_sphere(pobj.data)
        elif type == PolygonType.CAPSULE:
            create_capsule(pobj)
        elif type == PolygonType.CYLINDER:
            create_cylinder(pobj.data)

        pobj.parent = aobj
        # bpy.context.view_layer.objects.active = bpy.data.objects[cobj.name] if you enable this you wont be able to stay selecting the composite obj...

    def create_poly_from_verts(self, context, type, parent):
        if not parent:
            self.report({'WARNING'}, 'Must specify a parent object!')
            return {'CANCELLED'}
        elif parent.sollum_type != BoundType.GEOMETRYBVH and parent.sollum_type != BoundType.GEOMETRY:
            self.report(
                {'WARNING'}, f'Parent must be a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]}!')
            return {'CANCELLED'}

        selected = context.selected_objects
        if len(selected) < 1:
            self.report({'INFO'}, 'No objects selected!')
            return {'CANCELLED'}
        verts = []
        for obj in selected:
            # We need to switch from Edit mode to Object mode so the vertex selection gets updated (disgusting!)
            bpy.ops.object.mode_set(mode='OBJECT')
            verts.extend([obj.matrix_world @ Vector((v.co.x, v.co.y, v.co.z))
                          for v in obj.data.vertices if v.select])
            bpy.ops.object.mode_set(mode='EDIT')
        pobj = BoundHelper.create_bound(type, True)

        if len(verts) < 1:
            self.report({'INFO'}, 'No vertices selected.')
            return {'CANCELLED'}
        print(len(verts))
        obb, axis, world_matrix = get_obb(verts)
        bbmin, bbmax = get_obb_extents(obb)

        center = world_matrix @ (bbmin + bbmax) / 2
        local_center = (bbmin + bbmax) / 2

        height, width = get_obb_dimensions(bbmin, bbmax)
        radius = width / 2

        if type == PolygonType.BOX:
            create_box_from_extents(
                pobj.data, bbmin - local_center, bbmax - local_center)
        elif type == PolygonType.SPHERE:
            create_sphere(pobj.data, height / 2)
        elif type == PolygonType.CAPSULE or type == PolygonType.CYLINDER:
            if type == PolygonType.CAPSULE:
                create_capsule(pobj, radius, height)
            elif type == PolygonType.CYLINDER:
                # rot_mat = world_matrix.decompose()[1].to_matrix()
                # rot_mat = Matrix.Rotation(radians(90), 4, axis)
                create_cylinder(pobj.data, radius, height,
                                None)
        print(axis, world_matrix.decompose()[1])
        pobj.matrix_world = world_matrix
        pobj.location = center

        pobj.parent = parent

    def execute(self, context):
        aobj = context.active_object
        type = context.scene.poly_bound_type
        parent = context.scene.poly_parent

        if aobj.mode == "EDIT":
            self.create_poly_from_verts(context, type, parent)
        else:
            self.create_poly(aobj, type)

        return {'FINISHED'}


class SOLLUMZ_OT_center_composite(bpy.types.Operator):
    """Center a bound composite with the rest of it's geometry. Note: Has no effect on export"""
    bl_idname = "sollumz.centercomposite"
    bl_label = "Center Composite"
    bl_options = {'UNDO'}

    def execute(self, context):
        aobj = context.active_object
        if not aobj:
            self.report(
                {'INFO'}, f'No {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]} selected.')
            return {'CANCELLED'}
        elif aobj.sollum_type != BoundType.COMPOSITE:
            self.report(
                {'INFO'}, f'{aobj.name} must be a {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]}!')
            return {'CANCELLED'}

        if context.mode != 'OBJECT':
            self.report({'INFO'}, f'Operator can only be ran in Object mode.')
            return {'CANCELLED'}

        center = get_bound_center(aobj)
        aobj.location = center
        for obj in aobj.children:
            obj.delta_location = -center

        return {'FINISHED'}


class SOLLUMZ_OT_create_collision_material(bpy.types.Operator):
    """Create a sollumz collision material"""
    bl_idname = "sollumz.createcollisionmaterial"
    bl_label = "Create Collision Material"
    bl_options = {"UNDO"}

    def execute(self, context):

        selected = context.selected_objects
        if len(selected) < 1:
            self.report({'INFO'}, 'No objects selected!')
            return {'CANCELLED'}

        for obj in selected:
            correct_type = False
            if is_sollum_type(obj, PolygonType) or is_sollum_type(obj, BoundType):
                if obj.sollum_type != BoundType.COMPOSITE and obj.sollum_type != BoundType.GEOMETRY and obj.sollum_type != BoundType.GEOMETRYBVH:
                    correct_type = True
                    mat = create_collision_material_from_index(
                        context.scene.collision_material_index)
                    obj.data.materials.append(mat)
            if not correct_type:
                self.report(
                    {'INFO'}, f"{obj.name} must be a Poly Bound or Bound other than {SOLLUMZ_UI_NAMES[BoundType.COMPOSITE]}, {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]}, or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}. Object skipped.")

        return {'FINISHED'}


class SOLLUMZ_OT_delete_flag_preset(bpy.types.Operator):
    """Delete a flag preset"""
    bl_idname = "sollumz.delete_flag_preset"
    bl_label = "Delete Flag Preset"
    bl_options = {"UNDO"}

    preset_blacklist = ['Default']

    def execute(self, context):
        index = context.scene.flag_preset_index
        handle_load_flag_presets(self)

        try:
            preset = flag_presets.presets[index]
            if preset.name in self.preset_blacklist:
                self.report({'INFO'}, f"Cannot delete a default preset!")
                return {'CANCELLED'}

            filepath = get_flag_presets_path()
            flag_presets.presets.remove(preset)

            try:
                flag_presets.write_xml(filepath)
                handle_load_flag_presets(self)

                return {'FINISHED'}
            except:
                self.report({'ERROR'}, traceback.format_exc())
                return {'CANCELLED'}

        except IndexError:
            self.report(
                {'ERROR'}, f"Flag preset does not exist! Ensure the preset file is present in the '{filepath}' directory.")
            return {'CANCELLED'}


class SOLLUMZ_OT_save_flag_preset(bpy.types.Operator):
    """Save a flag preset"""
    bl_idname = "sollumz.save_flag_preset"
    bl_label = "Save Flag Preset"
    bl_options = {"UNDO"}

    def execute(self, context):
        obj = context.active_object
        handle_load_flag_presets(self)

        if not obj:
            self.report({'INFO'}, 'No object selected!')
            return {'CANCELLED'}

        if obj.sollum_type and not (obj.sollum_type == BoundType.GEOMETRY or obj.sollum_type == BoundType.GEOMETRYBVH):
            self.report(
                {'INFO'}, f'Selected object must be either a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}!')
            return {'CANCELLED'}

        name = context.scene.new_flag_preset_name
        if len(name) < 1:
            self.report(
                {'INFO'}, f'Please specify a name for the new flag preset.')
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

        filepath = get_flag_presets_path()

        for preset in flag_presets.presets:
            if preset.name == name:
                self.report(
                    {'INFO'}, f'A preset with that name already exists! If you wish to overwrite this preset, delete the original.')
                return {'CANCELLED'}

        try:
            flag_presets.presets.append(flag_preset)
            flag_presets.write_xml(filepath)
            handle_load_flag_presets(self)

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

        handle_load_flag_presets(self)

        for obj in selected:
            if obj.sollum_type and not (obj.sollum_type == BoundType.GEOMETRY or obj.sollum_type == BoundType.GEOMETRYBVH):
                self.report(
                    {'INFO'}, f'Selected objects must be either a {SOLLUMZ_UI_NAMES[BoundType.GEOMETRY]} or {SOLLUMZ_UI_NAMES[BoundType.GEOMETRYBVH]}!')
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
                filepath = get_flag_presets_path()
                self.report(
                    {'ERROR'}, f"Flag preset does not exist! Ensure the preset file is present in the '{filepath}' directory.")
                return {'CANCELLED'}

        return {'FINISHED'}


class SOLLUMZ_OT_clear_col_flags(bpy.types.Operator):
    """Load commonly used collision flags"""
    bl_idname = "sollumz.clear_col_flags"
    bl_label = "Clear Collision Flags"
    bl_options = {"UNDO"}

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

        return {'FINISHED'}
