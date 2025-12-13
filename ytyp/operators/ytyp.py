import os
import traceback
import bpy
from bpy.props import (
    IntProperty,
    BoolProperty,
    StringProperty,
    PointerProperty,
)
from bpy_extras.io_utils import ImportHelper
from ...sollumz_helper import SOLLUMZ_OT_base, has_embedded_textures, has_collision
from ...sollumz_properties import SOLLUMZ_UI_NAMES, ArchetypeType, AssetType, SollumType
from ...sollumz_operators import SelectTimeFlagsRangeMultiSelect, ClearTimeFlagsMultiSelect, ImportAssetsOperatorImpl, ExportSettingsOverride
from ...sollumz_preferences import get_export_settings, get_addon_preferences
from ...ydr.cloth_env import cloth_env_find_mesh_objects
from ..utils import get_selected_ytyp, get_selected_archetype
from ..ytypimport import import_ytyp
from ..ytypexport import selected_ytyp_to_xml
from ...shared.multiselection import (
    MultiSelectOneOperator,
    MultiSelectAllOperator,
    MultiSelectInvertOperator,
)
from ... import logger


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


class ArchetypesSelectMixin:
    ytyp_index: IntProperty(name="YTYP Index", min=-1, default=-1)

    def get_collection(self, context):
        return (
            get_selected_ytyp(context)
            if self.ytyp_index == -1
            else context.scene.ytyps[self.ytyp_index]
        ).archetypes


