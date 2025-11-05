"""Operators to help with vertex painting multiple objects at the same time."""

from collections import defaultdict

import bpy
import numpy as np
from bpy.props import (
    CollectionProperty,
    EnumProperty,
    PointerProperty,
)
from bpy.types import (
    Object,
    Operator,
    PropertyGroup,
)


class SOLLUMZ_OT_vertex_paint_multiproxy(Operator):
    bl_idname = "sollumz.vertex_paint_multiproxy"
    bl_label = "Enter Multi-Object Vertex Paint"
    bl_description = "Vertex paint across all selected objects simultaneously through a proxy object"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context) -> bool:
        aobj = context.active_object
        return (
            aobj and aobj.mode == "VERTEX_PAINT" and aobj.type == "MESH" and not aobj.sz_multiproxy_state.is_multiproxy
        )

    def execute(self, context):
        aobj = context.active_object
        objs = list(o for o in context.selected_objects if o.type == "MESH")
        if aobj not in objs:
            objs.append(aobj)

        attr_data_types = defaultdict(set)
        attr_domains = defaultdict(set)
        for obj in objs:
            for attr in obj.data.color_attributes:
                attr_data_types[attr.name].add(attr.data_type)
                attr_domains[attr.name].add(attr.domain)

        attr_on_different_domains = {name: len(domains) > 1 for name, domains in attr_domains.items()}
        if any(attr_on_different_domains.values()):
            bad_attrs = [
                name for name, on_different_domains in attr_on_different_domains.items() if on_different_domains
            ]
            bad_attrs = ", ".join(bad_attrs)
            self.report(
                {"WARNING"},
                f"Attributes found on different domains! Make sure the following attributes are on the same domain "
                f"for all selected objects: {bad_attrs}",
            )
            return {"CANCELLED"}

        attr_need_to_convert_data_type = {name: len(data_types) > 1 for name, data_types in attr_data_types.items()}
        any_attr_need_to_convert_data_type = any(attr_need_to_convert_data_type.values())

        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")

        objs_copy = [obj.copy() for obj in objs]
        for i, obj_copy in enumerate(objs_copy):
            obj_copy.data = obj_copy.data.copy()

            if any_attr_need_to_convert_data_type:
                # We have some attribute with the same name using both BYTE_COLOR and FLOAT_COLOR on different objects.
                # Need to convert BYTE_COLOR attributes to FLOAT_COLOR, so they all have the same data type and
                # bpy.ops.object.join won't split them in multiple attributes
                for attr_name in list(a.name for a in obj_copy.data.color_attributes):
                    if not attr_need_to_convert_data_type[attr_name]:
                        continue

                    attr_copy = obj_copy.data.color_attributes[attr_name]
                    if attr_copy.data_type == "FLOAT_COLOR":
                        continue

                    attr_copy_data = np.empty((len(attr_copy.data), 4), dtype=np.float32)
                    attr_copy.data.foreach_get("color_srgb", attr_copy_data.ravel())

                    attr_copy_domain = attr_copy.domain
                    obj_copy.data.color_attributes.remove(attr_copy)
                    attr_copy = obj_copy.data.color_attributes.new(attr_name, "FLOAT_COLOR", attr_copy_domain)
                    attr_copy.data.foreach_set("color_srgb", attr_copy_data.ravel())

            # This attribute indicates to which object each vertex belongs to
            ref_attr = obj_copy.data.attributes.new(".multiproxy.object_ref", "INT", "POINT")
            ref_attr_init_data = np.full(len(ref_attr.data), i)
            ref_attr.data.foreach_set("value", ref_attr_init_data)

            context.collection.objects.link(obj_copy)
            obj_copy.select_set(True)

        context.view_layer.objects.active = objs_copy[0]

        bpy.ops.object.join()
        merged_obj = context.active_object
        merged_obj.name = ".multiproxy"
        merged_obj.data.name = ".multiproxy"
        merged_obj.data.attributes.active_color_name = aobj.data.attributes.active_color_name
        proxy_state = merged_obj.sz_multiproxy_state
        proxy_state.objects.clear()

        for obj in objs:
            obj.hide_set(True)
            proxy_state.objects.add().ref = obj

        context.view_layer.objects.active = merged_obj
        merged_obj.select_set(True)
        bpy.ops.object.mode_set(mode="VERTEX_PAINT")

        return {"FINISHED"}


