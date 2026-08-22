import math
import pytest

from szio.gta5.shader import ShaderManager
from ..ydr.shader_materials import (
    _spec_map_is_packed, _specular_params, _is_parallax_pom, _is_displacement, _is_terrain_parallax,
    VEHICLE_SPECULAR_CONSTANTS,
)


def _normalize(v):
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v)


TANGENT = _normalize((0.9, 0.2, -0.3))
NORMAL = _normalize((0.1, -0.25, 0.96))

GAME_BINORMAL = tuple(
    TANGENT[(i + 1) % 3] * NORMAL[(i + 2) % 3] - TANGENT[(i + 2) % 3] * NORMAL[(i + 1) % 3]
    for i in range(3)
)
BLENDER_BITANGENT = tuple(-c for c in GAME_BINORMAL)


def calculate_world_normal(packed_x, packed_y, bumpiness):
    n_x = packed_x * 2 - 1
    n_y = packed_y * 2 - 1
    n_z = math.sqrt(abs(1 - (n_x * n_x + n_y * n_y)))
    b = max(0.001, bumpiness)
    n_x, n_y = n_x * b, n_y * b
    return _normalize(tuple(
        n_x * TANGENT[i] + n_y * GAME_BINORMAL[i] + n_z * NORMAL[i] for i in range(3)
    ))


def blender_normal_map_node(packed_rgb):
    n = _normalize(tuple(c * 2 - 1 for c in packed_rgb))
    return _normalize(tuple(
        n[0] * TANGENT[i] + n[1] * BLENDER_BITANGENT[i] + n[2] * NORMAL[i] for i in range(3)
    ))


def sollumz_packed_normal(packed_x, packed_y, bumpiness):
    n_x = packed_x * 2 - 1
    n_y = packed_y * 2 - 1
    n_z = math.sqrt(max(0.0, 1 - (n_x * n_x + n_y * n_y)))
    b = max(0.001, bumpiness)
    return (n_x * b * 0.5 + 0.5, n_y * b * -0.5 + 0.5, n_z * 0.5 + 0.5)


@pytest.mark.parametrize("packed_x,packed_y", [
    (0.5, 0.5), (1.0, 0.5), (0.0, 0.5), (0.5, 1.0), (0.5, 0.0), (0.8, 0.2), (0.13, 0.77),
])
@pytest.mark.parametrize("bumpiness", [0.0, 0.5, 1.0, 2.5])
def test_packed_normal_matches_calculate_world_normal(packed_x, packed_y, bumpiness):
    expected = calculate_world_normal(packed_x, packed_y, bumpiness)
    actual = blender_normal_map_node(sollumz_packed_normal(packed_x, packed_y, bumpiness))

    assert actual == pytest.approx(expected, abs=1e-6)


def test_green_channel_must_be_flipped():
    packed = sollumz_packed_normal(0.8, 0.2, 1.0)
    unflipped = (packed[0], 1.0 - packed[1], packed[2])

    assert blender_normal_map_node(unflipped) != pytest.approx(
        calculate_world_normal(0.8, 0.2, 1.0), abs=1e-6)


@pytest.mark.parametrize("a,b", [(0.0, 0.0), (1.0, 1.0), (0.5, 0.5), (0.25, 0.9)])
def test_detail_sample_average_simplification(a, b):
    reference = 0.5 * ((a * 2 - 1) + (b * 2 - 1))

    assert a + b - 1 == pytest.approx(reference)


@pytest.mark.parametrize("exponent", [0.0, 1.0, 100.0, 499.0, 500.0, 501.0, 512.0])
def test_specular_exponent_range_expansion(exponent):
    expand_range = max(0.0, exponent - 500.0)
    reference = (exponent - expand_range) * 3.0 + expand_range * 558.0

    assert 3.0 * exponent + 555.0 * expand_range == pytest.approx(reference)


def test_roughness_from_blinn_exponent_is_sane():
    def roughness(exponent):
        blinn = 3.0 * exponent + 555.0 * max(0.0, exponent - 500.0)
        return (2.0 / (blinn + 2.0)) ** 0.25

    assert roughness(0.0) == pytest.approx(1.0)
    # Monotonically sharper as the falloff multiplier grows.
    values = [roughness(e) for e in (0.0, 1.0, 10.0, 100.0, 500.0, 512.0)]
    assert all(a > b for a, b in zip(values, values[1:]))
    assert 0.0 < values[-1] < 0.2


