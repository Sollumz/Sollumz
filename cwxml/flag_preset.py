from .element import AttributeProperty, ElementTree, ListProperty, FlagsProperty


class FlagPresetsFile(ElementTree):
    tag_name = "FlagPresetsFile"

    def __init__(self):
        super().__init__()
        self.presets = Presets()


class FlagPreset(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = AttributeProperty("name", "NULL")
        self.flags1 = FlagsProperty("Flags1")
        self.flags2 = FlagsProperty("Flags2")


class Presets(ListProperty):
    list_type = FlagPreset
    tag_name = "Presets"
