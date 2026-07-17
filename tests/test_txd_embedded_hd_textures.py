import xml.etree.ElementTree as ET
from pathlib import Path

import bpy
import pytest

from ..lods import LODLevel
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_blender_object, create_empty_object
from ..tools.drawablehelper import convert_obj_to_drawable, convert_objs_to_single_drawable
from ..ytd.ytdexport import split_embedded_texture
from .shared import (
    assert_dds_is_full_res,
    assert_logs_no_warnings_or_errors,
    dropped_mip,
    log_capture,
    make_bc1_dds,
    new_packed_dds_image,
)


def _import_files(directory: Path, files: list[str], textures_mode: str = "PACK"):
    from .test_import_export import DEFAULT_IMPORT_SETTINGS

    bpy.ops.wm.read_homefile()
    bpy.ops.sollumz.import_assets(
        directory=str(directory),
        files=[{"name": f} for f in files],
        use_custom_settings=True,
        **DEFAULT_IMPORT_SETTINGS | {"textures_mode": textures_mode},
    )


def test_split_embedded_texture_not_hd():
    dds = make_bc1_dds(16, 16, 3)
    img = new_packed_dds_image("tex.dds", dds)

    with log_capture() as logs:
        texture, hi_texture = split_embedded_texture(img, "tex")

    logs.assert_no_warnings_or_errors()
    assert hi_texture is None
    assert (texture.width, texture.height) == (16, 16)
    assert texture.data.read_bytes() == dds


def test_split_embedded_texture_hd():
    dds = make_bc1_dds(16, 16, 3)
    img = new_packed_dds_image("tex.dds", dds)
    img.sz_is_hd = True

    with log_capture() as logs:
        texture, hi_texture = split_embedded_texture(img, "tex")

    logs.assert_no_warnings_or_errors()
    assert (texture.width, texture.height) == (8, 8)
    assert texture.data.read_bytes() == dropped_mip(dds)
    assert (hi_texture.width, hi_texture.height) == (16, 16)
    assert hi_texture.data.read_bytes() == dds


def test_split_embedded_texture_hd_single_mip_keeps_full_res():
    dds = make_bc1_dds(16, 16, 1)
    img = new_packed_dds_image("tex.dds", dds)
    img.sz_is_hd = True

    with log_capture() as logs:
        texture, hi_texture = split_embedded_texture(img, "tex")

    logs.assert_warning(match="Cannot drop first mip")
    assert (texture.width, texture.height) == (16, 16)
    assert texture.data.read_bytes() == dds
    assert (hi_texture.width, hi_texture.height) == (16, 16)
    assert hi_texture.data.read_bytes() == dds


def _new_plane_obj(name: str) -> bpy.types.Object:
    bpy.ops.mesh.primitive_plane_add()
    obj = bpy.context.object
    obj.name = name
    return obj


def _add_material_with_texture(obj: bpy.types.Object, img: bpy.types.Image, embedded: bool = True):
    """Adds a default shader material to `obj` with `img` assigned to its DiffuseSampler."""
    from ..tools.meshhelper import mesh_add_missing_color_attrs, mesh_add_missing_uv_maps
    from ..ydr.shader_materials import create_shader

    mat = create_shader("default.sps")
    obj.data.materials.append(mat)
    mesh_add_missing_uv_maps(obj.data)
    mesh_add_missing_color_attrs(obj.data)

    node = mat.node_tree.nodes["DiffuseSampler"]
    node.image = img
    node.texture_properties.embedded = embedded
    return mat


def _export_obj(obj: bpy.types.Object, tmp_path: Path):
    from .test_import_export import DEFAULT_EXPORT_SETTINGS

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)

    bpy.ops.sollumz.export_assets(
        directory=str(tmp_path.absolute()),
        direct_export=True,
        use_custom_settings=True,
        **DEFAULT_EXPORT_SETTINGS,
    )


def _embedded_texture_sizes(xml_path: Path, texture_name: str) -> list[tuple[int, int]]:
    """Sizes of every embedded texture named `texture_name` declared in the CWXML file."""
    sizes = []
    for item in ET.parse(xml_path).getroot().iter("Item"):
        name_elem = item.find("Name")
        width_elem = item.find("Width")
        if name_elem is not None and width_elem is not None and name_elem.text == texture_name:
            sizes.append((int(width_elem.get("value")), int(item.find("Height").get("value"))))
    return sizes


