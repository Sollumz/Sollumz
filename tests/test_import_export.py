from pathlib import Path
from xml.etree import ElementTree as ET

import bpy
import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_equal

from ..ybn.ybnexport import export_ybn
from ..ybn.ybnimport import import_ybn
from ..ycd.ycdexport import export_ycd
from ..ycd.ycdimport import import_ycd
from ..ydr.ydrexport import export_ydr
from ..ydr.ydrimport import import_ydr
from ..yft.yftexport import export_yft
from ..yft.yftimport import import_yft
from .shared import (
    assert_logs_no_warnings_or_errors,
    asset_path,
    data_path,
    glob_assets,
    is_tmp_dir_available,
    load_blend_data,
    requires_szio_native,
)
from .shared import (
    tmp_path as tmp_path_with_subdir,
)

if is_tmp_dir_available():
    def tmp_path(file_name: str) -> Path:
        return tmp_path_with_subdir(file_name, "import_export")

    @pytest.mark.parametrize("ydr_path, ydr_path_str", glob_assets("ydr"))
    def test_import_export_ydr(ydr_path: Path, ydr_path_str: str):
        obj = import_ydr(ydr_path_str)
        assert obj is not None

        out_path = tmp_path(ydr_path.name)
        success = export_ydr(obj, str(out_path))
        assert success
        assert out_path.exists()

    @pytest.mark.parametrize("yft_path, yft_path_str", glob_assets("yft"))
    def test_import_export_yft(yft_path: Path, yft_path_str: str):
        obj = import_yft(yft_path_str)
        assert obj is not None

        out_path = tmp_path(yft_path.name)
        success = export_yft(obj, str(out_path))
        assert success
        assert out_path.exists()

    @pytest.mark.parametrize("ybn_path, ybn_path_str", glob_assets("ybn"))
    def test_import_export_ybn(ybn_path: Path, ybn_path_str: str):
        obj = import_ybn(ybn_path_str)
        assert obj is not None

        out_path = tmp_path(ybn_path.name)
        success = export_ybn(obj, str(out_path))
        assert success
        assert out_path.exists()

    @pytest.mark.parametrize("ycd_path, ycd_path_str", glob_assets("ycd"))
    def test_import_export_ycd(ycd_path: Path, ycd_path_str: str):
        obj = import_ycd(ycd_path_str)
        assert obj is not None

        out_path = tmp_path(ycd_path.name)
        success = export_ycd(obj, str(out_path))
        assert success
        assert out_path.exists()

    # FPS settings equal or greater may output more frames than the original input file had.
    # This is expected because the created action will be longer (more frames) to reach
    # the defined duration at the given FPS. Tests will skip some checks in those cases.
    YCD_MAX_FPS_TO_CHECK_FRAME_COUNTS = 29.97

    def test_import_export_ycd_roundtrip_consistency_num_frames_and_duration(fps_dependent):
        ycd_path = asset_path("roundtrip_anim.ycd.xml")

        def _check_exported_ycd(path: Path):
            tree = ET.ElementTree()
            tree.parse(path)
            root = tree.getroot()

            start_times = [float(e.attrib["value"]) for e in root.findall("./Clips/Item/StartTime")]
            end_times = [float(e.attrib["value"]) for e in root.findall("./Clips/Item/EndTime")]
            rates = [float(e.attrib["value"]) for e in root.findall("./Clips/Item/Rate")]
            frame_counts = [int(e.attrib["value"]) for e in root.findall("./Animations/Item/FrameCount")]
            durations = [float(e.attrib["value"]) for e in root.findall("./Animations/Item/Duration")]

            # values from original roundtrip_anim.ycd.xml
            args = {"rtol": 1e-5, "err_msg": f"Roundtrip output '{path}' does not match original."}
            assert_allclose(start_times, [0.0, 13.33333], **args)
            assert_allclose(end_times, [13.3, 16.63333], **args)
            assert_allclose(rates, [1.0, 1.0], **args)
            if fps_dependent[0] < YCD_MAX_FPS_TO_CHECK_FRAME_COUNTS:
                assert_equal(frame_counts, [501], err_msg=args["err_msg"])
            assert_allclose(durations, [16.66666], **args)

        NUM_ROUNDTRIPS = 5
        curr_input_path = ycd_path
        for roundtrip in range(NUM_ROUNDTRIPS):
            obj = import_ycd(str(curr_input_path))
            assert obj is not None

            out_path = tmp_path(f"roundtrip_anim_{fps_dependent[1]}_{roundtrip}.ycd.xml")
            success = export_ycd(obj, str(out_path))
            assert success
            assert out_path.exists()

            _check_exported_ycd(out_path)

            curr_input_path = out_path

    def test_import_export_ycd_roundtrip_consistency_frame_values(fps_dependent):
        if fps_dependent[0] >= YCD_MAX_FPS_TO_CHECK_FRAME_COUNTS:
            # we check a array with length equal to the frame count, so cannot do this test with high FPS
            return

        ycd_path = asset_path("roundtrip_anim_values.ycd.xml")

        XPATH_QUANTIZE_FLOAT_CHANNEL = "./Animations/Item/Sequences/Item/SequenceData/Item/Channels/Item"

        orig_tree = ET.ElementTree()
        orig_tree.parse(ycd_path)
        orig_root = orig_tree.getroot()
        orig_quantize_float_channel = orig_root.find(XPATH_QUANTIZE_FLOAT_CHANNEL)
        orig_values = np.fromstring(orig_quantize_float_channel.find("Values").text, dtype=np.float32, sep=" ")
        assert len(orig_values) == 30  # quick check to verify we are reading the XML contents correctly
        orig_quantum = float(orig_quantize_float_channel.find("Quantum").attrib["value"])
        orig_offset = float(orig_quantize_float_channel.find("Offset").attrib["value"])

        def _check_exported_ycd(path: Path):
            tree = ET.ElementTree()
            tree.parse(path)
            root = tree.getroot()

            quantize_float_channel = root.find(XPATH_QUANTIZE_FLOAT_CHANNEL)
            values = np.fromstring(quantize_float_channel.find("Values").text, dtype=np.float32, sep=" ")
            quantum = float(quantize_float_channel.find("Quantum").attrib["value"])
            offset = float(quantize_float_channel.find("Offset").attrib["value"])

            args = {"rtol": 1e-5, "err_msg": f"Roundtrip output '{path}' does not match original."}
            assert_allclose(values, orig_values, **args)
            assert_allclose(quantum, orig_quantum, **args)
            assert_allclose(offset, orig_offset, **args)

        NUM_ROUNDTRIPS = 5
        curr_input_path = ycd_path
        for roundtrip in range(NUM_ROUNDTRIPS):
            obj = import_ycd(str(curr_input_path))
            assert obj is not None

            out_path = tmp_path(f"roundtrip_anim_values_{fps_dependent[1]}_{roundtrip}.ycd.xml")
            success = export_ycd(obj, str(out_path))
            assert success
            assert out_path.exists()

            _check_exported_ycd(out_path)

            curr_input_path = out_path

    def test_import_export_ycd_roundtrip_consistency_clip_anim_list(fps_dependent):
        ycd_path = asset_path("roundtrip_anim_clip_anim_list.ycd.xml")

        def _check_exported_ycd(path: Path):
            tree = ET.ElementTree()
            tree.parse(path)
            root = tree.getroot()

            clip_durations = [float(e.attrib["value"]) for e in root.findall("./Clips/Item/Duration")]
            start_times = [float(e.attrib["value"]) for e in root.findall("./Clips/Item/Animations/Item/StartTime")]
            end_times = [float(e.attrib["value"]) for e in root.findall("./Clips/Item/Animations/Item/EndTime")]
            rates = [float(e.attrib["value"]) for e in root.findall("./Clips/Item/Animations/Item/Rate")]
            frame_counts = [int(e.attrib["value"]) for e in root.findall("./Animations/Item/FrameCount")]
            durations = [float(e.attrib["value"]) for e in root.findall("./Animations/Item/Duration")]

            # values from original roundtrip_anim_clip_anim_list.ycd.xml
            args = {"rtol": 1e-5, "err_msg": f"Roundtrip output '{path}' does not match original."}
            assert_allclose(clip_durations, [1.33333], **args)
            assert_allclose(start_times, [9.966667, 7.3], **args)
            assert_allclose(end_times, [11.3, 8.7], **args)
            assert_allclose(rates, [1.0, 1.05], **args)
            if fps_dependent[0] < YCD_MAX_FPS_TO_CHECK_FRAME_COUNTS:
                assert_equal(frame_counts, [709, 551], err_msg=args["err_msg"])
            assert_allclose(durations, [23.6, 22.0], **args)

        NUM_ROUNDTRIPS = 5
        curr_input_path = ycd_path
        for roundtrip in range(NUM_ROUNDTRIPS):
            obj = import_ycd(str(curr_input_path))
            assert obj is not None

            out_path = tmp_path(f"roundtrip_anim_clip_anim_list_{fps_dependent[1]}_{roundtrip}.ycd.xml")
            success = export_ycd(obj, str(out_path))
            assert success
            assert out_path.exists()

            _check_exported_ycd(out_path)

            curr_input_path = out_path


