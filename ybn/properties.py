import bpy
from bpy.props import (
    BoolProperty
)
from ..sollumz_properties import SOLLUMZ_UI_NAMES, SollumType
from bpy.app.handlers import persistent
from .collision_materials import collisionmats
from ..cwxml.flag_preset import FlagPresetsFile
from ..tools.meshhelper import create_disc, create_cylinder, create_sphere, create_capsule, create_box
from ..tools.blenderhelper import tag_redraw
from mathutils import Vector, Matrix
import os


class CollisionMatFlags(bpy.types.PropertyGroup):
    stairs: bpy.props.BoolProperty(name="STAIRS", default=False)
    not_climbable: bpy.props.BoolProperty(name="NOT CLIMBABLE", default=False)
    see_through: bpy.props.BoolProperty(name="SEE THROUGH", default=False)
    shoot_through: bpy.props.BoolProperty(name="SHOOT THROUGH", default=False)
    not_cover: bpy.props.BoolProperty(name="NOT COVER", default=False)
    walkable_path: bpy.props.BoolProperty(name="WALKABLE PATH", default=False)
    no_cam_collision: bpy.props.BoolProperty(name="NO CAM COLLISION", default=False)
    shoot_through_fx: bpy.props.BoolProperty(name="SHOOT THROUGH FX", default=False)
    no_decal: bpy.props.BoolProperty(name="NO DECAL", default=False)
    no_navmesh: bpy.props.BoolProperty(name="NO NAVMESH", default=False)
    no_ragdoll: bpy.props.BoolProperty(name="NO RAGDOLL", default=False)
    vehicle_wheel: bpy.props.BoolProperty(name="VEHICLE WHEEL", default=False)
    no_ptfx: bpy.props.BoolProperty(name="NO PTFX", default=False)
    too_steep_for_player: bpy.props.BoolProperty(name="TOO STEEP FOR PLAYER", default=False)
    no_network_spawn: bpy.props.BoolProperty(name="NO NETWORK SPAWN", default=False)
    no_cam_collision_allow_clipping: bpy.props.BoolProperty(name="NO CAM COLLISION ALLOW CLIPPING", default=False)


def set_collision_mat_raw_flags(f: CollisionMatFlags, flags_lo: int, flags_hi: int):
    # fmt: off
    f.stairs           = (flags_lo & (1 << 0)) != 0
    f.not_climbable    = (flags_lo & (1 << 1)) != 0
    f.see_through      = (flags_lo & (1 << 2)) != 0
    f.shoot_through    = (flags_lo & (1 << 3)) != 0
    f.not_cover        = (flags_lo & (1 << 4)) != 0
    f.walkable_path    = (flags_lo & (1 << 5)) != 0
    f.no_cam_collision = (flags_lo & (1 << 6)) != 0
    f.shoot_through_fx = (flags_lo & (1 << 7)) != 0

    f.no_decal                        = (flags_hi & (1 << 0)) != 0
    f.no_navmesh                      = (flags_hi & (1 << 1)) != 0
    f.no_ragdoll                      = (flags_hi & (1 << 2)) != 0
    f.vehicle_wheel                   = (flags_hi & (1 << 3)) != 0
    f.no_ptfx                         = (flags_hi & (1 << 4)) != 0
    f.too_steep_for_player            = (flags_hi & (1 << 5)) != 0
    f.no_network_spawn                = (flags_hi & (1 << 6)) != 0
    f.no_cam_collision_allow_clipping = (flags_hi & (1 << 7)) != 0
    # fmt: on


def get_collision_mat_raw_flags(f: CollisionMatFlags) -> tuple[int, int]:
    flags_lo = 0
    flags_hi = 0
    # fmt: off
    flags_lo |= (1 << 0) if f.stairs else 0
    flags_lo |= (1 << 1) if f.not_climbable else 0
    flags_lo |= (1 << 2) if f.see_through else 0
    flags_lo |= (1 << 3) if f.shoot_through else 0
    flags_lo |= (1 << 4) if f.not_cover else 0
    flags_lo |= (1 << 5) if f.walkable_path else 0
    flags_lo |= (1 << 6) if f.no_cam_collision else 0
    flags_lo |= (1 << 7) if f.shoot_through_fx else 0

    flags_hi |= (1 << 0) if f.no_decal else 0
    flags_hi |= (1 << 1) if f.no_navmesh else 0
    flags_hi |= (1 << 2) if f.no_ragdoll else 0
    flags_hi |= (1 << 3) if f.vehicle_wheel else 0
    flags_hi |= (1 << 4) if f.no_ptfx else 0
    flags_hi |= (1 << 5) if f.too_steep_for_player else 0
    flags_hi |= (1 << 6) if f.no_network_spawn else 0
    flags_hi |= (1 << 7) if f.no_cam_collision_allow_clipping else 0
    # fmt: on
    return flags_lo, flags_hi


