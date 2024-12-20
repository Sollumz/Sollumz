import math
import bpy
import numpy as np
from numpy.typing import NDArray
from mathutils import Vector, Euler
from ..sollumz_helper import duplicate_object_with_children, set_object_collection
from ..tools.ymaphelper import add_occluder_material, get_cargen_mesh
from ..sollumz_properties import SollumType
from ..sollumz_preferences import get_import_settings
from ..cwxml.ymap import CMapData, OccludeModel, YMAP
from ..tools.blenderhelper import create_blender_object, create_empty_object
from ..tools.meshhelper import create_box
from .. import logger

# TODO: Make better?


def occlude_model_to_mesh_data(model: OccludeModel) -> tuple[NDArray, NDArray]:
    assert (model.num_tris & 0x8000) != 0, "Only float vertex format of occlude models is supported"

    num_verts_in_bytes = model.num_verts_in_bytes
    num_verts = num_verts_in_bytes // (4*3)  # sizeof(float)*3
    num_tris = model.num_tris & ~0x8000

    data = np.frombuffer(model.verts, dtype=np.uint8)
    verts = data[:num_verts_in_bytes].view(dtype=np.float32).reshape((num_verts, 3))
    faces = data[num_verts_in_bytes:].reshape((num_tris, 3))
    return verts, faces


def apply_entity_properties(obj, entity):
    obj.entity_properties.archetype_name = entity.archetype_name
    obj.entity_properties.flags = entity.flags
    obj.entity_properties.guid = entity.guid
    obj.entity_properties.parent_index = entity.parent_index
    obj.entity_properties.lod_dist = entity.lod_dist
    obj.entity_properties.child_lod_dist = entity.child_lod_dist
    obj.entity_properties.lod_level = "sollumz_" + entity.lod_level.lower()
    obj.entity_properties.num_children = entity.num_children
    obj.entity_properties.priority_level = "sollumz_" + entity.priority_level.lower()
    obj.entity_properties.ambient_occlusion_multiplier = entity.ambient_occlusion_multiplier
    obj.entity_properties.artificial_ambient_occlusion = entity.artificial_ambient_occlusion
    obj.entity_properties.tint_value = entity.tint_value
    if entity.type != "CMloInstanceDef":
        # Entities in YMAPs need rotation inverted
        entity.rotation.invert()
    obj.matrix_world = entity.rotation.to_matrix().to_4x4()
    obj.location = entity.position
    obj.scale = Vector((entity.scale_xy, entity.scale_xy, entity.scale_z))


def entity_to_obj(ymap_obj: bpy.types.Object, ymap: CMapData):
    group_obj = bpy.data.objects.new("Entities", None)
    group_obj.sollum_type = SollumType.YMAP_ENTITY_GROUP
    group_obj.parent = ymap_obj
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(group_obj)
    bpy.context.view_layer.objects.active = group_obj

    found = False
    if ymap.entities:
        for obj in bpy.context.collection.all_objects:
            for entity in ymap.entities:
                if entity.archetype_name == obj.name and obj.name in bpy.context.view_layer.objects:
                    found = True
                    apply_entity_properties(obj, entity)
        if found:
            logger.info(f"Succesfully imported: {ymap.name}.ymap")
            return True
        else:
            logger.info(
                f"No entities from '{ymap.name}.ymap' exist in the view layer!")
            return False
    else:
        logger.error(f"{ymap.name}.ymap contains no entities to import!")
        return False