class SOLLUMZ_OT_vertex_paint_multiproxy_exit(Operator):
    bl_idname = "sollumz.vertex_paint_multiproxy_exit"
    bl_label = "Exit Multi-Object Vertex Paint"
    bl_description = "Apply vertex paint changes to the original objects and delete the proxy object"
    bl_options = {"UNDO"}

    missing_attributes_mode: EnumProperty(
        items=(
            (
                "ADD_MISSING",
                "Add Missing",
                "Add all attributes to the meshes that don't have them",
            ),
            (
                "SKIP_MISSING",
                "Skip Missing",
                "Skip missing attributes, only apply attributes that already exist in the meshes",
            ),
        ),
        name="Missing Attributes Mode",
        default="ADD_MISSING",
    )

    @classmethod
    def poll(cls, context) -> bool:
        aobj = context.active_object
        return aobj and aobj.mode == "VERTEX_PAINT" and aobj.type == "MESH" and aobj.sz_multiproxy_state.is_multiproxy

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)
        col.scale_y = 0.9
        col.label(text="Objects have different color attributes.")
        col.label(text="Choose how to handle missing attributes on exit:")
        layout.prop(self, "missing_attributes_mode", expand=True)
        layout.separator()

    def _execute_impl(self, context, dry_run: bool):
        proxy_obj = context.active_object
        proxy_mesh = proxy_obj.data
        proxy_state = proxy_obj.sz_multiproxy_state

        if not dry_run:
            bpy.ops.object.mode_set(mode="OBJECT")
            bpy.ops.object.select_all(action="DESELECT")

        vertex_to_object_index_map = np.empty(len(proxy_mesh.vertices), dtype=np.int32)
        vertex_to_object_index_attr = proxy_mesh.attributes[".multiproxy.object_ref"]
        vertex_to_object_index_attr.data.foreach_get("value", vertex_to_object_index_map)

        loop_vertex_index = np.empty(len(proxy_mesh.loops), dtype=np.int32)
        proxy_mesh.loops.foreach_get("vertex_index", loop_vertex_index)
        loop_to_object_index_map = vertex_to_object_index_map[loop_vertex_index]

        proxy_color_data_per_attr = {}
        for proxy_color_attr in proxy_mesh.color_attributes:
            proxy_color_data = np.empty((len(proxy_color_attr.data), 4), dtype=np.float32)
            proxy_color_attr.data.foreach_get("color_srgb", proxy_color_data.ravel())
            proxy_color_data_per_attr[proxy_color_attr.name] = proxy_color_data

        objs_orig = [
            (i, o.ref)
            for i, o in enumerate(proxy_state.objects)
            if o.ref is not None  # Skip if original object got deleted
        ]

        # Transfer color data from proxy to original objects
        for color_attr_name, proxy_color_data in proxy_color_data_per_attr.items():
            for obj_idx, obj_orig in objs_orig:
                mesh_orig = obj_orig.data
                color_attr = mesh_orig.color_attributes.get(color_attr_name, None)
                if color_attr is None:
                    if dry_run:
                        # Show dialog asking how to handle missing attributes
                        return context.window_manager.invoke_props_dialog(self)

                    match self.missing_attributes_mode:
                        case "ADD_MISSING":
                            proxy_color_attr = proxy_mesh.color_attributes[color_attr_name]
                            color_attr = mesh_orig.color_attributes.new(
                                color_attr_name, proxy_color_attr.data_type, proxy_color_attr.domain
                            )
                            del proxy_color_attr
                        case "SKIP_MISSING":
                            continue

                if not dry_run:
                    match color_attr.domain:
                        case "CORNER":
                            loops_belonging_to_this_object_mask = loop_to_object_index_map == obj_idx
                            color_data_for_this_object = proxy_color_data[loops_belonging_to_this_object_mask]
                        case "POINT":
                            vertices_belonging_to_this_object_mask = vertex_to_object_index_map == obj_idx
                            color_data_for_this_object = proxy_color_data[vertices_belonging_to_this_object_mask]

                    assert len(color_data_for_this_object) == len(color_attr.data)
                    color_attr.data.foreach_set("color_srgb", color_data_for_this_object.ravel())

        if not dry_run:
            for _, obj_orig in objs_orig:
                obj_orig.data.update_tag()
                obj_orig.hide_set(False)

            bpy.data.objects.remove(proxy_obj)

            if objs_orig:
                # TODO: make the active object the same as what was originally active
                context.view_layer.objects.active = objs_orig[0][1]
                bpy.ops.object.mode_set(mode="VERTEX_PAINT")

        return {"FINISHED"}

    def execute(self, context):
        return self._execute_impl(context, dry_run=False)

    def invoke(self, context, event):
        ret = self._execute_impl(context, dry_run=True)
        if ret == {"FINISHED"}:
            return self._execute_impl(context, dry_run=False)
        return ret


class MultiproxyObjectRef(PropertyGroup):
    ref: PointerProperty(type=Object)


class MultiproxyState(PropertyGroup):
    objects: CollectionProperty(type=MultiproxyObjectRef)

    @property
    def is_multiproxy(self) -> bool:
        return bool(self.objects)


def register():
    Object.sz_multiproxy_state = PointerProperty(type=MultiproxyState)


def unregister():
    del Object.sz_multiproxy_state
