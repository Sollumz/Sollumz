import bpy
from ...sollumz_properties import ArchetypeType
from mathutils import Vector, Matrix
from ..utils import get_selected_archetype, get_selected_ytyp, get_selected_portal
from ...tools.blenderhelper import find_parent


def can_draw_gizmos(context):
    aobj = context.active_object
    selected_archetype = get_selected_archetype(context)
    if aobj and selected_archetype:
        if not selected_archetype.asset or selected_archetype.type != ArchetypeType.MLO:
            return False
        if not selected_archetype.asset.visible_get():
            return False
        return aobj == selected_archetype.asset or find_parent(
            aobj, selected_archetype.asset.name)
    return False


class RoomGizmo(bpy.types.Gizmo):
    bl_idname = "OBJECT_GT_room"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.linked_room = None

    @staticmethod
    def get_verts(bbmin, bbmax):
        return [
            bbmin,
            Vector((bbmin.x, bbmin.y, bbmax.z)),

            bbmin,
            Vector((bbmax.x, bbmin.y, bbmin.z)),

            bbmin,
            Vector((bbmin.x, bbmax.y, bbmin.z)),

            Vector((bbmax.x, bbmin.y, bbmax.z)),
            Vector((bbmax.x, bbmin.y, bbmin.z)),

            Vector((bbmin.x, bbmin.y, bbmax.z)),
            Vector((bbmin.x, bbmax.y, bbmax.z)),

            Vector((bbmin.x, bbmax.y, bbmin.z)),
            Vector((bbmin.x, bbmax.y, bbmax.z)),

            Vector((bbmax.x, bbmin.y, bbmax.z)),
            Vector((bbmax.x, bbmin.y, bbmax.z)),

            Vector((bbmax.x, bbmin.y, bbmax.z)),
            Vector((bbmin.x, bbmin.y, bbmax.z)),

            Vector((bbmax.x, bbmin.y, bbmin.z)),
            Vector((bbmax.x, bbmax.y, bbmin.z)),

            Vector((bbmin.x, bbmax.y, bbmin.z)),
            Vector((bbmax.x, bbmax.y, bbmin.z)),

            Vector((bbmax.x, bbmin.y, bbmax.z)),
            bbmax,

            Vector((bbmin.x, bbmax.y, bbmax.z)),
            bbmax,

            Vector((bbmax.x, bbmax.y, bbmin.z)),
            bbmax
        ]

    def draw(self, context):
        selected_ytyp = get_selected_ytyp(context)
        selected_archetype = selected_ytyp.selected_archetype
        selected_room = selected_archetype.rooms.active_item
        room = self.linked_room

        self.color = 0.31, 0.38, 1
        self.alpha = 0.7
        self.use_draw_scale = False

        if room == selected_room:
            self.color = self.color * 2
            self.alpha = 0.9

        asset = selected_archetype.asset
        if asset and room:
            self.custom_shape = self.new_custom_shape(
                "LINES", RoomGizmo.get_verts(room.bb_min, room.bb_max))
            self.draw_custom_shape(
                self.custom_shape, matrix=asset.matrix_world)


class RoomGizmoGroup(bpy.types.GizmoGroup):
    bl_idname = "OBJECT_GGT_Room"
    bl_label = "MLO Room"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT"}

    @classmethod
    def poll(cls, context):
        if not context.scene.show_room_gizmo:
            return False
        if can_draw_gizmos(context):
            selected_ytyp = get_selected_ytyp(context)
            selected_archetype = selected_ytyp.selected_archetype
            return selected_archetype.rooms.active_index < len(selected_archetype.rooms)
        return False

    def setup(self, context):
        pass

    def draw_prepare(self, context):
        selected_ytyp = get_selected_ytyp(context)
        selected_archetype = selected_ytyp.selected_archetype
        self.gizmos.clear()
        for room in selected_archetype.rooms:
            gz = self.gizmos.new(RoomGizmo.bl_idname)
            gz.linked_room = room


class PortalGizmo(bpy.types.Gizmo):
    bl_idname = "OBJECT_GT_portal"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.linked_portal = None

    @staticmethod
    def get_verts(corners):
        return [
            corners[0],
            corners[1],
            corners[3],

            corners[2],
            corners[3],
            corners[1],
        ]

    def draw(self, context):
        self.draw_select(context)

    def draw_select(self, context, select_id=None):
        selected_archetype = get_selected_archetype(context)
        selected_portal = get_selected_portal(context)
        portal = self.linked_portal
        asset = selected_archetype.asset

        self.color = 0.45, 0.98, 0.55
        self.alpha = 0.5

        if selected_portal == portal:
            self.color = self.color * 1.5
            self.alpha = 0.7

        self.color_highlight = self.color * 0.9
        self.alpha_highlight = self.alpha

        if portal and asset:
            corners = [portal.corner1, portal.corner2,
                       portal.corner3, portal.corner4]

            self.portal_poly = self.new_custom_shape(
                "TRIS", PortalGizmo.get_verts(corners))

            self.draw_custom_shape(
                self.portal_poly, matrix=asset.matrix_world, select_id=select_id)

    def invoke(self, context, event):
        selected_archetype = get_selected_archetype(context)
        portals = list(selected_archetype.portals)

        if self.linked_portal not in portals:
            return

        selected_archetype.portals.select(portals.index(self.linked_portal))

        return {'PASS_THROUGH'}

    def modal(self, context, event, tweak):
        return {'PASS_THROUGH'}


class PortalNormalGizmo(bpy.types.Gizmo):
    bl_idname = "OBJECT_GT_portal_normal"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.linked_portal = None

    def draw(self, context):
        selected_archetype = get_selected_archetype(context)
        selected_portal = get_selected_portal(context)
        portal = self.linked_portal
        asset = selected_archetype.asset

        self.color = 0, 0.6, 1

        if selected_portal != portal:
            self.alpha = 0

        if selected_portal == portal:
            self.alpha = 0.3

            if portal and asset:
                corners = [portal.corner1, portal.corner2,
                           portal.corner3, portal.corner4]
                x = [p[0] for p in corners]
                y = [p[1] for p in corners]
                z = [p[2] for p in corners]
                centroid = Vector(
                    (sum(x) / len(corners), sum(y) / len(corners), sum(z) / len(corners)))
                normal = -(corners[2] - corners[0]
                           ).cross(corners[1] - corners[0]).normalized()
                default_axis = Vector((0, 0, 1))
                rot = default_axis.rotation_difference(normal)
                arrow_mat = Matrix.LocRotScale(
                    centroid, rot, Vector((0.3, 0.3, 0.3)))
                self.draw_preset_arrow(
                    matrix=asset.matrix_world @ arrow_mat)


class PortalGizmoGroup(bpy.types.GizmoGroup):
    bl_idname = "OBJECT_GGT_Portal"
    bl_label = "MLO Portal"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT", "SELECT"}

    @classmethod
    def poll(cls, context):
        if not context.scene.show_portal_gizmo:
            return False

        if not can_draw_gizmos(context):
            return False

        selected_archetype = get_selected_archetype(context)

        return selected_archetype.portals.active_index < len(selected_archetype.portals)

    def setup(self, context):
        pass

    def refresh(self, context):
        self.gizmos.clear()
        selected_archetype = get_selected_archetype(context)

        for portal in selected_archetype.portals:
            ngz = self.gizmos.new(PortalNormalGizmo.bl_idname)
            ngz.linked_portal = portal
            gz = self.gizmos.new(PortalGizmo.bl_idname)
            gz.linked_portal = portal
