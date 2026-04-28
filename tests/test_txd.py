import bpy

from .shared import (
    assert_logs_no_warnings_or_errors,
    load_blend_data,
)

@assert_logs_no_warnings_or_errors
def test_txd_create_from_object_source(context, tmp_path):
    data = load_blend_data("model_with_packed_textures.blend")

    bpy.ops.sollumz.txd_create()

    assert context.scene.sz_txds.texture_dictionaries
    assert len(context.scene.sz_txds.texture_dictionaries) == 1

    txd = context.scene.sz_txds.texture_dictionaries[0]
    txd.name = "test_txd"

    bpy.ops.sollumz.txd_create_source()

    assert txd.sources
    assert len(txd.sources) == 1

    src = txd.sources[0]
    assert src.source_type == "OBJECT"

    src.object_name = "test_model"

    bpy.ops.sollumz.txd_refresh_sources()

    src = txd.sources[0]
    assert src.images
    assert len(src.images) == 1

    src_img = src.images[0]
    assert src_img.image
    assert src_img.image.name == "test_image.dds"
    assert not src_img.use  # texture is embedded, not used by default

    assert not txd.textures

    # use and refresh, should be added to the textures
    bpy.ops.sollumz.txd_source_use_all_images(use=True)
    bpy.ops.sollumz.txd_refresh_sources()

    assert txd.textures
    assert len(txd.textures) == 1

    tex = txd.textures[0]
    assert tex.image
    assert tex.image.name == "test_image.dds"
    assert tex.managed_by_source

    from .test_import_export import DEFAULT_EXPORT_SETTINGS

    bpy.ops.sollumz.export_ytd(
        directory=str(tmp_path.absolute()),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS,
    )

    expected_contents = data.images["test_image.dds"].packed_file.data
    for expected_file in [
        tmp_path / "gen8" / "test_txd" / "test_image.dds",
        tmp_path / "gen9" / "test_txd" / "test_image.dds",
    ]:
        assert expected_file.is_file()
        assert expected_file.read_bytes() == expected_contents
