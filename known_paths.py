import bpy
import os

CONFIG_DIR_NAME = "sollumz"
PREFS_FILE_NAME = "sollumz_prefs.ini"


def prefs_file_path() -> str:
    return os.path.join(bpy.utils.user_resource(resource_type="CONFIG"), PREFS_FILE_NAME)


def config_directory_path() -> str:
    return bpy.utils.user_resource(resource_type="CONFIG", path=CONFIG_DIR_NAME, create=True)


def data_directory_path() -> str:
    import addon_utils

    is_extension = bpy.app.version >= (4, 2, 0) and addon_utils.check_extension(__package__)
    if is_extension:
        path = bpy.utils.extension_path_user(__package__)
    else:
        # Fallback to config directory if we are not an extension
        path = os.path.join(config_directory_path(), "data")

    return path
