"""Monotonic revision counter for the map entity data that viewport overlays cache.

Overlays (e.g. the LOD hierarchy overlay) snapshot entity properties into GPU batches and only
rebuild that snapshot when something changed. Blender does not notify us when an item of a
``PropertyGroup`` collection is mutated, and the number of entities alone is not enough to detect
a change (relinking, changing the LOD level or deleting-and-adding entities all keep the count),
so every mutation of the properties the snapshots depend on bumps this counter instead.

The counter is session state, not file state: it is not saved and not restored by undo, so undo /
redo / file load must bump it too (see the overlay handlers).
"""

_entities_revision: int = 0


def entities_revision() -> int:
    """Current revision of the map entity data. Cheap enough to query on every redraw."""
    return _entities_revision


def notify_entities_changed() -> None:
    """Signal that map entity data changed, so overlay caches derived from it are rebuilt."""
    global _entities_revision
    _entities_revision += 1
