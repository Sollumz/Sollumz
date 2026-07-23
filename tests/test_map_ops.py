import bpy

from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_blender_object
from ..ymap_next.properties.map import get_maps

ALL_LOD_LEVELS = {"ORPHAN_HD", "HD", "LOD", "SLOD1", "SLOD2", "SLOD3", "SLOD4"}


def _new_group(name: str = "test_group"):
    maps = get_maps(bpy.context, create_if_missing=True)
    group = maps.new_group()
    group.name = name
    return group


def _add_entity(group, name: str, lod_level: str, parent_uuid: bytes = b"", linked: bool = True):
    """Creates an entity in `group`. Returns (entity uuid, linked object or None)."""
    e = group.new_entity()
    e.archetype_name = name
    e.lod_level = lod_level
    e.parent_uuid = parent_uuid
    obj = None
    if linked:
        obj = create_blender_object(SollumType.DRAWABLE_MODEL, name + "_obj")
        e.linked_object = obj
    return e.uuid, obj


def test_hide_entities_filters_by_lod_category():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    lod_uuid, lod_obj = _add_entity(group, "lod", "LOD")
    _, hd_obj = _add_entity(group, "hd", "HD", parent_uuid=lod_uuid)
    _, orphan_obj = _add_entity(group, "orphan", "HD")

    result = bpy.ops.sollumz.map_hide_entities(lod_levels={"ORPHAN_HD"}, scope="ACTIVE")

    assert result == {"FINISHED"}
    assert orphan_obj.hide_get()
    assert not hd_obj.hide_get()  # HD with a LOD parent is not ORPHAN_HD
    assert not lod_obj.hide_get()

    result = bpy.ops.sollumz.map_hide_entities(lod_levels={"HD", "LOD"}, scope="ACTIVE")

    assert result == {"FINISHED"}
    assert hd_obj.hide_get()
    assert lod_obj.hide_get()


def test_hide_entities_hides_child_objects():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    _, obj = _add_entity(group, "orphan", "HD")
    child_obj = create_blender_object(SollumType.NONE, "child_obj")
    child_obj.parent = obj

    result = bpy.ops.sollumz.map_hide_entities(lod_levels={"ORPHAN_HD"}, scope="ACTIVE")

    assert result == {"FINISHED"}
    assert obj.hide_get()
    assert child_obj.hide_get()


def test_show_entities():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    _, hidden_obj = _add_entity(group, "orphan", "HD")
    _, slod_obj = _add_entity(group, "slod", "SLOD2")
    hidden_obj.hide_set(True)
    slod_obj.hide_set(True)

    result = bpy.ops.sollumz.map_show_entities(lod_levels={"ORPHAN_HD"}, scope="ACTIVE")

    assert result == {"FINISHED"}
    assert not hidden_obj.hide_get()
    assert slod_obj.hide_get()  # not in the selected LOD levels, stays hidden


def test_hide_entities_no_levels_selected_is_cancelled():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    _, obj = _add_entity(group, "orphan", "HD")

    result = bpy.ops.sollumz.map_hide_entities(lod_levels=set(), scope="ACTIVE")

    assert result == {"CANCELLED"}
    assert not obj.hide_get()


def test_hide_entities_skips_entities_without_linked_object():
    bpy.ops.wm.read_homefile()

    group = _new_group()
    _add_entity(group, "no_obj", "SLOD1", linked=False)

    result = bpy.ops.sollumz.map_hide_entities(lod_levels=ALL_LOD_LEVELS, scope="ACTIVE")

    assert result == {"FINISHED"}


def test_hide_entities_scope():
    bpy.ops.wm.read_homefile()

    _, obj_a = _add_entity(_new_group("group_a"), "a", "HD")
    _, obj_b = _add_entity(_new_group("group_b"), "b", "HD")  # group_b becomes the active group

    result = bpy.ops.sollumz.map_hide_entities(lod_levels=ALL_LOD_LEVELS, scope="ACTIVE")

    assert result == {"FINISHED"}
    assert not obj_a.hide_get()  # only the active group is affected
    assert obj_b.hide_get()

    result = bpy.ops.sollumz.map_hide_entities(lod_levels=ALL_LOD_LEVELS, scope="ALL")

    assert result == {"FINISHED"}
    assert obj_a.hide_get()
    assert obj_b.hide_get()
