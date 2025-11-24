import bpy
from typing import Union
from mathutils import Vector, Quaternion
from szio.gta5 import (
    AssetMapTypes,
    Archetype,
    ArchetypeType,
    MloEntity,
    MloRoom,
    MloPortal,
    MloEntitySet,
    MloTimeCycleModifier,
    Extension,
)
from ..iecontext import import_context
from ..sollumz_helper import duplicate_object_with_children
from .properties.ytyp import CMapTypesProperties, ArchetypeProperties, SpecialAttribute, TimecycleModifierProperties, RoomProperties, PortalProperties, MloEntityProperties, EntitySetProperties
from .properties.extensions import ExtensionProperties, ExtensionType, ExtensionsContainer, EXTENSION_DEF_CLASS_TO_TYPE
from szio.gta5 import LightFlashiness


def import_ytyp(asset: AssetMapTypes, name: str):
    """Create a ytyp data-block in the Blender scene given a ytyp asset."""
    ytyp: CMapTypesProperties = bpy.context.scene.ytyps.add()
    ytyp.name = name
    bpy.context.scene.ytyp_index = len(bpy.context.scene.ytyps) - 1

    for arch in asset.archetypes:
        create_archetype(arch, ytyp)


def create_archetype(archetype: Archetype, ytyp: CMapTypesProperties) -> ArchetypeProperties:
    """Create a ytyp archetype given an archetype definition and a Blender ytyp data-block."""
    a = ytyp.new_archetype()
    a.name = archetype.name
    a.type = f"sollumz_archetype_{archetype.type.name.lower()}"
    a.flags.total = str(archetype.flags)
    a.lod_dist = archetype.lod_dist
    a.special_attribute = SpecialAttribute(archetype.special_attribute).name
    a.hd_texture_dist = archetype.hd_texture_dist
    a.texture_dictionary = archetype.texture_dictionary
    a.clip_dictionary = archetype.clip_dictionary
    a.drawable_dictionary = archetype.drawable_dictionary
    a.physics_dictionary = archetype.physics_dictionary
    a.bb_min = archetype.bb_min
    a.bb_max = archetype.bb_max
    a.bs_center = archetype.bs_center
    a.bs_radius = archetype.bs_radius
    a.asset_name = archetype.asset_name
    a.asset_type = f"sollumz_asset_{archetype.asset_type.name.lower()}"

    find_and_set_archetype_asset(a)

    match archetype.type:
        case ArchetypeType.TIME:
            a.time_flags.total = str(archetype.time_flags)
        case ArchetypeType.MLO:
            a.mlo_flags.total = str(archetype.mlo_flags)
            create_mlo_archetype_children(archetype, a)

    for extension in archetype.extensions:
        create_extension(extension, a)

    return a


def find_and_set_archetype_asset(archetype: ArchetypeProperties):
    """Atempt to find an existing archetype asset in the scene and set it as the current asset."""
    obj = bpy.context.scene.objects.get(archetype.asset_name, None)
    if obj is None:
        return

    archetype.asset = obj


def create_mlo_archetype_children(archetype: Archetype, archetype_props: ArchetypeProperties):
    """Create entities, rooms, portals, and timecylce modifiers for an MLO archetype."""
    for entity in archetype.entities:
        create_mlo_entity(entity, archetype_props)

    for room in archetype.rooms:
        create_mlo_room(room, archetype_props)

    for portal in archetype.portals:
        create_mlo_portal(portal, archetype_props)

    for entity_set in archetype.entity_sets:
        create_mlo_entity_set(entity_set, archetype_props)

    for tcm in archetype.timecycle_modifiers:
        create_mlo_tcm(tcm, archetype_props)

    entities_are_instanced = import_context().settings.mlo_instance_entities
    if entities_are_instanced:
        organize_mlo_entities_in_collections(archetype_props)


def create_mlo_entity(entity: MloEntity, archetype: ArchetypeProperties) -> MloEntityProperties:
    """Create an MLO entity from a definition for the provided archetype data-block."""
    e = archetype.new_entity()
    e.archetype_name = entity.archetype_name
    e.position = entity.position
    e.rotation = entity.rotation.inverted()
    e.scale_xy = entity.scale_xy
    e.scale_z = entity.scale_z
    e.flags.total = str(entity.flags)
    e.guid = entity.guid
    e.parent_index = entity.parent_index
    e.lod_dist = entity.lod_dist
    e.child_lod_dist = entity.child_lod_dist
    e.lod_level = f"sollumz_lodtypes_depth_{entity.lod_level.name.lower()}"
    e.priority_level = f"sollumz_pri_{entity.priority_level.name.lower()}"
    e.num_children = entity.num_children
    e.ambient_occlusion_multiplier = entity.ambient_occlusion_multiplier
    e.artificial_ambient_occlusion = entity.artificial_ambient_occlusion
    e.tint_value = entity.tint_value

    find_and_link_entity_object(e)

    for extension in entity.extensions:
        create_extension(extension, e)

    return e


def find_and_link_entity_object(entity: MloEntityProperties):
    """Attempt to find an existing entity object in the scene and link it to the entity data-block.

    If the import setting ``ImportSettings.mlo_instance_entities`` is set, a copy of the found object is
    linked instead of the object itself.
    """

    should_instance = import_context().settings.mlo_instance_entities

    # Lookup in the whole .blend (i.e. current scene, other scenes, asset browser)
    obj = bpy.data.objects.get(entity.archetype_name, None)
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


