import json

import bpy
from bpy.props import (
    FloatProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import PropertyGroup, WindowManager
from numpy.testing import assert_allclose

from ...shared.multiselection import (
    MultiSelectAccess,
    MultiSelectCollection,
    MultiSelectProperty,
    define_multiselect_collection,
)
from ...shared.presets.serializer import dict_to_struct, struct_to_dict


class SzTestChild(PropertyGroup):
    value: FloatProperty(default=1.0)
    other_value: IntProperty(default=100)


class SzTestChildSelectionAccess(MultiSelectAccess):
    value: MultiSelectProperty()
    other_value: MultiSelectProperty()


@define_multiselect_collection("children", {"name": "Children"})
class SzTestParent(PropertyGroup):
    __sz_preset_capture__ = ("children",)

    name: StringProperty()
    children: MultiSelectCollection[SzTestChild, SzTestChildSelectionAccess]


_classes = (SzTestChild, SzTestParent)


def setup_module():
    for cls in _classes:
        bpy.utils.register_class(cls)

    WindowManager.sz_preset_serializer_test_parent = PointerProperty(type=SzTestParent)


def teardown_module():
    del WindowManager.sz_preset_serializer_test_parent

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


def _make_parent() -> SzTestParent:
    p = bpy.context.window_manager.sz_preset_serializer_test_parent
    p.name = "MyParent"
    p.children.clear()
    c1 = p.children.add()
    c1.value = 0.5
    c1.other_value = 10
    c2 = p.children.add()
    c2.value = 0.8
    c2.other_value = 20
    p.children.select(0)
    return p


def test_capture_multiselect_is_json_serializable():
    p = _make_parent()

    data = struct_to_dict(p)

    text = json.dumps(data)
    roundtripped = json.loads(text)

    assert list(roundtripped.keys()) == ["children"]
    children = roundtripped["children"]
    assert_allclose([c["value"] for c in children], [0.5, 0.8])
    assert_allclose([c["other_value"] for c in children], [10, 20])


def test_capture_only_whitelisted_fields():
    p = _make_parent()

    data = struct_to_dict(p)

    # __sz_preset_capture__ is ("children",) -> the name is not captured.
    assert "name" not in data


def test_apply_replaces_items_and_resets_selection():
    p = _make_parent()
    data = json.loads(json.dumps(struct_to_dict(p)))

    # Pre-existing content must be replaced, not appended to.
    p.children.clear()
    decoy = p.children.add()
    decoy.value = 123
    decoy.other_value = 123

    dict_to_struct(p, data)

    children = list(p.children)
    assert_allclose([c["value"] for c in children], [0.5, 0.8])
    assert_allclose([c["other_value"] for c in children], [10, 20])

    # Selection is reset to the first item.
    assert p.children.active_index == 0
    assert [s.index for s in p.children.selection_indices] == [0]


def test_apply_empty_list_clears_and_leaves_no_selection():
    p = _make_parent()

    dict_to_struct(p, {"children": []})

    assert len(p.children) == 0
    assert [s.index for s in p.children.selection_indices] == []