class CollisionProperties(CollisionMatFlags, bpy.types.PropertyGroup):
    collision_index: bpy.props.IntProperty(name="Collision Index", default=0)
    procedural_id: bpy.props.IntProperty(name="Procedural ID", default=0)
    room_id: bpy.props.IntProperty(name="Room ID", default=0)
    ped_density: bpy.props.IntProperty(name="Ped Density", default=0)
    material_color_index: bpy.props.IntProperty(name="Material Color Index", default=0)


class BoundFlags(bpy.types.PropertyGroup):
    unknown: bpy.props.BoolProperty(name="UNKNOWN", default=False)
    map_weapon: bpy.props.BoolProperty(name="MAP WEAPON", default=False)
    map_dynamic: bpy.props.BoolProperty(name="MAP DYNAMIC", default=False)
    map_animal: bpy.props.BoolProperty(name="MAP ANIMAL", default=False)
    map_cover: bpy.props.BoolProperty(name="MAP COVER", default=False)
    map_vehicle: bpy.props.BoolProperty(name="MAP VEHICLE", default=False)
    vehicle_not_bvh: bpy.props.BoolProperty(name="VEHICLE NOT BVH", default=False)
    vehicle_bvh: bpy.props.BoolProperty(name="VEHICLE BVH", default=False)
    ped: bpy.props.BoolProperty(name="PED", default=False)
    ragdoll: bpy.props.BoolProperty(name="RAGDOLL", default=False)
    animal: bpy.props.BoolProperty(name="ANIMAL", default=False)
    animal_ragdoll: bpy.props.BoolProperty(name="ANIMAL RAGDOLL", default=False)
    object: bpy.props.BoolProperty(name="OBJECT", default=False)
    object_env_cloth: bpy.props.BoolProperty(name="OBJECT_ENV_CLOTH", default=False)
    plant: bpy.props.BoolProperty(name="PLANT", default=False)
    projectile: bpy.props.BoolProperty(name="PROJECTILE", default=False)
    explosion: bpy.props.BoolProperty(name="EXPLOSION", default=False)
    pickup: bpy.props.BoolProperty(name="PICKUP", default=False)
    foliage: bpy.props.BoolProperty(name="FOLIAGE", default=False)
    forklift_forks: bpy.props.BoolProperty(name="FORKLIFT FORKS", default=False)
    test_weapon: bpy.props.BoolProperty(name="TEST WEAPON", default=False)
    test_camera: bpy.props.BoolProperty(name="TEST CAMERA", default=False)
    test_ai: bpy.props.BoolProperty(name="TEST AI", default=False)
    test_script: bpy.props.BoolProperty(name="TEST SCRIPT", default=False)
    test_vehicle_wheel: bpy.props.BoolProperty(name="TEST VEHICLE WHEEL", default=False)
    glass: bpy.props.BoolProperty(name="GLASS", default=False)
    map_river: bpy.props.BoolProperty(name="MAP RIVER", default=False)
    smoke: bpy.props.BoolProperty(name="SMOKE", default=False)
    unsmashed: bpy.props.BoolProperty(name="UNSMASHED", default=False)
    map_stairs: bpy.props.BoolProperty(name="MAP STAIRS", default=False)
    map_deep_surface: bpy.props.BoolProperty(name="MAP DEEP SURFACE", default=False)


