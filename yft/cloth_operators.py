import bpy
from bpy.types import (
    Context,
    Operator,
    Attribute,
)
from bpy.props import (
    FloatProperty,
    BoolProperty,
)
from .cloth import (
    ClothAttr,
    is_cloth_mesh_object,
    mesh_add_cloth_attribute,
    mesh_has_cloth_attribute,
)


class ClothEditRestrictedHelper:
    @classmethod
    def poll(cls, context: Context):
        cls.poll_message_set("Must be in Edit mode with a cloth drawable model.")
        obj = context.active_object
        return obj is not None and obj.mode == "EDIT" and is_cloth_mesh_object(obj)


class ClothRestrictedHelper:
    @classmethod
    def poll(cls, context: Context):
        cls.poll_message_set("Must have a cloth drawable model selected.")
        objs = context.selected_objects
        return any(is_cloth_mesh_object(obj) for obj in objs)


class ClothSetAttributeBase(ClothEditRestrictedHelper):
    bl_options = {"REGISTER", "UNDO"}

    attribute: ClothAttr

    def execute(self, context):
        obj = context.active_object

        mode = obj.mode
        # we need to switch from Edit mode to Object mode so the selection gets updated
        bpy.ops.object.mode_set(mode="OBJECT")

        mesh = obj.data
        if not mesh_has_cloth_attribute(mesh, self.attribute):
            mesh_add_cloth_attribute(mesh, self.attribute)

        attr = mesh.attributes[self.attribute]
        for v in mesh.vertices:
            if not v.select:
                continue

            self.do_set_attribute(v.index, attr)

        bpy.ops.object.mode_set(mode=mode)
        return {"FINISHED"}

    def do_set_attribute(self, vertex_index: int, attr: Attribute):
        attr.data[vertex_index].value = self.value


class SOLLUMZ_OT_cloth_set_vertex_weight(Operator, ClothSetAttributeBase):
    bl_idname = "sollumz.cloth_set_vertex_weight"
    bl_label = "Set Cloth Vertex Weight"
    bl_description = (
        "Sets the weight of the cloth at the selected vertices.\n\n"
    ) + f"{ClothAttr.VERTEX_WEIGHT.label}: {ClothAttr.VERTEX_WEIGHT.description}"

    attribute = ClothAttr.VERTEX_WEIGHT
    value: FloatProperty(
        name=ClothAttr.VERTEX_WEIGHT.label, description=ClothAttr.VERTEX_WEIGHT.description,
        min=0.00001, max=1.0, default=ClothAttr.VERTEX_WEIGHT.default_value,
        precision=6, step=1
    )


class SOLLUMZ_OT_cloth_set_inflation_scale(Operator, ClothSetAttributeBase):
    bl_idname = "sollumz.cloth_set_inflation_scale"
    bl_label = "Set Cloth Inflation Scale"
    bl_description = (
        "Sets the inflation scale of the cloth at the selected vertices.\n\n"
    ) + f"{ClothAttr.INFLATION_SCALE.label}: {ClothAttr.INFLATION_SCALE.description}"

    attribute = ClothAttr.INFLATION_SCALE
    value: FloatProperty(
        name=ClothAttr.INFLATION_SCALE.label, description=ClothAttr.INFLATION_SCALE.description,
        min=0.0, max=1.0, default=ClothAttr.INFLATION_SCALE.default_value
    )


class SOLLUMZ_OT_cloth_set_pinned(Operator, ClothSetAttributeBase):
    bl_idname = "sollumz.cloth_set_pinned"
    bl_label = "Pin Cloth Vertices"
    bl_description = (
        "Pins or unpins the selected cloth vertices.\n\n"
    ) + f"{ClothAttr.PINNED.label}: {ClothAttr.PINNED.description}"

    attribute = ClothAttr.PINNED
    value: BoolProperty(
        name="Pin", description=ClothAttr.PINNED.description,
        default=ClothAttr.PINNED.default_value
    )
