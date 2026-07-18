import bpy
import numpy as np
import pytest
from numpy.testing import assert_allclose

from ..sollumz_properties import LODLevel, SollumType
from .shared import load_blend_data


@pytest.mark.parametrize("bake_type", ("DIFFUSE", "NORMAL"))
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


@pytest.mark.parametrize(
    "op_kwargs",
    (
        pytest.param(
            dict(
                decimate_method="COLLAPSE",
                decimate_step=0.5,
            ),
            id="collapse",
        ),
        pytest.param(
            dict(
                decimate_method="COLLAPSE",
                decimate_step=0.2,
                decimate_from_original=True,
            ),
            id="collapse_from_original",
        ),
        pytest.param(
            dict(
                decimate_method="UNSUBDIV",
                unsubdiv_iterations=2,
            ),
            id="unsubdiv",
        ),
        pytest.param(
            dict(
                decimate_method="DISSOLVE",
                planar_angle_limit=0.087266,
            ),
            id="dissolve",
        ),
        pytest.param(
            dict(
                decimate_method="COLLAPSE",
                use_per_lod_ratios=True,
                per_lod_ratio=(1.0, 0.8, 0.5, 0.25, 0.1),
            ),
            id="per_lod_ratios",
        ),
        pytest.param(
            dict(
                decimate_method="COLLAPSE",
                use_per_lod_ratios=True,
                per_lod_use_target_tri_count=(True, True, True, True, True),
                per_lod_target_tri_count=(500, 400, 300, 200, 100),
            ),
            id="per_lod_target_tri_count",
        ),
    ),
)
def test_ops_lod_tools_auto_lod(op_kwargs, context):
    bpy.ops.wm.read_homefile()
    bpy.ops.mesh.primitive_monkey_add()
    obj = context.object
    obj.sollum_type = SollumType.DRAWABLE_MODEL
    obj.sz_lods.get_lod(LODLevel.VERYHIGH).mesh = obj.data
    obj.sz_lods.active_lod_level = LODLevel.VERYHIGH

    ref_mesh = obj.data
    ref_vert_count = len(ref_mesh.vertices)

    generated_lod_levels = (LODLevel.HIGH, LODLevel.MEDIUM, LODLevel.LOW, LODLevel.VERYLOW)

    result = bpy.ops.sollumz.auto_lod(
        ref_mesh_name=ref_mesh.name,
        levels={lod_level.value for lod_level in generated_lod_levels},
        **op_kwargs,
    )
    assert result == {"FINISHED"}

    assert obj.sz_lods.active_lod_level == LODLevel.VERYHIGH
    assert obj.data == ref_mesh

    for lod_level in generated_lod_levels:
        mesh = obj.sz_lods.get_lod(lod_level).mesh
        assert mesh is not None
        assert len(mesh.vertices) < ref_vert_count
