import pytest
import bpy


def pytest_sessionstart(session):
    # Re-enable so coverage correctly includes startup/registration code
    bpy.ops.preferences.addon_disable(module="Sollumz")
    bpy.ops.preferences.addon_enable(module="Sollumz")


@pytest.fixture()
def context():
    return bpy.context


@pytest.fixture()
def prefs_temp_file(tmp_path, monkeypatch):
    """Redirect preferences to an isolated temp .ini and restore the real preferences afterwards. Use it in any test
    that changes the preferences, directly or through an operator, so nothing touches (or leaks into) the developer's
    real Sollumz preferences.

    `_save_preferences` / `_load_preferences` resolve the file through the module-global `prefs_file_path` (imported by
    name at module load), so the patch must be applied on `sollumz_preferences` itself, not on `known_paths`.
    """
    from .. import sollumz_preferences as prefs_mod
    from .. import sollumz_tool
    from .. import sollumz_ui

    ini_path = tmp_path / "sollumz_prefs.ini"
    monkeypatch.setattr(prefs_mod, "prefs_file_path", lambda: str(ini_path))

    prefs = prefs_mod.get_addon_preferences()
    # Snapshot the real preferences so any mutation a test makes is rolled back afterwards.
    snapshot = prefs_mod._get_bpy_struct_as_dict(prefs)
    try:
        yield ini_path
    finally:
        prefs_mod._update_bpy_struct_from_dict(prefs, snapshot, eval_strings=True)
        # `_load_preferences` syncs the REAL panel/tool visibility state; sync it back from the
        # restored collections so no visibility state leaks into other tests
        sollumz_ui.panel_visibility().sync(prefs.hidden_panels)
        sollumz_tool.tool_visibility().sync(prefs.hidden_tools)


@pytest.fixture()
def plane_object(context):
    bpy.ops.mesh.primitive_plane_add()
    obj = context.object
    obj_name = obj.name

    yield obj

    obj = bpy.data.objects.get(obj_name, None)
    if obj:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        bpy.ops.object.delete()

@pytest.fixture()
def four_plane_objects(context):
    objs = []
    bpy.ops.mesh.primitive_plane_add(location=(2.0, 0.0, 0.0))
    objs.append(context.object)
    bpy.ops.mesh.primitive_plane_add(location=(0.0, 2.0, 0.0))
    objs.append(context.object)
    bpy.ops.mesh.primitive_plane_add(location=(-2.0, 0.0, 0.0))
    objs.append(context.object)
    bpy.ops.mesh.primitive_plane_add(location=(0.0, -2.0, 0.0))
    objs.append(context.object)
    objs_names = [o.name for o in objs]

    yield objs

    objs = [o for oname in objs_names if (o := bpy.data.objects.get(oname, None))]
    if objs:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action="DESELECT")
        for obj in objs:
            obj.select_set(True)
        bpy.ops.object.delete()

@pytest.fixture()
def cube_object(context):
    bpy.ops.mesh.primitive_cube_add()
    obj = context.object
    obj_name = obj.name

    yield obj

    obj = bpy.data.objects.get(obj_name, None)
    if obj:
        bpy.ops.object.mode_set(mode="OBJECT")
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        bpy.ops.object.delete()


@pytest.fixture(params=[
    (1, 1.0),
    (30, 2.0),    # 15.0 (just to make sure fps_base is taken into account)
    (24, 1.001),  # 23.98
    (24, 1.0),
    (25, 1.0),
    (30, 1.001),  # 29.97
    (30, 1.0),
    (50, 1.0),
    (60, 1.001),  # 59.94
    (60, 1.0),
    (120, 1.0),
    (240, 1.0),
])
def fps_dependent(request):
    """Runs the test with multiple different FPS settings.
    Passes a tuple (float, str) to the test with the FPS value and its string representation.
    """
    fps, fps_base = request.param
    prev_fps = bpy.context.scene.render.fps, bpy.context.scene.render.fps_base
    bpy.context.scene.render.fps, bpy.context.scene.render.fps_base = fps, fps_base

    yield fps / fps_base, f"{fps / fps_base:.2f}"

    bpy.context.scene.render.fps, bpy.context.scene.render.fps_base = prev_fps
