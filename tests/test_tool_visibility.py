import bpy
import pytest
from bl_ui.space_toolsystem_common import ToolDef, ToolSelectPanelHelper
from types import SimpleNamespace

from ..sollumz_tool import SollumzToolDef, ToolVisibility


def _toolbar(context_mode: str) -> list:
    """Blender's internal tool list for the `context_mode` 3D viewport toolbar."""
    return ToolSelectPanelHelper._tool_class_from_space_type("VIEW_3D")._tools[context_mode]


def _tool_cls(name: str, context_mode: str = "OBJECT") -> type:
    return type(f"SollumzTestTool{name}", (bpy.types.WorkSpaceTool,), {
        "bl_idname": f"sollumz_test.{name.lower()}",
        "bl_label": name,
        "bl_space_type": "VIEW_3D",
        "bl_context_mode": context_mode,
    })


@pytest.fixture()
def tools():
    """A group of three object mode tools and a vertex paint mode tool.

    - `tools.visibility` is the `ToolVisibility` instance.
    - `tools.hide(...)` hides tools the same way loading the preferences would.
    - `tools.layout(mode)` returns what tools appear in the toolbar, with `None` for a
      separator and a tuple for a group of tools, the way Blender lays them out.
    """
    a, b, c = (_tool_cls(name) for name in "ABC")
    d = _tool_cls("D", context_mode="PAINT_VERTEX")
    visibility = ToolVisibility((
        SollumzToolDef(a, separator=True, group=True),
        SollumzToolDef(b, after=a.bl_idname),
        SollumzToolDef(c, after=b.bl_idname),
        SollumzToolDef(d, separator=True),
    ))
    # no test tool chains from a builtin or Sollumz tool, so they all land at the end of the toolbars
    prefixes = {mode: list(_toolbar(mode)) for mode in ("OBJECT", "PAINT_VERTEX")}

    def _labels(item):
        if item is None:
            return None
        # ToolDef is a NamedTuple itself, check it before the plain tuple that makes up a group
        return item.label if isinstance(item, ToolDef) else tuple(tool.label for tool in item)

    def _layout(context_mode: str) -> list:
        toolbar, prefix = _toolbar(context_mode), prefixes[context_mode]
        assert toolbar[:len(prefix)] == prefix, "the test tools disturbed the already registered tools"
        return [_labels(item) for item in toolbar[len(prefix):]]

    def _hide(*tool_ids):
        visibility.sync([SimpleNamespace(name=i) for i in tool_ids])

    try:
        yield SimpleNamespace(
            visibility=visibility,
            layout=_layout,
            hide=_hide,
        )
    finally:
        visibility.unregister()


def test_hidden_tools_keep_their_place_in_the_toolbar(tools):
    # preferences are loaded before the tools are registered, syncing must not register them early
    tools.hide("sollumz_test.b")
    assert tools.visibility.has_hidden and tools.visibility.is_hidden("sollumz_test.b")
    assert tools.layout("OBJECT") == []

    tools.visibility.register()
    assert tools.layout("OBJECT") == [None, ("A", "C")]
    assert tools.layout("PAINT_VERTEX") == [None, "D"]

    # showing everything again puts the hidden tool back in its place
    tools.hide()
    assert not tools.visibility.has_hidden
    assert tools.layout("OBJECT") == [None, ("A", "B", "C")]

    # hiding the group leader hands its separator and group over to the tool taking its place
    tools.hide("sollumz_test.a", "sollumz_test.b")
    assert tools.layout("OBJECT") == [None, ("C",)]

    # nothing takes the place of a hidden tool with no tools after it
    tools.hide("sollumz_test.c", "sollumz_test.d")
    assert tools.layout("OBJECT") == [None, ("A", "B")]
    assert tools.layout("PAINT_VERTEX") == []

    # hiding every tool leaves nothing registered, showing them again must bring them back
    tools.hide("sollumz_test.a", "sollumz_test.b", "sollumz_test.c", "sollumz_test.d")
    assert tools.layout("OBJECT") == []
    assert tools.layout("PAINT_VERTEX") == []

    tools.hide()
    assert tools.layout("OBJECT") == [None, ("A", "B", "C")]
    assert tools.layout("PAINT_VERTEX") == [None, "D"]

    # unregistering only touches the tools that are registered, unregistering a hidden one would
    # raise, and doing it again is a no-op
    tools.visibility.unregister()
    tools.visibility.unregister()
    assert tools.layout("OBJECT") == []
    assert tools.layout("PAINT_VERTEX") == []

