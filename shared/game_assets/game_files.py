import gzip
import hashlib
import os
import pickle
import re
from dataclasses import dataclass
from pathlib import Path
from szio import VPath
from szio.gta5 import ArchetypeAssetType, ArchetypeType, Asset, AssetMapTypes, try_load_asset
from szio.jenkhash import name_to_hash
from collections.abc import Sequence

ASSET_FILE_EXTENSIONS = (
    (".ytyp",),
    (".ydr",),
    (".yft",),
    (".ydd",),
    (".ytd",),
    (".ytyp", ".xml"),
    (".ydr", ".xml"),
    (".yft", ".xml"),
    (".ydd", ".xml"),
    (".ytd", ".xml"),
)
"""Suffix tuples of the asset files relevant to game asset libraries, in the format used as keys by
`GameFiles.read_asset_filelist`."""

FileIndexByName = dict[tuple[str, ...], dict[str, list[str]]]
"""Index of game files, as built by `GameFiles.read_asset_filelist`, in the form `{extensions: {name: [paths]}}`.

- `extensions`: suffix tuple of the files (e.g. `(".ydr",)` for binary drawables, `(".ydr", ".xml")` for their
  CWXML variants).
- `name`: file name without its extensions (e.g. `prop` for `prop.ydr`).
- `paths`: paths of every file with that name and extensions, which may be inside .rpf archives (e.g.
  `<game_dir>/update/update.rpf/.../prop.ydr`). When the game has a dlclist, they are sorted by DLC load order,
  so the last one is the highest-priority file that overrides the others.
"""

FileIndexByHash = dict[tuple[str, ...], dict[int, list[str]]]
"""Index of game files, as built by `GameFiles.index_by_name_hash`, in the form `{extensions: {name_hash: [paths]}}`.
Same as `FileIndexByName`, but keyed by the case-insensitive JOAAT hash (`name_to_hash`) of the file name.
"""


def is_game_installation(directory: str | os.PathLike | VPath) -> bool:
    """Whether `directory` is a GTA V installation directory, detected by the presence of the legacy or Enhanced
    executable."""
    directory = VPath(directory)
    return (directory / "GTA5.exe").is_file() or (directory / "GTA5_Enhanced.exe").is_file()


class GameFiles:
    """Discovers asset files within a directory tree rooted at `root_dir`, which may be a GTA V installation or any
    folder of extracted assets.
    """

    def __init__(self, root_dir: str | os.PathLike | VPath):
        self.root = VPath(root_dir)

    def is_game_installation(self) -> bool:
        """Whether the root is a GTA V game installation."""
        return is_game_installation(self.root)

    def read_dlclist(
        self, dlclist_subpath: str | os.PathLike | VPath = "update/update.rpf/common/data/dlclist.xml"
    ) -> dict[str, int] | None:
        """Parse dlclist.xml and return a mapping of DLC name to its load-order index, or `None` if the file is
        not found.
        """

        import io
        from xml.etree import ElementTree

        dlclist_path = self.root / dlclist_subpath
        if not dlclist_path.is_file():
            return None

        dlclist_str = dlclist_path.read_text(encoding="utf-8")
        with io.StringIO(dlclist_str) as s:
            dlclist_xml = ElementTree.parse(s)

        def _extract_dlc_name(dlc_path: str) -> str:
            if dlc_path.startswith("platform:/dlcpacks/"):
                dlc_path = dlc_path[len("platform:/dlcpacks/") :]
            elif dlc_path.startswith("dlcpacks:/"):
                dlc_path = dlc_path[len("dlcpacks:/") :]
            dlc_path = dlc_path.strip("/")
            return dlc_path

        dlclist = {
            _extract_dlc_name(item.text.lower()): idx for idx, item in enumerate(dlclist_xml.findall("./Paths/*"))
        }
        return dlclist

    def read_asset_filelist(self, file_extensions: Sequence[tuple[str, ...]] | None = None) -> FileIndexByName:
        """Recursively scan the root for asset files, returning them grouped as `{extensions: {file_stem: [paths]}}`.
        The key is a tuple of all path suffixes (including the leading dots), e.g. `prop.ydr` is keyed `(".ydr",)`
        and `prop.ydr.xml` is keyed `(".ydr", ".xml")`. Files with no extension are keyed `()`.
        Pass `file_extensions` as suffix tuples to keep only those types; they are matched exactly against the keys.
        When a dlclist is present, the paths for each file are sorted by DLC load order so the highest-priority
        (overriding) file comes last.
        """

        if file_extensions is not None:
            file_extensions = set(file_extensions)

        asset_files = {}
        for file_path in self.root.rglob("*"):
            if not file_path.is_file():
                continue

            file_suffixes = tuple(file_path.suffixes)
            if file_extensions is not None and file_suffixes not in file_extensions:
                continue

            file_name = file_path.name[: -sum(map(len, file_suffixes))] if file_suffixes else file_path.name

            asset_files.setdefault(file_suffixes, {}).setdefault(file_name, []).append(str(file_path))

        dlclist = self.read_dlclist()
        if dlclist is not None:
            DLC_PACK_REGEX = re.compile(r"update[\\/]x64[\\/]dlcpacks[\\/](.*?)[\\/]dlc[0-9]?.rpf")
            DLC_PATCH_REGEX = re.compile(r"update[\\/]update.rpf[\\/]dlc_patch[\\/](.*?)[\\/]")

            def _sort_by_dlc(path):
                path = str(path)
                if (dlc_match := DLC_PACK_REGEX.search(path)) and (
                    idx := dlclist.get(dlc_match.group(1).lower())
                ) is not None:
                    order = idx * 2
                elif (dlc_match := DLC_PATCH_REGEX.search(path)) and (
                    idx := dlclist.get(dlc_match.group(1).lower())
                ) is not None:
                    order = idx * 2 + 1
                else:
                    order = -1
                return order

            for _asset_suffixes, asset_files_for_ext in asset_files.items():
                for _asset_file, asset_file_paths in asset_files_for_ext.items():
                    asset_file_paths.sort(key=_sort_by_dlc)

        # import json
        # with open(r"D:\sources\Sollumz\asset_files.json", "w") as fp:
        #     json.dump(asset_files, fp, indent=2)

        return asset_files

    @staticmethod
    def index_by_name_hash(asset_files: FileIndexByName) -> FileIndexByHash:
        """Re-key the inner dicts of a `read_asset_filelist` result so each file is keyed by the JOAAT hash of
        its name instead of the name string. The outer extension-tuple keys are left unchanged.
        """

        result = {}
        for file_suffixes, files_by_name in asset_files.items():
            files_by_hash = {}
            for file_name, file_paths in files_by_name.items():
                files_by_hash.setdefault(name_to_hash(file_name), []).extend(file_paths)
            result[file_suffixes] = files_by_hash
        return result


