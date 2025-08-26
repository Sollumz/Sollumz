import bpy
from bpy.types import (
    Object,
    Scene,
    Depsgraph,
)
from typing import Sequence
from contextlib import contextmanager
from .properties.ytyp import ArchetypeType

_suppress_sync = False
_suppress_sync_once = False
_last_selection_hash = None


@contextmanager
def suppress_sync_selection_context():
    global _suppress_sync
    _suppress_sync = True
    try:
        yield
    finally:
        _suppress_sync = False


def suppress_next_sync_selection():
    global _suppress_sync_once
    _suppress_sync_once = True


def sync_selection(scene: Scene, active: Object, selected: Sequence[Object]):
    def _root_parent(obj: Object) -> Object:
        while p := obj.parent:
            obj = p
        return obj

    active_obj = active and _root_parent(active)
    all_objects = set(_root_parent(o) for o in selected)
    all_objects.add(active_obj)

    sync_archetypes = scene.sz_sync_archetypes_selection
    sync_entities = scene.sz_sync_mlo_entities_selection

    for ytyp_idx, ytyp in enumerate(scene.ytyps):
        arch_indices = []
        for arch_idx, arch in enumerate(ytyp.archetypes):
            arch_obj = arch.asset
            if sync_archetypes and arch_obj and arch_obj in all_objects:
                if arch_obj == active_obj:
                    arch_indices.insert(0, arch_idx)  # first is the active object
                else:
                    arch_indices.append(arch_idx)

            if not sync_entities or arch.type != ArchetypeType.MLO:
                continue

            entity_indices = []
            for entity_idx, entity in enumerate(arch.entities):
                entity_obj = entity.linked_object
                if entity_obj and entity_obj in all_objects:
                    if entity_obj == active_obj:
                        entity_indices.insert(0, entity_idx)  # first is the active object
                    else:
                        entity_indices.append(entity_idx)

            if entity_indices:
                scene.ytyp_index = ytyp_idx
                ytyp.archetypes.select(arch_idx)
                arch.entities.select_many(entity_indices)
                arch_indices.clear()  # entities in a MLO have priority for selection
                return  # assume all selection belong to the same MLO and exit early

        if arch_indices:
            scene.ytyp_index = ytyp_idx
            ytyp.archetypes.select_many(arch_indices)
            return


@bpy.app.handlers.persistent
def depsgraph_update_post_handler(scene: Scene, depsgraph: Depsgraph):
    # Exit early if there is not map types in the scene
    if not scene.ytyps:
        return

    # Filter out unwanted depsgraph updates. When the selection changes, there is a single update entry
    # containing the scene. Other updates may look the same but can't check much more to differentiate them.
    scene_update = len(depsgraph.updates) == 1 and depsgraph.id_type_updated("SCENE")
    if not scene_update:
        return

    # Exit early if selection sync is disabled
    if not scene.sz_sync_archetypes_selection and not scene.sz_sync_mlo_entities_selection:
        return

    active = depsgraph.view_layer.objects.active
    selected = depsgraph.view_layer.objects.selected

    # Build a hash of the selection state to avoid repeated syncing in too many unnecessary/incorrect cases
    global _last_selection_hash
    prev_selection_hash = _last_selection_hash
    selection_hash = hash((active, *selected))
    _last_selection_hash = selection_hash

    if _suppress_sync:
        return

    global _suppress_sync_once
    if _suppress_sync_once:
        _suppress_sync_once = False
        return

    if selection_hash != prev_selection_hash:
        sync_selection(scene, active, selected)


def register():
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)
