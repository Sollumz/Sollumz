"""Operators to transfer color channels between color attributes."""

import numpy as np
from bpy.props import (
    EnumProperty,
    StringProperty,
)
from bpy.types import (
    Operator,
)

from .utils import Channel, ChannelWithNoneEnumItems, attr_domain_size


class SOLLUMZ_OT_vertex_paint_transfer_channels(Operator):
    bl_idname = "sollumz.vertex_paint_transfer_channels"
    bl_label = "Transfer Channels"
    bl_description = "Transfer channels between color attributes"
    bl_options = {"UNDO"}

    src_attribute: StringProperty(name="Source Attribute")
    dst_attribute: StringProperty(name="Destination Attribute")
    src_for_dst_r: EnumProperty(
        items=ChannelWithNoneEnumItems, name="Source Channel for Destination Red Channel", default=-1
    )
    src_for_dst_g: EnumProperty(
        items=ChannelWithNoneEnumItems, name="Source Channel for Destination Green Channel", default=-1
    )
    src_for_dst_b: EnumProperty(
        items=ChannelWithNoneEnumItems, name="Source Channel for Destination Blue Channel", default=-1
    )
    src_for_dst_a: EnumProperty(
        items=ChannelWithNoneEnumItems, name="Source Channel for Destination Alpha Channel", default=-1
    )

    @classmethod
    def poll(cls, context) -> bool:
        aobj = context.active_object
        return aobj and aobj.mode == "VERTEX_PAINT" and aobj.type == "MESH"

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        src_attr = mesh.color_attributes.get(self.src_attribute, None)
        dst_attr = mesh.color_attributes.get(self.dst_attribute, None)

        if src_attr is None or dst_attr is None:
            self.report({"INFO"}, "Source and/or destination attributes do not exist.")
            return {"CANCELLED"}

        src_domain_size = attr_domain_size(mesh, src_attr)
        dst_domain_size = attr_domain_size(mesh, dst_attr)
        src_data = np.empty((src_domain_size, 4), dtype=np.float32)
        dst_data = np.empty((dst_domain_size, 4), dtype=np.float32)
        src_attr.data.foreach_get("color_srgb", src_data.ravel())
        dst_attr.data.foreach_get("color_srgb", dst_data.ravel())

        if src_attr.domain == "POINT" and dst_attr.domain == "CORNER":
            # Vertex to face corner
            loop_vertex_index = np.empty(len(mesh.loops), dtype=np.int32)
            mesh.loops.foreach_get("vertex_index", loop_vertex_index)

            # Convert vertex domain to face corner domain
            src_data = src_data[loop_vertex_index]

        elif src_attr.domain == "CORNER" and dst_attr.domain == "POINT":
            # Face corner to vertex
            loop_vertex_index = np.empty(len(mesh.loops), dtype=np.int32)
            mesh.loops.foreach_get("vertex_index", loop_vertex_index)

            # Calculate average of all face corners for each vertex
            src_avg_data = np.zeros_like(dst_data)
            np.add.at(src_avg_data, loop_vertex_index, src_data)

            unique_vertex_index, count_vertex_index = np.unique(loop_vertex_index, return_counts=True)
            src_avg_data[unique_vertex_index] /= count_vertex_index[:, np.newaxis]

            src_data = src_avg_data

        else:
            # Same domain (vertex to vertex or face corner to face corner)
            assert src_domain_size == dst_domain_size

        # Get channels that need to be transferred
        channels = [
            (Channel(dst_ch_idx), Channel[src_ch])
            for dst_ch_idx, src_ch in enumerate(
                (self.src_for_dst_r, self.src_for_dst_g, self.src_for_dst_b, self.src_for_dst_a)
            )
            if src_ch != "NONE"
        ]

        # Copy channel data
        for dst_ch, src_ch in channels:
            dst_data[:, dst_ch.value] = src_data[:, src_ch.value]

        dst_attr.data.foreach_set("color_srgb", dst_data.ravel())

        mesh.update_tag()
        return {"FINISHED"}
