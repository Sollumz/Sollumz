from bpy.props import EnumProperty
from bpy.types import Operator

from ...sollumz_preferences import get_addon_preferences
from ..context import active_group
from ..instancing import instance_map_entities, uninstance_map_entities
from ..map_index import MAP_INDEX
from ..properties.map import MapLodLevelEnumFlagItems


class SOLLUMZ_OT_map_instance_entities(Operator):
    bl_idname = "sollumz.map_instance_entities"
    bl_label = "Instance Entities"
    bl_description = (
        "Create editable Blender objects for the entities of the active map group, linked from the shared asset "
        "library. Entities already linked to an object are skipped"
    )
    bl_options = {"REGISTER", "UNDO"}

    lod_levels: EnumProperty(
        name="LOD Levels",
        description="Only instance entities of the selected LOD levels",
        items=MapLodLevelEnumFlagItems,
        options={"ENUM_FLAG"},
        default={item[0] for item in MapLodLevelEnumFlagItems},  # all levels
    )

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        return group is not None and group.entities

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        layout = self.layout
        layout.label(text="LOD Levels")
        layout.props_enum(self, "lod_levels")

    def execute(self, context):
        if not get_addon_preferences(context).shared_assets_directories:
            self.report(
                {"WARNING"},
                "No shared asset directories configured. Set them up and build the asset library first",
            )
            return {"CANCELLED"}

        selected = set(self.lod_levels)
        if not selected:
            self.report({"WARNING"}, "No LOD levels selected")
            return {"CANCELLED"}

        group = active_group(context)
        num_linked, num_missing, num_skipped = instance_map_entities(
            group, entity_filter=lambda e: e.lod_level in selected
        )
        MAP_INDEX.invalidate_and_rebuild()

        parts = [f"Instanced {num_linked} object(s)"]
        if num_missing:
            parts.append(f"{num_missing} archetype(s) not found in asset library")
        if num_skipped:
            parts.append(f"{num_skipped} already instanced")
        self.report({"INFO"} if num_linked else {"WARNING"}, ", ".join(parts))
        return {"FINISHED"}


class SOLLUMZ_OT_map_remove_entity_instances(Operator):
    bl_idname = "sollumz.map_remove_entity_instances"
    bl_label = "Remove Instances"
    bl_description = (
        "Remove the linked Blender objects of the active map group's entities, saving each object's current "
        "transform back into the entity data"
    )
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        return group is not None and group.entities

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        group = active_group(context)
        num_instanced = sum(1 for e in group.entities if e.linked_object is not None)
        self.layout.label(text=f"Remove {num_instanced} entity instance(s)?")

    def execute(self, context):
        group = active_group(context)
        num_removed = uninstance_map_entities(group)
        MAP_INDEX.invalidate_and_rebuild()

        if num_removed == 0:
            self.report({"INFO"}, "No instanced entities to remove")
            return {"CANCELLED"}

        self.report({"INFO"}, f"Removed {num_removed} entity instance(s)")
        return {"FINISHED"}
