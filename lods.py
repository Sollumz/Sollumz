"""LOD Management system."""
import bpy
from typing import Optional
from .sollumz_properties import SollumType, LODLevel, FRAGMENT_TYPES, DRAWABLE_TYPES, SOLLUMZ_UI_NAMES, BOUND_TYPES, BOUND_POLYGON_TYPES, items_from_enums
from .tools.blenderhelper import get_all_collections
from .sollumz_helper import find_sollumz_parent


class ObjectLODProps(bpy.types.PropertyGroup):
    def update_mesh(self, context: bpy.types.Context):
        obj: bpy.types.Object = self.id_data

        active_obj_lod = obj.sollumz_lods.active_lod

        if active_obj_lod == self and self.mesh is not None:
            obj.data = self.mesh
            if obj.name in context.view_layer.objects:
                obj.hide_set(False)
        elif self.mesh is None:
            if obj.name in context.view_layer.objects:
                obj.hide_set(True)

    level: bpy.props.EnumProperty(
        items=items_from_enums(LODLevel))
    mesh: bpy.props.PointerProperty(
        type=bpy.types.Mesh, update=update_mesh)


class LODLevels(bpy.types.PropertyGroup):
    def get_lod(self, lod_level: str) -> ObjectLODProps | None:
        for lod in self.lods:
            if lod.level == lod_level:
                return lod

    def set_lod_mesh(self, lod_level: str, mesh: bpy.types.Mesh) -> ObjectLODProps | None:
        for lod in self.lods:
            if lod.level == lod_level:
                lod.mesh = mesh
                return lod

    def add_lod(self, lod_level: str, mesh: Optional[bpy.types.Mesh] = None) -> ObjectLODProps | None:
        # Can't have multiple lods with the same type
        if self.get_lod(lod_level):
            return None

        self.lods.add()
        i = len(self.lods) - 1
        obj_lod = self.lods[i]
        obj_lod.level = lod_level

        if mesh is not None:
            obj_lod.mesh = mesh

        return obj_lod

    def set_active_lod(self, lod_level: str):
        for i, lod in enumerate(self.lods):
            if lod.level == lod_level:
                self.active_lod_index = i
                return

    def update_active_lod(self, context):
        self.active_lod.update_mesh(context)

    def add_empty_lods(self):
        """Add all LOD lods with no meshes assigned."""
        self.add_lod(LODLevel.VERYHIGH)
        self.add_lod(LODLevel.HIGH)
        self.add_lod(LODLevel.MEDIUM)
        self.add_lod(LODLevel.LOW)
        self.add_lod(LODLevel.VERYLOW)

    @property
    def active_lod(self) -> ObjectLODProps | None:
        if self.active_lod_index < len(self.lods):
            return self.lods[self.active_lod_index]

    lods: bpy.props.CollectionProperty(type=ObjectLODProps)
    active_lod_index: bpy.props.IntProperty(
        min=0, update=update_active_lod)


class SetLodLevelHelper:
    """Helper class for setting the LOD level of Sollumz objects."""
    LOD_LEVEL: LODLevel = LODLevel.HIGH
    bl_description = "Set the viewing level for the selected Fragment/Drawable"

    @classmethod
    def poll(cls, context):
        active_obj = context.view_layer.objects.active
        return active_obj is not None and find_sollumz_parent(active_obj)

    def execute(self, context):
        active_obj = context.view_layer.objects.active
        obj = find_sollumz_parent(active_obj)
        set_all_lods(obj, self.LOD_LEVEL)

        return {"FINISHED"}


