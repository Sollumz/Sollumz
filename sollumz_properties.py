import bpy
from enum import Enum
from typing import Sequence
from .tools.utils import flag_list_to_int, flag_prop_to_list, int_to_bool_list


class SollumType(str, Enum):
    NONE = "sollumz_none"

    FRAGMENT = "sollumz_fragment"
    FRAGGROUP = "sollumz_fraggroup"
    FRAGCHILD = "sollumz_fragchild"
    FRAGLOD = "sollumz_lod"
    SHATTERMAP = "sollumz_frag_vehicle_window"

    DRAWABLE_DICTIONARY = "sollumz_drawable_dictionary"
    DRAWABLE = "sollumz_drawable"
    DRAWABLE_MODEL = "sollumz_drawable_model"
    DRAWABLE_GEOMETRY = "sollumz_drawable_geometry"
    SKELETON = "sollumz_skeleton"
    LIGHT = "sollumz_light"

    BOUND_BOX = "sollumz_bound_box"
    BOUND_SPHERE = "sollumz_bound_sphere"
    BOUND_CAPSULE = "sollumz_bound_capsule"
    BOUND_CYLINDER = "sollumz_bound_cylinder"
    BOUND_DISC = "sollumz_bound_disc"
    BOUND_CLOTH = "sollumz_bound_cloth"
    BOUND_GEOMETRY = "sollumz_bound_geometry"
    BOUND_GEOMETRYBVH = "sollumz_bound_geometrybvh"
    BOUND_COMPOSITE = "sollumz_bound_composite"

    BOUND_POLY_BOX = "sollumz_bound_poly_box"
    BOUND_POLY_SPHERE = "sollumz_bound_poly_sphere"
    BOUND_POLY_CAPSULE = "sollumz_bound_poly_capsule"
    BOUND_POLY_CYLINDER = "sollumz_bound_poly_cylinder"
    BOUND_POLY_TRIANGLE = "sollumz_bound_poly_triangle"

    NAVMESH = "sollumz_navmesh"
    NAVMESH_POLY_MESH = "sollumz_navmesh_mesh"
    NAVMESH_PORTAL = "sollumz_navmesh_portal"
    NAVMESH_POINT = "sollumz_navmesh_point"

    CLIP_DICTIONARY = "sollumz_clip_dictionary"
    CLIPS = "sollumz_clips"
    CLIP = "sollumz_clip"
    ANIMATIONS = "sollumz_animations"
    ANIMATION = "sollumz_animation"

    YMAP = "sollumz_ymap"
    YMAP_ENTITY_GROUP = "sollumz_ymap_entity_group"
    YMAP_BOX_OCCLUDER_GROUP = "sollumz_ymap_box_occluder_group"
    YMAP_MODEL_OCCLUDER_GROUP = "sollumz_ymap_model_occluder_group"
    YMAP_CAR_GENERATOR_GROUP = "sollumz_ymap_car_generator_group"
    YMAP_BOX_OCCLUDER = "sollumz_ymap_box_occluder"
    YMAP_MODEL_OCCLUDER = "sollumz_ymap_model_occluder"
    YMAP_CAR_GENERATOR = "sollumz_ymap_car_generator"

    WATER_DATA = "sollumz_water_data"
    WATER_QUADS = "sollumz_water_quads"
    CALMING_QUADS = "sollumz_calming_quads"
    WAVE_QUADS = "sollumz_wave_quads"
    WATER_QUAD = "sollumz_water_quad"
    CALMING_QUAD = "sollumz_calming_quad"
    WAVE_QUAD = "sollumz_wave_quad"


class LightType(str, Enum):
    NONE = "sollumz_light_none"
    POINT = "sollumz_light_point"
    SPOT = "sollumz_light_spot"
    CAPSULE = "sollumz_light_capsule"


class MaterialType(str, Enum):
    NONE = "sollumz_material_none",
    SHADER = "sollumz_material_shader",
    COLLISION = "sollumz_material_collision"
    SHATTER_MAP = "sollumz_material_shard"


