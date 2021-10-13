import bpy
from Sollumz.sollumz_properties import PolygonType, items_from_enums
from bpy.app.handlers import persistent
from .collision_materials import create_collision_material_from_index, collisionmats

class CollisionFlags(bpy.types.PropertyGroup):
    none : bpy.props.BoolProperty(name = "NONE", default = False)
    stairs : bpy.props.BoolProperty(name = "STAIRS", default = False)
    not_climbable : bpy.props.BoolProperty(name = "NOT CLIMBABLE", default = False)
    see_through : bpy.props.BoolProperty(name = "SEE THROUGH", default = False)
    shoot_through : bpy.props.BoolProperty(name = "SHOOT THROUGH", default = False)
    not_cover : bpy.props.BoolProperty(name = "NOT COVER", default = False)
    walkable_path : bpy.props.BoolProperty(name = "WALKABLE PATH", default = False)
    no_cam_collision : bpy.props.BoolProperty(name = "NO CAM COLLISION", default = False)
    shoot_through_fx : bpy.props.BoolProperty(name = "SHOOT THROUGH FX", default = False)
    no_decal : bpy.props.BoolProperty(name = "NO DECAL", default = False)
    no_navmesh : bpy.props.BoolProperty(name = "NO NAVMESH", default = False)
    no_ragdoll : bpy.props.BoolProperty(name = "NO RAGDOLL", default = False)
    vehicle_wheel : bpy.props.BoolProperty(name = "VEHICLE WHEEL", default = False)
    no_ptfx : bpy.props.BoolProperty(name = "NO PTFX", default = False)
    too_steep_for_player : bpy.props.BoolProperty(name = "TOO STEEP FOR PLAYER", default = False)
    no_network_spawn : bpy.props.BoolProperty(name = "NO NETWORK SPAWN", default = False)
    no_cam_collision_allow_clipping : bpy.props.BoolProperty(name = "NO CAM COLLISION ALLOW CLIPPING", default = False)


class CollisionProperties(CollisionFlags, bpy.types.PropertyGroup):
    collision_index : bpy.props.IntProperty(name = 'Collision Index', default = 0)
    procedural_id : bpy.props.IntProperty(name = "Procedural ID", default = 0)
    room_id : bpy.props.IntProperty(name = "Room ID", default = 0)
    ped_density : bpy.props.IntProperty(name = "Ped Density", default = 0)
    material_color_index : bpy.props.IntProperty(name = "Material Color Index", default = 0)


