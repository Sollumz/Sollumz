from collections.abc import Iterable

import bpy
from bpy.types import Object, Scene


class ObjectHierarchySnapshot:
    """Snapshot of the object parenting hierarchy.

    `Object.children` and `Object.children_recursive` rebuild the whole parent-child map on each access, so prefer
    this class when looking up the children of multiple objects.

    Snapshots of a scene, as created by `for_scene`, only include the objects in that scene. Objects that the user
    removed from the scene but are still in the .blend file, because some other data-block still referenced them,
    are excluded.
    """

    __slots__ = ("_parent_child_map",)

    def __init__(self, objects: Iterable[Object]):
        parent_child_map = {}
        for child in objects:
            if (parent := child.parent) is not None:
                parent_child_map.setdefault(parent, []).append(child)

        self._parent_child_map = parent_child_map

    @classmethod
    def for_blend(cls) -> "ObjectHierarchySnapshot":
        """Creates a snapshot with every object in the .blend file."""
        return cls(bpy.data.objects)

    @classmethod
    def for_scene(cls, scene: Scene | None = None) -> "ObjectHierarchySnapshot":
        """Creates a snapshot with the objects in `scene`, or in the current scene if `None`."""
        if scene is None:
            scene = bpy.context.scene

        return cls(scene.objects)

    @classmethod
    def for_object(cls, obj: Object) -> "ObjectHierarchySnapshot":
        """Creates a snapshot suited for traversing the hierarchy of `obj`.

        Uses the current scene when `obj` is in it. Otherwise, `obj` is elsewhere (another scene, or nowhere, like
        objects appended from the asset browser), so every object in the .blend file is used.
        """
        scene = bpy.context.scene
        if scene.objects.get(obj.name) == obj:
            return cls.for_scene(scene)

        return cls.for_blend()

    def get_children(self, obj: Object) -> tuple[Object, ...]:
        """Gets the direct children of `obj`. Equivalent to `Object.children`."""
        return tuple(self._parent_child_map.get(obj, ()))

    def get_children_recursive(self, obj: Object) -> list[Object]:
        """Gets all the descendants of `obj`. Equivalent to `Object.children_recursive`."""
        parent_child_map = self._parent_child_map
        children_recursive = []

        def _recurse(parent):
            for child in parent_child_map.get(parent, ()):
                children_recursive.append(child)
                _recurse(child)

        _recurse(obj)
        return children_recursive

    def get_object_with_children_recursive(self, obj: Object) -> list[Object]:
        """Gets `obj` along with all its descendants, `obj` first."""
        return [obj, *self.get_children_recursive(obj)]
