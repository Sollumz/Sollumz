"""Handle changes between 2.4.0 and 2.5.0."""

import bpy
from bpy.types import (
    BlendData,
    Object,
    Mesh,
)
from ..ytyp.properties.ytyp import (
    CMapTypesProperties
)

from .versioning_230 import get_src_props

def update_lods(obj: Object):
    src_props = get_src_props(obj)
    if src_props is None:
        return

    src_lods_props = src_props.get("sollumz_lods", None)
    if src_lods_props is None:
        return

    src_lods_arr = src_lods_props.get("lods", None)
    if src_lods_arr is None or len(src_lods_arr) == 0:
        return

    # Get LODs from the old property group
    active_lod_index = src_lods_props.get("active_lod_index", -1)
    active_lod_level_int = None

    new_lods = {}
    for i, src_lod_props in enumerate(src_lods_arr):
        lod_level_int = src_lod_props.get("level", -1)
        if not 0 <= lod_level_int <= 4:
            continue

        mesh = src_lod_props.get("mesh", None)
        # In some cases 'mesh' can end up with an empty bpy id prop, ensure that it is a Mesh
        if mesh is None or not isinstance(mesh, Mesh):
            continue

        new_lods[lod_level_int] = mesh
        if i == active_lod_index:
            active_lod_level_int = lod_level_int

    # Delete the old LOD properties
    if bpy.app.version < (5, 0, 0):
        del obj["sollumz_lods"]

    # Create the new LOD properties
    new_lods_props = obj.sz_lods
    if active_lod_level_int is not None:
        from ..lods import LODLevelEnumItems
        active_lod_level_str = LODLevelEnumItems[active_lod_level_int][0]
        new_lods_props.disable_active_lod_level_callback = True
        new_lods_props.active_lod_level = active_lod_level_str
        new_lods_props.active_lod_level_prev = active_lod_level_str
        new_lods_props.disable_active_lod_level_callback = False

    lod_prop_names = [
        # field names in class LODLevels(PropertyGroup)
        "high",       # 0
        "medium",     # 1
        "low",        # 2
        "very_low",   # 3
        "very_high",  # 4
    ]
    for new_lod_level, new_lod_mesh in new_lods.items():
        lod_prop_name = lod_prop_names[new_lod_level]
        new_lod_props = getattr(new_lods_props, lod_prop_name)
        new_lod_props.has_mesh = new_lod_mesh is not None
        if new_lod_level != active_lod_level_int:
            # only non-active LODs keep a reference to the mesh
            new_lod_props.mesh_ref = new_lod_mesh


def update_mlo_tcmods_percentage(ytyp: CMapTypesProperties):
    for arch in ytyp.archetypes_:
        for tcmod in arch.timecycle_modifiers_:
            tcmod_props = get_src_props(tcmod)
            if tcmod_props is None:
                continue

            old_percentage = tcmod_props.get("percentage", None)
            if old_percentage is None:
                continue

            # convert to float
            new_percentage = float(old_percentage)
            new_percentage = max(0.0, min(100.0, new_percentage))
            tcmod.percentage = new_percentage


def add_new_default_light_preset():
    """Adds the new "Default" light preset. Not really part of the .blend data, but this is probably the best place to
    check for this.
    """
    import os
    from ..ydr.properties import get_light_presets_path, get_default_light_presets_path, load_light_presets
    from ..cwxml.light_preset import LightPresetsFile

    user_path = get_light_presets_path()
    if not os.path.exists(user_path):
        # No custom light presets, don't need to do anything, the default light presets file will be loaded
        return

    default_path = get_default_light_presets_path()
    if not os.path.exists(default_path):
        # The default light presets file doesn't exist, worrying but can't do anything about it
        return

    user_presets = LightPresetsFile.from_xml_file(user_path)
    if any(p.name == "Default" for p in user_presets.presets):
        # Already have the "Default" preset
        return

    default_presets = LightPresetsFile.from_xml_file(default_path)
    preset = next((p for p in default_presets.presets if p.name == "Default"), None)
    if preset is None:
        # "Default" preset missing
        return

    user_presets.presets.insert(0, preset)
    user_presets.write_xml(user_path)

    # Refresh presets UI
    load_light_presets()


def convert_constraint_child_of_to_copy_transform(obj: Object):
    from ..tools.blenderhelper import add_child_of_bone_constraint

    child_of_constraints = [
        con for con in obj.constraints
        if (con.type == "CHILD_OF" and
            con.target_space == "POSE" and
            con.owner_space == "LOCAL" and
            con.target is not None and
            con.target.type == "ARMATURE")
    ]
    for con in child_of_constraints:
        armature_obj = con.target
        bone_name = con.subtarget
        obj.constraints.remove(con)
        add_child_of_bone_constraint(obj, armature_obj, bone_name)


def do_versions(data_version: int, data: BlendData):
    if data_version < 2:
        for obj in data.objects:
            update_lods(obj)

    # NOTE: moved to versioning_260 to correctly handle versioning after the multi-select collections
    # if data_version < 3:
    #     for scene in data.scenes:
    #         for ytyp in scene.ytyps:
    #             update_mlo_tcmods_percentage(ytyp)

    if data_version < 4:
        add_new_default_light_preset()

    if data_version < 5:
        for obj in data.objects:
            convert_constraint_child_of_to_copy_transform(obj)
