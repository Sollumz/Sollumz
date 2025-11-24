from bpy.types import (
    Material
)
from ..shared.shader_expr.builtins import (
    bsdf_diffuse,
    vec,
)
from ..shared.shader_expr import (
    expr,
    compile_to_material,
)
from szio.gta5 import CollisionMaterial
from ..sollumz_properties import MaterialType
from typing import NamedTuple
from .. import logger


class CollisionMaterialDef(NamedTuple):
    name: str
    ui_name: str
    color: tuple[int, int, int]
    density: float


collisionmats = [
    # fmt: off
    CollisionMaterialDef("DEFAULT",                    "Default",                    (255,   0, 255),  1750.0),
    CollisionMaterialDef("CONCRETE",                   "Concrete",                   (145, 145, 145),  7850.5),
    CollisionMaterialDef("CONCRETE_POTHOLE",           "Concrete Pothole",           (145, 145, 145),  4900.0),
    CollisionMaterialDef("CONCRETE_DUSTY",             "Concrete Dusty",             (145, 140, 130),  7850.5),
    CollisionMaterialDef("TARMAC",                     "Tarmac",                     ( 90,  90,  90),  6300.0),
    CollisionMaterialDef("TARMAC_PAINTED",             "Tarmac Painted",             ( 90,  90,  90),  6300.0),
    CollisionMaterialDef("TARMAC_POTHOLE",             "Tarmac Pothole",             ( 70,  70,  70),  4900.0),
    CollisionMaterialDef("RUMBLE_STRIP",               "Rumble Strip",               ( 90,  90,  90),  6300.0),
    CollisionMaterialDef("BREEZE_BLOCK",               "Breeze Block",               (145, 145, 145),  7000.0),
    CollisionMaterialDef("ROCK",                       "Rock",                       (185, 185, 185),  7000.0),
    CollisionMaterialDef("ROCK_MOSSY",                 "Rock Mossy",                 (185, 185, 185),  7000.0),
    CollisionMaterialDef("STONE",                      "Stone",                      (185, 185, 185),  7000.0),
    CollisionMaterialDef("COBBLESTONE",                "Cobblestone",                (185, 185, 185),  7000.0),
    CollisionMaterialDef("BRICK",                      "Brick",                      (195,  95,  30),  7000.0),
    CollisionMaterialDef("MARBLE",                     "Marble",                     (195, 155, 145),  8970.5),
    CollisionMaterialDef("PAVING_SLAB",                "Paving Slab",                (200, 165, 130),  7000.0),
    CollisionMaterialDef("SANDSTONE_SOLID",            "Sandstone Solid",            (215, 195, 150),  8130.5),
    CollisionMaterialDef("SANDSTONE_BRITTLE",          "Sandstone Brittle",          (205, 180, 120),  5075.0),
    CollisionMaterialDef("SAND_LOOSE",                 "Sand Loose",                 (235, 220, 190),  5047.0),
    CollisionMaterialDef("SAND_COMPACT",               "Sand Compact",               (250, 240, 220),  5950.0),
    CollisionMaterialDef("SAND_WET",                   "Sand Wet",                   (190, 185, 165),  6727.0),
    CollisionMaterialDef("SAND_TRACK",                 "Sand Track",                 (250, 240, 220),  5775.0),
    CollisionMaterialDef("SAND_UNDERWATER",            "Sand Underwater",            (135, 130, 120),  5775.0),
    CollisionMaterialDef("SAND_DRY_DEEP",              "Sand Dry Deep",              (110, 100,  85),  5047.0),
    CollisionMaterialDef("SAND_WET_DEEP",              "Sand Wet Deep",              (110, 100,  85),  6727.0),
    CollisionMaterialDef("ICE",                        "Ice",                        (200, 250, 255),  3216.5),
    CollisionMaterialDef("ICE_TARMAC",                 "Ice Tarmac",                 (200, 250, 255),  3216.5),
    CollisionMaterialDef("SNOW_LOOSE",                 "Snow Loose",                 (255, 255, 255),   560.0),
    CollisionMaterialDef("SNOW_COMPACT",               "Snow Compact",               (255, 255, 255),  1683.5),
    CollisionMaterialDef("SNOW_DEEP",                  "Snow Deep",                  (255, 255, 255),   560.0),
    CollisionMaterialDef("SNOW_TARMAC",                "Snow Tarmac",                (255, 255, 255),  6300.0),
    CollisionMaterialDef("GRAVEL_SMALL",               "Gravel Small",               (255, 255, 255),  6727.0),
    CollisionMaterialDef("GRAVEL_LARGE",               "Gravel Large",               (255, 255, 255),  5887.0),
    CollisionMaterialDef("GRAVEL_DEEP",                "Gravel Deep",                (255, 255, 255),  6727.0),
    CollisionMaterialDef("GRAVEL_TRAIN_TRACK",         "Gravel Train Track",         (145, 140, 130),  6727.0),
    CollisionMaterialDef("DIRT_TRACK",                 "Dirt Track",                 (175, 160, 140),  4550.0),
    CollisionMaterialDef("MUD_HARD",                   "Mud Hard",                   (175, 160, 140),  5327.0),
    CollisionMaterialDef("MUD_POTHOLE",                "Mud Pothole",                (105,  95,  75),  4200.0),
    CollisionMaterialDef("MUD_SOFT",                   "Mud Soft",                   (105,  95,  75),  6055.0),
    CollisionMaterialDef("MUD_UNDERWATER",             "Mud Underwater",             ( 75,  65,  50),  6055.0),
    CollisionMaterialDef("MUD_DEEP",                   "Mud Deep",                   (105,  95,  75),  6055.0),
    CollisionMaterialDef("MARSH",                      "Marsh",                      (105,  95,  75),  6055.0),
    CollisionMaterialDef("MARSH_DEEP",                 "Marsh Deep",                 (105,  95,  75),  6055.0),
    CollisionMaterialDef("SOIL",                       "Soil",                       (105,  95,  75),  5047.0),
    CollisionMaterialDef("CLAY_HARD",                  "Clay Hard",                  (160, 160, 160),  6111.0),
    CollisionMaterialDef("CLAY_SOFT",                  "Clay Soft",                  (160, 160, 160),  3755.5),
    CollisionMaterialDef("GRASS_LONG",                 "Grass Long",                 (130, 205,  75),  4900.0),
    CollisionMaterialDef("GRASS",                      "Grass",                      (130, 205,  75),  5600.0),
    CollisionMaterialDef("GRASS_SHORT",                "Grass Short",                (130, 205,  75),  5950.0),
    CollisionMaterialDef("HAY",                        "Hay",                        (240, 205, 125),  5950.0),
    CollisionMaterialDef("BUSHES",                     "Bushes",                     ( 85, 160,  30),   525.0),
    CollisionMaterialDef("TWIGS",                      "Twigs",                      (115, 100,  70),   700.0),
    CollisionMaterialDef("LEAVES",                     "Leaves",                     ( 70, 100,  50),   350.0),
    CollisionMaterialDef("WOODCHIPS",                  "Woodchips",                  (115, 100,  70),  1820.0),
    CollisionMaterialDef("TREE_BARK",                  "Tree Bark",                  (115, 100,  70),   840.0),
    CollisionMaterialDef("METAL_SOLID_SMALL",          "Metal Solid Small",          (155, 180, 190), 24500.0),
    CollisionMaterialDef("METAL_SOLID_MEDIUM",         "Metal Solid Medium",         (155, 180, 190), 28000.0),
    CollisionMaterialDef("METAL_SOLID_LARGE",          "Metal Solid Large",          (155, 180, 190), 31500.0),
    CollisionMaterialDef("METAL_HOLLOW_SMALL",         "Metal Hollow Small",         (155, 180, 190),  1750.0),
    CollisionMaterialDef("METAL_HOLLOW_MEDIUM",        "Metal Hollow Medium",        (155, 180, 190),  2100.0),
    CollisionMaterialDef("METAL_HOLLOW_LARGE",         "Metal Hollow Large",         (155, 180, 190),  2450.0),
    CollisionMaterialDef("METAL_CHAINLINK_SMALL",      "Metal Chainlink Small",      (155, 180, 190),  3500.0),
    CollisionMaterialDef("METAL_CHAINLINK_LARGE",      "Metal Chainlink Large",      (155, 180, 190),  3850.0),
    CollisionMaterialDef("METAL_CORRUGATED_IRON",      "Metal Corrugated Iron",      (155, 180, 190), 21000.0),
    CollisionMaterialDef("METAL_GRILLE",               "Metal Grille",               (155, 180, 190),  3500.0),
    CollisionMaterialDef("METAL_RAILING",              "Metal Railing",              (155, 180, 190),  4200.0),
    CollisionMaterialDef("METAL_DUCT",                 "Metal Duct",                 (155, 180, 190),  1750.0),
    CollisionMaterialDef("METAL_GARAGE_DOOR",          "Metal Garage Door",          (155, 180, 190), 31500.0),
    CollisionMaterialDef("METAL_MANHOLE",              "Metal Manhole",              (155, 180, 190), 31500.0),
    CollisionMaterialDef("WOOD_SOLID_SMALL",           "Wood Solid Small",           (155, 130,  95),  1400.0),
    CollisionMaterialDef("WOOD_SOLID_MEDIUM",          "Wood Solid Medium",          (155, 130,  95),  2100.0),
    CollisionMaterialDef("WOOD_SOLID_LARGE",           "Wood Solid Large",           (155, 130,  95),  2852.5),
    CollisionMaterialDef("WOOD_SOLID_POLISHED",        "Wood Solid Polished",        (155, 130,  95),  2800.0),
    CollisionMaterialDef("WOOD_FLOOR_DUSTY",           "Wood Floor Dusty",           (165, 145, 110),  2100.0),
    CollisionMaterialDef("WOOD_HOLLOW_SMALL",          "Wood Hollow Small",          (170, 150, 125),   350.0),
    CollisionMaterialDef("WOOD_HOLLOW_MEDIUM",         "Wood Hollow Medium",         (170, 150, 125),   700.0),
    CollisionMaterialDef("WOOD_HOLLOW_LARGE",          "Wood Hollow Large",          (170, 150, 125),  1050.0),
    CollisionMaterialDef("WOOD_CHIPBOARD",             "Wood Chipboard",             (170, 150, 125),   595.0),
    CollisionMaterialDef("WOOD_OLD_CREAKY",            "Wood Old Creaky",            (155, 130,  95),  2100.0),
    CollisionMaterialDef("WOOD_HIGH_DENSITY",          "Wood High Density",          (155, 130,  95), 21000.0),
    CollisionMaterialDef("WOOD_LATTICE",               "Wood Lattice",               (155, 130,  95),  1400.0),
    CollisionMaterialDef("CERAMIC",                    "Ceramic",                    (220, 210, 195),  9695.0),
    CollisionMaterialDef("ROOF_TILE",                  "Roof Tile",                  (220, 210, 195),  7000.0),
    CollisionMaterialDef("ROOF_FELT",                  "Roof Felt",                  (165, 145, 110),  5250.0),
    CollisionMaterialDef("FIBREGLASS",                 "Fibreglass",                 (255, 250, 210),  1750.0),
    CollisionMaterialDef("TARPAULIN",                  "Tarpaulin",                  (255, 250, 210),  2800.0),
    CollisionMaterialDef("PLASTIC",                    "Plastic",                    (255, 250, 210),  3500.0),
    CollisionMaterialDef("PLASTIC_HOLLOW",             "Plastic Hollow",             (240, 230, 185),   875.0),
    CollisionMaterialDef("PLASTIC_HIGH_DENSITY",       "Plastic High Density",       (255, 250, 210), 21000.0),
    CollisionMaterialDef("PLASTIC_CLEAR",              "Plastic Clear",              (255, 250, 210),  3500.0),
    CollisionMaterialDef("PLASTIC_HOLLOW_CLEAR",       "Plastic Hollow Clear",       (240, 230, 185),   875.0),
    CollisionMaterialDef("PLASTIC_HIGH_DENSITY_CLEAR", "Plastic High Density Clear", (255, 250, 210), 21000.0),
    CollisionMaterialDef("FIBREGLASS_HOLLOW",          "Fibreglass Hollow",          (240, 230, 185),   126.0),
    CollisionMaterialDef("RUBBER",                     "Rubber",                     ( 70,  70,  70),  4200.0),
    CollisionMaterialDef("RUBBER_HOLLOW",              "Rubber Hollow",              ( 70,  70,  70),   875.0),
    CollisionMaterialDef("LINOLEUM",                   "Linoleum",                   (205, 150,  80),  1925.0),
    CollisionMaterialDef("LAMINATE",                   "Laminate",                   (170, 150, 125),  2800.0),
    CollisionMaterialDef("CARPET_SOLID",               "Carpet Solid",               (250, 100, 100),  1050.0),
    CollisionMaterialDef("CARPET_SOLID_DUSTY",         "Carpet Solid Dusty",         (255, 135, 135),  1050.0),
    CollisionMaterialDef("CARPET_FLOORBOARD",          "Carpet Floorboard",          (250, 100, 100),  1750.0),
    CollisionMaterialDef("CLOTH",                      "Cloth",                      (250, 100, 100),   875.0),
    CollisionMaterialDef("PLASTER_SOLID",              "Plaster Solid",              (145, 145, 145),  2971.5),
    CollisionMaterialDef("PLASTER_BRITTLE",            "Plaster Brittle",            (225, 225, 225),  2971.5),
    CollisionMaterialDef("CARDBOARD_SHEET",            "Cardboard Sheet",            (120, 115,  95),   400.0),
    CollisionMaterialDef("CARDBOARD_BOX",              "Cardboard Box",              (120, 115,  95),   200.0),
    CollisionMaterialDef("PAPER",                      "Paper",                      (230, 225, 220),  4203.5),
    CollisionMaterialDef("FOAM",                       "Foam",                       (230, 235, 240),   175.0),
    CollisionMaterialDef("FEATHER_PILLOW",             "Feather Pillow",             (230, 230, 230),   192.5),
    CollisionMaterialDef("POLYSTYRENE",                "Polystyrene",                (255, 250, 210),   157.5),
    CollisionMaterialDef("LEATHER",                    "Leather",                    (250, 100, 100),  3307.5),
    CollisionMaterialDef("TVSCREEN",                   "Tvscreen",                   (115, 125, 125),  9026.5),
    CollisionMaterialDef("SLATTED_BLINDS",             "Slatted Blinds",             (255, 250, 210),  8750.0),
    CollisionMaterialDef("GLASS_SHOOT_THROUGH",        "Glass Shoot Through",        (205, 240, 255),  8750.0),
    CollisionMaterialDef("GLASS_BULLETPROOF",          "Glass Bulletproof",          (115, 125, 125),  8750.0),
    CollisionMaterialDef("GLASS_OPAQUE",               "Glass Opaque",               (205, 240, 255),  8750.0),
    CollisionMaterialDef("PERSPEX",                    "Perspex",                    (205, 240, 255),  4130.0),
    CollisionMaterialDef("CAR_METAL",                  "Car Metal",                  (255, 255, 255),  3363.5),
    CollisionMaterialDef("CAR_PLASTIC",                "Car Plastic",                (255, 255, 255),  1750.0),
    CollisionMaterialDef("CAR_SOFTTOP",                "Car Softtop",                (250, 100, 100),  1750.0),
    CollisionMaterialDef("CAR_SOFTTOP_CLEAR",          "Car Softtop Clear",          (250, 100, 100),  1750.0),
    CollisionMaterialDef("CAR_GLASS_WEAK",             "Car Glass Weak",             (210, 245, 245),  8750.0),
    CollisionMaterialDef("CAR_GLASS_MEDIUM",           "Car Glass Medium",           (210, 245, 245),  8750.0),
    CollisionMaterialDef("CAR_GLASS_STRONG",           "Car Glass Strong",           (210, 245, 245),  8750.0),
    CollisionMaterialDef("CAR_GLASS_BULLETPROOF",      "Car Glass Bulletproof",      (210, 245, 245),  8750.0),
    CollisionMaterialDef("CAR_GLASS_OPAQUE",           "Car Glass Opaque",           (210, 245, 245),  8750.0),
    CollisionMaterialDef("WATER",                      "Water",                      ( 55, 145, 230),  3573.5),
    CollisionMaterialDef("BLOOD",                      "Blood",                      (205,   5,   5),  3573.5),
    CollisionMaterialDef("OIL",                        "Oil",                        ( 80,  65,  65),  3573.5),
    CollisionMaterialDef("PETROL",                     "Petrol",                     ( 70, 100, 120),  3573.5),
    CollisionMaterialDef("FRESH_MEAT",                 "Fresh Meat",                 (255,  55,  20),  4200.0),
    CollisionMaterialDef("DRIED_MEAT",                 "Dried Meat",                 (185, 100,  85),  4200.0),
    CollisionMaterialDef("EMISSIVE_GLASS",             "Emissive Glass",             (205, 240, 255),  8750.0),
    CollisionMaterialDef("EMISSIVE_PLASTIC",           "Emissive Plastic",           (255, 250, 210),  3500.0),
    CollisionMaterialDef("VFX_METAL_ELECTRIFIED",      "Vfx Metal Electrified",      (155, 180, 190),  2100.0),
    CollisionMaterialDef("VFX_METAL_WATER_TOWER",      "Vfx Metal Water Tower",      (155, 180, 190),  2100.0),
    CollisionMaterialDef("VFX_METAL_STEAM",            "Vfx Metal Steam",            (155, 180, 190),  2100.0),
    CollisionMaterialDef("VFX_METAL_FLAME",            "Vfx Metal Flame",            (155, 180, 190),  2100.0),
    CollisionMaterialDef("PHYS_NO_FRICTION",           "Phys No Friction",           (  0,   0,   0),  1750.0),
    CollisionMaterialDef("PHYS_GOLF_BALL",             "Phys Golf Ball",             (  0,   0,   0),   577.5),
    CollisionMaterialDef("PHYS_TENNIS_BALL",           "Phys Tennis Ball",           (  0,   0,   0),   350.0),
    CollisionMaterialDef("PHYS_CASTER",                "Phys Caster",                (  0,   0,   0),  1750.0),
    CollisionMaterialDef("PHYS_CASTER_RUSTY",          "Phys Caster Rusty",          (  0,   0,   0),  1750.0),
    CollisionMaterialDef("PHYS_CAR_VOID",              "Phys Car Void",              (  0,   0,   0),  1750.0),
    CollisionMaterialDef("PHYS_PED_CAPSULE",           "Phys Ped Capsule",           (  0,   0,   0),  1750.0),
    CollisionMaterialDef("PHYS_ELECTRIC_FENCE",        "Phys Electric Fence",        (  0,   0,   0),  1750.0),
    CollisionMaterialDef("PHYS_ELECTRIC_METAL",        "Phys Electric Metal",        (  0,   0,   0),  1750.0),
    CollisionMaterialDef("PHYS_BARBED_WIRE",           "Phys Barbed Wire",           (  0,   0,   0),  1750.0),
    CollisionMaterialDef("PHYS_POOLTABLE_SURFACE",     "Phys Pooltable Surface",     (155, 130,  95),  8750.0),
    CollisionMaterialDef("PHYS_POOLTABLE_CUSHION",     "Phys Pooltable Cushion",     (155, 130,  95),  8750.0),
    CollisionMaterialDef("PHYS_POOLTABLE_BALL",        "Phys Pooltable Ball",        (255, 250, 210),  8750.0),
    CollisionMaterialDef("BUTTOCKS",                   "Buttocks",                   (  0,   0,   0),   350.0),
    CollisionMaterialDef("THIGH_LEFT",                 "Thigh Left",                 (  0,   0,   0),   350.0),
    CollisionMaterialDef("SHIN_LEFT",                  "Shin Left",                  (  0,   0,   0),   350.0),
    CollisionMaterialDef("FOOT_LEFT",                  "Foot Left",                  (  0,   0,   0),   350.0),
    CollisionMaterialDef("THIGH_RIGHT",                "Thigh Right",                (  0,   0,   0),   350.0),
    CollisionMaterialDef("SHIN_RIGHT",                 "Shin Right",                 (  0,   0,   0),   350.0),
    CollisionMaterialDef("FOOT_RIGHT",                 "Foot Right",                 (  0,   0,   0),   350.0),
    CollisionMaterialDef("SPINE0",                     "Spine0",                     (  0,   0,   0),   350.0),
    CollisionMaterialDef("SPINE1",                     "Spine1",                     (  0,   0,   0),   350.0),
    CollisionMaterialDef("SPINE2",                     "Spine2",                     (  0,   0,   0),   350.0),
    CollisionMaterialDef("SPINE3",                     "Spine3",                     (  0,   0,   0),   350.0),
    CollisionMaterialDef("CLAVICLE_LEFT",              "Clavicle Left",              (  0,   0,   0),   350.0),
    CollisionMaterialDef("UPPER_ARM_LEFT",             "Upper Arm Left",             (  0,   0,   0),   350.0),
    CollisionMaterialDef("LOWER_ARM_LEFT",             "Lower Arm Left",             (  0,   0,   0),   350.0),
    CollisionMaterialDef("HAND_LEFT",                  "Hand Left",                  (  0,   0,   0),   350.0),
    CollisionMaterialDef("CLAVICLE_RIGHT",             "Clavicle Right",             (  0,   0,   0),   350.0),
    CollisionMaterialDef("UPPER_ARM_RIGHT",            "Upper Arm Right",            (  0,   0,   0),   350.0),
    CollisionMaterialDef("LOWER_ARM_RIGHT",            "Lower Arm Right",            (  0,   0,   0),   350.0),
    CollisionMaterialDef("HAND_RIGHT",                 "Hand Right",                 (  0,   0,   0),   350.0),
    CollisionMaterialDef("NECK",                       "Neck",                       (  0,   0,   0),   350.0),
    CollisionMaterialDef("HEAD",                       "Head",                       (  0,   0,   0),   350.0),
    CollisionMaterialDef("ANIMAL_DEFAULT",             "Animal Default",             (  0,   0,   0),   350.0),
    CollisionMaterialDef("CAR_ENGINE",                 "Car Engine",                 (255, 255, 255),  3363.5),
    CollisionMaterialDef("PUDDLE",                     "Puddle",                     ( 55, 145, 230),  3573.5),
    CollisionMaterialDef("CONCRETE_PAVEMENT",          "Concrete Pavement",          (145, 145, 145),  7850.5),
    CollisionMaterialDef("BRICK_PAVEMENT",             "Brick Pavement",             (195,  95,  30),  7000.0),
    CollisionMaterialDef("PHYS_DYNAMIC_COVER_BOUND",   "Phys Dynamic Cover Bound",   (  0,   0,   0),  1750.0),
    CollisionMaterialDef("VFX_WOOD_BEER_BARREL",       "Vfx Wood Beer Barrel",       (155, 130,  95),  1400.0),
    CollisionMaterialDef("WOOD_HIGH_FRICTION",         "Wood High Friction",         (155, 130,  95),  1400.0),
    CollisionMaterialDef("ROCK_NOINST",                "Rock Noinst",                (185, 185, 185),  7000.0),
    CollisionMaterialDef("BUSHES_NOINST",              "Bushes Noinst",              ( 85, 160,  30),   525.0),
    CollisionMaterialDef("METAL_SOLID_ROAD_SURFACE",   "Metal Solid Road Surface",   (155, 180, 190), 28000.0),
    CollisionMaterialDef("STUNT_RAMP_SURFACE",         "Stunt Ramp Surface",         (155, 180, 190), 28000.0),
    CollisionMaterialDef("TEMP_01",                    "Temp 01",                    (255,   0, 255),  5950.0),
    CollisionMaterialDef("TEMP_02",                    "Temp 02",                    (255,   0, 255),  5950.0),
    # fmt: on
]


