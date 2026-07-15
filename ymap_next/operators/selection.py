from bpy.types import (
    Operator,
)

from ...shared.multiselection import (
    MultiSelectAllOperator,
    MultiSelectInvertOperator,
    MultiSelectOneOperator,
)
from ..properties.map import get_maps


class MapsGroupsSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups


class SOLLUMZ_OT_maps_select_group(MapsGroupsSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.maps_select_group"
    bl_label = "Select Map Group"


class SOLLUMZ_OT_maps_select_all_groups(MapsGroupsSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.maps_select_all_groups"
    bl_label = "Select All Map Groups"


class SOLLUMZ_OT_maps_select_invert_groups(MapsGroupsSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.maps_select_invert_groups"
    bl_label = "Invert Selected Map Groups"


class MapGroupMapsSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups.active_item.maps

    def _filter_items_impl(self, context) -> tuple[list[int], list[int]]:
        # TODO(ymap): this need to be in sync with SOLLUMZ_UL_map_group_map_data_list, refactor
        return [], [m.ui_tree_sort_id for m in self.get_collection(context)]
        # from ..ui.entities import entities_filter_items
        # return entities_filter_items(
        #     self.get_collection(context),
        #     self.filter_name,
        #     self.use_filter_sort_reverse,
        #     self.use_filter_sort_alpha
        # )


class SOLLUMZ_OT_map_group_select_map(MapGroupMapsSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.map_group_select_map"
    bl_label = "Select Map Container"


class SOLLUMZ_OT_map_group_select_all_maps(MapGroupMapsSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.map_group_select_all_maps"
    bl_label = "Select All Map Containers"


class SOLLUMZ_OT_map_group_select_invert_maps(MapGroupMapsSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.map_group_select_invert_maps"
    bl_label = "Invert Selected Map Container"


class MapGroupEntitiesSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups.active_item.entities

    def _filter_items_impl(self, context) -> tuple[list[int], list[int]]:
        from ..ui.entities import map_entities_filter_items

        return map_entities_filter_items(
            self.get_collection(context),
            self.filter_name,
            self.use_filter_sort_reverse,
            self.use_filter_sort_alpha,
        )


class SOLLUMZ_OT_map_group_select_entity(MapGroupEntitiesSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.map_group_select_entity"
    bl_label = "Select Map Entity"


class SOLLUMZ_OT_map_group_select_all_entities(MapGroupEntitiesSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.map_group_select_all_entities"
    bl_label = "Select All Map Entities"


class SOLLUMZ_OT_map_group_select_invert_entities(MapGroupEntitiesSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.map_group_select_invert_entities"
    bl_label = "Invert Selected Map Entities"


class MapGroupCarGensSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups.active_item.cargens


class SOLLUMZ_OT_map_group_select_cargen(MapGroupCarGensSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.map_group_select_cargen"
    bl_label = "Select Map Car Generator"


class SOLLUMZ_OT_map_group_select_all_cargens(MapGroupCarGensSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.map_group_select_all_cargens"
    bl_label = "Select All Map Car Generators"


class SOLLUMZ_OT_map_group_select_invert_cargens(MapGroupCarGensSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.map_group_select_invert_cargens"
    bl_label = "Invert Selected Map Car Generators"


class MapGroupTimecycleModifiersSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups.active_item.timecycle_modifiers


class SOLLUMZ_OT_map_group_select_tcm(MapGroupTimecycleModifiersSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.map_group_select_tcm"
    bl_label = "Select Map Timecycle Modifier"


class SOLLUMZ_OT_map_group_select_all_tcms(MapGroupTimecycleModifiersSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.map_group_select_all_tcms"
    bl_label = "Select All Map Timecycle Modifiers"


class SOLLUMZ_OT_map_group_select_invert_tcms(
    MapGroupTimecycleModifiersSelectMixin, MultiSelectInvertOperator, Operator
):
    bl_idname = "sollumz.map_group_select_invert_tcms"
    bl_label = "Invert Selected Map Timecycle Modifiers"


class MapGroupGrassBatchesSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups.active_item.grass_batches


class SOLLUMZ_OT_map_group_select_grass_batch(MapGroupGrassBatchesSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.map_group_select_grass_batch"
    bl_label = "Select Map Grass Batch"


class SOLLUMZ_OT_map_group_select_all_grass_batches(MapGroupGrassBatchesSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.map_group_select_all_grass_batches"
    bl_label = "Select All Map Grass Batches"


class SOLLUMZ_OT_map_group_select_invert_grass_batches(
    MapGroupGrassBatchesSelectMixin, MultiSelectInvertOperator, Operator
):
    bl_idname = "sollumz.map_group_select_invert_grass_batches"
    bl_label = "Invert Selected Map Grass Batches"


class MapGroupGrassTemplatesSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups.active_item.grass_batches.active_item.templates


class SOLLUMZ_OT_map_group_select_grass_template(MapGroupGrassTemplatesSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.map_group_select_grass_template"
    bl_label = "Select Map Grass template"


class SOLLUMZ_OT_map_group_select_all_grass_templates(
    MapGroupGrassTemplatesSelectMixin, MultiSelectAllOperator, Operator
):
    bl_idname = "sollumz.map_group_select_all_grass_templates"
    bl_label = "Select All Map Grass templates"


class SOLLUMZ_OT_map_group_select_invert_grass_templates(
    MapGroupGrassTemplatesSelectMixin, MultiSelectInvertOperator, Operator
):
    bl_idname = "sollumz.map_group_select_invert_grass_templates"
    bl_label = "Invert Selected Map Grass templates"


class MapGroupOccludersSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups.active_item.occluders


class SOLLUMZ_OT_map_group_select_occluder(MapGroupOccludersSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.map_group_select_occluder"
    bl_label = "Select Map Occluder"


class SOLLUMZ_OT_map_group_select_all_occluders(MapGroupOccludersSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.map_group_select_all_occluders"
    bl_label = "Select All Map Occluders"


class SOLLUMZ_OT_map_group_select_invert_occluders(MapGroupOccludersSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.map_group_select_invert_occluders"
    bl_label = "Invert Selected Map Occluders"


class MapGroupLodLightsSelectMixin:
    def get_collection(self, context):
        return get_maps(context).groups.active_item.lod_lights


class SOLLUMZ_OT_map_group_select_lod_lights(MapGroupLodLightsSelectMixin, MultiSelectOneOperator, Operator):
    bl_idname = "sollumz.map_group_select_lod_lights"
    bl_label = "Select Map LOD Lights"


class SOLLUMZ_OT_map_group_select_all_lod_lights(MapGroupLodLightsSelectMixin, MultiSelectAllOperator, Operator):
    bl_idname = "sollumz.map_group_select_all_lod_lights"
    bl_label = "Select All Map LOD Lights"


class SOLLUMZ_OT_map_group_select_invert_lod_lights(MapGroupLodLightsSelectMixin, MultiSelectInvertOperator, Operator):
    bl_idname = "sollumz.map_group_select_invert_lod_lights"
    bl_label = "Invert Selected Map LOD Lights"
