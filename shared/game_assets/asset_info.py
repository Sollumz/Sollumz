"""Centralized GTA asset metadata lookup; works for both library-baked and in-blend authored assets."""

import json
from dataclasses import asdict, dataclass, field
from typing import Literal

import bpy
from bpy.types import Object
from mathutils import Quaternion, Vector

from ...sollumz_properties import ArchetypeType, SollumType
from ...tools.blenderhelper import remove_number_suffix


@dataclass(slots=True)
class AssetArchetypeInfo:
    ytyp: str
    type: Literal["BASE", "TIME", "MLO"]
    lod_dist: float
    bb_min: Vector
    bb_max: Vector
    num_extensions: int
    mlo_num_exit_portals: int


@dataclass(slots=True)
class AssetInfoCache:
    """Per-operation cache. Pass the same instance to multiple lookups so the YTYP scan and the live
    Blender-data traversal are amortized across calls. Entries are keyed by the asset name with Blender's
    ``.001`` duplicate suffix stripped and lowercased, so duplicates and instance objects share entries."""

    _ytyp_lookup: dict[str, tuple[AssetArchetypeInfo | None, Object | None]] = field(default_factory=dict)
    _lights: dict[str, list | None] = field(default_factory=dict)
    _collisions: dict[str, dict | None] = field(default_factory=dict)
    _skeleton: dict[str, dict | None] = field(default_factory=dict)


def _asset_key(obj: Object) -> str:
    return remove_number_suffix(obj.name).lower()


def try_get_asset_metadata_archetype_info(obj: Object, *, cache: AssetInfoCache | None = None) -> AssetArchetypeInfo | None:
    """Return the archetype information for ``obj``. Pre-baked metadata is consulted first (assets linked from the
    shared asset library); if absent, the scene YTYPs are scanned for an archetype matching ``obj`` by name (Blender's
    ``.001`` duplicate suffix is stripped). Returns ``None`` if no archetype information can be resolved.
    """
    info_str = _try_get_asset_metadata_str(obj, "sz_asset_archetype_info")
    if info_str:
        return _parse_archetype_info(info_str)

    info, _ = _resolve_via_scene_ytyps(obj, cache)
    return info


def try_get_archetype_info_by_name(archetype_name: str, *, cache: AssetInfoCache | None = None) -> AssetArchetypeInfo | None:
    """Return the archetype information for ``archetype_name`` by scanning the scene YTYPs. Unlike
    ``try_get_asset_metadata_archetype_info``, no Blender object is required, so this resolves entities that only
    carry an archetype name (e.g. map entities without a linked object). Returns ``None`` if no archetype matches.
    """
    info, _ = _resolve_archetype_by_name(archetype_name, cache)
    return info


def try_get_asset_metadata_lights(obj: Object, *, cache: AssetInfoCache | None = None) -> list | None:
    """Return the asset's lights as a list of dicts (same shape as `serialize_lights`). For in-blend assets the lights
    are read from the canonical drawable referenced by the matching scene YTYP archetype's ``asset`` pointer, not from
    ``obj`` itself, since map entities may be duplicates that no longer carry the full data.
    """
    key = _asset_key(obj)
    if cache is not None and key in cache._lights:
        return cache._lights[key]

    result = _resolve_lights(obj, cache)

    if cache is not None:
        cache._lights[key] = result
    return result


def try_get_asset_metadata_collisions(obj: Object, *, cache: AssetInfoCache | None = None) -> dict | None:
    """Return ``{"bb_min": (x, y, z), "bb_max": (x, y, z)}`` for the asset's collision composite, or ``None``."""
    key = _asset_key(obj)
    if cache is not None and key in cache._collisions:
        return cache._collisions[key]

    result = _resolve_collisions(obj, cache)

    if cache is not None:
        cache._collisions[key] = result
    return result


def try_get_asset_metadata_skeleton(obj: Object, *, cache: AssetInfoCache | None = None) -> dict | None:
    """Return the asset's skeleton as a dict ``{"bones": [{"tag": ..., "position": ..., ...}, ...]}`` or ``None``."""
    key = _asset_key(obj)
    if cache is not None and key in cache._skeleton:
        return cache._skeleton[key]

    result = _resolve_skeleton(obj, cache)

    if cache is not None:
        cache._skeleton[key] = result
    return result


def _try_get_asset_metadata_str(obj: Object, key: str) -> str | None:
    info_str = obj.get(key, None)

    if not info_str and obj.data:
        info_str = obj.data.get(key, None)

    if not info_str and obj.instance_type == "COLLECTION" and obj.instance_collection:
        info_str = obj.instance_collection.get(key, None)

    if not info_str and obj.asset_data:
        info_str = obj.asset_data.get(key, None)

    if not info_str and obj.override_library:
        info_str = _try_get_asset_metadata_str(obj.override_library.reference, key)

    return info_str


