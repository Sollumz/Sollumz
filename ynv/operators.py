import bpy
from bpy.types import (
    Context,
    Operator,
)
from .navmesh import (
    navmesh_is_valid,
    navmesh_poly_update_flags,
)
from ..tools.blenderhelper import tag_redraw


class SOLLUMZ_OT_navmesh_polys_update_flags(Operator):
    bl_idname = "sollumz.navmesh_polys_update_flags"
    bl_label = "Update Poly Flags"
    bl_description = "Update 'Small' and 'Large' flags"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(self, context):
        self.poll_message_set("Must be in Edit Mode.")
        return context.mode == "EDIT_MESH"

    def execute(self, context: Context):
        for obj in context.objects_in_mode:
            if not navmesh_is_valid(obj):
                continue

            mesh = obj.data
            poly_access = mesh.sz_navmesh_poly_access
            navmesh_poly_update_flags(mesh, poly_access.active_poly)
            for poly_idx in poly_access.selected_polys:
                navmesh_poly_update_flags(mesh, poly_idx)

            mesh.update_tag()

        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="WINDOW")
        return {"FINISHED"}
