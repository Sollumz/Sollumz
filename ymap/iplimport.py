import bpy
from mathutils import Vector
from ..sollumz_helper import duplicate_object_with_children, set_object_collection
from ..sollumz_properties import SollumType
from ..sollumz_preferences import get_import_settings
from ..cwxml.ipl import IplData, IPL
from .. import logger


def apply_entity_properties(obj, entity):
    obj.entity_properties.archetype_name = entity.archetype_name
    obj.entity_properties.lod_dist = entity.lod_dist
    obj.entity_properties.lod_level = "sollumz_" + entity.lod_level.lower()
    obj.matrix_world = entity.rotation.to_matrix().to_4x4()
    obj.location = entity.position
    obj.scale = entity.scale


def entity_to_obj(ipl_obj: bpy.types.Object, ipl: IplData):
    group_obj = bpy.data.objects.new("Entities", None)
    group_obj.sollum_type = SollumType.YMAP_ENTITY_GROUP
    group_obj.parent = ipl_obj
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(group_obj)
    bpy.context.view_layer.objects.active = group_obj

    found = False
    if ipl.entities:
        print("entities found")
        for obj in bpy.context.collection.all_objects:
            for entity in ipl.entities:
                if entity.archetype_name == obj.name and obj.name in bpy.context.view_layer.objects:
                    found = True
                    apply_entity_properties(obj, entity)
        if found:
            logger.info(f"Succesfully imported: {ipl.name}.ipl")
            return True
        else:
            logger.info(
                f"No entities from '{ipl.name}.ipl' exist in the view layer!")
            return False
    else:
        logger.error(f"{ipl.name}.ipl contains no entities to import!")
        return False


def instanced_entity_to_obj(ipl_obj: bpy.types.Object, ipl: IplData):
    group_obj = bpy.data.objects.new("Entities", None)
    group_obj.sollum_type = SollumType.YMAP_ENTITY_GROUP
    group_obj.parent = ipl_obj
    group_obj.lock_location = (True, True, True)
    group_obj.lock_rotation = (True, True, True)
    group_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(group_obj)
    bpy.context.view_layer.objects.active = group_obj

    if ipl.entities:
        entities_amount = len(ipl.entities)
        count = 0

        for entity in ipl.entities:
            obj = bpy.data.objects.get(entity.archetype_name, None)
            if obj is None:
                continue

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
            for entity in ipl.entities:
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
                f"No entity from '{ipl_obj.name}.ipl' exist in the view layer!")
            return False
    else:
        logger.error(f"{ipl_obj.name}.ipl doesn't contains any entity!")
        return False


def ipl_to_obj(ipl: IplData):
    ipl_obj = bpy.data.objects.new(ipl.name, None)
    ipl_obj.sollum_type = SollumType.YMAP
    ipl_obj.lock_location = (True, True, True)
    ipl_obj.lock_rotation = (True, True, True)
    ipl_obj.lock_scale = (True, True, True)
    bpy.context.collection.objects.link(ipl_obj)
    bpy.context.view_layer.objects.active = ipl_obj

    ipl_obj.ymap_properties.parent = ipl.parent

    import_settings = get_import_settings()


    if not import_settings.ymap_exclude_entities and ipl.entities:
        if import_settings.ymap_instance_entities:
            instanced_entity_to_obj(ipl_obj, ipl)
        else:
            entity_to_obj(ipl_obj, ipl)

    # Set ipl obj hierarchy in the active collection
    set_object_collection(ipl_obj)

    return ipl_obj


def import_ipl(filepath):
    ipl_xml: IplData = IPL.from_xml_file(filepath)
    found = False
    for obj in bpy.context.scene.objects:
        if obj.sollum_type == SollumType.YMAP and obj.name == ipl_xml.name:
            logger.error(
                f"{ipl_xml.name} is already existing in the scene. Aborting.")
            found = True
            break
    if not found:
        obj = ipl_to_obj(ipl_xml)
