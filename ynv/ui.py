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
    import bmesh
    bm = bmesh.from_edit_mesh(mesh)
    return sum(1 for f in bm.faces if f.select), bm


def _draw_flag_group(layout, context, attr, bits):
    obj = _active_navmesh_polymesh(context)
    mesh = obj.data if obj is not None else None
    enabled = mesh is not None and mesh.is_editmode
    sel_count, bm = _bm_selected_count(mesh) if enabled else (0, None)

    layer = None
    if bm is not None:
        try:
            layer = bm.faces.layers.int[attr.value]
        except KeyError:
            layer = None

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
        op.value = not all_on

    select_row = layout.row()
    select_row.enabled = enabled and sel_count > 0
    op_sel = select_row.operator("sollumz.navmesh_select_polys_by_flag_byte",
                                 text="Select Matching Polygons",
                                 icon="RESTRICT_SELECT_OFF")
    op_sel.attr_name = attr.value


class SOLLUMZ_PT_NAVMESH_TOOL_PANEL(Panel):
    bl_label = "NavMesh"
    bl_idname = "SOLLUMZ_PT_NAVMESH_TOOL_PANEL"
    bl_category = "Sollumz Tools"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_options = {"DEFAULT_CLOSED"}
    bl_order = 3

    def draw_header(self, context):
        self.layout.label(text="", icon="MESH_GRID")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object
        sollum_type = obj.sollum_type if obj is not None else None

        nav_col = layout.column()
        nav_col.enabled = sollum_type == SollumType.NAVMESH
        if sollum_type == SollumType.NAVMESH:
            props = obj.sz_navmesh
            nav_col.prop(props, "area_id")
            nav_col.prop(props, "content_flags")
        else:
            nav_col.label(text="Select a NavMesh", icon="INFO")

        layout.separator(factor=2.0)
        layout.operator("sollumz.export_all_navmeshes",
                        text="Export All NavMeshes",
                        icon="EXPORT")


class NavMeshToolChildPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_parent_id = SOLLUMZ_PT_NAVMESH_TOOL_PANEL.bl_idname
    bl_category = SOLLUMZ_PT_NAVMESH_TOOL_PANEL.bl_category


class SOLLUMZ_PT_navmesh_poly_flags(NavMeshToolChildPanel, Panel):
    bl_label = "Polygon Flags"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flags"
    bl_order = 1
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text="", icon="BOOKMARKS")

    def draw(self, context):
        layout = self.layout
        obj = _active_navmesh_polymesh(context)

        if obj is None:
            layout.active = False
            layout.label(text="Select a navmesh polygon mesh", icon="INFO")
            return

        mesh = obj.data
        if not mesh.is_editmode:
            layout.label(text="Enter Edit Mode to edit flags", icon="INFO")
        else:
            sel_count, _ = _bm_selected_count(mesh)
            layout.label(text=(f"{sel_count} polygon(s) selected"
                               if sel_count else "Select polygon(s) to edit"),
                         icon="FACESEL")


class _NavMeshFlagSubPanel:
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "Sollumz Tools"
    bl_parent_id = "SOLLUMZ_PT_navmesh_poly_flags"


class SOLLUMZ_PT_navmesh_poly_flag_0(_NavMeshFlagSubPanel, Panel):
    bl_label = "General"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flag_0"
    bl_order = 0

    def draw(self, context):
        _draw_flag_group(self.layout, context, NavMeshAttr.POLY_FLAG_0, FLAG0_BITS)


class SOLLUMZ_PT_navmesh_poly_flag_1(_NavMeshFlagSubPanel, Panel):
    bl_label = "Behavior"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flag_1"
    bl_order = 1

    def draw(self, context):
        _draw_flag_group(self.layout, context, NavMeshAttr.POLY_FLAG_1, FLAG1_BITS)


class SOLLUMZ_PT_navmesh_poly_flag_2(_NavMeshFlagSubPanel, Panel):
    bl_label = "Surface Category"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flag_2"
    bl_order = 2
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        _draw_flag_group(self.layout, context, NavMeshAttr.POLY_FLAG_2, FLAG2_BITS)


class SOLLUMZ_PT_navmesh_poly_flag_3(_NavMeshFlagSubPanel, Panel):
    bl_label = "Slope Direction"
    bl_idname = "SOLLUMZ_PT_navmesh_poly_flag_3"
    bl_order = 3
    bl_options = {"DEFAULT_CLOSED"}

    def draw(self, context):
        _draw_flag_group(self.layout, context, NavMeshAttr.POLY_FLAG_3, FLAG3_BITS)


class SOLLUMZ_PT_navmesh_portals_points(NavMeshToolChildPanel, Panel):
    bl_label = "Portals & Points"
    bl_idname = "SOLLUMZ_PT_navmesh_portals_points"
    bl_order = 2
    bl_options = {"DEFAULT_CLOSED"}

    def draw_header(self, context):
        self.layout.label(text="", icon="EMPTY_AXIS")

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        obj = context.active_object
        sollum_type = obj.sollum_type if obj is not None else None

        portal_col = layout.column(heading="Portal")
        portal_col.enabled = sollum_type == SollumType.NAVMESH_PORTAL
        if obj is not None:
            portal = obj.sz_nav_portal
            portal_col.prop(portal, "portal_type")
            portal_col.prop(portal, "angle")
            portal_col.prop(portal, "poly_from")
            portal_col.prop(portal, "poly_to")

        layout.separator()

        point_col = layout.column(heading="Point")
        point_col.enabled = sollum_type == SollumType.NAVMESH_POINT
        if obj is not None:
            point_col.prop(obj.sz_nav_point, "point_type")


# Sollumz top-level panels use a fixed bl_order (Collisions=2, Fragments=3, ...).
# To slot NavMesh between Collisions and Fragments we bump every panel at
# order >= 3 by one at register time and restore them on unregister.
_SHIFTED_PANELS: list[tuple[type, int]] = []


def _shift_sibling_panels():
    _SHIFTED_PANELS.clear()
    for cls in bpy.types.Panel.__subclasses__():
        if getattr(cls, "bl_category", None) != "Sollumz Tools":
            continue
        if getattr(cls, "bl_parent_id", ""):
            continue
        if cls is SOLLUMZ_PT_NAVMESH_TOOL_PANEL:
            continue
        order = getattr(cls, "bl_order", 0)
        if order >= 3:
            _SHIFTED_PANELS.append((cls, order))
            cls.bl_order = order + 1
    SOLLUMZ_PT_NAVMESH_TOOL_PANEL.bl_order = 3


def _restore_sibling_panels():
    for cls, original in _SHIFTED_PANELS:
        cls.bl_order = original
    _SHIFTED_PANELS.clear()


def register():
    _shift_sibling_panels()


def unregister():
    _restore_sibling_panels()

