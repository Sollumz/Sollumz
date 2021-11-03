import xml.etree.ElementTree as ET
import os
from .codewalker_xml import *
from .drawable import ParametersListProperty, VertexLayoutListProperty
from ..tools.utils import *


class RenderBucketProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'RenderBucket', value or [])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        items = element.text.strip().split(' ')
        for item in items:
            new.value.append(int(item))
        return items

    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.text = ' '.join(self.value)


class FileNameListProperty(ListProperty):
    class Item(TextProperty):
        tag_name = 'Item'

    list_type = Item
    tag_name = "FileName"


class LayoutListProperty(ListProperty):
    class Layout(VertexLayoutListProperty):
        tag_name = 'Item'

    list_type = Layout
    tag_name = "Layout"


class Shader(ElementTree):
    tag_name = 'Item'

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.filename = FileNameListProperty
        self.render_bucket = RenderBucketProperty()
        self.layouts = LayoutListProperty()
        self.parameters = ParametersListProperty("Parameters")


class ShaderManager:
    shaderxml = os.path.join(os.path.dirname(__file__), 'Shaders.xml')
    shaders = {}

    @staticmethod
    def load_shaders():
        tree = ET.parse(ShaderManager.shaderxml)
        for node in tree.getroot():
            shader = Shader.from_xml(node)
            ShaderManager.shaders[shader.name] = shader

    def print_shader_collection(self):
        string = ""
        for shader in self.shaders.values():
            name = shader.name.upper()
            ui_name = shader.name.replace("_", " ").upper()
            value = shader.name.lower()
            string += "ShaderMaterial(\"" + name + "\", \"" + \
                ui_name + "\", \"" + value + "\"),\n"

        print(string)


ShaderManager.load_shaders()
