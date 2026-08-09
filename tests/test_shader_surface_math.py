"""Checks for the GTA V surface math transcribed in ``ydr.shader_materials``.

These verify the *derivations* used to express the game's math with Blender nodes (the algebraic
simplifications and the packed-normal encoding), not the generated node trees themselves.
``test_shader_creation.test_create_shader`` covers those building without error.
"""
import math
import pytest

from szio.gta5.shader import ShaderManager
from ..ydr.shader_materials import _spec_map_is_packed, _specular_params, VEHICLE_SPECULAR_CONSTANTS


def _normalize(v):
    length = math.sqrt(sum(c * c for c in v))
    return tuple(c / length for c in v)


# Arbitrary but non-degenerate, non-orthonormal-on-purpose tangent frame.
TANGENT = _normalize((0.9, 0.2, -0.3))
NORMAL = _normalize((0.1, -0.25, 0.96))
# The game builds its binormal as cross(tangent, normal); Blender uses cross(normal, tangent).
GAME_BINORMAL = tuple(
    TANGENT[(i + 1) % 3] * NORMAL[(i + 2) % 3] - TANGENT[(i + 2) % 3] * NORMAL[(i + 1) % 3]
    for i in range(3)
)
BLENDER_BITANGENT = tuple(-c for c in GAME_BINORMAL)


def calculate_world_normal(packed_x, packed_y, bumpiness):
    """``CalculateWorldNormal`` from ``common.fxh``."""
    n_x = packed_x * 2 - 1
    n_y = packed_y * 2 - 1
    n_z = math.sqrt(abs(1 - (n_x * n_x + n_y * n_y)))
    b = max(0.001, bumpiness)
    n_x, n_y = n_x * b, n_y * b
    return _normalize(tuple(
        n_x * TANGENT[i] + n_y * GAME_BINORMAL[i] + n_z * NORMAL[i] for i in range(3)
    ))


def blender_normal_map_node(packed_rgb):
    """Blender's Normal Map node at Strength 1: decode, normalise, transform by its own TBN."""
    n = _normalize(tuple(c * 2 - 1 for c in packed_rgb))
    return _normalize(tuple(
        n[0] * TANGENT[i] + n[1] * BLENDER_BITANGENT[i] + n[2] * NORMAL[i] for i in range(3)
    ))


def sollumz_packed_normal(packed_x, packed_y, bumpiness):
    """The colour ``gta_decode_normal_expr`` feeds into the Normal Map node."""
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
    """Guards the binormal handedness difference: not flipping green gives a different normal."""
    packed = sollumz_packed_normal(0.8, 0.2, 1.0)
    unflipped = (packed[0], 1.0 - packed[1], packed[2])

    assert blender_normal_map_node(unflipped) != pytest.approx(
        calculate_world_normal(0.8, 0.2, 1.0), abs=1e-6)


@pytest.mark.parametrize("a,b", [(0.0, 0.0), (1.0, 1.0), (0.5, 0.5), (0.25, 0.9)])
def test_detail_sample_average_simplification(a, b):
    """``gta_detail_expr`` folds 0.5*((2a-1) + (2b-1)) into a + b - 1."""
    reference = 0.5 * ((a * 2 - 1) + (b * 2 - 1))

    assert a + b - 1 == pytest.approx(reference)


@pytest.mark.parametrize("exponent", [0.0, 1.0, 100.0, 499.0, 500.0, 501.0, 512.0])
def test_specular_exponent_range_expansion(exponent):
    """``populateMaterialProperties`` in lighting_common.fxh, folded into 3e + 555*max(0, e-500)."""
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


# Shaders the game compiles with SPEC_MAP_INTFALLOFF_PACK / SPEC_MAP_INTFALLOFFFRESNEL_PACK, i.e.
# intensity in R and falloff in G instead of the mask-dotted RGB / alpha layout. Note this is not a
# whole family: ped packing is gated on PED_RIM_LIGHT, so ped_default*/ped_decal use the mask
# layout, as does weapon_normal_spec_alpha.
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
    """The game's reflectance is ``specularIntensity * Schlick(F0 = 1 - specularFresnel)``.

    Blender computes ``F0 = ior_to_F0(IOR) * 2 * specularIORLevel`` (measured exactly in EEVEE), and
    Specular IOR Level carries the intensity, so the IOR must supply ``(1 - specularFresnel) / 2``.
    """
    blender_f0 = ior_to_f0(gta_fresnel_ior(specular_fresnel)) * 2.0 * specular_intensity
    game_f0 = specular_intensity * (1.0 - specular_fresnel)

    assert blender_f0 == pytest.approx(game_f0, abs=1e-9)


def test_fresnel_ior_stays_in_a_sane_range():
    # specularFresnel is declared 0..1, so F0 tops out at 0.5 and the IOR stays well bounded.
    assert gta_fresnel_ior(1.0) == pytest.approx(1.0)   # no reflection head-on (vehicle_mesh)
    assert gta_fresnel_ior(0.0) == pytest.approx(5.8284, abs=1e-3)
    # Monotonic: less fresnel roll-off => higher base reflectance => higher IOR.
    values = [gta_fresnel_ior(f) for f in (1.0, 0.98, 0.9, 0.5, 0.0)]
    assert all(a < b for a, b in zip(values, values[1:]))


@pytest.mark.parametrize("shader_name", sorted(
    s.base_name for s in ShaderManager._shaders.values() if "SpecSampler" in s.parameter_map
))
def test_shaders_with_a_spec_map_always_get_specular(shader_name):
    """A spec map with no specular multiplier parameters means the game compiled the values in
    (the vehicle ``VEHCONST_*`` defines). Missing one from the table silently zeroes its specular."""
    shader = next(s for s in ShaderManager._shaders.values() if s.base_name == shader_name)

    assert _specular_params(shader) is not None, \
        f"{shader_name} has a spec map but no specular values; add it to VEHICLE_SPECULAR_CONSTANTS"


def test_vehicle_specular_constants_are_all_real_shaders():
    known = {s.base_name for s in ShaderManager._shaders.values()}

    assert set(VEHICLE_SPECULAR_CONSTANTS) <= known