PACKED_SPEC_SHADERS = {
    "ped", "ped_alpha", "ped_cloth", "ped_cloth_enveff", "ped_decal_decoration", "ped_decal_exp",
    "ped_decal_nodiff", "ped_emissive", "ped_enveff", "ped_fur", "ped_hair_cutout_alpha",
    "ped_hair_cutout_alpha_cloth", "ped_hair_spiked", "ped_nopeddamagedecals", "ped_palette",
    "ped_wrinkle", "ped_wrinkle_cloth", "ped_wrinkle_cloth_enveff", "ped_wrinkle_cs",
    "ped_wrinkle_enveff",
    "vehicle_mesh", "vehicle_mesh2_enveff", "vehicle_mesh_enveff", "vehicle_tire",
    "vehicle_tire_emissive",
    "weapon_normal_spec_cutout_palette", "weapon_normal_spec_detail_palette",
    "weapon_normal_spec_detail_tnt", "weapon_normal_spec_palette", "weapon_normal_spec_tnt",
}


@pytest.mark.parametrize("shader_name", sorted(
    s.base_name for s in ShaderManager._shaders.values() if "SpecSampler" in s.parameter_map
))
def test_spec_map_packing_matches_game_shader_families(shader_name):
    shader = next(s for s in ShaderManager._shaders.values() if s.base_name == shader_name)

    assert _spec_map_is_packed(shader) == (shader_name in PACKED_SPEC_SHADERS)


def gta_fresnel_ior(specular_fresnel):
    """The conversion in ``gta_fresnel_ior_expr``."""
    f0 = (1.0 - min(1.0, max(0.0, specular_fresnel))) * 0.5
    sqrt_f0 = math.sqrt(f0)
    return (1.0 + sqrt_f0) / (1.0 - sqrt_f0)


def ior_to_f0(ior):
    return ((ior - 1.0) / (ior + 1.0)) ** 2


@pytest.mark.parametrize("specular_fresnel", [0.0, 0.25, 0.5, 0.83, 0.96, 0.97, 0.98, 1.0])
@pytest.mark.parametrize("specular_intensity", [0.0, 0.065, 0.125, 0.6, 1.0])
def test_fresnel_ior_reproduces_game_normal_incidence_reflectance(specular_fresnel, specular_intensity):
    blender_f0 = ior_to_f0(gta_fresnel_ior(specular_fresnel)) * 2.0 * specular_intensity
    game_f0 = specular_intensity * (1.0 - specular_fresnel)

    assert blender_f0 == pytest.approx(game_f0, abs=1e-9)


def test_fresnel_ior_stays_in_a_sane_range():
    assert gta_fresnel_ior(1.0) == pytest.approx(1.0)   # no reflection head-on (vehicle_mesh)
    assert gta_fresnel_ior(0.0) == pytest.approx(5.8284, abs=1e-3)

    values = [gta_fresnel_ior(f) for f in (1.0, 0.98, 0.9, 0.5, 0.0)]
    assert all(a < b for a, b in zip(values, values[1:]))


@pytest.mark.parametrize("shader_name", sorted(
    s.base_name for s in ShaderManager._shaders.values() if "SpecSampler" in s.parameter_map
))
def test_shaders_with_a_spec_map_always_get_specular(shader_name):
    shader = next(s for s in ShaderManager._shaders.values() if s.base_name == shader_name)

    assert _specular_params(shader) is not None, \
        f"{shader_name} has a spec map but no specular values; add it to VEHICLE_SPECULAR_CONSTANTS"


def test_vehicle_specular_constants_are_all_real_shaders():
    known = {s.base_name for s in ShaderManager._shaders.values()}

    assert set(VEHICLE_SPECULAR_CONSTANTS) <= known

POM_SHADERS = {
    "normal_pxm", "normal_pxm_tnt", "normal_spec_pxm", "normal_spec_pxm_tnt",
    "normal_decal_pxm", "normal_decal_pxm_tnt", "normal_spec_decal_pxm",
}

DISPLACEMENT_SHADERS = {
    "normal_spec_dpm", "normal_detail_dpm", "normal_spec_detail_dpm", "normal_spec_detail_dpm_tnt",
    "normal_spec_detail_dpm_vertdecal_tnt", "normal_diffspec_detail_dpm",
    "normal_diffspec_detail_dpm_tnt",
}


@pytest.mark.parametrize("shader_name", sorted(
    s.base_name for s in ShaderManager._shaders.values() if "heightSampler" in s.parameter_map
))
def test_height_shaders_are_classified_as_parallax_or_displacement(shader_name):
    shader = next(s for s in ShaderManager._shaders.values() if s.base_name == shader_name)

    assert _is_parallax_pom(shader) == (shader_name in POM_SHADERS)
    assert _is_displacement(shader) == (shader_name in DISPLACEMENT_SHADERS)
    assert _is_parallax_pom(shader) != _is_displacement(shader)


