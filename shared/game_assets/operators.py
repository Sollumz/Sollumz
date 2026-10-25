import os
import functools
import posixpath
import time
from collections.abc import Iterable, Iterator, Sequence
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path

import bpy
from bpy.props import (
    BoolProperty,
    CollectionProperty,
    EnumProperty,
    StringProperty,
    IntProperty,
)
from bpy.types import (
    AssetRepresentation,
    Object,
    Operator,
    PropertyGroup,
)
from mathutils import Matrix
from szio.jenkhash import name_to_hash

from ... import logger
from ...dependencies import IS_SZIO_NATIVE_AVAILABLE, PYMATERIA_REQUIRED_MSG
from ...sollumz_preferences import (
    ImportSettingsBase,
    get_addon_preferences,
    get_import_settings,
    invoke_with_game_directory,
    save_game_directory,
)
from ...sollumz_helper import copy_object_hierarchy
from ...sollumz_operators import SOLLUMZ_OT_import_assets
from ...sollumz_properties import SollumType
from ...tools.blenderhelper import get_object_with_children_recursive, remove_number_suffix
from ..object_hierarchy import ObjectHierarchySnapshot
from .asset_info import (
    AssetArchetypeInfo,
    try_get_asset_metadata_archetype_info,
    try_get_asset_representation_archetype_info,
)
from .game_files import ArchetypeFiles, find_game_asset_files, is_game_installation
from .library import (
    asset_cache_path,
    build_library,
    build_library_cache,
)

NEW_TAG = "<<NEW>>"


def _output_directory_choice_items(self, context):
    prefs = get_addon_preferences(context)
    items = []
    for d in prefs.shared_assets_directories:
        if not d.path:
            continue
        items.append((d.path, f"{d.name} | {d.path}", ""))
    items.append((NEW_TAG, "New...", "Save it to a new asset library directory"))
    return items


_build_library_progress = None


def temporary_ui(layout):
    op = layout.operator(SOLLUMZ_OT_import_assets.bl_idname, text="Import To Asset Library", icon="IMPORT")
    op.import_as_asset = True
    layout.operator(SOLLUMZ_OT_build_game_asset_library.bl_idname)
    if _build_library_progress is not None:
        completed, total = _build_library_progress
        layout.progress(
            text=f"Creating Asset Libraries ({completed}/{total})...",
            factor=completed / total if total > 0 else 0,
        )
    layout.operator(SOLLUMZ_OT_rebuild_game_asset_cache.bl_idname)


