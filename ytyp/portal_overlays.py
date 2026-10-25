import bpy
from bpy.types import SpaceView3D
import blf
from mathutils import Vector
from bpy_extras.view3d_utils import location_3d_to_region_2d
from ..sollumz_preferences import get_theme_settings
from .gizmos.mlo import can_draw_gizmos
from .utils import get_selected_archetype, get_selected_portal
from .properties.mlo import PortalProperties


_AXIS_NAMES = ("X", "Y", "Z")


def get_portal_centroid_and_normal(portal) -> tuple[Vector, Vector]:
    """Returns the centroid and normal of the portal in the archetype local space. The normal matches the direction
    drawn by the portal direction arrow gizmo.
    """
    corners = [Vector(portal.corner1), Vector(portal.corner2), Vector(portal.corner3), Vector(portal.corner4)]
    centroid = sum(corners, Vector()) / len(corners)
    normal = -(corners[2] - corners[0]).cross(corners[1] - corners[0])
    if normal.length_squared > 0.0:
        normal.normalize()
    return centroid, normal


def get_direction_label(normal: Vector) -> str:
    """Describes the normal by its dominant axis, e.g. '+Y' or '-X'."""
    if normal.length_squared == 0.0:
        return "?"
    axis = max(range(3), key=lambda i: abs(normal[i]))
    sign = "+" if normal[axis] >= 0.0 else "-"
    return f"{sign}{_AXIS_NAMES[axis]}"


def get_enabled_flag_names(portal) -> list[str]:
    flags = portal.flags
    names = []
    for i in range(1, flags.size + 1):
        prop_name = f"flag{i}"
        if getattr(flags, prop_name, False):
            names.append(flags.bl_rna.properties[prop_name].name)
    return names


def get_portal_display_name(portal, index: int) -> str:
    """Same format as ``PortalProperties.name``, but without its getter's side effects: it can write the room name
    properties, which is not allowed from inside a viewport draw callback.
    """
    if cached := PortalProperties.get_cached_name(portal.uuid):
        return cached
    room_from = portal.room_from_name or portal.get_room_name(portal.room_from_index)
    room_to = portal.room_to_name or portal.get_room_name(portal.room_to_index)
    return f"{index + 1} | {room_from} to {room_to}"


def get_portal_label_lines(portal, index: int, normal_world: Vector, show_flags: bool) -> list[str]:
    lines = [get_portal_display_name(portal, index), f"Facing {get_direction_label(normal_world)}"]
    if show_flags:
        flag_names = get_enabled_flag_names(portal)
        lines.append(", ".join(flag_names) if flag_names else "No Flags")
    return lines


class PortalOverlaysDrawHandler:
    """Draws the name, direction and flags of each MLO portal in the 3D viewport."""

    def __init__(self):
        self.handler_text = None

    def register(self):
        self.handler_text = SpaceView3D.draw_handler_add(self.draw_text, (), "WINDOW", "POST_PIXEL")

    def unregister(self):
        if self.handler_text is not None:
            SpaceView3D.draw_handler_remove(self.handler_text, "WINDOW")
            self.handler_text = None

    def can_draw_anything(self, context) -> bool:
        scene = context.scene
        if scene is None:
            return False
        if not scene.show_portal_gizmo or not scene.show_portal_labels:
            return False
        if not can_draw_gizmos(context):
            return False
        archetype = get_selected_archetype(context)
        return archetype is not None and len(archetype.portals) > 0

    def draw_text(self):
        context = bpy.context
        if not self.can_draw_anything(context):
            return

        region = context.region
        rv3d = context.region_data
        if region is None or rv3d is None:
            return

        scene = context.scene
        theme = get_theme_settings(context)
        archetype = get_selected_archetype(context)
        selected_portal = get_selected_portal(context)
        asset = archetype.asset
        matrix_world = asset.matrix_world
        rot_world = matrix_world.to_3x3()
        selected_only = scene.portal_labels_selected_only
        show_flags = scene.show_portal_label_flags

        font_id = 0
        font_size = theme.mlo_gizmo_portal_label_size
        blf.size(font_id, font_size)
        blf.enable(font_id, blf.SHADOW)
        blf.shadow(font_id, 3, 0.0, 0.0, 0.0, 1.0)
        blf.shadow_offset(font_id, 1, -1)

        try:
            for index, portal in enumerate(archetype.portals):
                is_selected = portal == selected_portal
                if selected_only and not is_selected:
                    continue

                centroid, normal = get_portal_centroid_and_normal(portal)
                pos = location_3d_to_region_2d(region, rv3d, matrix_world @ centroid)
                if pos is None:
                    continue  # behind the view

                normal_world = rot_world @ normal
                if normal_world.length_squared > 0.0:
                    normal_world.normalize()

                color = theme.mlo_gizmo_portal_label_selected if is_selected else theme.mlo_gizmo_portal_label
                blf.color(font_id, *color)

                lines = get_portal_label_lines(portal, index, normal_world, show_flags)
                line_height = blf.dimensions(font_id, "Ag")[1] * 1.5
                total_height = line_height * len(lines)
                for i, line in enumerate(lines):
                    w, _ = blf.dimensions(font_id, line)
                    x = pos.x - w * 0.5
                    y = pos.y + total_height * 0.5 - line_height * (i + 1)
                    blf.position(font_id, x, y, 0.0)
                    blf.draw(font_id, line)
        finally:
            blf.disable(font_id, blf.SHADOW)


draw_handlers = []


def register():
    handler = PortalOverlaysDrawHandler()
    handler.register()
    draw_handlers.append(handler)


def unregister():
    for handler in draw_handlers:
        handler.unregister()
    draw_handlers.clear()
