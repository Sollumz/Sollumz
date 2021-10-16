from .codewalker_xml import AttributeProperty, ElementTree, FlagsProperty

class FlagPreset(ElementTree):
    tag_name = 'FlagPreset'

    def __init__(self):
        super().__init__()
        self.name = AttributeProperty('name', 'NULL')
        self.flags1 = FlagsProperty('Flags1')
        self.flags2 = FlagsProperty('Flags2')