class SOLLUMZ_OT_SET_LOD_VERY_HIGH(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_lod_very_high"
    bl_label = "Very High"

    LOD_LEVEL = LODLevel.VERYHIGH


class SOLLUMZ_OT_SET_LOD_HIGH(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_lod_high"
    bl_label = "High"

    LOD_LEVEL = LODLevel.HIGH


class SOLLUMZ_OT_SET_LOD_MED(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_lod_med"
    bl_label = "Medium"

    LOD_LEVEL = LODLevel.MEDIUM


class SOLLUMZ_OT_SET_LOD_LOW(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_lod_low"
    bl_label = "Low"

    LOD_LEVEL = LODLevel.LOW


class SOLLUMZ_OT_SET_LOD_VLOW(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_lod_vlow"
    bl_label = "Very Low"

    LOD_LEVEL = LODLevel.VERYLOW


class SOLLUMZ_OT_HIDE_OBJECT(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.hide_object"
    bl_label = "Hidden"

    def execute(self, context):
        active_obj = context.view_layer.objects.active
        obj = find_sollumz_parent(active_obj)
        obj_hidden = obj.sollumz_obj_is_hidden

        do_hide = not obj_hidden
        obj.sollumz_obj_is_hidden = do_hide

        obj.hide_set(do_hide)

        for child in obj.children_recursive:
            active_lod = child.sollumz_lods.active_lod
            if child.sollum_type != SollumType.DRAWABLE_MODEL or not active_lod or active_lod.mesh is None:
                continue

            child.hide_set(do_hide)

        return {"FINISHED"}


class SOLLUMZ_OT_HIDE_COLLISIONS(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.hide_collisions"
    bl_label = "Hide Collisions"
    bl_description = "Hide all collisions in the scene"

    def execute(self, context):
        for collection in get_all_collections():
            for obj in collection.all_objects:
                if not (obj.sollum_type in BOUND_TYPES or obj.sollum_type in BOUND_POLYGON_TYPES and obj.name in bpy.context.view_layer.objects):
                    continue

                obj.hide_set(not context.scene.sollumz_hide_collisions)

        context.scene.sollumz_hide_collisions = not context.scene.sollumz_hide_collisions

        return {"FINISHED"}


class SOLLUMZ_OT_HIDE_GLASS_SHARDS(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.hide_glass_shards"
    bl_label = "Hide Glass Shards"
    bl_description = "Hide all glass shards in the scene"

    def execute(self, context):
        for collection in get_all_collections():
            for obj in collection.all_objects:
                if obj.sollum_type != SollumType.FRAGVEHICLEWINDOW:
                    continue

                obj.hide_set(not context.scene.sollumz_hide_glass_shards)

        context.scene.sollumz_hide_glass_shards = not context.scene.sollumz_hide_glass_shards

        return {"FINISHED"}


class SOLLUMZ_OT_copy_lod(bpy.types.Operator):
    bl_idname = "sollumz.copy_lod"
    bl_label = "Copy LOD"
    bl_description = "Copy the current LOD level into the specified LOD level"
    bl_options = {"REGISTER", "UNDO"}

    copy_lod_level: bpy.props.EnumProperty(items=items_from_enums(LODLevel))

    @classmethod
    def poll(self, context):
        aobj = context.active_object

        return aobj is not None and aobj.sollumz_lods.active_lod is not None

    def draw(self, context):
        self.layout.props_enum(self, "copy_lod_level")

    def execute(self, context):
        aobj = context.active_object

        active_lod = aobj.sollumz_lods.active_lod
        lod = aobj.sollumz_lods.get_lod(self.copy_lod_level)

        if lod is None:
            return {"CANCELLED"}

        if lod.mesh is not None:
            self.report(
                {"INFO"}, f"{SOLLUMZ_UI_NAMES[self.copy_lod_level]} already has a mesh!")
            return {"CANCELLED"}

        lod.mesh = active_lod.mesh.copy()

        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class SOLLUMZ_UL_OBJ_LODS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_OBJ_LODS_LIST"

    def draw_item(
        self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index
    ):
        col = layout.column()
        col.scale_x = 0.35
        col.label(text=SOLLUMZ_UI_NAMES[item.level])
        col = layout.column()
        col.scale_x = 0.65
        col.prop(item, "mesh", text="")


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

    def draw(self, context):
        layout = self.layout
        active_obj = context.view_layer.objects.active

        layout.enabled = active_obj.mode == "OBJECT"

        row = layout.row()
        row.template_list(
            SOLLUMZ_UL_OBJ_LODS_LIST.bl_idname, "", active_obj.sollumz_lods, "lods", active_obj.sollumz_lods, "active_lod_index"
        )

        row.operator("sollumz.copy_lod", icon="COPYDOWN", text="")


def set_all_lods(obj: bpy.types.Object, lod_level: LODLevel):
    """Set LOD levels of all of children of ``obj``"""
    obj.sollumz_obj_is_hidden = False
    obj.hide_set(False)

    for child in obj.children_recursive:
        if child.type == "MESH" and child.sollum_type == SollumType.DRAWABLE_MODEL:
            child.sollumz_lods.set_active_lod(lod_level)
            continue


def register():
    bpy.types.Object.sollumz_lods = bpy.props.PointerProperty(
        type=LODLevels)
    bpy.types.Object.sollumz_obj_is_hidden = bpy.props.BoolProperty()
    bpy.types.Scene.sollumz_hide_collisions = bpy.props.BoolProperty()
    bpy.types.Scene.sollumz_hide_glass_shards = bpy.props.BoolProperty()
    bpy.types.Scene.sollumz_copy_lod_level = bpy.props.EnumProperty(
        items=items_from_enums(LODLevel))


def unregister():
    del bpy.types.Object.sollumz_lods
    del bpy.types.Object.sollumz_obj_is_hidden
    del bpy.types.Scene.sollumz_hide_glass_shards
    del bpy.types.Scene.sollumz_copy_lod_level
