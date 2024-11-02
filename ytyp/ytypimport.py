import bpy
from typing import Union
from mathutils import Vector, Quaternion
from ..cwxml import ytyp as ytypxml, ymap as ymapxml
from ..sollumz_properties import ArchetypeType, AssetType, EntityLodLevel, EntityPriorityLevel
from ..sollumz_preferences import get_import_settings
from ..sollumz_helper import duplicate_object_with_children
from .properties.ytyp import CMapTypesProperties, ArchetypeProperties, SpecialAttribute, TimecycleModifierProperties, RoomProperties, PortalProperties, MloEntityProperties, EntitySetProperties
from .properties.extensions import ExtensionProperties, ExtensionType, ExtensionsContainer
from ..ydr.light_flashiness import Flashiness


def create_mlo_entity_set(entity_set_xml: ytypxml.EntitySet, archetype: ArchetypeProperties):
    """Create an mlo entity sets from an xml for the provided archetype data-block."""

    entity_set: EntitySetProperties = archetype.new_entity_set()
    entity_set.name = entity_set_xml.name

    locations = entity_set_xml.locations
    entities = entity_set_xml.entities

    for index in range(len(locations)):
        entity = create_mlo_entity(entities[index], archetype)
        entity.attached_entity_set_id = str(entity_set.id)

        location = locations[index]
        if (location & (1 << 31)) != 0:
            # If MSB is set, the entity is attached to a portal
            location &= ~(1 << 31)  # clear MSB
            entity.attached_portal_id = str(archetype.portals[location].id)
        else:
            entity.attached_room_id = str(archetype.rooms[location].id)


def create_entity_set_entity(entity_xml: ymapxml.Entity, entity_set: EntitySetProperties):
    """Create an mlo entity from an xml for the provided archetype data-block."""

    entity: MloEntityProperties = entity_set.new_entity_set_entity()
    entity.position = entity_xml.position
    entity.rotation = entity_xml.rotation.inverted()
    entity.scale_xy = entity_xml.scale_xy
    entity.scale_z = entity_xml.scale_z

    find_and_link_entity_object(entity_xml, entity)

    entity.archetype_name = entity_xml.archetype_name
    entity.flags.total = str(entity_xml.flags)
    entity.guid = entity_xml.guid
    entity.parent_index = entity_xml.parent_index
    entity.lod_dist = entity_xml.lod_dist
    entity.child_lod_dist = entity_xml.child_lod_dist
    entity.lod_level = EntityLodLevel[entity_xml.lod_level]
    entity.priority_level = EntityPriorityLevel[entity_xml.priority_level]
    entity.num_children = entity_xml.num_children
    entity.ambient_occlusion_multiplier = entity_xml.ambient_occlusion_multiplier
    entity.artificial_ambient_occlusion = entity_xml.artificial_ambient_occlusion
    entity.tint_value = entity_xml.tint_value

    for extension_xml in entity_xml.extensions:
        create_extension(extension_xml, entity)


def create_mlo_tcm(tcm_xml: ytypxml.TimeCycleModifier, archetype: ArchetypeProperties):
    """Create an mlo timecycle modifier from an xml for the provided archetype data-block."""

    tcm: TimecycleModifierProperties = archetype.new_tcm()
    tcm.name = tcm_xml.name
    tcm.sphere = tcm_xml.sphere
    tcm.percentage = max(0.0, min(100.0, tcm_xml.percentage))
    tcm.range = tcm_xml.range
    tcm.start_hour = tcm_xml.start_hour
    tcm.end_hour = tcm_xml.end_hour


def create_mlo_portal(portal_xml: ytypxml.Portal, archetype: ArchetypeProperties):
    """Create an mlo portal from an xml for the provided archetype data-block."""

    portal: PortalProperties = archetype.new_portal()
    for index, corner in enumerate(portal_xml.corners):
        setattr(portal, f"corner{index + 1}", corner.value)
    portal.room_from_id = str(archetype.rooms[portal_xml.room_from].id)
    portal.room_to_id = str(archetype.rooms[portal_xml.room_to].id)
    portal.flags.total = str(portal_xml.flags)
    portal.mirror_priority = portal_xml.mirror_priority
    portal.opacity = portal_xml.opacity
    portal.audio_occlusion = str(
        portal_xml.audio_occlusion)
    for index in portal_xml.attached_objects:
        archetype.entities[index].attached_portal_id = str(portal.id)


