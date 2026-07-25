import os

from bpy.props import CollectionProperty, StringProperty
from bpy.types import Operator, OperatorFileListElement
from bpy_extras.io_utils import ExportHelper, ImportHelper
from szio.gta5 import AssetMapParentTxds
from szio.gta5.assets import try_load_asset
from szio.gta5.cwxml.adapters import save_map_parent_txds_to_cw
from szio.vfs import VPath

from ..gtxdimport import import_gtxd, unique_gtxd_name

FILE, PARENT, CHILD = 0, 1, 2


def _selected_node(context):
    nodes = context.scene.sz_gtxds
    index = context.scene.sz_gtxd_index
    return nodes[index] if 0 <= index < len(nodes) else None


def _block_end(nodes, index: int) -> int:
    """Index right after the last descendant of the node at ``index``."""
    depth = nodes[index].ui_tree_depth
    end = index + 1
    while end < len(nodes) and nodes[end].ui_tree_depth > depth:
        end += 1
    return end


def _append_node(nodes, depth: int, name: str):
    """Append a node at the end of the tree."""
    node = nodes.add()
    node.name = name
    node.ui_tree_depth = depth
    return node


def _insert_node(context, depth: int, name: str, at: int):
    """Insert a node at ``at``. Blender collections can only append, so the new node is moved into place."""
    nodes = context.scene.sz_gtxds
    _append_node(nodes, depth, name)
    if at < len(nodes) - 1:
        nodes.move(len(nodes) - 1, at)
    context.scene.sz_gtxd_index = at
    return nodes[at]


def _enclosing_index(context, depth: int) -> int | None:
    """Index of the node at ``depth`` that encloses the selection, or None. Stops at the enclosing gtxd file,
    so a node is never attached to a different file."""
    nodes = context.scene.sz_gtxds
    index = context.scene.sz_gtxd_index
    if not (0 <= index < len(nodes)):
        return None

    while index >= 0:
        node_depth = nodes[index].ui_tree_depth
        if node_depth == depth:
            return index
        if node_depth == FILE:
            # Reached the start of the file block without finding a node at `depth`
            return None
        index -= 1

    return None


class SOLLUMZ_OT_gtxd_create(Operator):
    """Add a GTXD file to the tree"""

    bl_idname = "sollumz.gtxd_create"
    bl_label = "Add GTXD"
    bl_options = {"UNDO"}

    def execute(self, context):
        nodes = context.scene.sz_gtxds
        _insert_node(context, FILE, unique_gtxd_name(nodes, "gtxd"), len(nodes))
        return {"FINISHED"}


class SOLLUMZ_OT_gtxd_add_parent(Operator):
    """Add a parent texture dictionary to the selected GTXD file"""

    bl_idname = "sollumz.gtxd_add_parent"
    bl_label = "Add Parent"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return _enclosing_index(context, FILE) is not None

    def execute(self, context):
        file_index = _enclosing_index(context, FILE)
        _insert_node(context, PARENT, "", _block_end(context.scene.sz_gtxds, file_index))
        return {"FINISHED"}


class SOLLUMZ_OT_gtxd_add_child(Operator):
    """Add a child texture dictionary to the selected parent"""

    bl_idname = "sollumz.gtxd_add_child"
    bl_label = "Add Child"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return _enclosing_index(context, PARENT) is not None

    def execute(self, context):
        parent_index = _enclosing_index(context, PARENT)
        _insert_node(context, CHILD, "", _block_end(context.scene.sz_gtxds, parent_index))
        return {"FINISHED"}


class SOLLUMZ_OT_gtxd_delete(Operator):
    """Delete the selected node and everything under it"""

    bl_idname = "sollumz.gtxd_delete"
    bl_label = "Delete"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return _selected_node(context) is not None

    def execute(self, context):
        nodes = context.scene.sz_gtxds
        index = context.scene.sz_gtxd_index
        for i in reversed(range(index, _block_end(nodes, index))):
            nodes.remove(i)

        context.scene.sz_gtxd_index = max(index - 1, 0)
        return {"FINISHED"}


