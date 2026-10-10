"""Tests for Sollumz parent lookup and the parent transforms unapplied on export (sollumz_helper)."""

import bpy
import pytest
from mathutils import Vector

from ..iecontext import ExportContext, ExportSettings, export_context_scope
from ..sollumz_helper import find_sollumz_parent, get_parent_inverse
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_blender_object, create_empty_object


def _drawable_with_model(parent=None):
    drawable = create_empty_object(SollumType.DRAWABLE, "drawable")
    drawable.parent = parent
    model = create_blender_object(SollumType.DRAWABLE_MODEL, "model")
    model.parent = drawable
    return drawable, model


def _export_scope(apply_transforms: bool = False):
    return export_context_scope(ExportContext("test", ExportSettings(targets=(), apply_transforms=apply_transforms)))


def test_find_sollumz_parent_untyped_returns_root():
    dwd = create_empty_object(SollumType.DRAWABLE_DICTIONARY, "dwd")
    _, model = _drawable_with_model(parent=dwd)

    assert find_sollumz_parent(model) == dwd


def test_find_sollumz_parent_typed_returns_closest_ancestor():
    dwd = create_empty_object(SollumType.DRAWABLE_DICTIONARY, "dwd")
    drawable, model = _drawable_with_model(parent=dwd)

    assert find_sollumz_parent(model, SollumType.DRAWABLE) == drawable
    assert find_sollumz_parent(drawable, SollumType.DRAWABLE) == drawable
    assert find_sollumz_parent(model, SollumType.DRAWABLE_DICTIONARY) == dwd
    assert find_sollumz_parent(model, SollumType.FRAGMENT) is None


def test_drawable_location_is_unapplied():
    drawable, model = _drawable_with_model()
    drawable.location = Vector((1.0, 2.0, 3.0))

    bpy.context.view_layer.update()

    with _export_scope():
        assert (get_parent_inverse(model) @ model.matrix_world).translation == Vector()


def test_drawable_in_dictionary_location_is_unapplied():
    dwd = create_empty_object(SollumType.DRAWABLE_DICTIONARY, "dwd")
    dwd.location = Vector((10.0, 0.0, 0.0))
    drawable, model = _drawable_with_model(parent=dwd)
    drawable.location = Vector((1.0, 2.0, 3.0))

    bpy.context.view_layer.update()

    with _export_scope():
        assert (get_parent_inverse(model) @ model.matrix_world).translation == Vector()


@pytest.mark.parametrize("apply_transforms", (False, True))
def test_drawable_rotation_is_unapplied_based_on_export_settings(apply_transforms: bool):
    drawable, model = _drawable_with_model()
    drawable.rotation_euler = (0.0, 0.0, 0.7)

    bpy.context.view_layer.update()

    with _export_scope(apply_transforms):
        transforms = get_parent_inverse(model) @ model.matrix_world

    assert transforms.to_euler().z == pytest.approx(0.7 if apply_transforms else 0.0)
