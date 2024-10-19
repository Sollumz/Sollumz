import os
import itertools
from typing import Optional
from pathlib import Path


def get_env_path(name: str) -> Optional[Path]:
    """Gets an environment variable as a ``Path``. Returns ``None`` if the environment
    variable or the path do not exist.
    """
    path_str = os.getenv(name, default=None)
    if path_str is None:
        return None

    path = Path(path_str)
    return path if path.exists() else None


SOLLUMZ_TEST_TMP_DIR = get_env_path("SOLLUMZ_TEST_TMP_DIR")
SOLLUMZ_TEST_GAME_ASSETS_DIR = get_env_path("SOLLUMZ_TEST_GAME_ASSETS_DIR")
SOLLUMZ_TEST_ASSETS_DIR = Path(__file__).parent.joinpath("assets/")


def is_tmp_dir_available() -> bool:
    return SOLLUMZ_TEST_TMP_DIR is not None


def tmp_path(file_name: str, subdirectory: Optional[str] = None) -> Path:
    if not is_tmp_dir_available():
        raise Exception("SOLLUMZ_TEST_TMP_DIR environment variable is required.")

    dir_path = SOLLUMZ_TEST_TMP_DIR
    if subdirectory is not None:
        dir_path = dir_path.joinpath(subdirectory)
        if not dir_path.is_dir():
            dir_path.mkdir()
    path = dir_path.joinpath(file_name)
    return path


def glob_assets(ext: str) -> list[tuple[Path, str]]:
    glob_pattern = f"*.{ext}.xml"
    assets = SOLLUMZ_TEST_ASSETS_DIR.rglob(glob_pattern)
    if SOLLUMZ_TEST_GAME_ASSETS_DIR is not None:
        game_assets = SOLLUMZ_TEST_GAME_ASSETS_DIR.rglob(glob_pattern)
        assets = itertools.chain(assets, game_assets)

    return list(map(lambda p: (p, str(p)), assets))


def asset_path(file_name: str) -> Path:
    path = SOLLUMZ_TEST_ASSETS_DIR.joinpath(file_name)
    assert path.exists()
    return path
