"""UI panels for navmesh editing.

* **N-panel "NavMesh Polygon Flags"** — main flag editor under the
  "Sollumz Tools" category. Active in Edit Mode (where polygon selection
  is meaningful); disabled with a hint in Object Mode.
* **N-panel "NavMesh"** — root metadata + export button (shown for the
  NAVMESH parent object).

Navmesh material info is drawn inline inside the Sollumz material panel
(see ``sollumz_ui.SOLLUMZ_PT_MAT_PANEL``), not as its own sub-panel.
"""
import bpy
from bpy.types import Panel

from ..sollumz_properties import SollumType
from .navmesh_attributes import (
    FLAG0_BITS,
    FLAG1_BITS,
    FLAG2_BITS,
    FLAG3_BITS,
    NavMeshAttr,
)


def _active_navmesh_polymesh(context):
    obj = context.active_object
    if obj is None:
        return None
    if obj.sollum_type == SollumType.NAVMESH_POLY_MESH and obj.type == "MESH":
        return obj
    return None


def _bm_selected_count(mesh):
    """Cheap selected-face count for an Edit Mode mesh."""
    import bmesh
    bm = bmesh.from_edit_mesh(mesh)
    return sum(1 for f in bm.faces if f.select), bm


def _draw_flag_group(layout, context, attr, bits):
    """2-column checkbox grid for one flag byte + a 'select matching' button."""
    obj = _active_navmesh_polymesh(context)
    if obj is None:
        return
    mesh = obj.data
    enabled = mesh.is_editmode
    sel_count, bm = _bm_selected_count(mesh) if enabled else (0, None)

    layer = None
    if bm is not None:
        try:
            layer = bm.faces.layers.int[attr.value]
        except KeyError:
            layout.label(text="(attribute missing)", icon="ERROR")
            return

    grid = layout.grid_flow(columns=2, even_columns=True, align=True)
    grid.enabled = enabled and sel_count > 0

    for bit_idx, bit_label in bits:
        mask = 1 << bit_idx
        if layer is not None and sel_count:
            count_on = sum(1 for f in bm.faces if f.select and f[layer] & mask)
            all_on = count_on == sel_count
        else:
            all_on = False
        op = grid.operator("sollumz.navmesh_set_poly_flag_bit",
                           text=bit_label,
                           icon="CHECKBOX_HLT" if all_on else "CHECKBOX_DEHLT",
                           depress=all_on)
        op.attr_name = attr.value
        op.mask = mask
        op.value = not all_on  # click toggles: all-on -> off, otherwise -> on

    # Select every polygon whose flag byte matches the active poly's byte.
    # Shift-click extends instead of replacing the selection.
    select_row = layout.row()
    select_row.enabled = enabled and sel_count > 0
    op_sel = select_row.operator("sollumz.navmesh_select_polys_by_flag_byte",
                                 text="Select Matching Polygons",
                                 icon="RESTRICT_SELECT_OFF")
    op_sel.attr_name = attr.value


class SOLLUMZ_PT_navmesh_poly_flags(Panel):
    """N-panel: per-polygon flag editor for the active navmesh polygon mesh."""
    bl_label = "NavMesh Polygon Flags"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flags"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"

    @classmethod
    def poll(cls, context):
        return _active_navmesh_polymesh(context) is not None

    def draw_header(self, context):
        self.layout.label(text="", icon="CON_FOLLOWPATH")

    def draw(self, context):
        layout = self.layout
        obj = _active_navmesh_polymesh(context)
        mesh = obj.data

        if not mesh.is_editmode:
            warn = layout.column(align=True)
            warn.label(text="Enter Edit Mode to edit polygon flags.", icon="INFO")
            warn.label(text="(polygon selection isn't available in Object Mode.)")
        else:
            sel_count, _ = _bm_selected_count(mesh)
            layout.label(text=(f"{sel_count} polygon(s) selected"
                               if sel_count else "Select polygon(s) to edit"),
                         icon="FACESEL")


