from pathlib import Path
from xml.etree import ElementTree as ET

import bpy
import numpy as np
import pytest
from numpy.testing import assert_allclose, assert_equal

from ..sollumz_properties import SollumType
from ..ybn.ybnexport import export_ybn
from ..ybn.ybnimport import import_ybn
from ..ycd.ycdexport import export_ycd
from ..ycd.ycdimport import import_ycd
from ..ydr.ydrexport import export_ydr
from ..ydr.ydrimport import import_ydr
from ..yft.yftexport import export_yft
from ..yft.yftimport import import_yft
from .shared import (
    assert_logs_no_errors,
    assert_logs_no_warnings_or_errors,
    asset_path,
    data_path,
    glob_assets,
    is_tmp_dir_available,
    load_blend_data,
    log_capture,
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
    @pytest.mark.skip(reason="old import/export code, some new cloth assets are not handled correctly")
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
    "textures_mode": "PACK",
    "textures_extract_custom_directory": "",
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
@pytest.mark.parametrize("textures_mode", ("PACK", "IMPORT_DIR", "CUSTOM_DIR", "CUSTOM_DIR_NOT_SET"))
@assert_logs_no_warnings_or_errors
def test_import_model_with_embedded_textures(tmp_path: Path, version_dir: str, textures_mode: str):
    bpy.ops.wm.read_homefile()

    ydr_filename = "model_with_embedded_textures.ydr"
    ydr_path = asset_path(version_dir, ydr_filename)

    # Copy to temp dir
    (tmp_path / ydr_filename).write_bytes(ydr_path.read_bytes())

    custom_dir = (tmp_path / "my_textures_custom_dir").absolute()
    texture_in_import_dir = tmp_path / "model_with_embedded_textures" / "test_image.dds"
    texture_in_custom_dir = custom_dir / "model_with_embedded_textures" / "test_image.dds"

    assert not texture_in_import_dir.is_file()
    assert not texture_in_custom_dir.is_file()
    assert "test_image.dds" not in bpy.data.images

    res = bpy.ops.sollumz.import_assets(
        directory=str(tmp_path.absolute()),
        files=[{"name": ydr_path.name}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS | ({
            "textures_mode": textures_mode,
            "textures_extract_custom_directory": str(custom_dir),
        } if textures_mode != "CUSTOM_DIR_NOT_SET" else {
            "textures_mode": "CUSTOM_DIR",
            "textures_extract_custom_directory": "",
        }),
    )
    assert res == {"FINISHED"}

    assert "test_image.dds" in bpy.data.images
    img = bpy.data.images["test_image.dds"]
    assert img.size[:] == (64, 64)
    assert img.source == "FILE"

    match textures_mode:
        case "PACK":
            # embedded textures loaded into a packed image directly, without creating any file
            assert not texture_in_import_dir.is_file()
            assert not texture_in_custom_dir.is_file()
            assert img.filepath == "//test_image.dds"
            assert img.packed_file
            assert img.packed_file.data and img.packed_file.data.startswith(b"DDS ")

        case "IMPORT_DIR" | "CUSTOM_DIR_NOT_SET":
            # embedded textures are extracted to import directory
            assert not texture_in_custom_dir.is_file()
            assert texture_in_import_dir.is_file()
            assert texture_in_import_dir.read_bytes().startswith(b"DDS ")
            assert img.filepath == str(texture_in_import_dir)
            assert not img.packed_file

        case "CUSTOM_DIR":
            # embedded textures are extracted to custom directory
            assert not texture_in_import_dir.is_file()
            assert texture_in_custom_dir.is_file()
            assert texture_in_custom_dir.read_bytes().startswith(b"DDS ")
            assert img.filepath == str(texture_in_custom_dir)
            assert not img.packed_file


@pytest.mark.parametrize("textures_mode", ("PACK", "IMPORT_DIR", "CUSTOM_DIR", "CUSTOM_DIR_NOT_SET"))
@assert_logs_no_warnings_or_errors
def test_import_model_with_embedded_textures_cwxml(tmp_path: Path, textures_mode: str):
    # CWXML embedded textures are actually external textures in the import directory so the behaviour is slightly
    # different than in native formats

    bpy.ops.wm.read_homefile()

    ydr_filename = "model_with_embedded_textures.ydr.xml"
    ydr_path = asset_path("cwxml", ydr_filename)
    ydr_external_tex_path = asset_path("cwxml", "model_with_embedded_textures", "test_image.dds")

    # Copy to temp dir
    (tmp_path / ydr_filename).write_bytes(ydr_path.read_bytes())
    (tmp_path / "model_with_embedded_textures").mkdir()
    (tmp_path / "model_with_embedded_textures" / "test_image.dds").write_bytes(ydr_external_tex_path.read_bytes())

    custom_dir = (tmp_path / "my_textures_custom_dir").absolute()
    texture_in_import_dir = tmp_path / "model_with_embedded_textures" / "test_image.dds"
    texture_in_custom_dir = custom_dir / "model_with_embedded_textures" / "test_image.dds"

    assert texture_in_import_dir.is_file(), "CWXML should already have textures in the import directory"
    assert not texture_in_custom_dir.is_file()
    assert "test_image.dds" not in bpy.data.images

    res = bpy.ops.sollumz.import_assets(
        directory=str(tmp_path.absolute()),
        files=[{"name": ydr_path.name}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS | ({
            "textures_mode": textures_mode,
            "textures_extract_custom_directory": str(custom_dir),
        } if textures_mode != "CUSTOM_DIR_NOT_SET" else {
            "textures_mode": "CUSTOM_DIR",
            "textures_extract_custom_directory": "",
        }),
    )
    assert res == {"FINISHED"}

    assert "test_image.dds" in bpy.data.images
    img = bpy.data.images["test_image.dds"]
    assert img.size[:] == (64, 64)
    assert img.source == "FILE"

    match textures_mode:
        case "PACK":
            # embedded textures loaded from import directory and packed
            assert texture_in_import_dir.is_file()
            assert not texture_in_custom_dir.is_file()
            assert img.filepath == str(texture_in_import_dir)
            assert img.packed_file
            assert img.packed_file.data and img.packed_file.data.startswith(b"DDS ")

        case "IMPORT_DIR" | "CUSTOM_DIR_NOT_SET":
            # embedded textures remain in import directory
            assert not texture_in_custom_dir.is_file()
            assert texture_in_import_dir.is_file()
            assert texture_in_import_dir.read_bytes().startswith(b"DDS ")
            assert img.filepath == str(texture_in_import_dir)
            assert not img.packed_file

        case "CUSTOM_DIR":
            # embedded textures copied from import directory to custom directory
            assert texture_in_import_dir.is_file()
            assert texture_in_custom_dir.is_file()
            assert texture_in_custom_dir.read_bytes().startswith(b"DDS ")
            assert texture_in_import_dir.read_bytes() == texture_in_custom_dir.read_bytes()
            assert img.filepath == str(texture_in_custom_dir)
            assert not img.packed_file


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
        **DEFAULT_IMPORT_SETTINGS | {
            "textures_mode": "IMPORT_DIR"
        },
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


@requires_szio_native
@assert_logs_no_warnings_or_errors
def test_export_vehicle_shattermaps(tmp_path: Path):
    data = load_blend_data("shattermaps.blend")

    bpy.ops.object.select_all(action="DESELECT")

    data.objects["test_shattermaps"].select_set(True)

    bpy.ops.sollumz.export_assets(
        directory=str(tmp_path.absolute()),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS,
    )

    tree = ET.ElementTree()
    tree.parse(tmp_path / "gen8" / "test_shattermaps.yft.xml")
    root = tree.getroot()
    assert len(root.findall("./VehicleGlassWindows/Window/ShatterMap")) == 3


@requires_szio_native
@assert_logs_no_errors
def test_export_vehicle_shattermaps_with_no_painted_edges(tmp_path: Path):
    data = load_blend_data("shattermaps.blend")

    bpy.ops.object.select_all(action="DESELECT")

    data.objects["test_shattermaps_no_edges"].select_set(True)

    with log_capture() as logs:
        bpy.ops.sollumz.export_assets(
            directory=str(tmp_path.absolute()),
            direct_export=True,
            use_custom_settings=True,
            **DEFAULT_EXPORT_SETTINGS,
        )

        logs.assert_no_errors()
        logs.assert_warning(match="Mesh 'window_lf_high.001'.*no blue channel data.*", num=3)
        logs.assert_warning(match="Mesh 'window_rf_high.001'.*no blue channel data.*", num=3)
        logs.assert_warning(match="Mesh 'windscreen_high.001'.*no blue channel data.*", num=3)

    tree = ET.ElementTree()
    tree.parse(tmp_path / "gen8" / "test_shattermaps_no_edges.yft.xml")
    root = tree.getroot()
    assert len(root.findall("./VehicleGlassWindows/Window/ShatterMap")) == 3


@pytest.mark.parametrize(
    "frag_obj_name",
    (
        "cloth_only",
        "cloth_with_mesh",
        "cloth_with_world_bounds_planes",
        "cloth_with_world_bounds_capsules",
        "cloth_with_world_bounds_planes_and_capsules",
    ),
)
@assert_logs_no_warnings_or_errors
def test_export_fragment_cloth(frag_obj_name: str, tmp_path: Path):
    data = load_blend_data("fragment_cloth.blend")

    bpy.ops.object.select_all(action="DESELECT")

    data.objects[frag_obj_name].select_set(True)

    bpy.ops.sollumz.export_assets(
        directory=str(tmp_path.absolute()),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS,
    )

    tree = ET.ElementTree()
    tree.parse(tmp_path / "gen8" / f"{frag_obj_name}.yft.xml")
    root = tree.getroot()

    assert len(root.findall("./Cloths/Item/Controller")) == 1
    assert len(root.findall("./Cloths/Item/Drawable")) == 1
    ndrawable = len(root.findall("./Drawable"))
    bounds_xpath = "./Cloths/Item/Controller/VerletCloth1/Bounds[@type='Composite']/Children/Item"
    nbounds = len(root.findall(bounds_xpath))
    nbounds_planes = len(root.findall(f"{bounds_xpath}[@type='Cloth']"))
    nbounds_capsules = len(root.findall(f"{bounds_xpath}[@type='Capsule']"))
    match frag_obj_name:
        case "cloth_only":
            assert ndrawable == 0
            assert nbounds == 0
        case "cloth_with_mesh":
            assert ndrawable == 1
            assert nbounds == 0
        case "cloth_with_world_bounds_planes":
            assert ndrawable == 0
            assert nbounds == 2
            assert nbounds_planes == 2
            assert nbounds_capsules == 0
        case "cloth_with_world_bounds_capsules":
            assert ndrawable == 0
            assert nbounds == 2
            assert nbounds_planes == 0
            assert nbounds_capsules == 2
        case "cloth_with_world_bounds_planes_and_capsules":
            assert ndrawable == 0
            assert nbounds == 2
            assert nbounds_planes == 1
            assert nbounds_capsules == 1


@requires_szio_native
@pytest.mark.parametrize("version_dir", ("gen8", "gen9", "cwxml"))
@pytest.mark.parametrize(
    "model",
    (
        "cloth_only",
        "cloth_with_mesh",
        "cloth_with_world_bounds_planes",
        "cloth_with_world_bounds_capsules",
        "cloth_with_world_bounds_planes_and_capsules",
    ),
)
@assert_logs_no_warnings_or_errors
def test_import_fragment_cloth(version_dir: str, model: str, tmp_path: Path):
    from ..ydr.cloth_env import cloth_env_find_mesh_objects

    bpy.ops.wm.read_homefile()

    yft_filename = f"{model}.yft"
    if version_dir == "cwxml":
        yft_filename += ".xml"
    yft_path = asset_path(version_dir, yft_filename)

    # Copy to temp dir
    (tmp_path / yft_filename).write_bytes(yft_path.read_bytes())

    res = bpy.ops.sollumz.import_assets(
        directory=str(tmp_path.absolute()),
        files=[{"name": yft_path.name}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS,
    )
    assert res == {"FINISHED"}

    frag_obj = bpy.data.objects[model]
    assert frag_obj.sollum_type == SollumType.FRAGMENT

    cloth_objs = cloth_env_find_mesh_objects(frag_obj)
    assert len(cloth_objs) == 1

    cloth_props = frag_obj.fragment_properties.cloth
    world_bounds_name = f"{model}.cloth_world_bounds"
    match model:
        case "cloth_only" | "cloth_with_mesh":
            assert world_bounds_name not in bpy.data.objects
            assert cloth_props.world_bounds is None
        case "cloth_with_world_bounds_planes" | "cloth_with_world_bounds_capsules" | "cloth_with_world_bounds_planes_and_capsules":
            world_bounds_obj = bpy.data.objects[world_bounds_name]
            assert world_bounds_obj.sollum_type == SollumType.BOUND_COMPOSITE
            assert cloth_props.world_bounds == world_bounds_obj