class BoundShapeProps(bpy.types.PropertyGroup):
    """Provides properties to modify a bound shape mesh. These properties are calculated from the object bounding box,
    instead of storing the values. By doing so, if the user modifies the mesh by scaling it, the properties don't end
    up out of sync.
    """

    def box_extents_getter(self) -> Vector:
        from .ybnexport import get_bound_extents

        obj = self.id_data
        bbmin, bbmax = get_bound_extents(obj)
        return bbmax - bbmin

    def box_extents_setter(self, value: Vector):
        obj = self.id_data
        create_box(obj.data, 1, Matrix.Diagonal(value))
        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="WINDOW")

    box_extents: bpy.props.FloatVectorProperty(
        name="Extents",
        size=3,
        get=box_extents_getter,
        set=box_extents_setter,
        subtype="XYZ_LENGTH",
        unit="LENGTH",
        min=0.01,
    )


    def sphere_radius_getter(self) -> float:
        from .ybnexport import get_bound_extents
        from ..tools.meshhelper import get_inner_sphere_radius

        obj = self.id_data
        bbmin, bbmax = get_bound_extents(obj)
        radius = get_inner_sphere_radius(bbmin, bbmax)
        return radius

    def sphere_radius_setter(self, value: float):
        obj = self.id_data
        create_sphere(obj.data, value)
        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="WINDOW")

    sphere_radius: bpy.props.FloatProperty(
        name="Radius",
        get=sphere_radius_getter,
        set=sphere_radius_setter,
        subtype="DISTANCE",
        unit="LENGTH",
        min=0.01,
    )


    def capsule_axis(self):
        obj = self.id_data
        match obj.sollum_type:
            case SollumType.BOUND_POLY_CAPSULE:
                return "Z"
            case _:
                return "Y"

    def capsule_radius_getter(self) -> float:
        from .ybnexport import get_bound_extents

        obj = self.id_data
        bbmin, bbmax = get_bound_extents(obj)
        extents = bbmax - bbmin
        radius = extents.x * 0.5
        return radius

    def capsule_length_getter(self) -> float:
        from .ybnexport import get_bound_extents

        obj = self.id_data
        bbmin, bbmax = get_bound_extents(obj)
        extents = bbmax - bbmin
        radius = extents.x * 0.5
        length = extents.z if self.capsule_axis() == "Z" else extents.y
        length = max(0.0, length - radius * 2.0) # Remove capsule caps from length
        return length

    def capsule_radius_setter(self, value: float):
        self.capsule_update(value, self.capsule_length_getter())

    def capsule_length_setter(self, value: float):
        self.capsule_update(self.capsule_radius_getter(), value)

    def capsule_update(self, radius: float, length: float):
        obj = self.id_data
        create_capsule(obj.data, radius=radius, length=length, axis=self.capsule_axis())
        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="WINDOW")

    capsule_radius: bpy.props.FloatProperty(
        name="Radius",
        get=capsule_radius_getter,
        set=capsule_radius_setter,
        subtype="DISTANCE",
        unit="LENGTH",
        min=0.01,
    )
    capsule_length: bpy.props.FloatProperty(
        name="Length",
        get=capsule_length_getter,
        set=capsule_length_setter,
        subtype="DISTANCE",
        unit="LENGTH",
        min=0.0,
    )


    def cylinder_axis(self):
        obj = self.id_data
        match obj.sollum_type:
            case SollumType.BOUND_POLY_CYLINDER:
                return "Z"
            case SollumType.BOUND_DISC:
                return "X"
            case _:
                return "Y"

    def cylinder_radius_getter(self) -> float:
        from .ybnexport import get_bound_extents

        obj = self.id_data
        bbmin, bbmax = get_bound_extents(obj)
        extents = bbmax - bbmin
        diameter = extents.x if self.cylinder_axis() != "X" else extents.y
        radius = diameter * 0.5
        return radius

    def cylinder_length_getter(self) -> float:
        from .ybnexport import get_bound_extents

        obj = self.id_data
        bbmin, bbmax = get_bound_extents(obj)
        extents = bbmax - bbmin
        match self.cylinder_axis():
            case "X":
                length = extents.x
            case "Y":
                length = extents.y
            case "Z":
                length = extents.z
        return length

    def cylinder_radius_setter(self, value: float):
        self.cylinder_update(value, self.cylinder_length_getter())

    def cylinder_length_setter(self, value: float):
        self.cylinder_update(self.cylinder_radius_getter(), value)

    def cylinder_update(self, radius: float, length: float):
        obj = self.id_data
        create_cylinder(obj.data, radius=radius, length=length, axis=self.cylinder_axis())
        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="WINDOW")

    cylinder_radius: bpy.props.FloatProperty(
        name="Radius",
        get=cylinder_radius_getter,
        set=cylinder_radius_setter,
        subtype="DISTANCE",
        unit="LENGTH",
        min=0.01,
    )
    cylinder_length: bpy.props.FloatProperty(
        name="Length",
        get=cylinder_length_getter,
        set=cylinder_length_setter,
        subtype="DISTANCE",
        unit="LENGTH",
        min=0.01,
    )


