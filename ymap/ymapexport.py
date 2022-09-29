import bpy

from struct import pack
from ..cwxml.ymap import *
from binascii import hexlify
from mathutils import Vector
from ..tools.meshhelper import get_bound_extents
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.utils import get_min_vector, get_max_vector


def box_from_obj(obj):
    box = BoxOccluderItem()

    box.center_x = round(obj.location.x * 4)
    box.center_y = round(obj.location.y * 4)
    box.center_z = round(obj.location.z * 4)
    box.length = round(obj.scale.x * 4)
    box.width = round(obj.scale.y * 4)
    box.height = round(obj.scale.z * 4)
    dir = Vector((1,0,0))
    dir.rotate(obj.rotation_euler)
    dir *= 0.5
    box.sin_z = round(dir.x * 32767)
    box.cos_z = round(dir.y * 32767)

    # IDEA: Maybe update object transforms to match its rounded exported values
    # since 0.2 * 4 -> 0.8 round -> 1.0 / 4 -> 0.25

    return box

def triangulate_obj(obj):
    '''Convert mesh from n-polygons to triangles'''
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode="OBJECT")

def get_verts_from_obj(obj):
    '''
    For each vertex get its coordinates in global space (this way we don't need to apply transfroms)
    then get their bytes hex representation and append. After that for each face get its indices, 
    get their bytes hex representation and append.

    :return verts: String if vertex coordinates and face indices in hex representation
    :rtype str:
    '''
    verts = ''
    for v in obj.data.vertices:
        for c in obj.matrix_world @ v.co:
            verts += str(hexlify(pack('f', c)))[2:-1].upper()
    for p in obj.data.polygons:
        for i in p.vertices:
           verts += str(hexlify(pack('B', i)))[2:-1].upper()
    return verts

def model_from_obj(obj, export_op):        
    triangulate_obj(obj)

    model = OccludeModelItem()
    model.bmin, model.bmax = get_bound_extents(obj)
    model.verts = get_verts_from_obj(obj)
    model.num_verts_in_bytes = len(obj.data.vertices) * 12
    face_count = len(obj.data.polygons)
    model.num_tris = face_count + 32768
    model.data_size = model.num_verts_in_bytes + (face_count * 3)
    model.flags = obj.ymap_properties.flags

    return model

# TODO: This needs more work for non occluder object (entities )
def calculate_extents(ymap, obj):
    bbmin, bbmax = get_bound_extents(obj)

    ymap.entities_extents_min = get_min_vector(ymap.entities_extents_min, bbmin)
    ymap.entities_extents_max = get_max_vector(ymap.entities_extents_max , bbmax)
    ymap.streaming_extents_min = get_min_vector(ymap.streaming_extents_min, bbmin)
    ymap.streaming_extents_max = get_max_vector(ymap.streaming_extents_max, bbmax)

def ymap_from_object(export_op, obj, exportpath, export_settings=None):
    ymap = CMapData()
    max_int = (2**31)-1
    ymap.entities_extents_min = Vector((max_int, max_int, max_int))
    ymap.entities_extents_max = Vector((0, 0, 0))
    ymap.streaming_extents_min = Vector((max_int, max_int, max_int))
    ymap.streaming_extents_max = Vector((0, 0, 0))

    for child in obj.children:
        # TODO: entities

        if child.sollum_type == SollumType.YMAP_BOX_OCCLUDER_GROUP:
            obj.ymap_properties.content_flags_toggle.has_occl = True

            for box in child.children:
                if box.sollum_type == SollumType.YMAP_BOX_OCCLUDER:
                    
                    ymap.box_occluders.append(box_from_obj(box))
                    calculate_extents(ymap, box)
                else:
                    export_op.report({'WARNING'},
                        f"Object {box.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.YMAP_BOX_OCCLUDER]} type.")

        if child.sollum_type == SollumType.YMAP_MODEL_OCCLUDER_GROUP:
            obj.ymap_properties.content_flags_toggle.has_occl = True

            for model in child.children:
                if model.sollum_type == SollumType.YMAP_MODEL_OCCLUDER:
                    if len(model.data.vertices) > 256:
                        export_op.report({"ERROR"}, 
                            message=f"Object {model.name} has too many vertices and will be skipped. It can not have more than 256 vertices.")
                        continue
                    
                    ymap.occlude_models.append(model_from_obj(model, export_op))
                    calculate_extents(ymap, model)
                else:
                    export_op.report({'WARNING'},
                        f"Object {model.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.YMAP_MODEL_OCCLUDER]} type.")

        # TODO: physics_dictionaries

        # TODO: time cycle

        # TODO: car generators

        # TODO: lod ligths

        # TODO: distant lod lights

    ymap.name = obj.name if not "." in obj.name else obj.name.split(".")[0]
    ymap.parent = obj.ymap_properties.parent
    ymap.flags = obj.ymap_properties.flags
    ymap.content_flags = obj.ymap_properties.content_flags

    # TODO: Calc extents

    ymap.block.version  = obj.ymap_properties.block.version 
    ymap.block.versiflagson  = obj.ymap_properties.block.flags
    ymap.block.name  = obj.ymap_properties.block.name
    ymap.block.exported_by  = obj.ymap_properties.block.exported_by
    ymap.block.owner  = obj.ymap_properties.block.owner
    ymap.block.time  = obj.ymap_properties.block.time

    return ymap


def export_ymap(export_op, obj, filepath, export_settings):
    ymap = ymap_from_object(export_op, obj, filepath, export_settings)
    ymap.write_xml(filepath)