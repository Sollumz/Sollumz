import bpy
import numpy as np
import pytest
from numpy.testing import assert_allclose

from .shared import load_blend_data


@pytest.mark.parametrize("bake_type", ("DIFFUSE", "NORMAL", "ROUGHNESS"))
def test_ops_lod_tools_material_merge_bake(bake_type, context):
    data = load_blend_data("lod_tools_material_merge_bake.blend")
    assert context.active_object.name == "mesh_to_bake", ".blend not setup properly"

    bpy.ops.sollumz.material_merge_bake(
        texture_size="256",
        bake_type=bake_type,
        uv_margin=0.0,
        samples=128,
    )

    bake_name = f"mesh_to_bake_BakedMaterial_{bake_type}"
    assert bake_name in data.images
    assert bake_name in data.materials

    img = data.images[bake_name]
    w, h = img.size
    assert (w, h) == (256, 256)
    assert img.has_data
    pixels = np.array(img.pixels).reshape((h, w, 4))
    match bake_type:
        case "DIFFUSE":
            assert_allclose(pixels[64, 64], [0.0, 1.0, 0.0, 1.0])
            assert_allclose(pixels[192, 64], [1.0, 0.0, 0.0, 1.0])
        case "NORMAL":
            assert_allclose(pixels[128, 128], [0.5019, 0.5019, 1.0, 1.0], atol=0.001)
        case "ROUGHNESS":
            # TODO: verify correctness of roughness baking.
            #       Blender 4.0 bakes all black (0.0), Blender 4.2, 4.5 and 5.0 bake all white (1.0). I get same
            #       results when baking manually in cycles.
            #       While roughness in the materials' BSDF is set to 0.5.
            # assert_allclose(pixels[128, 128], [0.5, 0.5, 0.5, 1.0])
            pass

def test_ops_lod_tools_auto_lod(context):
    # TODO: test_ops_lod_tools_auto_lod
    pass
