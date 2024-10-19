import bpy
from bpy.types import (
    BlendData,
)
from pathlib import Path

SOLLUMZ_TEST_VERSIONING_DATA_DIR = Path(__file__).parent.joinpath("data/")


def data_path(file_name: str) -> Path:
    path = SOLLUMZ_TEST_VERSIONING_DATA_DIR.joinpath(file_name)
    assert path.exists()
    return path


def load_blend_data(file_name: str) -> BlendData:
    bpy.ops.wm.open_mainfile(filepath=str(data_path(file_name)))
    return bpy.data
