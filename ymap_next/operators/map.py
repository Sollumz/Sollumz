import bpy
from bpy.props import (
    StringProperty,
    FloatVectorProperty,
)
from bpy.types import (
    Operator,
)
from mathutils import Vector

from ...shared.multiselection import SelectMode
from ...tools.blenderhelper import remove_number_suffix, tag_redraw
from ..context import (
    active_entity,
    active_entity_extension,
    active_grass_batch,
    active_group,
    active_map,
)
from ..map_index import (
    MAP_INDEX,
    CacheObjectData,
)
from ..properties.map import MapPartitionMode, get_maps


class SOLLUMZ_OT_maps_new_group(Operator):
    bl_idname = "sollumz.maps_new_group"
    bl_label = "Create Map Group"
    bl_description = "Create a map group"
    bl_options = {"REGISTER", "UNDO"}

    name: StringProperty(name="Name")

    def execute(self, context):
        name = self.name or "map"
        maps = get_maps(context, create_if_missing=True)
        g = maps.new_group()
        g.name = name
        m = g.new_map()
        m.name = name
        g.refresh_ui()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)


class SOLLUMZ_OT_maps_delete_group(Operator):
    bl_idname = "sollumz.maps_delete_group"
    bl_label = "Delete Map Group"
    bl_description = "Delete selected map group(s)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        maps = get_maps(context)
        return maps and maps.groups

    def execute(self, context):
        get_maps(context).groups.remove_selected()
        MAP_INDEX.invalidate_and_rebuild()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        groups = list(get_maps(context).groups.iter_selected_items())
        layout = self.layout
        layout.label(text=f"Delete {len(groups)} map group(s)?")
        counts = (
            (sum(len(g.maps) for g in groups), "container(s)"),
            (sum(len(g.entities) for g in groups), "entity(s)"),
            (sum(len(g.cargens) for g in groups), "car generator(s)"),
            (sum(len(g.timecycle_modifiers) for g in groups), "timecycle modifier(s)"),
            (sum(len(g.grass_batches) for g in groups), "grass batch(es)"),
            (sum(len(g.occluders) for g in groups), "occluder(s)"),
            (sum(len(g.lod_lights) for g in groups), "LOD lights"),
        )
        for n, label in counts:
            if n > 0:
                layout.label(text=f"    {n} {label}")


class SOLLUMZ_OT_map_group_new_map_data(Operator):
    bl_idname = "sollumz.map_group_new_map_data"
    bl_label = "Create Map Data"
    bl_description = "Create a map data container in the active map group"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None

    def execute(self, context):
        group = active_group(context)

        existing_names = {m.name for m in group.maps}
        name_base = group.name
        n = 1
        while (name := f"{name_base}_{n:02d}") in existing_names:
            n += 1

        md = group.new_map()
        md.name = name

        group.refresh_ui()

        group.maps.select(len(group.maps) - 1)

        return {"FINISHED"}


class SOLLUMZ_OT_map_group_delete_map_data(Operator):
    bl_idname = "sollumz.map_group_delete_map_data"
    bl_label = "Delete Map Data"
    bl_description = "Delete the selected map data container"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        if active_map(context) is None:
            return False
        group = active_group(context)
        if group is not None and group.incomplete_lod_hierarchy_lock:
            cls.poll_message_set("LOD hierarchy is incomplete. Cannot delete containers!")
            return False
        return True

    def execute(self, context):
        group = active_group(context)

        md_uuids = {md.uuid for md in group.maps.iter_selected_items()}

        # Clear map_data_uuid on items that reference this map data
        for entity in group.entities:
            if entity.map_data_uuid in md_uuids:
                entity.map_data_uuid = b""
        for cargen in group.cargens:
            if cargen.map_data_uuid in md_uuids:
                cargen.map_data_uuid = b""
        for tcm in group.timecycle_modifiers:
            if tcm.map_data_uuid in md_uuids:
                tcm.map_data_uuid = b""
        for batch in group.grass_batches:
            if batch.map_data_uuid in md_uuids:
                batch.map_data_uuid = b""

        # Clear parent_uuid on children
        for m in group.maps:
            if m.parent_uuid in md_uuids:
                m.parent_uuid = b""

        group.maps.remove_selected()
        group.refresh_ui()
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_confirm(self, event)


