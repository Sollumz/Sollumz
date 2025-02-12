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


def do_versions(data_version: int, data: BlendData):
    if data_version < 7:
        for scene in data.scenes:
            update_archetype_uuids_in_scene(scene)
