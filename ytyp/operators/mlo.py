from bpy.types import Operator, Object
import bpy
from ...sollumz_properties import SollumType
from ..utils import get_selected_archetype
from ..properties.ytyp import ArchetypeType


class ObjectHierarchySnapshot:
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


class SOLLUMZ_OT_mlo_create_instance(Operator):
    bl_idname = "sollumz.mlo_create_instance"
    bl_label = "Create MLO Instance"
    bl_description = "Create an instance of this MLO that can be placed in maps"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype is not None and selected_archetype.type == ArchetypeType.MLO

    def execute(self, context):
        archetype = get_selected_archetype(context)

        collection = archetype.mlo_collection_for_instancing
        if not collection:
            collection = bpy.data.collections.new(f"{archetype.name}.for_instancing")
            archetype.mlo_collection_for_instancing = collection

            h = ObjectHierarchySnapshot()
            objs = []
            seen = set()
            for entity in archetype.entities:
                obj = entity.linked_object
                if obj is None:
                    continue

                for o in (obj, *h.get_children_recursive(obj)):
                    if o.name in seen or o.sollum_type != SollumType.DRAWABLE_MODEL:
                        continue
                    seen.add(o.name)
                    objs.append(o)

            link = collection.objects.link
            for obj in objs:
                link(obj)

            if archetype.asset is not None:
                collection.instance_offset = archetype.asset.matrix_world.translation

        instance_obj = bpy.data.objects.new(archetype.name, None)
        instance_obj.instance_type = "COLLECTION"
        instance_obj.instance_collection = collection
        if archetype.asset is not None:
            # Keep the instanced entities at their current world position, with the instance pivot at the MLO origin
            instance_obj.location = archetype.asset.matrix_world.translation
        context.collection.objects.link(instance_obj)

        for obj in context.selected_objects:
            obj.select_set(False)
        instance_obj.select_set(True)
        context.view_layer.objects.active = instance_obj

        self.report({"INFO"}, f"Created MLO instance '{archetype.name}'")
        return {"FINISHED"}


class SOLLUMZ_OT_mlo_refresh_instances(Operator):
    bl_idname = "sollumz.mlo_refresh_instances"
    bl_label = "Refresh MLO Instances"
    bl_description = (
        "Refresh instances of this MLO. Use when added or removed entities are not reflected in existing instances"
    )
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return (
            selected_archetype is not None
            and selected_archetype.type == ArchetypeType.MLO
            and selected_archetype.mlo_collection_for_instancing is not None
        )

    def execute(self, context):
        archetype = get_selected_archetype(context)

        collection = archetype.mlo_collection_for_instancing
        if not collection:
            return {"CANCELLED"}

        h = ObjectHierarchySnapshot()
        objs = []
        seen = set()
        for entity in archetype.entities:
            obj = entity.linked_object
            if obj is None:
                continue

            for o in (obj, *h.get_children_recursive(obj)):
                n = o.name
                if n in seen or o.sollum_type != SollumType.DRAWABLE_MODEL:
                    continue
                seen.add(n)
                objs.append(o)

        coll_objs = collection.objects
        unlink = coll_objs.unlink
        for ob in list(coll_objs):
            unlink(ob)

        link = coll_objs.link
        for obj in objs:
            link(obj)

        if archetype.asset is not None:
            collection.instance_offset = archetype.asset.matrix_world.translation

        self.report({"INFO"}, f"Refreshed MLO instances of '{archetype.name}'")
        return {"FINISHED"}
