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

def unregister():
    del bpy.types.Scene.poly_bound_type
    del bpy.types.Object.bound_properties
    del bpy.types.Object.composite_flags1 
    del bpy.types.Object.composite_flags2 
    del bpy.types.Scene.collision_material_index
    del bpy.types.Scene.collision_materials
    del bpy.types.Material.collision_properties

    bpy.app.handlers.load_post.remove(on_file_loaded)