import bpy
from enum import Enum

class ObjectType(str, Enum):
    NONE = 'sollumz_none'
    DRAWABLE = 'sollumz_drawable'
    GEOMETRY = 'sollumz_geometry'
    SKELETON = 'sollumz_skeleton'


class BoundType(str, Enum):
    BOX = 'sollumz_bound_box'
    SPHERE = 'sollumz_bound_sphere'
    CAPSULE = 'sollumz_bound_capsule'
    CYLINDER = 'sollumz_bound_cylinder'
    DISC = 'sollumz_bound_disc'
    CLOTH = 'sollumz_bound_cloth'
    GEOMETRY = 'sollumz_bound_geometry'
    GEOMETRYBVH = 'sollumz_bound_geometrybvh'
    COMPOSITE = 'sollumz_bound_composite'


class PolygonType(str, Enum):
    BOX = 'sollumz_bound_poly_box'
    SPHERE = 'sollumz_bound_poly_sphere'
    CAPSULE = 'sollumz_bound_poly_capsule'
    CYLINDER = 'sollumz_bound_poly_cylinder'
    TRIANGLE = 'sollumz_bound_poly_triangle'


class MaterialType(str, Enum):
    NONE = 'sollumz_material_none',
    MATERIAL = 'sollumz_material',
    COLLISION = 'sollumz_material_collision'


class TextureType(str, Enum):
    UNKNOWN = 'sollumz_unknown'
    TINTPALLETE = 'sollumz_tintpallete'
    DEFAULT = 'sollumz_default'
    TERRAIN = 'sollumz_terrain'
    CLOUDDENSITY = 'sollumz_clouddensity'
    CLOUDNORMAL = 'sollumz_cloudnormal'
    CABLE = 'sollumz_cable'
    FENCE = 'sollumz_fence'
    ENVEFFECT = 'sollumz_env.effect'
    SCRIPT = 'sollumz_script'
    WATERFLOW = 'sollumz_waterflow'
    WATERFOAM = 'sollumz_waterfoam'
    WATERFOG = 'sollumz_waterfog'
    WATEROCEAN = 'sollumz_waterocean'
    WATER = 'sollumz_water'
    FOAMOPACITY = 'sollumz_foamopacity'
    FOAM = 'sollumz_foam'
    DIFFUSEDETAIL = 'sollumz_diffusedetail'
    DIFFUSEDARK = 'sollumz_diffusedark'
    DIFFUSEALPHAOPAQUE = 'sollumz_diffuseaplhaopaque'
    DETAIL = 'sollumz_detail'
    NORMAL = 'sollumz_normal'
    SPECULAR = 'sollumz_specular'
    EMMISIVE = 'sollumz_emmisive'
    SKIPPROCCESING = 'sollumz_skipproccesing'
    DONTOPTIMIZE = 'sollumz_dontoptimize'
    TEST = 'sollumz_test'
    COUNT = 'sollumz_count'
    DIFFUSE = 'sollumz_diffuse'

class TextureFormat(str, Enum):
    DXT1 = 'sollumz_dxt1'
    DXT3 = 'sollumz_dxt3'
    DXT5 = 'sollumz_dxt5'
    ATI1 = 'sollumz_ati1'
    ATI2 = 'sollumz_ati2'
    BC7 = 'sollumz_bc7'
    A1R5G5B5 = 'sollumz_a1r5g5b5'
    A1R8G8B8 = 'sollumz_a1r8g8b8'
    A8R8G8B8 = 'sollumz_a8r8g8b8'
    A8 = 'sollumz_a8'
    L8 = 'sollumz_l8'

class LodType(str, Enum):
    HIGH = 'sollumz_high'
    MED = 'sollumz_med'
    LOW = 'sollumz_low'
    VLOW = 'sollumz_vlow'


