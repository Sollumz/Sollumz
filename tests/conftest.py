import pytest
import bpy


def pytest_sessionstart(session):
    # Re-enable so coverage correctly includes startup/registration code
    bpy.ops.preferences.addon_disable(module="Sollumz")
    bpy.ops.preferences.addon_enable(module="Sollumz")


@pytest.fixture()
def context():
    return bpy.context


@pytest.fixture()
def plane_object(context):
    bpy.ops.mesh.primitive_plane_add()
    obj = context.object

    yield obj

    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.ops.object.select_all(action='DESELECT')
    obj.select_set(True)
    bpy.ops.object.delete()


@pytest.fixture(params=[
    (1, 1.0),
    (30, 2.0),    # 15.0 (just to make sure fps_base is taken into account)
    (24, 1.001),  # 23.98
    (24, 1.0),
    (25, 1.0),
    (30, 1.001),  # 29.97
    (30, 1.0),
    (50, 1.0),
    (60, 1.001),  # 59.94
    (60, 1.0),
    (120, 1.0),
    (240, 1.0),
])
def fps_dependent(request):
    """Runs the test with multiple different FPS settings.
    Passes a tuple (float, str) to the test with the FPS value and its string representation.
    """
    fps, fps_base = request.param
    prev_fps = bpy.context.scene.render.fps, bpy.context.scene.render.fps_base
    bpy.context.scene.render.fps, bpy.context.scene.render.fps_base = fps, fps_base

    yield fps / fps_base, f"{fps / fps_base:.2f}"

    bpy.context.scene.render.fps, bpy.context.scene.render.fps_base = prev_fps
