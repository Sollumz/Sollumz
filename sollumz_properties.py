import bpy
from Sollumz.resources.bound import BoundType, PolygonType

class DrawableProperties(bpy.types.PropertyGroup):
    lod_dist_high : bpy.props.FloatProperty(min = 0, max = 10000, default = 9998, name = "Lod Distance High")
    lod_dist_med : bpy.props.FloatProperty(min = 0, max = 10000, default = 9998, name = "Lod Distance Med")
    lod_dist_low : bpy.props.FloatProperty(min = 0, max = 10000, default = 9998, name = "Lod Distance Low")
    lod_dist_vlow : bpy.props.FloatProperty(min = 0, max = 10000, default = 9998, name = "Lod Distance Vlow")

class GeometryProperties(bpy.types.PropertyGroup):
    sollum_lod : bpy.props.EnumProperty(
        items = [("sollumz_high", "High", "High Lod"),
                ("sollumz_med", "Med", "Med Lod"),
                ("sollumz_low", "Low", "Low Lod"),
                ("sollumz_vlow", "Vlow", "Vlow Lod"),
                ],
        name = "LOD",
        default = "sollumz_high"
    )

class TextureProperties(bpy.types.PropertyGroup):
    embedded : bpy.props.BoolProperty(name = "Embedded", default = False)
    ########################## CHECK CW TO SEE IF THIS IS TRUE ##########################
    usage : bpy.props.EnumProperty(
        items = [("sollumz_unknown", "UNKNOWN", "Sollumz Unknown"),
                ("sollumz_tintpallete", "TINTPALLETE", "Sollumz Tint Pallete"),
                ("sollumz_default", "DEFAULT", "Sollumz Default"),
                ("sollumz_terrain", "TERRAIN", "Sollumz Terrain"),
                ("sollumz_clouddensity", "CLOUDDENSITY", "Sollumz Cloud Density"),
                ("sollumz_cloudnormal", "CLOUDNORMAL", "Sollumz Cloud Nomral"),
                ("sollumz_cable", "CABLE", "Sollumz Cable"),
                ("sollumz_fence", "FENCE", "Sollumz Fence"),
                ("sollumz_env.effect", "ENV.EFFECT", "Sollumz Env.Effect"),
                ("sollumz_script", "SCRIPT", "Sollumz Script"),
                ("sollumz_waterflow", "WATERFLOW", "Sollumz Water Flow"),
                ("sollumz_waterfoam", "WATERFOAM", "Sollumz Water Foam"),
                ("sollumz_waterfog", "WATERFOG", "Sollumz Water Fog"),
                ("sollumz_waterocean", "WATEROCEAN", "Sollumz Water Ocean"),
                ("sollumz_water", "WATER", "Sollumz Water"),
                ("sollumz_foamopacity", "FOAMOPACITY", "Sollumz Foam Opacity"),
                ("sollumz_foam", "FOAM", "Sollumz Foam"),
                ("sollumz_diffusedetail", "DIFFUSEDETAIL", "Sollumz Diffuse Detail"),
                ("sollumz_diffusedark", "DIFFUSEDARK", "Sollumz Diffuse Dark"),
                ("sollumz_diffuseaplhaopaque", "DIFFUSEALPHAOPAQUE", "Sollumz Diffuse Alpha Opaque"),
                ("sollumz_detail", "DETAIL", "Sollumz Detail"),
                ("sollumz_normal", "NORMAL", "Sollumz Normal"),
                ("sollumz_specular", "SPECULAR", "Sollumz Specular"),
                ("sollumz_emmisive", "EMMISIVE", "Sollumz Emmisive"),
                ("sollumz_skipproccesing", "SKIPPROCCESING", "Sollumz Skip Proccesing"),
                ("sollumz_dontoptimize", "DONTOPTIMIZE", "Sollumz Dont Optimize"),
                ("sollumz_test", "TEST", "Sollumz Test"),
                ("sollumz_count", "COUNT", "Sollumz Count"),
                ("sollumz_diffuse", "DIFFUSE", "Sollumz Diffuse")
                ],
        name = "Usage",
        default = "sollumz_diffuse"
    )

    #usage flags 
    not_half : bpy.props.BoolProperty(name = "NOT_HALF", default = False)
    hd_split : bpy.props.BoolProperty(name = "HD_SPLIT", default = False)
    x2 : bpy.props.BoolProperty(name = "X2", default = False)
    x4 : bpy.props.BoolProperty(name = "X4", default = False)
    y4 : bpy.props.BoolProperty(name = "Y4", default = False)
    x8 : bpy.props.BoolProperty(name = "X8", default = False)
    x16 : bpy.props.BoolProperty(name = "X16", default = False)
    x32 : bpy.props.BoolProperty(name = "X32", default = False)
    x64 : bpy.props.BoolProperty(name = "X64", default = False)
    y64 : bpy.props.BoolProperty(name = "Y64", default = False)
    x128 : bpy.props.BoolProperty(name = "X128", default = False)
    x256 : bpy.props.BoolProperty(name = "X256", default = False)
    x512 : bpy.props.BoolProperty(name = "X512", default = False)
    y512 : bpy.props.BoolProperty(name = "Y512", default = False)
    x1024 : bpy.props.BoolProperty(name = "X1024", default = False)
    y1024 : bpy.props.BoolProperty(name = "Y1024", default = False)
    x2048 : bpy.props.BoolProperty(name = "X2048", default = False)
    y2048 : bpy.props.BoolProperty(name = "Y2048", default = False)
    embeddedscriptrt : bpy.props.BoolProperty(name = "EMBEDDEDSCRIPTRT", default = False)
    unk19 : bpy.props.BoolProperty(name = "UNK19", default = False)
    unk20 : bpy.props.BoolProperty(name = "UNK20", default = False)
    unk21 : bpy.props.BoolProperty(name = "UNK21", default = False)
    flag_full : bpy.props.BoolProperty(name = "FLAG_FULL", default = False)
    maps_half : bpy.props.BoolProperty(name = "MAPS_HALF", default = False)
    unk24 : bpy.props.BoolProperty(name = "UNK24", default = False)

    ########################## CHECK CW TO SEE IF THIS IS TRUE ##########################
    format : bpy.props.EnumProperty(
        items = [("sollumz_dxt1", "D3DFMT_DXT1", "Sollumz DXT1"),
                ("sollumz_dxt3", "D3DFMT_DXT3", "Sollumz DXT3"),
                ("sollumz_dxt5", "D3DFMT_DXT5", "Sollumz DXT5"),
                ("sollumz_ati1", "D3DFMT_ATI1", "Sollumz ATI1"),
                ("sollumz_ati2", "D3DFMT_ATI2", "Sollumz ATI2"),
                ("sollumz_bc7", "D3DFMT_DXT1", "Sollumz BC7"),
                ("sollumz_a1r5g5b5", "D3DFMT_DXT1", "Sollumz A1R5G5B5"),
                ("sollumz_a1r8g8b8", "D3DFMT_DXT1", "Sollumz A1R8G8b8"),
                ("sollumz_a8r8g8b8", "D3DFMT_DXT1", "Sollumz A8R8G8B8"),
                ("sollumz_a8", "D3DFMT_DXT1", "Sollumz A8"),
                ("sollumz_l8", "D3DFMT_DXT1", "Sollumz L8")
                ],
        name = "Format",
        default = "sollumz_dxt1"
    )

    extra_flags : bpy.props.IntProperty(name = "Extra Flags", default = 0)