class BoundFlags(bpy.types.PropertyGroup):

    unknown : bpy.props.BoolProperty(name = "UNKNOWN", default = False)
    map_weapon : bpy.props.BoolProperty(name = "MAP WEAPON", default = False)
    map_dynamic : bpy.props.BoolProperty(name = "MAP DYNAMIC", default = False)
    map_animal : bpy.props.BoolProperty(name = "MAP ANIMAL", default = False)
    map_cover : bpy.props.BoolProperty(name = "MAP COVER", default = False)
    map_vehicle : bpy.props.BoolProperty(name = "MAP VEHICLE", default = False)
    vehicle_not_bvh : bpy.props.BoolProperty(name = "VEHICLE NOT BVH", default = False)
    vehicle_bvh : bpy.props.BoolProperty(name = "VEHICLE BVH", default = False)
    ped : bpy.props.BoolProperty(name = "PED", default = False)
    ragdoll : bpy.props.BoolProperty(name = "RAGDOLL", default = False)
    animal : bpy.props.BoolProperty(name = "ANIMAL", default = False)
    animal_ragdoll : bpy.props.BoolProperty(name = "ANIMAL RAGDOLL", default = False)
    object : bpy.props.BoolProperty(name = "OBJECT", default = False)
    object_env_cloth : bpy.props.BoolProperty(name = "OBJECT_ENV_CLOTH", default = False)
    plant : bpy.props.BoolProperty(name = "PLANT", default = False)
    projectile : bpy.props.BoolProperty(name = "PROJECTILE", default = False)
    explosion : bpy.props.BoolProperty(name = "EXPLOSION", default = False)
    pickup : bpy.props.BoolProperty(name = "PICKUP", default = False)
    foliage : bpy.props.BoolProperty(name = "FOLIAGE", default = False)
    forklift_forks : bpy.props.BoolProperty(name = "FORKLIFT FORKS", default = False)
    test_weapon : bpy.props.BoolProperty(name = "TEST WEAPON", default = False)
    test_camera : bpy.props.BoolProperty(name = "TEST CAMERA", default = False)
    test_ai : bpy.props.BoolProperty(name = "TEST AI", default = False)
    test_script : bpy.props.BoolProperty(name = "TEST SCRIPT", default = False)
    test_vehicle_wheel : bpy.props.BoolProperty(name = "TEST VEHICLE WHEEL", default = False)
    glass : bpy.props.BoolProperty(name = "GLASS", default = False)
    map_river : bpy.props.BoolProperty(name = "MAP RIVER", default = False)
    smoke : bpy.props.BoolProperty(name = "SMOKE", default = False)
    unsmashed : bpy.props.BoolProperty(name = "UNSMASHED", default = False)
    map_stairs : bpy.props.BoolProperty(name = "MAP STAIRS", default = False)
    map_deep_surface : bpy.props.BoolProperty(name = "MAP DEEP SURFACE", default = False)


class BoundProperties(bpy.types.PropertyGroup):
    procedural_id : bpy.props.IntProperty(name = "Procedural ID", default = 0)
    room_id : bpy.props.IntProperty(name = "Room ID", default = 0)
    ped_density : bpy.props.IntProperty(name = "Ped Density", default = 0)
    poly_flags : bpy.props.IntProperty(name = "Poly Flags", default = 0)


class CollisionMaterial(bpy.types.PropertyGroup):
    index : bpy.props.IntProperty('Index')
    name : bpy.props.StringProperty('Name')


# Handler sets the default value of the CollisionMaterials collection on blend file load
@persistent
def on_file_loaded(_):
    bpy.context.scene.collision_materials.clear()
    for index, mat in enumerate(collisionmats):
        item = bpy.context.scene.collision_materials.add()
        item.index = index
        item.name = mat.name