class SOLLUMZ_OT_build_game_asset_library(Operator):
    bl_idname = "sollumz.build_game_asset_library"
    bl_label = "Build Asset Library"
    bl_description = (
        "Import .ytyp game files from a directory and create .blend asset library files "
        "in the configured Shared Assets directory"
    )

    directory: StringProperty(
        name="Source Directory",
        description="Directory containing .ytyp files and their assets",
        subtype="DIR_PATH",
        options={"HIDDEN"},
    )

    filter_glob: StringProperty(
        default="*.ytyp;*.ytyp.xml",
        options={"HIDDEN", "SKIP_SAVE"},
        maxlen=255,
    )

    output_directory: StringProperty(
        name="Output Directory",
        description="Directory where .blend libraries should be saved",
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    output_directory_choice: EnumProperty(
        name="Output Library",
        description="Which directory to write the .blend libraries into",
        items=_output_directory_choice_items,
        options={"SKIP_SAVE"},
    )
    new_output_directory_name: StringProperty(
        name="Name",
        description="Name of the new asset library",
    )
    new_output_directory_path: StringProperty(
        name="Path",
        description="Path to a directory where to store the new asset library",
    )

    pattern: StringProperty(
        name="Pattern",
        description=(
            "Regular expression matched against .ytyp file names to filter which ones are imported. "
            "Leave empty to import all"
        ),
    )
    num_subprocesses: IntProperty(
        name="Subprocesses",
        description=(
            "Number of Blender subprocesses to spawn for building libraries in parallel. "
            "Each worker runs a separate Blender instance, so higher values build faster but use more memory and CPU"
        ),
        default=max(1, os.cpu_count() // 4),
        min=1,
        max=os.cpu_count(),
    )

    @classmethod
    def poll(cls, context):
        if bpy.app.version < (4, 2, 0):
            # Currently, we use Blender CLI commands to spawn the subprocess workers which were added in 4.2.
            cls.poll_message_set("Cannot build library on this Blender version. Update to Blender 4.2 or newer.")
            return False

        return True

    def invoke(self, context, event):
        context.window_manager.fileselect_add(self)
        return {"RUNNING_MODAL"}

    def draw(self, context):
        layout = self.layout
        layout.use_property_split = True
        layout.use_property_decorate = False

        col = layout.column(align=True)
        col.prop(self, "output_directory_choice")
        if self.output_directory_choice == NEW_TAG:
            col.prop(self, "new_output_directory_name")
            col.prop(self, "new_output_directory_path")

        layout.prop(self, "pattern")
        layout.prop(self, "num_subprocesses")

    def execute(self, context):
        if not self.output_directory:
            prefs = get_addon_preferences(context)
            if self.output_directory_choice == NEW_TAG:
                new_directory = Path(bpy.path.abspath(self.new_output_directory_path))
                try:
                    new_directory.mkdir(parents=True, exist_ok=True)
                except FileExistsError:
                    self.report({"ERROR"}, f"Expected a directory, not a file: {str(new_directory)}")
                    return {"CANCELLED"}

                self.output_directory = self.new_output_directory_path
                bpy.ops.sollumz.prefs_shared_assets_directory_add(
                    name=self.new_output_directory_name, path=self.new_output_directory_path
                )
            else:
                if not prefs.shared_assets_directories:
                    self.report({"ERROR"}, "No Shared Assets directory configured. Add one in Preferences > Sollumz.")
                    return {"CANCELLED"}

                configured_paths = [d.path for d in prefs.shared_assets_directories if d.path]
                if len(configured_paths) > 1:
                    if self.output_directory_choice and self.output_directory_choice in configured_paths:
                        self.output_directory = self.output_directory_choice
                    else:
                        self.report({"WARNING"}, "No output library selected; using the first configured directory.")
                        self.output_directory = configured_paths[0]
                else:
                    self.output_directory = configured_paths[0]

        output_directory = Path(bpy.path.abspath(self.output_directory))
        output_directory.mkdir(parents=True, exist_ok=True)

        source_directory = Path(bpy.path.abspath(self.directory))
        if not source_directory.is_dir():
            self.report({"ERROR"}, f"Source directory does not exist: '{source_directory}'")
            return {"CANCELLED"}

        work_iter = build_library(
            source_directory,
            output_directory,
            game_catalog="GTA5",
            num_subprocesses=self.num_subprocesses,
            typ_pattern=self.pattern,
            report_progress_cb=_report_build_library_progress,
        )
        bpy.app.timers.register(functools.partial(_timer_do_work, work_iter), first_interval=0.0, persistent=True)
        return {"FINISHED"}


def _report_build_library_progress(num_completed: int | None, num_total: int | None):
    global _build_library_progress
    if num_completed is None:
        # finished
        _build_library_progress = None
    else:
        _build_library_progress = num_completed, num_total


def _timer_do_work(work_iter):
    interval = next(work_iter, None)
    return interval


class SOLLUMZ_OT_rebuild_game_asset_cache(Operator):
    bl_idname = "sollumz.rebuild_game_asset_cache"
    bl_label = "Debug - Rebuild Asset Cache"
    bl_description = "Rebuild the SQLite asset cache from existing .blend files in the Shared Assets directory"
    bl_options = {"UNDO"}

    @classmethod
    def poll(cls, context):
        prefs = get_addon_preferences(context)
        return len(prefs.shared_assets_directories) > 0

    def execute(self, context):
        prefs = get_addon_preferences(context)
        if not prefs.shared_assets_directories:
            self.report({"ERROR"}, "No Shared Assets directory configured.")
            return {"CANCELLED"}

        directories = []
        for d in prefs.shared_assets_directories:
            if not d.path:
                continue
            path = Path(bpy.path.abspath(d.path))
            if not path.is_dir():
                self.report({"WARNING"}, f"Shared Assets directory does not exist, skipping: '{path}'")
                continue
            directories.append(path)

        if not directories:
            self.report({"ERROR"}, "No valid Shared Assets directories found.")
            return {"CANCELLED"}

        build_library_cache(directories)
        self.report({"INFO"}, f"Asset cache rebuilt at '{asset_cache_path()}'")
        return {"FINISHED"}


def get_active_game_asset(context) -> AssetArchetypeInfo | None:
    """Return the archetype information of the active asset in the Asset Browser if it is an asset from a game asset
    library, otherwise `None`.
    """
    return try_get_asset_representation_archetype_info(getattr(context, "asset", None))


def iter_selected_game_assets(context) -> Iterator[tuple[AssetRepresentation, AssetArchetypeInfo]]:
    """Iterate the selected assets in the Asset Browser that are from a game asset library, with their archetype
    information.
    """
    assets = getattr(context, "selected_assets", None) or (getattr(context, "asset", None),)
    for asset in assets:
        if (archetype_info := try_get_asset_representation_archetype_info(asset)) is not None:
            yield asset, archetype_info


def get_object_game_asset(obj: Object | None) -> AssetArchetypeInfo | None:
    """If `obj` is an object from a game asset library, return its archetype information, otherwise `None`."""
    return try_get_asset_metadata_archetype_info(obj, resolve_scene_ytyps=False)


def _validated_game_directory(operator: Operator, context) -> Path | None:
    """The GTA V installation directory selected in `operator`, which is saved in the preferences. Logs an error and
    returns `None` if it is not a game installation.
    """
    if not operator.directory:
        logger.error("No GTA V installation directory selected.")
        return None

    game_dir = Path(bpy.path.abspath(operator.directory))
    if not is_game_installation(game_dir):
        logger.error(f"'{operator.directory}' is not a GTA V installation directory.")
        return None

    save_game_directory(game_dir, context)
    return game_dir


@contextmanager
def _wait_cursor(context):
    window = context.window
    if window is not None:
        window.cursor_modal_set("WAIT")
    try:
        yield
    finally:
        if window is not None:
            window.cursor_modal_restore()


def _find_game_asset_files_batch(
    context, game_dir: Path, assets: Iterable[tuple[str, str]]
) -> list[ArchetypeFiles | None]:
    # Finding the files needs to index the whole game directory the first time, which takes a while
    with _wait_cursor(context):
        ytyp_cache = {}
        found_files = []
        for asset_name, ytyp_name in assets:
            files = find_game_asset_files(game_dir, asset_name, ytyp_name, ytyp_cache=ytyp_cache)
            if files is None:
                logger.error(f"Could not find the game files of '{asset_name}'.")
            found_files.append(files)
        return found_files


def _import_game_asset_files(files: Iterable[ArchetypeFiles]) -> list[str]:
    """Import the game files of assets with the Import RAGE Assets operator and the user import settings. Files shared
    by multiple assets, such as texture dictionaries, are only imported once, and texture dictionaries already in the
    scene are not imported again. Returns the errors reported by the import.
    """
    import_settings = get_import_settings()
    import_kwargs = {name: getattr(import_settings, name) for name in ImportSettingsBase.__annotations__}
    textures_mode = import_kwargs["textures_mode"]
    has_custom_dir = bool(import_kwargs["textures_extract_custom_directory"])
    if textures_mode == "IMPORT_DIR" or (textures_mode == "CUSTOM_DIR" and not has_custom_dir):
        # Cannot extract textures next to the imported files, they are inside the game archives
        import_kwargs["textures_mode"] = "PACK"

    # Disable external skeleton since drawable dictionaries used in .ytyp don't use external skeletons, only peds do
    import_kwargs["dwd_import_external_skeleton"] = "NO"

    # Import all files in a single call, from their common directory and with their paths relative to it as names. The
    # import operator imports .ytds before the models, so their textures are used by the model materials
    files = list(files)
    scene_txds = {name_to_hash(txd.name) for txd in bpy.context.scene.sz_txds.texture_dictionaries}
    txd_paths = [
        f.txd for f in files if f.txd is not None and name_to_hash(f.txd.name.split(".", 1)[0]) not in scene_txds
    ]
    asset_paths = [f.asset for f in files if f.asset is not None]
    paths = list(dict.fromkeys(str(p) for p in (*txd_paths, *asset_paths)))
    if not paths:
        return []

    directory = posixpath.commonpath([posixpath.dirname(p) for p in paths])
    try:
        bpy.ops.sollumz.import_assets(
            directory=directory,
            files=[{"name": p[len(directory):].lstrip("/")} for p in paths],
            use_custom_settings=True,
            **import_kwargs,
        )
    except RuntimeError as e:
        # Errors reported by the operator are raised as exceptions
        return [str(e).strip()]

    return []


class GameDirectoryOperatorMixin:
    """Operators that read the game files, from the GTA V installation directory saved in the preferences or selected
    with the file browser."""

    # SKIP_SAVE so a directory remembered from a previous run doesn't take priority over the one in the preferences
    directory: StringProperty(
        name="Game Directory",
        description="GTA V installation directory",
        subtype="DIR_PATH",
        options={"HIDDEN", "SKIP_SAVE"},
    )

    def invoke(self, context, event):
        return invoke_with_game_directory(self, context)

    def draw(self, context):
        self.layout.label(text="Select the GTA V installation directory")


class GameAssetItem(PropertyGroup):
    asset_name: StringProperty()
    ytyp_name: StringProperty()
    is_interior: BoolProperty()


class SOLLUMZ_OT_import_library_asset_from_game_installation(GameDirectoryOperatorMixin, Operator):
    bl_idname = "sollumz.import_library_asset_from_game_installation"
    bl_label = "Import from Game Installation"
    bl_description = (
        "Search the game installation directory for the files of the selected assets and import them with all their "
        "data (LODs, collisions, lights, skeleton, etc.), instead of the simplified models stored in the asset "
        "library"
    )
    bl_options = {"UNDO"}

    # Copied from the selected assets on invoke, the assets are no longer in the context after the file browser closes
    assets: CollectionProperty(
        type=GameAssetItem,
        options={"HIDDEN", "SKIP_SAVE"},
    )

    @classmethod
    def poll(cls, context):
        if not IS_SZIO_NATIVE_AVAILABLE:
            cls.poll_message_set(PYMATERIA_REQUIRED_MSG)
            return False

        any_game_asset = False
        for _, archetype_info in iter_selected_game_assets(context):
            if archetype_info.type != "MLO":
                return True
            any_game_asset = True

        if any_game_asset:
            cls.poll_message_set("Importing interiors from game installation is not supported")
        else:
            cls.poll_message_set("No game asset selected")
        return False

    @classmethod
    def label(cls, context) -> str:
        """Label for the operator buttons, includes the number of assets that will be imported when there are
        multiple."""
        num_assets = sum(1 for _, archetype_info in iter_selected_game_assets(context) if archetype_info.type != "MLO")
        if num_assets > 1:
            return f"Import {num_assets} Assets from Game Installation"
        return cls.bl_label

    def invoke(self, context, event):
        self.assets.clear()
        for asset, archetype_info in iter_selected_game_assets(context):
            item = self.assets.add()
            item.asset_name = asset.name
            item.ytyp_name = archetype_info.ytyp
            item.is_interior = archetype_info.type == "MLO"

        return invoke_with_game_directory(self, context)

    def execute(self, context):
        start_time = time.time()
        with logger.use_operator_logger(self):
            if (game_dir := _validated_game_directory(self, context)) is None:
                return {"CANCELLED"}

            if not self.assets:
                logger.error("No game asset selected.")
                return {"CANCELLED"}

            assets = []
            for item in self.assets:
                asset_name = remove_number_suffix(item.asset_name).lower()
                if item.is_interior:
                    logger.warning(
                        f"Importing interiors from game installation is not supported, skipping '{asset_name}'."
                    )
                    continue
                assets.append((asset_name, item.ytyp_name))

            found_files = [f for f in _find_game_asset_files_batch(context, game_dir, assets) if f is not None]
            if not found_files:
                return {"CANCELLED"}

            any_skipped = len(found_files) < len(self.assets)

        # Outside of the operator logger, the import operator reports its own messages
        errors = _import_game_asset_files(found_files)
        for error in errors:
            self.report({"ERROR"}, error)

        if len(found_files) == 1:
            imported = f"'{found_files[0].asset}'"
        else:
            imported = f"{len(found_files)} assets"
        self.report(
            {"WARNING"} if errors or any_skipped else {"INFO"},
            f"Imported {imported} in {time.time() - start_time:.2f} seconds",
        )
        return {"FINISHED"}


@dataclass(slots=True)
class _EntityObjectsReplacement:
    """The game asset library objects linked to the entities of an archetype, to replace with the import of the
    archetype from the game installation."""

    asset_name: str
    ytyp_name: str
    objects: dict[Object, PropertyGroup | None] = field(default_factory=dict)
    """The library objects to replace, with the entity linked to them, `None` if not linked to an entity."""
    files: ArchetypeFiles | None = None
    """The game files of the archetype, `None` if not found or not needed."""
    model: Object | None = None
    """The model of the archetype, if reused from the scene instead of imported: an unused drawable of a drawable
    dictionary."""


def _collect_entity_objects_replacements(
    objects: Iterable[Object], all_entities: Iterable
) -> list[_EntityObjectsReplacement]:
    """Group the game asset library objects of `objects` by archetype, each with the entity of `all_entities` linked to
    it, so it links to the object that replaces it. Other objects are ignored.
    """
    replacements: dict[int, _EntityObjectsReplacement] = {}
    replacements_by_object: dict[Object, _EntityObjectsReplacement] = {}
    for obj in objects:
        if obj in replacements_by_object or (archetype_info := get_object_game_asset(obj)) is None:
            continue

        asset_name = remove_number_suffix(obj.name).lower()
        if archetype_info.type == "MLO":
            logger.warning(f"Importing interiors from game installation is not supported, skipping '{asset_name}'.")
            continue

        replacement = replacements.setdefault(
            name_to_hash(asset_name), _EntityObjectsReplacement(asset_name, archetype_info.ytyp)
        )
        replacement.objects[obj] = None
        replacements_by_object[obj] = replacement

    for entity in all_entities:
        obj = entity.linked_object
        if (replacement := replacements_by_object.get(obj, None)) is not None:
            replacement.objects[obj] = entity

    return list(replacements.values())


def _iter_all_entities(context) -> Iterator:
    """All the map and MLO entities in the scene."""
    from ...ymap_next.properties.map import get_maps

    if (maps := get_maps(context)) is not None:
        for group in maps.groups:
            yield from group.entities
    for ytyp in context.scene.ytyps:
        for archetype in ytyp.archetypes:
            yield from archetype.entities


def _find_unused_dictionary_drawables(context, replacements: Iterable[_EntityObjectsReplacement]):
    """Set the model of the replacements whose archetype is a drawable of a drawable dictionary in the scene that is not
    linked to any entity, so it is used instead of importing the drawable dictionary again."""
    replacements_by_name = {name_to_hash(r.asset_name): r for r in replacements}
    linked_objects = {e.linked_object for e in _iter_all_entities(context)}
    for obj in context.scene.objects:
        if (
            obj.sollum_type != SollumType.DRAWABLE
            or obj.parent is None
            or obj.parent.sollum_type != SollumType.DRAWABLE_DICTIONARY
            or obj in linked_objects
        ):
            continue

        replacement = replacements_by_name.get(name_to_hash(remove_number_suffix(obj.name)), None)
        if replacement is not None and replacement.model is None:
            replacement.model = obj


def _replace_entity_objects(
    replacements: Sequence[_EntityObjectsReplacement], new_objects: Sequence[Object]
) -> tuple[dict[Object, Object], list[Object]]:
    """Replace the library objects with the model of their archetype. The first library object of each archetype is
    replaced by the imported original object, and the rest by copies of it.

    Returns the replaced library objects mapped to the objects that replace them, and the objects to remove, the library
    objects.
    """
    from ...ydr.shader_materials import apply_tint_preview_index

    # The imported model of each archetype is the drawable or fragment with its name, at the root or in a drawable
    # dictionary
    imported_models = {}
    for obj in new_objects:
        if obj.sollum_type not in {SollumType.DRAWABLE, SollumType.FRAGMENT}:
            continue
        if obj.parent is not None and obj.parent.sollum_type != SollumType.DRAWABLE_DICTIONARY:
            continue
        imported_models.setdefault(name_to_hash(remove_number_suffix(obj.name)), obj)

    hierarchy = ObjectHierarchySnapshot.for_blend()
    objects_to_remove = []
    replaced_objects = {}
    for replacement in replacements:
        model = replacement.model
        if model is None:
            if replacement.files is None:
                continue

            model = imported_models.get(name_to_hash(replacement.asset_name), None)
            if model is None:
                logger.error(f"Could not find the imported model of '{replacement.asset_name}'.")
                continue

        model_objects = get_object_with_children_recursive(model, hierarchy)
        for i, (library_obj, entity) in enumerate(replacement.objects.items()):
            objects_to_remove.extend(get_object_with_children_recursive(library_obj, hierarchy))
            replacement_objects = model_objects if i == 0 else copy_object_hierarchy(model_objects)
            new_root = replacement_objects[0]
            _replace_object(library_obj, replacement_objects)
            if entity is not None:
                entity.linked_object = new_root
                if entity.tint_value != 0:
                    apply_tint_preview_index(new_root, entity.tint_value)
            replaced_objects[library_obj] = new_root

    return replaced_objects, list(set(objects_to_remove))


def _remove_free_number_suffixes(objects: Iterable[Object]):
    """Remove the `.001`-like suffix of the objects whose name without it is not used by any other object. The imported
    objects get the suffix because the library objects they replace had the same name until they were removed."""
    for obj in objects:
        name = remove_number_suffix(obj.name)
        if name == obj.name:
            continue

        # Linked objects don't count, they don't share names with the objects of this .blend
        existing = bpy.data.objects.get(name, None)
        if existing is None or existing.library is not None:
            obj.name = name


def _select_objects(context, selected_objects: set[Object], active_object: Object | None):
    # Not iterating `view_layer.objects`, the objects just linked to the scene are not in it until the view layer is
    # synced. `context.selected_objects` and `select_set` sync it
    for obj in context.selected_objects:
        if obj not in selected_objects:
            obj.select_set(False)
    for obj in selected_objects:
        try:
            obj.select_set(True)
        except RuntimeError:
            # Not in the view layer, e.g. in an excluded collection
            pass
    context.view_layer.objects.active = active_object


def _replace_object(old_obj: Object, new_objects: Sequence[Object]):
    """Put the hierarchy `new_objects` (root first) in place of `old_obj`: in the same collections, with the same parent
    and transform, and with the references to `old_obj`, such as the light effect constraints of MLO entities, changed
    to the new root. A drawable of a drawable dictionary stays in the dictionary, so it can still be exported, and only
    its transform is changed.
    """
    new_root = new_objects[0]
    collections = old_obj.users_collection
    for collection in collections:
        collection.objects.unlink(old_obj)

    if (parent := new_root.parent) is not None and parent.sollum_type == SollumType.DRAWABLE_DICTIONARY:
        parent_matrix = _unevaluated_matrix_world(parent) @ new_root.matrix_parent_inverse
        new_root.matrix_basis = parent_matrix.inverted_safe() @ _unevaluated_matrix_world(old_obj)
    else:
        for obj in new_objects:
            for collection in obj.users_collection:
                collection.objects.unlink(obj)
            for collection in collections:
                collection.objects.link(obj)

        new_root.parent = old_obj.parent
        new_root.matrix_parent_inverse = old_obj.matrix_parent_inverse.copy()
        new_root.matrix_basis = old_obj.matrix_basis.copy()

    old_obj.user_remap(new_root)


def _unevaluated_matrix_world(obj: Object) -> Matrix:
    """World matrix of `obj` from its parents and local transforms, ignoring constraints. Not `matrix_world`, it is not
    up to date in objects that are not evaluated, e.g. in hidden collections.
    """
    matrix = obj.matrix_basis
    while obj.parent is not None:
        matrix = obj.parent.matrix_basis @ obj.matrix_parent_inverse @ matrix
        obj = obj.parent
    return matrix


class GameAssetObjectsFromGameInstallationOperatorBase(GameDirectoryOperatorMixin):
    """Base of the operators that replace game asset library objects with the import of their archetypes from the game
    installation. Subclasses implement `get_objects` and `get_all_entities`.
    """

    bl_label = "Import from Game Installation"
    bl_options = {"UNDO"}

    no_objects_message = "No selected object is from a game asset library"

    @classmethod
    def get_objects(cls, context) -> Iterable[Object]:
        """The objects to replace."""
        raise NotImplementedError

    @classmethod
    def get_all_entities(cls, context) -> Iterable:
        """The entities to link to the objects that replace the objects they are linked to. An object is linked to at
        most one entity."""
        raise NotImplementedError

    @classmethod
    def poll(cls, context):
        if not IS_SZIO_NATIVE_AVAILABLE:
            cls.poll_message_set(PYMATERIA_REQUIRED_MSG)
            return False

        any_game_asset = False
        for obj in cls.get_objects(context):
            if (archetype_info := get_object_game_asset(obj)) is None:
                continue
            if archetype_info.type != "MLO":
                return True
            any_game_asset = True

        if any_game_asset:
            cls.poll_message_set("Importing interiors from game installation is not supported")
        else:
            cls.poll_message_set(cls.no_objects_message)
        return False

    def execute(self, context):
        start_time = time.time()
        with logger.use_operator_logger(self):
            if (game_dir := _validated_game_directory(self, context)) is None:
                return {"CANCELLED"}

            replacements = _collect_entity_objects_replacements(
                self.get_objects(context), self.get_all_entities(context)
            )
            if not replacements:
                logger.error(f"{self.no_objects_message}.")
                return {"CANCELLED"}

            _find_unused_dictionary_drawables(context, replacements)
            to_import = [r for r in replacements if r.model is None]
            found_files = _find_game_asset_files_batch(
                context, game_dir, ((r.asset_name, r.ytyp_name) for r in to_import)
            )
            for replacement, files in zip(to_import, found_files):
                replacement.files = files

            if all(replacement.model is None and replacement.files is None for replacement in replacements):
                return {"CANCELLED"}

        # Keep the object selection, with the new objects in place of the library objects they replace. Taken before the
        # import, which can change the active object
        selected_objects = set(context.selected_objects)
        active_object = context.view_layer.objects.active

        # Outside of the operator logger, the import operator reports its own messages
        objects_before = set(bpy.data.objects)
        errors = _import_game_asset_files(r.files for r in replacements if r.files is not None)
        new_objects = [obj for obj in bpy.data.objects if obj not in objects_before]
        for error in errors:
            self.report({"ERROR"}, error)

        with logger.use_operator_logger(self):
            replaced_objects, objects_to_remove = _replace_entity_objects(replacements, new_objects)
            _select_objects(
                context,
                {replaced_objects.get(obj, obj) for obj in selected_objects},
                replaced_objects.get(active_object, active_object),
            )
            bpy.data.batch_remove(objects_to_remove)
            _remove_free_number_suffixes(replaced_objects.values())

        num_replaced = len(replaced_objects)
        num_to_replace = sum(len(replacement.objects) for replacement in replacements)
        self.report(
            {"WARNING"} if errors or num_replaced < num_to_replace else {"INFO"},
            f"Replaced {num_replaced} object(s) in {time.time() - start_time:.2f} seconds",
        )
        return {"FINISHED"}


class EntityObjectsFromGameInstallationOperatorBase(GameAssetObjectsFromGameInstallationOperatorBase):
    """Base of the operators that replace the game asset library objects linked to the selected entities. Subclasses
    implement `get_entities`."""

    no_objects_message = "No selected entity is linked to an object from a game asset library"

    @classmethod
    def get_entities(cls, context) -> Sequence:
        """The selected entities."""
        raise NotImplementedError

    @classmethod
    def get_objects(cls, context):
        return (e.linked_object for e in cls.get_entities(context) if e.linked_object is not None)

    @classmethod
    def get_all_entities(cls, context):
        return cls.get_entities(context)


class SOLLUMZ_OT_import_objects_from_game_installation(GameAssetObjectsFromGameInstallationOperatorBase, Operator):
    bl_idname = "sollumz.import_objects_from_game_installation"
    bl_description = (
        "Replace the selected objects from the game asset library with the import of their models from the game "
        "installation with all their data (LODs, collisions, lights, etc.). The map and MLO entities linked to them "
        "are linked to the new objects"
    )

    @classmethod
    def get_objects(cls, context):
        objects = list(context.selected_objects)
        if (active := context.active_object) is not None and active not in objects:
            objects.append(active)
        return objects

    @classmethod
    def get_all_entities(cls, context):
        return _iter_all_entities(context)
