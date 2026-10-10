import bpy

from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_blender_object
from ..ymap_next.data_revision import entities_revision
from ..ymap_next.overlays import lod_hierarchy
from ..ymap_next.overlays.lod_hierarchy import E_POS, E_VISUAL, LodHierarchyOverlayDrawHandler
from ..ymap_next.properties.map import get_maps


def _new_group(name: str = "test_group"):
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = name
    return group


def _add_entity(group, name: str, lod_level: str, parent_uuid: bytes = b"", linked: bool = True):
    """Creates an entity in `group`. Returns (entity, linked object or None)."""
    e = group.new_entity()
    e.archetype_name = name
    e.lod_level = lod_level
    e.parent_uuid = parent_uuid
    obj = None
    if linked:
        obj = create_blender_object(SollumType.DRAWABLE_MODEL, name + "_obj")
        e.linked_object = obj
    return e, obj


def test_new_entity_bumps_revision():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    before = entities_revision()
    group.new_entity()

    assert entities_revision() != before


def test_editing_entity_bumps_revision():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    lod, _ = _add_entity(group, "lod", "LOD")
    lod_uuid = lod.uuid  # read before the next new_entity() invalidates `lod`
    hd, _ = _add_entity(group, "hd", "HD")

    # Each property the LOD hierarchy overlay draws must invalidate its cached snapshot
    for apply_change in (
        lambda: setattr(hd, "parent_uuid", lod_uuid),
        lambda: setattr(hd, "lod_level", "LOD"),
        lambda: setattr(hd, "archetype_name", "renamed"),
        lambda: setattr(hd, "position", (1.0, 2.0, 3.0)),
        lambda: setattr(hd, "linked_object", None),
    ):
        before = entities_revision()
        apply_change()
        assert entities_revision() != before


def test_delete_entity_bumps_revision():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    _add_entity(group, "hd", "HD", linked=False)
    group.entities.select(0)

    before = entities_revision()
    result = bpy.ops.sollumz.map_group_delete_entity()

    assert result == {"FINISHED"}
    assert entities_revision() != before


def test_entity_cache_follows_lod_parent_changes():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    lod, _ = _add_entity(group, "lod", "LOD", linked=False)
    lod_uuid = lod.uuid  # read before the next new_entity() invalidates `lod`
    hd, _ = _add_entity(group, "hd", "HD", linked=False)

    handler = LodHierarchyOverlayDrawHandler()
    handler._rebuild_entity_cache(group)

    assert handler.entities[1][E_VISUAL] == "ORPHAN_HD"

    # Linking the HD entity to a LOD parent must be picked up by the overlay (issue #1226)
    group.set_entity_parent(hd, lod_uuid)
    handler._rebuild_entity_cache(group)

    assert handler.entities[1][E_VISUAL] == "HD"
    assert handler._children_by_parent[lod_uuid] == [1]


def test_refresh_positions_follows_linked_object():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    _, obj = _add_entity(group, "hd", "HD")

    handler = LodHierarchyOverlayDrawHandler()
    handler._rebuild_entity_cache(group)

    assert not handler.refresh_positions()  # nothing moved yet

    obj.location = (10.0, 20.0, 30.0)
    bpy.context.view_layer.update()

    assert handler.refresh_positions()
    assert handler.entities[0][E_POS] == (10.0, 20.0, 30.0)


def test_depsgraph_update_refreshes_moved_linked_object():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    _, obj = _add_entity(group, "hd", "HD")
    bpy.context.view_layer.update()  # flush the object creation so it doesn't invalidate the cache below

    handler = lod_hierarchy._active_handler
    handler._rebuild_entity_cache(group)

    # The depsgraph handler receives evaluated IDs, which must be mapped back to the original objects
    obj.location = (10.0, 20.0, 30.0)
    bpy.context.view_layer.update()

    assert handler.entities[0][E_POS] == (10.0, 20.0, 30.0)


def test_invalidate_cache_drops_references():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    _add_entity(group, "hd", "HD")

    handler = LodHierarchyOverlayDrawHandler()
    handler._rebuild_entity_cache(group)
    assert handler.entities

    handler.invalidate_cache()

    assert not handler.entities
    assert not handler.uuid_to_idx
    assert not handler._children_by_parent