class SOLLUMZ_OT_map_group_new_entity(Operator):
    bl_idname = "sollumz.map_group_new_entity"
    bl_label = "Create Map Entity"
    bl_description = "Create a map entity in the active map group"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None

    def execute(self, context):
        group = active_group(context)
        group.new_entity()
        group.entities.select(len(group.entities) - 1)
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_delete_entity(Operator):
    bl_idname = "sollumz.map_group_delete_entity"
    bl_label = "Delete Map Entity"
    bl_description = "Delete selected map entity(s)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        if group is None or not group.entities:
            return False

        if group.incomplete_lod_hierarchy_lock:
            cls.poll_message_set("LOD hierarchy is incomplete. Cannot delete entities!")
            return False

        return True

    def execute(self, context):
        # TODO(ymap): delete entity should delete linked objects
        active_group(context).entities.remove_selected()
        MAP_INDEX.invalidate_and_rebuild()
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_new_cargen(Operator):
    bl_idname = "sollumz.map_group_new_cargen"
    bl_label = "Create Map Car Generator"
    bl_description = "Create a car generator in the active map group"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None

    def execute(self, context):
        group = active_group(context)
        group.new_cargen()
        group.cargens.select(len(group.cargens) - 1)
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_delete_cargen(Operator):
    bl_idname = "sollumz.map_group_delete_cargen"
    bl_label = "Delete Map Car Generator"
    bl_description = "Delete selected car generator(s)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        return group is not None and group.cargens

    def execute(self, context):
        # TODO(ymap): delete cargen should delete linked collections and objects
        active_group(context).cargens.remove_selected()
        MAP_INDEX.invalidate_and_rebuild()
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_new_tcm(Operator):
    bl_idname = "sollumz.map_group_new_tcm"
    bl_label = "Create Map Timecycle Modifier"
    bl_description = "Create a timecycle modifier in the active map group"
    bl_options = {"REGISTER", "UNDO"}

    location: FloatVectorProperty(name="Location", default=(0.0, 0.0, 0.0), size=3, subtype="XYZ")
    size: FloatVectorProperty(name="Size", default=(10.0, 10.0, 5.0), size=3, subtype="XYZ")

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None

    def execute(self, context):
        group = active_group(context)
        tcm = group.new_tcm()
        tcm.location = self.location
        tcm.size = self.size
        group.timecycle_modifiers.select(len(group.timecycle_modifiers) - 1)
        return {"FINISHED"}

    def invoke(self, context, event):
        self.location = context.scene.cursor.location
        return self.execute(context)


class SOLLUMZ_OT_map_group_delete_tcm(Operator):
    bl_idname = "sollumz.map_group_delete_tcm"
    bl_label = "Delete Map Timecycle Modifier"
    bl_description = "Delete selected timecycle modifier(s)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        return group is not None and group.timecycle_modifiers

    def execute(self, context):
        active_group(context).timecycle_modifiers.remove_selected()
        MAP_INDEX.invalidate_and_rebuild()
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_new_grass_batch(Operator):
    bl_idname = "sollumz.map_group_new_grass_batch"
    bl_label = "Create Map Grass Batch"
    bl_description = "Create a grass batch in the active map group"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None

    def execute(self, context):
        group = active_group(context)
        group.new_grass_batch()
        group.grass_batches.select(len(group.grass_batches) - 1)
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_delete_grass_batch(Operator):
    bl_idname = "sollumz.map_group_delete_grass_batch"
    bl_label = "Delete Map Grass Batch"
    bl_description = "Delete selected grass batch(es)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        return group is not None and group.grass_batches

    def execute(self, context):
        # TODO(ymap): delete grass batch should delete linked objects
        active_group(context).grass_batches.remove_selected()
        MAP_INDEX.invalidate_and_rebuild()
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_new_grass_template(Operator):
    bl_idname = "sollumz.map_group_new_grass_template"
    bl_label = "Create Map Grass Template"
    bl_description = "Create a grass template in the active grass batch"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_grass_batch(context) is not None

    def execute(self, context):
        batch = active_grass_batch(context)
        batch.templates.add()
        batch.templates.select(len(batch.templates) - 1)
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_delete_grass_template(Operator):
    bl_idname = "sollumz.map_group_delete_grass_template"
    bl_label = "Delete Map Grass Template"
    bl_description = "Delete selected grass template(s)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        batch = active_grass_batch(context)
        return batch is not None and batch.templates

    def execute(self, context):
        active_grass_batch(context).templates.remove_selected()
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_new_occluder(Operator):
    bl_idname = "sollumz.map_group_new_occluder"
    bl_label = "Create Map Occluder"
    bl_description = "Create an occluder in the active map group"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None

    def execute(self, context):
        group = active_group(context)
        group.new_occluder()
        group.occluders.select(len(group.occluders) - 1)
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_delete_occluder(Operator):
    bl_idname = "sollumz.map_group_delete_occluder"
    bl_label = "Delete Map Occluder"
    bl_description = "Delete selected occluder(s)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        return group is not None and group.occluders

    def execute(self, context):
        # TODO(ymap): delete occluder should delete linked objects
        active_group(context).occluders.remove_selected()
        MAP_INDEX.invalidate_and_rebuild()
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_new_lod_lights(Operator):
    bl_idname = "sollumz.map_group_new_lod_lights"
    bl_label = "Create Map LOD Lights"
    bl_description = "Create LOD lights in the active map group"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None

    def execute(self, context):
        group = active_group(context)
        group.new_lod_lights()
        group.lod_lights.select(len(group.lod_lights) - 1)
        return {"FINISHED"}


