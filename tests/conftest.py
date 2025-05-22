import pytest

def pytest_sessionstart(session):
    import bpy
    # Re-enable so coverage correctly includes startup/registration code
    bpy.ops.preferences.addon_disable(module="Sollumz")
    bpy.ops.preferences.addon_enable(module="Sollumz")
