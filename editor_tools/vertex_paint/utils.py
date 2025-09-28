from enum import Enum

from ...icons import icon

CHANNEL_LABELS = ("Red", "Green", "Blue", "Alpha")
CHANNEL_ICONS = ("RGBA_RED", "RGBA_GREEN", "RGBA_BLUE", "RGBA_ALPHA")


class Channel(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2
    ALPHA = 3

    @property
    def label(self) -> str:
        return CHANNEL_LABELS[self.value]

    @property
    def icon(self) -> int:
        return icon(CHANNEL_ICONS[self.value])


def attr_domain_size(mesh, attr) -> int:
    match attr.domain:
        case "POINT":
            return len(mesh.vertices)
        case "CORNER":
            return len(mesh.loops)
        case _:
            raise AssertionError(f"Unsupported domain '{attr.domain}'")
