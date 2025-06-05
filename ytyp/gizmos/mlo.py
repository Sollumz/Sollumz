import bpy
from ...sollumz_properties import ArchetypeType
from ...sollumz_preferences import get_theme_settings
from mathutils import Vector, Matrix
from ..utils import get_selected_archetype, get_selected_ytyp, get_selected_portal, get_selected_tcm
from ...tools.blenderhelper import find_parent


def can_draw_gizmos(context):
    aobj = context.active_object
    selected_archetype = get_selected_archetype(context)
    if aobj and selected_archetype:
        if not selected_archetype.asset or selected_archetype.type != ArchetypeType.MLO:
            return False
        if not selected_archetype.asset.visible_get():
            return False
        return aobj == selected_archetype.asset or find_parent(aobj, selected_archetype.asset.name)
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
        theme = get_theme_settings(context)
        selected_ytyp = get_selected_ytyp(context)
        selected_archetype = selected_ytyp.selected_archetype
        selected_room = selected_archetype.rooms.active_item
        room = self.linked_room

        self.use_draw_scale = False

        if room == selected_room:
            r, g, b, a = theme.mlo_gizmo_room_selected
        else:
            r, g, b, a = theme.mlo_gizmo_room

        self.color = r, g, b
        self.alpha = a

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
        theme = get_theme_settings(context)
        selected_archetype = get_selected_archetype(context)
        selected_portal = get_selected_portal(context)
        portal = self.linked_portal
        asset = selected_archetype.asset

        if selected_portal == portal:
            r, g, b, a = theme.mlo_gizmo_portal_selected
        else:
            r, g, b, a = theme.mlo_gizmo_portal

        self.color = r, g, b
        self.alpha = a

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
        theme = get_theme_settings(context)
        selected_archetype = get_selected_archetype(context)
        selected_portal = get_selected_portal(context)
        portal = self.linked_portal
        asset = selected_archetype.asset

        r, g, b, a = theme.mlo_gizmo_portal_direction
        self.color = r, g, b

        if selected_portal != portal:
            self.alpha = 0

        if selected_portal == portal:
            self.alpha = a

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
                scale = theme.mlo_gizmo_portal_direction_size
                arrow_mat = Matrix.LocRotScale(
                    centroid, rot, Vector((scale, scale, scale)))
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


class TimecycleModifierGizmo(bpy.types.Gizmo):
    bl_idname = "OBJECT_GT_timecycle_modifier"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.linked_tcm = None

    def draw(self, context):
        self.draw_select(context)

    def draw_select(self, context, select_id=None):
        theme = get_theme_settings(context)
        selected_archetype = get_selected_archetype(context)
        selected_tcm = get_selected_tcm(context)
        tcm = self.linked_tcm
        asset = selected_archetype.asset

        if selected_tcm == tcm:
            r, g, b, a = theme.mlo_gizmo_tcm_selected
        else:
            r, g, b, a = theme.mlo_gizmo_tcm

        self.color = r, g, b
        self.alpha = a

        self.color_highlight = self.color * 0.9
        self.alpha_highlight = self.alpha

        if tcm and asset:
            select_id = select_id if select_id is not None else -1
            t = asset.matrix_world @ Matrix.Translation(tcm.sphere_center)
            m = t @ Matrix.Scale(tcm.sphere_radius, 4)
            self.draw_preset_circle(m, axis="POS_X", select_id=select_id)
            self.draw_preset_circle(m, axis="POS_Y", select_id=select_id)
            self.draw_preset_circle(m, axis="POS_Z", select_id=select_id)
            m = t @ Matrix.Scale(tcm.range, 4)
            self.draw_preset_circle(m, axis="POS_Z", select_id=select_id)

    def invoke(self, context, event):
        selected_archetype = get_selected_archetype(context)
        tcms = list(selected_archetype.timecycle_modifiers)

        if self.linked_tcm not in tcms:
            return

        selected_archetype.timecycle_modifiers.select(tcms.index(self.linked_tcm))

        return {"PASS_THROUGH"}

    def modal(self, context, event, tweak):
        return {"PASS_THROUGH"}


class TimecycleModifierGizmoGroup(bpy.types.GizmoGroup):
    bl_idname = "OBJECT_GGT_timecycle_modifier"
    bl_label = "MLO Timecycle Modifier"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT", "SELECT"}

    @classmethod
    def poll(cls, context):
        if not context.scene.show_mlo_tcm_gizmo:
            return False

        if not can_draw_gizmos(context):
            return False

        selected_archetype = get_selected_archetype(context)

        return selected_archetype.timecycle_modifiers.active_index < len(selected_archetype.timecycle_modifiers)

    def setup(self, context):
        pass

    def refresh(self, context):
        self.gizmos.clear()
        selected_archetype = get_selected_archetype(context)

        for tcm in selected_archetype.timecycle_modifiers:
            gz = self.gizmos.new(TimecycleModifierGizmo.bl_idname)
            gz.linked_tcm = tcm
