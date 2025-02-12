from .shared import load_blend_data
from ...sollumz_properties import LODLevel


def test_versioning_lods():
    data = load_blend_data("v240_lods.blend")

    obj = data.objects["Sphere.model"]
    lods = obj.sz_lods

    assert lods.active_lod_level == LODLevel.VERYHIGH
    assert lods.active_lod_level_prev == LODLevel.VERYHIGH
    for lod_level, mesh_name in (
        (LODLevel.VERYHIGH, "Sphere.very_high"),
        (LODLevel.HIGH, "Sphere.high"),
        (LODLevel.MEDIUM, "Sphere.med"),
        (LODLevel.LOW, "Sphere.low"),
        (LODLevel.VERYLOW, "Sphere.very_low"),
    ):
        lod = lods.get_lod(lod_level)
        assert lod.has_mesh
        if lod_level == LODLevel.VERYHIGH:
            assert lod.mesh_ref is None  # active LOD, no ref
        else:
            assert lod.mesh_ref == data.meshes[mesh_name]
        assert lod.mesh == data.meshes[mesh_name]
        assert lod.mesh_name == mesh_name


def test_versioning_tcmod_percentage():
    data = load_blend_data("v240_tcmod_percentage.blend")

    ytyp = data.scenes[0].ytyps[0]
    mlo = ytyp["archetypes_"][0]
    tcmod = mlo["timecycle_modifiers_"][0]
    assert isinstance(tcmod["percentage"], float)
    assert tcmod["percentage"] == 75.0


def test_versioning_convert_child_of_to_copy_transform():
    data = load_blend_data("v240_child_of_to_copy_transform.blend")

    armature_obj = data.objects["dummy_prop"]
    objs_to_check = (
        # object name, target bone name
        ("the_root_mesh", "the_root"),
        ("the_bone_mesh", "the_bone"),
        ("the_root_mesh.col", "the_root"),
        ("the_root_mesh.col.001", "the_root"),
        ("the_bone_mesh.col", "the_bone"),
    )
    for obj_name, target_bone_name in objs_to_check:
        obj = data.objects[obj_name]
        assert len(obj.constraints) == 1
        con = obj.constraints[0]
        assert con.type == "COPY_TRANSFORMS"
        assert con.target == armature_obj
        assert con.subtarget == target_bone_name
