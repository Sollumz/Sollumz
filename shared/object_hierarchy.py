import bpy
from bpy.types import Object


class ObjectHierarchySnapshot:
    __slots__ = ("_parent_child_map",)

    def __init__(self):
        parent_child_map = {}
        for child in bpy.data.objects:
            if (parent := child.parent) is not None:
                parent_child_map.setdefault(parent, []).append(child)

        self._parent_child_map = parent_child_map

    def get_children_recursive(self, obj: Object) -> list[Object]:
        parent_child_map = self._parent_child_map
        children_recursive = []

        def _recurse(parent):
            for child in parent_child_map.get(parent, ()):
                children_recursive.append(child)
                _recurse(child)

        _recurse(obj)
        return children_recursive
