import bpy
from ...sollumz_operators import SOLLUMZ_OT_base
from ...tools.blenderhelper import get_selected_vertices
from ...tools.utils import sort_points, is_coplanar
from ..utils import get_selected_archetype, get_selected_portal, get_selected_room
from bpy_extras.view3d_utils import location_3d_to_region_2d


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


class SOLLUMZ_OT_create_portal_from_selection(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create a portal from selected verts"""
    bl_idname = "sollumz.createportalfromselection"
    bl_label = "Create Portal From Verts"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None and (context.active_object and context.active_object.mode == "EDIT")

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_verts = []

        if context.active_object.mode != "EDIT":
            self.message(
                "Must be in edit mode and have a selection of 4 vertices.")
            return False

        for obj in context.objects_in_mode:
            selected_verts.extend(get_selected_vertices(obj))

        if len(selected_verts) != 4:
            self.message("You must select exactly 4 vertices.")
            return False

        if not is_coplanar(selected_verts):
            self.warning(
                "Selection of points are not coplanar. This may cause issues with the portal.")

        if not selected_archetype.asset:
            self.message("You must select an asset.")
            return False

        # Get 2D screen coords of selected vertices
        region = bpy.context.region
        region_3d = bpy.context.space_data.region_3d

        corners2d = []
        for corner in selected_verts:
            corners2d.append(location_3d_to_region_2d(
                region, region_3d, corner))

        # Sort the 2d points in a winding order
        sort_order = sort_points(corners2d)
        sorted_corners = [selected_verts[i] for i in sort_order]

        pos = selected_archetype.asset.location
        new_portal = selected_archetype.new_portal()
        new_portal.corner1 = sorted_corners[2] - pos
        new_portal.corner2 = sorted_corners[1] - pos
        new_portal.corner3 = sorted_corners[0] - pos
        new_portal.corner4 = sorted_corners[3] - pos

        return True


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
            selected_portal.room_from_id = selected_room.id
        elif self.room_to:
            selected_portal.room_to_id = selected_room.id
        return True


class SOLLUMZ_OT_set_portal_room_from(SetPortalRoomHelper, bpy.types.Operator):
    """Set 'room from' to selected room"""
    bl_idname = "sollumz.setportalroomfrom"
    room_from = True


class SOLLUMZ_OT_set_portal_room_to(SetPortalRoomHelper, bpy.types.Operator):
    """Set 'room to' to selected room"""
    bl_idname = "sollumz.setportalroomto"
    room_to = True
