import bpy
import pytest
from bpy.props import (
    PointerProperty,
    StringProperty,
)
from bpy.types import (
    Operator,
    PropertyGroup,
    WindowManager,
)
from numpy.testing import assert_equal

from ..shared.multiselection import (
    MultiSelectAccess,
    MultiSelectCollection,
    MultiSelectInvertOperator,
    MultiSelectProperty,
    define_multiselect_collection,
)


class SzTestItem(PropertyGroup):
    name: StringProperty(name="Name")


class SzTestItemSelectionAccess(MultiSelectAccess):
    name: MultiSelectProperty()


@define_multiselect_collection("coll", {"name": "Test Collection"})
class SzTestData(PropertyGroup):
    coll: MultiSelectCollection[SzTestItem, SzTestItemSelectionAccess]


def get_test_collection(context) -> MultiSelectCollection[SzTestItem, SzTestItemSelectionAccess]:
    return context.window_manager.sz_multiselection_test_data.coll


@pytest.fixture()
def test_collection(context):
    c = get_test_collection(context)
    c.clear()
    yield c
    c.clear()


class SOLLUMZTEST_OT_multiselect_test_data_invert(MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz_test.multiselect_test_data_invert"
    bl_label = "Test Invert"

    def get_collection(self, context):
        return get_test_collection(context)


_classes = (
    SzTestItem,
    SzTestData,
    SOLLUMZTEST_OT_multiselect_test_data_invert,
)


def setup_module():
    for cls in _classes:
        bpy.utils.register_class(cls)

    WindowManager.sz_multiselection_test_data = PointerProperty(type=SzTestData)


def teardown_module():
    del WindowManager.sz_multiselection_test_data

    for cls in reversed(_classes):
        bpy.utils.unregister_class(cls)


def test_multiselection_ops_invert(test_collection):
    coll = test_collection
    coll.add().name = "Item0"
    coll.add().name = "Item1"
    coll.add().name = "Item2"
    coll.add().name = "Item3"
    coll.select_many([1, 2])

    bpy.ops.sollumz_test.multiselect_test_data_invert()
    assert_equal(list(coll.iter_selected_items_indices()), [0, 3])

    bpy.ops.sollumz_test.multiselect_test_data_invert()
    assert_equal(list(coll.iter_selected_items_indices()), [1, 2])


def test_multiselection_ops_invert_with_filter(test_collection):
    coll = test_collection
    coll.add().name = "ItemA0"
    coll.add().name = "ItemB1"
    coll.add().name = "ItemA2"
    coll.add().name = "ItemB3"
    coll.select_many([0, 3])

    # should only select filtered items
    bpy.ops.sollumz_test.multiselect_test_data_invert(apply_filter=True, filter_name="ItemA")
    assert_equal(list(coll.iter_selected_items_indices()), [2])

    bpy.ops.sollumz_test.multiselect_test_data_invert(apply_filter=True, filter_name="ItemA")
    assert_equal(list(coll.iter_selected_items_indices()), [0])