class ShaderProperties(bpy.types.PropertyGroup):
    renderbucket : bpy.props.IntProperty(name = "Render Bucket", default = 0)
    #????????? DONT KNOW IF I WANNA DO THIS
    #filename : bpy.props.EnumProperty(
    #    items = [("sollumz_none", "None", "Sollumz None")
    #            ],
    #    name = "FileName",
    #    default = "sollumz_none"
    #)
    #LAYOUT ENUM? 
    filename : bpy.props.StringProperty(name = "FileName", default = "default")

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

class CollisionProperties(bpy.types.PropertyGroup):
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

def assign_properties():
    
    bpy.types.Object.sollum_type = bpy.props.EnumProperty(
        items = [("sollumz_none", "None", "Sollumz None"),
                ("sollumz_drawable", "Drawable", "Sollumz Drawable"),
                ("sollumz_geometry", "Geometry", "Sollumz Geometry"),
                ("sollumz_skeleton", "Skeleton", "Sollumz Skeleton"),
                (BoundType.COMPOSITE.value, "Bound Composite", "Sollumz Bound Composite"),
                (BoundType.BOX.value, "Bound Box", "Sollumz Bound Box"),
                (BoundType.SPHERE.value, "Bound Sphere", "Sollumz Bound Sphere"),
                (BoundType.CAPSULE.value, "Bound Capsule", "Sollumz Bound Capsule"),
                (BoundType.CYLINDER.value, "Bound Cylinder", "Sollumz Bound Cylinder"),
                (BoundType.DISC.value, "Bound Disc", "Sollumz Bound Disc"),
                (BoundType.CLOTH.value, "Bound Cloth", "Sollumz Bound Cloth"),
                (BoundType.GEOMETRY.value, "Bound Geometry", "Sollumz Bound Geometry"),
                (BoundType.GEOMETRYBVH.value, "Bound GeometryBVH", "Sollumz Bound GeometryBVH"),
                (PolygonType.TRIANGLE.value, "Bound Poly Triangle", "Sollumz Bound Poly Triangle"),
                (PolygonType.SPHERE.value, "Bound Poly Sphere", "Sollumz Bound Poly Sphere"),
                (PolygonType.CAPSULE.value, "Bound Poly Capsule", "Sollumz Bound Poly Capsule"),
                (PolygonType.BOX.value, "Bound Poly Box", "Sollumz Bound Poly Box"),
                (PolygonType.CYLINDER.value, "Bound Poly Cylinder", "Sollumz Bound Poly Cylinder"),
                ],
        name = "Sollumz Type",
        default = "sollumz_none"
    )

    bpy.types.Scene.poly_bound_type = bpy.props.EnumProperty(
        items = [(PolygonType.TRIANGLE.value, "Bound Poly Triangle", "Sollumz Bound Poly Triangle"),
                (PolygonType.SPHERE.value, "Bound Poly Sphere", "Sollumz Bound Poly Sphere"),
                (PolygonType.CAPSULE.value, "Bound Poly Capsule", "Sollumz Bound Poly Capsule"),
                (PolygonType.BOX.value, "Bound Poly Box", "Sollumz Bound Poly Box"),
                (PolygonType.CYLINDER.value, "Bound Poly Cylinder", "Sollumz Bound Poly Cylinder"),
                ],
        name = "Poly Type",
        default = PolygonType.TRIANGLE.value
    )

    #COLLISION TOOLS UI PROPERTIES
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

    bpy.types.Material.sollum_type = bpy.props.EnumProperty(
        items = [("sollumz_none", "None", "Sollumz None"),
                ("sollumz_gta_material", "Gta Material", "Sollumz Gta Material"),
                ("sollumz_gta_collision_material", "Gta Collision Material", "Sollumz Gta Collision Material")
                ],
        name = "Sollumz Material Type",
        default = "sollumz_none"
    )

    bpy.types.Object.drawable_properties = bpy.props.PointerProperty(type = DrawableProperties)
    bpy.types.Object.geometry_properties = bpy.props.PointerProperty(type = GeometryProperties)
    bpy.types.Object.bound_properties = bpy.props.PointerProperty(type = BoundProperties)

    #nest these in object.bound_properties ? is it possible#
    bpy.types.Object.composite_flags1 = bpy.props.PointerProperty(type = BoundFlags)
    bpy.types.Object.composite_flags2 = bpy.props.PointerProperty(type = BoundFlags)
    ##

    bpy.types.Material.shader_properties = bpy.props.PointerProperty(type = ShaderProperties)
    bpy.types.Material.collision_properties = bpy.props.PointerProperty(type = CollisionProperties)
    bpy.types.Material.collision_flags = bpy.props.PointerProperty(type = CollisionFlags)
    bpy.types.ShaderNodeTexImage.texture_properties = bpy.props.PointerProperty(type = TextureProperties)