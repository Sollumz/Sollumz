import bpy

from ..sollumz_properties import ArchetypeType, SollumType
from ..tools.blenderhelper import create_blender_object, create_empty_object
from .shared import (
    assert_logs_no_warnings_or_errors,
    load_blend_data,
)


@assert_logs_no_warnings_or_errors
def test_mlo_entityset_toggle_visibility():
    data = load_blend_data("entitysets_visibility.blend")

    objs = [data.objects[n] for n in ("Cube", "Cube.001", "Cube.002", "Cube.003", "Cube.003.child")]

    def _hide_state():
        return [o.hide_get() for o in objs]

    assert _hide_state() == ([False] * len(objs))

    # entity set indices in the .blend
    set_with_multiple_entities = 0
    set_with_single_entities = 1
    set_with_unlinked_entity = 2
    set_with_no_entities = 3

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_multiple_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, False, False, False]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_single_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, True, False, False]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_unlinked_entity, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, True, True, True]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_no_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, True, True, True]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_unlinked_entity, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, True, False, False]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_single_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, False, False, False]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_multiple_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [False, False, False, False, False]


def _new_mlo_archetype():
    scene = bpy.context.scene
    ytyp = scene.ytyps.add()
    ytyp.name = "test_mlo"
    scene.ytyp_index = len(scene.ytyps) - 1
    a = ytyp.new_archetype(ArchetypeType.MLO)
    a.name = "test_mlo"
    return a


@assert_logs_no_warnings_or_errors
def test_mlo_create_instance():
    bpy.ops.wm.read_homefile()
    context = bpy.context

    col = create_empty_object(SollumType.BOUND_COMPOSITE, "mlo_col")

    shell = create_empty_object(SollumType.DRAWABLE, "mlo_shell")
    shell.location = (10.0, 20.0, 30.0)
    child_model = create_blender_object(SollumType.DRAWABLE_MODEL, "child_model")
    child_model.parent = shell
    non_model = create_empty_object(SollumType.NONE, "non_model")
    non_model.parent = shell
    standalone_model = create_blender_object(SollumType.DRAWABLE_MODEL, "standalone_model")

    archetype = _new_mlo_archetype()
    archetype.asset = col
    archetype.new_entity().linked_object = shell
    archetype.new_entity().linked_object = standalone_model
    archetype.new_entity()  # entity without linked object should be ignored

    context.view_layer.update()
    bpy.ops.sollumz.mlo_create_instance()

    collection = archetype.mlo_collection_for_instancing
    assert collection is not None
    assert set(collection.objects.keys()) == {"child_model", "standalone_model"}
    assert collection.instance_offset == col.matrix_world.translation

    instance_obj = context.view_layer.objects.active
    assert instance_obj is not None
    assert instance_obj.instance_type == "COLLECTION"
    assert instance_obj.instance_collection == collection
    assert instance_obj.location == col.matrix_world.translation
    assert instance_obj.select_get()


@assert_logs_no_warnings_or_errors
def test_mlo_create_instance_reuses_collection():
    bpy.ops.wm.read_homefile()
    context = bpy.context

    model = create_blender_object(SollumType.DRAWABLE_MODEL, "model")
    archetype = _new_mlo_archetype()
    archetype.new_entity().linked_object = model

    bpy.ops.sollumz.mlo_create_instance()
    collection = archetype.mlo_collection_for_instancing
    first_instance = context.view_layer.objects.active

    num_collections = len(bpy.data.collections)
    bpy.ops.sollumz.mlo_create_instance()
    second_instance = context.view_layer.objects.active

    assert archetype.mlo_collection_for_instancing == collection
    assert len(bpy.data.collections) == num_collections
    assert first_instance != second_instance
    assert first_instance.instance_collection == collection
    assert second_instance.instance_collection == collection


@assert_logs_no_warnings_or_errors
def test_mlo_refresh_instances():
    bpy.ops.wm.read_homefile()
    context = bpy.context

    old_model = create_blender_object(SollumType.DRAWABLE_MODEL, "old_model")
    archetype = _new_mlo_archetype()
    archetype.new_entity().linked_object = old_model

    bpy.ops.sollumz.mlo_create_instance()
    collection = archetype.mlo_collection_for_instancing
    instance_obj = context.view_layer.objects.active
    assert set(collection.objects.keys()) == {"old_model"}

    new_model = create_blender_object(SollumType.DRAWABLE_MODEL, "new_model")
    archetype.new_entity().linked_object = new_model
    archetype.entities[0].linked_object = None

    bpy.ops.sollumz.mlo_refresh_instances()

    assert set(collection.objects.keys()) == {"new_model"}
    assert instance_obj.instance_collection == collection