def create_mlo_room(room_xml: ytypxml.Room, archetype: ArchetypeProperties):
    """Create an mlo room from an xml for the provided archetype data-block."""

    room: RoomProperties = archetype.new_room()
    room.name = room_xml.name
    room.bb_min = room_xml.bb_min
    room.bb_max = room_xml.bb_max
    room.blend = room_xml.blend
    room.timecycle = room_xml.timecycle_name
    room.secondary_timecycle = room_xml.secondary_timecycle_name
    room.flags.total = str(room_xml.flags)
    room.floor_id = room_xml.floor_id
    room.exterior_visibility_depth = room_xml.exterior_visibility_depth
    for index in room_xml.attached_objects:
        archetype.entities[index].attached_room_id = str(room.id)


def find_and_link_entity_object(entity_xml: ymapxml.Entity, entity: MloEntityProperties):
    """Attempt to find an existing entity object in the scene and link it to the entity data-block.

    If the import setting ``SollumzImportSettings.ytyp_mlo_instance_entities`` is set, a copy of the found object is
    linked instead of the object itself.
    """

    should_instance = get_import_settings().ytyp_mlo_instance_entities

    # Lookup in the whole .blend (i.e. current scene, other scenes, asset browser)
    obj = bpy.data.objects.get(entity_xml.archetype_name, None)
    if obj is None:
        # No object with the given archetype name found
        return

    if obj.name not in bpy.context.scene.objects:
        # Since it isn't in the current scene, we have to duplicate the object always
        should_instance = True
    elif should_instance:
        # If found in the scene and user wants to instance entities, only instance it if it is no longer at the origin,
        # meaning it was already placed elsewhere in the MLO or the user moved it away.
        # This is to support the workflow of importing all models and then importing the MLO ytyp with instancing
        # enabled, without duplicating every entity.
        origin = Vector((0.0, 0.0, 0.0))
        should_instance = obj.location != origin

    if should_instance:
        obj = duplicate_object_with_children(obj)

    entity.linked_object = obj
    obj.location = entity.position
    obj.rotation_euler = entity.rotation.to_euler()
    obj.scale = Vector((entity.scale_xy, entity.scale_xy, entity.scale_z))


def create_mlo_entity(entity_xml: ymapxml.Entity, archetype: ArchetypeProperties):
    """Create an mlo entity from an xml for the provided archetype data-block."""

    entity: MloEntityProperties = archetype.new_entity()
    entity.position = entity_xml.position
    entity.rotation = entity_xml.rotation.inverted()
    entity.scale_xy = entity_xml.scale_xy
    entity.scale_z = entity_xml.scale_z

    find_and_link_entity_object(entity_xml, entity)

    entity.archetype_name = entity_xml.archetype_name
    entity.flags.total = str(entity_xml.flags)
    entity.guid = entity_xml.guid
    entity.parent_index = entity_xml.parent_index
    entity.lod_dist = entity_xml.lod_dist
    entity.child_lod_dist = entity_xml.child_lod_dist
    entity.lod_level = EntityLodLevel[entity_xml.lod_level]
    entity.priority_level = EntityPriorityLevel[entity_xml.priority_level]
    entity.num_children = entity_xml.num_children
    entity.ambient_occlusion_multiplier = entity_xml.ambient_occlusion_multiplier
    entity.artificial_ambient_occlusion = entity_xml.artificial_ambient_occlusion
    entity.tint_value = entity_xml.tint_value

    for extension_xml in entity_xml.extensions:
        create_extension(extension_xml, entity)

    return entity


