import bpy
from bpy.props import (
    FloatProperty,
    BoolProperty,
)
import bmesh
from .cloth import is_cloth_mesh_object, ClothAttr, mesh_add_cloth_attribute, mesh_has_cloth_attribute


class SOLLUMZ_OT_CLOTH_TEST(bpy.types.Operator):
    """"""
    bl_idname = "sollumz.cloth_test"
    bl_label = "Test"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return any(is_cloth_mesh_object(o) for o in context.selected_objects)

    def execute(self, context):
        for obj in context.selected_objects:
            if not is_cloth_mesh_object(obj):
                continue

            print(f"{obj=}")

        return {"FINISHED"}


class SOLLUMZ_OT_CLOTH_SET_VERTEX_WEIGHT(bpy.types.Operator):
    """"""
    bl_idname = "sollumz.cloth_set_vertex_weight"
    bl_label = "Modify Cloth Vertex Weights"
    bl_options = {"REGISTER", "UNDO"}

    vertex_weight: FloatProperty(
        name=ClothAttr.VERTEX_WEIGHT.label, description=ClothAttr.VERTEX_WEIGHT.description,
        default=ClothAttr.VERTEX_WEIGHT.default_value, min=0.00001, max=1.0, precision=6, step=1
    )
    selection: BoolProperty(name="Selection", default=True)

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and is_cloth_mesh_object(context.active_object)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        if not mesh_has_cloth_attribute(mesh, ClothAttr.VERTEX_WEIGHT):
            mesh_add_cloth_attribute(mesh, ClothAttr.VERTEX_WEIGHT)

        bm = bmesh.from_edit_mesh(mesh)
        vertex_weight_layer = bm.verts.layers.float.get(ClothAttr.VERTEX_WEIGHT)
        for v in bm.verts:
            if not self.selection or v.select:
                v[vertex_weight_layer] = self.vertex_weight

        bmesh.update_edit_mesh(mesh)

        return {"FINISHED"}


class SOLLUMZ_OT_CLOTH_SET_INFLATION_SCALE(bpy.types.Operator):
    """"""
    bl_idname = "sollumz.cloth_set_inflation_scale"
    bl_label = "Modify Cloth Inflation Scale"
    bl_options = {"REGISTER", "UNDO"}

    inflation_scale: FloatProperty(
        name=ClothAttr.INFLATION_SCALE.label, description=ClothAttr.INFLATION_SCALE.description,
        default=ClothAttr.INFLATION_SCALE.default_value, min=0.0, max=1.0
    )
    selection: BoolProperty(name="Selection", default=True)

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and is_cloth_mesh_object(context.active_object)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        if not mesh_has_cloth_attribute(mesh, ClothAttr.INFLATION_SCALE):
            mesh_add_cloth_attribute(mesh, ClothAttr.INFLATION_SCALE)

        bm = bmesh.from_edit_mesh(mesh)
        inflation_scale_layer = bm.verts.layers.float.get(ClothAttr.INFLATION_SCALE)
        for v in bm.verts:
            if not self.selection or v.select:
                v[inflation_scale_layer] = self.inflation_scale

        bmesh.update_edit_mesh(mesh)

        return {"FINISHED"}


class SOLLUMZ_OT_CLOTH_SET_PINNED(bpy.types.Operator):
    """"""
    bl_idname = "sollumz.cloth_set_pinned"
    bl_label = "Pin Cloth Vertices"
    bl_options = {"REGISTER", "UNDO"}

    pin: BoolProperty(
        name="Pin", description="",
        default=False
    )
    selection: BoolProperty(name="Selection", default=True)

    @classmethod
    def poll(cls, context):
        return context.mode == "EDIT_MESH" and is_cloth_mesh_object(context.active_object)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data

        if not mesh_has_cloth_attribute(mesh, ClothAttr.PINNED):
            mesh_add_cloth_attribute(mesh, ClothAttr.PINNED)

        bm = bmesh.from_edit_mesh(mesh)

        pinned_layer = bm.verts.layers.int.get(ClothAttr.PINNED)
        pin = 1 if self.pin else 0
        for v in bm.verts:
            if not self.selection or v.select:
                v[pinned_layer] = pin

        bmesh.update_edit_mesh(mesh)

        return {"FINISHED"}
