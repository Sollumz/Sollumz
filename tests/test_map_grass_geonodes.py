import bpy
import pytest

from ..ymap_next.grass.geonodes import (
    add_grass_batch_modifier,
    create_grass_batch_geonodes,
    disable_grass_batch_modifier_preview,
    is_grass_batch_geonodes_supported,
)
from ..ymap_next.properties.map import get_maps
from .shared import assert_logs_no_errors

# The whole module is skipped on Blender < 5.0
pytestmark = pytest.mark.skipif(
    not is_grass_batch_geonodes_supported(),
    reason="grass batch geonodes require Blender 5.0+",
)


@pytest.fixture(autouse=True)
def _reset_blend():
    bpy.ops.wm.read_homefile()


def _new_group(name="test_grass_group"):
    group = get_maps(bpy.context, create_if_missing=True).new_group()
    group.name = name
    return group


def _new_batch(group, name, weights):
    """Create a grass batch with one template per weight in `weights`."""
    batch = group.new_grass_batch()
    batch.name = name
    for i, w in enumerate(weights):
        t = batch.templates.add()
        t.archetype_name = f"arch_{i}"
        t.spawn_weight = w
    return batch


@assert_logs_no_errors
def test_create_builds_named_node_groups():
    group = _new_group()
    batch = _new_batch(group, "b1", [1.0, 1.0, 1.0])

    create_grass_batch_geonodes(batch)

    assert batch.modifier_ng is not None
    assert batch.modifier_ng.name == "GrassBatchGenModifier.b1"
    # sub node-trees renamed after the batch
    assert bpy.data.node_groups.get("GrassBatchTemplates.b1") is not None
    assert bpy.data.node_groups.get("GrassBatchTemplateSelector.b1") is not None


@assert_logs_no_errors
def test_create_single_template_removes_selector_nodes():
    group = _new_group()
    batch = _new_batch(group, "one", [1.0])

    create_grass_batch_geonodes(batch)

    sel = batch.modifier_ng.nodes["GrassBatchTemplateSelector"].node_tree
    # num_templates <= 1 branch: all compare/switch/threshold nodes removed,
    # output falls back to Template Index default 0.
    for n in ("Switch0", "Switch1", "CompareThreshold0", "Threshold0", "Threshold1"):
        assert sel.nodes.get(n) is None
    assert sel.nodes["Group Output"].inputs["Template Index"].default_value == 0


@assert_logs_no_errors
def test_create_two_templates_keeps_only_switch0():
    group = _new_group()
    batch = _new_batch(group, "two", [1.0, 3.0])

    create_grass_batch_geonodes(batch)

    sel = batch.modifier_ng.nodes["GrassBatchTemplateSelector"].node_tree
    assert sel.nodes.get("Switch0") is not None
    assert sel.nodes["Switch0"].inputs["False"].default_value == 1
    for n in ("Switch1", "Threshold1", "CompareThreshold1"):
        assert sel.nodes.get(n) is None


@assert_logs_no_errors
def test_create_three_templates_sets_normalized_thresholds():
    group = _new_group()
    # weights [1, 1, 2] -> normalized thresholds = [0.25, 0.5, 1.0]
    batch = _new_batch(group, "three", [1.0, 1.0, 2.0])

    create_grass_batch_geonodes(batch)

    sel = batch.modifier_ng.nodes["GrassBatchTemplateSelector"].node_tree
    assert sel.nodes["Threshold0"].outputs[0].default_value == pytest.approx(0.25)
    assert sel.nodes["Threshold1"].outputs[0].default_value == pytest.approx(0.5)
    assert sel.nodes.get("Switch1") is not None  # both switches kept for 3 templates


@assert_logs_no_errors
def test_create_regenerates_and_removes_old_node_groups():
    """Second call user_remaps + removes the old sub node-groups."""
    group = _new_group()
    batch = _new_batch(group, "regen", [1.0, 1.0])

    create_grass_batch_geonodes(batch)
    create_grass_batch_geonodes(batch)

    # The regenerated group reuses the exact name with no ".001" suffix: Blender would
    # have suffixed the new one if the old data-block still existed, so the plain name
    # (and a single group per prefix) proves the old node groups were removed.
    assert batch.modifier_ng.name == "GrassBatchGenModifier.regen"
    for prefix in ("GrassBatchGenModifier.", "GrassBatchTemplates.", "GrassBatchTemplateSelector."):
        matching = [ng.name for ng in bpy.data.node_groups if ng.name.startswith(prefix)]
        assert matching == [prefix + "regen"], f"{prefix!r}: expected one regenerated group, got {matching}"


@assert_logs_no_errors
def test_add_modifier_creates_nodes_modifier():
    group = _new_group()
    batch = _new_batch(group, "mod", [1.0, 1.0])
    create_grass_batch_geonodes(batch)

    obj = bpy.data.objects.new("grass_mesh", bpy.data.meshes.new("grass_mesh"))
    bpy.context.scene.collection.objects.link(obj)

    mod = add_grass_batch_modifier(obj, batch)

    assert mod is not None
    assert mod.type == "NODES"
    assert mod.name == "GrassBatchGen"
    assert mod.node_group == batch.modifier_ng


@assert_logs_no_errors
def test_add_modifier_returns_none_without_node_group():
    group = _new_group()
    batch = _new_batch(group, "nomod", [1.0])
    # modifier_ng never created -> None
    obj = bpy.data.objects.new("plain", bpy.data.meshes.new("plain"))
    bpy.context.scene.collection.objects.link(obj)

    assert add_grass_batch_modifier(obj, batch) is None
    assert len(obj.modifiers) == 0


@assert_logs_no_errors
def test_disable_preview_resets_socket():
    group = _new_group()
    batch = _new_batch(group, "prev", [1.0, 1.0])
    create_grass_batch_geonodes(batch)

    obj = bpy.data.objects.new("grass_prev", bpy.data.meshes.new("grass_prev"))
    bpy.context.scene.collection.objects.link(obj)
    mod = add_grass_batch_modifier(obj, batch)

    if bpy.app.version >= (5, 2, 0):
        mod.properties.inputs.Socket_6.value = "Full"
    else:
        mod["Socket_6"] = 2  # Preview Grass = Full
    disable_grass_batch_modifier_preview(obj, batch)

    if bpy.app.version >= (5, 2, 0):
        assert mod.properties.inputs.Socket_6.value == "Off"
    else:
        assert mod["Socket_6"] == 0


@assert_logs_no_errors
def test_disable_preview_noop_without_node_group():
    group = _new_group()
    batch = _new_batch(group, "prev_noop", [1.0])
    obj = bpy.data.objects.new("no_ng", bpy.data.meshes.new("no_ng"))
    bpy.context.scene.collection.objects.link(obj)
    # modifier_ng is None -> early return, no crash
    disable_grass_batch_modifier_preview(obj, batch)