def _setup_and_export_hd_drawable(tmp_path: Path) -> tuple[bytes, bytes]:
    """Creates a drawable with an HD texture and a normal texture, then exports it.
    Returns the full-resolution DDS bytes of the HD texture and of the normal texture.
    """
    bpy.ops.wm.read_homefile()

    full_dds = make_bc1_dds(16, 16, 3)
    sd_dds = make_bc1_dds(16, 16, 1)
    hd_img = new_packed_dds_image("hd_tex.dds", full_dds)
    hd_img.sz_is_hd = True
    sd_img = new_packed_dds_image("sd_tex.dds", sd_dds)

    hd_obj = _new_plane_obj("hd_model")
    _add_material_with_texture(hd_obj, hd_img)
    sd_obj = _new_plane_obj("sd_model")
    _add_material_with_texture(sd_obj, sd_img)
    drawable_obj = convert_objs_to_single_drawable([hd_obj, sd_obj])
    drawable_obj.name = "test_drawable"

    _export_obj(drawable_obj, tmp_path)
    return full_dds, sd_dds


@assert_logs_no_warnings_or_errors
def test_export_ydr_splits_hd_embedded_textures(tmp_path):
    full_dds, sd_dds = _setup_and_export_hd_drawable(tmp_path)

    for gen in ("gen8", "gen9"):
        d = tmp_path / gen
        assert (d / "test_drawable+hidr.ytd.xml").is_file()
        assert (d / "test_drawable" / "hd_tex.dds").read_bytes() == dropped_mip(full_dds)
        assert (d / "test_drawable" / "sd_tex.dds").read_bytes() == sd_dds
        assert (d / "test_drawable+hidr" / "hd_tex.dds").read_bytes() == full_dds
        assert not (d / "test_drawable+hidr" / "sd_tex.dds").exists()

    gen8 = tmp_path / "gen8"
    assert _embedded_texture_sizes(gen8 / "test_drawable.ydr.xml", "hd_tex") == [(8, 8)]
    assert _embedded_texture_sizes(gen8 / "test_drawable.ydr.xml", "sd_tex") == [(16, 16)]
    assert _embedded_texture_sizes(gen8 / "test_drawable+hidr.ytd.xml", "hd_tex") == [(16, 16)]
    assert _embedded_texture_sizes(gen8 / "test_drawable+hidr.ytd.xml", "sd_tex") == []


@assert_logs_no_warnings_or_errors
def test_export_ydr_without_hd_textures_has_no_hidr(tmp_path):
    bpy.ops.wm.read_homefile()

    sd_dds = make_bc1_dds(16, 16, 1)
    sd_img = new_packed_dds_image("sd_tex.dds", sd_dds)

    obj = _new_plane_obj("test_drawable")
    _add_material_with_texture(obj, sd_img)
    drawable_obj = convert_obj_to_drawable(obj)

    _export_obj(drawable_obj, tmp_path)

    for gen in ("gen8", "gen9"):
        d = tmp_path / gen
        assert (d / "test_drawable.ydr.xml").is_file()
        assert (d / "test_drawable" / "sd_tex.dds").read_bytes() == sd_dds
        assert not (d / "test_drawable+hidr.ytd").exists()
        assert not (d / "test_drawable+hidr.ytd.xml").exists()
        assert not (d / "test_drawable+hidr").exists()


def _new_fragment_obj(name: str) -> bpy.types.Object:
    """Creates a minimal valid fragment: an armature object with a single bone."""
    armature = bpy.data.armatures.new(f"{name}.skel")
    frag_obj = create_blender_object(SollumType.FRAGMENT, name, armature)

    bpy.context.view_layer.objects.active = frag_obj
    bpy.ops.object.mode_set(mode="EDIT")
    bone = armature.edit_bones.new("root")
    bone.tail = (0.0, 0.0, 0.1)
    bpy.ops.object.mode_set(mode="OBJECT")
    return frag_obj


def _setup_and_export_hd_fragment(tmp_path: Path, with_hi_lod: bool = False) -> bytes:
    """Creates a fragment with an HD texture, then exports it. With `with_hi_lod`, the model gets a very
    high LOD so a _hi.yft is exported along the base .yft. Returns the full-resolution DDS bytes of the
    HD texture.
    """
    bpy.ops.wm.read_homefile()

    full_dds = make_bc1_dds(16, 16, 3)
    hd_img = new_packed_dds_image("hd_tex.dds", full_dds)
    hd_img.sz_is_hd = True

    frag_obj = _new_fragment_obj("test_frag")
    model_obj = _new_plane_obj("test_frag_model")
    _add_material_with_texture(model_obj, hd_img)
    drawable_obj = convert_obj_to_drawable(model_obj)
    drawable_obj.parent = frag_obj

    if with_hi_lod:
        model_obj.sz_lods.get_lod(LODLevel.VERYHIGH).mesh = model_obj.data.copy()

    _export_obj(frag_obj, tmp_path)
    return full_dds


