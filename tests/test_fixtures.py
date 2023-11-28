import pytest
import bpy
from ..ydr.shader_materials import shadermats
from ..ybn.collision_materials import collisionmats

SOLLUMZ_SHADERS = list(map(lambda s: s.value, shadermats))
SOLLUMZ_COLLISION_MATERIALS = list(collisionmats)
BLENDER_LANGUAGES = ("en_US", "es")  # bpy.app.translations.locales


@pytest.fixture()
def context():
    return bpy.context


@pytest.fixture()
def plane_object(context):
    bpy.ops.mesh.primitive_plane_add()
    obj = context.object

    yield obj

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
