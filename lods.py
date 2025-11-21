"""LOD Management system."""
import bpy
from bpy.types import (
    Context,
    Mesh,
    PropertyGroup,
    Object,
    Operator,
)
from bpy.props import (
    EnumProperty,
    PointerProperty,
    StringProperty,
    BoolProperty,
)
from typing import Callable, Optional
from .sollumz_properties import (
    SollumType,
    LODLevel,
    LODLevelEnumItems,
    FRAGMENT_TYPES,
    DRAWABLE_TYPES,
    SOLLUMZ_UI_NAMES,
    BOUND_TYPES,
    BOUND_POLYGON_TYPES,
)
from .tools.blenderhelper import lod_level_enum_flag_prop_factory
from .sollumz_helper import find_sollumz_parent
from .icons import icon_manager


class LODLevelProps(PropertyGroup):
    def on_lod_level_enter(self):
        """Called when the LOD level switches to this level."""
        obj: Object = self.id_data

        if self.has_mesh:
            # Update the object current mesh to this LOD mesh
            obj.data = self.mesh_ref
            self.mesh_ref = None  # keep a single ref to the mesh, in Object.data

        if obj.name in bpy.context.view_layer.objects:
            obj.hide_set(not self.has_mesh)

    def on_lod_level_exit(self):
        """Called when the LOD level switches aways from this level."""
        obj: Object = self.id_data

        # Store a reference to the mesh
        self.mesh_ref = obj.data if self.has_mesh else None

    def _get_mesh_name(self) -> str:
        m = self.mesh
        return m.name if m is not None else ""

    def _set_mesh_name(self, value: str) -> str:
        self.mesh = bpy.data.meshes.get(value, None)

    # Wrapper property so we can modify the LOD meshes from the UI without keeping a reference to the mesh of the
    # active LOD.
    mesh_name: StringProperty(get=_get_mesh_name, set=_set_mesh_name)

    # Only set on non-active LOD levels, used to keep a reference to the mesh data-block so Blender doesn't remove it
    # during garbage collection. For the active LOD, the mesh is the current object.data mesh.
    # Blender expects a single reference to the mesh (in object.data) for many operations, otherwise asks
    # the user to duplicate the mesh and then object.data becomes out-of-sync with Sollumz LODs.
    mesh_ref: PointerProperty(type=Mesh)  # DO NOT MODIFY DIRECTLY OUTSIDE THIS CLASS, use .mesh or .mesh_name

    # Whether this LOD actually has a mesh. Needed because when a level that doesn't have a mesh becomes the active LOD,
    # object.data keeps the previous mesh and instead the object is hidden, so when switching away we wouldn't know if
    # object.data is actually our mesh or not.
    has_mesh: BoolProperty(default=False)  # DO NOT MODIFY DIRECTLY OUTSIDE THIS CLASS, use .mesh or .mesh_name

    @property
    def mesh(self) -> Optional[Mesh]:
        """Gets the mesh of this LOD level, or ``None`` if there is no mesh."""
        if not self.has_mesh:
            return None

        obj: Object = self.id_data
        lods: LODLevels = obj.sz_lods
        if lods.active_lod_level == self.level:
            return obj.data
        else:
            return self.mesh_ref

    @mesh.setter
    def mesh(self, value: Optional[Mesh]):
        """Sets the mesh of this LOD level. Set to ``None`` to remove the mesh."""
        obj: Object = self.id_data
        lods: LODLevels = obj.sz_lods
        self.has_mesh = value is not None
        if lods.active_lod_level == self.level:
            self.mesh_ref = None
            if self.has_mesh:
                obj.data = value

            if obj.name in bpy.context.view_layer.objects:
                obj.hide_set(not self.has_mesh)
        else:
            self.mesh_ref = value

    @property
    def level(self) -> LODLevel:
        obj: Object = self.id_data
        lods: LODLevels = obj.sz_lods
        if lods.very_high == self:
            return LODLevel.VERYHIGH
        if lods.high == self:
            return LODLevel.HIGH
        if lods.medium == self:
            return LODLevel.MEDIUM
        if lods.low == self:
            return LODLevel.LOW
        if lods.very_low == self:
            return LODLevel.VERYLOW

        assert False, "LODLevelProps for unknown LOD level"