def find_file_in_index(file_index: FileIndexByHash, name_hash: int, ext: str) -> VPath | None:
    """Look up a file by name hash and extension (e.g. `.ydr`) in an index built by `GameFiles.index_by_name_hash`.
    Binary files are preferred over their CWXML `.xml` variants. When there are multiple files with the same name,
    the last one, the highest-priority file in DLC load order, is returned.
    """
    paths = file_index.get((ext,), {}).get(name_hash, None) or file_index.get((ext, ".xml"), {}).get(name_hash, None)
    return VPath(paths[-1]) if paths else None


_game_file_index_cache: dict[str, FileIndexByHash] = {}

_GAME_FILE_INDEX_FORMAT_VERSION = 1
"""Version of the game file index saved to disk. Increment when format changes occur, so indices saved by older
versions are rebuilt.
"""


def get_game_file_index(game_dir: str | os.PathLike) -> FileIndexByHash:
    """Return the index of `ASSET_FILE_EXTENSIONS` files in `game_dir`, keyed by name hash. Building it requires
    walking through all the game archives, which is slow, so the index is cached for the rest of the session and saved
    to disk. Later sessions load it from disk, unless the game files changed since.
    """
    game_dir = os.path.abspath(game_dir)
    key = os.path.normcase(game_dir)
    file_index = _game_file_index_cache.get(key, None)
    if file_index is not None:
        return file_index

    import time
    from ... import logger

    start = time.time()
    header = _game_file_index_header(game_dir)
    cache_filename = f"{hashlib.blake2b(key.encode('utf-8'), digest_size=8).hexdigest()}.bin"
    cache_path = _game_file_index_cache_directory() / cache_filename
    file_index = _load_game_file_index(cache_path, header)
    if file_index is not None:
        logger.info(f"Loaded index of game files in '{game_dir}' in {time.time() - start:.1f} seconds")
    else:
        logger.info(f"Indexing game files in '{game_dir}'...")
        file_index = GameFiles.index_by_name_hash(GameFiles(game_dir).read_asset_filelist(ASSET_FILE_EXTENSIONS))
        logger.info(f"Indexed game files in {time.time() - start:.1f} seconds")
        _save_game_file_index(cache_path, header, file_index)

    _game_file_index_cache[key] = file_index
    return file_index


def clear_game_file_index_cache():
    """Clear the game file indices cached in memory. Indices saved to disk are kept, and only rebuilt when the game
    files change."""
    _game_file_index_cache.clear()


def _game_file_index_cache_directory() -> Path:
    from ...known_paths import data_directory_path

    return Path(data_directory_path()) / "game_files.cache"


def _game_file_index_header(game_dir: str) -> dict:
    """Describes what a saved index was built from. A saved index is only used if its header is equal to the current
    one."""
    # Size and modification time of the files the index is built from: the .rpf archives (changing anything inside an
    # archive, including its nested archives, changes the archive file) and loose asset files.
    endings = (".rpf",) + tuple("".join(suffixes) for suffixes in ASSET_FILE_EXTENSIONS)
    files = []
    for dirpath, dirnames, filenames in os.walk(game_dir):
        dirnames.sort()
        for filename in sorted(filenames):
            if filename.lower().endswith(endings):
                path = os.path.join(dirpath, filename)
                try:
                    st = os.stat(path)
                except OSError:
                    continue
                files.append((os.path.relpath(path, game_dir), st.st_size, st.st_mtime_ns))

    return {
        "format_version": _GAME_FILE_INDEX_FORMAT_VERSION,
        "file_extensions": ASSET_FILE_EXTENSIONS,
        "game_dir": game_dir,
        "files": files,
    }


