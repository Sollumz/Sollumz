import bpy
from ..sollumz_properties import items_from_enums, SOLLUMZ_UI_NAMES, SollumType
from bpy.app.handlers import persistent
from .collision_materials import collisionmats
from ..resources.flag_preset import FlagPresetsFile
from ..tools.meshhelper import create_disc, create_cylinder, create_sphere, create_capsule, create_box
from mathutils import Vector, Matrix
import os


class CollisionMatFlags(bpy.types.PropertyGroup):
    none: bpy.props.BoolProperty(name="NONE", default=False)
    stairs: bpy.props.BoolProperty(name="STAIRS", default=False)
    not_climbable: bpy.props.BoolProperty(name="NOT CLIMBABLE", default=False)
    see_through: bpy.props.BoolProperty(name="SEE THROUGH", default=False)
    shoot_through: bpy.props.BoolProperty(name="SHOOT THROUGH", default=False)
    not_cover: bpy.props.BoolProperty(name="NOT COVER", default=False)
    walkable_path: bpy.props.BoolProperty(name="WALKABLE PATH", default=False)
    no_cam_collision: bpy.props.BoolProperty(
        name="NO CAM COLLISION", default=False)
    shoot_through_fx: bpy.props.BoolProperty(
        name="SHOOT THROUGH FX", default=False)
    no_decal: bpy.props.BoolProperty(name="NO DECAL", default=False)
    no_navmesh: bpy.props.BoolProperty(name="NO NAVMESH", default=False)
    no_ragdoll: bpy.props.BoolProperty(name="NO RAGDOLL", default=False)
    vehicle_wheel: bpy.props.BoolProperty(name="VEHICLE WHEEL", default=False)
    no_ptfx: bpy.props.BoolProperty(name="NO PTFX", default=False)
    too_steep_for_player: bpy.props.BoolProperty(
        name="TOO STEEP FOR PLAYER", default=False)
    no_network_spawn: bpy.props.BoolProperty(
        name="NO NETWORK SPAWN", default=False)
    no_cam_collision_allow_clipping: bpy.props.BoolProperty(
        name="NO CAM COLLISION ALLOW CLIPPING", default=False)


class CollisionProperties(CollisionMatFlags, bpy.types.PropertyGroup):
    collision_index: bpy.props.IntProperty(name='Collision Index', default=0)
    procedural_id: bpy.props.IntProperty(name="Procedural ID", default=0)
    room_id: bpy.props.IntProperty(name="Room ID", default=0)
    ped_density: bpy.props.IntProperty(name="Ped Density", default=0)
    material_color_index: bpy.props.IntProperty(
        name="Material Color Index", default=0)


