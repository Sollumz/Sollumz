from typing import Iterable
import bpy
from mathutils import Euler, Vector, Quaternion

from ..cwxml import ytyp as ytypxml, ymap as ymapxml
from ..sollumz_properties import ArchetypeType, AssetType, EntityLodLevel, EntityPriorityLevel
from ..tools.meshhelper import get_bound_extents, get_bound_center, get_sphere_radius
from .properties.ytyp import ArchetypeProperties, TimecycleModifierProperties, RoomProperties, PortalProperties, MloEntityProperties, EntitySetProperties
from .properties.extensions import ExtensionProperties


def set_room_attached_objects(room_xml: ytypxml.Room, room_index: int, entities: Iterable[MloEntityProperties]):
    """Set attached objects of room from the mlo archetype entities collection provided."""

    for index, entity in enumerate(entities):
        if entity.room_index == room_index:
            room_xml.attached_objects.append(index)


def set_portal_attached_objects(portal_xml: ytypxml.Portal, portal_index: int, entities: Iterable[MloEntityProperties]):
    """Set attached objects of portal from the mlo archetype entities collection provided."""

    for index, entity in enumerate(entities):
        if entity.portal_index == portal_index:
            portal_xml.attached_objects.append(index)


def get_portal_count(room: RoomProperties, portals: Iterable[PortalProperties]) -> int:
    """Get number of portals in room."""

    count = 0
    for portal in portals:
        if portal.room_from_id == str(room.id) or portal.room_to_id == str(room.id):
            count += 1

    return count


def set_entity_xml_transforms_from_object(entity_obj: bpy.types.Object, entity_xml: ymapxml.Entity):
    """Set the transforms of an entity xml based on a Blender mesh object."""

    entity_xml.position = entity_obj.location
    entity_xml.rotation = entity_obj.rotation_euler.to_quaternion().inverted()
    entity_xml.scale_xy = entity_obj.scale.x
    entity_xml.scale_z = entity_obj.scale.z


def set_entity_xml_transforms(entity: MloEntityProperties, entity_xml: ymapxml.Entity):
    """Set the transforms of an entity xml based on the provided entity data-block."""

    entity_xml.position = Vector(entity.position)
    entity_xml.rotation = Quaternion(entity.rotation)
    entity_xml.scale_xy = entity.scale_xy
    entity_xml.scale_z = entity.scale_z


def set_portal_xml_corners(portal: PortalProperties, portal_xml: ytypxml.Portal):
    """Set all 4 corners of portal xml based on portal data-block."""

    for i in range(4):
        corner = getattr(portal, f"corner{i + 1}")
        corner_xml = ytypxml.Corner()
        corner_xml.value = corner
        portal_xml.corners.append(corner_xml)


def create_entity_set_xml(entityset: EntitySetProperties) -> ytypxml.EntitySet:
    """Create xml mlo entity sets from an entityset data-block"""
    entity_set = ytypxml.EntitySet()
    entity_set.name = entityset.name
    for entity in entityset.entities:
        entity_room_index = int(entity.attached_entity_set_room_id)-1
        entity_set.entities.append(create_entity_xml(entity))
        entity_set.locations.append(entity_room_index)
    return entity_set


def create_entity_xml(entity: MloEntityProperties) -> ymapxml.Entity:
    """Create xml mlo entity from an entity data-block."""

    entity_xml = ymapxml.Entity()
    entity_obj = entity.linked_object
    if entity_obj:
        set_entity_xml_transforms_from_object(entity_obj, entity_xml)
    else:
        set_entity_xml_transforms(entity, entity_xml)

    entity_xml.archetype_name = entity.archetype_name
    entity_xml.flags = entity.flags.total
    entity_xml.parent_index = entity.parent_index
    entity_xml.lod_dist = entity.lod_dist
    entity_xml.child_lod_dist = entity.child_lod_dist
    entity_xml.ambient_occlusion_multiplier = entity.ambient_occlusion_multiplier
    entity_xml.artificial_ambient_occlusion = entity.artificial_ambient_occlusion
    entity_xml.tint_value = entity.tint_value

    lod_level = next(name for name, value in vars(
        EntityLodLevel).items() if value == (entity.lod_level))
    priority_level = next(name for name, value in vars(
        EntityPriorityLevel).items() if value == (entity.priority_level))
    entity_xml.lod_level = lod_level
    entity_xml.priority_level = priority_level

    for extension in entity.extensions:
        extension_xml = create_extension_xml(extension)
        entity_xml.extensions.append(extension_xml)

    return entity_xml


