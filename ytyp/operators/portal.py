import bpy
import numpy
from ...sollumz_operators import SOLLUMZ_OT_base, SearchEnumHelper
from ...tools.blenderhelper import get_selected_vertices
from ..utils import get_selected_archetype, get_selected_portal, get_selected_room
from bpy_extras.view3d_utils import location_3d_to_region_2d
from ..properties.mlo import PortalProperties, get_room_items


class SOLLUMZ_OT_create_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a portal to the selected archetype"""
    bl_idname = "sollumz.createportal"
    bl_label = "Create Portal"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.new_portal()

        return True


class PortalCreatorHelper:
    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None and (context.active_object and context.active_object.mode == "EDIT")

    @staticmethod
    def sort_coords_2d_winding(coords: list[tuple[float, float, float]]):
        """Sort 4 3D points in a winding order by projecting the coords to 2D."""
        # Thank you Pranav! https://stackoverflow.com/a/70624269/11903486
        screen_coords = PortalCreatorHelper.get_screen_coords(coords)

        np_coords = numpy.array(screen_coords)
        centroid = numpy.sum(np_coords, axis=0) / np_coords.shape[0]
        vector_from_centroid = np_coords - centroid
        vector_angle = numpy.arctan2(
            vector_from_centroid[:, 1], vector_from_centroid[:, 0])
        # Find the indices that give a sorted vector_angle array
        sort_order = list(numpy.argsort(-vector_angle))

        # Apply sort_order to original pts array.
        return [coords[i] for i in sort_order]

    @staticmethod
    def get_screen_coords(coords_3d: list[tuple[float, float, float]]) -> list[tuple[float, float]]:
        """Get 2D screen coords of the provided 3d coords."""
        region = bpy.context.region
        region_3d = bpy.context.space_data.region_3d

        screen_coords = []
        for coord in coords_3d:
            # TODO: Fails here. location_3d_to_region_2d returns None because the portal coords are behind the viewport (when transformed by obj.matrix_world)
            screen_coords.append(location_3d_to_region_2d(
                region, region_3d, coord))

        return screen_coords

    @staticmethod
    def is_coplanar(points: list[tuple[float, float, float]]):
        """Check if 4 3D points lie on the same plane."""
        leg1 = points[1] - points[0]
        leg2 = points[2] - points[0]
        leg3 = points[3] - points[0]

        return leg3.dot(leg1.cross(leg2)) == 0

    def get_selected_portal_verts(self, context):
        selected_verts = []

        selected_archetype = get_selected_archetype(context)

        if selected_archetype.asset is None:
            self.message("You must set an asset for this mlo archetype.")
            return selected_verts

        for obj in context.objects_in_mode:
            selected_verts.extend(
                [vert for vert in get_selected_vertices(obj)])

        return selected_verts

    def set_portal_corners_to_selected_verts(self, context, portal: PortalProperties, offset: tuple[float, float, float]):
        """Set portal corners to selected verts in winding order."""
        selected_verts = self.get_selected_portal_verts(context)

        if len(selected_verts) != 4:
            self.message("You must select exactly 4 vertices.")
            return False

        if not PortalCreatorHelper.is_coplanar(selected_verts):
            self.warning(
                "Selection of points are not coplanar. This may cause issues with the portal.")

        sorted_verts = PortalCreatorHelper.sort_coords_2d_winding(
            selected_verts)

        portal.corner1 = sorted_verts[2] - offset
        portal.corner2 = sorted_verts[1] - offset
        portal.corner3 = sorted_verts[0] - offset
        portal.corner4 = sorted_verts[3] - offset

        return True


class SOLLUMZ_OT_create_portal_from_selection(PortalCreatorHelper, SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a portal from selected verts"""
    bl_idname = "sollumz.createportalfromselection"
    bl_label = "Create Portal From Verts"

    def run(self, context):
        selected_archetype = get_selected_archetype(context)

        portal_offset = selected_archetype.asset.location
        new_portal = selected_archetype.new_portal()

        return self.set_portal_corners_to_selected_verts(context, new_portal, portal_offset)


class SOLLUMZ_OT_update_portal_from_selection(PortalCreatorHelper, SOLLUMZ_OT_base, bpy.types.Operator):
    """Update a portal from selected verts"""
    bl_idname = "sollumz.updateportalfromselection"
    bl_label = "Update Portal From Verts"

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_portal = get_selected_portal(context)

        portal_offset = selected_archetype.asset.location

        return self.set_portal_corners_to_selected_verts(context, selected_portal, portal_offset)


class SOLLUMZ_OT_delete_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete portal from selected archetype"""
    bl_idname = "sollumz.deleteportal"
    bl_label = "Delete Portal"

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context)

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_archetype.portals.remove(selected_archetype.portal_index)
        selected_archetype.portal_index = max(
            selected_archetype.portal_index - 1, 0)
        # Force redraw of gizmos
        context.space_data.show_gizmo = context.space_data.show_gizmo
        return True

class SOLLUMZ_OT_flip_portal(bpy.types.Operator):
    """Flip portal direction"""
    bl_idname = "sollumz.flipportal"
    bl_label = "Change portal direction"

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def execute(self, context):
        selected_portal = get_selected_portal(context)
        if selected_portal is not None:
            corners = [selected_portal.corner1.copy(), selected_portal.corner2.copy(
            ), selected_portal.corner3.copy(), selected_portal.corner4.copy()]
            selected_portal.corner4 = corners[0]
            selected_portal.corner3 = corners[1]
            selected_portal.corner2 = corners[2]
            selected_portal.corner1 = corners[3]

        return {"FINISHED"}

class SetPortalRoomHelper(SOLLUMZ_OT_base):
    bl_label = "Set to Selected"
    room_from = False
    room_to = False

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def run(self, context):
        selected_room = get_selected_room(context)
        selected_portal = get_selected_portal(context)
        if selected_portal is None:
            self.message("No portal selected!")
            return False

        if selected_room is None:
            self.message("No room selected!")
            return False

        if self.room_from:
            selected_portal.room_from_id = str(selected_room.id)
        elif self.room_to:
            selected_portal.room_to_id = str(selected_room.id)
        return True


class SOLLUMZ_OT_search_portal_room_from(SearchEnumHelper, bpy.types.Operator):
    """Search for room"""
    bl_idname = "sollumz.search_portal_room_from"
    bl_property = "room_from_id"

    room_from_id: bpy.props.EnumProperty(items=get_room_items, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def get_data_block(self, context):
        return get_selected_portal(context)


class SOLLUMZ_OT_search_portal_room_to(SearchEnumHelper, bpy.types.Operator):
    """Search for room"""
    bl_idname = "sollumz.search_portal_room_to"
    bl_property = "room_to_id"

    room_to_id: bpy.props.EnumProperty(items=get_room_items, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def get_data_block(self, context):
        return get_selected_portal(context)

