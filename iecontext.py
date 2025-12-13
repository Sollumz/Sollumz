import contextlib
import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from collections.abc import Sequence
from szio.gta5 import Asset, AssetFormat, AssetTarget, save_asset
from .ydr.vertex_buffer_builder_domain import VBBuilderDomain


@dataclass(slots=True, frozen=True)
class ImportSettings:
    import_as_asset: bool
    """Import to the asset library."""
    split_by_group: bool
    """Split each drawable model by vertex group."""
    mlo_instance_entities: bool
    """Instance MLO entities when importing a YTYP."""
    import_external_skeleton: bool
    """Look for a YFT to use as skeleton when importing a YDD."""
    frag_import_vehicle_windows: bool = False
    """Whether to import vehicle windows when importing a YFT."""


@dataclass(slots=True, frozen=True)
class ImportContext:
    """Context of an import operation."""

    asset_name: str
    directory: Path
    settings: ImportSettings


@dataclass(slots=True, frozen=True)
class ExportBundle:
    """Result of an export operation.
    Any output file/asset should be stored in the bundle instead of writing it to disk directly.
    """

    asset_name: str
    main_asset: Asset | None
    """Main asset of the export operation."""

    secondary_assets: tuple[tuple[str, Asset], ...]
    """Additional assets exported along with the main asset, e.g. _hi.yft or .yld. Tuple of tuples like (suffix, asset)."""

    files_to_copy: tuple[str | os.PathLike]
    """Files to copy to a folder with same name as the asset, generally embedded textures."""

    def save(self, directory: Path):
        """Writes the whole bundle to disk at the specified directory."""

        from .meta import sollumz_version

        tool_metadata = "Sollumz", sollumz_version()

        gen8_directory = directory / "gen8"
        gen9_directory = directory / "gen9"
        main_asset = self.main_asset
        save_asset(main_asset, directory, self.asset_name, tool_metadata, gen8_directory, gen9_directory)
        for suffix, asset in self.secondary_assets:
            save_asset(asset, directory, self.asset_name + suffix, tool_metadata, gen8_directory, gen9_directory)

        do_copy_files = self.files_to_copy and (
            # We only use files_to_copy for embedded textures, which are only really needed for CWXML. Initially, these
            # were always copied but users requested that this not be done for native format.
            # If we start using files_to_copy for something else, we will need to rework this.
            main_asset.ASSET_FORMAT == AssetFormat.CWXML
            or (
                main_asset.ASSET_FORMAT == AssetFormat.MULTI_TARGET and AssetFormat.CWXML in main_asset.target_formats()
            )
        )

        if do_copy_files:
            if main_asset.ASSET_FORMAT == AssetFormat.MULTI_TARGET and len(main_asset.target_versions()) > 1:
                output_dirs = (gen8_directory, gen9_directory)
            else:
                output_dirs = (directory,)

            for d in output_dirs:
                res_directory = d / self.asset_name
                for file in self.files_to_copy:
                    if os.path.isfile(file):
                        res_directory.mkdir(exist_ok=True)
                        dst_file = res_directory / os.path.basename(file)
                        # check if paths are the same because if they are, no need to copy (and would throw an error otherwise)
                        if not dst_file.exists() or not dst_file.samefile(file):
                            shutil.copy(file, dst_file)

    def is_valid(self) -> bool:
        """Checks whether the export operation was successful."""
        return self.main_asset is not None

    def __bool__(self):
        return self.is_valid()


@dataclass(slots=True)
class ExportSettings:
    targets: tuple[AssetTarget, ...]
    """Target formats to export."""
    apply_transforms: bool = False
    exclude_skeleton: bool = False
    mesh_domain: VBBuilderDomain = VBBuilderDomain.FACE_CORNER


@dataclass(slots=True, frozen=True)
class ExportContext:
    """Context of an export operation."""

    asset_name: str
    settings: ExportSettings

    def make_bundle(
        self,
        main_asset: Asset | None,
        /,
        *secondary_assets: tuple[str, Asset | None],
        files_to_copy: Sequence[str | os.PathLike] = (),
    ) -> ExportBundle:
        """Creates an `ExportBundle` from the given assets and optional files.

        Args:
            main_asset: The primary asset produced during export. Can be None if export failed.
            secondary_assets: Optional secondary assets represented as (suffix, asset) pairs. Only non-None assets will
                be included in the bundle.
            files_to_copy: Additional files to copy into a subdirectory named after the asset, typically used for
                embedded resources like textures.
        """
        return ExportBundle(
            self.asset_name,
            main_asset,
            tuple(s for s in secondary_assets if s[1] is not None),
            tuple(files_to_copy),
        )


g_import_context: ImportContext | None = None
g_export_context: ExportContext | None = None


def import_context() -> ImportContext:
    """Gets the current import context. Raises an error if not in import context."""
    if g_import_context is None:
        raise RuntimeError(
            "No import context! Make sure to use `import_context_scope` before calling import functions."
        )
    return g_import_context


@contextlib.contextmanager
def import_context_scope(ctx: ImportContext):
    """Starts an import context. Returns a context manager."""
    global g_import_context
    if g_import_context is not None:
        raise RuntimeError("Already in import context!")
    g_import_context = ctx
    try:
        yield
    finally:
        g_import_context = None


def export_context() -> ExportContext:
    """Gets the current export context. Raises an error if not in export context."""
    if g_export_context is None:
        raise RuntimeError(
            "No export context! Make sure to use `export_context_scope` before calling import functions."
        )
    return g_export_context


@contextlib.contextmanager
def export_context_scope(ctx: ExportContext):
    """Starts an export context. Returns a context manager."""
    global g_export_context
    if g_export_context is not None:
        raise RuntimeError("Already in export context!")
    g_export_context = ctx
    try:
        yield
    finally:
        g_export_context = None
