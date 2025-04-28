import os
import traceback
import bpy
from bpy.props import (
    IntProperty,
)
from bpy_extras.io_utils import ImportHelper
from ...sollumz_helper import SOLLUMZ_OT_base, has_embedded_textures, has_collision
from ...sollumz_properties import SOLLUMZ_UI_NAMES, ArchetypeType, AssetType, SollumType
from ...sollumz_operators import SelectTimeFlagsRangeMultiSelect, ClearTimeFlagsMultiSelect
from ...sollumz_preferences import get_export_settings
from ..utils import get_selected_ytyp, get_selected_archetype
from ..ytypimport import import_ytyp
from ..ytypexport import selected_ytyp_to_xml
from ...shared.multiselection import MultiSelectOneOperator, MultiSelectAllOperator


class SOLLUMZ_OT_create_ytyp(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a ytyp to the project"""
    bl_idname = "sollumz.createytyp"
    bl_label = "Create YTYP"

    def run(self, context):
        item = context.scene.ytyps.add()
        index = len(context.scene.ytyps)
        item.name = f"YTYP.{index}"
        context.scene.ytyp_index = index - 1

        return True


class SOLLUMZ_OT_delete_ytyp(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete a ytyp from the project"""
    bl_idname = "sollumz.deleteytyp"
    bl_label = "Delete YTYP"

    @classmethod
    def poll(cls, context):
        return len(context.scene.ytyps) > 0

    def run(self, context):
        context.scene.ytyps.remove(context.scene.ytyp_index)
        context.scene.ytyp_index = max(context.scene.ytyp_index - 1, 0)
        # Force redraw of gizmos
        context.space_data.show_gizmo = context.space_data.show_gizmo

        return True


class SOLLUMZ_OT_create_archetype(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add an archetype to the selected ytyp"""
    bl_idname = "sollumz.createarchetype"
    bl_label = "Create Archetype"

    @classmethod
    def poll(cls, context):
        return get_selected_ytyp(context) is not None

    def run(self, context):
        archetype_type = context.scene.create_archetype_type
        selected_ytyp = get_selected_ytyp(context)
        selected_ytyp.new_archetype(archetype_type)

        return True


class SOLLUMZ_OT_ytyp_select_archetype(MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.ytyp_select_archetype"
    bl_label = "Select Archetype"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_ytyp(context)
            if self.ytyp_index == -1
            else context.scene.ytyps[self.ytyp_index]
        ).archetypes


class SOLLUMZ_OT_ytyp_select_all_archetypes(MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.ytyp_select_all_archetypes"
    bl_label = "Select All Archetypes"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_ytyp(context)
            if self.ytyp_index == -1
            else context.scene.ytyps[self.ytyp_index]
        ).archetypes


class SOLLUMZ_OT_archetype_select_mlo_entity(MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_entity"
    bl_label = "Select Entity"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).entities

    def _filter_items_impl(self, context) -> tuple[list[int], list[int]]:
        from ..ui.entities import entities_filter_items
        return entities_filter_items(
            self.get_collection(context),
            self.filter_name,
            self.use_filter_sort_reverse,
            self.use_filter_sort_alpha
        )


class SOLLUMZ_OT_archetype_select_all_mlo_entity(MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_entity"
    bl_label = "Select All Entities"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).entities

    def _filter_items_impl(self, context) -> tuple[list[int], list[int]]:
        from ..ui.entities import entities_filter_items
        return entities_filter_items(
            self.get_collection(context),
            self.filter_name,
            self.use_filter_sort_reverse,
            self.use_filter_sort_alpha
        )


class SOLLUMZ_OT_archetype_select_mlo_portal(MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_portal"
    bl_label = "Select Portal"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).portals


class SOLLUMZ_OT_archetype_select_all_mlo_portal(MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_portal"
    bl_label = "Select All Portals"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).portals


class SOLLUMZ_OT_archetype_select_mlo_room(MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_room"
    bl_label = "Select Room"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).rooms


class SOLLUMZ_OT_archetype_select_all_mlo_room(MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_room"
    bl_label = "Select All Rooms"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).rooms


class SOLLUMZ_OT_archetype_select_mlo_tcm(MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_tcm"
    bl_label = "Select Room"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).timecycle_modifiers


class SOLLUMZ_OT_archetype_select_all_mlo_tcm(MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_tcm"
    bl_label = "Select All Rooms"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).timecycle_modifiers


class SOLLUMZ_OT_archetype_select_mlo_entity_set(MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_entity_set"
    bl_label = "Select Entity Set"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).entity_sets


class SOLLUMZ_OT_archetype_select_all_mlo_entity_set(MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_entity_set"
    bl_label = "Select All Entity Sets"

    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)
    archetype_index: IntProperty(name="Archetype Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_archetype(context)
            if self.archetype_index == -1
            else (
                get_selected_ytyp(context)
                if self.ytyp_index == -1
                else context.scene.ytyps[self.ytyp_index]
            ).archetypes[self.archetype_index]
        ).entity_sets


class SOLLUMZ_OT_create_archetype_from_selected(SOLLUMZ_OT_base, bpy.types.Operator):
    """Create archetype from selected"""
    bl_idname = "sollumz.createarchetypefromselected"
    bl_label = "Auto-Create From Selected"

    allowed_types = [SollumType.DRAWABLE,
                     SollumType.BOUND_COMPOSITE, SollumType.FRAGMENT, SollumType.DRAWABLE_DICTIONARY]

    @classmethod
    def poll(cls, context):
        return get_selected_ytyp(context) is not None

    def run(self, context):
        selected_objs = context.selected_objects
        found = False
        for obj in selected_objs:
            archetype_type = context.scene.create_archetype_type
            if not obj.sollum_type in self.allowed_types:
                continue
            if archetype_type == ArchetypeType.MLO:
                if obj.sollum_type != SollumType.BOUND_COMPOSITE:
                    self.message(
                        f"MLO asset '{obj.name}' must be a {SOLLUMZ_UI_NAMES[SollumType.BOUND_COMPOSITE]}!")
                    continue
            found = True
            selected_ytyp = get_selected_ytyp(context)
            item = selected_ytyp.new_archetype(archetype_type)
            item.name = obj.name
            item.asset = obj
            item.texture_dictionary = obj.name if has_embedded_textures(obj) else ""
            drawable_dictionary = ""
            if obj.parent:
                if obj.parent.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                    drawable_dictionary = obj.parent.name
            item.drawable_dictionary = drawable_dictionary
            item.physics_dictionary = obj.name if has_collision(obj) and obj.sollum_type != SollumType.FRAGMENT else ""

            if obj.sollum_type == SollumType.DRAWABLE:
                item.asset_type = AssetType.DRAWABLE
            elif obj.sollum_type == SollumType.DRAWABLE_DICTIONARY:
                item.asset_type = AssetType.DRAWABLE_DICTIONARY
            elif obj.sollum_type == SollumType.BOUND_COMPOSITE:
                item.asset_type = AssetType.ASSETLESS
            elif obj.sollum_type == SollumType.FRAGMENT:
                item.asset_type = AssetType.FRAGMENT

        if not found:
            self.message(
                f"No asset of type '{','.join([SOLLUMZ_UI_NAMES[type] for type in self.allowed_types])}' found!")
            return False
        return True


class SOLLUMZ_OT_delete_archetype(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete selected archetype(s)"""
    bl_idname = "sollumz.deletearchetype"
    bl_label = "Delete Archetype"

    @classmethod
    def poll(cls, context):
        selected_ytyp = get_selected_ytyp(context)
        return selected_ytyp is not None and len(selected_ytyp.archetypes) > 0

    def run(self, context):
        selected_ytyp = get_selected_ytyp(context)

        indices_to_remove = selected_ytyp.archetypes.selected_items_indices
        indices_to_remove.sort(reverse=True)
        new_active_index = max(indices_to_remove[-1] - 1, 0) if indices_to_remove else 0
        for index_to_remove in indices_to_remove:
            selected_ytyp.archetypes.remove(index_to_remove)
        selected_ytyp.archetypes.select(new_active_index)

        # Force redraw of gizmos
        context.space_data.show_gizmo = context.space_data.show_gizmo

        return True


class SOLLUMZ_OT_create_timecycle_modifier(SOLLUMZ_OT_base, bpy.types.Operator):
    """Add a timecycle modifier to the selected archetype"""
    bl_idname = "sollumz.createtimecyclemodifier"
    bl_label = "Create Timecycle Modifier"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def run(self, context):
        selected_archetype = get_selected_archetype(context)
        item = selected_archetype.new_tcm()
        item.name = f"Timecycle Modifier.{len(selected_archetype.timecycle_modifiers)}"
        return True


class SOLLUMZ_OT_delete_timecycle_modifier(SOLLUMZ_OT_base, bpy.types.Operator):
    """Delete selected timecycle modifier(s)"""
    bl_idname = "sollumz.deletetimecyclemodifier"
    bl_label = "Delete Timecycle Modifier"

    @classmethod
    def poll(cls, context):
        selected_archetype = get_selected_archetype(context)
        return selected_archetype is not None and selected_archetype.timecycle_modifiers

    def run(self, context):
        selected_archetype = get_selected_archetype(context)

        indices_to_remove = selected_archetype.timecycle_modifiers.selected_items_indices
        indices_to_remove.sort(reverse=True)
        new_active_index = max(indices_to_remove[-1] - 1, 0) if indices_to_remove else 0
        for index_to_remove in indices_to_remove:
            selected_archetype.timecycle_modifiers.remove(index_to_remove)
        selected_archetype.timecycle_modifiers.select(new_active_index)

        return True


class SOLLUMZ_OT_YTYP_TIME_FLAGS_select_range(SelectTimeFlagsRangeMultiSelect, bpy.types.Operator):
    bl_idname = "sollumz.ytyp_time_flags_select_range"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def iter_selection_flags(self, context):
        yield from (arch.time_flags for arch in get_selected_ytyp(context).archetypes.iter_selected_items())


class SOLLUMZ_OT_YTYP_TIME_FLAGS_clear(ClearTimeFlagsMultiSelect, bpy.types.Operator):
    bl_idname = "sollumz.ytyp_time_flags_clear"

    @classmethod
    def poll(cls, context):
        return get_selected_archetype(context) is not None

    def iter_selection_flags(self, context):
        yield from (arch.time_flags for arch in get_selected_ytyp(context).archetypes.iter_selected_items())


class SOLLUMZ_OT_import_ytyp(SOLLUMZ_OT_base, bpy.types.Operator, ImportHelper):
    """Import a ytyp.xml"""
    bl_idname = "sollumz.importytyp"
    bl_label = "Import ytyp.xml"
    bl_action = "Import a YTYP"

    filename_ext = ".ytyp.xml"

    filter_glob: bpy.props.StringProperty(
        default="*.ytyp.xml",
        options={"HIDDEN"},
        maxlen=255,
    )

    def draw(self, context):
        pass

    def run(self, context):
        try:
            import_ytyp(self.filepath)
            self.message(f"Successfully imported: {self.filepath}")
            return True
        except:
            self.error(f"Error during import: {traceback.format_exc()}")
            return False


class SOLLUMZ_OT_export_ytyp(SOLLUMZ_OT_base, bpy.types.Operator):
    """Export the selected YTYP"""
    bl_idname = "sollumz.exportytyp"
    bl_label = "Export ytyp.xml"
    bl_action = "Export a YTYP"

    filter_glob: bpy.props.StringProperty(
        default="*.ytyp.xml",
        options={"HIDDEN"},
        maxlen=255,
    )

    directory: bpy.props.StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
    )

    def draw(self, context):
        pass

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    @classmethod
    def poll(cls, context):
        num_ytyps = len(context.scene.ytyps)
        return num_ytyps > 0 and context.scene.ytyp_index < num_ytyps

    def get_filepath(self, name):
        return os.path.join(self.directory, name + ".ytyp.xml")

    def run(self, context):
        try:
            export_settings = get_export_settings(context)

            ytyp = selected_ytyp_to_xml(export_settings.apply_transforms)
            filepath = self.get_filepath(ytyp.name)
            ytyp.write_xml(filepath)
            self.message(f"Successfully exported: {filepath}")
            return True
        except:
            self.error(f"Error during export: {traceback.format_exc()}")
            return False