class SOLLUMZ_OT_map_group_delete_lod_lights(Operator):
    bl_idname = "sollumz.map_group_delete_lod_lights"
    bl_label = "Delete Map LOD Lights"
    bl_description = "Delete selected LOD lights(s)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        return group is not None and group.lod_lights

    def execute(self, context):
        # TODO(ymap): delete lod lights should delete linked objects
        active_group(context).lod_lights.remove_selected()
        MAP_INDEX.invalidate_and_rebuild()
        return {"FINISHED"}


class SOLLUMZ_OT_map_generate_partitions(Operator):
    bl_idname = "sollumz.map_generate_partitions"
    bl_label = "Generate Partitions"
    bl_description = "Generate or regenerate auto-partitioned leaf map datas for the selected map"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        md = active_map(context)
        if md is None or md.partition_mode != MapPartitionMode.AUTO.name:
            return False
        group = active_group(context)
        if group is not None and group.incomplete_lod_hierarchy_lock:
            cls.poll_message_set("LOD hierarchy is incomplete. Partitioning is disabled!")
            return False
        return True

    def execute(self, context):
        from ..partitioning import generate_partitions, PartitioningSettings
        settings = PartitioningSettings()

        group = active_group(context)
        md = active_map(context)
        generate_partitions(group, md, settings)
        return {"FINISHED"}


class SOLLUMZ_OT_map_collapse_to_auto(Operator):
    bl_idname = "sollumz.map_collapse_to_auto"
    bl_label = "Collapse to Auto"
    bl_description = "Merge items from leaf children back into this map data and switch to auto-partition mode"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        md = active_map(context)
        if md is None or md.partition_mode != MapPartitionMode.NONE.name:
            return False
        group = active_group(context)
        if group is not None and group.incomplete_lod_hierarchy_lock:
            cls.poll_message_set("LOD hierarchy is incomplete. Partitioning is disabled!")
            return False
        return True

    def execute(self, context):
        from ..partitioning import collapse_to_auto

        group = active_group(context)
        md = active_map(context)
        collapse_to_auto(group, md)
        return {"FINISHED"}


class SOLLUMZ_OT_map_convert_to_manual(Operator):
    bl_idname = "sollumz.map_convert_to_manual"
    bl_label = "Convert to Manual"
    bl_description = "Switch to manual mode. Auto-generated leaves become regular map datas"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        md = active_map(context)
        if md is None or md.partition_mode != MapPartitionMode.AUTO.name:
            return False
        group = active_group(context)
        if group is not None and group.incomplete_lod_hierarchy_lock:
            cls.poll_message_set("LOD hierarchy is incomplete. Partitioning is disabled!")
            return False
        return True

    def execute(self, context):
        from ..partitioning import convert_to_manual

        group = active_group(context)
        md = active_map(context)
        convert_to_manual(group, md)
        group.refresh_ui()
        return {"FINISHED"}


