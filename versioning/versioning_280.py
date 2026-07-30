"""Handle changes between 2.8.0 and 2.9.0."""

import bpy
from bpy.types import (
    BlendData,
    Object,
    Scene,
)


def update_archetype_spawn_point_extensions(scene: Scene):
    from .versioning_230 import move_renamed_prop, get_src_props

    for ytyp in scene.ytyps:
        for arch in ytyp.archetypes_:
            for ext in arch.extensions:
                ext_dst_props = ext.spawn_point_extension_properties
                ext_src_props = get_src_props(ext_dst_props)

                move_renamed_prop(ext_dst_props, ext_src_props, "required_map", "required_imap")

                time_float_to_int = lambda v: min(24, max(0, int(v)))
                move_renamed_prop(ext_dst_props, ext_src_props, "start", "start", time_float_to_int)
                move_renamed_prop(ext_dst_props, ext_src_props, "end", "end", time_float_to_int)


def update_mlo_entity_ao_and_tint(scene: Scene):
    from .versioning_230 import move_renamed_prop, get_src_props

    # These were floats but always represented 0-255 integers
    to_uint8 = lambda v: min(255, max(0, int(v)))

    for ytyp in scene.ytyps:
        for arch in ytyp.archetypes_:
            for entity in arch.entities_:
                src_props = get_src_props(entity)
                for prop_name in ("ambient_occlusion_multiplier", "artificial_ambient_occlusion", "tint_value"):
                    move_renamed_prop(entity, src_props, prop_name, prop_name, to_uint8)


def update_frag_vehicle_window_shattermap_mode(obj: Object):
    from .versioning_230 import get_src_props

    src_props = get_src_props(obj)
    if src_props is None:
        return

    src_child_props = src_props.get("child_properties", None)
    if src_child_props is None:
        return

    if src_child_props.get("is_veh_window", False):
        obj.child_properties.shattermap_mode = "MANUAL"

    if bpy.app.version < (5, 0, 0):
        for old_prop in ("is_veh_window", "window_mat"):
            if old_prop in src_child_props:
                del src_child_props[old_prop]


def do_versions(data_version: int, data: BlendData):
    if data_version < 9:
        for scene in data.scenes:
            update_archetype_spawn_point_extensions(scene)

    if data_version < 10:
        for scene in data.scenes:
            update_mlo_entity_ao_and_tint(scene)

    if data_version < 11:
        for obj in data.objects:
            update_frag_vehicle_window_shattermap_mode(obj)
