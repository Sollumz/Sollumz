import binascii
import struct
import math
import bpy

from ..cwxml.ymap import *
from mathutils import Vector
from ..sollumz_properties import SollumType

def box_to_obj(obj, ymap: CMapData):
    group_obj = bpy.data.objects.new("Box Occluders", None)
    group_obj.sollum_type = SollumType.YMAP_BOX_OCCLUDER_GROUP
    group_obj.parent = obj
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(group_obj)
    bpy.context.view_layer.objects.active = group_obj

    obj.ymap_properties.content_flags_toggle.has_occl = True

    # TODO: Make materials color choosable somewhere
    material = bpy.data.materials.new("box_occl_material")
    material.diffuse_color = [0.01, 0.8, 0.2, 1.0]
    for box in ymap.box_occluders:
        bpy.ops.mesh.primitive_cube_add(size=1)
        box_obj = bpy.context.view_layer.objects.active
        box_obj.sollum_type = SollumType.YMAP_BOX_OCCLUDER
        box_obj.name = "Box"
        box_obj.active_material = material
        box_obj.location = Vector([box.center_x, box.center_y, box.center_z]) / 4
        box_obj.rotation_euler[2] = math.atan2(box.cos_z, box.sin_z)
        box_obj.scale = Vector([box.length, box.width, box.height]) / 4
        box_obj.parent = group_obj

    return group_obj

# TODO: Make better?
def get_mesh_data(model: OccludeModelItem):

    result = ([], [])
    for i in range(int(model.num_verts_in_bytes / 12)):
        pos_data: str = model.verts[i*24:(i*24)+24]
        x = struct.unpack('<f', binascii.a2b_hex(pos_data[:8]))[0]
        y = struct.unpack('<f', binascii.a2b_hex(pos_data[8:16]))[0]
        z = struct.unpack('<f', binascii.a2b_hex(pos_data[16:24]))[0]
        result[0].append((x, y, z))

    indicies: str = model.verts[int(model.num_verts_in_bytes * 2):]
    for i in range(int(model.num_tris - 32768)):
        j = i*6
        i0 = int.from_bytes(binascii.a2b_hex(indicies[j:j+2]), 'little')
        i1 = int.from_bytes(binascii.a2b_hex(indicies[j+2:j+4]), 'little')
        i2 = int.from_bytes(binascii.a2b_hex(indicies[j+4:j+6]), 'little')
        result[1].append((i0, i1, i2))

    return result

def model_to_obj(import_op, obj: bpy.types.Object, ymap: CMapData):
    group_obj = bpy.data.objects.new('Model Occluder', None)
    group_obj.parent = obj
    group_obj.sollum_type = SollumType.YMAP_MODEL_OCCLUDER_GROUP
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(group_obj)
    bpy.context.view_layer.objects.active = group_obj

    obj.ymap_properties.content_flags_toggle.has_occl = True

    material = bpy.data.materials.new("model_occl_material")
    material.diffuse_color = [0.8, 0.02, 0.01, 1.0]
    for model in ymap.occlude_models:
        verts, faces = get_mesh_data(model)

        mesh = bpy.data.meshes.new("Model Occluder")
        model_obj = bpy.data.objects.new("Model", mesh)
        model_obj.sollum_type = SollumType.YMAP_MODEL_OCCLUDER
        model_obj.ymap_properties.flags = model.flags
        model_obj.active_material = material
        bpy.context.collection.objects.link(model_obj)
        bpy.context.view_layer.objects.active = model_obj
        mesh.from_pydata(verts, [], faces)
        model_obj.parent = group_obj
        model_obj.lock_location = (True, True, True)
        model_obj.lock_rotation = (True, True, True)
        model_obj.lock_scale = (True, True, True)

def ymap_to_obj(import_op, ymap: CMapData):
    ymap_obj = bpy.data.objects.new(ymap.name, None)
    ymap_obj.sollum_type = SollumType.YMAP
    ymap_obj.lock_location = (True, True, True)
    ymap_obj.lock_rotation = (True, True, True)
    ymap_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(ymap_obj)
    bpy.context.view_layer.objects.active = ymap_obj

    ymap_obj.ymap_properties.name = ymap.name
    ymap_obj.ymap_properties.parent = ymap.parent
    ymap_obj.ymap_properties.flags = ymap.flags
    ymap_obj.ymap_properties.content_flags = ymap.content_flags

    ymap_obj.ymap_properties.streaming_extents_min = ymap.streaming_extents_min
    ymap_obj.ymap_properties.streaming_extents_max = ymap.streaming_extents_max
    ymap_obj.ymap_properties.entities_extents_min =  ymap.entities_extents_min
    ymap_obj.ymap_properties.entities_extents_max =  ymap.entities_extents_max

    if len(ymap.entities) > 0:
        print('Hello World!')

    if len(ymap.box_occluders) > 0:
        box_to_obj(ymap_obj, ymap)
    
    if len(ymap.occlude_models) > 0:
        model_to_obj(import_op, ymap_obj, ymap)

    # TODO: physics_dictionaries

    # TODO: time cycle

    # TODO: car_generators

    # TODO: lod ligths

    # TODO: distant lod lights

    ymap_obj.ymap_properties.block.version = str(ymap.block.version)
    ymap_obj.ymap_properties.block.flags = str(ymap.block.flags)
    ymap_obj.ymap_properties.block.name = ymap.block.name
    ymap_obj.ymap_properties.block.exported_by = ymap.block.exported_by
    ymap_obj.ymap_properties.block.owner = ymap.block.owner
    ymap_obj.ymap_properties.block.time = ymap.block.time

    return ymap_obj


def import_ymap(import_op, filepath, import_settings):
    ymap_xml: CMapData = YMAP.from_xml_file(filepath)
    obj = ymap_to_obj(import_op, ymap_xml)