def register():
    bpy.types.Scene.poly_bound_type = bpy.props.EnumProperty(
        items = items_from_enums(PolygonType),
        name = "Poly Type",
        default = PolygonType.TRIANGLE.value
    )

    bpy.types.Object.bound_properties = bpy.props.PointerProperty(type = BoundProperties)

    #nest these in object.bound_properties ? is it possible#
    bpy.types.Object.composite_flags1 = bpy.props.PointerProperty(type = BoundFlags)
    bpy.types.Object.composite_flags2 = bpy.props.PointerProperty(type = BoundFlags)
    ##

    bpy.types.Scene.collision_material_index = bpy.props.IntProperty(name = "Material Index") #MAKE ENUM WITH THE MATERIALS NAMES
    bpy.types.Scene.collision_materials = bpy.props.CollectionProperty(type = CollisionMaterial, name = 'Collision Materials')
    bpy.app.handlers.load_post.append(on_file_loaded)

    bpy.types.Material.collision_properties = bpy.props.PointerProperty(type = CollisionProperties)
    bpy.types.Material.collision_flags = bpy.props.PointerProperty(type = CollisionFlags)


    #COLLISION TOOLS UI PROPERTIES
    bpy.types.Scene.poly_bound_type = bpy.props.EnumProperty(
        #maybe remove PolygonType.TRIANGLE from list?
        items = items_from_enums(PolygonType),
        name = "Poly Type",
        default = PolygonType.BOX.value    
    )
    bpy.types.Scene.create_collision_material_type = bpy.props.EnumProperty(
        items = [("sollumz_default", "Default ", "Sollumz Default "),
                 ("sollumz_concrete", "Concrete ", "Sollumz Concrete "),
                 ("sollumz_concrete_pothole", "Concrete Pothole ", "Sollumz Concrete Pothole "),
                 ("sollumz_concrete_dusty", "Concrete Dusty ", "Sollumz Concrete Dusty "),
                 ("sollumz_tarmac", "Tarmac ", "Sollumz Tarmac "),
                 ("sollumz_tarmac_painted", "Tarmac Painted ", "Sollumz Tarmac Painted "),
                 ("sollumz_tarmac_pothole", "Tarmac Pothole ", "Sollumz Tarmac Pothole "),
                 ("sollumz_rumble_strip", "Rumble Strip ", "Sollumz Rumble Strip "),
                 ("sollumz_breeze_block", "Breeze Block ", "Sollumz Breeze Block "),
                 ("sollumz_rock", "Rock ", "Sollumz Rock "),
                 ("sollumz_rock_mossy", "Rock Mossy ", "Sollumz Rock Mossy "),
                 ("sollumz_stone", "Stone ", "Sollumz Stone "),
                 ("sollumz_cobblestone", "Cobblestone ", "Sollumz Cobblestone "),
                 ("sollumz_brick", "Brick ", "Sollumz Brick "),
                 ("sollumz_marble", "Marble ", "Sollumz Marble "),
                 ("sollumz_paving_slab", "Paving Slab ", "Sollumz Paving Slab "),
                 ("sollumz_sandstone_solid", "Sandstone Solid ", "Sollumz Sandstone Solid "),
                 ("sollumz_sandstone_brittle", "Sandstone Brittle ", "Sollumz Sandstone Brittle "),
                 ("sollumz_sand_loose", "Sand Loose ", "Sollumz Sand Loose "),
                 ("sollumz_sand_compact", "Sand Compact ", "Sollumz Sand Compact "),
                 ("sollumz_sand_wet", "Sand Wet ", "Sollumz Sand Wet "),
                 ("sollumz_sand_track", "Sand Track ", "Sollumz Sand Track "),
                 ("sollumz_sand_underwater", "Sand Underwater ", "Sollumz Sand Underwater "),
                 ("sollumz_sand_dry_deep", "Sand Dry Deep ", "Sollumz Sand Dry Deep "),
                 ("sollumz_sand_wet_deep", "Sand Wet Deep ", "Sollumz Sand Wet Deep "),
                 ("sollumz_ice", "Ice ", "Sollumz Ice "),
                 ("sollumz_ice_tarmac", "Ice Tarmac ", "Sollumz Ice Tarmac "),
                 ("sollumz_snow_loose", "Snow Loose ", "Sollumz Snow Loose "),
                 ("sollumz_snow_compact", "Snow Compact ", "Sollumz Snow Compact "),
                 ("sollumz_snow_deep", "Snow Deep ", "Sollumz Snow Deep "),
                 ("sollumz_snow_tarmac", "Snow Tarmac ", "Sollumz Snow Tarmac "),
                 ("sollumz_gravel_small", "Gravel Small ", "Sollumz Gravel Small "),
                 ("sollumz_gravel_large", "Gravel Large ", "Sollumz Gravel Large "),
                 ("sollumz_gravel_deep", "Gravel Deep ", "Sollumz Gravel Deep "),
                 ("sollumz_gravel_train_track", "Gravel Train Track ", "Sollumz Gravel Train Track "),
                 ("sollumz_dirt_track", "Dirt Track ", "Sollumz Dirt Track "),
                 ("sollumz_mud_hard", "Mud Hard ", "Sollumz Mud Hard "),
                 ("sollumz_mud_pothole", "Mud Pothole ", "Sollumz Mud Pothole "),
                 ("sollumz_mud_soft", "Mud Soft ", "Sollumz Mud Soft "),
                 ("sollumz_mud_underwater", "Mud Underwater ", "Sollumz Mud Underwater "),
                 ("sollumz_mud_deep", "Mud Deep ", "Sollumz Mud Deep "),
                 ("sollumz_marsh", "Marsh ", "Sollumz Marsh "),
                 ("sollumz_marsh_deep", "Marsh Deep ", "Sollumz Marsh Deep "),
                 ("sollumz_soil", "Soil ", "Sollumz Soil "),
                 ("sollumz_clay_hard", "Clay Hard ", "Sollumz Clay Hard "),
                 ("sollumz_clay_soft", "Clay Soft ", "Sollumz Clay Soft "),
                 ("sollumz_grass_long", "Grass Long ", "Sollumz Grass Long "),
                 ("sollumz_grass", "Grass ", "Sollumz Grass "),
                 ("sollumz_grass_short", "Grass Short ", "Sollumz Grass Short "),
                 ("sollumz_hay", "Hay ", "Sollumz Hay "),
                 ("sollumz_bushes", "Bushes ", "Sollumz Bushes "),
                 ("sollumz_twigs", "Twigs ", "Sollumz Twigs "),
                 ("sollumz_leaves", "Leaves ", "Sollumz Leaves "),
                 ("sollumz_woodchips", "Woodchips ", "Sollumz Woodchips "),
                 ("sollumz_tree_bark", "Tree Bark ", "Sollumz Tree Bark "),
                 ("sollumz_metal_solid_small", "Metal Solid Small ", "Sollumz Metal Solid Small "),
                 ("sollumz_metal_solid_medium", "Metal Solid Medium ", "Sollumz Metal Solid Medium "),
                 ("sollumz_metal_solid_large", "Metal Solid Large ", "Sollumz Metal Solid Large "),
                 ("sollumz_metal_hollow_small", "Metal Hollow Small ", "Sollumz Metal Hollow Small "),
                 ("sollumz_metal_hollow_medium", "Metal Hollow Medium ", "Sollumz Metal Hollow Medium "),
                 ("sollumz_metal_hollow_large", "Metal Hollow Large ", "Sollumz Metal Hollow Large "),
                 ("sollumz_metal_chainlink_small", "Metal Chainlink Small ", "Sollumz Metal Chainlink Small "),
                 ("sollumz_metal_chainlink_large", "Metal Chainlink Large ", "Sollumz Metal Chainlink Large "),
                 ("sollumz_metal_corrugated_iron", "Metal Corrugated Iron ", "Sollumz Metal Corrugated Iron "),
                 ("sollumz_metal_grille", "Metal Grille ", "Sollumz Metal Grille "),
                 ("sollumz_metal_railing", "Metal Railing ", "Sollumz Metal Railing "),
                 ("sollumz_metal_duct", "Metal Duct ", "Sollumz Metal Duct "),
                 ("sollumz_metal_garage_door", "Metal Garage Door ", "Sollumz Metal Garage Door "),
                 ("sollumz_metal_manhole", "Metal Manhole ", "Sollumz Metal Manhole "),
                 ("sollumz_wood_solid_small", "Wood Solid Small ", "Sollumz Wood Solid Small "),
                 ("sollumz_wood_solid_medium", "Wood Solid Medium ", "Sollumz Wood Solid Medium "),
                 ("sollumz_wood_solid_large", "Wood Solid Large ", "Sollumz Wood Solid Large "),
                 ("sollumz_wood_solid_polished", "Wood Solid Polished ", "Sollumz Wood Solid Polished "),
                 ("sollumz_wood_floor_dusty", "Wood Floor Dusty ", "Sollumz Wood Floor Dusty "),
                 ("sollumz_wood_hollow_small", "Wood Hollow Small ", "Sollumz Wood Hollow Small "),
                 ("sollumz_wood_hollow_medium", "Wood Hollow Medium ", "Sollumz Wood Hollow Medium "),
                 ("sollumz_wood_hollow_large", "Wood Hollow Large ", "Sollumz Wood Hollow Large "),
                 ("sollumz_wood_chipboard", "Wood Chipboard ", "Sollumz Wood Chipboard "),
                 ("sollumz_wood_old_creaky", "Wood Old Creaky ", "Sollumz Wood Old Creaky "),
                 ("sollumz_wood_high_density", "Wood High Density ", "Sollumz Wood High Density "),
                 ("sollumz_wood_lattice", "Wood Lattice ", "Sollumz Wood Lattice "),
                 ("sollumz_ceramic", "Ceramic ", "Sollumz Ceramic "),
                 ("sollumz_roof_tile", "Roof Tile ", "Sollumz Roof Tile "),
                 ("sollumz_roof_felt", "Roof Felt ", "Sollumz Roof Felt "),
                 ("sollumz_fibreglass", "Fibreglass ", "Sollumz Fibreglass "),
                 ("sollumz_tarpaulin", "Tarpaulin ", "Sollumz Tarpaulin "),
                 ("sollumz_plastic", "Plastic ", "Sollumz Plastic "),
                 ("sollumz_plastic_hollow", "Plastic Hollow ", "Sollumz Plastic Hollow "),
                 ("sollumz_plastic_high_density", "Plastic High Density ", "Sollumz Plastic High Density "),
                 ("sollumz_plastic_clear", "Plastic Clear ", "Sollumz Plastic Clear "),
                 ("sollumz_plastic_hollow_clear", "Plastic Hollow Clear ", "Sollumz Plastic Hollow Clear "),
                 ("sollumz_plastic_high_density_clear", "Plastic High Density Clear ", "Sollumz Plastic High Density Clear "),
                 ("sollumz_fibreglass_hollow", "Fibreglass Hollow ", "Sollumz Fibreglass Hollow "),
                 ("sollumz_rubber", "Rubber ", "Sollumz Rubber "),
                 ("sollumz_rubber_hollow", "Rubber Hollow ", "Sollumz Rubber Hollow "),
                 ("sollumz_linoleum", "Linoleum ", "Sollumz Linoleum "),
                 ("sollumz_laminate", "Laminate ", "Sollumz Laminate "),
                 ("sollumz_carpet_solid", "Carpet Solid ", "Sollumz Carpet Solid "),
                 ("sollumz_carpet_solid_dusty", "Carpet Solid Dusty ", "Sollumz Carpet Solid Dusty "),
                 ("sollumz_carpet_floorboard", "Carpet Floorboard ", "Sollumz Carpet Floorboard "),
                 ("sollumz_cloth", "Cloth ", "Sollumz Cloth "),
                 ("sollumz_plaster_solid", "Plaster Solid ", "Sollumz Plaster Solid "),
                 ("sollumz_plaster_brittle", "Plaster Brittle ", "Sollumz Plaster Brittle "),
                 ("sollumz_cardboard_sheet", "Cardboard Sheet ", "Sollumz Cardboard Sheet "),
                 ("sollumz_cardboard_box", "Cardboard Box ", "Sollumz Cardboard Box "),
                 ("sollumz_paper", "Paper ", "Sollumz Paper "),
                 ("sollumz_foam", "Foam ", "Sollumz Foam "),
                 ("sollumz_feather_pillow", "Feather Pillow ", "Sollumz Feather Pillow "),
                 ("sollumz_polystyrene", "Polystyrene ", "Sollumz Polystyrene "),
                 ("sollumz_leather", "Leather ", "Sollumz Leather "),
                 ("sollumz_tvscreen", "Tvscreen ", "Sollumz Tvscreen "),
                 ("sollumz_slatted_blinds", "Slatted Blinds ", "Sollumz Slatted Blinds "),
                 ("sollumz_glass_shoot_through", "Glass Shoot Through ", "Sollumz Glass Shoot Through "),
                 ("sollumz_glass_bulletproof", "Glass Bulletproof ", "Sollumz Glass Bulletproof "),
                 ("sollumz_glass_opaque", "Glass Opaque ", "Sollumz Glass Opaque "),
                 ("sollumz_perspex", "Perspex ", "Sollumz Perspex "),
                 ("sollumz_car_metal", "Car Metal ", "Sollumz Car Metal "),
                 ("sollumz_car_plastic", "Car Plastic ", "Sollumz Car Plastic "),
                 ("sollumz_car_softtop", "Car Softtop ", "Sollumz Car Softtop "),
                 ("sollumz_car_softtop_clear", "Car Softtop Clear ", "Sollumz Car Softtop Clear "),
                 ("sollumz_car_glass_weak", "Car Glass Weak ", "Sollumz Car Glass Weak "),
                 ("sollumz_car_glass_medium", "Car Glass Medium ", "Sollumz Car Glass Medium "),
                 ("sollumz_car_glass_strong", "Car Glass Strong ", "Sollumz Car Glass Strong "),
                 ("sollumz_car_glass_bulletproof", "Car Glass Bulletproof ", "Sollumz Car Glass Bulletproof "),
                 ("sollumz_car_glass_opaque", "Car Glass Opaque ", "Sollumz Car Glass Opaque "),
                 ("sollumz_water", "Water ", "Sollumz Water "),
                 ("sollumz_blood", "Blood ", "Sollumz Blood "),
                 ("sollumz_oil", "Oil ", "Sollumz Oil "),
                 ("sollumz_petrol", "Petrol ", "Sollumz Petrol "),
                 ("sollumz_fresh_meat", "Fresh Meat ", "Sollumz Fresh Meat "),
                 ("sollumz_dried_meat", "Dried Meat ", "Sollumz Dried Meat "),
                 ("sollumz_emissive_glass", "Emissive Glass ", "Sollumz Emissive Glass "),
                 ("sollumz_emissive_plastic", "Emissive Plastic ", "Sollumz Emissive Plastic "),
                 ("sollumz_vfx_metal_electrified", "Vfx Metal Electrified ", "Sollumz Vfx Metal Electrified "),
                 ("sollumz_vfx_metal_water_tower", "Vfx Metal Water Tower ", "Sollumz Vfx Metal Water Tower "),
                 ("sollumz_vfx_metal_steam", "Vfx Metal Steam ", "Sollumz Vfx Metal Steam "),
                 ("sollumz_vfx_metal_flame", "Vfx Metal Flame ", "Sollumz Vfx Metal Flame "),
                 ("sollumz_phys_no_friction", "Phys No Friction ", "Sollumz Phys No Friction "),
                 ("sollumz_phys_golf_ball", "Phys Golf Ball ", "Sollumz Phys Golf Ball "),
                 ("sollumz_phys_tennis_ball", "Phys Tennis Ball ", "Sollumz Phys Tennis Ball "),
                 ("sollumz_phys_caster", "Phys Caster ", "Sollumz Phys Caster "),
                 ("sollumz_phys_caster_rusty", "Phys Caster Rusty ", "Sollumz Phys Caster Rusty "),
                 ("sollumz_phys_car_void", "Phys Car Void ", "Sollumz Phys Car Void "),
                 ("sollumz_phys_ped_capsule", "Phys Ped Capsule ", "Sollumz Phys Ped Capsule "),
                 ("sollumz_phys_electric_fence", "Phys Electric Fence ", "Sollumz Phys Electric Fence "),
                 ("sollumz_phys_electric_metal", "Phys Electric Metal ", "Sollumz Phys Electric Metal "),
                 ("sollumz_phys_barbed_wire", "Phys Barbed Wire ", "Sollumz Phys Barbed Wire "),
                 ("sollumz_phys_pooltable_surface", "Phys Pooltable Surface ", "Sollumz Phys Pooltable Surface "),
                 ("sollumz_phys_pooltable_cushion", "Phys Pooltable Cushion ", "Sollumz Phys Pooltable Cushion "),
                 ("sollumz_phys_pooltable_ball", "Phys Pooltable Ball ", "Sollumz Phys Pooltable Ball "),
                 ("sollumz_buttocks", "Buttocks ", "Sollumz Buttocks "),
                 ("sollumz_thigh_left", "Thigh Left ", "Sollumz Thigh Left "),
                 ("sollumz_shin_left", "Shin Left ", "Sollumz Shin Left "),
                 ("sollumz_foot_left", "Foot Left ", "Sollumz Foot Left "),
                 ("sollumz_thigh_right", "Thigh Right ", "Sollumz Thigh Right "),
                 ("sollumz_shin_right", "Shin Right ", "Sollumz Shin Right "),
                 ("sollumz_foot_right", "Foot Right ", "Sollumz Foot Right "),
                 ("sollumz_spine0", "Spine0 ", "Sollumz Spine0 "),
                 ("sollumz_spine1", "Spine1 ", "Sollumz Spine1 "),
                 ("sollumz_spine2", "Spine2 ", "Sollumz Spine2 "),
                 ("sollumz_spine3", "Spine3 ", "Sollumz Spine3 "),
                 ("sollumz_clavicle_left", "Clavicle Left ", "Sollumz Clavicle Left "),
                 ("sollumz_upper_arm_left", "Upper Arm Left ", "Sollumz Upper Arm Left "),
                 ("sollumz_lower_arm_left", "Lower Arm Left ", "Sollumz Lower Arm Left "),
                 ("sollumz_hand_left", "Hand Left ", "Sollumz Hand Left "),
                 ("sollumz_clavicle_right", "Clavicle Right ", "Sollumz Clavicle Right "),
                 ("sollumz_upper_arm_right", "Upper Arm Right ", "Sollumz Upper Arm Right "),
                 ("sollumz_lower_arm_right", "Lower Arm Right ", "Sollumz Lower Arm Right "),
                 ("sollumz_hand_right", "Hand Right ", "Sollumz Hand Right "),
                 ("sollumz_neck", "Neck ", "Sollumz Neck "),
                 ("sollumz_head", "Head ", "Sollumz Head "),
                 ("sollumz_animal_default", "Animal Default ", "Sollumz Animal Default "),
                 ("sollumz_car_engine", "Car Engine ", "Sollumz Car Engine "),
                 ("sollumz_puddle", "Puddle ", "Sollumz Puddle "),
                 ("sollumz_concrete_pavement", "Concrete Pavement ", "Sollumz Concrete Pavement "),
                 ("sollumz_brick_pavement", "Brick Pavement ", "Sollumz Brick Pavement "),
                 ("sollumz_phys_dynamic_cover_bound", "Phys Dynamic Cover Bound ", "Sollumz Phys Dynamic Cover Bound "),
                 ("sollumz_vfx_wood_beer_barrel", "Vfx Wood Beer Barrel ", "Sollumz Vfx Wood Beer Barrel "),
                 ("sollumz_wood_high_friction", "Wood High Friction ", "Sollumz Wood High Friction "),
                 ("sollumz_rock_noinst", "Rock Noinst ", "Sollumz Rock Noinst "),
                 ("sollumz_bushes_noinst", "Bushes Noinst ", "Sollumz Bushes Noinst "),
                 ("sollumz_metal_solid_road_surface", "Metal Solid Road Surface ", "Sollumz Metal Solid Road Surface ")
                ],
        name = "Material Type",
        default = "sollumz_default"
    )

def unregister():
    del bpy.types.Scene.poly_bound_type
    del bpy.types.Object.bound_properties
    del bpy.types.Object.composite_flags1 
    del bpy.types.Object.composite_flags2 
    del bpy.types.Scene.collision_material_index
    del bpy.types.Scene.collision_materials
    del bpy.types.Material.collision_properties

    bpy.app.handlers.load_post.remove(on_file_loaded)