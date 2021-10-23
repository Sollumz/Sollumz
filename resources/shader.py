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

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or 'FileName', value=value or [])


class LayoutListProperty(ListProperty):
    class Layout(VertexLayoutListProperty):
        tag_name = 'Item'

    list_type = Layout

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name=tag_name or 'Layout', value=[])


class Shader(ElementTree):
    tag_name = 'Item'

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.filename = FileNameListProperty
        self.render_bucket = RenderBucketProperty()
        self.layouts = LayoutListProperty()
        self.parameters = ParametersListProperty("Parameters")


SHADERS = {}
path = os.path.join(os.path.dirname(__file__), 'Shaders.xml')
tree = ET.parse(path)

for node in tree.getroot():
    shader = Shader.from_xml(node)
    SHADERS[shader.name] = shader
