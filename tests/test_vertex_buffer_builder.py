import pytest
import numpy as np
from numpy.testing import assert_array_equal, assert_allclose
from ..ydr.vertex_buffer_builder import dedupe_and_get_indices
from ..cwxml.drawable import VertexBuffer


def test_dedupe_repeated():
    struct_dtype = [VertexBuffer.VERT_ATTR_DTYPES["Position"], VertexBuffer.VERT_ATTR_DTYPES["Normal"]]
    input_vertex_arr = np.empty(3, dtype=struct_dtype)
    input_vertex_arr["Position"] = [
        [1, 0.5, 0.25],
        [1, 0.5, 0.25],
        [1, 0.5, 0.25],
    ]
    input_vertex_arr["Normal"] = [
        [1, 0, 0],
        [1, 0, 0],
        [1, 0, 0],
    ]

    vertex_arr, ind_arr = dedupe_and_get_indices(input_vertex_arr)

    assert len(vertex_arr) == 1
    assert len(ind_arr) == 3
    assert_array_equal(vertex_arr[ind_arr], input_vertex_arr)


def test_dedupe_different_and_repeated():
    struct_dtype = [VertexBuffer.VERT_ATTR_DTYPES["Position"], VertexBuffer.VERT_ATTR_DTYPES["Normal"]]
    input_vertex_arr = np.empty(6, dtype=struct_dtype)
    input_vertex_arr["Position"] = [
        [1, 0, 2.5],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 2.25],
        [1, 0, 2.5],  # repeated
        [0, 0, 1],   # repeated
    ]
    input_vertex_arr["Normal"] = [
        [1, 0, 0],
        [0, 1, 0],
        [0, 0, 1],
        [1, 0, 0],
        [1, 0, 0],
        [0, 0, 1],
    ]

    vertex_arr, ind_arr = dedupe_and_get_indices(input_vertex_arr)

    assert len(vertex_arr) == 4
    assert len(ind_arr) == 6
    assert_array_equal(vertex_arr[ind_arr], input_vertex_arr)


def test_dedupe_same_integer_different_decimals():
    struct_dtype = [VertexBuffer.VERT_ATTR_DTYPES["Position"]]
    input_vertex_arr = np.empty(3, dtype=struct_dtype)
    input_vertex_arr["Position"] = [
        [1.0, 0, 2.5],
        [1.5, 0, 2.25],
        [1.75, 0, 2.0],
    ]

    vertex_arr, ind_arr = dedupe_and_get_indices(input_vertex_arr)

    assert len(vertex_arr) == 3
    assert len(ind_arr) == 3
    assert_array_equal(vertex_arr[ind_arr], input_vertex_arr)


def test_dedupe_repeated_but_with_rounding_errors():
    # From a real case, Blender calculated these normals and Sollumz wasn't deduplicating them on export
    # Technically different, but the difference is just rounding errors.
    # It was breaking cloth mesh export.
    struct_dtype = [VertexBuffer.VERT_ATTR_DTYPES["Normal"]]
    input_vertex_arr = np.empty(9, dtype=struct_dtype)
    input_vertex_arr["Normal"] = [
        [-1.0, -0.000000087422769468048500129953, -0.000000043711327890605389256962],
        [-1.0, -0.000000087422769468048500129953, -0.000000043711526842571402085014],
        [-1.0, -0.000000087422776573475857730955, -0.000000043711427366588395670988],
        [-1.0, -0.000000087422776573475857730955, -0.000000043711526842571402085014],
        [-1.0, -0.000000087422790784330572932959, -0.000000043711327890605389256962],
        [-1.0, -0.000000087422790784330572932959, -0.000000043711427366588395670988],

        [1.0, 0.0, 0.0],
        [0.9999999, 0.0, 0.0],
        [1.0, 0.0, -0.0000001],
    ]

    vertex_arr, ind_arr = dedupe_and_get_indices(input_vertex_arr)

    assert len(vertex_arr) == 2
    assert len(ind_arr) == 9
    assert_allclose(vertex_arr[ind_arr]["Normal"], input_vertex_arr["Normal"], atol=1e-6)