@pytest.mark.parametrize("files, expected_deduped_files", (
    ([], []),
    (["test.ydr.xml", "test2.ydr"], ["test.ydr.xml", "test2.ydr"]),
    (["test.yft.xml", "test2.yft"], ["test.yft.xml", "test2.yft"]),
    (["test_hi.yft.xml", "test.yft.xml"], ["test.yft.xml"]),
    (["test_hi.yft.xml", "test.yft"], ["test.yft"]),
    (["test_hi.yft", "test.yft.xml"], ["test.yft.xml"]),
    (["test_hi.yft", "test.yft"], ["test.yft"]),
    (["test.yft", "test_hi.yft"], ["test.yft"]),
    (["other.ydr", "test_hi.yft.xml", "something.ybn", "test.yft.xml"], ["other.ydr", "something.ybn", "test.yft.xml"]),
))
def test_import_dedupe_hi_yft_files(files: str, expected_deduped_files: str):
    from ..sollumz_operators import SOLLUMZ_OT_import_assets
    res = SOLLUMZ_OT_import_assets._dedupe_hi_yft_filenames(None, files)
    assert_equal(res, expected_deduped_files)


DEFAULT_EXPORT_SETTINGS = {
    "target_formats": {"NATIVE", "CWXML"},
    "target_versions": {"GEN8", "GEN9"},
    "limit_to_selected": True,
    "exclude_skeleton": False,
    "ymap_exclude_entities": False,
    "ymap_box_occluders": False,
    "ymap_model_occluders": False,
    "ymap_car_generators": False,
    "apply_transforms": False,
    "mesh_domain": "FACE_CORNER"
}


