import bpy
from pathlib import Path
from ..shared import SOLLUMZ_TEST_VERSIONING_DATA_DIR
from ...versioning import do_versions
from ...sollumz_properties import LODLevel


def data_path(file_name: str) -> Path:
    path = SOLLUMZ_TEST_VERSIONING_DATA_DIR.joinpath(file_name)
    assert path.exists()
    return path


def load_blend_data(data: bpy.types.BlendData, file_name: str):
    with data.libraries.load(str(data_path(file_name))) as (data_from, data_to):
        for attr in dir(data_to):
            setattr(data_to, attr, getattr(data_from, attr))


def test_versioning_lods():
    with bpy.data.temp_data() as temp_data:
        load_blend_data(temp_data, "v240_lods.blend")

        do_versions(temp_data)

        obj = temp_data.objects["Sphere.model"]
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
                assert lod.mesh_ref == temp_data.meshes[mesh_name]
            assert lod.mesh == temp_data.meshes[mesh_name]
            assert lod.mesh_name == mesh_name


def test_versioning_tcmod_percentage():
    with bpy.data.temp_data() as temp_data:
        load_blend_data(temp_data, "v240_tcmod_percentage.blend")

        do_versions(temp_data)

        ytyp = temp_data.scenes[0].ytyps[0]
        mlo = ytyp.archetypes[0]
        tcmod = mlo.timecycle_modifiers[0]
        assert tcmod.percentage == 75.0


def test_versioning_convert_child_of_to_copy_transform():
    # NOTE: cannot use temp_data() here, constraints don't accept temporary IDs
    # >       constraint.target = armature_obj
    # E       TypeError: bpy_struct: item.attr = val: CopyTransformsConstraint.target ID type assignment is temporary, can't assign
    data = bpy.data
    load_blend_data(data, "v240_child_of_to_copy_transform.blend")

    do_versions(data)


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
