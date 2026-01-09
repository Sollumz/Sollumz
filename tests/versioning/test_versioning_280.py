from .shared import load_blend_data


def test_versioning_archetype_spawn_point_extensions():
    data = load_blend_data("v280_archetype_spawn_point_extensions.blend")

    arch = data.scenes[0].ytyps[0].archetypes[0]
    ext = arch.extensions[0]
    ext_props = ext.spawn_point_extension_properties
    assert ext_props.required_imap == "test_map"
    assert ext_props.start == 2
    assert ext_props.end == 18