def create_mlo_room(room: MloRoom, archetype: ArchetypeProperties) -> RoomProperties:
    """Create an MLO room from a definition for the provided archetype data-block."""
    r = archetype.new_room()
    r.name = room.name
    r.bb_min = room.bb_min
    r.bb_max = room.bb_max
    r.blend = room.blend
    r.timecycle = room.timecycle
    r.secondary_timecycle = room.secondary_timecycle
    r.flags.total = str(room.flags)
    r.floor_id = room.floor_id
    r.exterior_visibility_depth = room.exterior_visibility_depth
    for index in room.attached_objects:
        archetype.entities[index].attached_room_id = str(r.id)
    return r


def create_mlo_portal(portal: MloPortal, archetype: ArchetypeProperties) -> PortalProperties:
    """Create an MLO portal from a definition for the provided archetype data-block."""

    p = archetype.new_portal()
    p.corner1, p.corner2, p.corner3, p.corner4 = portal.corners
    p.room_from_id = str(archetype.rooms[portal.room_from].id)
    p.room_to_id = str(archetype.rooms[portal.room_to].id)
    p.flags.total = str(portal.flags)
    p.mirror_priority = portal.mirror_priority
    p.opacity = portal.opacity
    p.audio_occlusion = str(portal.audio_occlusion)
    for index in portal.attached_objects:
        archetype.entities[index].attached_portal_id = str(p.id)
    return p


def create_mlo_entity_set(entity_set: MloEntitySet, archetype: ArchetypeProperties) -> EntitySetProperties:
    """Create an MLO entity set from a definition for the provided archetype data-block."""
    s = archetype.new_entity_set()
    s.name = entity_set.name

    entity_set_id = str(s.id)
    assert len(entity_set.entities) == len(entity_set.locations)
    for entity, location in zip(entity_set.entities, entity_set.locations):
        e = create_mlo_entity(entity, archetype)
        e.attached_entity_set_id = entity_set_id

        if (location & (1 << 31)) != 0:
            # If MSB is set, the entity is attached to a portal
            location &= ~(1 << 31)  # clear MSB
            e.attached_portal_id = str(archetype.portals[location].id)
        else:
            e.attached_room_id = str(archetype.rooms[location].id)

    return s


def create_mlo_tcm(tcm: MloTimeCycleModifier, archetype: ArchetypeProperties) -> TimecycleModifierProperties:
    """Create an MLO timecycle modifier from a definition for the provided archetype data-block."""
    m = archetype.new_tcm()
    m.name = tcm.name
    m.sphere_center = tcm.sphere_center
    m.sphere_radius = tcm.sphere_radius
    m.percentage = max(0.0, min(100.0, tcm.percentage))
    m.range = tcm.range
    m.start_hour = tcm.start_hour
    m.end_hour = tcm.end_hour
    return m


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
        for child_obj in obj.children_recursive:  # could be slow with lots of entities, O(len(bpy.data.objects)) time
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


def create_extension(extension: Extension, extensions_container: ExtensionsContainer) -> ExtensionProperties:
    """Create an entity extension from the given extension definition."""
    extension_type = EXTENSION_DEF_CLASS_TO_TYPE[type(extension)]
    extension_props = extensions_container.new_extension(extension_type)
    set_extension_props(extension, extension_props)

    if extension_type == ExtensionType.LIGHT_EFFECT and not extensions_container.IS_ARCHETYPE:
        # Create the light objects from this light effect extension
        obj = extensions_container.linked_object
        armature_obj = obj if obj is not None and obj.type == "ARMATURE" else None

        from ..ydr.lights_io import create_light_objs
        lights_parent_obj = create_light_objs(extension.instances, armature_obj)
        lights_parent_obj.name = f"{extensions_container.archetype_name}.light_effect"
        if obj is not None:
            # Constraint instead of parenting for a simpler hierarchy
            # Also this way we don't need to distinguish between original lights and light effect lights.
            # Original ones will always be the lights children of the object.
            constraint = lights_parent_obj.constraints.new("COPY_TRANSFORMS")
            constraint.target = obj

        extension_props.light_effect_properties.linked_lights_object = lights_parent_obj

    return extension_props


def set_extension_props(extension_def: Extension, extension_props: ExtensionProperties):
    """Set extension data-block properties from the provided extension definition."""
    extension_props.name = extension_def.name
    extension_properties = extension_props.get_properties()
    extension_properties.offset_position = extension_def.offset_position

    if extension_props.extension_type == ExtensionType.LIGHT_EFFECT:
        # light instances creation not handled here
        return

    # Assumes extension definition and extension Blender properties classes have the same attribute names
    for prop_name in extension_def.__class__.__annotations__:
        prop_value = getattr(extension_def, prop_name)
        if prop_value is None:
            continue

        if isinstance(prop_value, Quaternion):
            prop_value = prop_value.to_euler()

        elif prop_name == "flashiness":
            # `flashiness` is now an enum property, we need the enum as string
            prop_value = prop_value.name

        setattr(extension_properties, prop_name, prop_value)