def _load_game_file_index(cache_path: Path, header: dict) -> FileIndexByHash | None:
    """Load an index saved by `_save_game_file_index`, or `None` if there is none or it is outdated."""
    try:
        with gzip.open(cache_path, "rb") as f:
            if pickle.load(f) != header:
                return None
            return pickle.load(f)
    except Exception:
        # Missing, corrupted or written by an incompatible version, it will be rebuilt
        return None


def _save_game_file_index(cache_path: Path, header: dict, file_index: FileIndexByHash):
    from ... import logger

    # The header is written first, so loading can check it without reading the whole index
    tmp_path = cache_path.with_suffix(".tmp")
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        with gzip.open(tmp_path, "wb", compresslevel=6) as f:
            pickle.dump(header, f, protocol=pickle.HIGHEST_PROTOCOL)
            pickle.dump(file_index, f, protocol=pickle.HIGHEST_PROTOCOL)
        os.replace(tmp_path, cache_path)
    except OSError as e:
        logger.warning(f"Could not save the index of game files to '{cache_path}': {e}")
        try:
            os.remove(tmp_path)
        except OSError:
            pass


@dataclass(slots=True)
class ArchetypeFiles:
    asset: VPath | None
    """The archetype's main .ydr/.yft/.ydd file, or `None` if not found."""
    txd: VPath | None
    """The archetype's texture dictionary .ytd file, or `None` if not found or the archetype doesn't have one."""


def find_game_asset_files(
    game_dir: str | os.PathLike,
    asset_name: str,
    ytyp_name: str,
    *,
    ytyp_cache: dict[VPath, Asset | None] | None = None,
) -> ArchetypeFiles | None:
    """Find the game files a library asset was built from.

    Searches the game files for the `ytyp_name` .ytyp and resolves the archetype files from it.

    Pass the same `ytyp_cache` dictionary when finding the files of multiple assets so each .ytyp is only loaded once.

    Returns `None` if the asset files could not be found.
    """
    file_index = get_game_file_index(game_dir)
    if ytyp_cache is None:
        ytyp_cache = {}

    return _find_archetype_files(file_index, asset_name, ytyp_name, ytyp_cache)


def _find_archetype_files(
    file_index: FileIndexByHash,
    asset_name: str,
    ytyp_name: str,
    ytyp_cache: dict[VPath, Asset | None],
) -> ArchetypeFiles | None:
    """Find the main and texture dictionary files of the `asset_name` archetype from the `ytyp_name` .ytyp, in an
    index built by `GameFiles.index_by_name_hash`. Returns `None` if the .ytyp, the archetype or its drawable file is
    not found. MLO archetypes and unsupported asset types have no drawable file.
    """
    from ... import logger

    if (ytyp_path := find_file_in_index(file_index, name_to_hash(ytyp_name), ".ytyp")) is None:
        logger.warning(f"Could not find '{ytyp_name}.ytyp' in the game files.")
        return None

    if ytyp_path not in ytyp_cache:
        ytyp_cache[ytyp_path] = try_load_asset(ytyp_path)
    ytyp = ytyp_cache[ytyp_path]
    if not isinstance(ytyp, AssetMapTypes):
        logger.warning(f"Could not load '{ytyp_path}'.")
        return None

    asset_name_hash = name_to_hash(asset_name)
    arch = next((a for a in ytyp.archetypes if name_to_hash(a.name) == asset_name_hash), None)
    if arch is None:
        logger.warning(f"Could not find archetype '{asset_name}' in '{ytyp_path}'.")
        return None

    asset_file = None
    if arch.type != ArchetypeType.MLO:
        match arch.asset_type:
            case ArchetypeAssetType.DRAWABLE:
                asset_file = arch.asset_name, ".ydr"
            case ArchetypeAssetType.FRAGMENT:
                asset_file = arch.asset_name, ".yft"
            case ArchetypeAssetType.DRAWABLE_DICTIONARY:
                asset_file = arch.drawable_dictionary, ".ydd"

    if asset_file is None:
        return None

    asset_file_name, asset_ext = asset_file
    if (asset_path := find_file_in_index(file_index, name_to_hash(asset_file_name), asset_ext)) is None:
        logger.warning(f"Could not find '{asset_file_name}{asset_ext}' in the game files.")
        return None

    txd_path = None
    if arch.texture_dictionary:
        txd_path = find_file_in_index(file_index, name_to_hash(arch.texture_dictionary), ".ytd")

    return ArchetypeFiles(asset_path, txd_path)