def set_extension_props(extension_xml: ymapxml.Extension, extension: ExtensionProperties):
    """Set extension data-block properties to the provided extension xml props."""
    extension.name = extension_xml.name
    extension_properties = extension.get_properties()

    extension_properties.offset_position = extension_xml.offset_position

    ignored_props = getattr(extension_properties.__class__, "ignored_in_import_export", None) # see LightShaftExtensionProperties

    for prop_name in extension_properties.__class__.__annotations__:
        if ignored_props is not None and prop_name in ignored_props:
            continue

        # TODO: this check doesn't work as intended, `hasattr` with XML classes always returns true for some reason
        if not hasattr(extension_xml, prop_name):
            # Unknown prop name. Need warning
            print(
                f"Unknown {extension.extension_type} prop name '{prop_name}'.")
            continue

        prop_value = getattr(extension_xml, prop_name)

        if prop_value is None:
            continue

        if isinstance(prop_value, Quaternion):
            prop_value = prop_value.to_euler()

        elif prop_name == "effect_hash":
            # `effectHash` is stored as decimal value.
            # Convert to `hash_` string or empty string for 0
            try:
                prop_value_int = int(prop_value)
            except ValueError:
                prop_value_int = 0
            prop_value = f"hash_{prop_value_int:08X}" if prop_value_int != 0 else ""

        elif prop_name == "flashiness":
            # `flashiness` is now an enum property, we need the enum as string
            prop_value = Flashiness(prop_value).name


        setattr(extension_properties, prop_name, prop_value)


def create_extension(extension_xml: ymapxml.Extension, extensions_container: ExtensionsContainer) -> Union[ExtensionProperties, None]:
    """Create an entity extension from the given extension xml."""

    extension_type = extension_xml.type

    if extension_type not in ExtensionType._value2member_map_:
        # Warning needed here. Unknown extension type
        print(f"Unknown extension type {extension_type}")
        return None

    extension = extensions_container.new_extension(extension_type)
    set_extension_props(extension_xml, extension)

    if extension_type == ExtensionType.LIGHT_EFFECT and not extensions_container.IS_ARCHETYPE:
        # Create the light objects from this light effect extension
        obj = extensions_container.linked_object
        armature_obj = obj if obj is not None and obj.type == "ARMATURE" else None

        from ..ydr.lights import create_light_instance_objs
        lights_parent_obj = create_light_instance_objs(extension_xml.instances, armature_obj)
        lights_parent_obj.name = f"{extensions_container.archetype_name}.light_effect"
        if obj is not None:
            # Constraint instead of parenting for a simpler hierarchy
            # Also this way we don't need to distinguish between original lights and light effect lights.
            # Original ones will always be the lights children of the object.
            constraint = lights_parent_obj.constraints.new("COPY_TRANSFORMS")
            constraint.target = obj

        extension.light_effect_properties.linked_lights_object = lights_parent_obj

    return extension


def create_mlo_archetype_children(archetype_xml: ytypxml.MloArchetype, archetype: ArchetypeProperties):
    """Create entities, rooms, portals, and timecylce modifiers for an mlo archetype."""

    for entity_xml in archetype_xml.entities:
        create_mlo_entity(entity_xml, archetype)

    for room_xml in archetype_xml.rooms:
        create_mlo_room(room_xml, archetype)

    for portal_xml in archetype_xml.portals:
        create_mlo_portal(portal_xml, archetype)

    for tcm_xml in archetype_xml.timecycle_modifiers:
        create_mlo_tcm(tcm_xml, archetype)

    for entityset_xml in archetype_xml.entity_sets:
        create_mlo_entity_set(entityset_xml, archetype)

    entities_are_instanced = get_import_settings().ytyp_mlo_instance_entities
    if entities_are_instanced:
        organize_mlo_entities_in_collections(archetype)


def organize_mlo_entities_in_collections(archetype: ArchetypeProperties):
    """Places all entities linked objects in collections. One collection per room."""

    base_collection_name = f"{archetype.asset_name}.entities"
    base_collection = bpy.data.collections.new(base_collection_name)
    bpy.context.collection.children.link(base_collection)
    mlo_collections = {base_collection_name: base_collection}

    def _link_to_collection(obj, coll):
        for c in obj.users_collection:
            c.objects.unlink(obj)
        coll.objects.link(obj)

    def _link_to_collection_recursive(obj, coll):
        _link_to_collection(obj, coll)
        for child_obj in obj.children_recursive: # could be slow with lots of entities, O(len(bpy.data.objects)) time
            _link_to_collection(child_obj, coll)

    light_effect_objs = []
    for entity in archetype.entities:
        for ext in entity.extensions:
            if ext.extension_type == ExtensionType.LIGHT_EFFECT:
                props = ext.get_properties()
                if props.linked_lights_object is not None:
                    light_effect_objs.append(props.linked_lights_object)

        obj = entity.linked_object
        if obj is None:
            continue

        room_name = entity.get_room_name()
        if room_name:
            entity_collection_name = f"{archetype.asset_name}.{room_name}"
        else:
            entity_collection_name = base_collection_name

        entity_collection = mlo_collections.get(entity_collection_name, None)
        if entity_collection is None:
            entity_collection = bpy.data.collections.new(entity_collection_name)
            base_collection.children.link(entity_collection)
            mlo_collections[entity_collection_name] = entity_collection

        _link_to_collection_recursive(obj, entity_collection)

    if light_effect_objs:
        # Place all light effect objects in their own collection
        light_effect_collection_name = f"{archetype.asset_name}.light_effects"
        light_effect_collection = bpy.data.collections.new(light_effect_collection_name)
        bpy.context.collection.children.link(light_effect_collection)
        for lights_parent_obj in light_effect_objs:
            _link_to_collection_recursive(lights_parent_obj, light_effect_collection)


