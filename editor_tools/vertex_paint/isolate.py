"""Operators to isolate specific color channels of a color attribute."""

import re
from typing import NamedTuple

import numpy as np
from bpy.props import (
    BoolProperty,
    IntProperty,
)
from bpy.types import (
    Context,
    Operator,
)

from .utils import Channel, attr_domain_size

ISOLATED_ATTR_FORMAT = ".isolated_{}{}{}{}.{}"
ISOLATED_ATTR_REGEX = re.compile(r"\.isolated_(?P<R>R?)(?P<G>G?)(?P<B>B?)(?P<A>A?)\.(?P<attr>.*)")


class IsolateState(NamedTuple):
    active_attr_name: str
    """Active color attribute."""
    base_attr_name: str
    """Base color attribute for the isolated active color attribute."""
    channels: set[Channel]
    """Currently isolated channels from `base_attr_name`, stored in `active_attr_name`."""


def isolate_get_state(context: Context) -> IsolateState:
    mesh = context.active_object.data
    active_attr_name = mesh.attributes.active_color_name
    if m := ISOLATED_ATTR_REGEX.match(active_attr_name):
        base_attr_name = m.group("attr")
        channels = set()
        if m.group("R"):
            channels.add(Channel.RED)
        if m.group("G"):
            channels.add(Channel.GREEN)
        if m.group("B"):
            channels.add(Channel.BLUE)
        if m.group("A"):
            channels.add(Channel.ALPHA)
    else:
        base_attr_name = active_attr_name
        channels = set()

    return IsolateState(active_attr_name, base_attr_name, channels)


def isolate_toggle_channel(context: Context, ch: Channel, extend: bool):
    mesh = context.active_object.data

    active_attr_name, base_attr_name, old_isolated_channels = isolate_get_state(context)
    if extend and (ch != Channel.ALPHA and Channel.ALPHA not in old_isolated_channels):
        # Select multiple channels (Ctrl+click)
        new_isolated_channels = {ch} | old_isolated_channels
    else:
        # Select single channel
        new_isolated_channels = {ch}

    if ch in old_isolated_channels:
        # Deselect channel
        new_isolated_channels.remove(ch)

    base_attr = mesh.attributes[base_attr_name]
    base_attr_data = None

    domain_size = attr_domain_size(mesh, base_attr)

    if active_attr_name != base_attr_name and old_isolated_channels:
        # Update base attribute with the values in the isolated attribute
        old_isolated_attr = mesh.attributes[active_attr_name]
        old_isolated_attr_data = np.empty((domain_size, 4), dtype=np.float32)
        old_isolated_attr.data.foreach_get("color_srgb", old_isolated_attr_data.ravel())

        base_attr_data = np.empty((domain_size, 4), dtype=np.float32)
        base_attr.data.foreach_get("color_srgb", base_attr_data.ravel())

        if Channel.RED in old_isolated_channels:
            base_attr_data[:, 0] = old_isolated_attr_data[:, 0]
        if Channel.GREEN in old_isolated_channels:
            base_attr_data[:, 1] = old_isolated_attr_data[:, 1]
        if Channel.BLUE in old_isolated_channels:
            base_attr_data[:, 2] = old_isolated_attr_data[:, 2]

        if Channel.ALPHA in old_isolated_channels:
            # Alpha channel should be in grayscale so RGB channels should have the same values, so just consider R
            base_attr_data[:, 3] = old_isolated_attr_data[:, 0]

        base_attr.data.foreach_set("color_srgb", base_attr_data.ravel())

        mesh.attributes.remove(old_isolated_attr)

        # Lookup again to avoid dangling reference after removing the other attribute
        base_attr = mesh.attributes[base_attr_name]

    if not new_isolated_channels:
        # Nothing selected, go back to the base attribute
        mesh.attributes.active_color_name = base_attr_name
        return

    # Create a new isolated attribute and fill it with the values of the base attribute
    isolated_attr_name = ISOLATED_ATTR_FORMAT.format(
        "R" if Channel.RED in new_isolated_channels else "",
        "G" if Channel.GREEN in new_isolated_channels else "",
        "B" if Channel.BLUE in new_isolated_channels else "",
        "A" if Channel.ALPHA in new_isolated_channels else "",
        base_attr_name,
    )

    if existing_attr := mesh.attributes.get(isolated_attr_name, None):
        # Remove any leftover attribute (e.g. user manually changed the active attribute)
        mesh.attributes.remove(existing_attr)

        # Lookup again to avoid dangling reference after removing the other attribute
        base_attr = mesh.attributes[base_attr_name]

    isolated_attr = mesh.attributes.new(isolated_attr_name, base_attr.data_type, base_attr.domain)
    isolated_attr_data = np.zeros((domain_size, 4), dtype=np.float32)

    if base_attr_data is None:
        # Lookup again to avoid dangling reference after adding the new attribute
        base_attr = mesh.attributes[base_attr_name]

        base_attr_data = np.empty((domain_size, 4), dtype=np.float32)
        base_attr.data.foreach_get("color_srgb", base_attr_data.ravel())

    if Channel.RED in new_isolated_channels:
        isolated_attr_data[:, 0] = base_attr_data[:, 0]
    if Channel.GREEN in new_isolated_channels:
        isolated_attr_data[:, 1] = base_attr_data[:, 1]
    if Channel.BLUE in new_isolated_channels:
        isolated_attr_data[:, 2] = base_attr_data[:, 2]

    if Channel.ALPHA in new_isolated_channels:
        # Fill RGB channels with alpha values to visualize it as grayscale
        isolated_attr_data[:, :3] = base_attr_data[:, 3:4]

    isolated_attr.data.foreach_set("color_srgb", isolated_attr_data.ravel())

    mesh.attributes.active_color = isolated_attr


class SOLLUMZ_OT_vertex_paint_isolate_toggle_channel(Operator):
    bl_idname = "sollumz.vertex_paint_isolate_toggle_channel"
    bl_label = "Isolate Channel"
    bl_description = "Isolate a channel of the active color attribute"
    bl_options = {"UNDO"}

    channel: IntProperty(name="Channel", min=0, max=3, default=0)
    extend: BoolProperty(name="Extend", default=False)

    @classmethod
    def description(cls, context, properties) -> str:
        match Channel(properties.channel):
            case Channel.RED:
                return "Isolate the red channel of the active color attribute"
            case Channel.GREEN:
                return "Isolate the green channel of the active color attribute"
            case Channel.BLUE:
                return "Isolate the blue channel of the active color attribute"
            case Channel.ALPHA:
                return "Isolate the alpha channel of the active color attribute"

        return cls.bl_description

    @classmethod
    def poll(cls, context) -> bool:
        aobj = context.active_object
        return aobj and aobj.mode == "VERTEX_PAINT" and aobj.type == "MESH" and aobj.data.attributes.active_color

    def execute(self, context):
        isolate_toggle_channel(context, Channel(self.channel), self.extend)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.extend = event.ctrl
        return self.execute(context)
