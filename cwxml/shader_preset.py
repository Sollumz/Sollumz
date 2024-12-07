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
        self.x = AttributeProperty("x")
        self.y = AttributeProperty("y")
        self.z = AttributeProperty("z")
        self.w = AttributeProperty("w")
        self.texture = AttributeProperty("texture")


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