class BoundFlags(bpy.types.PropertyGroup):
    unknown: bpy.props.BoolProperty(name="UNKNOWN", default=False)
    map_weapon: bpy.props.BoolProperty(name="MAP WEAPON", default=False)
    map_dynamic: bpy.props.BoolProperty(name="MAP DYNAMIC", default=False)
    map_animal: bpy.props.BoolProperty(name="MAP ANIMAL", default=False)
    map_cover: bpy.props.BoolProperty(name="MAP COVER", default=False)
    map_vehicle: bpy.props.BoolProperty(name="MAP VEHICLE", default=False)
    vehicle_not_bvh: bpy.props.BoolProperty(
        name="VEHICLE NOT BVH", default=False)
    vehicle_bvh: bpy.props.BoolProperty(name="VEHICLE BVH", default=False)
    ped: bpy.props.BoolProperty(name="PED", default=False)
    ragdoll: bpy.props.BoolProperty(name="RAGDOLL", default=False)
    animal: bpy.props.BoolProperty(name="ANIMAL", default=False)
    animal_ragdoll: bpy.props.BoolProperty(
        name="ANIMAL RAGDOLL", default=False)
    object: bpy.props.BoolProperty(name="OBJECT", default=False)
    object_env_cloth: bpy.props.BoolProperty(
        name="OBJECT_ENV_CLOTH", default=False)
    plant: bpy.props.BoolProperty(name="PLANT", default=False)
    projectile: bpy.props.BoolProperty(name="PROJECTILE", default=False)
    explosion: bpy.props.BoolProperty(name="EXPLOSION", default=False)
    pickup: bpy.props.BoolProperty(name="PICKUP", default=False)
    foliage: bpy.props.BoolProperty(name="FOLIAGE", default=False)
    forklift_forks: bpy.props.BoolProperty(
        name="FORKLIFT FORKS", default=False)
    test_weapon: bpy.props.BoolProperty(name="TEST WEAPON", default=False)
    test_camera: bpy.props.BoolProperty(name="TEST CAMERA", default=False)
    test_ai: bpy.props.BoolProperty(name="TEST AI", default=False)
    test_script: bpy.props.BoolProperty(name="TEST SCRIPT", default=False)
    test_vehicle_wheel: bpy.props.BoolProperty(
        name="TEST VEHICLE WHEEL", default=False)
    glass: bpy.props.BoolProperty(name="GLASS", default=False)
    map_river: bpy.props.BoolProperty(name="MAP RIVER", default=False)
    smoke: bpy.props.BoolProperty(name="SMOKE", default=False)
    unsmashed: bpy.props.BoolProperty(name="UNSMASHED", default=False)
    map_stairs: bpy.props.BoolProperty(name="MAP STAIRS", default=False)
    map_deep_surface: bpy.props.BoolProperty(
        name="MAP DEEP SURFACE", default=False)


class BoundProperties(bpy.types.PropertyGroup):
    procedural_id: bpy.props.IntProperty(name="Procedural ID", default=0)
    room_id: bpy.props.IntProperty(name="Room ID", default=0)
    ped_density: bpy.props.IntProperty(name="Ped Density", default=0)
    poly_flags: bpy.props.IntProperty(name="Poly Flags", default=0)
    inertia: bpy.props.FloatVectorProperty(name="Inertia")
    volume: bpy.props.FloatProperty(name="Volume", precision=3)
    unk_flags: bpy.props.FloatProperty(name="UnkFlags")
    unk_float_1: bpy.props.FloatProperty(name="UnkFloat 1")
    unk_float_2: bpy.props.FloatProperty(name="UnkFloat 2")


