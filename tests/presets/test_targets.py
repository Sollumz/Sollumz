"""Tests for multi-target preset resolution."""

from types import SimpleNamespace

import bpy
from bpy.props import IntProperty, PointerProperty
from bpy.types import PropertyGroup, WindowManager

from ...shared.multiselection import (
    MultiSelectAccess,
    MultiSelectCollection,
    MultiSelectProperty,
    SelectMode,
    define_multiselect_collection,
)
from ...shared.presets.core import (
    PresetCategory,
    make_get_targets_from_collection,
    make_get_targets_from_objects,
)


def _category(**kwargs) -> PresetCategory:
    return PresetCategory(id="testcat", label="Test", game="testgame", **kwargs)


def test_iter_targets_falls_back_to_single_get_target():
    cat = _category(get_target=lambda ctx: "A")
    assert cat.iter_targets(None) == ["A"]


def test_iter_targets_single_none_yields_empty():
    cat = _category(get_target=lambda ctx: None)
    assert cat.iter_targets(None) == []


def test_iter_targets_prefers_category_get_targets():
    cat = _category(get_target=lambda ctx: "active", get_targets=lambda ctx: ["a", "b", "c"])
    assert cat.iter_targets(None) == ["a", "b", "c"]


def test_iter_targets_filters_none_from_get_targets():
    cat = _category(get_targets=lambda ctx: ["a", None, "b", None])
    assert cat.iter_targets(None) == ["a", "b"]


def test_iter_targets_get_targets_override_wins_over_category():
    cat = _category(get_target=lambda ctx: "active", get_targets=lambda ctx: ["cat"])
    result = cat.iter_targets(None, get_targets_override=lambda ctx: ["op1", "op2"])
    assert result == ["op1", "op2"]


def test_iter_targets_get_target_override_used_for_single_fallback():
    cat = _category(get_target=lambda ctx: "cat")
    result = cat.iter_targets(None, get_target_override=lambda ctx: "op")
    assert result == ["op"]


class _Obj:
    """Mock for a Blender Object."""

    def __init__(self, target=None):
        self.target = target


def test_make_get_targets_from_objects_maps_selected_then_active():
    o1, o2, o3 = _Obj(), _Obj(), _Obj()
    ctx = SimpleNamespace(selected_objects=[o1, o2], active_object=o3)
    assert make_get_targets_from_objects(lambda o: o)(ctx) == [o1, o2, o3]


def test_make_get_targets_from_objects_active_already_selected_not_duplicated():
    o1, o2 = _Obj(), _Obj()
    ctx = SimpleNamespace(selected_objects=[o1, o2], active_object=o1)
    assert make_get_targets_from_objects(lambda o: o)(ctx) == [o1, o2]


def test_make_get_targets_from_objects_drops_none_and_dedups_shared_target():
    shared = object()
    o1, o2, o3 = _Obj(shared), _Obj(shared), _Obj(None)
    ctx = SimpleNamespace(selected_objects=[o1, o2, o3], active_object=None)
    assert make_get_targets_from_objects(lambda o: o.target)(ctx) == [shared]


def test_make_get_targets_from_objects_empty_when_no_objects():
    ctx = SimpleNamespace(selected_objects=[], active_object=None)
    assert make_get_targets_from_objects(lambda o: o)(ctx) == []


class SzTargetsItem(PropertyGroup):
    value: IntProperty()


class SzTargetsItemSelectionAccess(MultiSelectAccess):
    value: MultiSelectProperty()


@define_multiselect_collection("items", {"name": "Items"})
class SzTargetsParent(PropertyGroup):
    items: MultiSelectCollection[SzTargetsItem, SzTargetsItemSelectionAccess]


_classes = (SzTargetsItem, SzTargetsParent)


def setup_module():
    for cls in _classes:
        bpy.utils.register_class(cls)
    WindowManager.sz_targets_test_parent = PointerProperty(type=SzTargetsParent)


def teardown_module():
    del WindowManager.sz_targets_test_parent
    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


def _make_parent(values) -> SzTargetsParent:
    p = bpy.context.window_manager.sz_targets_test_parent
    p.items.clear()
    for v in values:
        p.items.add().value = v
    return p


def test_make_get_targets_from_collection_yields_each_selected_item():
    p = _make_parent([10, 20, 30])
    p.items.select(0)
    p.items.select(2, mode=SelectMode.EXTEND)  # selects 0..2

    targets = make_get_targets_from_collection(lambda ctx: p.items)(None)

    assert sorted(t.value for t in targets) == [10, 20, 30]


def test_make_get_targets_from_collection_single_selection_is_active_only():
    p = _make_parent([10, 20, 30])
    p.items.select(1)

    targets = make_get_targets_from_collection(lambda ctx: p.items)(None)

    assert [t.value for t in targets] == [20]


def test_make_get_targets_from_collection_none_collection_yields_empty():
    assert make_get_targets_from_collection(lambda ctx: None)(None) == []


def test_make_get_targets_from_collection_transform_maps_and_skips_none():
    p = _make_parent([10, 20, 30])
    p.items.select(0)
    p.items.select(2, mode=SelectMode.EXTEND)

    out = make_get_targets_from_collection(
        lambda ctx: p.items,
        transform=lambda it: it.value if it.value != 20 else None,
    )(None)

    assert sorted(out) == [10, 30]
