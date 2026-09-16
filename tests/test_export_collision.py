import bpy
import pytest
from szio.gta5 import AssetFormat, AssetTarget, AssetVersion, BoundPrimitiveType

from ..iecontext import ExportContext, ExportSettings, export_context_scope
from ..sollumz_properties import SollumType
from ..tools.blenderhelper import create_empty_object
from ..ybn.collision_materials import create_collision_material_from_index
from ..ybn.ybnexport import create_bound_asset, export_ybn
from .shared import log_capture


@pytest.mark.parametrize("bound_type, empty_geometry", [
    (SollumType.BOUND_GEOMETRY, "empty_mesh"),
    (SollumType.BOUND_GEOMETRY, "vertices_only"),
    (SollumType.BOUND_GEOMETRY, "modifier"),
    (SollumType.BOUND_GEOMETRYBVH, "empty_mesh"),
    (SollumType.BOUND_GEOMETRYBVH, "vertices_only"),
    (SollumType.BOUND_GEOMETRYBVH, "modifier"),
    (SollumType.BOUND_GEOMETRYBVH, "no_children"),
    (SollumType.BOUND_GEOMETRYBVH, "ignored_child"),
])
def test_export_reports_empty_collision(cube_object, request, bound_type, empty_geometry):
    mesh_obj = cube_object
    mesh_obj.sollum_type = SollumType.BOUND_GEOMETRY
    material = create_collision_material_from_index(0)
    request.addfinalizer(lambda: bpy.data.materials.remove(material, do_unlink=True))
    mesh_obj.data.materials.append(material)
    bound_obj = mesh_obj
    if bound_type == SollumType.BOUND_GEOMETRYBVH:
        bound_obj = create_empty_object(bound_type)
        request.addfinalizer(lambda: bpy.data.objects.remove(bound_obj, do_unlink=True))
        mesh_obj.parent = bound_obj
        mesh_obj.sollum_type = SollumType.BOUND_POLY_TRIANGLE

    if empty_geometry == "empty_mesh":
        mesh_obj.data.clear_geometry()
    elif empty_geometry == "vertices_only":
        mesh_obj.data.clear_geometry()
        mesh_obj.data.from_pydata([(0, 0, 0), (1, 0, 0), (0, 1, 0)], [(0, 1), (1, 2)], [])
    elif empty_geometry == "modifier":
        group = mesh_obj.vertex_groups.new(name="empty")
        modifier = mesh_obj.modifiers.new(name="Remove all geometry", type="MASK")
        modifier.vertex_group = group.name
        assert len(mesh_obj.data.polygons) > 0
    elif empty_geometry == "no_children":
        mesh_obj.parent = None
    elif empty_geometry == "ignored_child":
        mesh_obj.sollum_type = SollumType.NONE

    composite = create_empty_object(SollumType.BOUND_COMPOSITE)
    request.addfinalizer(lambda: bpy.data.objects.remove(composite, do_unlink=True))
    bound_obj.parent = composite
    bpy.context.view_layer.update()

    message = f"'{bound_obj.name}' has no collision primitives"
    with log_capture() as logs:
        bound = create_bound_asset(bound_obj, is_root=True)
    assert bound is not None
    assert not bound.geometry_primitives
    assert len(logs.errors) == 1
    assert message in logs.errors[0]

    # Report all invalid children instead of stopping at the first empty bound.
    other_bound_obj = create_empty_object(SollumType.BOUND_GEOMETRYBVH)
    request.addfinalizer(lambda: bpy.data.objects.remove(other_bound_obj, do_unlink=True))
    other_bound_obj.parent = composite
    bpy.context.view_layer.update()
    settings = ExportSettings(targets=(
        AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8),
        AssetTarget(AssetFormat.NATIVE, AssetVersion.GEN8),
    ))
    with export_context_scope(ExportContext("empty_collision", settings)):
        with log_capture() as logs:
            bundle = export_ybn(composite)
    assert len(bundle.main_asset.children) == 2
    assert len(logs.errors) == 2
    assert any(message in error for error in logs.errors)
    assert any(f"'{other_bound_obj.name}' has no collision primitives" in error for error in logs.errors)


@pytest.mark.parametrize("sollum_type, primitive_type, num_primitives", [
    (SollumType.BOUND_GEOMETRY, BoundPrimitiveType.TRIANGLE, 12),
    (SollumType.BOUND_POLY_TRIANGLE, BoundPrimitiveType.TRIANGLE, 12),
    (SollumType.BOUND_POLY_BOX, BoundPrimitiveType.BOX, 1),
    (SollumType.BOUND_POLY_SPHERE, BoundPrimitiveType.SPHERE, 1),
    (SollumType.BOUND_POLY_CAPSULE, BoundPrimitiveType.CAPSULE, 1),
    (SollumType.BOUND_POLY_CYLINDER, BoundPrimitiveType.CYLINDER, 1),
])
def test_export_preserves_valid_collision(cube_object, request, sollum_type, primitive_type, num_primitives):
    mesh_obj = cube_object
    mesh_obj.sollum_type = sollum_type
    material = create_collision_material_from_index(0)
    request.addfinalizer(lambda: bpy.data.materials.remove(material, do_unlink=True))
    mesh_obj.data.materials.append(material)
    bound_obj = mesh_obj
    if sollum_type != SollumType.BOUND_GEOMETRY:
        bound_obj = create_empty_object(SollumType.BOUND_GEOMETRYBVH)
        request.addfinalizer(lambda: bpy.data.objects.remove(bound_obj, do_unlink=True))
        mesh_obj.parent = bound_obj

    bpy.context.view_layer.update()
    with log_capture() as logs:
        bound = create_bound_asset(bound_obj)

    logs.assert_no_warnings_or_errors()
    assert bound is not None
    assert len(bound.geometry_primitives) == num_primitives
    assert all(prim.primitive_type == primitive_type for prim in bound.geometry_primitives)
