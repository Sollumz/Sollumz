from pathlib import Path

import bpy
import numpy as np
from bpy.types import (
    NodesModifier,
    Object,
)
from mathutils import Vector

from ... import logger
from ...shared.game_assets.library import link_objects_from_library
from ..properties.map import MapGrassBatch

LIBRARY_PATH = Path(__file__).parent / "assets/grass_batch_geonodes.blend"


def create_grass_batch_geonodes(grass_batch: MapGrassBatch):
    archetype_names = [t.archetype_name for t in grass_batch.templates]

    res = link_objects_from_library(archetype_names)
    if res is None:
        return
    archetype_datas, num_missing = res
    # TODO: properly report this to the user
    if num_missing:
        logger.info("num missing grass archetypes: " + str(num_missing))
    archetype_objects = {obj.name: obj for data in archetype_datas for obj in data.objects}

    with bpy.data.libraries.load(str(LIBRARY_PATH), assets_only=True) as (data_src, data_dst):
        data_dst.node_groups = ["GrassBatchGenModifier.Base"]

    modifier_ng = data_dst.node_groups[0]
    modifier_ng.asset_clear()
    templates_ng = modifier_ng.nodes["GrassBatchTemplates"].node_tree
    templates_ng.asset_clear()
    template_selector_ng = modifier_ng.nodes["GrassBatchTemplateSelector"].node_tree
    template_selector_ng.asset_clear()

    # Setup templates node groups
    template_object_node_0 = templates_ng.nodes["Object"]
    template_object_info_node_0 = templates_ng.nodes["Object Info"]
    template_geo_to_inst_node = templates_ng.nodes["Geometry to Instance"]
    template_geo_to_inst_node_input = template_geo_to_inst_node.inputs["Geometry"]

    # Remove existing link
    templates_ng.links.remove(template_object_info_node_0.outputs["Geometry"].links[0])

    # Reverse so links to the "Geometry to Instance" multi-input are inserted in the correct order
    for i, template in reversed(list(enumerate(grass_batch.templates))):
        if i > 0:
            template_object_node_i = templates_ng.nodes.new("GeometryNodeInputObject")
            template_object_node_i.label = template.archetype_name
            template_object_node_i.location = template_object_node_0.location + Vector((0, -75 * i))
            template_object_node_i.width = template_object_node_0.width
            template_object_node_i.object = archetype_objects.get(template.archetype_name, None)
            template_object_info_node_i = templates_ng.nodes.new("GeometryNodeObjectInfo")
            template_object_info_node_i.location = template_object_info_node_0.location + Vector((0, -75 * i))
            template_object_info_node_i.hide = True

            templates_ng.links.new(template_object_info_node_i.inputs["Object"], template_object_node_i.outputs[0])
            templates_ng.links.new(template_geo_to_inst_node_input, template_object_info_node_i.outputs["Geometry"])
        elif i == 0:
            template_object_node_0.label = template.archetype_name
            template_object_node_0.object = archetype_objects.get(template.archetype_name, None)
            templates_ng.links.new(template_geo_to_inst_node_input, template_object_info_node_0.outputs["Geometry"])

    # Setup template selector node group
    spawn_weights = np.array([t.spawn_weight for t in grass_batch.templates])
    spawn_thresholds = spawn_weights.cumsum() / spawn_weights.sum()

    selector_group_input_node = template_selector_ng.nodes["Group Input"]
    selector_group_input_random_value_output = selector_group_input_node.outputs["Random Value"]
    selector_threshold_node_0 = template_selector_ng.nodes["Threshold0"]
    selector_threshold_node_1 = template_selector_ng.nodes["Threshold1"]
    selector_cmp_node_0 = template_selector_ng.nodes["CompareThreshold0"]
    selector_switch_node_0 = template_selector_ng.nodes["Switch0"]
    selector_switch_node_1 = template_selector_ng.nodes["Switch1"]
    selector_switch_node_iprev = None
    # TODO: len(templates) == 0 or == 1 need special case handling (need to delete existing nodes)
    # don't need extra nodes for the last one, previous one already handles it
    for i, template in enumerate(grass_batch.templates[:-1]):
        if i > 1:
            selector_threshold_node_i = template_selector_ng.nodes.new("ShaderNodeValue")
            selector_threshold_node_i.parent = selector_threshold_node_1.parent
            selector_threshold_node_i.location = selector_threshold_node_0.location + Vector((0, -75 * i))
            selector_threshold_node_i.width = selector_threshold_node_0.width
            selector_threshold_node_i.outputs[0].default_value = spawn_thresholds[i]

            selector_cmp_node_i = template_selector_ng.nodes.new("FunctionNodeCompare")
            selector_cmp_node_i.data_type = "FLOAT"
            selector_cmp_node_i.operation = "LESS_EQUAL"
            selector_cmp_node_i.location = selector_cmp_node_0.location + Vector((0, -160 * i))

            selector_switch_node_i = template_selector_ng.nodes.new("GeometryNodeSwitch")
            selector_switch_node_i.input_type = "INT"
            selector_switch_node_i.inputs["True"].default_value = i
            selector_switch_node_i.inputs["False"].default_value = i + 1
            selector_switch_node_i.location = selector_switch_node_0.location + Vector((0, -160 * i))

            template_selector_ng.links.new(selector_cmp_node_i.inputs["A"], selector_group_input_random_value_output)
            template_selector_ng.links.new(selector_cmp_node_i.inputs["B"], selector_threshold_node_i.outputs[0])
            template_selector_ng.links.new(
                selector_switch_node_i.inputs["Switch"], selector_cmp_node_i.outputs["Result"]
            )
            template_selector_ng.links.new(
                selector_switch_node_iprev.inputs["False"], selector_switch_node_i.outputs["Output"]
            )

            selector_switch_node_iprev = selector_switch_node_i
        elif i == 1:
            selector_threshold_node_1.outputs[0].default_value = spawn_thresholds[1]
            selector_switch_node_iprev = selector_switch_node_1
        elif i == 0:
            selector_threshold_node_0.outputs[0].default_value = spawn_thresholds[0]
            selector_switch_node_iprev = selector_switch_node_0

    if grass_batch.modifier_ng is not None:
        # Remove all existing node groups, replace all their references with the new ones
        old_modifier_ng = grass_batch.modifier_ng
        old_templates_ng = (n := old_modifier_ng.nodes.get("GrassBatchTemplates", None)) and n.node_tree
        old_template_selector_ng = (n := old_modifier_ng.nodes.get("GrassBatchTemplateSelector", None)) and n.node_tree
        for old_ng, new_ng in (
            (old_modifier_ng, modifier_ng),
            (old_templates_ng, templates_ng),
            (old_template_selector_ng, template_selector_ng),
        ):
            if old_ng is None:
                continue
            old_ng.user_remap(new_ng)
            bpy.data.node_groups.remove(old_ng)

    modifier_ng.name = "GrassBatchGenModifier." + grass_batch.name
    templates_ng.name = "GrassBatchTemplates." + grass_batch.name
    template_selector_ng.name = "GrassBatchTemplateSelector." + grass_batch.name
    grass_batch.modifier_ng = modifier_ng


def add_grass_batch_modifier(obj: Object, grass_batch: MapGrassBatch) -> NodesModifier:
    mod: NodesModifier = obj.modifiers.new("GrassBatchGen", "NODES")
    mod.node_group = grass_batch.modifier_ng  # TODO: decide what to do if it doesn't exist
    mod["Socket_7_attribute_name"] = ".grass.source_density"
    mod["Socket_14_attribute_name"] = ".grass.source_color_ao"
    mod.show_group_selector = False
    if bpy.app.version >= (5, 0, 0):
        mod.show_manage_panel = False
    return mod


def disable_grass_batch_modifier_preview(obj: Object, grass_batch: MapGrassBatch):
    modifier_ng = grass_batch.modifier_ng
    for mod in obj.modifiers:
        if not isinstance(mod, NodesModifier) or mod.node_group != modifier_ng:
            continue

        if mod["Socket_6"] != 0:
            mod["Socket_6"] = 0  # Socket_6 = 'Preview Grass': 0 = No, 1 = Simplified, 2 = Yes
            obj.update_tag()
