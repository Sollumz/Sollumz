import bpy
import re
import math

from mathutils import Vector
from struct import pack
from ..cwxml.ymap import *
from binascii import hexlify
from ..tools.blenderhelper import remove_number_suffix
from ..tools.meshhelper import get_bound_center_from_bounds, get_extents, get_dimensions
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from ..tools.utils import get_min_vector, get_max_vector
from ..sollumz_preferences import get_export_settings
from .. import logger


def box_from_obj(obj):
    box = BoxOccluder()

    bbmin, bbmax = get_extents(obj)
    center = get_bound_center_from_bounds(bbmin, bbmax)
    dimensions = obj.dimensions

    box.center_x = round(center.x * 4)
    box.center_y = round(center.y * 4)
    box.center_z = round(center.z * 4)

    box.length = round(dimensions.x * 4)
    box.width = round(dimensions.y * 4)
    box.height = round(dimensions.z * 4)

    dir = Vector((1, 0, 0))
    dir.rotate(obj.rotation_euler)
    dir *= 0.5
    box.sin_z = round(dir.x * 32767)
    box.cos_z = round(dir.y * 32767)

    return box


def triangulate_obj(obj):
    """Convert mesh from n-polygons to triangles"""
    bpy.context.view_layer.objects.active = obj
    bpy.ops.object.mode_set(mode="EDIT")
    bpy.ops.mesh.select_all(action="SELECT")
    bpy.ops.mesh.quads_convert_to_tris()
    bpy.ops.object.mode_set(mode="OBJECT")


def get_verts_from_obj(obj):
    """
    For each vertex get its coordinates in global space (this way we don't need to apply transfroms)
    then get their bytes hex representation and append. After that for each face get its indices, 
    get their bytes hex representation and append.

    :return verts: String if vertex coordinates and face indices in hex representation
    :rtype str:
    """
    verts = ''
    for v in obj.data.vertices:
        for c in obj.matrix_world @ v.co:
            verts += str(hexlify(pack('f', c)))[2:-1].upper()
    for p in obj.data.polygons:
        for i in p.vertices:
            verts += str(hexlify(pack('B', i)))[2:-1].upper()
    return verts


def model_from_obj(obj):
    triangulate_obj(obj)

    model = OccludeModel()
    model.bmin, model.bmax = get_extents(obj)
    model.verts = get_verts_from_obj(obj)
    model.num_verts_in_bytes = len(obj.data.vertices) * 12
    face_count = len(obj.data.polygons)
    model.num_tris = face_count + 32768
    model.data_size = model.num_verts_in_bytes + (face_count * 3)
    model.flags = obj.ymap_properties.flags

    return model


def entity_from_obj(obj):
    # Removing " (not found)" suffix, created when importing ymaps while entity was not found in the view layer
    obj.name = re.sub(" \(not found\)", "", obj.name.lower())

    entity = Entity()
    entity.archetype_name = remove_number_suffix(obj.name)
    entity.flags = int(obj.entity_properties.flags)
    entity.guid = int(obj.entity_properties.guid)
    entity.position = obj.location
    entity.rotation = obj.rotation_euler.to_quaternion()
    if entity.type != "CMloInstanceDef":
        entity.rotation.invert()
    entity.scale_xy = obj.scale.x
    entity.scale_z = obj.scale.z
    entity.parent_index = int(obj.entity_properties.parent_index)
    entity.lod_dist = obj.entity_properties.lod_dist
    entity.child_lod_dist = obj.entity_properties.child_lod_dist
    entity.lod_level = obj.entity_properties.lod_level.upper().replace("SOLLUMZ_", "")
    entity.num_children = int(obj.entity_properties.num_children)
    entity.priority_level = obj.entity_properties.priority_level.upper().replace("SOLLUMZ_", "")
    entity.ambient_occlusion_multiplier = int(
        obj.entity_properties.ambient_occlusion_multiplier)
    entity.artificial_ambient_occlusion = int(
        obj.entity_properties.artificial_ambient_occlusion)
    entity.tint_value = int(obj.entity_properties.tint_value)

    return entity

# TODO: This needs more work for non occluder object (entities )


def calculate_extents(ymap, obj):
    bbmin, bbmax = get_extents(obj)

    ymap.entities_extents_min = get_min_vector(
        ymap.entities_extents_min, bbmin)
    ymap.entities_extents_max = get_max_vector(
        ymap.entities_extents_max, bbmax)
    ymap.streaming_extents_min = get_min_vector(
        ymap.streaming_extents_min, bbmin)
    ymap.streaming_extents_max = get_max_vector(
        ymap.streaming_extents_max, bbmax)