class LODLevel(str, Enum):
    VERYHIGH = "sollumz_veryhigh"
    HIGH = "sollumz_high"
    MEDIUM = "sollumz_medium"
    LOW = "sollumz_low"
    VERYLOW = "sollumz_verylow"


LODLevelEnumItems = (
    (LODLevel.HIGH, "High", "", 0),
    (LODLevel.MEDIUM, "Medium", "", 1),
    (LODLevel.LOW, "Low", "", 2),
    (LODLevel.VERYLOW, "Very Low", "", 3),
    (LODLevel.VERYHIGH, "Very High", "", 4),
)


class EntityLodLevel(str, Enum):
    LODTYPES_DEPTH_HD = "sollumz_lodtypes_depth_hd"
    LODTYPES_DEPTH_LOD = "sollumz_lodtypes_depth_lod"
    LODTYPES_DEPTH_SLOD1 = "sollumz_lodtypes_depth_slod1"
    LODTYPES_DEPTH_SLOD2 = "sollumz_lodtypes_depth_slod2"
    LODTYPES_DEPTH_SLOD3 = "sollumz_lodtypes_depth_slod3"
    LODTYPES_DEPTH_SLOD4 = "sollumz_lodtypes_depth_slod4"
    LODTYPES_DEPTH_ORPHANHD = "sollumz_lodtypes_depth_orphanhd"


class EntityPriorityLevel(str, Enum):
    PRI_REQUIRED = "sollumz_pri_required"
    PRI_OPTIONAL_HIGH = "sollumz_pri_optional_high"
    PRI_OPTIONAL_MEDIUM = "sollumz_pri_optional_medium"
    PRI_OPTIONAL_LOW = "sollumz_pri_optional_low"


class ArchetypeType(str, Enum):
    BASE = "sollumz_archetype_base"
    TIME = "sollumz_archetype_time"
    MLO = "sollumz_archetype_mlo"


class AssetType(str, Enum):
    UNITIALIZED = "sollumz_asset_unintialized"
    FRAGMENT = "sollumz_asset_fragment"
    DRAWABLE = "sollumz_asset_drawable"
    DRAWABLE_DICTIONARY = "sollumz_asset_drawable_dictionary"
    ASSETLESS = "sollumz_asset_assetless"


class VehicleLightID(str, Enum):
    NONE = "none"
    ALWAYS_ON = "0"
    LEFT_HEADLIGHT = "1"
    RIGHT_HEADLIGHT = "2"
    LEFT_TAILLIGHT = "3"
    RIGHT_TAILLIGHT = "4"
    FRONT_LEFT_INDICATOR = "5"
    FRONT_RIGHT_INDICATOR = "6"
    REAR_LEFT_INDICATOR = "7"
    REAR_RIGHT_INDICATOR = "8"
    LEFT_BRAKELIGHT = "9"
    RIGHT_BRAKELIGHT = "10"
    CENTER_BRAKELIGHT = "11"
    LEFT_REVERSE_LIGHT = "12"
    RIGHT_REVERSE_LIGHT = "13"
    EXTRA_FRONT_LEFT = "14"
    EXTRA_FRONT_RIGHT = "15"
    EXTRA_REAR_LEFT = "16"
    EXTRA_REAR_RIGHT = "17"
    CUSTOM = "custom"


MIN_VEHICLE_LIGHT_ID = 0
MAX_VEHICLE_LIGHT_ID = 17


FRAGMENT_TYPES = [
    SollumType.FRAGMENT,
    SollumType.FRAGGROUP,
    SollumType.FRAGCHILD,
    SollumType.FRAGLOD,
    SollumType.SHATTERMAP,
]

BOUND_TYPES = [
    SollumType.BOUND_COMPOSITE,
    SollumType.BOUND_BOX,
    SollumType.BOUND_SPHERE,
    SollumType.BOUND_CYLINDER,
    SollumType.BOUND_CAPSULE,
    SollumType.BOUND_DISC,
    SollumType.BOUND_CLOTH,
    SollumType.BOUND_GEOMETRY,
    SollumType.BOUND_GEOMETRYBVH,
]

