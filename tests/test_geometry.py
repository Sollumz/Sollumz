import pytest
import numpy as np
from ..shared.geometry import shrink_mesh
from .shared import SOLLUMZ_TEST_ASSETS_DIR

def read_shrink_mesh_test_data(file_path):
    with open(file_path) as f:
        input_vertices_str = f.readline()
        input_indices_str = f.readline()
        expected_vertices_str = f.readline()
        expected_margin_str = f.readline()

        input_vertices = np.fromstring(input_vertices_str, dtype=np.float32, sep=" ").reshape((-1, 3))
        input_indices = np.fromstring(input_indices_str, dtype=np.uint32, sep=" ").reshape((-1, 3))
        expected_vertices = np.fromstring(expected_vertices_str, dtype=np.float32, sep=" ").reshape((-1, 3))
        expected_margin = float(expected_margin_str)

        return input_vertices, input_indices, expected_vertices, expected_margin


@pytest.mark.parametrize("test_data_file_name", (
    "shrink_mesh_test_data_000.txt",
    "shrink_mesh_test_data_001.txt",
))
def test_geometry_shrink_mesh(test_data_file_name):
    test_data_file_path = SOLLUMZ_TEST_ASSETS_DIR.joinpath(test_data_file_name)
    input_vertices, input_indices, expected_vertices, expected_margin = read_shrink_mesh_test_data(test_data_file_path)

    output_vertices, output_margin = shrink_mesh(input_vertices, input_indices)

    assert len(output_vertices) == len(input_vertices)
    assert len(output_vertices) == len(expected_vertices)
    assert abs(output_margin - expected_margin) <= 1e-3, "Shrunk mesh margin does not match expected margin."

    n = 0
    s = "\n"
    for vertex_idx, (expected_vertex, output_vertex) in enumerate(zip(expected_vertices, output_vertices)):
        if not np.allclose(expected_vertex, output_vertex, atol=1e-3):
            n += 1
            s += (f"Shrunk vertex #{vertex_idx} does not match expected vertex.\n"
                  f"   diff={output_vertex - expected_vertex}\n")

    assert n == 0, f"{n} / {len(output_vertices)}{s}"