class SOLLUMZ_OT_map_auto_assign_unassigned(Operator):
    bl_idname = "sollumz.map_auto_assign_unassigned"
    bl_label = "Auto-Assign Unassigned Items"
    bl_description = "Assign items without a map data to the nearest existing leaf map data by spatial proximity"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        group = active_group(context)
        if group is None or not group.maps:
            return False
        if group.incomplete_lod_hierarchy_lock:
            cls.poll_message_set("LOD hierarchy is incomplete. Partitioning is disabled!")
            return False
        return True

    def execute(self, context):
        from ..partitioning import auto_assign_unassigned

        group = active_group(context)
        auto_assign_unassigned(group)
        return {"FINISHED"}


class SOLLUMZ_OT_map_calculate_extents(Operator):
    bl_idname = "sollumz.map_calculate_extents"
    bl_label = "Calculate Extents"
    bl_description = (
        "Recalculate entities and streaming extents of the selected container(s) from their assigned items"
    )
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_map(context) is not None

    def execute(self, context):
        from ..extents import update_maps_extents

        group = active_group(context)
        map_uuids = [md.uuid for md in group.maps.iter_selected_items()]
        num_updated = update_maps_extents(group, map_uuids)
        if num_updated == 0:
            self.report({"WARNING"}, "Selected container(s) have no assigned items. Extents unchanged")
        return {"FINISHED"}


class SOLLUMZ_OT_map_add_obj_as_entity(Operator):
    bl_idname = "sollumz.map_add_obj_as_entity"
    bl_label = "Add Object(s) as Entity"
    bl_description = "Create Map Entities from selected objects (auto-sets linked object)"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None and len(context.selected_objects) > 0

    def execute(self, context):
        group = active_group(context)

        first_new_entity_index = len(group.entities)

        for obj in context.selected_objects:
            existing_entity = self._get_entity_using_obj(obj, group)

            if existing_entity is not None:
                self.report(
                    {"INFO"},
                    f"Object '{obj.name}' already linked to entity '{existing_entity.archetype_name}'! Skipping...",
                )
                continue

            entity = group.new_entity()
            entity.archetype_name = remove_number_suffix(obj.name)
            entity.linked_object = obj

        last_new_entity_index = len(group.entities) - 1
        if first_new_entity_index <= last_new_entity_index and first_new_entity_index < len(group.entities):
            group.entities.select(first_new_entity_index)
            group.entities.select(last_new_entity_index, SelectMode.EXTEND)

        return {"FINISHED"}

    def _get_entity_using_obj(self, obj, group):
        for entity in group.entities:
            if entity.linked_object == obj:
                return entity
        return None


class SOLLUMZ_OT_map_highlight_map_data_entities(Operator):
    bl_idname = "sollumz.map_highlight_map_data_entities"
    bl_label = "Highlight Entities"
    bl_description = "Temporarily highlight all entities belonging to the selected container in the viewport"

    @classmethod
    def poll(cls, context):
        return active_map(context) is not None

    def execute(self, context):
        from ..overlays.map_data_highlight import _handler

        group = active_group(context)
        md = active_map(context)
        if md is None or _handler is None:
            self.report({"WARNING"}, "No map data selected")
            return {"CANCELLED"}

        md_uuid = md.uuid
        positions = []
        for entity in group.entities:
            if entity.map_data_uuid == md_uuid:
                obj = entity.linked_object
                pos = tuple(obj.matrix_world.translation) if obj is not None else tuple(entity.position)
                positions.append(pos)

        if not positions:
            self.report({"INFO"}, "No entities found for this container")
            return {"CANCELLED"}

        _handler.start_flash(positions)
        return {"FINISHED"}


class SOLLUMZ_OT_map_go_to_entity(Operator):
    bl_idname = "sollumz.map_go_to_entity"
    bl_label = "Go To Entity"
    bl_description = "Go to the active entity"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        return active_group(context) is not None

    def execute(self, context):
        group = active_group(context)
        entity = group.entities.active_item

        if not entity:
            return {"CANCELLED"}

        if obj := entity.linked_object:
            context.region_data.view_location = obj.matrix_world.translation
            bpy.ops.object.select_all(action="DESELECT")
            obj.select_set(True)
            context.view_layer.objects.active = obj
        else:
            context.region_data.view_location = entity.position
            bpy.ops.object.select_all(action="DESELECT")

        return {"FINISHED"}


