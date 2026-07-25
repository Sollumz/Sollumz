import bpy
from szio.gta5 import AssetMapParentTxds

FILE, PARENT, CHILD = 0, 1, 2


def unique_gtxd_name(nodes, name: str) -> str:
    """Make ``name`` unique among the gtxd names, so creating and importing never produce duplicates."""
    name = name.strip() or "gtxd"
    taken = {n.name.strip().lower() for n in nodes if n.ui_tree_depth == FILE}
    if name.lower() not in taken:
        return name

    n = 1
    while f"{name}.{n:03d}".lower() in taken:
        n += 1
    return f"{name}.{n:03d}"


def import_gtxd(asset: AssetMapParentTxds, name: str) -> int:
    """Create a GTXD tree in the Blender scene from a gtxd asset. Returns the number of relationships."""
    children_by_parent = {}
    for child, parent in asset.parents.items():
        parent, child = parent.strip(), child.strip()
        if parent and child:
            children_by_parent.setdefault(parent.lower(), (parent, []))[1].append(child)

    nodes = bpy.context.scene.sz_gtxds
    file_index = len(nodes)

    def _append(depth: int, node_name: str):
        node = nodes.add()
        node.name = node_name
        node.ui_tree_depth = depth

    # The nodes are appended in tree order: the gtxd file, then each parent followed by its children
    _append(FILE, unique_gtxd_name(nodes, name))
    for parent, children in children_by_parent.values():
        _append(PARENT, parent)
        for child in children:
            _append(CHILD, child)

    bpy.context.scene.sz_gtxd_index = file_index
    return len(asset.parents)
