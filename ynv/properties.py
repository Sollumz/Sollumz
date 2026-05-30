import bpy
from bpy.props import (
    FloatProperty,
    FloatVectorProperty,
    IntProperty,
    PointerProperty,
    StringProperty,
)
from bpy.types import Object, PropertyGroup


# Magic area_id for standalone navmeshes (vehicles, interiors).
STANDALONE_AREA_ID = 10000


class SzNavMeshProperties(PropertyGroup):
    area_id: IntProperty(
        name="Area ID",
        description="Grid cell index for map navmeshes, or 10000 for standalone",
        default=STANDALONE_AREA_ID,
        min=0,
    )
    content_flags: StringProperty(
        name="Content Flags",
        description="Comma-separated content flag names, e.g. 'Polygons, Portals'",
        default="Polygons, Portals",
    )
    bb_min: FloatVectorProperty(name="BB Min", size=3, subtype="XYZ")
    bb_max: FloatVectorProperty(name="BB Max", size=3, subtype="XYZ")


class SzNavPortalProperties(PropertyGroup):
    portal_type: IntProperty(name="Type", default=1, min=0, max=255)
    angle: FloatProperty(name="Angle", default=0.0)
    poly_from: IntProperty(name="Poly From", default=0, min=0)
    poly_to: IntProperty(name="Poly To", default=0, min=0)


class SzNavPointProperties(PropertyGroup):
    point_type: IntProperty(name="Type", default=0, min=0, max=255)


def register():
    Object.sz_navmesh = PointerProperty(type=SzNavMeshProperties)
    Object.sz_nav_portal = PointerProperty(type=SzNavPortalProperties)
    Object.sz_nav_point = PointerProperty(type=SzNavPointProperties)


def unregister():
    del Object.sz_nav_point
    del Object.sz_nav_portal
    del Object.sz_navmesh