class SOLLUMZ_OT_ytyp_select_archetype(ArchetypesSelectMixin, MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.ytyp_select_archetype"
    bl_label = "Select Archetype"


class SOLLUMZ_OT_ytyp_select_all_archetypes(ArchetypesSelectMixin, MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.ytyp_select_all_archetypes"
    bl_label = "Select All Archetypes"


class SOLLUMZ_OT_ytyp_select_invert_archetypes(ArchetypesSelectMixin, MultiSelectInvertOperator, bpy.types.Operator):
    bl_idname = "sollumz.ytyp_select_invert_archetypes"
    bl_label = "Invert Selected Archetypes"


class MloEntitiesSelectMixin:
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


class SOLLUMZ_OT_archetype_select_mlo_entity(MloEntitiesSelectMixin, MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_entity"
    bl_label = "Select Entity"


class SOLLUMZ_OT_archetype_select_all_mlo_entity(MloEntitiesSelectMixin, MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_entity"
    bl_label = "Select All Entities"


class SOLLUMZ_OT_archetype_select_invert_mlo_entity(MloEntitiesSelectMixin, MultiSelectInvertOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_invert_mlo_entity"
    bl_label = "Invert Selected Entities"


class MloPortalsSelectMixin:
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


class SOLLUMZ_OT_archetype_select_mlo_portal(MloPortalsSelectMixin, MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_portal"
    bl_label = "Select Portal"


class SOLLUMZ_OT_archetype_select_all_mlo_portal(MloPortalsSelectMixin, MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_portal"
    bl_label = "Select All Portals"


class SOLLUMZ_OT_archetype_select_invert_mlo_portal(MloPortalsSelectMixin, MultiSelectInvertOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_invert_mlo_portal"
    bl_label = "Invert Selected Portals"


class MloRoomsSelectMixin:
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


class SOLLUMZ_OT_archetype_select_mlo_room(MloRoomsSelectMixin, MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_room"
    bl_label = "Select Room"


class SOLLUMZ_OT_archetype_select_all_mlo_room(MloRoomsSelectMixin, MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_room"
    bl_label = "Select All Rooms"


class SOLLUMZ_OT_archetype_select_invert_mlo_room(MloRoomsSelectMixin, MultiSelectInvertOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_invert_mlo_room"
    bl_label = "Invert Selected Rooms"


class MloTcmSelectMixin:
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


class SOLLUMZ_OT_archetype_select_mlo_tcm(MloTcmSelectMixin, MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_tcm"
    bl_label = "Select Timecycle Modifiers"


class SOLLUMZ_OT_archetype_select_all_mlo_tcm(MloTcmSelectMixin, MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_tcm"
    bl_label = "Select All Timecycle Modifiers"


class SOLLUMZ_OT_archetype_select_invert_mlo_tcm(MloTcmSelectMixin, MultiSelectInvertOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_invert_mlo_tcm"
    bl_label = "Invert Selected Timecycle Modifiers"


class MloEntitySetsSelectMixin:
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


class SOLLUMZ_OT_archetype_select_mlo_entity_set(MloEntitySetsSelectMixin, MultiSelectOneOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_mlo_entity_set"
    bl_label = "Select Entity Set"


class SOLLUMZ_OT_archetype_select_all_mlo_entity_set(MloEntitySetsSelectMixin, MultiSelectAllOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_all_mlo_entity_set"
    bl_label = "Select All Entity Sets"


class SOLLUMZ_OT_archetype_select_invert_mlo_entity_set(MloEntitySetsSelectMixin, MultiSelectInvertOperator, bpy.types.Operator):
    bl_idname = "sollumz.archetype_select_invert_mlo_entity_set"
    bl_label = "Invert Selected Entity Sets"


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

                if cloth_env_find_mesh_objects(obj, silent=True):
                    item.flags.flag26 = True  # set 'Has Cloth' flag

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


class SOLLUMZ_OT_import_ytyp_io(ImportAssetsOperatorImpl, bpy.types.Operator):
    """Import YTYPs"""
    bl_idname = "sollumz.import_ytyp_io"
    bl_label = "Import YTYP"
    bl_options = {"UNDO"}

    filter_glob: bpy.props.StringProperty(
        default="*.ytyp;*.ytyp.xml",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )


class SOLLUMZ_OT_export_ytyp_io(bpy.types.Operator):
    """Export the selected YTYP"""
    bl_idname = "sollumz.export_ytyp_io"
    bl_label = "Export YTYP"

    directory: StringProperty(
        name="Output directory",
        description="Select export output directory",
        subtype="DIR_PATH",
        options={"HIDDEN"}
    )

    # These are for scripts that use these operators to override the settings and avoid messing with the user preferences.
    use_custom_settings: BoolProperty(name="Use Custom Settings", default=False, options={"HIDDEN", "SKIP_SAVE"})
    custom_settings: PointerProperty(type=ExportSettingsOverride,
                                     name="Custom Settings", options={"HIDDEN", "SKIP_SAVE"})

    def draw(self, context):
        prefs = get_addon_preferences(context)
        if prefs.legacy_import_export:
            return

        export_prefs = prefs.export_settings
        from szio.gta5 import AssetFormat, is_provider_available
        row = self.layout.row(align=False)
        col = row.column(align=True, heading="Format")
        for f in ("NATIVE", "CWXML"):
            subrow = col.row(align=True)
            subrow.enabled = is_provider_available(AssetFormat[f])
            subrow.prop_enum(export_prefs, "target_formats", f)

        col = row.column(align=True, heading="Version")
        for f in ("GEN8", "GEN9"):
            col.prop_enum(export_prefs, "target_versions", f)

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    @classmethod
    def poll(cls, context):
        return 0 <= context.scene.ytyp_index < len(context.scene.ytyps)

    def execute(self, context):
        with logger.use_operator_logger(self) as op_log:
            prefs_export_settings = self.custom_settings if self.use_custom_settings else get_export_settings()

            from pathlib import Path
            from ..ytypexport_io import export_ytyp as export_ytyp_asset
            from ...iecontext import export_context_scope, ExportContext

            export_settings = prefs_export_settings.to_export_context_settings()
            if not export_settings.targets:
                from szio.gta5 import AssetFormat, AssetVersion, AssetTarget
                export_settings.targets = (AssetTarget(AssetFormat.CWXML, AssetVersion.GEN8),)
                logger.warning(
                    "No export target found. Make sure you select both Format and Version in the export settings. "
                    "Defaulting to CW XML / Gen 8."
                )

            directory = Path(bpy.path.abspath(self.directory))

            ytyp_name = context.scene.ytyps[context.scene.ytyp_index].name
            try:
                with export_context_scope(ExportContext(ytyp_name, export_settings)):
                    export_bundle = export_ytyp_asset(context.scene, context.scene.ytyp_index)
                success = bool(export_bundle)
                if success:
                    export_bundle.save(directory)
                    if op_log.has_warnings_or_errors:
                        logger.info(
                            f"Exported '{ytyp_name}' with WARNINGS or ERRORS! Please check the Info Log for details."
                        )
                    else:
                        logger.info(f"Successfully exported '{ytyp_name}'")
                else:
                    if op_log.has_warnings_or_errors:
                        logger.info(
                            f"Failed to export '{ytyp_name}', ERRORS found! Please check the Info Log for details."
                        )
                return {"FINISHED"}
            except Exception:
                logger.error(f"Error exporting: {ytyp_name} \n {traceback.format_exc()}")
                return {"CANCELLED"}
