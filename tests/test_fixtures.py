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
