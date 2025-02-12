"""Handle changes between 2.6.0 and 2.7.0."""

from bpy.types import (
    BlendData,
    Scene,
)


def update_archetype_uuids_in_scene(scene: Scene):
    from uuid import uuid4
    for ytyp in scene.ytyps:
        for arch in ytyp.get("archetypes", []):
            arch_uuid = str(uuid4())
            arch["uuid"] = arch_uuid
            for e in arch.get("entities", []):
                e["uuid"] = str(uuid4())
                e["mlo_archetype_uuid"] = arch_uuid
            for s in arch.get("entity_sets", []):
                s["uuid"] = str(uuid4())
                s["mlo_archetype_uuid"] = arch_uuid
            for p in arch.get("portals", []):
                p["uuid"] = str(uuid4())
                p["mlo_archetype_uuid"] = arch_uuid
            for r in arch.get("rooms", []):
                r["uuid"] = str(uuid4())
                r["mlo_archetype_uuid"] = arch_uuid
            for t in arch.get("timecycle_modifiers", []):
                t["mlo_archetype_uuid"] = arch_uuid


def update_archetype_multiselect_collections_in_scene(scene: Scene):
    """With multiselection the actual CollectionProperty is at 'propname_' while 'propname' is a regular Python
    property that returns a wrapper for more ergonomic use of multiselection collections.

    Rename the old CollectionProperties.
    """
    from .versioning_230 import move_renamed_prop
    for ytyp in scene.ytyps:
        move_renamed_prop(ytyp, "archetypes", "archetypes_")
        for arch in ytyp.get("archetypes_", []):
            move_renamed_prop(arch, "rooms", "rooms_")
            move_renamed_prop(arch, "portals", "portals_")
            move_renamed_prop(arch, "entities", "entities_")
            move_renamed_prop(arch, "timecycle_modifiers", "timecycle_modifiers_")
            move_renamed_prop(arch, "entity_sets", "entity_sets_")


def do_versions(data_version: int, data: BlendData):
    if data_version < 7:
        for scene in data.scenes:
            update_archetype_uuids_in_scene(scene)

    if data_version < 8:
        for scene in data.scenes:
            update_archetype_multiselect_collections_in_scene(scene)
