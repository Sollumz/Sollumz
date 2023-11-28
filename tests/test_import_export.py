import pytest
import itertools
import numpy as np
from numpy.testing import assert_allclose, assert_equal
from pathlib import Path
from xml.etree import ElementTree as ET
from .test_fixtures import fps_dependent
from .shared import SOLLUMZ_TEST_TMP_DIR, SOLLUMZ_TEST_GAME_ASSETS_DIR, SOLLUMZ_TEST_ASSETS_DIR
from ..ydr.ydrimport import import_ydr
from ..ydr.ydrexport import export_ydr
from ..yft.yftimport import import_yft
from ..yft.yftexport import export_yft
from ..ybn.ybnimport import import_ybn
from ..ybn.ybnexport import export_ybn
from ..ycd.ycdimport import import_ycd
from ..ycd.ycdexport import export_ycd


if SOLLUMZ_TEST_TMP_DIR is not None:
    def asset_path(file_name: str) -> Path:
        path = SOLLUMZ_TEST_ASSETS_DIR.joinpath(file_name)
        assert path.exists()
        return path

    def tmp_path(file_name: str) -> Path:
        path = SOLLUMZ_TEST_TMP_DIR.joinpath(file_name)
        return path

    def glob_assets(ext: str) -> list[tuple[Path, str]]:
        glob_pattern = f"*.{ext}.xml"
        assets = SOLLUMZ_TEST_ASSETS_DIR.rglob(glob_pattern)
        if SOLLUMZ_TEST_GAME_ASSETS_DIR is not None:
            game_assets = SOLLUMZ_TEST_GAME_ASSETS_DIR.rglob(glob_pattern)
            assets = itertools.chain(assets, game_assets)

        return list(map(lambda p: (p, str(p)), assets))

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
