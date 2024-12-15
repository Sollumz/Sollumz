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
            for s in arch.entity_sets:
                s.uuid = str(uuid4())
            for p in arch.portals:
                p.uuid = str(uuid4())
            for r in arch.rooms:
                r.uuid = str(uuid4())


def do_versions(data_version: int, data: BlendData):
    if data_version < 7:
        for scene in data.scenes:
            update_archetype_uuids_in_scene(scene)