def create_room_xml(room: RoomProperties, room_index: int, archetype: ArchetypeProperties) -> ytypxml.Room:
    """Create xml room from a room data-block."""

    room_xml = ytypxml.Room()
    room_xml.name = room.name
    room_xml.bb_min = room.bb_min
    room_xml.bb_max = room.bb_max
    room_xml.blend = room.blend
    room_xml.timecycle_name = room.timecycle
    room_xml.secondary_timecycle_name = room.secondary_timecycle
    room_xml.flags = room.flags.total
    room_xml.floor_id = room.floor_id
    room_xml.exterior_visibility_depth = room.exterior_visibility_depth
    room_xml.portal_count = get_portal_count(
        room, archetype.portals)

    set_room_attached_objects(
        room_xml, room_index, archetype.entities)

    return room_xml


def create_portal_xml(portal: PortalProperties, portal_index: int, archetype: ArchetypeProperties) -> ytypxml.Portal:
    """Create xml portal from a portal data-block."""

    portal_xml = ytypxml.Portal()

    set_portal_xml_corners(portal, portal_xml)

    portal_xml.room_from = portal.room_from_index
    portal_xml.room_to = portal.room_to_index
    portal_xml.flags = portal.flags.total
    portal_xml.mirror_priority = portal.mirror_priority
    portal_xml.opacity = portal.opacity
    portal_xml.audio_occlusion = int(
        portal.audio_occlusion)

    set_portal_attached_objects(
        portal_xml, portal_index, archetype.entities)

    return portal_xml


def create_tcm_xml(tcm: TimecycleModifierProperties) -> ytypxml.TimeCycleModifier:
    """Create a xml timecycle modifier from a timecycle modifier data-block."""

    tcm_xml = ytypxml.TimeCycleModifier()
    tcm_xml.name = tcm.name
    tcm_xml.sphere = tcm.sphere
    tcm_xml.percentage = tcm.percentage
    tcm_xml.range = tcm.range
    tcm_xml.start_hour = tcm.start_hour
    tcm_xml.end_hour = tcm.end_hour

    return tcm_xml


def set_extension_xml_props(extension: ExtensionProperties, extension_xml: ymapxml.Extension):
    """Automatically set extension xml properties based on BaseExtensionProperties data-block."""
    extension_xml.name = extension.name
    extension_properties = extension.get_properties()

    extension_xml.offset_position = Vector(
        extension_properties.offset_position)

    for prop_name in extension_properties.__class__.__annotations__:
        if not hasattr(extension_xml, prop_name):
            # Unknown prop name. Need warning
            print(
                f"Unknown {extension.extension_type} prop name '{prop_name}'.")
            continue

        prop_value = getattr(extension_properties, prop_name)

        if isinstance(prop_value, Euler):
            prop_value = prop_value.to_quaternion()

        setattr(extension_xml, prop_name, prop_value)


def create_extension_xml(extension: ExtensionProperties):
    """Create an entity extension from the given extension xml."""

    extension_type = extension.extension_type
    extension_xml_class = ymapxml.ExtensionsList.get_extension_xml_class_from_type(
        extension_type)

    if extension_xml_class is None:
        # Warning needed here. Unknown extension type
        print(f"Unknown extension type {extension_type}")
        return None

    extension_xml = extension_xml_class()

    set_extension_xml_props(extension, extension_xml)

    return extension_xml


def set_archetype_xml_bounds_from_asset(archetype: ArchetypeProperties, archetype_xml: ytypxml.BaseArchetype):
    """Calculate bounds from the archetype asset."""

    bbmin, bbmax = get_bound_extents(archetype.asset)
    archetype_xml.bb_min = bbmin
    archetype_xml.bb_max = bbmax
    archetype_xml.bs_center = get_bound_center(archetype.asset)
    archetype_xml.bs_radius = get_sphere_radius(bbmax, archetype_xml.bs_center)


