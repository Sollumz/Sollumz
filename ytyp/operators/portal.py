import bpy
import numpy
from mathutils import Vector, Matrix
from ...sollumz_operators import SOLLUMZ_OT_base, SearchEnumHelper
from ...tools.blenderhelper import get_selected_vertices, get_selected_edit_vertices
from ..utils import get_selected_archetype, get_selected_portal, get_selected_room, validate_dynamic_enums, validate_dynamic_enum
from bpy_extras.view3d_utils import location_3d_to_region_2d
from ..properties.mlo import PortalProperties, get_room_items_for_selected_archetype


class SOLLUMZ_OT_create_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a portal to the selected archetype"""
    bl_idname = "sollumz.createportal"
    bl_label = "Create Portal"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        portal = selected_archetype.new_portal()

        portal.room_from_id = context.scene.sollumz_add_portal_room_from
        portal.room_to_id = context.scene.sollumz_add_portal_room_to

        return True


class PortalCreatorHelper:
    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None and (context.active_object and context.active_object.mode == "EDIT")

    def execute(self, context: bpy.types.Context):
        selected_archetype = get_selected_archetype(context)

        if selected_archetype.asset is not None:
            matrix = selected_archetype.asset.matrix_world
        else:
            matrix = Matrix()

        portal = self.get_portal(context)

        self.set_portal_corners_to_selected_verts(context, portal, matrix)

        # Force gizmo redraw
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.mode_set(mode="EDIT")

        return {"FINISHED"}

    def get_portal(self, context) -> PortalProperties:
        ...

    def get_selected_portal_verts(self, context: bpy.types.Context):
        selected_verts = []

        for obj in context.objects_in_mode:
            selected_verts.extend(
                [obj.matrix_world @ v for v in get_selected_edit_vertices(obj.data)])

        return selected_verts

    def set_portal_corners_to_selected_verts(self, context: bpy.types.Context, portal: PortalProperties, composite_matrix: Matrix):
        """Set portal corners to selected verts in winding order."""
        selected_verts = self.get_selected_portal_verts(context)

        if len(selected_verts) != 4:
            self.report({"INFO"}, "You must select exactly 4 vertices.")
            return False

        sort_order = PortalCreatorHelper.sort_coords_2d_winding(selected_verts)

        # Unapply the Bound Composite matrix since that is applied to the Gizmo
        sorted_verts = [composite_matrix.inverted() @ selected_verts[i]
                        for i in sort_order]

        portal.corner1 = sorted_verts[2]
        portal.corner2 = sorted_verts[1]
        portal.corner3 = sorted_verts[0]
        portal.corner4 = sorted_verts[3]

    @staticmethod
    def sort_coords_2d_winding(coords: list[tuple[float, float, float]]):
        """Sort 4 3D points in a winding order by projecting the coords to 2D. Returns sort order"""
        # Thank you Pranav! https://stackoverflow.com/a/70624269/11903486
        screen_coords = PortalCreatorHelper.get_screen_coords(coords)

        np_coords = numpy.array(screen_coords)
        centroid = numpy.sum(np_coords, axis=0) / np_coords.shape[0]
        vector_from_centroid = np_coords - centroid
        vector_angle = numpy.arctan2(
            vector_from_centroid[:, 1], vector_from_centroid[:, 0])
        # Find the indices that give a sorted vector_angle array
        return list(numpy.argsort(-vector_angle))

    @staticmethod
    def get_screen_coords(coords_3d: list[tuple[float, float, float]]) -> list[tuple[float, float]]:
        """Get 2D screen coords of the provided 3d coords."""
        region = bpy.context.region
        region_3d = bpy.context.space_data.region_3d

        screen_coords = []
        for coord in coords_3d:
            screen_coords.append(
                location_3d_to_region_2d(region, region_3d, coord))

        return screen_coords


class SOLLUMZ_OT_create_portal_from_selection(PortalCreatorHelper, bpy.types.Operator):
    """Create a portal from selected verts"""
    bl_idname = "sollumz.createportalfromselection"
    bl_label = "Create Portal From Verts"
    bl_options = {"REGISTER", "UNDO"}

    def get_portal(self, context):
        selected_archetype = get_selected_archetype(context)
        new_portal = selected_archetype.new_portal()

        new_portal.room_from_id = context.scene.sollumz_add_portal_room_from
        new_portal.room_to_id = context.scene.sollumz_add_portal_room_to

        return new_portal


class SOLLUMZ_OT_update_portal_from_selection(PortalCreatorHelper, bpy.types.Operator):
    """Update a portal from selected verts"""
    bl_idname = "sollumz.updateportalfromselection"
    bl_label = "Update Portal From Verts"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        return (
            super().poll(context) and
            get_selected_portal(context) is not None and
            not get_selected_archetype(context).portals.has_multiple_selection
        )

    def get_portal(self, context):
        return get_selected_portal(context)


class SOLLUMZ_OT_delete_portal(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete selected portal(s)"""
    bl_idname = "sollumz.deleteportal"
    bl_label = "Delete Portal"

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context)

    def run(self, context):
        selected_archetype = get_selected_archetype(context)

        indices_to_remove = selected_archetype.portals.selected_items_indices
        indices_to_remove.sort(reverse=True)
        new_active_index = max(indices_to_remove[-1] - 1, 0) if indices_to_remove else 0
        for index_to_remove in indices_to_remove:
            selected_archetype.portals.remove(index_to_remove)
        selected_archetype.portals.select(new_active_index)

        # Force redraw of gizmos
        context.space_data.show_gizmo = context.space_data.show_gizmo

        validate_dynamic_enums(selected_archetype.entities, "attached_portal_id", selected_archetype.portals)
        validate_dynamic_enum(context.scene, "sollumz_add_entity_portal", selected_archetype.portals)
        validate_dynamic_enum(context.scene, "sollumz_entity_filter_portal", selected_archetype.portals)

        return True


class SOLLUMZ_OT_flip_portal(bpy.types.Operator):
    """Flip portal direction"""
    bl_idname = "sollumz.flipportal"
    bl_label = "Change portal direction"

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def execute(self, context):
        selected_archetype = get_selected_archetype(context)
        for selected_portal in selected_archetype.portals.iter_selected_items():
            corners = [
                selected_portal.corner1.copy(), selected_portal.corner2.copy(),
                selected_portal.corner3.copy(), selected_portal.corner4.copy()
            ]
            selected_portal.corner4 = corners[0]
            selected_portal.corner3 = corners[1]
            selected_portal.corner2 = corners[2]
            selected_portal.corner1 = corners[3]

        return {"FINISHED"}


class SOLLUMZ_OT_search_portal_room_from(SearchEnumHelper, bpy.types.Operator):
    """Search for room"""
    bl_idname = "sollumz.search_portal_room_from"
    bl_property = "room_from_id"

    room_from_id: bpy.props.EnumProperty(items=get_room_items_for_selected_archetype, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def get_data_block(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.portals.selection


class SOLLUMZ_OT_search_portal_room_to(SearchEnumHelper, bpy.types.Operator):
    """Search for room"""
    bl_idname = "sollumz.search_portal_room_to"
    bl_property = "room_to_id"

    room_to_id: bpy.props.EnumProperty(items=get_room_items_for_selected_archetype, default=-1)

    @classmethod
    def poll(cls, context):
        return get_selected_portal(context) is not None

    def get_data_block(self, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype.portals.selection
