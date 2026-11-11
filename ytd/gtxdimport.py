import bpy
from szio.gta5 import AssetMapParentTxds
from .properties import refresh_gtxd_ui

def unique_name(items, name: str, fallback: str) -> str:
    name = name.strip() or fallback
    taken = {item.name.strip().lower() for item in items}
    if name.lower() not in taken:
        return name

    n = 1
    while f"{name}.{n:03d}".lower() in taken:
        n += 1
    return f"{name}.{n:03d}"


def import_gtxd(asset: AssetMapParentTxds, name: str = "") -> int:
    scene = bpy.context.scene
    name = unique_name(scene.sz_gtxds, name, "gtxd")
    gtxd = scene.sz_gtxds.add()
    gtxd.name = name
    nodes = gtxd.nodes

    existing = set()
    imported = 0
    for child, parent in asset.parents.items():
        parent, child = parent.strip(), child.strip()
        if not parent or not child or child.lower() in existing:
            continue

        node = nodes.add()
        node["name_"] = child
        node["parent_"] = parent
        existing.add(child.lower())
        imported += 1

    for parent in {p.strip() for p in asset.parents.values() if p.strip()}:
        if parent.lower() not in existing:
            node = nodes.add()
            node["name_"] = parent
            existing.add(parent.lower())

    scene.sz_gtxd_index = len(scene.sz_gtxds) - 1
    gtxd.node_index = 0
    refresh_gtxd_ui(gtxd)
    return imported