import shutil
from pathlib import Path

import bpy
import pytest
from bpy.types import (
    Image,
    ShaderNodeTexImage,
)

from .shared import (
    assert_dds_is_full_res,
    assert_logs_no_warnings_or_errors,
    dropped_mip,
    load_blend_data,
    make_bc1_dds,
    new_packed_dds_image,
    requires_szio_native,
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


@assert_logs_no_warnings_or_errors
def test_txd_create_from_collection_source(context, tmp_path):
    data = load_blend_data("model_with_packed_textures.blend")

    collection = data.collections.new("test_collection")
    context.scene.collection.children.link(collection)
    collection.objects.link(data.objects["test_model"])

    bpy.ops.sollumz.txd_create()

    assert context.scene.sz_txds.texture_dictionaries
    assert len(context.scene.sz_txds.texture_dictionaries) == 1

    txd = context.scene.sz_txds.texture_dictionaries[0]
    txd.name = "test_txd"

    bpy.ops.sollumz.txd_create_source()

    assert txd.sources
    assert len(txd.sources) == 1

    src = txd.sources[0]
    src.source_type = "COLLECTION"
    src.collection_name = "test_collection"

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


def _setup_and_export_hi_txd(context, tmp_path) -> tuple[bytes, bytes]:
    """Creates a txd with an HD texture and a normal texture, then exports it.
    Returns the full-resolution DDS bytes of the HD texture and of the normal texture.
    """
    from .test_import_export import DEFAULT_EXPORT_SETTINGS

    bpy.ops.wm.read_homefile()

    full_dds = make_bc1_dds(16, 16, 3)
    sd_dds = make_bc1_dds(16, 16, 1)
    hd_img = new_packed_dds_image("hd_tex.dds", full_dds)
    hd_img.sz_is_hd = True
    sd_img = new_packed_dds_image("sd_tex.dds", sd_dds)

    txd = context.scene.sz_txds.new_texture_dictionary(name="test_txd")
    txd.new_texture(hd_img)
    txd.new_texture(sd_img)

    bpy.ops.sollumz.export_ytd(
        directory=str(tmp_path.absolute()),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS,
    )

    return full_dds, sd_dds


@requires_szio_native
@pytest.mark.parametrize("textures_mode", ("PACK", "IMPORT_DIR"))
@pytest.mark.parametrize("import_file", ("test_txd.ytd", "test_txd.ytd.xml"))
@assert_logs_no_warnings_or_errors
def test_txd_hi_roundtrip(context, tmp_path, import_file, textures_mode):
    from .test_import_export import DEFAULT_IMPORT_SETTINGS

    full_dds, sd_dds = _setup_and_export_hi_txd(context, tmp_path)

    gen8 = tmp_path / "gen8"
    assert (gen8 / "test_txd+hi.ytd").is_file()
    assert (gen8 / "test_txd+hi" / "hd_tex.dds").read_bytes() == full_dds
    assert (gen8 / "test_txd" / "hd_tex.dds").read_bytes() == dropped_mip(full_dds)
    assert (gen8 / "test_txd" / "sd_tex.dds").read_bytes() == sd_dds

    bpy.ops.wm.read_homefile()
    bpy.ops.sollumz.import_assets(
        directory=str(gen8),
        files=[{"name": import_file}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS | {"textures_mode": textures_mode},
    )

    txds = context.scene.sz_txds.texture_dictionaries
    assert len(txds) == 1
    txd = txds[0]
    assert txd.name == "test_txd"

    slots = {t.name: t for t in txd.textures}
    assert set(slots) == {"hd_tex", "sd_tex"}

    hd_img = slots["hd_tex"].image
    sd_img = slots["sd_tex"].image
    assert hd_img.sz_is_hd
    assert not sd_img.sz_is_hd

    if textures_mode == "PACK":
        assert_dds_is_full_res(hd_img.packed_file.data, (16, 16))
        assert_dds_is_full_res(sd_img.packed_file.data, (16, 16))
    else:
        assert Path(hd_img.filepath).parent.name == "test_txd+hi"
        assert Path(hd_img.filepath).read_bytes() == full_dds
        assert Path(sd_img.filepath).parent.name == "test_txd"
        assert Path(sd_img.filepath).read_bytes() == sd_dds

    assert "hd_tex.dds.001" not in bpy.data.images


@requires_szio_native
@assert_logs_no_warnings_or_errors
def test_import_hi_ytd_selects_base(context, tmp_path):
    from .test_import_export import DEFAULT_IMPORT_SETTINGS

    _setup_and_export_hi_txd(context, tmp_path)

    bpy.ops.wm.read_homefile()
    bpy.ops.sollumz.import_assets(
        directory=str(tmp_path / "gen8"),
        files=[{"name": "test_txd+hi.ytd"}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS,
    )

    txds = context.scene.sz_txds.texture_dictionaries
    assert len(txds) == 1
    txd = txds[0]
    assert txd.name == "test_txd"

    slots = {t.name: t for t in txd.textures}
    assert set(slots) == {"hd_tex", "sd_tex"}
    assert slots["hd_tex"].image.sz_is_hd
    assert_dds_is_full_res(slots["hd_tex"].image.packed_file.data, (16, 16))
    assert_dds_is_full_res(slots["sd_tex"].image.packed_file.data, (16, 16))


@requires_szio_native
@assert_logs_no_warnings_or_errors
def test_import_both_base_and_hi_ytd_dedupes(context, tmp_path):
    from .test_import_export import DEFAULT_IMPORT_SETTINGS

    _setup_and_export_hi_txd(context, tmp_path)

    bpy.ops.wm.read_homefile()
    bpy.ops.sollumz.import_assets(
        directory=str(tmp_path / "gen8"),
        files=[{"name": "test_txd.ytd"}, {"name": "test_txd+hi.ytd"}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS,
    )

    txds = context.scene.sz_txds.texture_dictionaries
    assert len(txds) == 1
    assert txds[0].name == "test_txd"
    assert "hd_tex.dds.001" not in bpy.data.images

    slots = {t.name: t for t in txds[0].textures}
    assert set(slots) == {"hd_tex", "sd_tex"}
    assert slots["hd_tex"].image.sz_is_hd
    assert not slots["sd_tex"].image.sz_is_hd


@requires_szio_native
@assert_logs_no_warnings_or_errors
def test_import_hi_ytd_without_base(context, tmp_path):
    from .test_import_export import DEFAULT_IMPORT_SETTINGS

    _setup_and_export_hi_txd(context, tmp_path)

    hi_only_dir = tmp_path / "hi_only"
    hi_only_dir.mkdir()
    shutil.copyfile(tmp_path / "gen8" / "test_txd+hi.ytd", hi_only_dir / "test_txd+hi.ytd")

    bpy.ops.wm.read_homefile()
    bpy.ops.sollumz.import_assets(
        directory=str(hi_only_dir),
        files=[{"name": "test_txd+hi.ytd"}],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS,
    )

    # Without the base .ytd next to it, the +hi.ytd imports as a regular texture dictionary
    txds = context.scene.sz_txds.texture_dictionaries
    assert len(txds) == 1
    txd = txds[0]
    assert txd.name == "test_txd+hi"

    slots = {t.name: t for t in txd.textures}
    assert set(slots) == {"hd_tex"}
    assert not slots["hd_tex"].image.sz_is_hd
    assert_dds_is_full_res(slots["hd_tex"].image.packed_file.data, (16, 16))


def _new_missing_image(name: str, tmp_path: Path, filename: str) -> Image:
    """Creates an image whose source file does not exist, like the placeholders the importers create
    for textures that could not be found.
    """
    img = bpy.data.images.new(name=name, width=1, height=1)
    img.source = "FILE"
    img.filepath = str(tmp_path / "does_not_exist" / filename)
    return img


def _new_material_using_image(name: str, img: Image) -> ShaderNodeTexImage:
    """Creates a material with a texture node referencing `img` and returns the node."""
    mat = bpy.data.materials.new(name)
    if bpy.app.version < (5, 0, 0):
        mat.use_nodes = True
    node = mat.node_tree.nodes.new("ShaderNodeTexImage")
    node.image = img
    return node


def _new_txd_with_packed_texture(context, name: str):
    txd = context.scene.sz_txds.new_texture_dictionary(name="test_txd")
    img = new_packed_dds_image(name, make_bc1_dds(4, 4, 1))
    txd.new_texture(img)
    return txd, img


@assert_logs_no_warnings_or_errors
def test_txd_find_missing_replaces_missing_images(context, tmp_path):
    bpy.ops.wm.read_homefile()
    _, txd_img = _new_txd_with_packed_texture(context, "tex_a.dds")

    missing = _new_missing_image("missing_placeholder_a", tmp_path, "tex_a.dds")
    node_a = _new_material_using_image("mat_a", missing)
    node_b = _new_material_using_image("mat_b", missing)

    unmatched = _new_missing_image("missing_placeholder_b", tmp_path, "tex_b.dds")
    node_c = _new_material_using_image("mat_c", unmatched)

    assert bpy.ops.sollumz.txd_find_missing() == {"FINISHED"}

    # all users of the missing image are remapped to the txd texture and the placeholder is deleted
    assert node_a.image == txd_img
    assert node_b.image == txd_img
    assert "missing_placeholder_a" not in bpy.data.images

    # missing images without a matching texture are left untouched
    assert node_c.image == unmatched
    assert "missing_placeholder_b" in bpy.data.images


@pytest.mark.parametrize("tex_filename", ("tex.dds", "TEX.dds", "tex.png"))
@pytest.mark.parametrize("missing_filename", ("tex.dds", "TEX.DDS", "tex.png"))
@assert_logs_no_warnings_or_errors
def test_txd_find_missing_name_matching(context, tmp_path, tex_filename, missing_filename):
    bpy.ops.wm.read_homefile()
    _, txd_img = _new_txd_with_packed_texture(context, tex_filename)

    missing = _new_missing_image("missing", tmp_path, missing_filename)
    orig_name = missing.name
    node = _new_material_using_image("mat", missing)

    bpy.ops.sollumz.txd_find_missing()

    assert node.image == txd_img
    assert orig_name not in bpy.data.images


@assert_logs_no_warnings_or_errors
def test_txd_find_missing_skips_images_that_are_not_missing(context, tmp_path):
    bpy.ops.wm.read_homefile()
    _new_txd_with_packed_texture(context, "tex.dds")

    # an image whose file exists on disk is not missing, even if a texture with the same name exists
    on_disk_path = tmp_path / "tex.dds"
    on_disk_path.write_bytes(b"content does not matter")
    on_disk = bpy.data.images.new(name="tex", width=1, height=1)
    on_disk.source = "FILE"
    on_disk.filepath = str(on_disk_path)
    node_a = _new_material_using_image("mat_a", on_disk)

    # a packed image is not missing either
    packed = new_packed_dds_image("packed_tex", make_bc1_dds(4, 4, 1), filename="tex.dds")
    node_b = _new_material_using_image("mat_b", packed)

    bpy.ops.sollumz.txd_find_missing()

    assert node_a.image == on_disk
    assert node_b.image == packed
    assert "tex" in bpy.data.images
    assert "packed_tex" in bpy.data.images


@assert_logs_no_warnings_or_errors
def test_txd_find_missing_never_replaces_txd_images(context, tmp_path):
    bpy.ops.wm.read_homefile()
    txd, _ = _new_txd_with_packed_texture(context, "tex.dds")

    # a txd texture whose own file is missing must not be replaced or deleted, even though the
    # packed "tex.dds" texture has the same name
    missing_txd_img = _new_missing_image("tex_missing", tmp_path, "tex.dds")
    txd.new_texture(missing_txd_img)

    bpy.ops.sollumz.txd_find_missing()

    assert "tex_missing" in bpy.data.images
    assert txd.textures[1].image == missing_txd_img