def find_and_set_archetype_asset(archetype: ArchetypeProperties):
    """Atempt to find an existing archetype asset in the scene and set it as the current asset."""

    obj = bpy.context.scene.objects.get(archetype.asset_name, None)
    if obj is None:
        return

    archetype.asset = obj


def get_asset_type_enum(xml_asset_type: str) -> str:
    """Get asset type enum based on xml asset type string."""

    if xml_asset_type == "ASSET_TYPE_UNINITIALIZED":
        return AssetType.UNITIALIZED
    elif xml_asset_type == "ASSET_TYPE_FRAGMENT":
        return AssetType.FRAGMENT
    elif xml_asset_type == "ASSET_TYPE_DRAWABLE":
        return AssetType.DRAWABLE
    elif xml_asset_type == "ASSET_TYPE_DRAWABLEDICTIONARY":
        return AssetType.DRAWABLE_DICTIONARY

    return AssetType.ASSETLESS


def create_archetype(archetype_xml: ytypxml.BaseArchetype, ytyp: CMapTypesProperties):
    """Create a ytyp archetype given an archetype cwxml and a Blender ytyp data-block."""

    archetype: ArchetypeProperties = ytyp.new_archetype()

    archetype.name = archetype_xml.name
    archetype.flags.total = str(archetype_xml.flags)
    archetype.lod_dist = archetype_xml.lod_dist
    archetype.special_attribute = SpecialAttribute(archetype_xml.special_attribute).name
    archetype.hd_texture_dist = archetype_xml.hd_texture_dist
    archetype.texture_dictionary = archetype_xml.texture_dictionary
    archetype.clip_dictionary = archetype_xml.clip_dictionary
    archetype.drawable_dictionary = archetype_xml.drawable_dictionary
    archetype.physics_dictionary = archetype_xml.physics_dictionary
    archetype.bb_min = archetype_xml.bb_min
    archetype.bb_max = archetype_xml.bb_max
    archetype.bs_center = archetype_xml.bs_center
    archetype.bs_radius = archetype_xml.bs_radius
    archetype.asset_name = archetype_xml.asset_name
    archetype.asset_type = get_asset_type_enum(archetype_xml.asset_type)

    find_and_set_archetype_asset(archetype)

    if archetype_xml.type == "CBaseArchetypeDef":
        archetype.type = ArchetypeType.BASE
    elif archetype_xml.type == "CTimeArchetypeDef":
        archetype.type = ArchetypeType.TIME
        archetype.time_flags.total = str(archetype_xml.time_flags)
    elif archetype_xml.type == "CMloArchetypeDef":
        archetype.type = ArchetypeType.MLO
        archetype.mlo_flags.total = str(archetype_xml.mlo_flags)
        create_mlo_archetype_children(archetype_xml, archetype)

    for extension_xml in archetype_xml.extensions:
        create_extension(extension_xml, archetype)


def ytyp_to_obj(ytyp_xml: ytypxml.CMapTypes):
    """Create a ytyp data-block in the Blender scene given a ytyp cwxml."""

    ytyp: CMapTypesProperties = bpy.context.scene.ytyps.add()
    ytyp.name = ytyp_xml.name

    bpy.context.scene.ytyp_index = len(bpy.context.scene.ytyps) - 1

    for arch_xml in ytyp_xml.archetypes:
        create_archetype(arch_xml, ytyp)


def import_ytyp(filepath: str):
    ytyp_xml = ytypxml.YTYP.from_xml_file(filepath)
    ytyp_to_obj(ytyp_xml)