DEFAULT_IMPORT_SETTINGS = {
    "import_as_asset": False,
    "split_by_group": True,
    "import_ext_skeleton": False,
    "frag_import_vehicle_windows": False,
    "ymap_skip_missing_entities": True,
    "ymap_exclude_entities": False,
    "ymap_box_occluders": False,
    "ymap_model_occluders": False,
    "ymap_car_generators": False,
    "ymap_instance_entities": False,
    "ytyp_mlo_instance_entities": True,
}


@assert_logs_no_warnings_or_errors
def test_export_model_with_packed_textures(tmp_path: Path):
    data = load_blend_data("model_with_packed_textures.blend")

    # .blend was saved with the object to export already selected
    bpy.ops.sollumz.export_assets(
        directory=str(tmp_path.absolute()),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS,
    )

    expected_contents = data.images["test_image.dds"].packed_file.data
    for expected_file in [
        tmp_path / "gen8" / "test_model" / "test_image.dds",
        tmp_path / "gen9" / "test_model" / "test_image.dds",
    ]:
        assert expected_file.is_file()
        assert expected_file.read_bytes() == expected_contents


@assert_logs_no_warnings_or_errors
def test_export_model_with_external_textures(tmp_path: Path):
    data = load_blend_data("model_with_external_textures.blend")

    # .blend was saved with the object to export already selected
    bpy.ops.sollumz.export_assets(
        directory=str(tmp_path.absolute()),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS,
    )

    expected_contents = data_path("textures", "test_image.dds").read_bytes()
    for expected_file in [
        tmp_path / "gen8" / "test_model" / "test_image.dds",
        tmp_path / "gen9" / "test_model" / "test_image.dds",
    ]:
        assert expected_file.is_file()
        assert expected_file.read_bytes() == expected_contents


@requires_szio_native
@pytest.mark.parametrize("version_dir", ("gen8", "gen9"))
@assert_logs_no_warnings_or_errors
def test_import_model_with_embedded_textures_extract_to_import_dir(tmp_path: Path, version_dir: str):
    bpy.ops.wm.read_homefile()

    ydr_filename = "model_with_embedded_textures.ydr"
    ydr_path = asset_path(version_dir, ydr_filename)

    # Copy to temp dir
    (tmp_path / ydr_filename).write_bytes(ydr_path.read_bytes())

    expected_file = tmp_path / "model_with_embedded_textures" / "test_image.dds"
    assert not expected_file.is_file()

    bpy.ops.sollumz.import_assets(
        directory=str(tmp_path.absolute()),
        files=[{"name": ydr_path.name}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS,
    )

    assert expected_file.is_file()
    assert expected_file.read_bytes().startswith(b"DDS ")


@requires_szio_native
@assert_logs_no_warnings_or_errors
def test_export_to_same_dir_as_import_and_textures_are_exported_correctly(tmp_path: Path):
    # Check that there are no errors when exporting embedded textures and their source and
    # destination file paths are same.

    bpy.ops.wm.read_homefile()

    ydr_filename = "model_with_embedded_textures.ydr"
    ydr_path = asset_path("gen8", ydr_filename)

    # Copy to temp dir
    (tmp_path / ydr_filename).write_bytes(ydr_path.read_bytes())

    bpy.ops.sollumz.import_assets(
        directory=str(tmp_path.absolute()),
        files=[{"name": ydr_path.name}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS,
    )

    texture_file = tmp_path / "model_with_embedded_textures" / "test_image.dds"
    texture_contents_after_import = texture_file.read_bytes()

    bpy.data.objects["model_with_embedded_textures"].select_set(True)

    bpy.ops.sollumz.export_assets(
        directory=str(tmp_path.absolute()),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS | {
            "target_formats": {"CWXML"},
            "target_versions": {"GEN8"},
        },
    )

    texture_contents_after_export = texture_file.read_bytes()
    assert texture_contents_after_export == texture_contents_after_import
