from bpy.types import Panel
from types import SimpleNamespace

from .. import sollumz_ui as ui
from ..tabbed_panels import TabPanel


def _hide(panels: ui.PanelVisibility, *panel_ids: str):
    """Hide `panel_ids` the same way loading the preferences would."""
    panels.sync([SimpleNamespace(name=panel_id) for panel_id in panel_ids])


def _make_panels() -> SimpleNamespace:
    """Dummy panels covering everything the tree builder has to deal with."""

    class _ViewPanel:
        bl_space_type = "VIEW_3D"
        bl_region_type = "UI"
        bl_category = "Test"

    class SOLLUMZ_TEST_PT_root(_ViewPanel, Panel):
        bl_idname = "SOLLUMZ_TEST_PT_root"
        bl_label = "Root"
        poll_calls = 0
        poll_result = True

        @classmethod
        def poll(cls, context):
            cls.poll_calls += 1
            return cls.poll_result

    class SOLLUMZ_TEST_PT_child(_ViewPanel, Panel):
        # no bl_idname on purpose, the class name is the identifier then
        bl_label = "Child"
        bl_parent_id = SOLLUMZ_TEST_PT_root.bl_idname

    class SOLLUMZ_TEST_PT_props(_ViewPanel, Panel):
        bl_idname = "SOLLUMZ_TEST_PT_props"
        bl_label = "Props"
        bl_space_type = "PROPERTIES"
        bl_region_type = "WINDOW"
        bl_category = None
        bl_context = "object"

    class SOLLUMZ_TEST_PT_builtin_child(Panel):
        bl_idname = "SOLLUMZ_TEST_PT_builtin_child"
        bl_label = "Builtin Child"
        bl_space_type = "PROPERTIES"
        bl_region_type = "WINDOW"
        bl_parent_id = "OBJECT_PT_transform"  # builtin Properties > Object > Transform panel

    # Panels the user cannot show/hide, none of these may end up in the tree
    class SOLLUMZ_TEST_PT_no_toggle(ui.NoVisibilityToggle, _ViewPanel, Panel):
        bl_idname = "SOLLUMZ_TEST_PT_no_toggle"
        bl_label = "No Toggle"

    class SOLLUMZ_TEST_PT_no_toggle_child(_ViewPanel, Panel):
        bl_idname = "SOLLUMZ_TEST_PT_no_toggle_child"
        bl_label = "No Toggle Child"
        bl_parent_id = SOLLUMZ_TEST_PT_no_toggle.bl_idname

    class SOLLUMZ_TEST_PT_file_browser(Panel):
        bl_idname = "SOLLUMZ_TEST_PT_file_browser"
        bl_label = "File Browser"
        bl_space_type = "FILE_BROWSER"
        bl_region_type = "TOOL_PROPS"

    class SOLLUMZ_TEST_PT_popover(_ViewPanel, Panel):
        bl_idname = "SOLLUMZ_TEST_PT_popover"
        bl_label = "Popover"
        bl_region_type = "HEADER"

    class SOLLUMZ_TEST_PT_tab(TabPanel, _ViewPanel, Panel):
        bl_idname = "SOLLUMZ_TEST_PT_tab"
        bl_label = "Tab"

    return SimpleNamespace(
        root=SOLLUMZ_TEST_PT_root,
        child=SOLLUMZ_TEST_PT_child,
        props=SOLLUMZ_TEST_PT_props,
        builtin_child=SOLLUMZ_TEST_PT_builtin_child,
        excluded=[
            SOLLUMZ_TEST_PT_no_toggle, SOLLUMZ_TEST_PT_no_toggle_child,
            SOLLUMZ_TEST_PT_file_browser, SOLLUMZ_TEST_PT_popover, SOLLUMZ_TEST_PT_tab,
        ],
    )


def test_panel_tree():
    p = _make_panels()
    classes = [p.root, p.child, p.props, p.builtin_child, *p.excluded, int]  # non-panel classes are ignored

    panels = ui.PanelVisibility()
    panels.hook_panels(classes)

    # groups come out sorted by display label; panels with no toggle, in the file browser, in a
    # header (popovers) or inside a tab are excluded along with their whole subtree
    assert [group.label for group in panels._tree] == ["3D Viewport › Test", "Properties › Object"]
    assert all("poll" not in cls.__dict__ for cls in p.excluded)  # excluded panels aren't hooked either
    view_group, props_group = panels._tree

    assert (view_group.space_type, view_group.region_type, view_group.category) == ("VIEW_3D", "UI", "Test")
    assert [node.idname for node in view_group.roots] == ["SOLLUMZ_TEST_PT_root"]
    child_node = view_group.roots[0].children[0]
    # falls back to the class name when bl_idname is not set
    assert (child_node.idname, child_node.label) == ("SOLLUMZ_TEST_PT_child", "Child")

    # "object" comes from the builtin parent panel, SOLLUMZ_TEST_PT_builtin_child has no bl_context
    assert (props_group.space_type, props_group.region_type, props_group.category) == ("PROPERTIES", "WINDOW", "object")
    assert [node.idname for node in props_group.roots] == ["SOLLUMZ_TEST_PT_props", "SOLLUMZ_TEST_PT_builtin_child"]

    panels.unhook_panels()
    assert panels._tree == ()


def test_panel_poll_hooking():
    p = _make_panels()
    classes = [p.root, p.child]
    original_poll = p.root.__dict__["poll"]

    panels = ui.PanelVisibility()
    panels.hook_panels(classes)
    assert all("poll" in cls.__dict__ for cls in classes)

    # hooking again must not stack wrappers
    wrapped_poll = p.root.__dict__["poll"]
    panels.hook_panels(classes)
    assert p.root.__dict__["poll"] is wrapped_poll

    # a visible panel delegates to its original poll, a panel without one polls True
    assert p.root.poll(None) is True
    assert p.child.poll(None) is True
    p.root.poll_result = False
    assert p.root.poll(None) is False
    p.root.poll_result = True
    assert p.root.poll_calls == 2

    assert not panels.has_hidden
    _hide(panels, "SOLLUMZ_TEST_PT_root", "SOLLUMZ_TEST_PT_child")
    assert panels.has_hidden and panels.is_hidden("SOLLUMZ_TEST_PT_root")
    assert p.root.poll(None) is False
    assert p.child.poll(None) is False
    assert p.root.poll_calls == 2  # the original poll is not reached while hidden

    _hide(panels)
    assert not panels.has_hidden
    assert p.root.poll(None) is True

    panels.unhook_panels()
    assert p.root.__dict__["poll"] is original_poll  # restored
    assert "poll" not in p.child.__dict__  # had no poll of its own, ours is removed
