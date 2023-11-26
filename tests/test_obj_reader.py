import bpy
import pytest
import numpy as np
from numpy.testing import assert_array_equal
from pathlib import Path
from ..shared.obj_reader import obj_read_from_str, obj_read_from_file, ObjMesh


def test_obj_read():
    obj = obj_read_from_str("""
        v 1.2 3.4 5.6
        v 2.0 4.0 6.0
        v 10.0 5.0 10.0
        v 1.0 2.0 3.0
        f 1 2 3
        f 4 3 1
    """)

    assert obj is not None

    assert_array_equal(obj.vertices, np.array([
        [1.2, 3.4, 5.6],
        [2.0, 4.0, 6.0],
        [10.0, 5.0, 10.0],
        [1.0, 2.0, 3.0],
    ], dtype=np.float32))

    assert_array_equal(obj.indices, np.array([
        [0, 1, 2],
        [3, 2, 0],
    ], dtype=np.uint16))


def test_obj_read_ignores_comments_and_unknown_elements():
    obj = obj_read_from_str("""
        # comment
        v 1.0 2.0 3.0
        # other comment
        u unknown
        f 1 2 3
    """)

    assert obj is not None

    assert_array_equal(obj.vertices, np.array([
        [1.0, 2.0, 3.0],
    ], dtype=np.float32))

    assert_array_equal(obj.indices, np.array([
        [0, 1, 2],
    ], dtype=np.uint16))


def test_obj_as_vertices_only():
    obj_mesh = ObjMesh(
        vertices=np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0],
        ], dtype=np.float32),
        indices=np.array([
            [0, 1, 2],
            [2, 1, 0],
        ], dtype=np.uint16)
    )

    obj_mesh_vertices = obj_mesh.as_vertices_only()
    assert_array_equal(obj_mesh_vertices, np.array([
        [1.0, 2.0, 3.0],
        [4.0, 5.0, 6.0],
        [7.0, 8.0, 9.0],
        [7.0, 8.0, 9.0],
        [4.0, 5.0, 6.0],
        [1.0, 2.0, 3.0],
    ]))


@pytest.mark.parametrize("obj_relative_file_path", (
    "../tools/car_model.obj",
    "../ytyp/gizmos/models/AudioEmitter.obj",
    "../ytyp/gizmos/models/AudioCollisionSettings.obj",
    "../ytyp/gizmos/models/Buoyancy.obj",
    "../ytyp/gizmos/models/Door.obj",
    "../ytyp/gizmos/models/Expression.obj",
    "../ytyp/gizmos/models/Ladder.obj",
    "../ytyp/gizmos/models/LadderTop.obj",
    "../ytyp/gizmos/models/LadderBottom.obj",
    "../ytyp/gizmos/models/LightShaft.obj",
    "../ytyp/gizmos/models/ParticleEffect.obj",
    "../ytyp/gizmos/models/ProcObject.obj",
    "../ytyp/gizmos/models/SpawnPoint.obj",
    "../ytyp/gizmos/models/SpawnPointOverride.obj",
    "../ytyp/gizmos/models/WindDisturbance.obj",
))
def test_obj_read_sollumz_builtin_asset(obj_relative_file_path: str):
    obj_path = Path(__file__).parent.joinpath(obj_relative_file_path)
    obj = obj_read_from_file(obj_path)

    assert obj is not None
    assert len(obj.vertices.flatten()) > 0
    assert len(obj.indices.flatten()) > 0

    obj_mesh = obj.as_bpy_mesh(obj_path.stem)
    assert obj_mesh is not None

    invalid_geom = obj_mesh.validate(verbose=True)
    assert not invalid_geom

    bpy.data.meshes.remove(obj_mesh)