# TODO(ymap): support other map items in sollumz.map_view_object_in_sidebar
class SOLLUMZ_OT_map_view_object_in_sidebar(Operator):
    bl_idname = "sollumz.map_view_object_in_sidebar"
    bl_label = "View in Sidebar"
    bl_description = ""
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        aobj = context.active_object
        return aobj is not None and MAP_INDEX.is_ready and get_maps(context)

    def _lookup_cache(self, obj):
        c = MAP_INDEX.find_by_id(obj)
        if c is None:
            for coll in obj.users_collection:
                c = MAP_INDEX.find_by_id(coll)
                if c is not None:
                    break

        return c

    def execute(self, context):
        aobj = context.active_object
        active_cache = self._lookup_cache(aobj)
        if active_cache is None:
            self.report({"WARNING"}, f"Object '{aobj.name}' not used in any map.")
            return {"CANCELLED"}

        selected_cache = [
            c
            for o in context.selected_objects
            if o != aobj
            and (c := self._lookup_cache(o))
            and c.map_group_uuid == active_cache.map_group_uuid
            and c.data_type == active_cache.data_type
        ]

        maps = get_maps(context)
        group_index = maps.find_group_index(active_cache.map_group_uuid)
        group = maps.groups[group_index]

        maps.groups.select(group_index)
        match active_cache.data_type:
            case CacheObjectData.ENTITY:
                from ..ui.entities import SOLLUMZ_PT_map_entities

                entity_indices = [MAP_INDEX.try_get_entity(active_cache.data_uuid).index] + [
                    MAP_INDEX.try_get_entity(c.data_uuid).index for c in selected_cache
                ]
                group.entities.select_many(entity_indices)
                SOLLUMZ_PT_map_entities.make_active_tab()

            case CacheObjectData.CARGEN:
                from ..ui.cargens import SOLLUMZ_PT_map_cargens

                cargen_uuids = [active_cache.data_uuid] + [
                    c.data_uuid for c in selected_cache if c.data_uuid != active_cache.data_uuid
                ]
                cargen_indices_by_uuid = {cg.uuid: i for i, cg in enumerate(group.cargens)}
                cargen_indices = [cargen_indices_by_uuid[uuid] for uuid in cargen_uuids]
                group.cargens.select_many(cargen_indices)
                SOLLUMZ_PT_map_cargens.make_active_tab()

            case CacheObjectData.GRASS_BATCH:
                pass
            case CacheObjectData.OCCLUDER:
                pass
            case CacheObjectData.LOD_LIGHTS:
                pass

        tag_redraw(context, space_type="VIEW_3D", region_type="UI")

        return {"FINISHED"}


class SOLLUMZ_OT_map_entity_add_extension(Operator):
    """Add an extension to the entity"""

    bl_idname = "sollumz.map_entity_add_extension"
    bl_options = {"UNDO"}
    bl_label = "Add Extension"

    @classmethod
    def poll(cls, context):
        return active_entity(context) is not None

    def execute(self, context):
        selected_entity = active_entity(context)
        selected_entity.new_extension()
        return {"FINISHED"}


class SOLLUMZ_OT_map_entity_delete_extension(Operator):
    """Delete the selected extension from the entity"""

    bl_idname = "sollumz.map_entity_delete_extension"
    bl_options = {"UNDO"}
    bl_label = "Delete Extension"

    @classmethod
    def poll(cls, context):
        return active_entity_extension(context) is not None

    def execute(self, context):
        selected_entity = active_entity(context)
        selected_entity.delete_selected_extension()
        return {"FINISHED"}


class SOLLUMZ_OT_map_entity_duplicate_extension(Operator):
    """Duplicate the selected extension in the entity"""

    bl_idname = "sollumz.map_entity_duplicate_extension"
    bl_options = {"UNDO"}
    bl_label = "Duplicate Extension"

    @classmethod
    def poll(cls, context):
        return active_entity_extension(context) is not None

    def execute(self, context):
        selected_entity = active_entity(context)
        selected_entity.duplicate_selected_extension()
        return {"FINISHED"}