@assert_logs_no_warnings_or_errors
def test_export_yft_splits_hd_embedded_textures(tmp_path):
    full_dds = _setup_and_export_hd_fragment(tmp_path)

    for gen in ("gen8", "gen9"):
        d = tmp_path / gen
        assert (d / "test_frag+hifr.ytd.xml").is_file()
        assert not (d / "test_frag_hi.yft.xml").exists()
        assert (d / "test_frag" / "hd_tex.dds").read_bytes() == dropped_mip(full_dds)
        assert (d / "test_frag+hifr" / "hd_tex.dds").read_bytes() == full_dds

    gen8 = tmp_path / "gen8"
    assert _embedded_texture_sizes(gen8 / "test_frag.yft.xml", "hd_tex") == [(8, 8)]
    assert _embedded_texture_sizes(gen8 / "test_frag+hifr.ytd.xml", "hd_tex") == [(16, 16)]


def _setup_and_export_hd_dwd(tmp_path: Path) -> bytes:
    """Creates a drawable dictionary with three drawables that share HD textures, then exports it.
    Returns the full-resolution DDS bytes of the HD textures.
    """
    bpy.ops.wm.read_homefile()

    full_dds = make_bc1_dds(16, 16, 3)
    hd_img = new_packed_dds_image("hd_tex.dds", full_dds)
    hd_img.sz_is_hd = True
    hd_img_2 = new_packed_dds_image("hd_tex_2.dds", full_dds)
    hd_img_2.sz_is_hd = True

    dwd_obj = create_empty_object(SollumType.DRAWABLE_DICTIONARY)
    dwd_obj.name = "test_dwd"
    for i in range(3):
        obj = _new_plane_obj(f"test_dwd_child_{i}")
        _add_material_with_texture(obj, hd_img if i <= 1 else hd_img_2)
        drawable_obj = convert_obj_to_drawable(obj)
        drawable_obj.parent = dwd_obj

    _export_obj(dwd_obj, tmp_path)
    return full_dds


@assert_logs_no_warnings_or_errors
def test_export_ydd_merges_hd_textures_across_drawables(tmp_path):
    full_dds = _setup_and_export_hd_dwd(tmp_path)

    gen8 = tmp_path / "gen8"
    # Each child drawable embeds its own mip-dropped copy, the +hidd texture dictionary contains the
    # full-resolution texture only once
    assert _embedded_texture_sizes(gen8 / "test_dwd.ydd.xml", "hd_tex") == [(8, 8), (8, 8)]
    assert _embedded_texture_sizes(gen8 / "test_dwd+hidd.ytd.xml", "hd_tex") == [(16, 16)]

    assert _embedded_texture_sizes(gen8 / "test_dwd.ydd.xml", "hd_tex_2") == [(8, 8)]
    assert _embedded_texture_sizes(gen8 / "test_dwd+hidd.ytd.xml", "hd_tex_2") == [(16, 16)]

    for gen in ("gen8", "gen9"):
        d = tmp_path / gen
        assert (d / "test_dwd" / "hd_tex.dds").read_bytes() == dropped_mip(full_dds)
        assert (d / "test_dwd" / "hd_tex_2.dds").read_bytes() == dropped_mip(full_dds)
        assert (d / "test_dwd+hidd" / "hd_tex.dds").read_bytes() == full_dds
        assert (d / "test_dwd+hidd" / "hd_tex_2.dds").read_bytes() == full_dds


@pytest.mark.parametrize("textures_mode", ("PACK", "IMPORT_DIR"))
@assert_logs_no_warnings_or_errors
def test_import_ydr_uses_hd_txd(context, tmp_path, textures_mode):
    full_dds, sd_dds = _setup_and_export_hd_drawable(tmp_path)

    _import_files(tmp_path / "gen8", ["test_drawable.ydr.xml"], textures_mode=textures_mode)

    hd_img = bpy.data.images["hd_tex.dds"]
    sd_img = bpy.data.images["sd_tex.dds"]
    assert hd_img.sz_is_hd
    assert not sd_img.sz_is_hd

    if textures_mode == "PACK":
        assert_dds_is_full_res(hd_img.packed_file.data, (16, 16))
        assert sd_img.packed_file.data == sd_dds
    else:
        assert Path(hd_img.filepath).parent.name == "test_drawable+hidr"
        assert Path(hd_img.filepath).read_bytes() == full_dds
        assert Path(sd_img.filepath).parent.name == "test_drawable"
        assert Path(sd_img.filepath).read_bytes() == sd_dds

    assert "hd_tex.dds.001" not in bpy.data.images
    assert len(context.scene.sz_txds.texture_dictionaries) == 0


