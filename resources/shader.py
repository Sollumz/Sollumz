import xml.etree.ElementTree as ET
import os
from .codewalker_xml import *
from .drawable import ParametersListProperty, VertexLayoutListProperty
from ..tools.utils import *


class RenderBucketProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or "RenderBucket", value or [])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        items = element.text.strip().split(" ")
        for item in items:
            new.value.append(int(item))
        return items

    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.text = " ".join(self.value)


class FileNameListProperty(ListProperty):
    class FileNameItem(TextProperty):
        tag_name = "Item"

    list_type = FileNameItem
    tag_name = "FileName"


class LayoutListProperty(ListProperty):
    class Layout(VertexLayoutListProperty):
        tag_name = "Item"

    list_type = Layout
    tag_name = "Layout"


class Shader(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.filenames = FileNameListProperty()
        self.render_bucket = RenderBucketProperty()
        self.layouts = LayoutListProperty()
        self.parameters = ParametersListProperty("Parameters")

    @property
    def required_tangent(self):
        for layout in self.layouts:
            if "Tangent" in layout.value:
                return True
        return False

    def get_layout_from_semantic(self, vertex_semantic):
        for layout in self.layouts:
            if layout.vertex_semantic == vertex_semantic:
                return layout

        raise Exception(
            f"{vertex_semantic} layout is not found in the shader '{self.name}'")


class ShaderManager:
    shaderxml = os.path.join(os.path.dirname(__file__), "shaders.xml")
    shaders = {}

    @staticmethod
    def load_shaders():
        tree = ET.parse(ShaderManager.shaderxml)
        for node in tree.getroot():
            shader = Shader.from_xml(node)
            ShaderManager.shaders[shader.name] = shader

    @staticmethod
    def print_shader_collection():
        string = ""
        for shader in ShaderManager.shaders.values():
            name = shader.name.upper()
            ui_name = shader.name.replace("_", " ").upper()
            value = shader.name.lower()
            string += "ShaderMaterial(\"" + name + "\", \"" + \
                ui_name + "\", \"" + value + "\"),\n"

        print(string)

    @staticmethod
    def print_all_vertex_semantics():
        sems = []
        for shader in ShaderManager.shaders.values():
            for layout in shader.layouts:
                if layout.vertex_semantic in sems:
                    continue
                else:
                    sems.append(layout.vertex_semantic)

        for s in sems:
            print(s)

    @staticmethod
    def check_bumpmap_to_tangents():
        result = True

        for shader in ShaderManager.shaders.values():
            bumpsamp = False
            tangent = False
            for layout in shader.layouts:
                if "Tangent" in layout.value:
                    tangent = True
            for param in shader.parameters:
                if "BumpSampler" in param.name:
                    bumpsamp = True

            if bumpsamp != tangent:
                result = False
                print(
                    f"shader: {shader.name} bumpsamp: {str(bumpsamp)} tangent: {str(tangent)}")

        if result:
            print(f"{result} dexy is correct")
        else:
            print(f"{result} :(")

    @staticmethod
    def check_if_all_layouts_have_tangents():

        for shader in ShaderManager.shaders.values():
            result = True
            tangent = False
            if "Tangent" in shader.layouts[0].value:
                tangent = True
            for layout in shader.layouts:
                if "Tangent" in layout.value and tangent != True:
                    result = False
                    print(shader.name)
                    break

    @staticmethod
    def print_filename_enum():
        result = []
        for shader in ShaderManager.shaders.values():
            i = 0
            for fn in shader.filenames:
                if fn.value not in result:
                    result.append(f"{shader.name.upper()}{i} = \"{fn.value}\"")
                    i += 1
        print("\t\n".join(result))

    @staticmethod
    def print_all_params():
        result = []
        for shader in ShaderManager.shaders.values():
            for p in shader.parameters:
                if p.name not in result:
                    if p.name:
                        if "sampler" not in p.name.lower():
                            result.append(p.name)
        print(result)
        # print("\t\n".join(result))


ShaderManager.load_shaders()
