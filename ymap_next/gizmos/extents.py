import functools

from bpy.props import (
    FloatVectorProperty,
)
from bpy.types import (
    Gizmo,
    GizmoGroup,
)
from mathutils import Matrix, Vector

from ..context import active_tcm
from ..properties.map import get_maps
from ..ui.map import SOLLUMZ_PT_map_tcms


@functools.cache
def get_extents_shape(extents: tuple[float, ...]) -> object:
    x0, y0, z0, x1, y1, z1 = extents
    bbmin = Vector((x0, y0, z0))
    bbmax = Vector((x1, y1, z1))
    verts = [
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
        bbmax,
    ]

    return Gizmo.new_custom_shape("LINES", verts)


class SOLLUMZ_GT_map_extents(Gizmo):
    bl_idname = "SOLLUMZ_GT_map_extents"

    extents_min: FloatVectorProperty(name="Extents Min", default=(0, 0, 0), size=3, subtype="XYZ")
    extents_max: FloatVectorProperty(name="Extents Max", default=(0, 0, 0), size=3, subtype="XYZ")

    def draw(self, context):
        self.draw_common(context, None)

    def draw_select(self, context, select_id):
        # self.draw_common(context, select_id)
        pass

    def draw_common(self, context, select_id):
        extents = (*self.extents_min, *self.extents_max)
        self.use_draw_scale = False
        self.draw_custom_shape(get_extents_shape(extents), matrix=Matrix.Identity(4), select_id=select_id)


class SOLLUMZ_GGT_maps(GizmoGroup):
    bl_idname = "SOLLUMZ_GGT_maps"
    bl_label = "Map Widgets"
    bl_space_type = "VIEW_3D"
    bl_region_type = "WINDOW"
    bl_options = {"3D", "PERSISTENT", "SCALE", "SHOW_MODAL_ALL"}

    @classmethod
    def poll(cls, context):
        return context.space_data.overlay.show_extras and (maps := get_maps(context)) and len(maps.groups) > 0

    def setup(self, context):
        self.extents_gizmos = []

    def refresh(self, context):
        pass

    def draw_prepare(self, context):
        extents_gz_idx = 0

        # theme = context.preferences.themes[0]
        # color_default = theme.view_3d.light[0:3]
        # color_selected = theme.view_3d.object_selected
        # color_active = theme.view_3d.object_active

        if SOLLUMZ_PT_map_tcms.is_active():
            tcm = active_tcm(context)

            if tcm:
                color = (0.0, 1.0, 1.0)  # TODO(ymap_next): TCM gizmo color theme
                extents_min, extents_max = tcm.extents
                if extents_gz_idx < len(self.extents_gizmos):
                    gz = self.extents_gizmos[extents_gz_idx]
                else:
                    gz = self.gizmos.new(SOLLUMZ_GT_map_extents.bl_idname)
                    self.extents_gizmos.append(gz)
                    gz.alpha = 0.9

                gz.use_event_handle_all = False
                gz.extents_min = extents_min
                gz.extents_max = extents_max
                gz.color = color
                gz.color_highlight = color
                gz.alpha_highlight = gz.alpha

                extents_gz_idx += 1

        # Remove unused gizmos
        for i in range(extents_gz_idx, len(self.extents_gizmos)):
            self.gizmos.remove(self.extents_gizmos[i])
        del self.extents_gizmos[extents_gz_idx:]