BOUND_SHAPE_TYPES = [
    SollumType.BOUND_BOX,
    SollumType.BOUND_SPHERE,
    SollumType.BOUND_CYLINDER,
    SollumType.BOUND_CAPSULE,
    SollumType.BOUND_DISC,
    SollumType.BOUND_POLY_BOX,
    SollumType.BOUND_POLY_SPHERE,
    SollumType.BOUND_POLY_CAPSULE,
    SollumType.BOUND_POLY_CYLINDER,
    SollumType.BOUND_POLY_TRIANGLE,
]

BOUND_POLYGON_TYPES = [
    SollumType.BOUND_POLY_BOX,
    SollumType.BOUND_POLY_SPHERE,
    SollumType.BOUND_POLY_CAPSULE,
    SollumType.BOUND_POLY_CYLINDER,
    SollumType.BOUND_POLY_TRIANGLE,
]

DRAWABLE_TYPES = [
    SollumType.DRAWABLE_DICTIONARY,
    SollumType.DRAWABLE,
    SollumType.DRAWABLE_MODEL,
    SollumType.DRAWABLE_GEOMETRY,
    SollumType.SKELETON,
]


YMAP_GROUP_TYPES = [
    SollumType.YMAP,
    SollumType.YMAP_ENTITY_GROUP,
    SollumType.YMAP_BOX_OCCLUDER_GROUP,
    SollumType.YMAP_MODEL_OCCLUDER_GROUP,
    SollumType.YMAP_CAR_GENERATOR_GROUP,
    SollumType.YMAP_BOX_OCCLUDER,
    SollumType.YMAP_MODEL_OCCLUDER,
    SollumType.YMAP_CAR_GENERATOR,
]


