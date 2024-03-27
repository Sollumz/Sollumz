import pytest
import numpy as np
from numpy.testing import assert_allclose
from typing import NamedTuple, Optional
from pathlib import Path
from functools import cache
from xml.etree import ElementTree as ET
from .shared import is_tmp_dir_available, tmp_path, glob_assets
from ..yft.yftimport import import_yft
from ..yft.yftexport import export_yft


def elem_to_vec(e: ET.Element):
    """Gets the `x`, `y` and `z` attributes values as a numpy array."""
    return np.array([float(e.get(k)) for k in ("x", "y", "z")])


def elem_to_vec4(e: ET.Element):
    """Gets the `x`, `y`, `z` and `w` attributes values as a numpy array."""
    return np.array([float(e.get(k)) for k in ("x", "y", "z", "w")])


def elem_to_float(e: ET.Element):
    """Gets the `value` attribute value as a numpy array."""
    return np.array([float(e.get("value"))])

def elem_to_vec_list(e: ET.Element):
    return np.fromstring(e.text.replace(", ", " ").replace("\n", " "), dtype=np.float32, sep=" ").reshape((-1, 3))


class YftFileTestCase(NamedTuple):
    input_path: Path
    input_root: ET.Element
    output_path: Path
    output_root: ET.Element

    @property
    def test_id(self) -> str:
        return self.input_path.stem


class YftTestCase(NamedTuple):
    # File specific data
    input_path: Path
    input_root: ET.Element
    output_path: Path
    output_root: ET.Element
    # Test case specific data (test case per physics child)
    child_key: tuple[str, int, str]  # (group name, bone tag, bound type)
    input_bound: ET.Element
    input_child: ET.Element
    input_link_attachment: ET.Element
    output_bound: ET.Element
    output_child: ET.Element
    output_link_attachment: ET.Element

    @property
    def test_id(self) -> str:
        child_key_str = "-".join(map(str, self.child_key))
        return f"{self.input_path.stem}-{child_key_str}"

    @property
    def is_root_composite(self) -> bool:
        return self.child_key[0] == "$root_composite"


