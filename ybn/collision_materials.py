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
from ..sollumz_properties import MaterialType
from typing import NamedTuple
from .. import logger


class CollisionMaterial(NamedTuple):
    name: str
    ui_name: str
    color: tuple[int, int, int]
    density: float


collisionmats = [
    # fmt: off
    CollisionMaterial("DEFAULT",                    "Default",                    (255,   0, 255),  1750.0),
    CollisionMaterial("CONCRETE",                   "Concrete",                   (145, 145, 145),  7850.5),
    CollisionMaterial("CONCRETE_POTHOLE",           "Concrete Pothole",           (145, 145, 145),  4900.0),
    CollisionMaterial("CONCRETE_DUSTY",             "Concrete Dusty",             (145, 140, 130),  7850.5),
    CollisionMaterial("TARMAC",                     "Tarmac",                     ( 90,  90,  90),  6300.0),
    CollisionMaterial("TARMAC_PAINTED",             "Tarmac Painted",             ( 90,  90,  90),  6300.0),
    CollisionMaterial("TARMAC_POTHOLE",             "Tarmac Pothole",             ( 70,  70,  70),  4900.0),
    CollisionMaterial("RUMBLE_STRIP",               "Rumble Strip",               ( 90,  90,  90),  6300.0),
    CollisionMaterial("BREEZE_BLOCK",               "Breeze Block",               (145, 145, 145),  7000.0),
    CollisionMaterial("ROCK",                       "Rock",                       (185, 185, 185),  7000.0),
    CollisionMaterial("ROCK_MOSSY",                 "Rock Mossy",                 (185, 185, 185),  7000.0),
    CollisionMaterial("STONE",                      "Stone",                      (185, 185, 185),  7000.0),
    CollisionMaterial("COBBLESTONE",                "Cobblestone",                (185, 185, 185),  7000.0),
    CollisionMaterial("BRICK",                      "Brick",                      (195,  95,  30),  7000.0),
    CollisionMaterial("MARBLE",                     "Marble",                     (195, 155, 145),  8970.5),
    CollisionMaterial("PAVING_SLAB",                "Paving Slab",                (200, 165, 130),  7000.0),
    CollisionMaterial("SANDSTONE_SOLID",            "Sandstone Solid",            (215, 195, 150),  8130.5),
    CollisionMaterial("SANDSTONE_BRITTLE",          "Sandstone Brittle",          (205, 180, 120),  5075.0),
    CollisionMaterial("SAND_LOOSE",                 "Sand Loose",                 (235, 220, 190),  5047.0),
    CollisionMaterial("SAND_COMPACT",               "Sand Compact",               (250, 240, 220),  5950.0),
    CollisionMaterial("SAND_WET",                   "Sand Wet",                   (190, 185, 165),  6727.0),
    CollisionMaterial("SAND_TRACK",                 "Sand Track",                 (250, 240, 220),  5775.0),
    CollisionMaterial("SAND_UNDERWATER",            "Sand Underwater",            (135, 130, 120),  5775.0),
    CollisionMaterial("SAND_DRY_DEEP",              "Sand Dry Deep",              (110, 100,  85),  5047.0),
    CollisionMaterial("SAND_WET_DEEP",              "Sand Wet Deep",              (110, 100,  85),  6727.0),
    CollisionMaterial("ICE",                        "Ice",                        (200, 250, 255),  3216.5),
    CollisionMaterial("ICE_TARMAC",                 "Ice Tarmac",                 (200, 250, 255),  3216.5),
    CollisionMaterial("SNOW_LOOSE",                 "Snow Loose",                 (255, 255, 255),   560.0),
    CollisionMaterial("SNOW_COMPACT",               "Snow Compact",               (255, 255, 255),  1683.5),
    CollisionMaterial("SNOW_DEEP",                  "Snow Deep",                  (255, 255, 255),   560.0),
    CollisionMaterial("SNOW_TARMAC",                "Snow Tarmac",                (255, 255, 255),  6300.0),
    CollisionMaterial("GRAVEL_SMALL",               "Gravel Small",               (255, 255, 255),  6727.0),
    CollisionMaterial("GRAVEL_LARGE",               "Gravel Large",               (255, 255, 255),  5887.0),
    CollisionMaterial("GRAVEL_DEEP",                "Gravel Deep",                (255, 255, 255),  6727.0),
    CollisionMaterial("GRAVEL_TRAIN_TRACK",         "Gravel Train Track",         (145, 140, 130),  6727.0),
    CollisionMaterial("DIRT_TRACK",                 "Dirt Track",                 (175, 160, 140),  4550.0),
    CollisionMaterial("MUD_HARD",                   "Mud Hard",                   (175, 160, 140),  5327.0),
    CollisionMaterial("MUD_POTHOLE",                "Mud Pothole",                (105,  95,  75),  4200.0),
    CollisionMaterial("MUD_SOFT",                   "Mud Soft",                   (105,  95,  75),  6055.0),
    CollisionMaterial("MUD_UNDERWATER",             "Mud Underwater",             ( 75,  65,  50),  6055.0),
    CollisionMaterial("MUD_DEEP",                   "Mud Deep",                   (105,  95,  75),  6055.0),
    CollisionMaterial("MARSH",                      "Marsh",                      (105,  95,  75),  6055.0),
    CollisionMaterial("MARSH_DEEP",                 "Marsh Deep",                 (105,  95,  75),  6055.0),
    CollisionMaterial("SOIL",                       "Soil",                       (105,  95,  75),  5047.0),
    CollisionMaterial("CLAY_HARD",                  "Clay Hard",                  (160, 160, 160),  6111.0),
    CollisionMaterial("CLAY_SOFT",                  "Clay Soft",                  (160, 160, 160),  3755.5),
    CollisionMaterial("GRASS_LONG",                 "Grass Long",                 (130, 205,  75),  4900.0),
    CollisionMaterial("GRASS",                      "Grass",                      (130, 205,  75),  5600.0),
    CollisionMaterial("GRASS_SHORT",                "Grass Short",                (130, 205,  75),  5950.0),
    CollisionMaterial("HAY",                        "Hay",                        (240, 205, 125),  5950.0),
    CollisionMaterial("BUSHES",                     "Bushes",                     ( 85, 160,  30),   525.0),
    CollisionMaterial("TWIGS",                      "Twigs",                      (115, 100,  70),   700.0),
    CollisionMaterial("LEAVES",                     "Leaves",                     ( 70, 100,  50),   350.0),
    CollisionMaterial("WOODCHIPS",                  "Woodchips",                  (115, 100,  70),  1820.0),
    CollisionMaterial("TREE_BARK",                  "Tree Bark",                  (115, 100,  70),   840.0),
    CollisionMaterial("METAL_SOLID_SMALL",          "Metal Solid Small",          (155, 180, 190), 24500.0),
    CollisionMaterial("METAL_SOLID_MEDIUM",         "Metal Solid Medium",         (155, 180, 190), 28000.0),
    CollisionMaterial("METAL_SOLID_LARGE",          "Metal Solid Large",          (155, 180, 190), 31500.0),
    CollisionMaterial("METAL_HOLLOW_SMALL",         "Metal Hollow Small",         (155, 180, 190),  1750.0),
    CollisionMaterial("METAL_HOLLOW_MEDIUM",        "Metal Hollow Medium",        (155, 180, 190),  2100.0),
    CollisionMaterial("METAL_HOLLOW_LARGE",         "Metal Hollow Large",         (155, 180, 190),  2450.0),
    CollisionMaterial("METAL_CHAINLINK_SMALL",      "Metal Chainlink Small",      (155, 180, 190),  3500.0),
    CollisionMaterial("METAL_CHAINLINK_LARGE",      "Metal Chainlink Large",      (155, 180, 190),  3850.0),
    CollisionMaterial("METAL_CORRUGATED_IRON",      "Metal Corrugated Iron",      (155, 180, 190), 21000.0),
    CollisionMaterial("METAL_GRILLE",               "Metal Grille",               (155, 180, 190),  3500.0),
    CollisionMaterial("METAL_RAILING",              "Metal Railing",              (155, 180, 190),  4200.0),
    CollisionMaterial("METAL_DUCT",                 "Metal Duct",                 (155, 180, 190),  1750.0),
    CollisionMaterial("METAL_GARAGE_DOOR",          "Metal Garage Door",          (155, 180, 190), 31500.0),
    CollisionMaterial("METAL_MANHOLE",              "Metal Manhole",              (155, 180, 190), 31500.0),
    CollisionMaterial("WOOD_SOLID_SMALL",           "Wood Solid Small",           (155, 130,  95),  1400.0),
    CollisionMaterial("WOOD_SOLID_MEDIUM",          "Wood Solid Medium",          (155, 130,  95),  2100.0),
    CollisionMaterial("WOOD_SOLID_LARGE",           "Wood Solid Large",           (155, 130,  95),  2852.5),
    CollisionMaterial("WOOD_SOLID_POLISHED",        "Wood Solid Polished",        (155, 130,  95),  2800.0),
    CollisionMaterial("WOOD_FLOOR_DUSTY",           "Wood Floor Dusty",           (165, 145, 110),  2100.0),
    CollisionMaterial("WOOD_HOLLOW_SMALL",          "Wood Hollow Small",          (170, 150, 125),   350.0),
    CollisionMaterial("WOOD_HOLLOW_MEDIUM",         "Wood Hollow Medium",         (170, 150, 125),   700.0),
    CollisionMaterial("WOOD_HOLLOW_LARGE",          "Wood Hollow Large",          (170, 150, 125),  1050.0),
    CollisionMaterial("WOOD_CHIPBOARD",             "Wood Chipboard",             (170, 150, 125),   595.0),
    CollisionMaterial("WOOD_OLD_CREAKY",            "Wood Old Creaky",            (155, 130,  95),  2100.0),
    CollisionMaterial("WOOD_HIGH_DENSITY",          "Wood High Density",          (155, 130,  95), 21000.0),
    CollisionMaterial("WOOD_LATTICE",               "Wood Lattice",               (155, 130,  95),  1400.0),
    CollisionMaterial("CERAMIC",                    "Ceramic",                    (220, 210, 195),  9695.0),
    CollisionMaterial("ROOF_TILE",                  "Roof Tile",                  (220, 210, 195),  7000.0),
    CollisionMaterial("ROOF_FELT",                  "Roof Felt",                  (165, 145, 110),  5250.0),
    CollisionMaterial("FIBREGLASS",                 "Fibreglass",                 (255, 250, 210),  1750.0),
    CollisionMaterial("TARPAULIN",                  "Tarpaulin",                  (255, 250, 210),  2800.0),
    CollisionMaterial("PLASTIC",                    "Plastic",                    (255, 250, 210),  3500.0),
    CollisionMaterial("PLASTIC_HOLLOW",             "Plastic Hollow",             (240, 230, 185),   875.0),
    CollisionMaterial("PLASTIC_HIGH_DENSITY",       "Plastic High Density",       (255, 250, 210), 21000.0),
    CollisionMaterial("PLASTIC_CLEAR",              "Plastic Clear",              (255, 250, 210),  3500.0),
    CollisionMaterial("PLASTIC_HOLLOW_CLEAR",       "Plastic Hollow Clear",       (240, 230, 185),   875.0),
    CollisionMaterial("PLASTIC_HIGH_DENSITY_CLEAR", "Plastic High Density Clear", (255, 250, 210), 21000.0),
    CollisionMaterial("FIBREGLASS_HOLLOW",          "Fibreglass Hollow",          (240, 230, 185),   126.0),
    CollisionMaterial("RUBBER",                     "Rubber",                     ( 70,  70,  70),  4200.0),
    CollisionMaterial("RUBBER_HOLLOW",              "Rubber Hollow",              ( 70,  70,  70),   875.0),
    CollisionMaterial("LINOLEUM",                   "Linoleum",                   (205, 150,  80),  1925.0),
    CollisionMaterial("LAMINATE",                   "Laminate",                   (170, 150, 125),  2800.0),
    CollisionMaterial("CARPET_SOLID",               "Carpet Solid",               (250, 100, 100),  1050.0),
    CollisionMaterial("CARPET_SOLID_DUSTY",         "Carpet Solid Dusty",         (255, 135, 135),  1050.0),
    CollisionMaterial("CARPET_FLOORBOARD",          "Carpet Floorboard",          (250, 100, 100),  1750.0),
    CollisionMaterial("CLOTH",                      "Cloth",                      (250, 100, 100),   875.0),
    CollisionMaterial("PLASTER_SOLID",              "Plaster Solid",              (145, 145, 145),  2971.5),
    CollisionMaterial("PLASTER_BRITTLE",            "Plaster Brittle",            (225, 225, 225),  2971.5),
    CollisionMaterial("CARDBOARD_SHEET",            "Cardboard Sheet",            (120, 115,  95),   400.0),
    CollisionMaterial("CARDBOARD_BOX",              "Cardboard Box",              (120, 115,  95),   200.0),
    CollisionMaterial("PAPER",                      "Paper",                      (230, 225, 220),  4203.5),
    CollisionMaterial("FOAM",                       "Foam",                       (230, 235, 240),   175.0),
    CollisionMaterial("FEATHER_PILLOW",             "Feather Pillow",             (230, 230, 230),   192.5),
    CollisionMaterial("POLYSTYRENE",                "Polystyrene",                (255, 250, 210),   157.5),
    CollisionMaterial("LEATHER",                    "Leather",                    (250, 100, 100),  3307.5),
    CollisionMaterial("TVSCREEN",                   "Tvscreen",                   (115, 125, 125),  9026.5),
    CollisionMaterial("SLATTED_BLINDS",             "Slatted Blinds",             (255, 250, 210),  8750.0),
    CollisionMaterial("GLASS_SHOOT_THROUGH",        "Glass Shoot Through",        (205, 240, 255),  8750.0),
    CollisionMaterial("GLASS_BULLETPROOF",          "Glass Bulletproof",          (115, 125, 125),  8750.0),
    CollisionMaterial("GLASS_OPAQUE",               "Glass Opaque",               (205, 240, 255),  8750.0),
    CollisionMaterial("PERSPEX",                    "Perspex",                    (205, 240, 255),  4130.0),
    CollisionMaterial("CAR_METAL",                  "Car Metal",                  (255, 255, 255),  3363.5),
    CollisionMaterial("CAR_PLASTIC",                "Car Plastic",                (255, 255, 255),  1750.0),
    CollisionMaterial("CAR_SOFTTOP",                "Car Softtop",                (250, 100, 100),  1750.0),
    CollisionMaterial("CAR_SOFTTOP_CLEAR",          "Car Softtop Clear",          (250, 100, 100),  1750.0),
    CollisionMaterial("CAR_GLASS_WEAK",             "Car Glass Weak",             (210, 245, 245),  8750.0),
    CollisionMaterial("CAR_GLASS_MEDIUM",           "Car Glass Medium",           (210, 245, 245),  8750.0),
    CollisionMaterial("CAR_GLASS_STRONG",           "Car Glass Strong",           (210, 245, 245),  8750.0),
    CollisionMaterial("CAR_GLASS_BULLETPROOF",      "Car Glass Bulletproof",      (210, 245, 245),  8750.0),
    CollisionMaterial("CAR_GLASS_OPAQUE",           "Car Glass Opaque",           (210, 245, 245),  8750.0),
    CollisionMaterial("WATER",                      "Water",                      ( 55, 145, 230),  3573.5),
    CollisionMaterial("BLOOD",                      "Blood",                      (205,   5,   5),  3573.5),
    CollisionMaterial("OIL",                        "Oil",                        ( 80,  65,  65),  3573.5),
    CollisionMaterial("PETROL",                     "Petrol",                     ( 70, 100, 120),  3573.5),
    CollisionMaterial("FRESH_MEAT",                 "Fresh Meat",                 (255,  55,  20),  4200.0),
    CollisionMaterial("DRIED_MEAT",                 "Dried Meat",                 (185, 100,  85),  4200.0),
    CollisionMaterial("EMISSIVE_GLASS",             "Emissive Glass",             (205, 240, 255),  8750.0),
    CollisionMaterial("EMISSIVE_PLASTIC",           "Emissive Plastic",           (255, 250, 210),  3500.0),
    CollisionMaterial("VFX_METAL_ELECTRIFIED",      "Vfx Metal Electrified",      (155, 180, 190),  2100.0),
    CollisionMaterial("VFX_METAL_WATER_TOWER",      "Vfx Metal Water Tower",      (155, 180, 190),  2100.0),
    CollisionMaterial("VFX_METAL_STEAM",            "Vfx Metal Steam",            (155, 180, 190),  2100.0),
    CollisionMaterial("VFX_METAL_FLAME",            "Vfx Metal Flame",            (155, 180, 190),  2100.0),
    CollisionMaterial("PHYS_NO_FRICTION",           "Phys No Friction",           (  0,   0,   0),  1750.0),
    CollisionMaterial("PHYS_GOLF_BALL",             "Phys Golf Ball",             (  0,   0,   0),   577.5),
    CollisionMaterial("PHYS_TENNIS_BALL",           "Phys Tennis Ball",           (  0,   0,   0),   350.0),
    CollisionMaterial("PHYS_CASTER",                "Phys Caster",                (  0,   0,   0),  1750.0),
    CollisionMaterial("PHYS_CASTER_RUSTY",          "Phys Caster Rusty",          (  0,   0,   0),  1750.0),
    CollisionMaterial("PHYS_CAR_VOID",              "Phys Car Void",              (  0,   0,   0),  1750.0),
    CollisionMaterial("PHYS_PED_CAPSULE",           "Phys Ped Capsule",           (  0,   0,   0),  1750.0),
    CollisionMaterial("PHYS_ELECTRIC_FENCE",        "Phys Electric Fence",        (  0,   0,   0),  1750.0),
    CollisionMaterial("PHYS_ELECTRIC_METAL",        "Phys Electric Metal",        (  0,   0,   0),  1750.0),
    CollisionMaterial("PHYS_BARBED_WIRE",           "Phys Barbed Wire",           (  0,   0,   0),  1750.0),
    CollisionMaterial("PHYS_POOLTABLE_SURFACE",     "Phys Pooltable Surface",     (155, 130,  95),  8750.0),
    CollisionMaterial("PHYS_POOLTABLE_CUSHION",     "Phys Pooltable Cushion",     (155, 130,  95),  8750.0),
    CollisionMaterial("PHYS_POOLTABLE_BALL",        "Phys Pooltable Ball",        (255, 250, 210),  8750.0),
    CollisionMaterial("BUTTOCKS",                   "Buttocks",                   (  0,   0,   0),   350.0),
    CollisionMaterial("THIGH_LEFT",                 "Thigh Left",                 (  0,   0,   0),   350.0),
    CollisionMaterial("SHIN_LEFT",                  "Shin Left",                  (  0,   0,   0),   350.0),
    CollisionMaterial("FOOT_LEFT",                  "Foot Left",                  (  0,   0,   0),   350.0),
    CollisionMaterial("THIGH_RIGHT",                "Thigh Right",                (  0,   0,   0),   350.0),
    CollisionMaterial("SHIN_RIGHT",                 "Shin Right",                 (  0,   0,   0),   350.0),
    CollisionMaterial("FOOT_RIGHT",                 "Foot Right",                 (  0,   0,   0),   350.0),
    CollisionMaterial("SPINE0",                     "Spine0",                     (  0,   0,   0),   350.0),
    CollisionMaterial("SPINE1",                     "Spine1",                     (  0,   0,   0),   350.0),
    CollisionMaterial("SPINE2",                     "Spine2",                     (  0,   0,   0),   350.0),
    CollisionMaterial("SPINE3",                     "Spine3",                     (  0,   0,   0),   350.0),
    CollisionMaterial("CLAVICLE_LEFT",              "Clavicle Left",              (  0,   0,   0),   350.0),
    CollisionMaterial("UPPER_ARM_LEFT",             "Upper Arm Left",             (  0,   0,   0),   350.0),
    CollisionMaterial("LOWER_ARM_LEFT",             "Lower Arm Left",             (  0,   0,   0),   350.0),
    CollisionMaterial("HAND_LEFT",                  "Hand Left",                  (  0,   0,   0),   350.0),
    CollisionMaterial("CLAVICLE_RIGHT",             "Clavicle Right",             (  0,   0,   0),   350.0),
    CollisionMaterial("UPPER_ARM_RIGHT",            "Upper Arm Right",            (  0,   0,   0),   350.0),
    CollisionMaterial("LOWER_ARM_RIGHT",            "Lower Arm Right",            (  0,   0,   0),   350.0),
    CollisionMaterial("HAND_RIGHT",                 "Hand Right",                 (  0,   0,   0),   350.0),
    CollisionMaterial("NECK",                       "Neck",                       (  0,   0,   0),   350.0),
    CollisionMaterial("HEAD",                       "Head",                       (  0,   0,   0),   350.0),
    CollisionMaterial("ANIMAL_DEFAULT",             "Animal Default",             (  0,   0,   0),   350.0),
    CollisionMaterial("CAR_ENGINE",                 "Car Engine",                 (255, 255, 255),  3363.5),
    CollisionMaterial("PUDDLE",                     "Puddle",                     ( 55, 145, 230),  3573.5),
    CollisionMaterial("CONCRETE_PAVEMENT",          "Concrete Pavement",          (145, 145, 145),  7850.5),
    CollisionMaterial("BRICK_PAVEMENT",             "Brick Pavement",             (195,  95,  30),  7000.0),
    CollisionMaterial("PHYS_DYNAMIC_COVER_BOUND",   "Phys Dynamic Cover Bound",   (  0,   0,   0),  1750.0),
    CollisionMaterial("VFX_WOOD_BEER_BARREL",       "Vfx Wood Beer Barrel",       (155, 130,  95),  1400.0),
    CollisionMaterial("WOOD_HIGH_FRICTION",         "Wood High Friction",         (155, 130,  95),  1400.0),
    CollisionMaterial("ROCK_NOINST",                "Rock Noinst",                (185, 185, 185),  7000.0),
    CollisionMaterial("BUSHES_NOINST",              "Bushes Noinst",              ( 85, 160,  30),   525.0),
    CollisionMaterial("METAL_SOLID_ROAD_SURFACE",   "Metal Solid Road Surface",   (155, 180, 190), 28000.0),
    CollisionMaterial("STUNT_RAMP_SURFACE",         "Stunt Ramp Surface",         (155, 180, 190), 28000.0),
    CollisionMaterial("TEMP_01",                    "Temp 01",                    (255,   0, 255),  5950.0),
    CollisionMaterial("TEMP_02",                    "Temp 02",                    (255,   0, 255),  5950.0),
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
