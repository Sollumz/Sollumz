"""LOD Management system."""
import bpy
from typing import Optional
from .sollumz_properties import SollumType, LODLevel, FRAGMENT_TYPES, SOLLUMZ_UI_NAMES, items_from_enums
from .sollumz_ui import SOLLUMZ_PT_VIEW_PANEL
from .tools.blenderhelper import get_children_recursive
from .sollumz_helper import find_fragment_parent


class ObjectLODProps(bpy.types.PropertyGroup):
    def update_object(self, context):
        obj: bpy.types.Object = self.id_data

        active_obj_lod = obj.sollumz_object_lods.active_lod

        if active_obj_lod == self and self.mesh is not None:
            obj.data = self.mesh
            obj.hide_set(False)
        elif self.mesh is None:
            obj.hide_set(True)

    type: bpy.props.EnumProperty(
        items=items_from_enums(LODLevel))
    mesh: bpy.props.PointerProperty(
        type=bpy.types.Mesh, update=update_object)


class LODLevels(bpy.types.PropertyGroup):
    def get_lod(self, lod_type: str) -> ObjectLODProps | None:
        for lod in self.lods:
            if lod.type == lod_type:
                return lod

    def set_lod_mesh(self, lod_type: str, mesh: bpy.types.Mesh) -> ObjectLODProps | None:
        for lod in self.lods:
            if lod.type == lod_type:
                lod.mesh = mesh
                return lod

    def add_lod(self, lod_type: str, mesh: Optional[bpy.types.Mesh] = None) -> ObjectLODProps | None:
        # Can't have multiple lods with the same type
        if self.get_lod(lod_type):
            return None

        self.lods.add()
        i = len(self.lods) - 1
        obj_lod = self.lods[i]
        obj_lod.type = lod_type

        if mesh is not None:
            obj_lod.mesh = mesh

        return obj_lod

    def remove_lod(self, lod_type: str):
        for i, lod in enumerate(self.lods):
            if lod.type == lod_type:
                self.lods.remove(i)
                return

    def set_active_lod(self, lod_type: str):
        for i, lod in enumerate(self.lods):
            if lod.type == lod_type:
                self.active_lod_index = i
                return

    def update_active_lod(self, context):
        self.active_lod.update_object(context)

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
    bl_description = "Set the viewing level for the selected Fragment"

    @classmethod
    def poll(cls, context):
        active_obj = context.view_layer.objects.active

        return active_obj is not None and find_fragment_parent(active_obj)

    def set_fragment_object_layer(self, frag_obj: bpy.types.Object, context: bpy.types.Context):
        context.scene.sollumz_frag_is_hidden = False
        frag_obj.hide_set(False)

        for child in get_children_recursive(frag_obj):
            if child.sollum_type not in FRAGMENT_TYPES or child.sollum_type == SollumType.FRAGVEHICLEWINDOW:
                continue

            if child.type == "MESH":
                child.sollumz_object_lods.set_active_lod(self.LOD_LEVEL)
                continue

    def execute(self, context):
        active_obj = context.view_layer.objects.active
        frag_obj = find_fragment_parent(active_obj)
        self.set_fragment_object_layer(frag_obj, context)

        return {"FINISHED"}


