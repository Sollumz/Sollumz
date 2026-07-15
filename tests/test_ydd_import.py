"""Tests for external skeleton loading when importing drawable dictionaries (ydd/yddimport_io)."""

from pathlib import Path

from szio.gta5 import AssetFormat, AssetTarget, AssetVersion

from ..iecontext import (
    ImportContext,
    ImportExternalSkeletonMode,
    ImportSettings,
    import_context_scope,
)
from ..ydd.yddimport_io import try_load_external_skeleton
from .shared import asset_path, log_capture


def _import_scope(
    mode: ImportExternalSkeletonMode,
    saved_path: Path | None = None,
    directory: Path | None = None,
):
    settings = ImportSettings(
        import_as_asset=False,
        split_by_group=True,
        mlo_instance_entities=True,
        map_instance_entities=True,
        dwd_import_external_skeleton=mode,
        dwd_import_external_skeleton_saved_path=saved_path,
    )
    return import_context_scope(ImportContext(
        asset_name="test_ydd",
        asset_target=AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8),
        directory=directory if directory is not None else asset_path(),
        settings=settings,
    ))


def test_external_skeleton_mode_no_loads_nothing():
    with _import_scope(ImportExternalSkeletonMode.NO), log_capture() as logs:
        assert try_load_external_skeleton() is None

    logs.assert_no_warnings_or_errors()


def test_external_skeleton_mode_from_dir_loads_first_yft_in_import_directory():
    # the assets directory contains a single top-level YFT, sollumz_cube.yft.xml
    with _import_scope(ImportExternalSkeletonMode.FROM_DIR), log_capture() as logs:
        yft = try_load_external_skeleton()

    assert yft is not None
    logs.assert_no_warnings_or_errors()


def test_external_skeleton_mode_from_dir_warns_when_no_yft_found(tmp_path):
    with _import_scope(ImportExternalSkeletonMode.FROM_DIR, directory=tmp_path), log_capture() as logs:
        assert try_load_external_skeleton() is None

    logs.assert_warning(match="Could not find external skeleton YFT")


def test_external_skeleton_mode_saved_loads_selected_path():
    with _import_scope(
        ImportExternalSkeletonMode.SAVED,
        saved_path=asset_path("sollumz_cube.yft.xml"),
    ), log_capture() as logs:
        yft = try_load_external_skeleton()

    assert yft is not None
    logs.assert_no_warnings_or_errors()


def test_external_skeleton_mode_saved_warns_without_selection():
    with _import_scope(ImportExternalSkeletonMode.SAVED), log_capture() as logs:
        assert try_load_external_skeleton() is None

    logs.assert_warning(match="No external skeleton YFT selected")