class CollisionMaterial(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty('Index')
    name: bpy.props.StringProperty('Name')


class FlagPresetProp(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty('Index')
    name: bpy.props.StringProperty('Name')


def get_flag_presets_path():
    package_name = __name__.split('.')[0]
    presets_path = f"{bpy.utils.user_resource('SCRIPTS', path='addons')}\\{package_name}\\ybn\\flag_presets.xml"
    if os.path.exists(presets_path):
        return presets_path
    else:
        raise FileNotFoundError(
            f"flag_presets.xml file not found! Please redownload this file from the github and place it in '{os.path.dirname(presets_path)}'")


flag_presets = FlagPresetsFile()


def load_flag_presets():
    bpy.context.scene.flag_presets.clear()
    path = get_flag_presets_path()
    if os.path.exists(path):
        file = FlagPresetsFile.from_xml_file(path)
        flag_presets.presets = file.presets
        for index, preset in enumerate(flag_presets.presets):
            item = bpy.context.scene.flag_presets.add()
            item.name = str(preset.name)
            item.index = index


def load_collision_materials():
    bpy.context.scene.collision_materials.clear()
    for index, mat in enumerate(collisionmats):
        item = bpy.context.scene.collision_materials.add()
        item.index = index
        item.name = mat.name


# Handler sets the default value of the CollisionMaterials collection on blend file load
@persistent
def on_file_loaded(_):
    load_collision_materials()
    load_flag_presets()


def update_bounds(self, context):
    if self.sollum_type == SollumType.BOUND_BOX:
        create_box(self.data, 1, Matrix.Diagonal(
            Vector(self.bound_dimensions)))
    elif self.sollum_type == SollumType.BOUND_SPHERE or self.sollum_type == SollumType.BOUND_POLY_SPHERE:
        create_sphere(mesh=self.data, radius=self.bound_radius)

    elif self.sollum_type == SollumType.BOUND_CYLINDER:
        create_cylinder(mesh=self.data, radius=self.bound_radius,
                        length=self.bound_length)
    elif self.sollum_type == SollumType.BOUND_POLY_CYLINDER:
        create_cylinder(mesh=self.data, radius=self.bound_radius,
                        length=self.bound_length, rot_mat=Matrix())

    elif self.sollum_type == SollumType.BOUND_DISC:
        create_disc(mesh=self.data, radius=self.bound_radius,
                    length=self.margin * 2)

    elif self.sollum_type == SollumType.BOUND_CAPSULE:
        create_capsule(mesh=self.data, diameter=self.margin,
                       length=self.bound_radius, use_rot=True)
    elif self.sollum_type == SollumType.BOUND_POLY_CAPSULE:
        create_capsule(mesh=self.data, diameter=self.bound_radius / 2,
                       length=self.bound_length)


def register():
    bpy.types.Object.bound_properties = bpy.props.PointerProperty(
        type=BoundProperties)
    bpy.types.Object.margin = bpy.props.FloatProperty(
        name="Margin", precision=3, update=update_bounds, min=0)
    bpy.types.Object.bound_radius = bpy.props.FloatProperty(
        name="Radius", precision=3, update=update_bounds, min=0)
    bpy.types.Object.bound_length = bpy.props.FloatProperty(
        name="Length", precision=3, update=update_bounds, min=0)
    bpy.types.Object.bound_dimensions = bpy.props.FloatVectorProperty(
        name="Extents", precision=3, min=0, update=update_bounds, subtype='XYZ')

    #nest these in object.bound_properties ? is it possible#
    bpy.types.Object.composite_flags1 = bpy.props.PointerProperty(
        type=BoundFlags)
    bpy.types.Object.composite_flags2 = bpy.props.PointerProperty(
        type=BoundFlags)

    # TO KEEP TRACK OF THE INDEX IT WAS AT IN THE FILE, SLOPPY BUT EASIER THAN COMPARING VALUES WHEN IMPORTING FRAGMENTS
    bpy.types.Object.creation_index = bpy.props.IntProperty(default=0)

    bpy.types.Scene.collision_material_index = bpy.props.IntProperty(
        name="Material Index")
    bpy.types.Scene.collision_materials = bpy.props.CollectionProperty(
        type=CollisionMaterial, name='Collision Materials')
    bpy.app.handlers.load_post.append(on_file_loaded)

    bpy.types.Scene.new_flag_preset_name = bpy.props.StringProperty(
        name='Flag Preset Name')
    bpy.types.Scene.flag_preset_index = bpy.props.IntProperty(
        name="Flag Preset Index")
    bpy.types.Scene.flag_presets = bpy.props.CollectionProperty(
        type=FlagPresetProp, name='Flag Presets')

    bpy.types.Material.collision_properties = bpy.props.PointerProperty(
        type=CollisionProperties)
    bpy.types.Material.collision_flags = bpy.props.PointerProperty(
        type=CollisionMatFlags)

    # COLLISION TOOLS UI PROPERTIES
    bpy.types.Scene.create_poly_bound_type = bpy.props.EnumProperty(
        items=[
            (SollumType.BOUND_POLY_BOX.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_BOX], "Create a bound poly box object."),
            (SollumType.BOUND_POLY_SPHERE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_SPHERE], "Create a bound poly sphere object."),
            (SollumType.BOUND_POLY_CAPSULE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_CAPSULE], "Create a bound poly capsule object."),
            (SollumType.BOUND_POLY_CYLINDER.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_CYLINDER], "Create a bound poly cylinder object."),
            (SollumType.BOUND_POLY_TRIANGLE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_TRIANGLE], "Create a bound poly triangle object. (if you have a object selected then it will be converted to a bound poly triangle object")
        ],
        name="Type",
        default=SollumType.BOUND_POLY_TRIANGLE.value
    )

    bpy.types.Scene.create_bound_type = bpy.props.EnumProperty(
        items=[
            (SollumType.BOUND_COMPOSITE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE], "Create a bound composite object. (if objects are selected a drawable will be created with them as the children)"),
            (SollumType.BOUND_GEOMETRY.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY], "Create a bound geometry object."),
            (SollumType.BOUND_GEOMETRYBVH.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRYBVH], "Create a bound geometrybvh object."),
            (SollumType.BOUND_BOX.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_BOX], "Create a bound box object."),
            (SollumType.BOUND_CAPSULE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_CAPSULE], "Create a bound capsule object."),
            (SollumType.BOUND_CYLINDER.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_CYLINDER], "Create a bound cylinder object."),
            (SollumType.BOUND_DISC.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_DISC], "Create a bound disc object."),
            (SollumType.BOUND_CLOTH.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_CLOTH], "Create a bound cloth object."),
        ],
        name="Type",
        default=SollumType.BOUND_COMPOSITE.value
    )

    bpy.types.Scene.poly_bound_type_verts = bpy.props.EnumProperty(
        items=[(SollumType.BOUND_POLY_BOX.value, SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_BOX], SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_BOX]),
               (SollumType.BOUND_POLY_TRIANGLE.value, SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_TRIANGLE], SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_TRIANGLE])],
        name="Type",
        default=SollumType.BOUND_POLY_TRIANGLE.value
    )

    bpy.types.Scene.poly_edge = bpy.props.EnumProperty(name="Edge", items=[("long", "Long Edge", "Create along the long edge"),
                                                                           ("short", "Short Edge", "Create along the short edge")])
    bpy.types.Scene.poly_parent = bpy.props.PointerProperty(
        type=bpy.types.Object, name='Parent', description=f"Bounds will be parented to this object. Parent must be a {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRYBVH]} or {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY]}.")

    bpy.types.Scene.composite_create_bvh = bpy.props.BoolProperty(
        name='BVH', description='If true, the operator will create GeometryBVH objects, otherwise it will create Geometry objects.', default=True)

    bpy.types.Scene.composite_replace_original = bpy.props.BoolProperty(
        name='Replace Original', description=f'If true, the operator will replace the selected objects with the {SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]}.', default=True)

    bpy.types.Scene.split_collision_count = bpy.props.IntProperty(
        name="Divide By", description=f"Amount to split {SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRYBVH]}s or {SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]}s by", default=2, min=2)


def unregister():
    del bpy.types.Object.bound_properties
    del bpy.types.Object.margin
    del bpy.types.Object.bound_radius
    del bpy.types.Object.bound_length
    del bpy.types.Object.bound_dimensions
    del bpy.types.Object.composite_flags1
    del bpy.types.Object.composite_flags2
    del bpy.types.Object.creation_index
    del bpy.types.Scene.collision_material_index
    del bpy.types.Scene.collision_materials
    del bpy.types.Material.collision_properties
    del bpy.types.Material.collision_flags
    del bpy.types.Scene.new_flag_preset_name
    del bpy.types.Scene.flag_presets
    del bpy.types.Scene.flag_preset_index
    del bpy.types.Scene.create_poly_bound_type
    del bpy.types.Scene.create_bound_type
    del bpy.types.Scene.poly_parent
    del bpy.types.Scene.composite_create_bvh
    del bpy.types.Scene.composite_replace_original
    del bpy.types.Scene.split_collision_count

    bpy.app.handlers.load_post.remove(on_file_loaded)
