import pytest
import bpy
import itertools
import random
from .test_fixtures import BLENDER_LANGUAGES, SOLLUMZ_SHADERS, SOLLUMZ_COLLISION_MATERIALS, context, plane_object
from ..ydr.shader_materials import create_shader
from ..ybn.collision_materials import create_collision_material_from_index
from ..ynv.ynvimport import get_material as ynv_get_material
from ..tools.ymaphelper import add_occluder_material
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import find_bsdf_and_material_output, material_from_image
from ..tools.drawablehelper import MaterialConverter


@pytest.fixture(scope="class", params=BLENDER_LANGUAGES)
def use_every_language(request):
    for mat in bpy.data.materials:
        bpy.data.materials.remove(mat)

    bpy.context.preferences.view.language = request.param
    # need to read it after changing otherwise Blender crashes (Windows fatal exception: access violation) wtf??
    _ = bpy.context.preferences.view.language
    return request.param


class TestAllLanguages:
    @pytest.mark.parametrize("shader", SOLLUMZ_SHADERS)
    def test_create_shader(self, shader, use_every_language):
        mat = create_shader(shader)
        assert mat is not None

    @pytest.mark.parametrize("material_index", list(range(len(SOLLUMZ_COLLISION_MATERIALS))))
    def test_create_collision_material(self, material_index, use_every_language):
        mat = create_collision_material_from_index(material_index)
        assert mat is not None

    def test_create_navmesh_material(self, use_every_language):
        mat = ynv_get_material("0 204 0 255 161 107", {})
        assert mat is not None

    @pytest.mark.parametrize("sollum_type", (SollumType.YMAP_MODEL_OCCLUDER, SollumType.YMAP_BOX_OCCLUDER))
    def test_create_occluder_material(self, sollum_type, use_every_language):
        mat = add_occluder_material(sollum_type)
        assert mat is not None

    def test_material_from_image(self, use_every_language):
        img = bpy.data.images.new("Test", 16, 16)
        mat = material_from_image(img)
        assert mat is not None

    def test_find_bsdf_and_material_output(self, use_every_language):
        mat = bpy.data.materials.new("Test")
        mat.use_nodes = True
        bsdf, mo = find_bsdf_and_material_output(mat)
        assert bsdf is not None
        assert mo is not None


def static_sample(population, k, seed=0):
    """Random sample from a specific ``seed``."""
    random.seed(seed)
    return random.sample(list(population), k)


@pytest.mark.parametrize("src_shader,dst_shader",
                         # HACK: random sample because it takes too long to test all combinations
                         static_sample(itertools.product(SOLLUMZ_SHADERS, SOLLUMZ_SHADERS), 500, seed=12345))
def test_convert_shader_to_shader(src_shader, dst_shader, plane_object):
    src_mat = create_shader(src_shader)
    plane_object.data.materials.append(src_mat)
    mat = MaterialConverter(plane_object, src_mat).convert(dst_shader)
    assert mat is not None
    assert src_mat != mat
    assert plane_object.data.materials[0] == mat
