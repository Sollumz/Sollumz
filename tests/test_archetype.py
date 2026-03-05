import bpy
import pytest

from ..sollumz_properties import AssetType
from .shared import (
    assert_logs_no_warnings_or_errors,
    load_blend_data,
)


# fmt: off
@pytest.mark.parametrize(
    "object_to_select,expected_asset_object_name,expected_asset_type,expected_drawable_dictionary",
    (
        ("test_drawable",                 "test_drawable",          AssetType.DRAWABLE, ""),
        ("test_drawable.model",           "test_drawable",          AssetType.DRAWABLE, ""),
        ("test_drawable_bound_composite", "test_drawable",          AssetType.DRAWABLE, ""),
        ("test_drawable_bound",           "test_drawable",          AssetType.DRAWABLE, ""),
        ("test_child_drawable_01",        "test_child_drawable_01", AssetType.DRAWABLE_DICTIONARY, "test_drawable_dictionary"),
        ("test_child_drawable_01.model",  "test_child_drawable_01", AssetType.DRAWABLE_DICTIONARY, "test_drawable_dictionary"),
        ("test_child_drawable_02",        "test_child_drawable_02", AssetType.DRAWABLE_DICTIONARY, "test_drawable_dictionary"),
        ("test_child_drawable_02.model",  "test_child_drawable_02", AssetType.DRAWABLE_DICTIONARY, "test_drawable_dictionary"),
        ("test_fragment",                 "test_fragment",          AssetType.FRAGMENT, ""),
        ("test_fragment.drawable",        "test_fragment",          AssetType.FRAGMENT, ""),
        ("test_fragment.model",           "test_fragment",          AssetType.FRAGMENT, ""),
        ("test_bound_composite",          "test_bound_composite",   AssetType.ASSETLESS, ""),
        ("test_bound",                    "test_bound_composite",   AssetType.ASSETLESS, ""),
    ),
)
# fmt: on
@assert_logs_no_warnings_or_errors
def test_archetype_auto_create_select_single(
    object_to_select: str, expected_asset_object_name: str, expected_asset_type: AssetType, expected_drawable_dictionary: str
):
    data = load_blend_data("archetypes.blend")

    bpy.ops.sollumz.createytyp()

    bpy.ops.object.select_all(action="DESELECT")
    data.objects[object_to_select].select_set(True)

    bpy.ops.sollumz.createarchetypefromselected()

    ytyp = bpy.context.scene.ytyps[0]
    archetypes = ytyp.archetypes
    assert len(archetypes) == 1

    archetype = archetypes[0]
    assert archetype.name == expected_asset_object_name
    assert archetype.asset == data.objects[expected_asset_object_name]
    assert archetype.asset_type == expected_asset_type
    assert archetype.drawable_dictionary == expected_drawable_dictionary


@assert_logs_no_warnings_or_errors
def test_archetype_auto_create_select_all():
    load_blend_data("archetypes.blend")

    bpy.ops.sollumz.createytyp()

    bpy.ops.object.select_all(action="SELECT")

    bpy.ops.sollumz.createarchetypefromselected()

    ytyp = bpy.context.scene.ytyps[0]
    archetypes = ytyp.archetypes
    assert len(archetypes) == 5
    assert any(a.name == "test_drawable" for a in archetypes)
    assert any(a.name == "test_child_drawable_01" for a in archetypes)
    assert any(a.name == "test_child_drawable_02" for a in archetypes)
    assert any(a.name == "test_fragment" for a in archetypes)
    assert any(a.name == "test_bound_composite" for a in archetypes)
