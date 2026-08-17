import bpy
from bpy.types import (
    Operator,
    UILayout,
)
from bpy.props import StringProperty
from dataclasses import dataclass, replace
from typing import Iterator

from .sollumz_preferences import get_addon_preferences
from .sollumz_ui import space_type_ui_name, context_mode_ui_name
from .tools.blenderhelper import tag_redraw_all_areas
from .ytyp.tools import ArchetypeExtensionTool
from .ydr.gizmos.light_manipulators.culling_plane import LightCullingPlaneTool
from .ymap_next.overlays.lod_hierarchy_tool import MapLodHierarchyTool
from .editor_tools.vertex_paint.gradient import VertexPaintGradientTool


@dataclass(frozen=True, slots=True)
class SollumzToolDef:
    cls: type
    separator: bool = False
    group: bool = False
    after: str | None = None


tools = (
    # Object Mode Tools
    SollumzToolDef(ArchetypeExtensionTool, separator=True, group=True),
    SollumzToolDef(LightCullingPlaneTool, after=ArchetypeExtensionTool.bl_idname),
    SollumzToolDef(MapLodHierarchyTool, after=LightCullingPlaneTool.bl_idname),
    # Vertex Paint Tools
    SollumzToolDef(VertexPaintGradientTool, separator=True),
)


class ToolVisibility:
    """Show/hide state of the workspace tools.

    Workspace tools have no `poll`, so hiding a tool means not registering it at all and
    toggling one re-registers the whole set.
    """

    def __init__(self, tool_defs: tuple[SollumzToolDef, ...]):
        self._defs = tuple(tool_defs)
        self._hidden_ids: set[str] = set()
        self._registered: list[type] = []
        self._is_registered = False

    def is_hidden(self, tool_id: str) -> bool:
        return tool_id in self._hidden_ids

    @property
    def has_hidden(self) -> bool:
        return bool(self._hidden_ids)

    def sync(self, hidden_tools):
        """Sync the runtime state with the `hidden_tools` preferences collection."""
        hidden_ids = {entry.name for entry in hidden_tools}
        if hidden_ids == self._hidden_ids:
            return

        self._hidden_ids = hidden_ids
        if self._is_registered:
            self.refresh()

    def set_hidden(self, context, tool_id: str, hidden: bool):
        prefs = get_addon_preferences(context)
        prefs.set_tool_hidden(tool_id, hidden)
        self.sync(prefs.hidden_tools)

    def show_all(self, context):
        prefs = get_addon_preferences(context)
        prefs.clear_hidden_tools()
        self.sync(prefs.hidden_tools)

    def _iter_tools_to_register(self) -> Iterator[SollumzToolDef]:
        """The definitions of the tools to register, with the hidden tools removed.

        A hidden tool leaves a hole in the `after` chain: the tools that came after it now chain
        from where it chained from and take over the separator/group it would have introduced.
        Otherwise Blender wouldn't find the tool referenced by `after` and would append the
        remaining tools at the end of the toolbar instead of keeping them in place.
        """
        holes: dict[str, SollumzToolDef] = {}  # hidden tool identifier -> the place it left behind
        for tool in self._defs:
            after, separator, group = tool.after, tool.separator, tool.group
            while (hole := holes.get(after)) is not None:
                after, separator, group = hole.after, separator or hole.separator, group or hole.group

            tool = replace(tool, after=after, separator=separator, group=group)
            if self.is_hidden(tool.cls.bl_idname):
                holes[tool.cls.bl_idname] = tool
            else:
                yield tool

    def register(self):
        for tool in self._iter_tools_to_register():
            bpy.utils.register_tool(tool.cls, separator=tool.separator, group=tool.group, after=tool.after)
            self._registered.append(tool.cls)
        self._is_registered = True

    def unregister(self):
        for cls in reversed(self._registered):
            bpy.utils.unregister_tool(cls)
        self._registered.clear()
        self._is_registered = False

    def refresh(self):
        """Re-register the tools so the toolbars match the current visibility state."""
        self.unregister()
        self.register()

    def draw_prefs_section(self, layout: UILayout):
        """Draw the tool list with a show/hide toggle on each tool."""
        row = layout.row()
        row.label(text="Tools")
        subrow = row.row()
        subrow.alignment = "RIGHT"
        subrow.operator(SOLLUMZ_OT_prefs_show_all_tools.bl_idname, text="   Show All   ", icon="HIDE_OFF")

        box = layout.box()

        groups = {}
        for tool in self._defs:
            key = (tool.cls.bl_space_type, tool.cls.bl_context_mode)
            groups.setdefault(key, []).append(tool)

        for ((space_type, context_mode), tools) in groups.items():
            if bpy.app.version >= (4, 1, 0):
                group_idname = f"sollumz_prefs_ui_tools_group_{space_type}_{context_mode}"
                group_header, group_body = box.panel(group_idname, default_closed=True)
            else:
                group_header, group_body = box, box
            group_header.label(text=f"{space_type_ui_name(space_type)} › {context_mode_ui_name(context_mode)}")
            if group_body:
                for tool in tools:
                    self._draw_tool(group_body, tool)

    def _draw_tool(self, layout: UILayout, tool: SollumzToolDef):
        row = layout.row(align=True)
        row.alignment = "LEFT"
        row.label(text="", icon="BLANK1")

        tool_id = tool.cls.bl_idname
        row.operator(
            SOLLUMZ_OT_prefs_toggle_tool_visibility.bl_idname,
            text=tool.cls.bl_label,
            icon="CHECKBOX_DEHLT" if self.is_hidden(tool_id) else "CHECKBOX_HLT",
            emboss=False,
        ).tool_id = tool_id


_tool_visibility = ToolVisibility(tools)


def tool_visibility() -> ToolVisibility:
    return _tool_visibility


class SOLLUMZ_OT_prefs_toggle_tool_visibility(Operator):
    """Show or hide this tool"""
    bl_idname = "sollumz.prefs_toggle_tool_visibility"
    bl_label = "Toggle Tool Visibility"
    bl_options = {"INTERNAL"}

    tool_id: StringProperty(options={"HIDDEN", "SKIP_SAVE"})

    def execute(self, context):
        visibility = tool_visibility()
        visibility.set_hidden(context, self.tool_id, not visibility.is_hidden(self.tool_id))
        tag_redraw_all_areas(context)
        return {"FINISHED"}


class SOLLUMZ_OT_prefs_show_all_tools(Operator):
    """Show all tools hidden in the tool list"""
    bl_idname = "sollumz.prefs_show_all_tools"
    bl_label = "Show All"
    bl_options = {"INTERNAL"}

    @classmethod
    def poll(cls, context):
        return tool_visibility().has_hidden

    def execute(self, context):
        tool_visibility().show_all(context)
        tag_redraw_all_areas(context)
        return {"FINISHED"}


def register():
    tool_visibility().register()


def unregister():
    tool_visibility().unregister()
