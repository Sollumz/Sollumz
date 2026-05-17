import bpy
from bpy.types import Material, Mesh

from ..tools.blenderhelper import find_bsdf_and_material_output


MATERIAL_NAME_PREFIX = "navmesh_"


_F2_FLAT_GROUND     = 1 << 0
_F2_ROAD            = 1 << 1
_F2_TRAIN_TRACK     = 1 << 3
_F2_SHALLOW_WATER   = 1 << 4
_F2_FOOTPATH_UNK1   = 1 << 5
_F2_FOOTPATH_UNK2   = 1 << 6
_F2_FOOTPATH_MALL   = 1 << 7
_F1_INTERACTION_UNK = 1 << 7


CATEGORY_INTERACTION   = "interaction"
CATEGORY_FOOTPATH      = "footpath"
CATEGORY_ROAD          = "road"
CATEGORY_TRACK         = "track"
CATEGORY_SHALLOW       = "shallow"
CATEGORY_FLAT          = "flat"
CATEGORY_OTHER         = "other"


# Priority-ordered; first match wins, so footpath beats flat ground.
_F2_PRIORITY: tuple[tuple[str, int], ...] = (
    (CATEGORY_FOOTPATH, _F2_FOOTPATH_UNK1 | _F2_FOOTPATH_UNK2 | _F2_FOOTPATH_MALL),
    (CATEGORY_ROAD,     _F2_ROAD),
    (CATEGORY_TRACK,    _F2_TRAIN_TRACK),
    (CATEGORY_SHALLOW,  _F2_SHALLOW_WATER),
    (CATEGORY_FLAT,     _F2_FLAT_GROUND),
)


_CATEGORY_COLORS: dict[str, tuple[float, float, float, float]] = {
    CATEGORY_INTERACTION: (0.85, 0.10, 0.10, 1.0),
    CATEGORY_FOOTPATH:    (0.75, 0.80, 0.20, 1.0),
    CATEGORY_ROAD:        (0.08, 0.12, 0.25, 1.0),
    CATEGORY_TRACK:       (0.45, 0.20, 0.45, 1.0),
    CATEGORY_SHALLOW:     (0.10, 0.35, 0.65, 1.0),
    CATEGORY_FLAT:        (0.20, 0.50, 0.20, 1.0),
    CATEGORY_OTHER:       (0.25, 0.25, 0.25, 1.0),
}


CATEGORY_LABELS: dict[str, str] = {
    CATEGORY_INTERACTION: "Interaction (Unk)",
    CATEGORY_FOOTPATH:    "Footpath",
    CATEGORY_ROAD:        "Road",
    CATEGORY_TRACK:       "Train Track",
    CATEGORY_SHALLOW:     "Shallow Water",
    CATEGORY_FLAT:        "Flat Ground",
    CATEGORY_OTHER:       "Other / Mixed",
}


ALL_CATEGORIES: tuple[str, ...] = (
    CATEGORY_INTERACTION,
    CATEGORY_FOOTPATH,
    CATEGORY_ROAD,
    CATEGORY_TRACK,
    CATEGORY_SHALLOW,
    CATEGORY_FLAT,
    CATEGORY_OTHER,
)


def classify_polygon(f1_byte: int, f2_byte: int) -> str:
    if f1_byte & _F1_INTERACTION_UNK:
        return CATEGORY_INTERACTION
    f2 = f2_byte & 0xFF
    for cat, mask in _F2_PRIORITY:
        if f2 & mask:
            return cat
    return CATEGORY_OTHER


def _category_material_name(category: str) -> str:
    return f"{MATERIAL_NAME_PREFIX}{category}"


def _make_category_material(category: str) -> Material:
    mat = bpy.data.materials.new(_category_material_name(category))
    if bpy.app.version < (5, 0, 0):
        mat.use_nodes = True
    color = _CATEGORY_COLORS[category]
    mat.diffuse_color = color
    bsdf, _ = find_bsdf_and_material_output(mat)
    if bsdf is not None and "Base Color" in bsdf.inputs:
        bsdf.inputs["Base Color"].default_value = color
    return mat


def get_navmesh_material(category: str, cache: dict[str, Material]) -> Material:
    if category in cache:
        return cache[category]
    name = _category_material_name(category)
    mat = bpy.data.materials.get(name) or _make_category_material(category)
    cache[category] = mat
    return mat


def material_category(mat: Material | None) -> str | None:
    if mat is None or not mat.name.startswith(MATERIAL_NAME_PREFIX):
        return None
    suffix = mat.name[len(MATERIAL_NAME_PREFIX):]
    return suffix if suffix in ALL_CATEGORIES else None


def draw_material_info(layout, mat: Material) -> None:
    cat = material_category(mat)
    if cat is not None:
        layout.label(text=f"Category: {CATEGORY_LABELS[cat]}", icon="MATERIAL")


def reassign_materials(mesh: Mesh) -> None:
    from .navmesh_attributes import NavMeshAttr

    if (NavMeshAttr.POLY_FLAG_1.value not in mesh.attributes
            or NavMeshAttr.POLY_FLAG_2.value not in mesh.attributes):
        return
    f1_data = mesh.attributes[NavMeshAttr.POLY_FLAG_1.value].data
    f2_data = mesh.attributes[NavMeshAttr.POLY_FLAG_2.value].data

    slot_by_category: dict[str, int] = {}
    for slot_idx, mat in enumerate(mesh.materials):
        cat = material_category(mat)
        if cat is not None and cat not in slot_by_category:
            slot_by_category[cat] = slot_idx

    def _slot_for(cat: str) -> int:
        if cat in slot_by_category:
            return slot_by_category[cat]
        mat = bpy.data.materials.get(_category_material_name(cat))
        if mat is None:
            mat = _make_category_material(cat)
        mesh.materials.append(mat)
        idx = len(mesh.materials) - 1
        slot_by_category[cat] = idx
        return idx

    for poly in mesh.polygons:
        cat = classify_polygon(f1_data[poly.index].value, f2_data[poly.index].value)
        poly.material_index = _slot_for(cat)