class LODLevels(PropertyGroup):
    def on_lod_level_update(self, context: Context):
        if self.disable_active_lod_level_callback:
            return

        prev_lod = self.get_lod(self.active_lod_level_prev)
        curr_lod = self.get_lod(self.active_lod_level)
        prev_lod.on_lod_level_exit()
        curr_lod.on_lod_level_enter()
        self.active_lod_level_prev = self.active_lod_level

    active_lod_level: EnumProperty(items=LODLevelEnumItems, update=on_lod_level_update)
    active_lod_level_prev: EnumProperty(items=LODLevelEnumItems)
    very_high: PointerProperty(type=LODLevelProps)
    high: PointerProperty(type=LODLevelProps)
    medium: PointerProperty(type=LODLevelProps)
    low: PointerProperty(type=LODLevelProps)
    very_low: PointerProperty(type=LODLevelProps)

    disable_active_lod_level_callback: BoolProperty(default=False)

    @property
    def active_lod(self) -> LODLevelProps:
        return self.get_lod(self.active_lod_level)

    def get_lod(self, lod_level: LODLevel) -> LODLevelProps:
        match lod_level:
            case LODLevel.VERYHIGH:
                return self.very_high
            case LODLevel.HIGH:
                return self.high
            case LODLevel.MEDIUM:
                return self.medium
            case LODLevel.LOW:
                return self.low
            case LODLevel.VERYLOW:
                return self.very_low
            case _:
                assert False, f"Unknown LOD level '{lod_level}'"

    def set_highest_lod_active(self):
        for lod_level in LODLevel:
            lod = self.get_lod(lod_level)
            if lod.mesh is not None:
                self.active_lod_level = lod_level
                return


class SOLLUMZ_OT_set_lod_level(Operator):
    bl_idname = "sollumz.set_lod_level"
    bl_label = "Set LOD Level"
    bl_description = "Set the viewing level for the selected Fragment/Drawable"

    lod_level: EnumProperty(name="LOD Level", items=LODLevelEnumItems)

    @classmethod
    def poll(cls, context):
        active_obj = context.view_layer.objects.active
        return active_obj is not None and active_obj.mode == "OBJECT" and find_sollumz_parent(active_obj)

    def execute(self, context):
        objs = set()

        active_obj = context.view_layer.objects.active
        objs.add(find_sollumz_parent(active_obj))

        for selected_obj in context.view_layer.objects.selected:
            if obj := find_sollumz_parent(selected_obj):
                objs.add(obj)

        lod_level = LODLevel(self.lod_level)
        for obj in objs:
            set_all_lods(obj, lod_level)

        return {"FINISHED"}


class SOLLUMZ_OT_hide_object(Operator):
    bl_idname = "sollumz.hide_object"
    bl_label = "Hidden"
    bl_description = "Set the viewing level for the selected Fragment/Drawable"

    @classmethod
    def poll(cls, context):
        active_obj = context.view_layer.objects.active
        return active_obj is not None and active_obj.mode == "OBJECT" and find_sollumz_parent(active_obj)

    def execute(self, context):
        objs = set()

        active_obj = context.view_layer.objects.active
        objs.add(find_sollumz_parent(active_obj))

        for selected_obj in context.view_layer.objects.selected:
            if obj := find_sollumz_parent(selected_obj):
                objs.add(obj)

        for obj in objs:
            do_hide = not obj.hide_get()
            obj.hide_set(do_hide)

            for child in obj.children_recursive:
                active_lod = child.sz_lods.active_lod
                if child.sollum_type != SollumType.DRAWABLE_MODEL or active_lod.mesh is None:
                    continue

                child.hide_set(do_hide)

        return {"FINISHED"}


class SOLLUMZ_OT_HIDE_COLLISIONS(bpy.types.Operator):
    bl_idname = "sollumz.hide_collisions"
    bl_label = "Hide Collisions"
    bl_description = "Hide all collisions in the scene"

    def execute(self, context):
        context.scene.sollumz_show_collisions = False
        set_collision_visibility(False)

        return {"FINISHED"}


class SOLLUMZ_OT_SHOW_COLLISIONS(bpy.types.Operator):
    bl_idname = "sollumz.show_collisions"
    bl_label = "Show Collisions"
    bl_description = "Show all collisions in the scene"

    def execute(self, context):
        context.scene.sollumz_show_collisions = True
        set_collision_visibility(True)

        return {"FINISHED"}


class SOLLUMZ_OT_SHOW_SHATTERMAPS(bpy.types.Operator):
    bl_idname = "sollumz.show_shattermaps"
    bl_label = "Show Shattermaps"
    bl_description = "Show all shattermaps in the scene"

    def execute(self, context):
        context.scene.sollumz_show_shattermaps = True
        set_shattermaps_visibility(True)

        return {"FINISHED"}


class SOLLUMZ_OT_HIDE_SHATTERMAPS(bpy.types.Operator):
    bl_idname = "sollumz.hide_shattermaps"
    bl_label = "Hide Shattermaps"
    bl_description = "Hide all shattermaps in the scene"

    def execute(self, context):
        context.scene.sollumz_show_shattermaps = False
        set_shattermaps_visibility(False)

        return {"FINISHED"}