def set_archetype_xml_bounds(archetype: ArchetypeProperties, archetype_xml: ytypxml.BaseArchetype):
    """Set archetype xml bounds from archetype data-block bounds."""

    if archetype.asset:
        set_archetype_xml_bounds_from_asset(archetype, archetype_xml)
        return

    archetype_xml.bb_min = Vector(archetype.bb_min)
    archetype_xml.bb_max = Vector(archetype.bb_max)
    archetype_xml.bs_center = Vector(archetype.bs_center)
    archetype_xml.bs_radius = archetype.bs_radius


def get_xml_asset_type(asset_type: AssetType) -> str:
    """Get xml asset type string from AssetType enum."""

    if asset_type == AssetType.UNITIALIZED:
        return "ASSET_TYPE_UNINITIALIZED"
    elif asset_type == AssetType.FRAGMENT:
        return "ASSET_TYPE_FRAGMENT"
    elif asset_type == AssetType.DRAWABLE:
        return "ASSET_TYPE_DRAWABLE"
    elif asset_type == AssetType.DRAWABLE_DICTIONARY:
        return "ASSET_TYPE_DRAWABLEDICTIONARY"
    elif asset_type == AssetType.ASSETLESS:
        return "ASSET_TYPE_ASSETLESS"


def create_mlo_archetype_children_xml(archetype: ArchetypeProperties, archetype_xml: ytypxml.MloArchetype):
    """Create all mlo children from an archetype data-block for the provided archetype xml."""

    for entity in archetype.entities:
        archetype_xml.entities.append(create_entity_xml(entity))

    for room_index, room in enumerate(archetype.rooms):
        archetype_xml.rooms.append(
            create_room_xml(room, room_index, archetype))

    for portal_index, portal in enumerate(archetype.portals):
        archetype_xml.portals.append(
            create_portal_xml(portal, portal_index, archetype))

    for tcm in archetype.timecycle_modifiers:
        archetype_xml.timecycle_modifiers.append(create_tcm_xml(tcm))

    for entityset in archetype.entity_sets:
        archetype_xml.entity_sets.append(create_entity_set_xml(entityset))


def create_archetype_xml(archetype: ArchetypeProperties) -> ytypxml.BaseArchetype:
    """Create archetype xml from an archetype data block"""

    archetype_xml = None

    if archetype.type == ArchetypeType.MLO:
        archetype_xml = ytypxml.MloArchetype()
        create_mlo_archetype_children_xml(archetype, archetype_xml)
    else:
        if archetype.type == ArchetypeType.TIME:
            archetype_xml = ytypxml.TimeArchetype()
            archetype_xml.time_flags = archetype.time_flags.total
        else:
            archetype_xml = ytypxml.BaseArchetype()
        set_archetype_xml_bounds(archetype, archetype_xml)

    archetype_xml.lod_dist = archetype.lod_dist
    archetype_xml.flags = archetype.flags.total
    archetype_xml.special_attribute = archetype.special_attribute
    archetype_xml.hd_texture_dist = archetype.hd_texture_dist
    archetype_xml.name = archetype.name.lower()
    archetype_xml.texture_dictionary = archetype.texture_dictionary.lower()
    archetype_xml.clip_dictionary = archetype.clip_dictionary
    archetype_xml.drawable_dictionary = archetype.drawable_dictionary.lower()
    archetype_xml.physics_dictionary = archetype.physics_dictionary.lower()
    archetype_xml.asset_name = archetype.asset_name.lower()
    archetype_xml.asset_type = get_xml_asset_type(archetype.asset_type)

    for extension in archetype.extensions:
        extension_xml = create_extension_xml(extension)
        archetype_xml.extensions.append(extension_xml)

    return archetype_xml


def selected_ytyp_to_xml() -> ytypxml.CMapTypes:
    """Create a ytyp xml from the selected ytyp data-block."""

    selected_ytyp = bpy.context.scene.ytyps[bpy.context.scene.ytyp_index]
    ytyp = ytypxml.CMapTypes()
    ytyp.name = selected_ytyp.name

    for archetype in selected_ytyp.archetypes:
        archetype_xml = create_archetype_xml(archetype)
        ytyp.archetypes.append(archetype_xml)

    return ytyp