def _iter_relationships(context, file_index: int):
    """Yield ``(parent, child)`` pairs of the gtxd file starting at ``file_index``."""
    nodes = context.scene.sz_gtxds
    parent = None
    for i in range(file_index + 1, _block_end(nodes, file_index)):
        node = nodes[i]
        name = node.name.strip()
        if node.ui_tree_depth == PARENT:
            parent = name
        elif node.ui_tree_depth == CHILD and parent and name:
            yield parent, name


def find_duplicate_nodes(nodes) -> set[int]:
    """Indices of nodes whose name is already used by a sibling: two gtxd files with the same name, two parents
    in the same file, or two children under the same parent."""
    duplicates = set()
    # Name -> index of its first occurrence, so both sides of a conflict can be marked
    file_names = {}
    parent_names = {}
    child_names = {}
    has_parent = False
    for index, node in enumerate(nodes):
        depth = node.ui_tree_depth
        if depth == FILE:
            parent_names.clear()
            child_names.clear()
            has_parent = False
        elif depth == PARENT:
            child_names.clear()
            has_parent = True

        name = node.name.strip().lower()
        if not name or (depth == CHILD and not has_parent):
            continue

        names = (file_names, parent_names, child_names)[depth]
        if (first := names.get(name)) is not None:
            duplicates.add(first)
            duplicates.add(index)
        else:
            names[name] = index

    return duplicates


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
    """Export the selected GTXD file.
    Name it 'gtxd.ymt.rbf.xml' to import it in CodeWalker and save it as a .ymt"""

    bl_idname = "sollumz.gtxd_export"
    bl_label = "Export GTXD"

    filename_ext = ".meta"
    filter_glob: StringProperty(default="*.meta;*.xml", options={"HIDDEN"}, maxlen=255)
    file_extension: StringProperty(default=".meta", options={"HIDDEN"})

    @classmethod
    def poll(cls, context):
        return _enclosing_index(context, FILE) is not None

    def invoke(self, context, event):
        file_index = _enclosing_index(context, FILE)
        name = context.scene.sz_gtxds[file_index].name or "gtxd"
        # `ExportHelper` only understands a single extension, so give it the last one. Otherwise it would turn
        # `gtxd.ymt.rbf.xml` into `gtxd.ymt.rbf.ymt.rbf.xml`.
        self.filename_ext = os.path.splitext(self.file_extension)[1] or self.file_extension
        self.filepath = name + self.file_extension
        return super().invoke(context, event)

    def execute(self, context):
        nodes = context.scene.sz_gtxds
        file_index = _enclosing_index(context, FILE)
        block = range(file_index, _block_end(nodes, file_index))
        if duplicates := find_duplicate_nodes(nodes) & set(block):
            self.report({"ERROR"}, f"Duplicate name: '{nodes[min(duplicates)].name}'.")
            return {"CANCELLED"}

        relationships = list(_iter_relationships(context, file_index))
        if not relationships:
            self.report({"WARNING"}, "Nothing to export. Add a parent and a child first.")
            return {"CANCELLED"}

        seen_children = set()
        parent_of = {}
        for parent, child in relationships:
            if parent == child:
                self.report({"ERROR"}, f"'{child}' cannot be its own parent.")
                return {"CANCELLED"}

            if child.lower() in seen_children:
                self.report({"ERROR"}, f"'{child}' is used as a child more than once.")
                return {"CANCELLED"}

            seen_children.add(child.lower())
            parent_of[child] = parent

        for child in parent_of:
            seen = {child}
            current = child
            while (current := parent_of.get(current)) is not None:
                if current in seen:
                    self.report({"ERROR"}, f"'{child}' is part of a parent cycle.")
                    return {"CANCELLED"}
                seen.add(current)

        asset = AssetMapParentTxds(parents={child: parent for parent, child in relationships})
        try:
            save_map_parent_txds_to_cw(asset).write_xml(self.filepath)
        except OSError as e:
            self.report({"ERROR"}, f"Could not write '{self.filepath}': {e.strerror or e}")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Successfully exported: {self.filepath}")
        return {"FINISHED"}
