import os

from bpy.props import CollectionProperty, StringProperty
from bpy.types import Operator, OperatorFileListElement
from bpy_extras.io_utils import ExportHelper, ImportHelper
from szio.gta5 import AssetMapParentTxds
from szio.gta5.assets import try_load_asset
from szio.gta5.cwxml.adapters import save_map_parent_txds_to_cw
from szio.vfs import VPath

from ..gtxdimport import import_gtxd, unique_gtxd_name
from ..properties import refresh_gtxd_ui


def _selected_node(context):
    nodes = context.scene.sz_gtxds
    index = context.scene.sz_gtxd_index
    return nodes[index] if 0 <= index < len(nodes) else None


def _tree_order(context):
    """The nodes in the order shown in the UI list."""
    return sorted(context.scene.sz_gtxds, key=lambda n: n.ui_tree_sort_id)


def _block(context, node):
    """``node`` and everything under it, using the depths computed for the UI list."""
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
    """Indices of nodes sharing a name. A texture dictionary can only inherit from a single parent, so each one
    must appear only once in the tree."""
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
    """Indices of nodes that cannot be exported: without a name, or named but not linked to anything, so they
    would not produce any relationship."""
    used_as_parent = {n.parent.strip().lower() for n in nodes if n.parent.strip()}
    return {
        index
        for index, node in enumerate(nodes)
        if not node.name.strip() or (not node.parent.strip() and node.name.strip().lower() not in used_as_parent)
    }


class SOLLUMZ_OT_gtxd_create(Operator):
    """Add a texture dictionary at the root of the tree"""

    bl_idname = "sollumz.gtxd_create"
    bl_label = "Add Texture Dictionary"
    bl_options = {"UNDO"}

    def execute(self, context):
        nodes = context.scene.sz_gtxds
        node = nodes.add()
        node["name_"] = unique_gtxd_name(nodes, "txd")
        context.scene.sz_gtxd_index = len(nodes) - 1
        refresh_gtxd_ui(context.scene)
        return {"FINISHED"}


class SOLLUMZ_OT_gtxd_delete(Operator):
    """Delete the selected texture dictionary and everything that inherits from it"""

    bl_idname = "sollumz.gtxd_delete"
    bl_label = "Delete"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return _selected_node(context) is not None

    def execute(self, context):
        nodes = context.scene.sz_gtxds
        to_remove = {n.as_pointer() for n in _block(context, _selected_node(context))}
        for i in reversed(range(len(nodes))):
            if nodes[i].as_pointer() in to_remove:
                nodes.remove(i)

        context.scene.sz_gtxd_index = min(context.scene.sz_gtxd_index, len(nodes) - 1)
        refresh_gtxd_ui(context.scene)
        return {"FINISHED"}


def _relationships_of(nodes) -> list[tuple[str, str]]:
    """The ``(parent, child)`` pairs of a gtxd file, in tree order."""
    return [
        (node.parent.strip(), node.name.strip())
        for node in nodes
        if node.parent.strip() and node.name.strip()
    ]


class SOLLUMZ_OT_gtxd_import(Operator, ImportHelper):
    """Import a gtxd .meta or .xml file into the tree"""

    bl_idname = "sollumz.gtxd_import"
    bl_label = "Import GTXD"
    bl_options = {"UNDO"}

    filter_glob: StringProperty(default="*.meta;*.xml", options={"HIDDEN"}, maxlen=255)
    files: CollectionProperty(type=OperatorFileListElement, options={"HIDDEN", "SKIP_SAVE"})
    directory: StringProperty(subtype="DIR_PATH", options={"HIDDEN", "SKIP_SAVE"})

    def invoke(self, context, event):
        if self.directory and len(self.files) > 0 and self.files[0].name != "":
            # Already have a list of files, don't open the import window and do the import directly.
            # Invoked by the file handler when dropping files into Blender.
            return self.execute(context)

        return super().invoke(context, event)

    def execute(self, context):
        if self.directory and len(self.files) > 0 and self.files[0].name != "":
            filepaths = [os.path.join(self.directory, f.name) for f in self.files if f.name]
        else:
            filepaths = [self.filepath]

        imported = 0
        for filepath in filepaths:
            if self._import_file(context, filepath):
                imported += 1

        return {"FINISHED"} if imported else {"CANCELLED"}

    def _import_file(self, context, filepath: str) -> bool:
        name = os.path.basename(filepath)
        try:
            asset = try_load_asset(VPath(filepath))
        except OSError as e:
            self.report({"ERROR"}, f"Could not read '{filepath}': {e.strerror or e}")
            return False

        if not isinstance(asset, AssetMapParentTxds):
            self.report({"ERROR"}, f"'{name}' is not a gtxd file.")
            return False

        # Strip the extensions, so `gtxd.ymt.rbf.xml` becomes `gtxd`
        for suffix in (".rbf.xml", ".xml", ".meta", ".ymt"):
            if name.lower().endswith(suffix) and len(name) > len(suffix):
                name = name[: -len(suffix)]

        imported = import_gtxd(asset, name)
        self.report({"INFO"}, f"Imported {imported} relationship(s).")
        return True


class SOLLUMZ_OT_gtxd_export(Operator, ExportHelper):
    """Export the texture dictionary relationships.
    Name it 'gtxd.ymt.rbf.xml' to import it in CodeWalker and save it as a .ymt"""

    bl_idname = "sollumz.gtxd_export"
    bl_label = "Export GTXD"

    filename_ext = ".meta"
    filter_glob: StringProperty(default="*.meta;*.xml", options={"HIDDEN"}, maxlen=255)
    file_extension: StringProperty(default=".meta", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return len(context.scene.sz_gtxds) > 0

    def invoke(self, context, event):
        # `ExportHelper` only understands a single extension, so give it the last one. Otherwise it would turn
        # `gtxd.ymt.rbf.xml` into `gtxd.ymt.rbf.ymt.rbf.xml`.
        self.filename_ext = os.path.splitext(self.file_extension)[1] or self.file_extension
        self.filepath = "gtxd" + self.file_extension
        return super().invoke(context, event)

    def execute(self, context):
        nodes = context.scene.sz_gtxds
        if duplicates := find_duplicate_nodes(nodes):
            self.report({"ERROR"}, f"Duplicate name: '{nodes[min(duplicates)].name}'.")
            return {"CANCELLED"}

        if incomplete := find_incomplete_nodes(nodes):
            node = nodes[min(incomplete)]
            if not node.name.strip():
                self.report({"ERROR"}, "A texture dictionary has no name.")
            else:
                self.report({"ERROR"}, f"'{node.name}' has no parent and no children, set a parent for it.")
            return {"CANCELLED"}

        relationships = _relationships_of(_tree_order(context))
        if not relationships:
            self.report({"WARNING"}, "Nothing to export. Add a texture dictionary with a parent first.")
            return {"CANCELLED"}

        asset = AssetMapParentTxds(parents={child: parent for parent, child in relationships})
        try:
            save_map_parent_txds_to_cw(asset).write_xml(self.filepath)
        except OSError as e:
            self.report({"ERROR"}, f"Could not write '{self.filepath}': {e.strerror or e}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Successfully exported: {self.filepath}")
        return {"FINISHED"}
