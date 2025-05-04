import numpy as np
import bmesh
import bpy
from bpy.types import (
    Context,
    Operator,
    Attribute,
    Object,
)
from bpy.props import (
    FloatProperty,
    IntProperty,
    BoolProperty,
)
from collections import deque
from .cloth import (
    ClothAttr,
    is_cloth_mesh_object,
    mesh_add_cloth_attribute,
    mesh_has_cloth_attribute,
    mesh_get_cloth_attribute_values,
)
from .cloth_env import (
    cloth_env_find_mesh_objects,
)
from .cloth_diagnostics import (
    cloth_last_export_contexts,
)
from ..sollumz_properties import SollumType
from ..sollumz_helper import find_sollumz_parent
from .. import logger


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


class SOLLUMZ_OT_cloth_set_force_transform(Operator, ClothSetAttributeBase):
    bl_idname = "sollumz.cloth_set_force_transform"
    bl_label = "Set Cloth Force Transform"
    bl_description = (
        "Sets the force transform of the cloth at the selected vertices.\n\n"
    ) + f"{ClothAttr.FORCE_TRANSFORM.label}: {ClothAttr.FORCE_TRANSFORM.description}"

    attribute = ClothAttr.FORCE_TRANSFORM
    value: IntProperty(
        name=ClothAttr.FORCE_TRANSFORM.label, description=ClothAttr.FORCE_TRANSFORM.description,
        min=0, max=2, default=ClothAttr.FORCE_TRANSFORM.default_value,
    )


def _ensure_cloth_num_pin_radius_sets(cloth_obj: Object, set_number: int):
    # Increase the number of pin radius sets in the cloth if we are applying values to a new set
    if cloth_obj and cloth_obj.sollum_type == SollumType.CHARACTER_CLOTH_MESH:
        drawable_obj = cloth_obj.parent
        if drawable_obj and drawable_obj.sollum_type == SollumType.DRAWABLE:
            cloth_props = drawable_obj.drawable_properties.char_cloth
            if set_number > cloth_props.num_pin_radius_sets:
                cloth_props.num_pin_radius_sets = set_number


class SOLLUMZ_OT_cloth_set_pin_radius(Operator, ClothSetAttributeBase):
    bl_idname = "sollumz.cloth_set_pin_radius"
    bl_label = "Set Cloth Pin Radius"
    bl_description = (
        "Sets the soft-pinning radius of the cloth at the selected vertices.\n\n"
    ) + f"{ClothAttr.PIN_RADIUS.label}: {ClothAttr.PIN_RADIUS.description}"

    attribute = ClothAttr.PIN_RADIUS
    set_number: IntProperty(name="Pin Radius Set", min=1, max=4, default=1)
    value: FloatProperty(
        name=ClothAttr.PIN_RADIUS.label, description=ClothAttr.PIN_RADIUS.description,
        min=0.0, max=1.0, default=0.1, step=5
    )

    def execute(self, context):
        _ensure_cloth_num_pin_radius_sets(context.active_object, self.set_number)
        return super().execute(context)

    def do_set_attribute(self, vertex_index: int, attr: Attribute):
        attr.data[vertex_index].color[self.set_number - 1] = self.value