class SOLLUMZ_PT_navmesh_poly_flag_0(Panel):
    bl_label = "Flag 0"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flag_0"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"
    bl_parent_id = "SOLLUMZ_PT_navmesh_poly_flags"

    def draw(self, context):
        _draw_flag_group(self.layout, context, NavMeshAttr.POLY_FLAG_0, FLAG0_BITS)


class SOLLUMZ_PT_navmesh_poly_flag_1(Panel):
    bl_label = "Flag 1"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flag_1"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"
    bl_parent_id = "SOLLUMZ_PT_navmesh_poly_flags"

    def draw(self, context):
        _draw_flag_group(self.layout, context, NavMeshAttr.POLY_FLAG_1, FLAG1_BITS)


class SOLLUMZ_PT_navmesh_poly_flag_2(Panel):
    bl_label = "Flag 2 (Category)"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flag_2"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"
    bl_parent_id = "SOLLUMZ_PT_navmesh_poly_flags"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        _draw_flag_group(self.layout, context, NavMeshAttr.POLY_FLAG_2, FLAG2_BITS)


class SOLLUMZ_PT_navmesh_poly_flag_3(Panel):
    bl_label = "Flag 3 (Slope)"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flag_3"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"
    bl_parent_id = "SOLLUMZ_PT_navmesh_poly_flags"
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        _draw_flag_group(self.layout, context, NavMeshAttr.POLY_FLAG_3, FLAG3_BITS)


class SOLLUMZ_PT_navmesh_root(Panel):
    """N-panel: root metadata + export button (shown on the NAVMESH parent)."""
    bl_label = "NavMesh"
    bl_idname = "SOLLUMZ_PT_navmesh_root"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.sollum_type == SollumType.NAVMESH

    def draw(self, context):
        layout = self.layout
        props = context.active_object.sz_navmesh

        col = layout.column(align=True)
        col.prop(props, "area_id")
        col.prop(props, "content_flags")

        layout.separator()
        col = layout.column(align=True)
        col.prop(props, "bb_min")
        col.prop(props, "bb_max")

        layout.separator()
        layout.operator("sollumz.export_ynv", icon="EXPORT")

        # Multi-cell export — required when deleting polygons that touch a
        # cell border (cross-cell edge indices in sibling files would go
        # stale otherwise).
        scene_navmesh_count = sum(
            1 for o in context.scene.objects
            if o.sollum_type == "sollumz_navmesh"
        )
        layout.separator()
        box = layout.box()
        box.label(text=f"Scene: {scene_navmesh_count} navmesh cell(s)",
                  icon="WORLD_DATA")
        if scene_navmesh_count <= 1:
            warn = box.column(align=True)
            warn.scale_y = 0.85
            warn.label(text="Load surrounding cells (3x3 grid)", icon="INFO")
            warn.label(text="before deleting border polygons —")
            warn.label(text="multi-cell export keeps neighbours")
            warn.label(text="from crashing the game.")
        box.operator("sollumz.export_all_navmeshes", icon="EXPORT")


class SOLLUMZ_PT_navmesh_portal(Panel):
    bl_label = "NavMesh Portal"
    bl_idname = "SOLLUMZ_PT_navmesh_portal"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.sollum_type == SollumType.NAVMESH_PORTAL

    def draw(self, context):
        layout = self.layout
        props = context.active_object.sz_nav_portal
        layout.prop(props, "portal_type")
        layout.prop(props, "angle")
        layout.prop(props, "poly_from")
        layout.prop(props, "poly_to")


class SOLLUMZ_PT_navmesh_point(Panel):
    bl_label = "NavMesh Point"
    bl_idname = "SOLLUMZ_PT_navmesh_point"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj is not None and obj.sollum_type == SollumType.NAVMESH_POINT

    def draw(self, context):
        layout = self.layout
        props = context.active_object.sz_nav_point
        layout.prop(props, "point_type")
