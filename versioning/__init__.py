"""
This package implements Sollumz versioning system, with the aim of keeping
backwards compatibility when loading old .blend files.

When saving a .blend file a Sollumz version identifier is stored. When an old
.blend file is loaded, its data is upgraded to the current version.
"""

import bpy
from bpy.app.handlers import persistent

SOLLUMZ_INTERNAL_VERSION_MISSING = -1
"""Represents a .blend file not yet saved or saved before versioning system."""

SOLLUMZ_INTERNAL_VERSION = 3
"""Current internal version for Sollumz data stored in .blend files. Independent
of release versions.

With each breaking change this version is incremented and versioning code is
added to keep backwards compatibility when loading old .blend files.

Version History:
 == v2.3.1 ==
  - 0: changes between 2.3.1 and 2.4.0, until the introduction of versioning system.
  - 1: renamed LightFlags, light shadow_blur normalized to 0.0-1.0 range.
 == v2.4.0 ==
  - 2: LOD system fixes.
  - 3: TimecycleModifierProperties.percentage IntProperty -> FloatProperty
  - <next>: <describe changes>
"""


def log(text: str):
    print(f"[sollumz:versioning] {text}")


@persistent
def on_load_post(file_path):
    if not file_path:
        # Skip startup file
        return

    do_versions(bpy.data)


@persistent
def on_save_pre(file_path):
    # Assign the current version before saving
    for scene in bpy.data.scenes:
        scene.sollumz_internal_version = SOLLUMZ_INTERNAL_VERSION


def determine_data_version(data: bpy.types.BlendData) -> int:
    data_version = SOLLUMZ_INTERNAL_VERSION_MISSING
    for scene in data.scenes:
        # All scenes should have the same version, but just in case we use the newest version
        data_version = max(data_version, scene.sollumz_internal_version)

    return data_version


def do_versions(data: bpy.types.BlendData):
    data_version = determine_data_version(data)

    if data_version >= SOLLUMZ_INTERNAL_VERSION:
        return

    log(f"Upgrading Sollumz data from version {data_version} to version {SOLLUMZ_INTERNAL_VERSION}")

    from . import versioning_230, versioning_240
    versioning_230.do_versions(data_version, data)
    versioning_240.do_versions(data_version, data)


def register():
    # Store the version in the Scenes. Blender doesn't allow global properties saved in .blend files, but there must
    # always exist at least one Scene, so we write the version to all scenes before saving.
    bpy.types.Scene.sollumz_internal_version = bpy.props.IntProperty(
        default=SOLLUMZ_INTERNAL_VERSION_MISSING, options={"HIDDEN"}
    )

    bpy.app.handlers.save_pre.append(on_save_pre)
    bpy.app.handlers.load_post.append(on_load_post)


def unregister():
    bpy.app.handlers.save_pre.remove(on_save_pre)
    bpy.app.handlers.load_post.remove(on_load_post)

    del bpy.types.Scene.sollumz_internal_version