def _parse_archetype_info(info_str: str) -> AssetArchetypeInfo:
    info_dict = json.loads(info_str)
    return AssetArchetypeInfo(
        ytyp=info_dict.get("ytyp", ""),
        type=info_dict.get("type", ""),
        lod_dist=info_dict.get("lod_dist", -1.0),
        bb_min=Vector(info_dict.get("bb_min", (0.0, 0.0, 0.0))),
        bb_max=Vector(info_dict.get("bb_max", (0.0, 0.0, 0.0))),
        num_extensions=info_dict.get("num_extensions", 0),
        mlo_num_exit_portals=info_dict.get("mlo_num_exit_portals", 0),
    )


def _resolve_via_scene_ytyps(
    obj: Object, cache: AssetInfoCache | None
) -> tuple[AssetArchetypeInfo | None, Object | None]:
    """Find the scene YTYP archetype matching ``obj`` by name (Blender's ``.001`` duplicate suffix stripped)."""
    return _resolve_archetype_by_name(_asset_key(obj), cache)


def _resolve_archetype_by_name(
    name: str, cache: AssetInfoCache | None
) -> tuple[AssetArchetypeInfo | None, Object | None]:
    """Find the scene YTYP archetype named ``name`` (case-insensitive). Returns
    ``(AssetArchetypeInfo, canonical_asset_obj)``, either of which may be ``None``.
    """
    target_name = name.lower()
    if cache is not None and target_name in cache._ytyp_lookup:
        return cache._ytyp_lookup[target_name]

    name_match: tuple | None = None
    for ytyp in bpy.context.scene.ytyps:
        for archetype in ytyp.archetypes:
            if name_match is None and archetype.name.lower() == target_name:
                name_match = (ytyp, archetype)
                break

    if name_match is None:
        result: tuple[AssetArchetypeInfo | None, Object | None] = (None, None)
    else:
        ytyp, archetype = name_match
        try:
            arch_type_name = ArchetypeType(archetype.type).name
        except ValueError:
            arch_type_name = ""
        info = AssetArchetypeInfo(
            ytyp=ytyp.name,
            type=arch_type_name,
            lod_dist=archetype.lod_dist,
            bb_min=Vector(archetype.bb_min),
            bb_max=Vector(archetype.bb_max),
            num_extensions=len(archetype.extensions),
            mlo_num_exit_portals=archetype.calc_num_exit_portals(),
        )
        result = (info, archetype.asset)

    if cache is not None:
        cache._ytyp_lookup[target_name] = result
    return result


def _resolve_lights(obj: Object, cache: AssetInfoCache | None) -> list | None:
    lights_str = _try_get_asset_metadata_str(obj, "sz_asset_lights")
    if lights_str:
        return json.loads(lights_str)

    _, canonical = _resolve_via_scene_ytyps(obj, cache)
    if canonical is None:
        return None

    # Local import to avoid pulling format-specific code into shared/ at module load time.
    from ...ydr.lights_io import export_lights, serialize_lights

    lights = export_lights(canonical)
    if not lights:
        return None

    return serialize_lights(lights)


def _resolve_collisions(obj: Object, cache: AssetInfoCache | None) -> dict | None:
    cols_str = _try_get_asset_metadata_str(obj, "sz_asset_collisions")
    if cols_str:
        return json.loads(cols_str)

    _, canonical = _resolve_via_scene_ytyps(obj, cache)
    if canonical is None:
        return None

    composite = next(
        (c for c in (canonical, *canonical.children_recursive) if c.sollum_type == SollumType.BOUND_COMPOSITE),
        None,
    )
    if composite is None:
        return None

    from ...tools.meshhelper import get_combined_bound_box

    bb_min, bb_max = get_combined_bound_box(composite)
    return {"bb_min": tuple(bb_min), "bb_max": tuple(bb_max)}


def _resolve_skeleton(obj: Object, cache: AssetInfoCache | None) -> dict | None:
    skel_str = _try_get_asset_metadata_str(obj, "sz_asset_skeleton")
    if skel_str:
        return json.loads(skel_str)

    _, canonical = _resolve_via_scene_ytyps(obj, cache)
    if canonical is None or canonical.type != "ARMATURE" or not canonical.pose or not canonical.pose.bones:
        return None

    from ...ydr.ydrexport_io import create_skeleton

    skel = create_skeleton(canonical)
    skel_dict = asdict(skel)
    for bone in skel_dict["bones"]:
        bone.pop("translation_limit")
        bone.pop("rotation_limit")
        for k, v in bone.items():
            if isinstance(v, (Vector, Quaternion)):
                bone[k] = tuple(v)

    return skel_dict