@assert_logs_no_warnings_or_errors
def test_import_ydr_with_hd_txd_selected_dedupes(context, tmp_path):
    _setup_and_export_hd_drawable(tmp_path)

    _import_files(tmp_path / "gen8", ["test_drawable.ydr.xml", "test_drawable+hidr.ytd.xml"])

    # The HD txd is consumed by the drawable import, not imported as a standalone texture dictionary
    assert len(context.scene.sz_txds.texture_dictionaries) == 0
    hd_img = bpy.data.images["hd_tex.dds"]
    assert hd_img.sz_is_hd
    assert_dds_is_full_res(hd_img.packed_file.data, (16, 16))
    assert "hd_tex.dds.001" not in bpy.data.images


@assert_logs_no_warnings_or_errors
def test_import_lone_hd_txd_as_regular_txd(context, tmp_path):
    _setup_and_export_hd_drawable(tmp_path)

    _import_files(tmp_path / "gen8", ["test_drawable+hidr.ytd.xml"])

    txds = context.scene.sz_txds.texture_dictionaries
    assert len(txds) == 1
    txd = txds[0]
    assert txd.name == "test_drawable+hidr"

    slots = {t.name: t for t in txd.textures}
    assert set(slots) == {"hd_tex"}
    assert not slots["hd_tex"].image.sz_is_hd
    assert_dds_is_full_res(slots["hd_tex"].image.packed_file.data, (16, 16))


@assert_logs_no_warnings_or_errors
def test_import_yft_uses_hd_txd(tmp_path):
    _setup_and_export_hd_fragment(tmp_path)

    _import_files(tmp_path / "gen8", ["test_frag.yft.xml"])

    hd_img = bpy.data.images["hd_tex.dds"]
    assert hd_img.sz_is_hd
    assert_dds_is_full_res(hd_img.packed_file.data, (16, 16))
    assert "hd_tex.dds.001" not in bpy.data.images


@pytest.mark.parametrize("import_file", ("test_frag.yft.xml", "test_frag_hi.yft.xml"))
@assert_logs_no_warnings_or_errors
def test_import_yft_with_hi_uses_hd_txd(tmp_path, import_file):
    _setup_and_export_hd_fragment(tmp_path, with_hi_lod=True)

    gen8 = tmp_path / "gen8"
    assert (gen8 / "test_frag_hi.yft.xml").is_file()
    _import_files(gen8, [import_file])

    hd_img = bpy.data.images["hd_tex.dds"]
    assert hd_img.sz_is_hd
    assert_dds_is_full_res(hd_img.packed_file.data, (16, 16))
    assert "hd_tex.dds.001" not in bpy.data.images


@assert_logs_no_warnings_or_errors
def test_import_ydd_shared_hd_texture(tmp_path):
    _setup_and_export_hd_dwd(tmp_path)

    _import_files(tmp_path / "gen8", ["test_dwd.ydd.xml"])

    hd_img = bpy.data.images["hd_tex.dds"]
    hd_img_2 = bpy.data.images["hd_tex_2.dds"]
    assert hd_img.sz_is_hd
    assert hd_img_2.sz_is_hd
    assert_dds_is_full_res(hd_img.packed_file.data, (16, 16))
    assert_dds_is_full_res(hd_img_2.packed_file.data, (16, 16))
    # The texture shared by two child drawables resolves to a single image
    assert "hd_tex.dds.001" not in bpy.data.images


@assert_logs_no_warnings_or_errors
def test_import_export_roundtrip_preserves_hd_split(tmp_path):
    full_dds, sd_dds = _setup_and_export_hd_drawable(tmp_path)

    _import_files(tmp_path / "gen8", ["test_drawable.ydr.xml"])

    roundtrip_path = tmp_path / "roundtrip"
    roundtrip_path.mkdir()
    _export_obj(bpy.data.objects["test_drawable"], roundtrip_path)

    gen8 = roundtrip_path / "gen8"
    assert _embedded_texture_sizes(gen8 / "test_drawable.ydr.xml", "hd_tex") == [(8, 8)]
    assert _embedded_texture_sizes(gen8 / "test_drawable.ydr.xml", "sd_tex") == [(16, 16)]
    assert _embedded_texture_sizes(gen8 / "test_drawable+hidr.ytd.xml", "hd_tex") == [(16, 16)]
    assert _embedded_texture_sizes(gen8 / "test_drawable+hidr.ytd.xml", "sd_tex") == []
    assert (gen8 / "test_drawable" / "hd_tex.dds").read_bytes() == dropped_mip(full_dds)
    assert (gen8 / "test_drawable" / "sd_tex.dds").read_bytes() == sd_dds
    assert (gen8 / "test_drawable+hidr" / "hd_tex.dds").read_bytes() == full_dds
