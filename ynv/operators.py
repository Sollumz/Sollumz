import os
import traceback

import bpy
import bmesh
from bpy.props import BoolProperty, IntProperty, StringProperty
from bpy.types import Operator

from .. import logger
from ..sollumz_properties import SollumType
from .cwxml_navmesh import YNV
from .navmesh_attributes import NavMeshAttr
from .navmesh_material import reassign_materials
from .ynvexport import build_edge_positional_index, export_ynv


def _find_navmesh_root(obj):
    while obj is not None:
        if obj.sollum_type == SollumType.NAVMESH:
            return obj
        obj = obj.parent
    return None


class SOLLUMZ_OT_export_ynv(Operator):
    bl_idname = "sollumz.export_ynv"
    bl_label = "Export NavMesh (.ynv.xml)"
    bl_options = {"REGISTER"}

    filepath: StringProperty(subtype="FILE_PATH")
    filter_glob: StringProperty(default="*.ynv.xml", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return _find_navmesh_root(context.active_object) is not None

    def invoke(self, context, event):
        root = _find_navmesh_root(context.active_object)
        if not self.filepath:
            self.filepath = (root.name if root else "navmesh") + YNV.file_extension
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        root = _find_navmesh_root(context.active_object)
        if root is None:
            self.report({"ERROR"}, "No NAVMESH object found in the selection.")
            return {"CANCELLED"}

        path = bpy.path.abspath(self.filepath)
        if not path.endswith(YNV.file_extension):
            path += YNV.file_extension

        with logger.use_operator_logger(self):
            try:
                ok = export_ynv(root, path)
            except Exception:
                logger.error(f"Failed to export '{root.name}':\n{traceback.format_exc()}")
                return {"CANCELLED"}

        if not ok:
            self.report({"ERROR"}, f"Failed to export '{root.name}'. See Info log.")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Exported {os.path.basename(path)}")
        return {"FINISHED"}


_CLASSIFICATION_AFFECTING_ATTRS = (
    NavMeshAttr.POLY_FLAG_1.value,
    NavMeshAttr.POLY_FLAG_2.value,
)


def _find_polymesh(navmesh_obj):
    for child in navmesh_obj.children:
        if child.sollum_type == SollumType.NAVMESH_POLY_MESH and child.type == "MESH":
            return child
    return None


def _scene_navmeshes(context) -> list:
    return [o for o in context.scene.objects if o.sollum_type == SollumType.NAVMESH]


class SOLLUMZ_OT_export_all_navmeshes(Operator):
    bl_idname = "sollumz.export_all_navmeshes"
    bl_label = "Export All NavMeshes (Multi-Cell)"
    bl_options = {"REGISTER"}

    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN"})
    filter_folder: bpy.props.BoolProperty(default=True, options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return any(o.sollum_type == SollumType.NAVMESH for o in context.scene.objects)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def execute(self, context):
        navmeshes = _scene_navmeshes(context)
        if not navmeshes:
            self.report({"ERROR"}, "No NAVMESH objects in scene.")
            return {"CANCELLED"}

        directory = bpy.path.abspath(self.directory)
        if not os.path.isdir(directory):
            self.report({"ERROR"}, f"Not a directory: {directory}")
            return {"CANCELLED"}

        all_indices: dict[int, dict] = {}
        polymesh_by_area: dict[int, object] = {}
        for nav_obj in navmeshes:
            poly_obj = _find_polymesh(nav_obj)
            if poly_obj is None:
                logger.warning(f"Skipping '{nav_obj.name}' — no polygon mesh child.")
                continue
            area = int(nav_obj.sz_navmesh.area_id)
            all_indices[area] = build_edge_positional_index(poly_obj.data)
            polymesh_by_area[area] = poly_obj

        exported, failed = 0, 0
        with logger.use_operator_logger(self):
            for nav_obj in navmeshes:
                own_area = int(nav_obj.sz_navmesh.area_id)
                siblings = {a: idx for a, idx in all_indices.items() if a != own_area}
                filename = nav_obj.name + YNV.file_extension
                filepath = os.path.join(directory, filename)
                try:
                    ok = export_ynv(nav_obj, filepath, sibling_indices=siblings)
                except Exception:
                    logger.error(
                        f"Failed exporting '{nav_obj.name}':\n{traceback.format_exc()}"
                    )
                    failed += 1
                    continue
                if ok:
                    exported += 1
                    logger.info(f"Exported {filename}")
                else:
                    failed += 1

        self.report(
            {"INFO" if failed == 0 else "WARNING"},
            f"Exported {exported}/{len(navmeshes)} navmesh(es) to {directory}"
            + (f"  ({failed} failed)" if failed else ""),
        )
        return {"FINISHED"}


def _navmesh_edit_poll(context) -> bool:
    obj = context.active_object
    return (obj is not None
            and obj.type == "MESH"
            and obj.sollum_type == SollumType.NAVMESH_POLY_MESH
            and obj.data.is_editmode)


def _navmesh_poly_obj_poll(context) -> bool:
    obj = context.active_object
    return (obj is not None
            and obj.type == "MESH"
            and obj.sollum_type == SollumType.NAVMESH_POLY_MESH)


class SOLLUMZ_OT_navmesh_set_poly_flag_bit(Operator):
    bl_idname = "sollumz.navmesh_set_poly_flag_bit"
    bl_label = "Toggle Navmesh Polygon Flag Bit"
    bl_options = {"REGISTER", "UNDO"}

    attr_name: StringProperty()
    mask: IntProperty()
    value: BoolProperty()

    @classmethod
    def poll(cls, context):
        return _navmesh_edit_poll(context)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        try:
            layer = bm.faces.layers.int[self.attr_name]
        except KeyError:
            self.report({"ERROR"}, f"Attribute '{self.attr_name}' not found on mesh.")
            return {"CANCELLED"}

        mask = int(self.mask) & 0xFF
        touched = 0
        if self.value:
            for f in bm.faces:
                if f.select:
                    f[layer] = (f[layer] | mask) & 0xFF
                    touched += 1
        else:
            inv = (~mask) & 0xFF
            for f in bm.faces:
                if f.select:
                    f[layer] = f[layer] & inv
                    touched += 1
        bmesh.update_edit_mesh(mesh)

        # f1/f2 bit toggles can change a polygon's category, so re-route slots.
        if self.attr_name in _CLASSIFICATION_AFFECTING_ATTRS:
            from .navmesh_material import classify_polygon, material_category
            from .navmesh_material import _make_category_material  # noqa: F401
            f1_layer = bm.faces.layers.int[NavMeshAttr.POLY_FLAG_1.value]
            f2_layer = bm.faces.layers.int[NavMeshAttr.POLY_FLAG_2.value]
            slot_by_category: dict[str, int] = {}
            for slot_idx, mat in enumerate(mesh.materials):
                cat = material_category(mat)
                if cat is not None and cat not in slot_by_category:
                    slot_by_category[cat] = slot_idx

            def _slot_for(cat: str) -> int:
                if cat in slot_by_category:
                    return slot_by_category[cat]
                from .navmesh_material import _category_material_name
                name = _category_material_name(cat)
                m = bpy.data.materials.get(name) or _make_category_material(cat)
                mesh.materials.append(m)
                idx = len(mesh.materials) - 1
                slot_by_category[cat] = idx
                return idx

            for f in bm.faces:
                cat = classify_polygon(f[f1_layer], f[f2_layer])
                f.material_index = _slot_for(cat)
            bmesh.update_edit_mesh(mesh)

        self.report({"INFO"}, f"{touched} polygon(s) updated.")
        return {"FINISHED"}


class SOLLUMZ_OT_navmesh_select_polys_by_flag(Operator):
    bl_idname = "sollumz.navmesh_select_polys_by_flag"
    bl_label = "Select Polys by Navmesh Flag"
    bl_options = {"REGISTER", "UNDO"}

    attr_name: StringProperty()
    mask: IntProperty()
    extend: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return _navmesh_edit_poll(context)

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        try:
            layer = bm.faces.layers.int[self.attr_name]
        except KeyError:
            self.report({"ERROR"}, f"Attribute '{self.attr_name}' not found on mesh.")
            return {"CANCELLED"}

        mask = int(self.mask) & 0xFF
        if not self.extend:
            for f in bm.faces:
                f.select_set(False)
        matched = 0
        for f in bm.faces:
            if f[layer] & mask:
                f.select_set(True)
                matched += 1
        bm.select_flush(True)
        bmesh.update_edit_mesh(mesh)
        self.report({"INFO"}, f"{matched} polygon(s) match the flag.")
        return {"FINISHED"}


class SOLLUMZ_OT_navmesh_select_polys_by_flag_byte(Operator):
    bl_idname = "sollumz.navmesh_select_polys_by_flag_byte"
    bl_label = "Select Polys by Matching Flag Byte"
    bl_options = {"REGISTER", "UNDO"}

    attr_name: StringProperty()
    extend: BoolProperty(default=False)

    @classmethod
    def poll(cls, context):
        return _navmesh_edit_poll(context)

    def invoke(self, context, event):
        self.extend = event.shift
        return self.execute(context)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)
        try:
            layer = bm.faces.layers.int[self.attr_name]
        except KeyError:
            self.report({"ERROR"}, f"Attribute '{self.attr_name}' not found on mesh.")
            return {"CANCELLED"}

        ref = bm.faces.active if (bm.faces.active and bm.faces.active.select) else None
        if ref is None:
            ref = next((f for f in bm.faces if f.select), None)
        if ref is None:
            self.report({"ERROR"}, "Select a polygon first — its flag byte is the match target.")
            return {"CANCELLED"}

        target = ref[layer] & 0xFF
        if not self.extend:
            for f in bm.faces:
                f.select_set(False)
        matched = 0
        for f in bm.faces:
            if (f[layer] & 0xFF) == target:
                f.select_set(True)
                matched += 1
        bm.select_flush(True)
        bmesh.update_edit_mesh(mesh)
        self.report({"INFO"}, f"{matched} polygon(s) match flag byte 0x{target:02X}.")
        return {"FINISHED"}


class SOLLUMZ_OT_navmesh_sink_polys(Operator):
    # Sinks polygons instead of deleting them; deleting would shift indices and
    # break references from neighbour edges, portals and sibling cells.
    bl_idname = "sollumz.navmesh_sink_polys"
    bl_label = "Sink Selected Polygons (-100m Z)"
    bl_options = {"REGISTER", "UNDO"}

    distance: bpy.props.FloatProperty(
        name="Distance (m)", default=100.0, min=0.1, soft_max=500.0,
    )

    @classmethod
    def poll(cls, context):
        return _navmesh_edit_poll(context)

    def execute(self, context):
        obj = context.active_object
        mesh = obj.data
        bm = bmesh.from_edit_mesh(mesh)

        sel_face_indices = {f.index for f in bm.faces if f.select}
        if not sel_face_indices:
            self.report({"WARNING"}, "Select polygons first.")
            return {"CANCELLED"}

        # Only sink vertices exclusive to the selected faces; shared verts
        # would drag neighbouring polygons down with them.
        vert_users: dict[int, set[int]] = {}
        for f in bm.faces:
            for v in f.verts:
                vert_users.setdefault(v.index, set()).add(f.index)

        sunk = 0
        for v in bm.verts:
            users = vert_users.get(v.index, set())
            if users and users.issubset(sel_face_indices):
                v.co.z -= self.distance
                sunk += 1

        bmesh.update_edit_mesh(mesh)
        self.report({"INFO"},
                    f"Sunk {sunk} vertex/vertices of {len(sel_face_indices)} polygon(s) "
                    f"by {self.distance:.1f}m. Polygons stay in the file — indices preserved.")
        return {"FINISHED"}


class SOLLUMZ_OT_navmesh_refresh_materials(Operator):
    bl_idname = "sollumz.navmesh_refresh_materials"
    bl_label = "Refresh NavMesh Materials"
    bl_options = {"REGISTER", "UNDO"}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj is not None
                and obj.type == "MESH"
                and obj.sollum_type == SollumType.NAVMESH_POLY_MESH
                and not obj.data.is_editmode)

    def execute(self, context):
        reassign_materials(context.active_object.data)
        context.active_object.data.update()
        return {"FINISHED"}


def menu_func_export(self, context):
    self.layout.operator(SOLLUMZ_OT_export_ynv.bl_idname, text="CodeWalker NavMesh (.ynv.xml)")


def register():
    bpy.types.TOPBAR_MT_file_export.append(menu_func_export)


def unregister():
    bpy.types.TOPBAR_MT_file_export.remove(menu_func_export)
