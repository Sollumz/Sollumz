"""Handle changes between 2.5.0 and 2.6.0."""

from bpy.types import (
    BlendData,
    Material,
)


def update_mat_paint_layer(mat: Material):
    old_paint_layer_int = mat.get("sollumz_paint_layer", None)
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

    del mat["sollumz_paint_layer"]


def do_versions(data_version: int, data: BlendData):
    if data_version < 6:
        for mat in data.materials:
            update_mat_paint_layer(mat)
