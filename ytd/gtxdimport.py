import bpy
from szio.gta5 import AssetMapParentTxds

from .properties import refresh_gtxd_ui


def unique_gtxd_name(nodes, name: str) -> str:
    """Make ``name`` unique among the texture dictionary names, so nothing collides in the tree."""
    name = name.strip() or "txd"
    taken = {n.name.strip().lower() for n in nodes}
    if name.lower() not in taken:
        return name

    n = 1
    while f"{name}.{n:03d}".lower() in taken:
        n += 1
    return f"{name}.{n:03d}"


def import_gtxd(asset: AssetMapParentTxds, name: str = "") -> int:
    """Add the relationships of a gtxd asset to the GTXD tree. Returns the number of relationships."""
    scene = bpy.context.scene
    nodes = scene.sz_gtxds
    first_index = len(nodes)

    # Each texture dictionary becomes a single node pointing at its parent, so hierarchies of any depth are kept
    existing = {n.name.strip().lower() for n in nodes}
    for child, parent in asset.parents.items():
        parent, child = parent.strip(), child.strip()
        if not parent or not child or child.lower() in existing:
            continue

        node = nodes.add()
        node["name_"] = child
        node["parent_"] = parent
        existing.add(child.lower())

    # Parents that are not a child of anything else are the roots of the tree
    for parent in {p.strip() for p in asset.parents.values() if p.strip()}:
        if parent.lower() not in existing:
            node = nodes.add()
            node["name_"] = parent
            existing.add(parent.lower())

    scene.sz_gtxd_index = first_index
    refresh_gtxd_ui(scene)
    return len(asset.parents)