SOLLUMZ_UI_NAMES = {
    BoundType.BOX: 'Bound Box',
    BoundType.SPHERE: 'Bound Sphere',
    BoundType.CAPSULE: 'Bound Capsule',
    BoundType.CYLINDER: 'Bound Cylinder',
    BoundType.DISC: 'Bound Disc',
    BoundType.CLOTH: 'Bound Cloth',
    BoundType.GEOMETRY: 'Bound Geometry',
    BoundType.GEOMETRYBVH: 'GeometryBVH',
    BoundType.COMPOSITE: 'Composite',

    PolygonType.BOX: 'Bound Poly Box',
    PolygonType.SPHERE: 'Bound Poly Sphere',
    PolygonType.CAPSULE: 'Bound Poly Capsule',
    PolygonType.CYLINDER: 'Bound Poly Cylinder',
    PolygonType.TRIANGLE: 'Bound Poly Mesh',

    MaterialType.NONE: 'None',
    MaterialType.MATERIAL: 'Sollumz Material',
    MaterialType.COLLISION: 'Sollumz Collision Material',

    TextureType.UNKNOWN: 'UNKNOWN',
    TextureType.TINTPALLETE: 'TINTPALLETE',
    TextureType.DEFAULT: 'DEFAULT',
    TextureType.TERRAIN: 'TERRAIN',
    TextureType.CLOUDDENSITY: 'CLOUDDENSITY',
    TextureType.CLOUDNORMAL: 'CLOUDNORMAL',
    TextureType.CABLE: 'CABLE',
    TextureType.FENCE: 'FENCE',
    TextureType.ENVEFFECT: 'ENV.EFFECT',
    TextureType.SCRIPT: 'SCRIPT',
    TextureType.WATERFLOW: 'WATERFLOW',
    TextureType.WATERFOAM: 'WATERFOAM',
    TextureType.WATERFOG: 'WATERFOG',
    TextureType.WATEROCEAN: 'WATEROCEAN',
    TextureType.WATER: 'WATER',
    TextureType.FOAMOPACITY: 'FOAMOPACITY',
    TextureType.FOAM: 'FOAM',
    TextureType.DIFFUSEDETAIL: 'DIFFUSEDETAIL',
    TextureType.DIFFUSEDARK: 'DIFFUSEDARK',
    TextureType.DIFFUSEALPHAOPAQUE: 'DIFFUSEALPHAOPAQUE',
    TextureType.DETAIL: 'DETAIL',
    TextureType.NORMAL: 'NORMAL',
    TextureType.SPECULAR: 'SPECULAR',
    TextureType.EMMISIVE: 'EMMISIVE',
    TextureType.SKIPPROCCESING: 'SKIPPROCCESING',
    TextureType.DONTOPTIMIZE: 'DONTOPTIMIZE',
    TextureType.TEST: 'TEST',
    TextureType.COUNT: 'COUNT',
    TextureType.DIFFUSE: 'DIFFUSE',

    TextureFormat.DXT1: 'D3DFMT_DXT1',
    TextureFormat.DXT3: 'D3DFMT_DXT3',
    TextureFormat.DXT5: 'D3DFMT_DXT5',
    TextureFormat.ATI1: 'D3DFMT_ATI1',
    TextureFormat.ATI2: 'D3DFMT_ATI2',
    TextureFormat.BC7: 'D3DFMT_DXT1',
    TextureFormat.A1R5G5B5: 'D3DFMT_DXT1',
    TextureFormat.A1R8G8B8: 'D3DFMT_DXT1',
    TextureFormat.A8R8G8B8: 'D3DFMT_DXT1',
    TextureFormat.A8: 'D3DFMT_DXT1',
    TextureFormat.L8: 'D3DFMT_DXT1',

    LodType.HIGH: 'High',
    LodType.MED: 'Med',
    LodType.LOW: 'Low',
    LodType.VLOW: 'Vlow',

    ObjectType.NONE: 'Sollumz None',
    ObjectType.DRAWABLE: 'Sollumz Drawable',
    ObjectType.GEOMETRY: 'Sollumz Geometry',
    ObjectType.SKELETON: 'Sollumz Skeleton',
}

def is_sollum_type(obj, type):
    return obj.sollum_type in type._value2member_map_

# Generate items from provided enums
def items_from_enums(*enums):
    items = []
    for enum in enums:
        for item in enum:
            if item not in SOLLUMZ_UI_NAMES:
                raise KeyError(f"UI name mapping not found for key {item} of {enum}.")
            items.append((item.value, SOLLUMZ_UI_NAMES[item], ''))
    return items


def register():
    bpy.types.Object.sollum_type = bpy.props.EnumProperty(
        items = items_from_enums(BoundType, PolygonType, ObjectType),
        name = "Sollumz Type",
        default = "sollumz_none"
    )
    
    bpy.types.Material.sollum_type = bpy.props.EnumProperty(
            items = items_from_enums(MaterialType),
            name = "Sollumz Material Type",
            default = MaterialType.NONE
    )
    
def unregister():
    del bpy.types.Object.sollum_type
    del bpy.types.Material.sollum_type
