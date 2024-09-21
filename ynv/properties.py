import bpy
from bpy.types import (
    Object,
    WindowManager,
    PropertyGroup
)
from bpy.props import (
    BoolProperty,
    IntProperty,
    EnumProperty,
    PointerProperty,
)
from enum import IntEnum


class NavCoverType(IntEnum):
    LOW_WALL = 0
    LOW_WALL_TO_LEFT = 1
    LOW_WALL_TO_RIGHT = 2
    WALL_TO_LEFT = 3
    WALL_TO_RIGHT = 4
    WALL_TO_NEITHER = 5


NavCoverTypeEnumItems = tuple((enum.name, label, desc, enum.value) for enum, label, desc in (
    (NavCoverType.LOW_WALL, "Low Wall", "Behind low wall, can only shoot over the top"),
    (NavCoverType.LOW_WALL_TO_LEFT, "Low Wall To Left", "Behind low wall corner, can shoot over the top and to the right"),
    (NavCoverType.LOW_WALL_TO_RIGHT, "Low Wall To Right", "Behind low wall corner, can shoot over the top and to the left"),
    (NavCoverType.WALL_TO_LEFT, "Wall To Left", "Behind high wall corner, can only shoot to the right"),
    (NavCoverType.WALL_TO_RIGHT, "Wall To Right", "Behind high wall corner, can only shoot to the left"),
    (NavCoverType.WALL_TO_NEITHER, "Wall To Neither", "Behind thin high wall, can shoot to either the left or right sides"),
))


class NavCoverPointProps(PropertyGroup):
    cover_type: EnumProperty(name="Type", items=NavCoverTypeEnumItems, default=NavCoverType.LOW_WALL.name)
    disabled: BoolProperty(name="Disabled", default=False)

    def get_raw_int(self) -> int:
        cover_type_int = NavCoverType[self.cover_type].value
        disabled_int = 0x8 if self.disabled else 0
        return cover_type_int | disabled_int

    def set_raw_int(self, value):
        cover_type_int = value & 0x7
        if cover_type_int <= 5:
            self.cover_type = NavCoverType(cover_type_int).name
        else:
            # in case of corrupted out-of-range values, default to low-wall
            self.cover_type = NavCoverType.LOW_WALL.name
        self.disabled = (value & 0x8) != 0


def register():
    Object.sz_nav_cover_point = PointerProperty(type=NavCoverPointProps)

    WindowManager.sz_ui_nav_view_bounds = BoolProperty(
        name="Display Grid Bounds", description="Display the navigation mesh map grid bounds on the 3D Viewport",
        default=False
    )


def unregister():
    del Object.sz_nav_cover_point
    del WindowManager.sz_ui_nav_view_bounds