class SOLLUMZ_OT_cloth_set_pin_radius_gradient(Operator, ClothSetAttributeBase):
    bl_idname = "sollumz.cloth_set_pin_radius_gradient"
    bl_label = "Set Cloth Pin Radius Gradient"
    bl_description = (
        "Apply a gradient to the soft-pinning radius of the cloth at the selected vertices. Pinned vertices are "
        "assigned a value of 0.0. Vertices directly adjacent to pinned ones receive the minimum value, while those "
        "farthest away receive the maximum. Intermediate vertices are interpolated between the minimum and maximum "
        "based on their distance from the pinned vertices.\n\n"
    ) + f"{ClothAttr.PIN_RADIUS.label}: {ClothAttr.PIN_RADIUS.description}"

    attribute = ClothAttr.PIN_RADIUS
    set_number: IntProperty(name="Pin Radius Set", min=1, max=4, default=1)
    min_value: FloatProperty(name="Minimum", min=0.0, max=1.0, default=0.1, step=5)
    max_value: FloatProperty(name="Maximum", min=0.0, max=1.0, default=0.8, step=5)

    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self._distances = None
        self._max_distance = None

    def execute(self, context):
        obj = context.active_object
        _ensure_cloth_num_pin_radius_sets(obj, self.set_number)

        mode = obj.mode
        bpy.ops.object.mode_set(mode="OBJECT")

        mesh = obj.data
        pinned = mesh_get_cloth_attribute_values(mesh, ClothAttr.PINNED)
        pinned_vertices = np.where(pinned != 0)[0]

        # Calculate distance of each vertex to the closest pinned vertex.
        # Distance measured in number of edges, instead of euclidean distance, so the values assigned at each vertex
        # are a bit more consistent and nicer.
        # Good cloth topology should have edges of more or less the same length, so this will still give a decent gradient.
        distances = {}
        max_distance = -1
        visited = set(pinned_vertices)
        # Pinned vertices start at -1 so directly adjacent vertices have distance 0
        queue = deque((vid, -1) for vid in pinned_vertices)

        bm = bmesh.new()
        try:
            bm.from_mesh(mesh)
            bm.verts.ensure_lookup_table()

            while queue:
                vid, dist = queue.popleft()
                distances[vid] = dist
                max_distance = max(max_distance, dist)

                v = bm.verts[vid]
                for e in v.link_edges:
                    other = e.other_vert(v)
                    if other.index not in visited:
                        visited.add(other.index)
                        queue.append((other.index, dist + 1))
        finally:
            bm.free()

        self._distances = distances
        self._max_distance = max_distance

        res = super().execute(context)
        bpy.ops.object.mode_set(mode=mode)
        return res

    def do_set_attribute(self, vertex_index: int, attr: Attribute):
        d = self._distances[vertex_index]
        if d >= 0 and self._max_distance > 0:
            factor = d / self._max_distance
            pin_radius = self.min_value + (self.max_value - self.min_value) * factor
        else:
            pin_radius = 0.0
        attr.data[vertex_index].color[self.set_number - 1] = pin_radius


class SOLLUMZ_OT_cloth_refresh_diagnostics(Operator):
    bl_idname = "sollumz.cloth_refresh_diagnostics"
    bl_label = "Refresh Cloth Diagnostics"
    bl_description = (
        "Collect diagnostics on all cloths in the scene.\n\n"
        "Note, a full export of all objects with cloth is attempted, so other errors unrelated to cloth may be reported "
        "as well"
    )

    def execute(self, context: bpy.types.Context):
        with logger.use_operator_logger(self):
            # Technically we only have diagnostics to visualize for character cloth, but fragment cloth export may
            # also log some errors so also try to export them
            cloth_objs = [
                obj
                for obj in context.view_layer.objects
                if obj.sollum_type == SollumType.CHARACTER_CLOTH_MESH
            ]
            frag_cloth_objs = [
                obj
                for obj in context.view_layer.objects
                if obj.sollum_type == SollumType.FRAGMENT and cloth_env_find_mesh_objects(obj, silent=True)
            ]
            if not cloth_objs and not frag_cloth_objs:
                logger.info("No cloth objects in the scene")
                return {"CANCELLED"}

            cloth_last_export_contexts().clear()

            if cloth_objs:
                from ..ydd.yddexport import export_ydd
                for cloth_obj in cloth_objs:
                    if not (dwd_obj := find_sollumz_parent(cloth_obj, SollumType.DRAWABLE_DICTIONARY)):
                        continue
                    logger.info(f"Checking '{dwd_obj.name}'...")
                    export_ydd(dwd_obj, None)

            if frag_cloth_objs:
                from ..yft.yftexport import export_yft
                for frag_obj in frag_cloth_objs:
                    logger.info(f"Checking '{frag_obj.name}'...")
                    export_yft(frag_obj, None)

        return {"FINISHED"}
