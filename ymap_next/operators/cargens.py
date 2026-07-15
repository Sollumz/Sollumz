from collections import Counter

import bpy
from bpy.types import Operator

from ...sollumz_properties import SollumType
from ...tools.blenderhelper import create_blender_object, get_all_collections
from ..context import (
    active_cargen,
    active_cargens_collection,
)
from ..map_index import CACHE_NOT_READY, MAP_INDEX, find_cargen_by_collection
from ..properties.map import MAP_CARGEN_FLAG_PROPS, MapCarGen


def _find_cargen_from_object(obj):
    """Walk obj.users_collection, returning (collection, map_group, cargen) for the first cargen collection hit.

    Returns None if no cargen collection is found, or CACHE_NOT_READY if the map index is still building.
    """
    if obj is None:
        return None
    saw_not_ready = False
    for coll in obj.users_collection:
        result = find_cargen_by_collection(coll)
        if result is CACHE_NOT_READY:
            saw_not_ready = True
            continue
        if result is not None:
            map_group, cargen = result
            return coll, map_group, cargen
    return CACHE_NOT_READY if saw_not_ready else None


class SOLLUMZ_OT_map_cargen_create_object(Operator):
    bl_idname = "sollumz.map_cargen_create_object"
    bl_label = "Create Car Generator Object"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_cargen(context) is not None

    def execute(self, context):
        cargen = active_cargen(context)
        coll = cargen.linked_collection
        if coll is None:
            # TODO(ymap): create collection if doesn't exist
            # TODO(ymap): Need some consistent way to lookup collections related to the active map group so we can create new ones and link them to the existing ones
            # coll = bpy.data.collections.new(f"{map_data.name}.cargen.{g.ui_label}")
            # cargen.linked_collection = coll
            self.report({"WARNING"}, "No linked collection in active car generator")
            return {"CANCELLED"}

        cargen_ref_mesh = MapCarGen.get_cargen_mesh()

        if dim_counts := Counter(tuple(obj.dimensions[:2]) for obj in coll.objects):
            (width, length), _ = dim_counts.most_common(1)[0]
        else:
            # defaults, car sized
            width, length = 2.5, 5.5

        cursor = context.scene.cursor

        obj = create_blender_object(SollumType.NONE, "CarGen", cargen_ref_mesh, link_to_context_collection=False)
        obj.location = cursor.location
        obj.rotation_euler = cursor.matrix.to_3x3().to_euler()
        obj.rotation_euler.x = 0.0
        obj.rotation_euler.y = 0.0
        obj.scale = width, length, 1.0
        coll.objects.link(obj)

        bpy.ops.object.select_all(action="DESELECT")
        obj.select_set(True)
        return {"FINISHED"}


class SOLLUMZ_OT_map_cargen_select_all_objects(Operator):
    bl_idname = "sollumz.map_cargen_select_all_objects"
    bl_label = "Select All Car Generator Objects"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_cargen(context) is not None

    def execute(self, context):
        cargens = active_cargens_collection(context)
        bpy.ops.object.select_all(action="DESELECT")
        first = True
        for cargen in cargens.iter_selected_items():
            coll = cargen.linked_collection
            if coll is None:
                self.report({"WARNING"}, f"No linked collection in '{cargen.ui_label}' car generator")
                continue

            for obj in coll.objects:
                if first:
                    context.view_layer.objects.active = obj
                    first = False
                obj.select_set(True)
        return {"FINISHED"}


class SOLLUMZ_OT_map_cargen_move_to_new_collection(Operator):
    bl_idname = "sollumz.map_cargen_move_to_new_collection"
    bl_label = "Move to New Collection"
    bl_description = (
        "Split the selected cargen objects off into a new car generator entry with its own collection. "
        "The new entry copies all settings from the source car generator"
    )
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        active = context.active_object
        if active is None or active not in context.selected_objects:
            return False
        result = _find_cargen_from_object(active)
        return result is not None and result is not CACHE_NOT_READY

    def execute(self, context):
        result = _find_cargen_from_object(context.active_object)
        if result is CACHE_NOT_READY:
            self.report({"INFO"}, "Map index is still building, try again in a moment")
            return {"CANCELLED"}
        if result is None:
            self.report({"WARNING"}, "Active object is not in a car generator collection")
            return {"CANCELLED"}

        src_collection, map_group, source_cargen = result

        objs_to_move = [obj for obj in context.selected_objects if src_collection in obj.users_collection]
        if not objs_to_move:
            self.report({"WARNING"}, "No selected objects are in the active car generator's collection")
            return {"CANCELLED"}

        # Snapshot source settings, group.new_cargen() calls cargens.add() which invalidates source_cargen.
        src_name = source_cargen.name
        src_model = source_cargen.model
        src_model_set = source_cargen.model_set
        src_body_color_remap = tuple(source_cargen.body_color_remap)
        src_livery = source_cargen.livery
        src_creation_rule = source_cargen.creation_rule
        src_map_data_uuid = source_cargen.map_data_uuid
        src_map_data_name = source_cargen.map_data_name
        src_flags = {prop_name: getattr(source_cargen, prop_name) for prop_name, _ in MAP_CARGEN_FLAG_PROPS}

        parent_coll = next(
            (c for c in get_all_collections() if src_collection.name in c.children),
            context.scene.collection,
        )

        new_cargen = map_group.new_cargen()
        new_cargen.map_data_uuid = src_map_data_uuid
        new_cargen.name = src_name
        new_cargen.model = src_model
        new_cargen.model_set = src_model_set
        new_cargen.body_color_remap = src_body_color_remap
        new_cargen.livery = src_livery
        new_cargen.creation_rule = src_creation_rule
        for prop_name, _ in MAP_CARGEN_FLAG_PROPS:
            setattr(new_cargen, prop_name, src_flags[prop_name])

        base_name = src_map_data_name or map_group.name
        new_coll = bpy.data.collections.new(f"{base_name}.cargen.{new_cargen.ui_label}")
        parent_coll.children.link(new_coll)
        new_cargen.linked_collection = new_coll

        for obj in objs_to_move:
            src_collection.objects.unlink(obj)
            new_coll.objects.link(obj)

        MAP_INDEX.invalidate_and_rebuild()

        self.report({"INFO"}, f"Moved {len(objs_to_move)} object(s) to new car generator '{new_cargen.ui_label}'")
        return {"FINISHED"}
