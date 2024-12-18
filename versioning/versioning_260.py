"""Handle changes between 2.6.0 and 2.7.0."""

from bpy.types import (
    BlendData,
    Scene,
)


def update_archetype_uuids_in_scene(scene: Scene):
    from uuid import uuid4
    for ytyp in scene.ytyps:
        for arch in ytyp.archetypes:
            arch.uuid = str(uuid4())
            for e in arch.entities:
                e.uuid = str(uuid4())
                e.mlo_archetype_uuid = arch.uuid
            for s in arch.entity_sets:
                s.uuid = str(uuid4())
                s.mlo_archetype_uuid = arch.uuid
            for p in arch.portals:
                p.uuid = str(uuid4())
                p.mlo_archetype_uuid = arch.uuid
            for r in arch.rooms:
                r.uuid = str(uuid4())
                r.mlo_archetype_uuid = arch.uuid
            for t in arch.timecycle_modifiers:
                t.mlo_archetype_uuid = arch.uuid


def do_versions(data_version: int, data: BlendData):
    if data_version < 7:
        for scene in data.scenes:
            update_archetype_uuids_in_scene(scene)
