import bpy

from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_blender_object, create_empty_object
from ..ydr.shader_materials import create_tint_geom_modifier
from ..ymap_next.properties.map import get_maps
from .shared import assert_logs_no_errors


@assert_logs_no_errors
def test_entity_tint_value_updates_tint_modifier_of_linked_object():
    bpy.ops.wm.read_homefile()

    root = create_empty_object(SollumType.DRAWABLE, "root")
    model = create_blender_object(SollumType.DRAWABLE_MODEL, "model")
    model.parent = root
    mod = create_tint_geom_modifier(model, "TintColor", None, None)

    group = get_maps(bpy.context, create_if_missing=True).new_group()
    map_data = group.new_map()
    entity = group.new_entity()
    entity.map_data_uuid = map_data.uuid
    entity.linked_object = root

    entity.tint_value = 99

    preview_id = mod.node_group.interface.items_tree["Palette (Preview)"].identifier
    if bpy.app.version >= (5, 2, 0):
        assert getattr(mod.properties.inputs, preview_id).value == 99
    else:
        assert mod[preview_id] == 99