def instanced_entity_to_obj(ymap_obj: bpy.types.Object, ymap: CMapData):
    group_obj = bpy.data.objects.new("Entities", None)
    group_obj.sollum_type = SollumType.YMAP_ENTITY_GROUP
    group_obj.parent = ymap_obj
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(group_obj)
    bpy.context.view_layer.objects.active = group_obj

    if ymap.entities:
        entities_amount = len(ymap.entities)
        count = 0

        for entity in ymap.entities:
            obj = bpy.data.objects.get(entity.archetype_name, None)
            if obj is None:
                # No object with the given archetype name found
                continue

            # TODO: requiring ymap entities to be drawable or fragment in blender seems like an unnecessary limitation
            # Need to special case assets because their type when imported by sollumz is drawable model
            if obj.sollum_type == SollumType.DRAWABLE or obj.sollum_type == SollumType.FRAGMENT or obj.asset_data is not None:
                new_obj = duplicate_object_with_children(obj)
                apply_entity_properties(new_obj, entity)
                new_obj.parent = group_obj
                count += 1
                entity.found = True
            else:
                logger.error(
                    f"Cannot use your '{obj.name}' object because it is not a 'Drawable' type!")

        # Creating empty entity if no object was found for reference, and notify user
        import_settings = get_import_settings()

        if not import_settings.ymap_skip_missing_entities:
            for entity in ymap.entities:
                if entity.found is None:
                    empty_obj = bpy.data.objects.new(
                        entity.archetype_name + " (not found)", None)
                    empty_obj.parent = group_obj
                    apply_entity_properties(empty_obj, entity)
                    empty_obj.sollum_type = SollumType.DRAWABLE
                    logger.error(
                        f"'{entity.archetype_name}' is missing in scene, creating an empty drawable instead.")
        if count > 0:
            logger.info(
                f"Succesfully placed {count}/{entities_amount} entities from scene!")
            return group_obj
        else:
            logger.info(
                f"No entity from '{ymap_obj.name}.ymap' exist in the view layer!")
            return False
    else:
        logger.error(f"{ymap_obj.name}.ymap doesn't contains any entity!")
        return False


def box_to_obj(obj, ymap: CMapData):
    group_obj = create_empty_object(SollumType.YMAP_BOX_OCCLUDER_GROUP, "Box Occluders")
    group_obj.parent = obj
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.view_layer.objects.active = group_obj

    obj.ymap_properties.content_flags_toggle.has_occl = True

    for box in ymap.box_occluders:
        box_obj = create_blender_object(SollumType.YMAP_BOX_OCCLUDER, "Box")
        box_obj.active_material = add_occluder_material(SollumType.YMAP_BOX_OCCLUDER)
        create_box(box_obj.data, 1)
        box_obj.location = Vector([box.center_x, box.center_y, box.center_z]) / 4
        box_obj.rotation_euler[2] = math.atan2(box.cos_z, box.sin_z)
        box_obj.scale = Vector([box.length, box.width, box.height]) / 4
        box_obj.parent = group_obj

    return group_obj


def model_to_obj(obj: bpy.types.Object, ymap: CMapData):
    group_obj = create_empty_object(SollumType.YMAP_MODEL_OCCLUDER_GROUP, "Model Occluders")
    group_obj.parent = obj
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.view_layer.objects.active = group_obj

    obj.ymap_properties.content_flags_toggle.has_occl = True

    for model in ymap.occlude_models:
        verts, faces = occlude_model_to_mesh_data(model)

        mesh = bpy.data.meshes.new("Model Occluders")
        model_obj = create_blender_object(SollumType.YMAP_MODEL_OCCLUDER, "Model", mesh)
        model_obj.ymap_model_occl_properties.model_occl_flags = model.flags
        model_obj.active_material = add_occluder_material(SollumType.YMAP_MODEL_OCCLUDER)
        mesh.from_pydata(verts, [], faces)
        model_obj.parent = group_obj
        model_obj.lock_location = (True, True, True)
        model_obj.lock_rotation = (True, True, True)
        model_obj.lock_scale = (True, True, True)


