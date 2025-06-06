import bpy
from bpy.types import (
    Object,
    Scene,
    Depsgraph,
)
from typing import Sequence
from contextlib import contextmanager
from .utils import get_selected_ytyp
from .properties.ytyp import ArchetypeType

_suppress_sync = False
_suppress_sync_once = False


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


def sync_selection(active: Object, selected: Sequence[Object]):
    def _root_parent(obj: Object) -> Object:
        p = obj.parent
        return _root_parent(p) if p else obj

    active_obj = _root_parent(active)
    all_objects = set(_root_parent(o) for o in selected)
    all_objects.add(active_obj)

    context = bpy.context
    scene = context.scene
    sync_archetypes = scene.sz_sync_archetypes_selection
    sync_entities = scene.sz_sync_mlo_entities_selection

    ytyp = get_selected_ytyp(bpy.context)
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
            ytyp.archetypes.select(arch_idx)
            arch.entities.select_many(entity_indices)
            arch_indices.clear()  # entities in a MLO have priority for selection
            break  # assume all selection belong to the same MLO and break early

    if arch_indices:
        ytyp.archetypes.select_many(arch_indices)


@bpy.app.handlers.persistent
def depsgraph_update_post_handler(scene: Scene, depsgraph: Depsgraph):
    # Filter out unwanted depsgraph updates. When the selection changes, there is a single update entry
    # containing the scene. Other updates may look the same but can't check much more to differentiate them.
    scene_update = len(depsgraph.updates) == 1 and depsgraph.id_type_updated("SCENE")
    if not scene_update:
        return

    # Exit early if selection sync is disabled
    if not scene.sz_sync_archetypes_selection and not scene.sz_sync_mlo_entities_selection:
        return

    if _suppress_sync:
        return

    global _suppress_sync_once
    if _suppress_sync_once:
        _suppress_sync_once = False
        return

    active = depsgraph.view_layer.objects.active
    selected = depsgraph.view_layer.objects.selected
    sync_selection(active, selected)


def register():
    bpy.app.handlers.depsgraph_update_post.append(depsgraph_update_post_handler)


def unregister():
    bpy.app.handlers.depsgraph_update_post.remove(depsgraph_update_post_handler)
