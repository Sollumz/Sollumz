import pytest
import itertools
from pathlib import Path
from .shared import SOLLUMZ_TEST_TMP_DIR, SOLLUMZ_TEST_GAME_ASSETS_DIR, SOLLUMZ_TEST_ASSETS_DIR
from ..ydr.ydrimport import import_ydr
from ..ydr.ydrexport import export_ydr
from ..yft.yftimport import import_yft
from ..yft.yftexport import export_yft
from ..ybn.ybnimport import import_ybn
from ..ybn.ybnexport import export_ybn

if SOLLUMZ_TEST_TMP_DIR is not None:
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

        out_path = SOLLUMZ_TEST_TMP_DIR.joinpath(ydr_path.name)
        success = export_ydr(obj, str(out_path))
        assert success
        assert out_path.exists()

    @pytest.mark.parametrize("yft_path, yft_path_str", glob_assets("yft"))
    def test_import_export_yft(yft_path: Path, yft_path_str: str):
        obj = import_yft(yft_path_str)
        assert obj is not None

        out_path = SOLLUMZ_TEST_TMP_DIR.joinpath(yft_path.name)
        success = export_yft(obj, str(out_path))
        assert success
        assert out_path.exists()

    @pytest.mark.parametrize("ybn_path, ybn_path_str", glob_assets("ybn"))
    def test_import_export_ybn(ybn_path: Path, ybn_path_str: str):
        obj = import_ybn(ybn_path_str)
        assert obj is not None

        out_path = SOLLUMZ_TEST_TMP_DIR.joinpath(ybn_path.name)
        success = export_ybn(obj, str(out_path))
        assert success
        assert out_path.exists()
