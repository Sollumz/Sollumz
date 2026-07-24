from .shared import load_blend_data


def test_versioning_archetype_spawn_point_extensions():
    data = load_blend_data("v280_archetype_spawn_point_extensions.blend")

    arch = data.scenes[0].ytyps[0].archetypes[0]
    ext = arch.extensions[0]
    ext_props = ext.spawn_point_extension_properties
    assert ext_props.required_imap == "test_map"
    assert ext_props.start == 2
    assert ext_props.end == 18


def test_versioning_mlo_entity_ao_and_tint():
    data = load_blend_data("v280_mlo_entity_ao_and_tint.blend")

    entities = data.scenes[0].ytyps[0].archetypes[0].entities
    assert len(entities) == 3

    # 128.5, 64.0, 33.0 -> truncated to ints
    assert entities[0].ambient_occlusion_multiplier == 128
    assert entities[0].artificial_ambient_occlusion == 64
    assert entities[0].tint_value == 33

    # -10.0, 300.0, 12.9 -> clamped to the 0-255 range
    assert entities[1].ambient_occlusion_multiplier == 0
    assert entities[1].artificial_ambient_occlusion == 255
    assert entities[1].tint_value == 12

    # never modified, so nothing was stored in the .blend and the defaults are used
    assert entities[2].ambient_occlusion_multiplier == 255
    assert entities[2].artificial_ambient_occlusion == 255
    assert entities[2].tint_value == 0

    for e in entities:
        assert isinstance(e.ambient_occlusion_multiplier, int)
        assert isinstance(e.artificial_ambient_occlusion, int)
        assert isinstance(e.tint_value, int)
