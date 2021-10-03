import bpy
from Sollumz.game_objects.bound import BoundType
from Sollumz.game_objects.polygon import PolygonType

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

class CollisionProperties(bpy.types.PropertyGroup):
    collision_index : bpy.props.IntProperty(name = 'Collision Index', default = 0)
    procedural_id : bpy.props.IntProperty(name = "Procedural ID", default = 0)
    room_id : bpy.props.IntProperty(name = "Room ID", default = 0)
    ped_density : bpy.props.IntProperty(name = "Ped Density", default = 0)
    material_color_index : bpy.props.IntProperty(name = "Material Color Index", default = 0)
    
    #flags
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
    bpy.types.ShaderNodeTexImage.texture_properties = bpy.props.PointerProperty(type = TextureProperties)