def cargen_to_obj(obj: bpy.types.Object, ymap: CMapData):
    group_obj = bpy.data.objects.new("Car Generators", None)
    group_obj.sollum_type = SollumType.YMAP_CAR_GENERATOR_GROUP
    group_obj.parent = obj
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(group_obj)
    bpy.context.view_layer.objects.active = group_obj

    cargen_ref_mesh = get_cargen_mesh()

    for cargen in ymap.car_generators:
        cargen_obj = bpy.data.objects.new("Car Generator", object_data=cargen_ref_mesh)
        cargen_obj.ymap_cargen_properties.orient_x = cargen.orient_x
        cargen_obj.ymap_cargen_properties.orient_y = cargen.orient_y
        cargen_obj.ymap_cargen_properties.perpendicular_length = cargen.perpendicular_length
        cargen_obj.ymap_cargen_properties.car_model = cargen.car_model
        cargen_obj.ymap_cargen_properties.flags = cargen.flags
        cargen_obj.ymap_cargen_properties.body_color_remap_1 = cargen.body_color_remap_1
        cargen_obj.ymap_cargen_properties.body_color_remap_2 = cargen.body_color_remap_2
        cargen_obj.ymap_cargen_properties.body_color_remap_3 = cargen.body_color_remap_3
        cargen_obj.ymap_cargen_properties.body_color_remap_4 = cargen.body_color_remap_4
        cargen_obj.ymap_cargen_properties.pop_group = cargen.pop_group
        cargen_obj.ymap_cargen_properties.livery = cargen.livery

        angl = math.atan2(cargen.orient_x, cargen.orient_y)
        cargen_obj.rotation_euler = Euler((0.0, 0.0, angl * -1))

        cargen_obj.location = cargen.position
        cargen_obj.sollum_type = SollumType.YMAP_CAR_GENERATOR
        cargen_obj.parent = group_obj


def ymap_to_obj(ymap: CMapData):
    ymap_obj = bpy.data.objects.new(ymap.name, None)
    ymap_obj.sollum_type = SollumType.YMAP
    ymap_obj.lock_location = (True, True, True)
    ymap_obj.lock_rotation = (True, True, True)
    ymap_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(ymap_obj)
    bpy.context.view_layer.objects.active = ymap_obj

    ymap_obj.ymap_properties.parent = ymap.parent
    ymap_obj.ymap_properties.flags = ymap.flags
    ymap_obj.ymap_properties.content_flags = ymap.content_flags

    ymap_obj.ymap_properties.streaming_extents_min = ymap.streaming_extents_min
    ymap_obj.ymap_properties.streaming_extents_max = ymap.streaming_extents_max
    ymap_obj.ymap_properties.entities_extents_min = ymap.entities_extents_min
    ymap_obj.ymap_properties.entities_extents_max = ymap.entities_extents_max

    import_settings = get_import_settings()

    # Entities
    # TODO: find a way to retrieve ignored stuff on export
    if not import_settings.ymap_exclude_entities and ymap.entities:
        if import_settings.ymap_instance_entities:
            instanced_entity_to_obj(ymap_obj, ymap)
        else:
            entity_to_obj(ymap_obj, ymap)

    # Box occluders
    if import_settings.ymap_box_occluders == False and len(ymap.box_occluders) > 0:
        box_to_obj(ymap_obj, ymap)

    # Model occluders
    if import_settings.ymap_model_occluders == False and len(ymap.occlude_models) > 0:
        model_to_obj(ymap_obj, ymap)

    # TODO: physics_dictionaries

    # TODO: time cycle

    # Car generators
    if import_settings.ymap_car_generators == False and len(ymap.car_generators) > 0:
        cargen_to_obj(ymap_obj, ymap)

    # TODO: lod ligths

    # TODO: distant lod lights

    ymap_obj.ymap_properties.block.version = str(ymap.block.version)
    ymap_obj.ymap_properties.block.flags = str(ymap.block.flags)
    ymap_obj.ymap_properties.block.name = ymap.block.name
    ymap_obj.ymap_properties.block.exported_by = ymap.block.exported_by
    ymap_obj.ymap_properties.block.owner = ymap.block.owner
    ymap_obj.ymap_properties.block.time = ymap.block.time

    # Set ymap obj hierarchy in the active collection
    set_object_collection(ymap_obj)

    return ymap_obj


def import_ymap(filepath):
    ymap_xml: CMapData = YMAP.from_xml_file(filepath)
    found = False
    for obj in bpy.context.scene.objects:
        if obj.sollum_type == SollumType.YMAP and obj.name == ymap_xml.name:
            logger.error(
                f"{ymap_xml.name} is already existing in the scene. Aborting.")
            found = True
            break
    if not found:
        obj = ymap_to_obj(ymap_xml)
