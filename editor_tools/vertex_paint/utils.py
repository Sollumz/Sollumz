from enum import Enum

CHANNEL_LABELS = ("Red", "Green", "Blue", "Alpha")
CHANNEL_ICONS = ("RGB_RED", "RGB_GREEN", "RGB_BLUE", "EVENT_A")


class Channel(Enum):
    RED = 0
    GREEN = 1
    BLUE = 2
    ALPHA = 3

    @property
    def label(self) -> str:
        return CHANNEL_LABELS[self.value]

    @property
    def icon(self) -> str:
        return CHANNEL_ICONS[self.value]


def attr_domain_size(mesh, attr) -> int:
    match attr.domain:
        case "POINT":
            return len(mesh.vertices)
        case "CORNER":
            return len(mesh.loops)
        case _:
            raise AssertionError(f"Unsupported domain '{attr.domain}'")