SOLLUMZ_UI_NAMES = {
    SollumType.BOUND_BOX: "Bound Box",
    SollumType.BOUND_SPHERE: "Bound Sphere",
    SollumType.BOUND_CAPSULE: "Bound Capsule",
    SollumType.BOUND_CYLINDER: "Bound Cylinder",
    SollumType.BOUND_DISC: "Bound Disc",
    SollumType.BOUND_CLOTH: "Bound Cloth",
    SollumType.BOUND_GEOMETRY: "Bound Geometry",
    SollumType.BOUND_GEOMETRYBVH: "Bound GeometryBVH",
    SollumType.BOUND_COMPOSITE: "Bound Composite",

    SollumType.BOUND_POLY_BOX: "Bound Poly Box",
    SollumType.BOUND_POLY_SPHERE: "Bound Poly Sphere",
    SollumType.BOUND_POLY_CAPSULE: "Bound Poly Capsule",
    SollumType.BOUND_POLY_CYLINDER: "Bound Poly Cylinder",
    SollumType.BOUND_POLY_TRIANGLE: "Bound Poly Mesh",

    SollumType.FRAGMENT: "Fragment",
    SollumType.FRAGGROUP: "Fragment Group",
    SollumType.FRAGCHILD: "Fragment Child",
    SollumType.FRAGLOD: "Fragment LOD",
    SollumType.SHATTERMAP: "Shattermap",

    SollumType.NONE: "None",
    SollumType.DRAWABLE_DICTIONARY: "Drawable Dictionary",
    SollumType.DRAWABLE: "Drawable",
    SollumType.DRAWABLE_MODEL: "Drawable Model",
    SollumType.DRAWABLE_GEOMETRY: "Drawable Geometry",
    SollumType.SKELETON: "Skeleton",
    SollumType.LIGHT: "Light",

    SollumType.NAVMESH: "NavMesh",
    SollumType.NAVMESH_POLY_MESH: "NavMesh Poly Mesh",
    SollumType.NAVMESH_PORTAL: "NavMesh Portal",
    SollumType.NAVMESH_POINT: "NavMesh Point",

    SollumType.CLIP_DICTIONARY: "Clip Dictionary",
    SollumType.CLIPS: "Clips",
    SollumType.CLIP: "Clip",
    SollumType.ANIMATIONS: "Animations",
    SollumType.ANIMATION: "Animation",

    SollumType.YMAP: "Ymap",
    SollumType.YMAP_ENTITY_GROUP: "Entity Group",
    SollumType.YMAP_BOX_OCCLUDER_GROUP: "Box Occluder Group",
    SollumType.YMAP_MODEL_OCCLUDER_GROUP: "Model Occluder Group",
    SollumType.YMAP_CAR_GENERATOR_GROUP: "Car Generator Group",
    SollumType.YMAP_BOX_OCCLUDER: "Box Occluder",
    SollumType.YMAP_MODEL_OCCLUDER: "Model Occluder",
    SollumType.YMAP_CAR_GENERATOR: "Car Generator",

    SollumType.WATER_DATA: "Water Data",
    SollumType.WATER_QUADS: "Water Quads",
    SollumType.WATER_QUAD: "Water Quad",
    SollumType.CALMING_QUADS: "Calming Quads",
    SollumType.CALMING_QUAD: "Calming Quad",
    SollumType.WAVE_QUADS: "Wave Quads",
    SollumType.WAVE_QUAD: "Wave Quad",

    MaterialType.NONE: "None",
    MaterialType.SHADER: "Sollumz Material",
    MaterialType.COLLISION: "Sollumz Collision Material",
    MaterialType.SHATTER_MAP: "Sollumz Shatter Map",

    LODLevel.VERYHIGH: "Very High",
    LODLevel.HIGH: "High",
    LODLevel.MEDIUM: "Medium",
    LODLevel.LOW: "Low",
    LODLevel.VERYLOW: "Very Low",

    EntityLodLevel.LODTYPES_DEPTH_HD: "DEPTH HD",
    EntityLodLevel.LODTYPES_DEPTH_LOD: "DEPTH LOD",
    EntityLodLevel.LODTYPES_DEPTH_SLOD1: "DEPTH SLOD1",
    EntityLodLevel.LODTYPES_DEPTH_SLOD2: "DEPTH SLOD2",
    EntityLodLevel.LODTYPES_DEPTH_SLOD3: "DEPTH SLOD3",
    EntityLodLevel.LODTYPES_DEPTH_SLOD4: "DEPTH SLOD4",
    EntityLodLevel.LODTYPES_DEPTH_ORPHANHD: "DEPTH ORPHAN HD",

    EntityPriorityLevel.PRI_REQUIRED: "REQUIRED",
    EntityPriorityLevel.PRI_OPTIONAL_HIGH: "OPTIONAL HIGH",
    EntityPriorityLevel.PRI_OPTIONAL_MEDIUM: "OPTIONAL MEDIUM",
    EntityPriorityLevel.PRI_OPTIONAL_LOW: "OPTIONAL LOW",

    LightType.NONE: "None",
    LightType.POINT: "Point",
    LightType.SPOT: "Spot",
    LightType.CAPSULE: "Capsule",

    ArchetypeType.BASE: "Base",
    ArchetypeType.TIME: "Time",
    ArchetypeType.MLO: "MLO",

    AssetType.UNITIALIZED: "Uninitialized",
    AssetType.FRAGMENT: "Fragment",
    AssetType.DRAWABLE: "Drawable",
    AssetType.DRAWABLE_DICTIONARY: "Drawable Dictionary",
    AssetType.ASSETLESS: "Assetless",

    VehicleLightID.NONE: "None",
    VehicleLightID.CUSTOM: "Custom",
    VehicleLightID.ALWAYS_ON: "Always On",
    VehicleLightID.LEFT_HEADLIGHT: "Left Headlight (headlight_l)",
    VehicleLightID.RIGHT_HEADLIGHT: "Right Headlight (headlight_r)",
    VehicleLightID.LEFT_TAILLIGHT: "Left Taillight (taillight_l)",
    VehicleLightID.RIGHT_TAILLIGHT: "Right Taillight (taillight_r)",
    VehicleLightID.FRONT_LEFT_INDICATOR: "Front Left Indicator (indicator_lf)",
    VehicleLightID.FRONT_RIGHT_INDICATOR: "Front Right Indicator (indicator_rf)",
    VehicleLightID.REAR_LEFT_INDICATOR: "Rear Left Indicator (indicator_lr)",
    VehicleLightID.REAR_RIGHT_INDICATOR: "Rear Right Indicator (indicator_rr)",
    VehicleLightID.LEFT_BRAKELIGHT: "Left Brakelight (brakelight_l)",
    VehicleLightID.RIGHT_BRAKELIGHT: "Right Brakelight (brakelight_r)",
    VehicleLightID.CENTER_BRAKELIGHT: "Center Brakelight (brakelight_m)",
    VehicleLightID.LEFT_REVERSE_LIGHT: "Left Reversing Light (reversinglight_l)",
    VehicleLightID.RIGHT_REVERSE_LIGHT: "Right Reversing Light (reversinglight_r)",
    VehicleLightID.EXTRA_FRONT_LEFT: "Extra Front Left (extralight_1)",
    VehicleLightID.EXTRA_FRONT_RIGHT: "Extra Front Right (extralight_2)",
    VehicleLightID.EXTRA_REAR_LEFT: "Extra Rear Left (extralight_3)",
    VehicleLightID.EXTRA_REAR_RIGHT: "Extra Rear Right (extralight_4)",

}


