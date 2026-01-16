import itertools
import os
import re
from collections import defaultdict
from contextlib import AbstractContextManager
from functools import wraps
from pathlib import Path
from typing import Optional

import bpy
import pytest
from bpy.types import (
    BlendData,
)

from ..logger import (
    LoggerBase,
    use_logger,
)


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
SOLLUMZ_TEST_DATA_DIR = Path(__file__).parent.joinpath("data/")


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


def asset_path(*path_segments: str) -> Path:
    path = SOLLUMZ_TEST_ASSETS_DIR.joinpath(*path_segments)
    assert path.exists()
    return path


def data_path(*path_segments: str) -> Path:
    path = SOLLUMZ_TEST_DATA_DIR.joinpath(*path_segments)
    assert path.exists()
    return path


def load_blend_data(file_name: str) -> BlendData:
    bpy.ops.wm.open_mainfile(filepath=str(data_path(file_name)))
    return bpy.data


def _is_szio_native_available() -> bool:
    import szio.gta5.native
    return szio.gta5.native.IS_BACKEND_AVAILABLE


requires_szio_native = pytest.mark.skipif(
    not _is_szio_native_available(),
    reason="test requires szio native backend to be available"
)

del _is_szio_native_available


class TestLogger(LoggerBase):
    def __init__(self):
        self._logs: dict[str, list[str]] = defaultdict(list)

    def do_log(self, msg: str, level: str):
        self._logs[level].append(msg)

    def reset(self):
        self._logs.clear()

    @property
    def warnings(self) -> list[str]:
        return self._logs["WARNING"]

    @property
    def errors(self) -> list[str]:
        return self._logs["ERROR"]

    @property
    def has_warnings_or_errors(self) -> bool:
        return bool(self.warnings or self.errors)

    @property
    def has_errors(self) -> bool:
        return bool(self.errors)

    def assert_no_warnings_or_errors(self):
        assert not self.has_warnings_or_errors, \
            f"{len(self.warnings)} warning(s), {len(self.errors)} error(s)"

    def assert_no_errors(self):
        assert not self.has_errors, \
            f"{len(self.errors)} error(s)"

    def assert_warning(self, *, match: str | re.Pattern[str] | None = None, num: int = 1):
        warnings = self.warnings
        assert len(warnings) == num, f"Expected {num} warning(s), got {len(warnings)} warning(s)"
        if match is not None:
            assert any(re.search(match, w) for w in warnings), f"Expected warning to match {match!r}."


def log_capture() -> AbstractContextManager[TestLogger]:
    return use_logger(TestLogger())


def assert_logs_no_warnings_or_errors(func):
    """Decorator that asserts that no user-facing warnings or errors were logged."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with log_capture() as logs:
            result = func(*args, **kwargs)
        logs.assert_no_warnings_or_errors()
        return result

    return wrapper


def assert_logs_no_errors(func):
    """Decorator that asserts that no user-facing errors were logged."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        with log_capture() as logs:
            result = func(*args, **kwargs)
        logs.assert_no_errors()
        return result

    return wrapper
