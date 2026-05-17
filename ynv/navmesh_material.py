"""Six named navmesh categories + one catch-all, each with its own material.

A polygon is classified by ``classify_polygon(f1, f2)`` and assigned the
matching category material. The material is **not** the source of truth for
flags — it only drives the viewport color and gives the user a one-click
way to select every polygon in a category via the standard Material
Properties → "Select" button.

The "interaction" category is special: it triggers off ``InteractionUnk``
(Flag 1, bit 7) regardless of f2, because it marks polygons the user
generally wants to spot at a glance.
"""
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


# Priority-ordered classification: walk top to bottom, first match wins.
# The list shape lets one polygon with several bits set land in the most
# specific category — e.g. FlatGround + FootpathUnk1 → footpath, not flat.
# All three footpath bits (Unk1, Unk2, Mall) collapse into a single
# "footpath" category.
_F2_PRIORITY: tuple[tuple[str, int], ...] = (
    (CATEGORY_FOOTPATH, _F2_FOOTPATH_UNK1 | _F2_FOOTPATH_UNK2 | _F2_FOOTPATH_MALL),
    (CATEGORY_ROAD,     _F2_ROAD),
    (CATEGORY_TRACK,    _F2_TRAIN_TRACK),
    (CATEGORY_SHALLOW,  _F2_SHALLOW_WATER),
    (CATEGORY_FLAT,     _F2_FLAT_GROUND),
)


# Palette tuned to match the CodeWalker / 3ds Max viewport (Legion Square
# screenshot reference): roads are the dark blue asphalt mass, footpaths
# the yellow-lime curb strips, lawn the saturated green, fountains the
# medium blue.
_CATEGORY_COLORS: dict[str, tuple[float, float, float, float]] = {
    CATEGORY_INTERACTION: (0.85, 0.10, 0.10, 1.0),  # red
    CATEGORY_FOOTPATH:    (0.75, 0.80, 0.20, 1.0),  # yellow-lime
    CATEGORY_ROAD:        (0.08, 0.12, 0.25, 1.0),  # asphalt dark blue
    CATEGORY_TRACK:       (0.45, 0.20, 0.45, 1.0),  # purple
    CATEGORY_SHALLOW:     (0.10, 0.35, 0.65, 1.0),  # water blue
    CATEGORY_FLAT:        (0.20, 0.50, 0.20, 1.0),  # lawn green
    CATEGORY_OTHER:       (0.25, 0.25, 0.25, 1.0),  # grey
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


# Order matters for panel listing — most attention-grabbing first.
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
    """Return the category key for a polygon with the given f1/f2 bytes.

    ``InteractionUnk`` (Flag 1, bit 7) wins over every f2 bit — those
    polygons should be unmistakable. Otherwise the first matching entry in
    ``_F2_PRIORITY`` wins; the order encodes "more specific beats less
    specific" so FlatGround + FootpathMall → footpath_mall, not flat.
    """
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
    """Return (creating if necessary) the material for ``category``."""
    if category in cache:
        return cache[category]
    name = _category_material_name(category)
    mat = bpy.data.materials.get(name) or _make_category_material(category)
    cache[category] = mat
    return mat


def material_category(mat: Material | None) -> str | None:
    """Reverse-lookup: which category does this material represent?"""
    if mat is None or not mat.name.startswith(MATERIAL_NAME_PREFIX):
        return None
    suffix = mat.name[len(MATERIAL_NAME_PREFIX):]
    return suffix if suffix in ALL_CATEGORIES else None


def draw_material_info(layout, mat: Material) -> None:
    """Inline navmesh material info — category + how-to-select hint.

    Drawn directly inside the Sollumz material panel; not its own sub-panel.
    """
    cat = material_category(mat)
    if cat is not None:
        layout.label(text=f"Category: {CATEGORY_LABELS[cat]}", icon="MATERIAL")
    info = layout.column(align=True)
    info.scale_y = 0.85
    info.label(text="Edit Mode → 'Select' above picks every", icon="INFO")
    info.label(text="polygon using this material. Flags are")
    info.label(text="edited in the N-panel (Sollumz Tools).")


def reassign_materials(mesh: Mesh) -> None:
    """Walk every face and re-route it to the material matching its current flags.

    Called after the user toggles bits that affect classification (f1 bit 7
    or any f2 bit). Creates category materials on demand if the mesh didn't
    have a slot for the new category yet.
    """
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
