import bpy
from typing import NamedTuple, Optional
from .ytyp.tools import ArchetypeExtensionTool
from .ydr.gizmos.light_manipulators.culling_plane import LightCullingPlaneTool
from .ymap_next.overlays.lod_hierarchy_tool import MapLodHierarchyTool
from .editor_tools.vertex_paint.gradient import VertexPaintGradientTool


class SollumzToolDef(NamedTuple):
    cls: type
    separator: bool = False
    group: bool = False
    after: Optional[str] = None


tools = (
    # Object Mode Tools
    SollumzToolDef(ArchetypeExtensionTool, separator=True, group=True),
    SollumzToolDef(LightCullingPlaneTool, after=ArchetypeExtensionTool.bl_idname),
    SollumzToolDef(MapLodHierarchyTool, after=LightCullingPlaneTool.bl_idname),
    # Vertex Paint Tools
    SollumzToolDef(VertexPaintGradientTool, separator=True),
)


def register_tools():
    for tool in tools:
        bpy.utils.register_tool(tool.cls, separator=tool.separator, group=tool.group, after=tool.after)


def unregister_tools():
    for tool in tools:
        bpy.utils.unregister_tool(tool.cls)
