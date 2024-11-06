from .element import ListProperty, AttributeProperty, ElementTree


class ShaderPresetsFile(ElementTree):
    tag_name = "ShaderPresetsFile"

    def __init__(self):
        super().__init__()
        self.presets = ShaderPresetList()


class ShaderPresetParam(ElementTree):
    tag_name = "Param"

    def __init__(self):
        self.name = AttributeProperty("name")
        self.x = AttributeProperty("x", 0.0)
        self.y = AttributeProperty("y", 0.0)
        self.z = AttributeProperty("z", 0.0)
        self.w = AttributeProperty("w", 0.0)


class ShaderPresetParamList(ListProperty):
    list_type = ShaderPresetParam
    tag_name = "Params"
    item_tag_name = "Item"


class ShaderPreset(ElementTree):
    tag_name = "ShaderPreset"

    def __init__(self):
        self.name = AttributeProperty("name")
        self.params = ShaderPresetParamList()


class ShaderPresetList(ListProperty):
    list_type = ShaderPreset
    tag_name = "ShaderPresets"
    item_tag_name = "Item"
