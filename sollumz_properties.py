import bpy
from enum import Enum

class DrawableType(str, Enum):
    NONE = 'sollumz_none'
    DRAWABLE_DICTIONARY = 'sollumz_drawable_dictionary'
    DRAWABLE = 'sollumz_drawable'
    DRAWABLE_MODEL = 'sollumz_drawable_model'
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
    TINTPALETTE = 'sollumz_tintpalette'
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
    SKIPPROCESSING = 'sollumz_skipprocessing'
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
    ALL = "sollumz_all" #for ui
    NONE = "sollumz_none" #for ui
    HIGH = 'sollumz_high'
    MEDIUM = 'sollumz_medium'
    LOW = 'sollumz_low'
    VERYLOW = 'sollumz_verylow'

SOLLUMZ_UI_NAMES = {
    BoundType.BOX: 'Bound Box',
    BoundType.SPHERE: 'Bound Sphere',
    BoundType.CAPSULE: 'Bound Capsule',
    BoundType.CYLINDER: 'Bound Cylinder',
    BoundType.DISC: 'Bound Disc',
    BoundType.CLOTH: 'Bound Cloth',
    BoundType.GEOMETRY: 'Bound Geometry',
    BoundType.GEOMETRYBVH: 'Bound GeometryBVH',
    BoundType.COMPOSITE: 'Bound Composite',

    PolygonType.BOX: 'Bound Poly Box',
    PolygonType.SPHERE: 'Bound Poly Sphere',
    PolygonType.CAPSULE: 'Bound Poly Capsule',
    PolygonType.CYLINDER: 'Bound Poly Cylinder',
    PolygonType.TRIANGLE: 'Bound Poly Mesh',

    MaterialType.NONE: 'None',
    MaterialType.MATERIAL: 'Sollumz Material',
    MaterialType.COLLISION: 'Sollumz Collision Material',

    TextureType.UNKNOWN: 'UNKNOWN',
    TextureType.TINTPALETTE: 'TINTPALETTE',
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
    TextureType.SKIPPROCESSING: 'SKIPPROCESSING',
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

    LodType.ALL: 'All',
    LodType.NONE: 'None',
    LodType.HIGH: 'High',
    LodType.MEDIUM: 'Med',
    LodType.LOW: 'Low',
    LodType.VERYLOW: 'Vlow',

    DrawableType.NONE: 'Sollumz None',
    DrawableType.DRAWABLE_DICTIONARY: 'Sollumz Drawable Dictionary',
    DrawableType.DRAWABLE: 'Sollumz Drawable',
    DrawableType.DRAWABLE_MODEL: 'Sollumz Drawable Model',
    DrawableType.GEOMETRY: 'Sollumz Geometry',
    DrawableType.SKELETON: 'Sollumz Skeleton',
}

class EntityProperties(bpy.types.PropertyGroup):
    archetype_name = bpy.props.StringProperty(name = "ArchetypeName")
    flags = bpy.props.IntProperty(name = "Flags")
    guid = bpy.props.IntProperty(name = "Guid")
    position = bpy.props.FloatVectorProperty(name = "Position")
    rotation = bpy.props.FloatVectorProperty(name = "Rotation", size = 4)
    scale_xy = bpy.props.FloatProperty(name = "ScaleXY")
    scale_z = bpy.props.FloatProperty(name = "ScaleZ")
    parent_index = bpy.props.IntProperty(name = "ParentIndex")
    lod_dist = bpy.props.FloatProperty(name = "Lod Distance")
    child_lod_dist = bpy.props.FloatProperty(name = "Child Lod Distance")
    lod_level = bpy.props.EnumProperty(items = [("","", "")], name = "LOD Level")
    num_children = bpy.props.IntProperty(name = "Number of Children")
    priority_level = bpy.props.EnumProperty(items = [("","", "")], name = "Priority Level")
    #extensions?
    ambient_occlusion_multiplier = bpy.props.FloatProperty(name =  "Ambient Occlusion Multiplier")
    artificial_ambient_occlusion = bpy.props.FloatProperty(name =  "Artificial Ambient Occlusion")
    tint_value = bpy.props.FloatProperty(name =  "Tint Value")

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
        items = items_from_enums(BoundType, PolygonType, DrawableType),
        name = "Sollumz Type",
        default = "sollumz_none",
        options={'HIDDEN'}
    )
    
    bpy.types.Material.sollum_type = bpy.props.EnumProperty(
            items = items_from_enums(MaterialType),
            name = "Sollumz Material Type",
            default = MaterialType.NONE,
            options={'HIDDEN'}
    )

    bpy.types.Scene.lod_level = bpy.props.EnumProperty(
            items = items_from_enums(LodType),
            name = "LOD Level",
            default = LodType.ALL,
            options={'HIDDEN'}
    )

    bpy.types.Object.ymap_properties = bpy.props.PointerProperty(type = EntityProperties)

def unregister():
    del bpy.types.Object.sollum_type
    del bpy.types.Material.sollum_type
    del bpy.types.Scene.lod_level
