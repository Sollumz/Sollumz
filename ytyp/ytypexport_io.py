from typing import Optional, Iterable
from bpy.types import (
    Scene,
)
from mathutils import Vector, Quaternion, Matrix, Euler
from szio.gta5 import (
    create_asset_map_types,
    AssetMapTypes,
    Archetype,
    ArchetypeType,
    ArchetypeAssetType,
    EntityLodLevel,
    EntityPriorityLevel,
    MloEntity,
    MloRoom,
    MloPortal,
    MloEntitySet,
    MloTimeCycleModifier,
    Extension,
    LightFlashiness,
)
from ..tools.meshhelper import (
    get_combined_bound_box,
    get_bound_center_from_bounds,
    get_sphere_radius,
)
from ..iecontext import export_context, ExportBundle
from .. import sollumz_properties as sz_props
from .properties.ytyp import (
    CMapTypesProperties,
    ArchetypeProperties,
    SpecialAttribute,
    MloEntityProperties,
    RoomProperties,
    PortalProperties,
    EntitySetProperties,
    TimecycleModifierProperties,
)
from .properties.extensions import ExtensionType, ExtensionProperties, EXTENSION_TYPE_TO_DEF_CLASS


def export_ytyp(scene: Scene, ytyp_index: int) -> ExportBundle:
    if 0 <= ytyp_index < len(scene.ytyps):
        ytyp = scene.ytyps[ytyp_index]
        map_types = create_map_types_asset(ytyp)
    else:
        map_types = None
    return export_context().make_bundle(map_types)


def create_map_types_asset(
    map_types: CMapTypesProperties,
) -> Optional[AssetMapTypes]:
    t = create_asset_map_types(export_context().settings.targets)
    t.name = map_types.name
    t.archetypes = [create_archetype(a) for a in map_types.archetypes]
    return t


def create_archetype(archetype: ArchetypeProperties) -> Archetype:
    """Create archetype asset from an archetype data block"""
    match archetype.type:
        case sz_props.ArchetypeType.TIME:
            arch_type = ArchetypeType.TIME
            extra_kwargs = {
                "time_flags": int(archetype.time_flags.total),
            }
        case sz_props.ArchetypeType.MLO:
            arch_type = ArchetypeType.MLO
            extra_kwargs = {
                "mlo_flags": int(archetype.mlo_flags.total),
                "entities": [create_mlo_entity(e, archetype) for e in archetype.non_entity_set_entities],
                "rooms": [create_mlo_room(r, archetype) for r in archetype.rooms],
                "portals": [create_mlo_portal(p, archetype) for p in archetype.portals],
                "entity_sets": [create_mlo_entity_set(s, archetype) for s in archetype.entity_sets],
                "timecycle_modifiers": [create_mlo_tcm(m) for m in archetype.timecycle_modifiers],
            }
        case _:
            arch_type = ArchetypeType.BASE
            extra_kwargs = {}

    bb_min, bb_max, bs_center, bs_radius = calc_archetype_bounds(archetype, export_context().settings.apply_transforms)

    return Archetype(
        name=archetype.name.lower(),
        type=arch_type,
        flags=int(archetype.flags.total),
        special_attribute=SpecialAttribute[archetype.special_attribute].value,
        lod_dist=archetype.lod_dist,
        hd_texture_dist=archetype.hd_texture_dist,
        texture_dictionary=archetype.texture_dictionary.lower(),
        clip_dictionary=archetype.clip_dictionary.lower(),
        drawable_dictionary=archetype.drawable_dictionary.lower(),
        physics_dictionary=archetype.physics_dictionary.lower(),
        asset_name=archetype.asset_name.lower(),
        asset_type=ArchetypeAssetType[sz_props.AssetType(archetype.asset_type).name],
        bb_min=bb_min,
        bb_max=bb_max,
        bs_center=bs_center,
        bs_radius=bs_radius,
        extensions=[create_extension(e) for e in archetype.extensions],
        **extra_kwargs,
    )


