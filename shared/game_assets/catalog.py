"""Module for reading and writing Blender Catalog Definition Files from asset libraries.

See: https://docs.blender.org/manual/en/latest/files/asset_libraries/catalogs.html#catalog-definition-files
"""

import uuid
from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class Catalog:
    uuid: uuid.UUID
    path: str
    simple_name: str | None


@dataclass(slots=True)
class CatalogDefinitionFile:
    catalogs: list[Catalog]

    def get_catalog(self, path: str) -> Catalog | None:
        for c in self.catalogs:
            if c.path == path:
                return c

        return None

    def add_catalog(self, path: str) -> Catalog:
        if self.get_catalog(path) is not None:
            raise ValueError(f"Catalog with path '{path}' already exists")

        c = Catalog(uuid.uuid4(), path, path.replace("/", "-"))
        self.catalogs.append(c)
        return c

    def get_or_add_catalog(self, path: str) -> Catalog:
        return self.get_catalog(path) or self.add_catalog(path)

    def parse(self, filepath: Path):
        with filepath.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#") or line.startswith("VERSION"):
                    continue
                uid, path, simple_name = line.split(":", 2)
                self.catalogs.append(
                    Catalog(
                        uuid=uuid.UUID(uid),
                        path=path,
                        simple_name=simple_name or None,
                    )
                )

    def save(self, filepath: Path):
        with filepath.open("w", newline="", encoding="utf-8") as f:
            f.write("VERSION 1\n\n")
            catalogs_ordered = sorted(self.catalogs, key=lambda c: (c.path, c.uuid))
            for cat in catalogs_ordered:
                f.write(f"{cat.uuid}:{cat.path}:{cat.simple_name or ''}\n")