@pytest.mark.parametrize("height", [0.0, 0.25, 1.0])
@pytest.mark.parametrize("scale,bias", [(0.03, 0.015), (0.2, 0.0), (0.05, -0.01)])
def test_pom_offset_folding(height, scale, bias):
    tan_xy, clamped_z, global_scale = (0.4, -0.2), 0.7, 0.8

    reference = tuple(
        (t / clamped_z) * bias * global_scale + (-t / clamped_z) * scale * global_scale * (1.0 - height)
        for t in tan_xy
    )
    k = global_scale * (bias - scale * (1.0 - height)) / clamped_z
    folded = tuple(t * k for t in tan_xy)

    assert folded == pytest.approx(reference)


@pytest.mark.parametrize("v_dot_n", [0.0, 0.05, 0.25, 0.5, 1.0])
def test_pom_step_count_term_is_always_one(v_dot_n):
    number_of_steps = 27.0 + (3.0 - 27.0) * v_dot_n

    assert min(1.0, max(0.0, number_of_steps - 1.0)) == 1.0


@pytest.mark.parametrize("height", [0.0, 0.5, 1.0])
@pytest.mark.parametrize("scale_bias", [0.03, 0.1])
def test_simple_parallax_offset_folding(height, scale_bias):
    reference = height * scale_bias - scale_bias * 0.5

    assert scale_bias * (height - 0.5) == pytest.approx(reference)


def test_pom_grazing_fade():
    def global_scale(v_dot_n):
        return min(1.0, max(0.0, abs(v_dot_n) / 0.25))

    assert global_scale(1.0) == pytest.approx(1.0)
    assert global_scale(0.25) == pytest.approx(1.0)
    assert global_scale(0.125) == pytest.approx(0.5)
    assert global_scale(0.0) == pytest.approx(0.0)


TERRAIN_POM_SHADERS = {
    "terrain_cb_w_4lyr_pxm", "terrain_cb_w_4lyr_pxm_spm", "terrain_cb_w_4lyr_spec_pxm",
    "terrain_cb_w_4lyr_spec_int_pxm", "terrain_cb_w_4lyr_2tex_pxm", "terrain_cb_w_4lyr_cm_pxm",
    "terrain_cb_w_4lyr_cm_pxm_tnt", "terrain_cb_w_4lyr_2tex_blend_pxm",
    "terrain_cb_w_4lyr_2tex_blend_pxm_spm",
}


@pytest.mark.parametrize("shader_name", sorted(s.base_name for s in ShaderManager._shaders.values()))
def test_terrain_parallax_classification(shader_name):
    shader = next(s for s in ShaderManager._shaders.values() if s.base_name == shader_name)

    assert _is_terrain_parallax(shader) == (shader_name in TERRAIN_POM_SHADERS)
    if _is_terrain_parallax(shader):
        assert not _is_parallax_pom(shader)
        assert not _is_displacement(shader)


@pytest.mark.parametrize("green,blue", [
    (0.0, 0.0), (1.0, 1.0), (0.0, 1.0), (1.0, 0.0), (0.3, 0.7), (0.5, 0.5), (0.9, 0.1),
])
def test_terrain_layer_blend_matches_get_alpha_weights(green, blue):
    values = (11.0, 22.0, 33.0, 44.0)

    def lerp(a, b, factor):
        return a + (b - a) * factor

    nested = lerp(lerp(values[0], values[1], blue), lerp(values[2], values[3], blue), green)

    weights = ((1 - green) * (1 - blue), (1 - green) * blue, green * (1 - blue), green * blue)
    reference = sum(w * v for w, v in zip(weights, values))

    assert sum(weights) == pytest.approx(1.0)
    assert nested == pytest.approx(reference)


def test_terrain_layer_blend_isolates_a_single_layer():
    def blend(values, green, blue):
        def lerp(a, b, f):
            return a + (b - a) * f
        return lerp(lerp(values[0], values[1], blue), lerp(values[2], values[3], blue), green)

    assert blend((0.2, 5.0, 5.0, 5.0), 0.0, 0.0) == pytest.approx(0.2)
    assert blend((5.0, 0.2, 5.0, 5.0), 0.0, 1.0) == pytest.approx(0.2)
    assert blend((5.0, 5.0, 0.2, 5.0), 1.0, 0.0) == pytest.approx(0.2)
    assert blend((5.0, 5.0, 5.0, 0.2), 1.0, 1.0) == pytest.approx(0.2)