# Generate items from provided enums
def items_from_enums(*enums, exclude=None):
    items = []
    for enum in enums:
        for item in enum:
            if exclude is not None and item in exclude:
                continue
            if item not in SOLLUMZ_UI_NAMES:
                raise KeyError(
                    f"UI name mapping not found for key {item} of {enum}.")
            items.append(
                (item.value, SOLLUMZ_UI_NAMES[item], ""))
    return items


class FlagPropertyGroup:
    def get_flag_names(self) -> Sequence[str]:
        return self.flag_names if self.flag_names else self.__annotations__.keys()

    def update_flags_total(self, context):
        # Ensure string can be converted to int
        try:
            int((self.total))
        except ValueError:
            self.total = "0"

        flags = int_to_bool_list(int(self.total), size=self.size)
        for index, flag_name in enumerate(self.get_flag_names()):
            if index >= self.size:
                break

            self[flag_name] = flags[index]

    def update_flag(self, context):
        flags = flag_prop_to_list(self.get_flag_names(), self, size=self.size)
        flags.pop()
        self.total = str(flag_list_to_int(flags))

    # Can be set to a list of strings to override the flags used or their order, otherwise, use the annotations.
    # Useful when the class annotations don't have all the flags (e.g. some flags are defined in base/mixin class)
    flag_names = None

    size = 32

    total: bpy.props.StringProperty(name="Flags", update=update_flags_total, default="0")


time_items = [("0", "12:00 AM", ""),
              ("1", "1:00 AM", ""),
              ("2", "2:00 AM", ""),
              ("3", "3:00 AM", ""),
              ("4", "4:00 AM", ""),
              ("5", "5:00 AM", ""),
              ("6", "6:00 AM", ""),
              ("7", "7:00 AM", ""),
              ("8", "8:00 AM", ""),
              ("9", "9:00 AM", ""),
              ("10", "10:00 AM", ""),
              ("11", "11:00 AM", ""),
              ("12", "12:00 PM", ""),
              ("13", "1:00 PM", ""),
              ("14", "2:00 PM", ""),
              ("15", "3:00 PM", ""),
              ("16", "4:00 PM", ""),
              ("17", "5:00 PM", ""),
              ("18", "6:00 PM", ""),
              ("19", "7:00 PM", ""),
              ("20", "8:00 PM", ""),
              ("21", "9:00 PM", ""),
              ("22", "10:00 PM", ""),
              ("23", "11:00 PM", "")]