if is_tmp_dir_available():  # need the temp directory to store exported .yfts

    @cache
    def get_yft_test_cases() -> tuple[list[YftFileTestCase], list[YftTestCase]]:
        """Imports and export all .yft assets available. Returns two lists of test cases with the parsed input and
        output XMLs. First list is per .yft file; and the second list, per .yft physics child.

        This function is cached, so only the first call does the actual import/export process inside Blender.
        """

        file_test_cases = []
        test_cases = []
        for yft_path, yft_path_str in glob_assets("yft"):
            if "sollumz_cube" in yft_path_str:  # has properties calculated with the old method, disabled until the model is updated
                continue

            if yft_path_str.endswith("_hi.yft.xml"):
                continue

            obj = import_yft(yft_path_str)
            assert obj is not None

            out_path = tmp_path(yft_path.name, "export_physics_properties_yfts")
            success = export_yft(obj, str(out_path))
            assert success
            assert out_path.exists()

            input_tree = ET.ElementTree()
            input_tree.parse(yft_path)
            input_root = input_tree.getroot()

            output_tree = ET.ElementTree()
            output_tree.parse(out_path)
            output_root = output_tree.getroot()

            XPATH_BOUND_COMPOSITE = "./Physics/LOD1/Archetype/Bounds"
            XPATH_BOUNDS = "./Physics/LOD1/Archetype/Bounds/Children/Item"
            XPATH_GROUPS = "./Physics/LOD1/Groups/Item"
            XPATH_CHILDREN = "./Physics/LOD1/Children/Item"
            XPATH_LINK_ATTACHMENTS = "./Physics/LOD1/Transforms/Item"

            input_composite = input_root.find(XPATH_BOUND_COMPOSITE)
            input_bounds = input_root.findall(XPATH_BOUNDS)
            output_composite = input_root.find(XPATH_BOUND_COMPOSITE)
            output_bounds = output_root.findall(XPATH_BOUNDS)

            input_groups = input_root.findall(XPATH_GROUPS)
            input_children = input_root.findall(XPATH_CHILDREN)
            input_link_attachments = input_root.findall(XPATH_LINK_ATTACHMENTS)
            output_groups = output_root.findall(XPATH_GROUPS)
            output_children = output_root.findall(XPATH_CHILDREN)
            output_link_attachments = output_root.findall(XPATH_LINK_ATTACHMENTS)

            assert len(input_bounds) == len(output_bounds), "Different number of bounds"

            def _build_children_mapping(groups, children, bounds):
                # Not a perfect mapping, there can be multiple children in the same group and for the same bone.
                # Included bound type in key to try making it more unique.
                # Should be good enough for now...
                # TODO: might want to check for duplicate keys and remove them from the mapping in that case, to
                #       skip those children and avoid testing cases where we might be comparing different bounds
                mapping = {}
                for child_index, child in enumerate(children):
                    bone_tag = int(child.find("BoneTag").get("value"))
                    group_index = int(child.find("GroupIndex").get("value"))
                    group_name = groups[group_index].find("Name").text
                    bound_type = bounds[child_index].get("type")
                    child_key = (group_name, bone_tag, bound_type)
                    mapping[child_key] = child_index
                return mapping

            input_children_mapping = _build_children_mapping(input_groups, input_children, input_bounds)
            output_children_mapping = _build_children_mapping(output_groups, output_children, output_bounds)

            for child_key in input_children_mapping.keys():
                input_child_index = input_children_mapping[child_key]
                output_child_index = output_children_mapping[child_key]

                test_cases.append(YftTestCase(
                    input_path=yft_path,
                    input_root=input_root,
                    output_path=out_path,
                    output_root=output_root,
                    child_key=child_key,
                    input_bound=input_bounds[input_child_index],
                    input_child=input_children[input_child_index],
                    input_link_attachment=input_link_attachments[input_child_index],
                    output_bound=output_bounds[output_child_index],
                    output_child=output_children[output_child_index],
                    output_link_attachment=output_link_attachments[output_child_index],
                ))

            test_cases.append(YftTestCase(
                input_path=yft_path,
                input_root=input_root,
                output_path=out_path,
                output_root=output_root,
                child_key=("$root_composite", -1, "Composite"),
                input_bound=input_composite,
                input_child=None,
                input_link_attachment=None,
                output_bound=output_composite,
                output_child=None,
                output_link_attachment=None,
            ))

            file_test_cases.append(YftFileTestCase(
                input_path=yft_path,
                input_root=input_root,
                output_path=out_path,
                output_root=output_root,
            ))

        return file_test_cases, test_cases

    def pytest_generate_tests(metafunc):
        """Parametrizes fixtures used in this module by the test cases generated by ``get_yft_test_cases``."""

        has_yft_file_test_case = "yft_file_test_case" in metafunc.fixturenames
        has_yft_test_case = "yft_test_case" in metafunc.fixturenames
        has_yft_test_case_geometry_only = "yft_test_case_geometry_only" in metafunc.fixturenames
        if (not has_yft_file_test_case and not has_yft_test_case and not has_yft_test_case_geometry_only):
            return

        yft_file_test_cases, yft_test_cases = get_yft_test_cases()

        if has_yft_file_test_case:
            argvalues = yft_file_test_cases
            ids = [t.test_id for t in argvalues]
            metafunc.parametrize("yft_file_test_case", argvalues, ids=ids, scope="class")

        if has_yft_test_case:
            argvalues = yft_test_cases
            ids = [t.test_id for t in argvalues]
            metafunc.parametrize("yft_test_case", argvalues, ids=ids, scope="class")

        if has_yft_test_case_geometry_only:
            argvalues = [t for t in yft_test_cases if t.child_key[2] in {"Geometry", "GeometryBVH"}]
            ids = [t.test_id for t in argvalues]
            metafunc.parametrize("yft_test_case_geometry_only", argvalues, ids=ids, scope="class")

    atol = 1e-3  # Absolute tolerance used in tests

    ##### Test Functions #####

    def test_yft_bound_centroid(yft_test_case: YftTestCase):
        input_bound = yft_test_case.input_bound
        output_bound = yft_test_case.output_bound

        input_centroid = elem_to_vec(input_bound.find("BoxCenter"))
        output_centroid = elem_to_vec(output_bound.find("BoxCenter"))
        assert_allclose(
            output_centroid, input_centroid,
            atol=atol,
            err_msg=(f"Calculated centroid does not match original.\n"
                     f"   diff={output_centroid - input_centroid}")
        )

    def test_yft_bound_radius(yft_test_case: YftTestCase):
        input_bound = yft_test_case.input_bound
        output_bound = yft_test_case.output_bound

        input_radius = elem_to_float(input_bound.find("SphereRadius"))
        output_radius = elem_to_float(output_bound.find("SphereRadius"))
        assert_allclose(
            output_radius, input_radius,
            atol=atol,
            err_msg=(f"Calculated radius around centroid does not match original.\n"
                     f"   diff={output_radius - input_radius}")
        )

    def test_yft_bound_center_of_gravity(yft_test_case: YftTestCase):
        input_bound = yft_test_case.input_bound
        output_bound = yft_test_case.output_bound

        input_cg = elem_to_vec(input_bound.find("SphereCenter"))
        output_cg = elem_to_vec(output_bound.find("SphereCenter"))
        assert_allclose(
            output_cg, input_cg,
            atol=atol,
            err_msg=(f"Calculated CG does not match original.\n"
                     f"   diff={output_cg - input_cg}")
        )

    def test_yft_bound_volume(yft_test_case: YftTestCase):
        input_bound = yft_test_case.input_bound
        output_bound = yft_test_case.output_bound

        input_volume = elem_to_float(input_bound.find("Volume"))
        output_volume = elem_to_float(output_bound.find("Volume"))
        assert_allclose(
            output_volume, input_volume,
            atol=atol,
            err_msg=(f"Calculated volume does not match original.\n"
                     f"   diff={output_volume - input_volume}")
        )

    def test_yft_bound_inertia(yft_test_case: YftTestCase):
        input_bound = yft_test_case.input_bound
        output_bound = yft_test_case.output_bound

        input_inertia = elem_to_vec(input_bound.find("Inertia"))
        output_inertia = elem_to_vec(output_bound.find("Inertia"))
        assert_allclose(
            output_inertia, input_inertia,
            atol=atol,
            err_msg=(f"Calculated inertia does not match original.\n"
                     f"   diff={output_inertia - input_inertia}")
        )

    def test_yft_bound_margin(yft_test_case: YftTestCase):
        input_bound = yft_test_case.input_bound
        output_bound = yft_test_case.output_bound

        input_margin = elem_to_float(input_bound.find("Margin"))
        output_margin = elem_to_float(output_bound.find("Margin"))
        assert_allclose(
            output_margin, input_margin,
            atol=atol,
            err_msg=(f"Calculated margin does not match original.\n"
                     f"   diff={output_margin - input_margin}")
        )

    def test_yft_bound_geometry_bb_center(yft_test_case_geometry_only: YftTestCase):
        input_bound = yft_test_case_geometry_only.input_bound
        output_bound = yft_test_case_geometry_only.output_bound

        input_bb_center = elem_to_vec(input_bound.find("GeometryCenter"))
        output_bb_center = elem_to_vec(output_bound.find("GeometryCenter"))

        assert_allclose(
            input_bb_center, output_bb_center,
            atol=atol,
            err_msg=(f"Calculated geometry bounding-box center does not match original.\n"
                     f"   diff={output_bb_center - input_bb_center}")
        )

    def test_yft_bound_geometry_vertices(yft_test_case_geometry_only: YftTestCase):
        input_bound = yft_test_case_geometry_only.input_bound
        output_bound = yft_test_case_geometry_only.output_bound

        input_bb_center = elem_to_vec(input_bound.find("GeometryCenter"))
        output_bb_center = elem_to_vec(output_bound.find("GeometryCenter"))

        input_vertices = elem_to_vec_list(input_bound.find("Vertices"))
        output_vertices = elem_to_vec_list(output_bound.find("Vertices"))

        input_vertices += input_bb_center
        output_vertices += output_bb_center

        assert len(input_vertices) == len(output_vertices)

        # Output vertices could appear in a different order.
        # Map the input vertices to the closest output vertex
        input_to_output_index_map = [-1] * len(input_vertices)
        outputs_mapped = set()
        for input_idx, input_vertex in enumerate(input_vertices):
            min_dist = 9999999.9
            for output_idx, output_vertex in enumerate(output_vertices):
                dist = np.linalg.norm(input_vertex - output_vertex)
                if dist < min_dist:
                    min_dist = dist
                    input_to_output_index_map[input_idx] = output_idx

            output_idx = input_to_output_index_map[input_idx]
            assert output_idx != -1, f"Input vertex #{input_idx} unmapped in output vertices"
            assert output_idx not in outputs_mapped, \
                   f"Output vertex #{input_to_output_index_map[input_idx]} maps to multiple input vertices"
            outputs_mapped.add(output_idx)

            closest_output_vertex = output_vertices[output_idx]
            assert_allclose(
                input_vertex, closest_output_vertex,
                atol=atol,
                err_msg=(f"Calculated geometry vertex (in={input_idx}, out={output_idx}) "
                          "does not match original.\n"
                         f"   diff={closest_output_vertex - input_vertex}")
            )

        if input_bound.find("VerticesShrunk") is not None and output_bound.find("VerticesShrunk") is not None:
            # Requires custom CW build that exports shrunk vertices
            input_vertices_shrunk = elem_to_vec_list(input_bound.find("VerticesShrunk"))
            output_vertices_shrunk = elem_to_vec_list(output_bound.find("VerticesShrunk"))
            for input_idx, output_idx in enumerate(input_to_output_index_map):
                input_vertex_shrunk = input_vertices_shrunk[input_idx]
                output_vertex_shrunk = output_vertices_shrunk[output_idx]
                s_atol = 0.5
                assert_allclose(
                    input_vertex_shrunk, output_vertex_shrunk,
                    atol=s_atol,
                    err_msg=(f"Calculated geometry shrunk vertex (in={input_idx}, out={output_idx}) "
                              "does not match original.\n"
                             f"   diff={output_vertex_shrunk - input_vertex_shrunk}")
                )



    def test_yft_link_attachment(yft_test_case: YftTestCase):
        if yft_test_case.is_root_composite:
            return

        input_link_attachment = yft_test_case.input_link_attachment
        output_link_attachment = yft_test_case.output_link_attachment

        input_values = np.fromstring(input_link_attachment.text, dtype=np.float32, sep=" ")
        output_values = np.fromstring(output_link_attachment.text, dtype=np.float32, sep=" ")

        input_values = input_values.reshape((4, 4))
        output_values = output_values.reshape((4, 4))

        mismatched = ~np.isclose(output_values, input_values, atol=atol)
        assert_allclose(
            output_values, input_values,
            atol=atol,
            err_msg=(f"Calculated link attachment does not match original.\n"
                     f"   {input_values=}\n"
                     f"   {output_values=}\n"
                     f"   {mismatched=}\n"
                     f"   {input_values[mismatched]=}\n"
                     f"   {output_values[mismatched]=}\n"
                     f"   diff={output_values[mismatched] - input_values[mismatched]}")
        )

    def test_yft_child_inertia(yft_test_case: YftTestCase):
        if yft_test_case.is_root_composite:
            return

        input_child = yft_test_case.input_child
        output_child = yft_test_case.output_child

        input_inertia = elem_to_vec4(input_child.find("InertiaTensor"))
        output_inertia = elem_to_vec4(output_child.find("InertiaTensor"))
        assert_allclose(
            output_inertia, input_inertia,
            atol=atol,
            err_msg=(f"Calculated child inertia does not match original.\n"
                     f"   diff={output_inertia - input_inertia}")
        )

    def test_yft_root_cg_offset(yft_file_test_case: YftFileTestCase):
        XPATH_ROOT_CG_OFFSET = "./Physics/LOD1/PositionOffset"

        input_root = yft_file_test_case.input_root
        output_root = yft_file_test_case.output_root

        input_root_cg_offset = elem_to_vec(input_root.find(XPATH_ROOT_CG_OFFSET))
        output_root_cg_offset = elem_to_vec(output_root.find(XPATH_ROOT_CG_OFFSET))

        assert_allclose(
            output_root_cg_offset, input_root_cg_offset,
            atol=atol,
            err_msg=(f"Calculated root CG offset does not match original.\n"
                     f"   diff={output_root_cg_offset - input_root_cg_offset}")
        )

    def test_yft_smallest_largest_ang_inertia(yft_file_test_case: YftFileTestCase):
        XPATH_SMALLEST_ANG_INERTIA = "./Physics/LOD1/Unknown14"
        XPATH_LARGEST_ANG_INERTIA = "./Physics/LOD1/Unknown18"

        input_root = yft_file_test_case.input_root
        output_root = yft_file_test_case.output_root

        input_smallest_ang_inertia = elem_to_float(input_root.find(XPATH_SMALLEST_ANG_INERTIA))
        input_largest_ang_inertia = elem_to_float(input_root.find(XPATH_LARGEST_ANG_INERTIA))
        output_smallest_ang_inertia = elem_to_float(output_root.find(XPATH_SMALLEST_ANG_INERTIA))
        output_largest_ang_inertia = elem_to_float(output_root.find(XPATH_LARGEST_ANG_INERTIA))

        assert_allclose(
            output_smallest_ang_inertia, input_smallest_ang_inertia,
            atol=atol,
            err_msg=(f"Calculated smallest angular inertia does not match original.\n"
                     f"   diff={output_smallest_ang_inertia - input_smallest_ang_inertia}")
        )
        assert_allclose(
            output_largest_ang_inertia, input_largest_ang_inertia,
            atol=atol,
            err_msg=(f"Calculated largest angular inertia does not match original.\n"
                     f"   diff={output_largest_ang_inertia - input_largest_ang_inertia}")
        )

    def test_yft_archetype_inertia(yft_file_test_case: YftFileTestCase):
        XPATH_ARCH_INERTIA = "./Physics/LOD1/Archetype/InertiaTensor"
        XPATH_ARCH_INERTIA_INV = "./Physics/LOD1/Archetype/InertiaTensorInv"

        input_root = yft_file_test_case.input_root
        output_root = yft_file_test_case.output_root

        input_inertia = elem_to_vec(input_root.find(XPATH_ARCH_INERTIA))
        input_inertia_inv = elem_to_vec(input_root.find(XPATH_ARCH_INERTIA_INV))
        output_inertia = elem_to_vec(output_root.find(XPATH_ARCH_INERTIA))
        output_inertia_inv = elem_to_vec(output_root.find(XPATH_ARCH_INERTIA_INV))

        assert_allclose(
            output_inertia, input_inertia,
            atol=atol,
            err_msg=(f"Calculated archetype inertia does not match original.\n"
                     f"   diff={output_inertia - input_inertia}")
        )
        assert_allclose(
            output_inertia_inv, input_inertia_inv,
            atol=atol,
            err_msg=(f"Calculated archetype inertia does not match original.\n"
                     f"   diff={output_inertia_inv - input_inertia_inv}")
        )