class CollisionMaterial(bpy.types.PropertyGroup):
    def _get_favorite(self):
        from ..sollumz_preferences import get_addon_preferences
        preferences = get_addon_preferences(bpy.context)
        return preferences.is_favorite_collision_material(self.name)

    def _set_favorite(self, value):
        from ..sollumz_preferences import get_addon_preferences
        preferences = get_addon_preferences(bpy.context)
        preferences.toggle_favorite_collision_material(self.name, value)

    index: bpy.props.IntProperty(name="Index")
    name: bpy.props.StringProperty(name="Name")
    search_name: bpy.props.StringProperty(name="Name")  # name without '_' or spaces used by list search filter
    favorite: BoolProperty(
        name="Favorite",
        get=_get_favorite,
        set=_set_favorite,
    )


class FlagPresetProp(bpy.types.PropertyGroup):
    index: bpy.props.IntProperty("Index")
    name: bpy.props.StringProperty("Name")


def get_flag_presets_path() -> str:
    from ..sollumz_preferences import get_config_directory_path
    return os.path.join(get_config_directory_path(), "flag_presets.xml")


_default_flag_presets_path = os.path.join(os.path.dirname(__file__), "flag_presets.xml")


def get_default_flag_presets_path() -> str:
    return _default_flag_presets_path


flag_presets = FlagPresetsFile()


def load_flag_presets():
    bpy.context.window_manager.sz_flag_presets.clear()

    path = get_flag_presets_path()
    if not os.path.exists(path):
        path = get_default_flag_presets_path()
        if not os.path.exists(path):
            return

    file = FlagPresetsFile.from_xml_file(path)
    flag_presets.presets = file.presets
    for index, preset in enumerate(flag_presets.presets):
        item = bpy.context.window_manager.sz_flag_presets.add()
        item.name = str(preset.name)
        item.index = index


def load_collision_materials():
    bpy.context.window_manager.sz_collision_materials.clear()
    for index, mat in enumerate(collisionmats):
        item = bpy.context.window_manager.sz_collision_materials.add()
        item.index = index
        item.name = mat.name
        item.search_name = mat.ui_name.replace(" ", "").replace("_", "")


def refresh_ui_collections():
    load_collision_materials()
    load_flag_presets()


@persistent
def on_blend_file_loaded(_):
    refresh_ui_collections()


