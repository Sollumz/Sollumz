import bpy
from bpy.types import (
    Context,
    Operator,
)
from bpy.props import (
    BoolProperty,
)
import bmesh
from .navmesh import (
    navmesh_is_valid,
    navmesh_poly_update_flags,
)
from .navmesh_attributes import (
    NavPolyAttributes,
    mesh_get_navmesh_poly_attributes,
    mesh_iter_navmesh_all_poly_attributes,
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


class SOLLUMZ_OT_navmesh_polys_select_similar(Operator):
    bl_idname = "sollumz.navmesh_polys_select_similar"
    bl_label = "Select Similar Polygons"
    bl_description = "Select polygons with same attributes as the active polygon"
    bl_options = {"REGISTER", "UNDO"}

    use_is_small: BoolProperty(name="Small", default=False)
    use_is_large: BoolProperty(name="Large", default=False)
    use_is_pavement: BoolProperty(name="Pavement", default=True)
    use_is_road: BoolProperty(name="Road", default=True)
    use_is_near_car_node: BoolProperty(name="Near Car Node", default=True)
    use_is_train_track: BoolProperty(name="Train Track", default=True)
    use_is_in_shelter: BoolProperty(name="In Shelter", default=True)
    use_is_interior: BoolProperty(name="Interior", default=True)
    use_is_too_steep_to_walk_on: BoolProperty(name="Too Steep To Walk On", default=True)
    use_is_water: BoolProperty(name="Water", default=True)
    use_is_shallow_water: BoolProperty(name="Shallow Water", default=True)
    use_is_network_spawn_candidate: BoolProperty(name="Network Spawn Candidate", default=True)
    use_is_isolated: BoolProperty(name="Isolated", default=True)
    use_lies_along_edge: BoolProperty(name="Lies Along Edge", default=True)
    use_is_dlc_stitch: BoolProperty(name="DLC Stitch", default=True)
    use_audio_reverb_size: BoolProperty(name="Audio Reverb Size", default=True)
    use_audio_reverb_wet: BoolProperty(name="Audio Reverb Wet", default=True)
    use_ped_density: BoolProperty(name="Ped Density", default=True)
    use_cover_directions: BoolProperty(name="Cover Directions", default=True)

    @classmethod
    def poll(self, context):
        self.poll_message_set("Must be in Edit Mode.")
        return context.mode == "EDIT_MESH" and navmesh_is_valid(context.active_object)

    def execute(self, context: Context):
        aobj = context.active_object
        target_poly_attrs = aobj.data.sz_navmesh_poly_access.active_poly_attributes
        fields_to_consider = self._get_fields_to_consider()

        for obj in context.objects_in_mode:
            if not navmesh_is_valid(obj):
                continue

            mesh = obj.data
            if mesh.is_editmode:
                bm = bmesh.from_edit_mesh(mesh)
                try:
                    bm.faces.ensure_lookup_table()
                    for poly_idx, poly_attrs in enumerate(mesh_iter_navmesh_all_poly_attributes(mesh)):
                        if self._is_similar(poly_attrs, target_poly_attrs, fields_to_consider):
                            bm.faces[poly_idx].select = True
                finally:
                    bm.free()
            else:
                polys = mesh.polygons
                for poly_idx, poly_attrs in enumerate(mesh_iter_navmesh_all_poly_attributes(mesh)):
                    if self._is_similar(poly_attrs, target_poly_attrs, fields_to_consider):
                        polys[poly_idx].select = True

            mesh.update_tag()

        tag_redraw(bpy.context, space_type="VIEW_3D", region_type="WINDOW")
        return {"FINISHED"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False
        col = layout.column(heading="Consider", align=True)
        for f in self.__annotations__.keys():
            col.prop(self, f)

    def _is_similar(self, a: NavPolyAttributes, b: NavPolyAttributes, fields: list[str]):
        for field in fields:
            if getattr(a, field) != getattr(b, field):
                return False

        return True

    def _get_fields_to_consider(self) -> list[str]:
        return [f[4:] for f in self.__annotations__.keys() if f.startswith("use_") and getattr(self, f)]