class SOLLUMZ_OT_copy_lod(bpy.types.Operator):
    bl_idname = "sollumz.copy_lod"
    bl_label = "Copy LOD"
    bl_description = "Copy the current LOD level into the specified LOD level"
    bl_options = {"REGISTER", "UNDO"}

    copy_lod_levels: lod_level_enum_flag_prop_factory(default={LODLevel.HIGH})

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        return aobj is not None and aobj.sz_lods.active_lod.mesh is not None

    def draw(self, context):
        self.layout.props_enum(self, "copy_lod_levels")

    def execute(self, context):
        aobj = context.active_object
        lods = aobj.sz_lods

        active_lod = lods.active_lod
        active_lod_mesh = active_lod.mesh

        for lod_level in self.copy_lod_levels:
            lod = lods.get_lod(lod_level)

            if lod is None:
                return {"CANCELLED"}

            if lod.mesh is not None:
                self.report({"INFO"}, f"{SOLLUMZ_UI_NAMES[lod_level]} already has a mesh!")
                return {"CANCELLED"}

            lod.mesh = active_lod_mesh.copy()

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class SOLLUMZ_PT_LOD_LEVEL_PANEL(bpy.types.Panel):
    bl_label = "Sollumz LODs"
    bl_idname = "SOLLUMZ_PT_LOD_LEVEL_PANEL"
    bl_space_type = "PROPERTIES"
    bl_region_type = "WINDOW"
    bl_context = "data"

    @classmethod
    def poll(cls, context):
        active_obj = context.view_layer.objects.active
        return active_obj is not None and active_obj.type == "MESH" and active_obj.sollum_type in [*FRAGMENT_TYPES, *DRAWABLE_TYPES]

    def draw_header(self, context):
        icon_manager.icon_label("sollumz_icon", self)

    def draw(self, context):
        layout = self.layout
        active_obj = context.view_layer.objects.active
        lods = active_obj.sz_lods

        layout.enabled = active_obj.mode == "OBJECT"
        row = layout.row()
        col = row.column(align=True)
        for lod_level in LODLevel:
            lod = lods.get_lod(lod_level)
            lod_split = col.split(align=True, factor=0.3)
            lod_split.prop_enum(lods, "active_lod_level", lod_level)
            lod_split.prop_search(lod, "mesh_name", bpy.data, "meshes", text="")

        row.operator(SOLLUMZ_OT_copy_lod.bl_idname, icon="COPYDOWN", text="")


def set_collision_visibility(is_visible: bool):
    """Set visibility of all collision objects in the scene"""
    for obj in bpy.context.view_layer.objects:
        obj_is_collision = obj.sollum_type in BOUND_TYPES or obj.sollum_type in BOUND_POLYGON_TYPES

        if not obj_is_collision:
            continue

        obj.hide_set(not is_visible)


def set_shattermaps_visibility(is_visible: bool):
    """Set visibility of all shattermap objects in the scene"""
    for obj in bpy.context.view_layer.objects:
        if obj.sollum_type != SollumType.SHATTERMAP:
            continue

        obj.hide_set(not is_visible)


def set_all_lods(obj: bpy.types.Object, lod_level: LODLevel):
    """Set LOD levels of all of children of ``obj``"""
    obj.hide_set(False)

    for child in obj.children_recursive:
        if child.type == "MESH" and child.mode == "OBJECT" and child.sollum_type == SollumType.DRAWABLE_MODEL:
            child.sz_lods.active_lod_level = lod_level
            continue


def operates_on_lod_level(func: Callable):
    """Decorator for functions that operate on a particular LOD level of an object.
    Will automatically set the LOD level to ``lod_level`` at the beginning of execution
    and will set it back to the original LOD level at the end."""
    def wrapper(model_obj: bpy.types.Object, lod_level: LODLevel, *args, **kwargs):
        current_lod_level = model_obj.sz_lods.active_lod_level

        was_hidden = model_obj.hide_get()
        model_obj.sz_lods.active_lod_level = lod_level

        res = func(model_obj, lod_level, *args, **kwargs)

        # Set the lod level back to what it was
        model_obj.sz_lods.active_lod_level = current_lod_level
        model_obj.hide_set(was_hidden)

        return res

    return wrapper


def register():
    bpy.types.Object.sz_lods = bpy.props.PointerProperty(type=LODLevels)
    bpy.types.Scene.sollumz_show_collisions = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.sollumz_show_shattermaps = bpy.props.BoolProperty(default=True)
    bpy.types.Scene.sollumz_copy_lod_level = bpy.props.EnumProperty(items=LODLevelEnumItems)


def unregister():
    del bpy.types.Object.sz_lods
    del bpy.types.Scene.sollumz_show_collisions
    del bpy.types.Scene.sollumz_show_shattermaps
    del bpy.types.Scene.sollumz_copy_lod_level