def calc_archetype_bounds_from_asset(archetype: ArchetypeProperties, apply_transforms: bool = False) -> tuple[Vector, Vector, Vector, float]:
    """Calculate bounds from the archetype asset."""

    if apply_transforms:
        # Unapply only translation
        matrix = Matrix.Translation(archetype.asset.matrix_world.translation).inverted()
    else:
        # Unapply all transforms
        matrix = archetype.asset.matrix_world.inverted()

    bb_min, bb_max = get_combined_bound_box(archetype.asset, use_world=True, matrix=matrix)
    bs_center = get_bound_center_from_bounds(bb_min, bb_max)
    bs_radius = get_sphere_radius(bb_min, bb_max)
    return bb_min, bb_max, bs_center, bs_radius


def calc_archetype_bounds(archetype: ArchetypeProperties, apply_transforms: bool = False) -> tuple[Vector, Vector, Vector, float]:
    if archetype.type == sz_props.ArchetypeType.MLO:
        return Vector(), Vector(), Vector(), 0.0

    if archetype.asset:
        return calc_archetype_bounds_from_asset(archetype, apply_transforms)

    return Vector(archetype.bb_min), Vector(archetype.bb_max), Vector(archetype.bs_center), archetype.bs_radius


def create_mlo_entity(entity: MloEntityProperties, archetype: ArchetypeProperties) -> MloEntity:
    """Create MLO entity definition from an entity data-block."""
    pos, rot, scale_xy, scale_z = calc_mlo_entity_transforms(entity, archetype)
    return MloEntity(
        archetype_name=entity.archetype_name,
        position=pos,
        rotation=rot,
        scale_xy=scale_xy,
        scale_z=scale_z,
        flags=int(entity.flags.total),
        guid=int(entity.guid),
        parent_index=entity.parent_index,
        lod_dist=entity.lod_dist,
        child_lod_dist=entity.child_lod_dist,
        lod_level=EntityLodLevel[entity.lod_level[len("sollumz_lodtypes_depth_"):].upper()],
        priority_level=EntityPriorityLevel[entity.priority_level[len("sollumz_pri_"):].upper()],
        num_children=entity.num_children,
        ambient_occlusion_multiplier=int(entity.ambient_occlusion_multiplier),
        artificial_ambient_occlusion=int(entity.artificial_ambient_occlusion),
        tint_value=int(entity.tint_value),
        extensions=[create_extension(e) for e in entity.extensions],
    )


def calc_mlo_entity_transforms_from_object(entity: MloEntityProperties, archetype: ArchetypeProperties) -> tuple[Vector, Quaternion, float, float]:
    """Get the transforms of an entity based on its linked Blender object."""
    transform: Matrix = entity.linked_object.matrix_world
    if archetype.asset is not None:
        # Get transform relative to MLO collisions object
        parent_transform_inv = archetype.asset.matrix_world.inverted()
        transform = parent_transform_inv @ transform
    location, rotation, scale = transform.decompose()

    return location, rotation.inverted(), scale.x, scale.z


def calc_mlo_entity_transforms(entity: MloEntityProperties, archetype: ArchetypeProperties) -> tuple[Vector, Quaternion, float, float]:
    if entity.linked_object is not None:
        return calc_mlo_entity_transforms_from_object(entity, archetype)

    return Vector(entity.position), Quaternion(entity.rotation.inverted()), entity.scale_xy, entity.scale_z


def create_mlo_room(room: RoomProperties, archetype: ArchetypeProperties) -> MloRoom:
    """Create MLO room definition from a room data-block."""
    return MloRoom(
        name=room.name,
        bb_min=room.bb_min,
        bb_max=room.bb_max,
        blend=room.blend,
        timecycle=room.timecycle,
        secondary_timecycle=room.secondary_timecycle,
        flags=int(room.flags.total),
        portal_count=calc_mlo_room_portal_count(room, archetype.portals),
        floor_id=room.floor_id,
        exterior_visibility_depth=room.exterior_visibility_depth,
        attached_objects=find_mlo_room_attached_objects(room, archetype.non_entity_set_entities),
    )


