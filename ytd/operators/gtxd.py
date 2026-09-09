import os

from bpy.props import StringProperty
from bpy.types import Operator
from bpy_extras.io_utils import ExportHelper
from szio.gta5 import AssetMapParentTxds
from szio.gta5.cwxml.adapters import save_map_parent_txds_to_cw

from ...sollumz_operators import ImportAssetsOperatorImpl
from ..gtxdimport import unique_name
from ..properties import get_gtxd_ui_order, get_selected_gtxd, refresh_gtxd_ui


def _selected_node(context):
    gtxd = get_selected_gtxd(context)
    if gtxd is None:
        return None
    nodes = gtxd.nodes
    index = gtxd.node_index
    return nodes[index] if 0 <= index < len(nodes) else None


def _tree_order(context):
    gtxd = get_selected_gtxd(context)
    return get_gtxd_ui_order(gtxd) if gtxd else []


def _block(context, node):
    ordered = _tree_order(context)
    index = next((i for i, n in enumerate(ordered) if n.as_pointer() == node.as_pointer()), None)
    if index is None:
        return []

    depth = ordered[index].ui_tree_depth
    end = index + 1
    while end < len(ordered) and ordered[end].ui_tree_depth > depth:
        end += 1

    return ordered[index:end]


def find_duplicate_nodes(nodes) -> set[int]:
    duplicates = set()
    first_index = {}
    for index, node in enumerate(nodes):
        name = node.name.strip().lower()
        if not name:
            continue

        if (first := first_index.get(name)) is not None:
            duplicates.add(first)
            duplicates.add(index)
        else:
            first_index[name] = index

    return duplicates


def find_incomplete_nodes(nodes) -> set[int]:
    used_as_parent = {n.parent.strip().lower() for n in nodes if n.parent.strip()}
    return {
        index
        for index, node in enumerate(nodes)
        if not node.name.strip() or (not node.parent.strip() and node.name.strip().lower() not in used_as_parent)
    }


class SOLLUMZ_OT_gtxd_create(Operator):
    """Add a GTXD to the project"""

    bl_idname = "sollumz.gtxd_create"
    bl_label = "Add GTXD"
    bl_options = {"UNDO"}

    def execute(self, context):
        gtxds = context.scene.sz_gtxds
        name = unique_name(gtxds, "gtxd", "gtxd")
        gtxd = gtxds.add()
        gtxd.name = name
        context.scene.sz_gtxd_index = len(gtxds) - 1
        return {"FINISHED"}


class SOLLUMZ_OT_gtxd_delete(Operator):

    bl_idname = "sollumz.gtxd_delete"
    bl_label = "Delete"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return get_selected_gtxd(context) is not None

    def execute(self, context):
        gtxds = context.scene.sz_gtxds
        gtxds.remove(context.scene.sz_gtxd_index)
        context.scene.sz_gtxd_index = min(context.scene.sz_gtxd_index, len(gtxds) - 1)
        return {"FINISHED"}

class SOLLUMZ_OT_gtxd_node_create(Operator):

    bl_idname = "sollumz.gtxd_node_create"
    bl_label = "Add Texture Dictionary"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return get_selected_gtxd(context) is not None

    def execute(self, context):
        gtxd = get_selected_gtxd(context)
        nodes = gtxd.nodes
        node = nodes.add()
        node["name_"] = unique_name(nodes, "txd", "txd")
        gtxd.node_index = len(nodes) - 1
        refresh_gtxd_ui(gtxd)
        return {"FINISHED"}

class SOLLUMZ_OT_gtxd_node_delete(Operator):
    bl_idname = "sollumz.gtxd_node_delete"
    bl_label = "Delete Texture Dictionary"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return _selected_node(context) is not None

    def execute(self, context):
        gtxd = get_selected_gtxd(context)
        nodes = gtxd.nodes
        to_remove = {n.as_pointer() for n in _block(context, _selected_node(context))}
        for i in reversed(range(len(nodes))):
            if nodes[i].as_pointer() in to_remove:
                nodes.remove(i)

        gtxd.node_index = min(gtxd.node_index, len(nodes) - 1)
        refresh_gtxd_ui(gtxd)
        return {"FINISHED"}


def _relationships_of(nodes) -> list[tuple[str, str]]:
    """Return the parent-child relationships."""
    return [
        (node.parent.strip(), node.name.strip())
        for node in nodes
        if node.parent.strip() and node.name.strip()
    ]


class SOLLUMZ_OT_gtxd_import(ImportAssetsOperatorImpl, Operator):
    bl_idname = "sollumz.gtxd_import"
    bl_label = "Import GTXD"
    bl_options = {"UNDO"}

    filter_glob: StringProperty(
        default="*.meta;*.ymt.rbf.xml",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )


class SOLLUMZ_OT_gtxd_export(Operator, ExportHelper):
    """Export the selected GTXD"""

    bl_idname = "sollumz.gtxd_export"
    bl_label = "Export GTXD"

    filename_ext = ".meta"
    filter_glob: StringProperty(default="*.meta;*.xml", options={"HIDDEN"}, maxlen=255)
    file_extension: StringProperty(default=".meta", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        gtxd = get_selected_gtxd(context)
        return gtxd is not None and len(gtxd.nodes) > 0

    def invoke(self, context, event):
        self.filename_ext = os.path.splitext(self.file_extension)[1] or self.file_extension
        self.filepath = get_selected_gtxd(context).name + self.file_extension
        return super().invoke(context, event)

    def execute(self, context):
        gtxd = get_selected_gtxd(context)
        if gtxd is None:
            return {"CANCELLED"}
        nodes = gtxd.nodes
        if duplicates := find_duplicate_nodes(nodes):
            self.report({"ERROR"}, f"Duplicate texture dictionary name: '{nodes[min(duplicates)].name}'.")
            return {"CANCELLED"}

        if incomplete := find_incomplete_nodes(nodes):
            node = nodes[min(incomplete)]
            if not node.name.strip():
                self.report({"ERROR"}, "Texture dictionary name cannot be empty.")
            else:
                self.report({"ERROR"}, f"Texture dictionary '{node.name}' is not part of any relationship.")
            return {"CANCELLED"}

        relationships = _relationships_of(_tree_order(context))
        asset = AssetMapParentTxds(parents={child: parent for parent, child in relationships})
        try:
            save_map_parent_txds_to_cw(asset).write_xml(self.filepath)
        except OSError as e:
            self.report({"ERROR"}, f"Could not write '{self.filepath}': {e.strerror or e}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Successfully exported: {self.filepath}")
        return {"FINISHED"}
