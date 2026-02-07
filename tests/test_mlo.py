import bpy

from .shared import (
    assert_logs_no_warnings_or_errors,
    load_blend_data,
)


@assert_logs_no_warnings_or_errors
def test_mlo_entityset_toggle_visibility():
    data = load_blend_data("entitysets_visibility.blend")

    objs = [data.objects[n] for n in ("Cube", "Cube.001", "Cube.002", "Cube.003")]

    def _hide_state():
        return [o.hide_get() for o in objs]

    assert _hide_state() == ([False] * 4)

    # entity set indices in the .blend
    set_with_multiple_entities = 0
    set_with_single_entities = 1
    set_with_unlinked_entity = 2
    set_with_no_entities = 3

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_multiple_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, False, False]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_single_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, True, False]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_unlinked_entity, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, True, True]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_no_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, True, True]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_unlinked_entity, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, True, False]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_single_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [True, True, False, False]

    bpy.ops.sollumz.entityset_toggle_visibility(index=set_with_multiple_entities, ytyp_index=0, archetype_index=0)
    assert _hide_state() == [False, False, False, False]