def register():
    bpy.types.Object.sz_bound_shape = bpy.props.PointerProperty(type=BoundShapeProps)
    bpy.types.Object.composite_flags1 = bpy.props.PointerProperty(type=BoundFlags)
    bpy.types.Object.composite_flags2 = bpy.props.PointerProperty(type=BoundFlags)

    bpy.types.WindowManager.sz_collision_material_index = bpy.props.IntProperty(name="Material Index")
    bpy.types.WindowManager.sz_collision_materials = bpy.props.CollectionProperty(type=CollisionMaterial, name="Collision Materials")
    bpy.types.Scene.convert_all_to_collision_material = bpy.props.BoolProperty(
        name="", description="Convert all shared materials to a collision material", default=False)

    bpy.types.WindowManager.sz_flag_preset_index = bpy.props.IntProperty(name="Flag Preset Index")
    bpy.types.WindowManager.sz_flag_presets = bpy.props.CollectionProperty(type=FlagPresetProp, name="Flag Presets")

    bpy.types.Material.collision_properties = bpy.props.PointerProperty(
        type=CollisionProperties)
    bpy.types.Material.collision_flags = bpy.props.PointerProperty(
        type=CollisionMatFlags)

    # COLLISION TOOLS UI PROPERTIES
    bpy.types.Scene.create_poly_bound_type = bpy.props.EnumProperty(
        items=[
            (SollumType.BOUND_POLY_BOX.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_BOX], "Create a bound poly box object"),
            (SollumType.BOUND_POLY_SPHERE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_SPHERE], "Create a bound poly sphere object"),
            (SollumType.BOUND_POLY_CAPSULE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_CAPSULE], "Create a bound poly capsule object"),
            (SollumType.BOUND_POLY_CYLINDER.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_CYLINDER], "Create a bound poly cylinder object"),
        ],
        name="Type",
        default=SollumType.BOUND_POLY_BOX.value
    )

    bpy.types.Scene.create_bound_type = bpy.props.EnumProperty(
        items=[
            (SollumType.BOUND_COMPOSITE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE], "Create a bound composite object"),
            (SollumType.BOUND_GEOMETRYBVH.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRYBVH], "Create a bound geometrybvh object"),
            (SollumType.BOUND_BOX.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_BOX], "Create a bound box object"),
            (SollumType.BOUND_SPHERE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_SPHERE], "Create a bound sphere object"),
            (SollumType.BOUND_CAPSULE.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_CAPSULE], "Create a bound capsule object"),
            (SollumType.BOUND_CYLINDER.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_CYLINDER], "Create a bound cylinder object"),
            (SollumType.BOUND_DISC.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_DISC], "Create a bound disc object"),
        ],
        name="Type",
        default=SollumType.BOUND_COMPOSITE.value
    )

    bpy.types.Scene.poly_bound_type_verts = bpy.props.EnumProperty(
        items=[
            (SollumType.BOUND_POLY_BOX.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_POLY_BOX], "Create a bound polygon box object"),
            (SollumType.BOUND_BOX.value, SOLLUMZ_UI_NAMES[SollumType.BOUND_BOX], "Create a bound box object")],
        name="Type",
        default=SollumType.BOUND_POLY_BOX.value
    )

    bpy.types.Scene.poly_edge = bpy.props.EnumProperty(name="Edge", items=[("long", "Long Edge", "Create along the long edge"),
                                                                           ("short", "Short Edge", "Create along the short edge")])
    bpy.types.Scene.bound_child_type = bpy.props.EnumProperty(
        items=[
            (SollumType.BOUND_GEOMETRY.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRY], "Create bound geometry children."),
            (SollumType.BOUND_GEOMETRYBVH.value,
             SOLLUMZ_UI_NAMES[SollumType.BOUND_GEOMETRYBVH], "Create bound geometrybvh children.")
        ],
        name="Child Type",
        description="The bound type of the Composite Children",
        default=SollumType.BOUND_GEOMETRYBVH.value)
    bpy.types.Scene.create_seperate_composites = bpy.props.BoolProperty(
        name="Separate Objects", description="Create a separate Composite for each selected object")

    bpy.types.Scene.center_composite_to_selection = bpy.props.BoolProperty(
        name="Center to Selection", description="Center the Bound Composite to all selected objects", default=True)

    bpy.types.WindowManager.sz_create_bound_box_parent = bpy.props.PointerProperty(
        name="Parent", description="Parent for the new box object. If not set, the parent of the active object is used.",
        type=bpy.types.Object
    )

    bpy.app.handlers.load_post.append(on_blend_file_loaded)


def unregister():
    del bpy.types.Object.composite_flags1
    del bpy.types.Object.composite_flags2
    del bpy.types.WindowManager.sz_collision_material_index
    del bpy.types.WindowManager.sz_collision_materials
    del bpy.types.Scene.convert_all_to_collision_material
    del bpy.types.Material.collision_properties
    del bpy.types.Material.collision_flags
    del bpy.types.WindowManager.sz_flag_presets
    del bpy.types.WindowManager.sz_flag_preset_index
    del bpy.types.Scene.create_poly_bound_type
    del bpy.types.Scene.create_seperate_composites
    del bpy.types.Scene.create_bound_type
    del bpy.types.Scene.bound_child_type
    del bpy.types.Scene.center_composite_to_selection
    del bpy.types.WindowManager.sz_create_bound_box_parent

    bpy.app.handlers.load_post.remove(on_blend_file_loaded)