def calc_mlo_room_portal_count(room: RoomProperties, portals: Iterable[PortalProperties]) -> int:
    """Get number of portals in room."""
    room_id = str(room.id)
    return sum(1 for p in portals if p.room_from_id == room_id or p.room_to_id == room_id)


def find_mlo_room_attached_objects(room: RoomProperties, entities: Iterable[MloEntityProperties]) -> list[int]:
    """Gets indices of MLO entities attached to the room."""
    room_id = str(room.id)
    return [i for i, entity in enumerate(entities) if entity.attached_room_id == room_id]


def create_mlo_portal(portal: PortalProperties, archetype: ArchetypeProperties) -> MloPortal:
    """Create MLO portal definition from a portal data-block."""
    return MloPortal(
        room_from=portal.room_from_index,
        room_to=portal.room_to_index,
        flags=int(portal.flags.total),
        mirror_priority=portal.mirror_priority,
        opacity=portal.opacity,
        audio_occlusion=int(portal.audio_occlusion),
        corners=(portal.corner1, portal.corner2, portal.corner3, portal.corner4),
        attached_objects=find_mlo_portal_attached_objects(portal, archetype.non_entity_set_entities),
    )


def find_mlo_portal_attached_objects(portal: PortalProperties, entities: Iterable[MloEntityProperties]) -> list[int]:
    """Gets indices of MLO entities attached to the portal."""
    portal_id = str(portal.id)
    return [i for i, entity in enumerate(entities) if entity.attached_portal_id == portal_id]


def create_mlo_entity_set(entity_set: EntitySetProperties, archetype: ArchetypeProperties) -> MloEntitySet:
    """Create MLO entity set definition from an entity set data-block"""
    entities = []
    locations = []
    entity_set_id = str(entity_set.id)
    for entity in archetype.entities:
        if entity.attached_entity_set_id != entity_set_id:
            continue

        entities.append(create_mlo_entity(entity, archetype))

        location = entity.room_index
        if location == -1:
            # If not attached to a room, it should be attached to a portal. Set MSB to indicate this is a portal index
            location = entity.portal_index | (1 << 31)

        locations.append(location)

    return MloEntitySet(
        name=entity_set.name,
        locations=locations,
        entities=entities,
    )


def create_mlo_tcm(tcm: TimecycleModifierProperties) -> MloTimeCycleModifier:
    """Create a MLO timecycle modifier definition from a timecycle modifier data-block."""
    return MloTimeCycleModifier(
        name=tcm.name,
        sphere_center=Vector((tcm.sphere.x, tcm.sphere.y, tcm.sphere.z)),
        sphere_radius=tcm.sphere.w,
        percentage=tcm.percentage,
        range=tcm.range,
        start_hour=tcm.start_hour,
        end_hour=tcm.end_hour,
    )


def create_extension(extension: ExtensionProperties) -> Extension:
    """Create an extension definition from the given extension data-block."""
    extension_type = extension.extension_type
    extension_def_cls = EXTENSION_TYPE_TO_DEF_CLASS[extension_type]
    return extension_def_cls(**get_extension_props(extension, extension_def_cls))


def get_extension_props(extension: ExtensionProperties, extension_def_cls: type) -> dict:
    """Automatically get extension properties based on ExtensionProperties data-block."""
    extension_type = extension.extension_type
    extension_properties = extension.get_properties()

    props = {
        "name": extension.name,
        "offset_position": Vector(extension_properties.offset_position)
    }

    if extension_type == ExtensionType.LIGHT_EFFECT:
        if extension_properties.linked_lights_object is not None:
            # Get the light objects and add them to the extension
            lights_obj = extension.get_properties().linked_lights_object

            from ..ydr.lights_io import export_lights
            props["instances"] = export_lights(lights_obj)
    else:
        # Assumes extension definition and extension Blender properties classes have the same attribute names
        for prop_name in extension_def_cls.__annotations__:
            prop_value = getattr(extension_properties, prop_name)

            if isinstance(prop_value, Euler):
                prop_value = prop_value.to_quaternion()

            elif prop_name == "flashiness":
                # convert enum string back to enum
                prop_value = LightFlashiness[prop_value]

            props[prop_name] = prop_value

    return props
