import bpy

from ..tools.blenderhelper import temporarily_unhide_all


def test_temporarily_unhide_all_restores_visibility():
    bpy.ops.wm.read_homefile()
    context = bpy.context

    parent_coll = bpy.data.collections.new("parent")
    child_coll = bpy.data.collections.new("child")
    context.scene.collection.children.link(parent_coll)
    parent_coll.children.link(child_coll)

    hidden_obj = bpy.data.objects.new("hidden", None)
    disabled_obj = bpy.data.objects.new("disabled", None)
    excluded_obj = bpy.data.objects.new("excluded", None)
    context.scene.collection.objects.link(hidden_obj)
    context.scene.collection.objects.link(disabled_obj)
    child_coll.objects.link(excluded_obj)

    hidden_obj.hide_set(True)
    disabled_obj.hide_viewport = True
    excluded_obj.hide_set(True)
    child_coll.hide_viewport = True
    parent_layer_coll = context.view_layer.layer_collection.children["parent"]
    child_layer_coll = parent_layer_coll.children["child"]
    child_layer_coll.exclude = True
    parent_layer_coll.exclude = True

    with temporarily_unhide_all(context):
        assert not parent_layer_coll.exclude
        assert not child_layer_coll.exclude
        assert not child_coll.hide_viewport
        assert hidden_obj.visible_get()
        assert disabled_obj.visible_get()
        assert excluded_obj.visible_get()

    assert parent_layer_coll.exclude
    assert child_layer_coll.exclude
    assert child_coll.hide_viewport
    assert disabled_obj.hide_viewport
    assert not hidden_obj.visible_get()
    assert not disabled_obj.visible_get()
    assert not excluded_obj.visible_get()
