import os
import re
from szio import VPath
from szio.jenkhash import name_to_hash
from collections.abc import Sequence


class GameFiles:
    """Discovers asset files within a directory tree rooted at `root_dir`, which may be a GTA V installation or any
    folder of extracted assets.
    """

    def __init__(self, root_dir: str | os.PathLike | VPath):
        self.root = VPath(root_dir)

    def is_game_installation(self) -> bool:
        """Whether the root is a GTA V game installation, detected by the presence of the legacy or Enhanced
        executable."""
        return (self.root / "GTA5.exe").is_file() or (self.root / "GTA5_Enhanced.exe").is_file()

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

    def read_asset_filelist(
        self, file_extensions: Sequence[tuple[str, ...]] | None = None
    ) -> dict[tuple[str, ...], dict[str, list[str]]]:
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
                if dlc_match := DLC_PACK_REGEX.search(path):
                    dlc = dlc_match.group(1).lower()
                    order = dlclist[dlc] * 2
                elif dlc_match := DLC_PATCH_REGEX.search(path):
                    dlc = dlc_match.group(1).lower()
                    order = dlclist[dlc] * 2 + 1
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
    def index_by_name_hash(
        asset_files: dict[tuple[str, ...], dict[str, list[str]]],
    ) -> dict[tuple[str, ...], dict[int, list[str]]]:
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