def collision_material_shader_expr(r: float, g: float, b: float) -> expr.ShaderExpr:
    return bsdf_diffuse(
        color=vec(r, g, b),
    )


def create_collision_material_from_index(index: int) -> Material:
    matinfo = collisionmats[0]

    try:
        matinfo = collisionmats[index]
    except IndexError:
        logger.warning(f"Invalid material index '{index}'! Setting to default...")

    r, g, b = matinfo.color
    r /= 255
    g /= 255
    b /= 255

    mat = compile_to_material(matinfo.name, collision_material_shader_expr(r, g, b))
    mat.sollum_type = MaterialType.COLLISION
    mat.collision_properties.collision_index = index
    mat.diffuse_color = r, g, b, 1.0
    return mat


def create_collision_material_from_data(material: CollisionMaterial) -> Material:
    mat = create_collision_material_from_index(material.material_index)
    mat.collision_properties.procedural_id = material.procedural_id
    mat.collision_properties.room_id = material.room_id
    mat.collision_properties.ped_density = material.ped_density
    mat.collision_properties.material_color_index = material.material_color_index
    mat_flags = material.material_flags.value
    # TODO: refactor so we don't need to split the flags here
    from .properties import set_collision_mat_raw_flags
    set_collision_mat_raw_flags(
        mat.collision_flags,
        mat_flags & 0xFF,
        (mat_flags >> 8) & 0xFF
    )
    return mat
