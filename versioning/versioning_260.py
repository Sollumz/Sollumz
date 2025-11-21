"""Handle changes between 2.6.0 and 2.7.0."""

from bpy.types import (
    BlendData,
    Scene,
)


def update_archetype_uuids_in_scene(scene: Scene):
    from uuid import uuid4
    for ytyp in scene.ytyps:
        for arch in ytyp.archetypes_:
            arch_uuid = str(uuid4())
            arch.uuid = arch_uuid
            for e in arch.entities_:
                e.uuid = str(uuid4())
                e.mlo_archetype_uuid = arch_uuid
            for s in arch.entity_sets_:
                s.uuid = str(uuid4())
                s.mlo_archetype_uuid = arch_uuid
            for p in arch.portals_:
                p.uuid = str(uuid4())
                p.mlo_archetype_uuid = arch_uuid
            for r in arch.rooms_:
                r.uuid = str(uuid4())
                r.mlo_archetype_uuid = arch_uuid
            for t in arch.timecycle_modifiers_:
                t.mlo_archetype_uuid = arch_uuid


def update_archetype_multiselect_collections_in_scene(scene: Scene):
    """With multiselection the actual CollectionProperty is at 'propname_' while 'propname' is a regular Python
    property that returns a wrapper for more ergonomic use of multiselection collections.

    Rename the old CollectionProperties.
    """
    from .versioning_230 import unsafe_move_renamed_prop, get_src_props
    for ytyp in scene.ytyps:
        ytyp_props = get_src_props(ytyp)
        unsafe_move_renamed_prop(ytyp_props, "archetypes", "archetypes_")
        for arch in ytyp.archetypes_:
            arch_props = get_src_props(arch)
            unsafe_move_renamed_prop(arch_props, "rooms", "rooms_")
            unsafe_move_renamed_prop(arch_props, "portals", "portals_")
            unsafe_move_renamed_prop(arch_props, "entities", "entities_")
            unsafe_move_renamed_prop(arch_props, "timecycle_modifiers", "timecycle_modifiers_")
            unsafe_move_renamed_prop(arch_props, "entity_sets", "entity_sets_")


def do_versions(data_version: int, data: BlendData):
    if data_version < 8:
        # Do this first as we need the archetype collections moved over before the UUIDs versinong
        for scene in data.scenes:
            update_archetype_multiselect_collections_in_scene(scene)

    # NOTE: moved from versioning_240 as it needs to happen after the multi-select collections versioning
    if data_version < 3:
        from .versioning_240 import update_mlo_tcmods_percentage
        for scene in data.scenes:
            for ytyp in scene.ytyps:
                update_mlo_tcmods_percentage(ytyp)

    if data_version < 7:
        for scene in data.scenes:
            update_archetype_uuids_in_scene(scene)
