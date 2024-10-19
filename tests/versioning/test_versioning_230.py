from numpy.testing import assert_array_equal
from .shared import load_blend_data
from ...shared.shader_nodes import SzShaderNodeParameter
from ...ydr.render_bucket import RenderBucket


def test_versioning_material_render_buckets():
    data = load_blend_data("v230_material_render_buckets.blend")

    for mat_name, expected_render_bucket in (
        ("rb_0", RenderBucket.OPAQUE),
        ("rb_1", RenderBucket.ALPHA),
        ("rb_2", RenderBucket.DECAL),
        ("rb_3", RenderBucket.CUTOUT),
        ("rb_4", RenderBucket.NO_SPLASH),
        ("rb_5", RenderBucket.NO_WATER),
        ("rb_6", RenderBucket.WATER),
        ("rb_7", RenderBucket.DISPLACEMENT_ALPHA),
    ):
        mat = data.materials[mat_name]
        assert mat.shader_properties.renderbucket == expected_render_bucket.name


def test_versioning_material_shader_parameters():
    data = load_blend_data("v230_material_shader_parameters.blend")

    m = data.materials["dummy_material"]
    for param_name, expected_values in (
        ("specularFalloffMult", (1234.0,)),
        ("envEffTexTileUV", (1.0,)),
        ("envEffScale", (5.0, 6.0)),
        ("envEffThickness", (9.0,)),
        ("diffuse2SpecMod", (13.0,)),
        ("reflectivePower", (17.0,)),
        ("specular2Color_DirLerp", (10.0, 20.0, 30.0, 40.0)),
        ("specMapIntMask", (12.0, 23.0, 34.0)),
        ("DamagedWheelOffsets", (1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0)),
    ):
        n = m.node_tree.nodes.get(param_name, None)
        assert isinstance(n, SzShaderNodeParameter)

        n_values = [n.get(i) for i in range(n.num_cols * n.num_rows)]
        assert_array_equal(n_values, expected_values)


def test_versioning_fragment_properties():
    data = load_blend_data("v230_fragment.blend")

    frag_obj = data.objects["sollumz_cube"]
    fragment_properties = frag_obj.fragment_properties
    lod_properties = fragment_properties.lod_properties
    archetype_properties = lod_properties.archetype_properties
    bone = frag_obj.data.bones["sollumz_cube_01"]
    group_properties = bone.group_properties
    drawable_model_mesh = data.meshes["sollumz_cube_01_high"]
    drawable_model_properties = drawable_model_mesh.drawable_model_properties
    col_obj = data.objects["sollumz_cube_01.col"]
    veh_window_properties = col_obj.vehicle_window_properties

    # fragment properties
    for prop_name, expected_value in (
        ("flags", 12),
        ("unbroken_elasticity", 23.0),
        ("template_asset", 3),
    ):
        assert fragment_properties.get(prop_name, None) == expected_value, prop_name

    # LOD properties
    for prop_name, expected_value in (
        ("smallest_ang_inertia", 11.0),
        ("largest_ang_inertia", 22.0),
        ("min_move_force", 33.0),
    ):
        assert lod_properties.get(prop_name, None) == expected_value, prop_name
    for prop_name, expected_value in (
        ("original_root_cg_offset", (4.0, 5.0, 6.0)),
        ("unbroken_cg_offset", (7.0, 8.0, 9.0)),
    ):
        assert_array_equal(lod_properties.get(prop_name, None), expected_value, prop_name)

    # Archetype properties
    for prop_name, expected_value in (
        ("gravity_factor", 12.0),
        ("max_speed", 23.0),
        ("max_ang_speed", 34.0),
        ("buoyancy_factor", 45.0),
    ):
        assert archetype_properties.get(prop_name, None) == expected_value, prop_name

    # Group properties
    for prop_name, expected_value in (
        ("weapon_health", 11.0),
        ("weapon_scale", 22.0),
        ("vehicle_scale", 33.0),
        ("ped_scale", 44.0),
        ("ragdoll_scale", 55.0),
        ("explosion_scale", 66.0),
        ("object_scale", 77.0),
        ("ped_inv_mass_scale", 88.0),
        ("melee_scale", 99.0),
    ):
        assert group_properties.get(prop_name, None) == expected_value, prop_name

    # Vehicle window properties
    for prop_name, expected_value in (
        ("data_min", 11.0),
        ("data_max", 22.0),
    ):
        assert veh_window_properties.get(prop_name, None) == expected_value, prop_name

    # Drawable model properties
    for prop_name, expected_value in (
        ("matrix_count", 123),
    ):
        assert drawable_model_properties.get(prop_name, None) == expected_value, prop_name


def test_versioning_bone_tags():
    data = load_blend_data("v200_armature.blend")

    armature = data.armatures["dummy_armature"]
    root_bone = armature.bones["ROOT"]
    bone = armature.bones["DUMMY_BONE"]

    assert root_bone.bone_properties.tag == 0
    assert root_bone.bone_properties.use_manual_tag is False
    assert bone.bone_properties.tag == 1234
    assert bone.bone_properties.use_manual_tag is True
    assert bone.bone_properties.manual_tag == 1234