def cargen_from_obj(obj):
    cargen = CarGenerator()
    cargen.position = obj.location

    cargen.orient_x, cargen.orient_y = calculate_cargen_orient(obj)

    cargen.perpendicular_length = obj.ymap_cargen_properties.perpendicular_length
    cargen.car_model = obj.ymap_cargen_properties.car_model
    cargen.flags = obj.ymap_cargen_properties.cargen_flags
    cargen.body_color_remap_1 = obj.ymap_cargen_properties.body_color_remap_1
    cargen.body_color_remap_2 = obj.ymap_cargen_properties.body_color_remap_2
    cargen.body_color_remap_3 = obj.ymap_cargen_properties.body_color_remap_3
    cargen.body_color_remap_4 = obj.ymap_cargen_properties.body_color_remap_4
    cargen.pop_group = obj.ymap_cargen_properties.pop_group
    cargen.livery = obj.ymap_cargen_properties.livery

    return cargen


def calculate_cargen_orient(obj):
    # *-1 because GTA likes to invert values
    angle = obj.rotation_euler[2] * -1

    return 5 * math.sin(angle), 5 * math.cos(angle)


def ymap_from_object(obj):
    ymap = CMapData()
    max_int = (2**31) - 1
    ymap.entities_extents_min = Vector((max_int, max_int, max_int))
    ymap.entities_extents_max = Vector((0, 0, 0))
    ymap.streaming_extents_min = Vector((max_int, max_int, max_int))
    ymap.streaming_extents_max = Vector((0, 0, 0))

    export_settings = get_export_settings()

    for child in obj.children:
        # Entities
        if export_settings.ymap_exclude_entities == False and child.sollum_type == SollumType.YMAP_ENTITY_GROUP:
            for entity in child.children:
                if entity.sollum_type == SollumType.DRAWABLE:
                    ymap.entities.append(entity_from_obj(entity))
                else:
                    logger.warning(
                        f"Object {entity.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.DRAWABLE]} type.")

        # Box occluders
        if export_settings.ymap_box_occluders == False and child.sollum_type == SollumType.YMAP_BOX_OCCLUDER_GROUP:
            obj.ymap_properties.content_flags_toggle.has_occl = True

            for cargen in child.children:
                if cargen.sollum_type == SollumType.YMAP_BOX_OCCLUDER:
                    ymap.box_occluders.append(box_from_obj(cargen))
                    calculate_extents(ymap, cargen)
                else:
                    logger.warning(
                        f"Object {cargen.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.YMAP_BOX_OCCLUDER]} type.")

        # Model occluders
        if export_settings.ymap_model_occluders == False and child.sollum_type == SollumType.YMAP_MODEL_OCCLUDER_GROUP:
            obj.ymap_properties.content_flags_toggle.has_occl = True

            for model in child.children:
                if model.sollum_type == SollumType.YMAP_MODEL_OCCLUDER:
                    if len(model.data.vertices) > 256:
                        logger.warning(
                            f"Object {model.name} has too many vertices and will be skipped. It can not have more than 256 vertices.")
                        continue

                    ymap.occlude_models.append(
                        model_from_obj(model))
                    calculate_extents(ymap, model)
                else:
                    logger.warning(
                        f"Object {model.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.YMAP_MODEL_OCCLUDER]} type.")

        # TODO: physics_dictionaries

        # TODO: time cycle

        # Car generators
        if export_settings.ymap_car_generators == False and child.sollum_type == SollumType.YMAP_CAR_GENERATOR_GROUP:
            for cargen in child.children:
                if cargen.sollum_type == SollumType.YMAP_CAR_GENERATOR:
                    ymap.car_generators.append(cargen_from_obj(cargen))
                else:
                    logger.warning(
                        f"Object {cargen.name} will be skipped because it is not a {SOLLUMZ_UI_NAMES[SollumType.YMAP_CAR_GENERATOR]} type.")

        # TODO: lod ligths

        # TODO: distant lod lights

    ymap.name = obj.name if not "." in obj.name else obj.name.split(".")[0]
    ymap.parent = obj.ymap_properties.parent
    ymap.flags = obj.ymap_properties.flags
    ymap.content_flags = obj.ymap_properties.content_flags

    # TODO: Calc extents

    ymap.block.version = obj.ymap_properties.block.version
    ymap.block.versiflagson = obj.ymap_properties.block.flags
    ymap.block.name = obj.ymap_properties.block.name
    ymap.block.exported_by = obj.ymap_properties.block.exported_by
    ymap.block.owner = obj.ymap_properties.block.owner
    ymap.block.time = obj.ymap_properties.block.time

    return ymap


def export_ymap(obj: bpy.types.Object, filepath: str) -> bool:
    ymap = ymap_from_object(obj)
    ymap.write_xml(filepath)
    return True