class TimeFlagsMixin(FlagPropertyGroup):
    size = 24
    flag_names = [f"hour{i + 1}" for i in range(0, 24)]
    hour1: bpy.props.BoolProperty(name="12:00 AM - 1:00 AM", update=FlagPropertyGroup.update_flag)
    hour2: bpy.props.BoolProperty(name="1:00 AM - 2:00 AM", update=FlagPropertyGroup.update_flag)
    hour3: bpy.props.BoolProperty(name="2:00 AM - 3:00 AM", update=FlagPropertyGroup.update_flag)
    hour4: bpy.props.BoolProperty(name="3:00 AM - 4:00 AM", update=FlagPropertyGroup.update_flag)
    hour5: bpy.props.BoolProperty(name="4:00 AM - 5:00 AM", update=FlagPropertyGroup.update_flag)
    hour6: bpy.props.BoolProperty(name="5:00 AM - 6:00 AM", update=FlagPropertyGroup.update_flag)
    hour7: bpy.props.BoolProperty(name="6:00 AM - 7:00 AM", update=FlagPropertyGroup.update_flag)
    hour8: bpy.props.BoolProperty(name="7:00 AM - 8:00 AM", update=FlagPropertyGroup.update_flag)
    hour9: bpy.props.BoolProperty(name="8:00 AM - 9:00 AM", update=FlagPropertyGroup.update_flag)
    hour10: bpy.props.BoolProperty(name="9:00 AM - 10:00 AM", update=FlagPropertyGroup.update_flag)
    hour11: bpy.props.BoolProperty(name="10:00 AM - 11:00 AM", update=FlagPropertyGroup.update_flag)
    hour12: bpy.props.BoolProperty(name="11:00 AM - 12:00 PM", update=FlagPropertyGroup.update_flag)
    hour13: bpy.props.BoolProperty(name="12:00 PM - 1:00 PM", update=FlagPropertyGroup.update_flag)
    hour14: bpy.props.BoolProperty(name="1:00 PM - 2:00 PM", update=FlagPropertyGroup.update_flag)
    hour15: bpy.props.BoolProperty(name="2:00 PM - 3:00 PM", update=FlagPropertyGroup.update_flag)
    hour16: bpy.props.BoolProperty(name="3:00 PM - 4:00 PM", update=FlagPropertyGroup.update_flag)
    hour17: bpy.props.BoolProperty(name="4:00 PM - 5:00 PM", update=FlagPropertyGroup.update_flag)
    hour18: bpy.props.BoolProperty(name="5:00 PM - 6:00 PM", update=FlagPropertyGroup.update_flag)
    hour19: bpy.props.BoolProperty(name="6:00 PM - 7:00 PM", update=FlagPropertyGroup.update_flag)
    hour20: bpy.props.BoolProperty(name="7:00 PM - 8:00 PM", update=FlagPropertyGroup.update_flag)
    hour21: bpy.props.BoolProperty(name="8:00 PM - 9:00 PM", update=FlagPropertyGroup.update_flag)
    hour22: bpy.props.BoolProperty(name="9:00 PM - 10:00 PM", update=FlagPropertyGroup.update_flag)
    hour23: bpy.props.BoolProperty(name="10:00 PM - 11:00 PM", update=FlagPropertyGroup.update_flag)
    hour24: bpy.props.BoolProperty(name="11:00 PM - 12:00 AM", update=FlagPropertyGroup.update_flag)

    time_flags_start: bpy.props.EnumProperty(items=time_items, name="Time Start")
    time_flags_end: bpy.props.EnumProperty(items=time_items, name="Time End")


class EntityProperties:
    archetype_name: bpy.props.StringProperty(name="Archetype Name")
    flags: bpy.props.IntProperty(name="Flags", default=32)
    guid: bpy.props.FloatProperty(name="GUID")
    parent_index: bpy.props.IntProperty(name="Parent Index", default=-1)
    lod_dist: bpy.props.FloatProperty(name="Lod Distance", default=200)
    child_lod_dist: bpy.props.FloatProperty(name="Child Lod Distance")
    lod_level: bpy.props.EnumProperty(
        items=items_from_enums(EntityLodLevel),
        name="LOD Level",
        default=EntityLodLevel.LODTYPES_DEPTH_ORPHANHD,
        options={"HIDDEN"}
    )
    num_children: bpy.props.IntProperty(name="Number of Children")
    priority_level: bpy.props.EnumProperty(
        items=items_from_enums(EntityPriorityLevel),
        name="Priority Level",
        default=EntityPriorityLevel.PRI_REQUIRED,
        options={"HIDDEN"}
    )
    ambient_occlusion_multiplier: bpy.props.FloatProperty(
        name="Ambient Occlusion Multiplier", default=255)
    artificial_ambient_occlusion: bpy.props.FloatProperty(
        name="Artificial Ambient Occlusion", default=255)
    tint_value: bpy.props.FloatProperty(name="Tint Value")


