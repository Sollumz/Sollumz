import bpy 

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
    procedural_id : bpy.props.IntProperty(name = "Procedural ID", default = 0)
    room_id : bpy.props.IntProperty(name = "Room ID", default = 0)
    ped_density : bpy.props.IntProperty(name = "Ped Density", default = 0)
    flags : bpy.props.EnumProperty( ############### NOT DONE ############### 
        items = [("sollumz_none", "None", "Sollumz None")
                ],
        name = "Flags",
        default = "sollumz_none"
    )

class BoundProperties(bpy.types.PropertyGroup):
    procedural_id : bpy.props.IntProperty(name = "Procedural ID", default = 0)
    room_id : bpy.props.IntProperty(name = "Room ID", default = 0)
    ped_density : bpy.props.IntProperty(name = "Ped Density", default = 0)
    poly_flags : bpy.props.EnumProperty( ############### NOT DONE ############### 
        items = [("sollumz_none", "None", "Sollumz None")
                ],
        name = "Poly Flags",
        default = "sollumz_none"
    )
    ## UNK_FLAGS ? ##
    composite_flags1 : bpy.props.EnumProperty( ############### NOT DONE ############### 
        items = [("sollumz_none", "None", "Sollumz None")
                ],
        name = "Composite Flags 1",
        default = "sollumz_none"
    )

    composite_flags2 : bpy.props.EnumProperty( ############### NOT DONE ############### 
        items = [
            ("sollumz_none", "None", "Sollumz None")
        ],
        name = "Composite Flags 2",
        default = "sollumz_none"
    )

def assign_properties():
    
    bpy.types.Object.sollum_type = bpy.props.EnumProperty(
        items = [("sollumz_none", "None", "Sollumz None"),
                ("sollumz_drawable", "Drawable", "Sollumz Drawable"),
                ("sollumz_geometry", "Geometry", "Sollumz Geometry"),
                ("sollumz_skeleton", "Skeleton", "Sollumz Skeleton"),
                ("sollumz_bound_composite", "Bound Composite", "Sollumz Bound Composite"),
                ("sollumz_bound_box", "Bound Box", "Sollumz Bound Box"),
                ("sollumz_bound_sphere", "Bound Sphere", "Sollumz Bound Sphere"),
                ("sollumz_bound_capsule", "Bound Capsule", "Sollumz Bound Capsule"),
                ("sollumz_bound_cylinder", "Bound Cylinder", "Sollumz Bound Cylinder"),
                ("sollumz_bound_disc", "Bound Disc", "Sollumz Bound Disc"),
                ("sollumz_bound_cloth", "Bound Cloth", "Sollumz Bound Cloth"),
                ("sollumz_bound_geometry", "Bound Geometry", "Sollumz Bound Geometry"),
                ("sollumz_bound_geometrybvh", "Bound GeometryBVH", "Sollumz Bound GeometryBVH"),
                ("sollumz_bound_poly_triangle", "Bound Poly Triangle", "Sollumz Bound Poly Triangle"),
                ("sollumz_bound_poly_sphere", "Bound Poly Sphere", "Sollumz Bound Poly Sphere"),
                ("sollumz_bound_poly_capsule", "Bound Poly Capsule", "Sollumz Bound Poly Capsule"),
                ("sollumz_bound_poly_box", "Bound Poly Box", "Sollumz Bound Poly Box"),
                ("sollumz_bound_poly_cylinder", "Bound Poly Cylinder", "Sollumz Bound Poly Cylinder"),
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
    bpy.types.Material.shader_properties = bpy.props.PointerProperty(type = ShaderProperties)
    bpy.types.Material.collision_properties = bpy.props.PointerProperty(type = CollisionProperties)
    bpy.types.ShaderNodeTexImage.texture_properties = bpy.props.PointerProperty(type = TextureProperties)