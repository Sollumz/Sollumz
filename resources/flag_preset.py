from .codewalker_xml import ElementTree
from .bound import FlagsProperty

class FlagPreset(ElementTree):
    def __init__(self):
        super().__init__()
        self.flags1 = FlagsProperty('Flags1')
        self.flags2 = FlagsProperty('Flags2')