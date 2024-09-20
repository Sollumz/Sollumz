import bpy
from bpy.types import (
    Object,
    WindowManager,
    PropertyGroup
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    PointerProperty,
)

class NavCoverPointProps(PropertyGroup):
    point_type: IntProperty(name="Type")

def register():
    Object.sz_nav_cover_point = PointerProperty(type=NavCoverPointProps)

    WindowManager.sz_ui_nav_view_bounds = BoolProperty(
        name="Display Grid Bounds", description="Display the navigation mesh map grid bounds on the 3D Viewport",
        default=False
    )


def unregister():
    del Object.sz_nav_cover_point
    del WindowManager.sz_ui_nav_view_bounds
