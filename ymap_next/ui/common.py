from bpy.types import UILayout

from ..map_index import (
    CACHE_NOT_READY,
    MAP_INDEX,
)


def draw_cache_result(layout: UILayout, cache_result: object | None, missing_msg: str) -> bool:
    if cache_result is CACHE_NOT_READY:
        progress = MAP_INDEX.build_progress
        if progress is None:
            layout.progress(text="Building cache...", factor=0.0, type="BAR")
        else:
            current, total = progress
            layout.progress(text=f"Building cache ({current}/{total})...", factor=current / total, type="BAR")
        return False

    if cache_result is None:
        layout.label(text=missing_msg)
        return False

    return True