class SOLLUMZ_OT_SET_FRAG_VERY_HIGH(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_frag_very_high"
    bl_label = "Very High"

    LOD_LEVEL = LODLevel.VERYHIGH


class SOLLUMZ_OT_SET_FRAG_HIGH(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_frag_high"
    bl_label = "High"

    LOD_LEVEL = LODLevel.HIGH


class SOLLUMZ_OT_SET_FRAG_MED(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_frag_med"
    bl_label = "Medium"

    LOD_LEVEL = LODLevel.MEDIUM


class SOLLUMZ_OT_SET_FRAG_LOW(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_frag_low"
    bl_label = "Low"

    LOD_LEVEL = LODLevel.LOW


class SOLLUMZ_OT_SET_FRAG_VLOW(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_frag_vlow"
    bl_label = "Very Low"

    LOD_LEVEL = LODLevel.VERYLOW


class SOLLUMZ_OT_SET_FRAG_HIDDEN(bpy.types.Operator, SetLodLevelHelper):
    bl_idname = "sollumz.set_frag_hidden"
    bl_label = "Hidden"

    @staticmethod
    def set_highest_lod_active(obj: bpy.types.Object):
        for lod_level in [LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW]:
            if obj.sollumz_object_lods.get_lod(lod_level) is None:
                continue

            obj.sollumz_object_lods.set_active_lod(lod_level)

            break

    def execute(self, context):
        active_obj = context.view_layer.objects.active
        frag_obj = find_fragment_parent(active_obj)
        frag_hidden = context.scene.sollumz_frag_is_hidden

        do_hide = not frag_hidden
        context.scene.sollumz_frag_is_hidden = do_hide

        frag_obj.hide_set(do_hide)

        for child in get_children_recursive(frag_obj):
            if child.sollum_type not in FRAGMENT_TYPES or child.sollum_type == SollumType.FRAGVEHICLEWINDOW:
                continue

            if child.type == "MESH" and do_hide is False:
                SOLLUMZ_OT_SET_FRAG_HIDDEN.set_highest_lod_active(child)

            child.hide_set(do_hide)

        return {"FINISHED"}


class SOLLUMZ_UL_OBJ_LODS_LIST(bpy.types.UIList):
    bl_idname = "SOLLUMZ_UL_OBJ_LODS_LIST"

    def draw_item(
        self, context, layout: bpy.types.UILayout, data, item, icon, active_data, active_propname, index
    ):
        col = layout.column()
        col.scale_x = 0.35
        col.label(text=SOLLUMZ_UI_NAMES[item.type])
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
        return active_obj is not None and active_obj.type == "MESH" and active_obj.sollum_type in [SollumType.FRAGGROUP, SollumType.FRAG_GEOM, SollumType.FRAGCHILD]

    def draw(self, context):
        layout = self.layout
        active_obj = context.view_layer.objects.active
        row = layout.row()
        row.template_list(
            SOLLUMZ_UL_OBJ_LODS_LIST.bl_idname, "", active_obj.sollumz_object_lods, "lods", active_obj.sollumz_object_lods, "active_lod_index"
        )

        layout.enabled = active_obj.mode == "OBJECT"


class SOLLUMZ_PT_LOD_VIEW_TOOLS(bpy.types.Panel):
    bl_label = "Fragment Mesh LODs"
    bl_idname = "SOLLUMZ_PT_LOD_VIEW_TOOLS"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"HIDE_HEADER"}
    bl_parent_id = SOLLUMZ_PT_VIEW_PANEL.bl_idname

    def draw(self, context):
        layout = self.layout
        layout.label(text="Fragment Mesh LODs")

        grid = layout.grid_flow(align=True, row_major=True)
        grid.scale_x = 0.7
        grid.operator(SOLLUMZ_OT_SET_FRAG_VERY_HIGH.bl_idname)
        grid.operator(SOLLUMZ_OT_SET_FRAG_HIGH.bl_idname)
        grid.operator(SOLLUMZ_OT_SET_FRAG_MED.bl_idname)
        grid.operator(SOLLUMZ_OT_SET_FRAG_LOW.bl_idname)
        grid.operator(SOLLUMZ_OT_SET_FRAG_VLOW.bl_idname)
        grid.operator(SOLLUMZ_OT_SET_FRAG_HIDDEN.bl_idname)

        grid.enabled = context.view_layer.objects.active is not None and context.view_layer.objects.active.mode == "OBJECT"


def register():
    bpy.types.Object.sollumz_object_lods = bpy.props.PointerProperty(
        type=LODLevels)
    bpy.types.Scene.sollumz_frag_is_hidden = bpy.props.BoolProperty()


def unregister():
    del bpy.types.Object.sollumz_object_lods
    del bpy.types.Scene.sollumz_frag_is_hidden