class ObjectEntityProperties(bpy.types.PropertyGroup, EntityProperties):
    pass


def register():
    bpy.types.Object.sollum_type = bpy.props.EnumProperty(
        items=items_from_enums(SollumType),
        name="Sollumz Type",
        default=SollumType.NONE,
        options={"HIDDEN"}
    )

    bpy.types.Material.sollum_type = bpy.props.EnumProperty(
        items=items_from_enums(MaterialType),
        name="Sollumz Material Type",
        default=MaterialType.NONE,
        options={"HIDDEN"}
    )

    bpy.types.ShaderNode.is_sollumz = bpy.props.BoolProperty(default=False)

    bpy.types.Object.entity_properties = bpy.props.PointerProperty(
        type=ObjectEntityProperties)

    bpy.types.Scene.vert_paint_color1 = bpy.props.FloatVectorProperty(
        name="Vert Color 1",
        subtype="COLOR_GAMMA",
        default=(1.0, 1.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color2 = bpy.props.FloatVectorProperty(
        name="Vert Color 2",
        subtype="COLOR_GAMMA",
        default=(0.0, 0.0, 1.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color3 = bpy.props.FloatVectorProperty(
        name="Vert Color 3",
        subtype="COLOR_GAMMA",
        default=(0.0, 1.0, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color4 = bpy.props.FloatVectorProperty(
        name="Vert Color 4",
        subtype="COLOR_GAMMA",
        default=(1.0, 0.0, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color5 = bpy.props.FloatVectorProperty(
        name="Vert Color 5",
        subtype="COLOR_GAMMA",
        default=(1.0, 0.501961, 0.0, 1.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_color6 = bpy.props.FloatVectorProperty(
        name="Vert Color 6",
        subtype="COLOR_GAMMA",
        default=(0.0, 0.0, 0.0, 0.0),
        min=0,
        max=1,
        size=4
    )

    bpy.types.Scene.vert_paint_alpha = bpy.props.FloatProperty(
        name="Alpha", min=-1, max=1)

    bpy.types.Scene.debug_sollum_type = bpy.props.EnumProperty(
        items=[(SollumType.DRAWABLE.value, SOLLUMZ_UI_NAMES[SollumType.DRAWABLE], SOLLUMZ_UI_NAMES[SollumType.DRAWABLE]),
               (SollumType.DRAWABLE_DICTIONARY.value,
                SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_DICTIONARY], SOLLUMZ_UI_NAMES[SollumType.DRAWABLE_DICTIONARY]),
               (SollumType.BOUND_COMPOSITE.value, SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE], SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE])],
        name="Hierarchy Type",
        default=SollumType.DRAWABLE,
        options={"HIDDEN"}
    )

    bpy.types.Scene.all_sollum_type = bpy.props.EnumProperty(
        items=sorted(items_from_enums(SollumType), key=lambda i: i[0]),
        name="Sollum Types",
        options={"HIDDEN"}
    )

    bpy.types.Scene.debug_lights_only_selected = bpy.props.BoolProperty(
        name="Limit to Selected", description="Only set intensity of the selected lights. (All instances will be affected)")

    bpy.types.Scene.sollumz_export_path = bpy.props.StringProperty(
        name="Export Path",
        default="",
        description="The path where files will be exported. If not set, the export dialog will be opened",
        subtype="DIR_PATH",
    )


def unregister():
    del bpy.types.Object.sollum_type
    del bpy.types.Material.sollum_type
    del bpy.types.Object.entity_properties
    del bpy.types.Scene.vert_paint_alpha
    del bpy.types.Scene.debug_sollum_type
    del bpy.types.Scene.all_sollum_type
    del bpy.types.Scene.debug_lights_only_selected
    del bpy.types.Scene.sollumz_export_path
