"""Handle changes between 2.5.0 and 2.6.0."""

import bpy
from bpy.types import (
    BlendData,
    Material,
)

from .versioning_230 import get_src_props

def update_mat_paint_layer(mat: Material):
    src_props = get_src_props(mat)
    if src_props is None:
        return

    old_paint_layer_int = src_props.get("sollumz_paint_layer", None)
    if old_paint_layer_int is None:
        return

    old_to_new = {
        0: 0,  # custom - not paintable
        1: 1,  # primary
        2: 2,  # secondary
        3: 4,  # wheel
        4: 6,  # interior trim
        5: 7,  # interior dash
        # pearlescent and default have no mapping in the old property
    }
    new_paint_layer_int = old_to_new.get(old_paint_layer_int, 0)

    if new_paint_layer_int != 0:
        from ..yft.properties import _set_mat_paint_layer
        _set_mat_paint_layer(mat, new_paint_layer_int)

    if bpy.app.version < (5, 0, 0):
        del mat["sollumz_paint_layer"]


def do_versions(data_version: int, data: BlendData):
    if data_version < 6:
        for mat in data.materials:
            update_mat_paint_layer(mat)
