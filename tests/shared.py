import os
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
SOLLUMZ_TEST_VERSIONING_DATA_DIR = Path(__file__).parent.joinpath("versioning/data/")
