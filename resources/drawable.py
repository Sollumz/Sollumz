from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod, abstractstaticmethod
from os import name
from xml.etree import ElementTree as ET
from .codewalker_xml import *
from Sollumz.tools.utils import *
from .bound import BoundsComposite
from collections import namedtuple


class YDD:

    file_extension = ".ydd.xml"

    @staticmethod
    def from_xml_file(filepath):
        return DrawableDictionary.from_xml_file(filepath)

    @staticmethod
    def write_xml(drawable_dict, filepath):
        return drawable_dict.write_xml(filepath)


class YDR:

    file_extension = ".ydr.xml"

    @staticmethod
    def from_xml_file(filepath):
        return Drawable.from_xml_file(filepath)

    @staticmethod
    def write_xml(drawable, filepath):
        return drawable.write_xml(filepath)


class TextureItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.unk32 = ValueProperty("Unk32", 0)
        self.usage = TextProperty("Usage")
        self.usage_flags = FlagsProperty("UsageFlags")
        self.extra_flags = ValueProperty("ExtraFlags", 0)
        self.width = ValueProperty("Width", 0)
        self.height = ValueProperty("Height", 0)
        self.miplevels = ValueProperty("MipLevels", 0)
        self.format = TextProperty("Format")
        self.filename = TextProperty("FileName", "")


class TextureDictionaryListProperty(ListProperty):
    list_type = TextureItem

    def __init__(self, tag_name: str = None, value=None):
        super().__init__(tag_name=tag_name or "TextureDictionary", value=value or [])


class ShaderParameter(ElementTree, AbstractClass):
    tag_name = "Item"

    @property
    @abstractmethod
    def type():
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.name = AttributeProperty("name")
        self.type = AttributeProperty("type", self.type)  # ENUM?


class TextureShaderParameter(ShaderParameter):
    type = 'Texture'

    def __init__(self):
        super().__init__()
        self.texture_name = TextProperty("Name", "")


class VectorShaderParameter(ShaderParameter):
    type = 'Vector'

    def __init__(self):
        super().__init__()
        self.x = AttributeProperty("x", 0)
        self.y = AttributeProperty("y", 0)
        self.z = AttributeProperty("z", 0)
        self.w = AttributeProperty("w", 0)


class ArrayShaderParameterProperty(ListProperty, ShaderParameter):
    type = 'Array'

    class Value(QuaternionProperty):
        tag_name = 'Value'

    list_type = Value

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name=tag_name or 'Item', value=value or [])


class ParametersListProperty(ListProperty):
    list_type = ShaderParameter

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name=tag_name or 'Shaders', value=value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = ParametersListProperty()

        for child in element.iter():
            if 'type' in child.attrib:
                param_type = child.get('type')
                if param_type == TextureShaderParameter.type:
                    new.value.append(TextureShaderParameter.from_xml(child))
                if param_type == VectorShaderParameter.type:
                    new.value.append(VectorShaderParameter.from_xml(child))
                if param_type == ArrayShaderParameterProperty.type:
                    new.value.append(
                        ArrayShaderParameterProperty.from_xml(child))

        return new


class ShaderItem(ElementTree):
    tag_name = 'Item'

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.filename = TextProperty("FileName", "")
        self.render_bucket = ValueProperty("RenderBucket", 0)
        self.parameters = ParametersListProperty("Parameters")


class ShadersListProperty(ListProperty):
    list_type = ShaderItem

    def __init__(self, tag_name: str = None, value=None):
        super().__init__(tag_name=tag_name or 'Shaders', value=value or [])


class ShaderGroupProperty(ElementTree):
    tag_name = "ShaderGroup"

    def __init__(self):
        super().__init__()
        self.unknown_30 = ValueProperty("Unknown30", 0)
        self.texture_dictionary = TextureDictionaryListProperty()
        self.shaders = ShadersListProperty()


class BoneItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        # make enum in the future with all of the specific bone names?
        self.name = TextProperty("Name", "")
        self.tag = ValueProperty("Tag", 0)
        self.index = ValueProperty("Index", 0)
        self.parent_index = ValueProperty("ParentIndex", 0)
        self.sibling_index = ValueProperty("SiblingIndex", 0)
        self.flags = FlagsProperty("Flags")
        self.translation = VectorProperty("Translation")
        self.rotation = QuaternionProperty("Rotation")
        self.scale = VectorProperty("Scale")
        self.transform_unk = QuaternionProperty("TransformUnk")


class BonesListProperty(ListProperty):
    list_type = BoneItem

    def __init__(self, tag_name: str = None, value=None):
        super().__init__(tag_name=tag_name or "Bones", value=value or [])


class SkeletonProperty(ElementTree):
    tag_name = "Skeleton"

    def __init__(self):
        super().__init__()
        self.unknown_1c = ValueProperty("Unknown1C", 0)
        self.unknown_50 = ValueProperty("Unknown50", 0)
        self.unknown_54 = ValueProperty("Unknown54", 0)
        self.unknown_58 = ValueProperty("Unknown58", 0)
        self.bones = BonesListProperty("Bones")


class VertexLayoutListProperty(ElementProperty):
    value_types = (list)
    tag_name = 'Layout'

    # Generate a namedtuple from a vertex layout
    @property
    def vertex_type(self):
        return namedtuple('Layout', [name.lower() for name in self.value])

    def __init__(self, tag_name=None):
        super().__init__(self.tag_name, [])
        self.type = 'GTAV1'

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        new.type = element.get('type')
        for child in element:
            new.value.append(child.tag)
        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.set('type', self.type)
        for item in self.value:
            element.append(ET.Element(item))
        return element


class VertexDataProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name=None):
        super().__init__(tag_name=tag_name or 'Data', value=[])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        text = element.text.strip().split('\n')
        if len(text) > 0:
            for line in text:
                items = line.strip().split("   ")
                vert = []
                for item in items:
                    words = item.strip().split(" ")
                    # Convert item to correct type
                    item = [get_str_type(word) for word in words]
                    vert.append(item)

                new.value.append(vert)

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        text = []
        for vertex in self.value:
            for property in vertex:
                text.append(' '.join([str(item)
                                      for item in property]) + '   ')
            text.append('\n')
        element.text = ''.join(text)

        return element


class VertexBuffer(ElementTree):
    tag_name = "VertexBuffer"

    def __init__(self):
        super().__init__()
        self.flags = ValueProperty("Flags", 0)
        self.layout = VertexLayoutListProperty()
        self.data = VertexDataProperty()
        self.data2 = VertexDataProperty('Data2')

    def get_vertex_type(self):
        return self.get_element('layout').vertex_type

    @classmethod
    def from_xml(cls: Element, element: ET.Element):
        new = super().from_xml(element)
        # Convert data to namedtuple matching the layout
        vert_type = new.get_vertex_type()
        new.data = list(map(lambda vert: vert_type(*vert), new.data))
        return new


class IndexDataProperty(ElementProperty):
    value_types = (int)

    def __init__(self):
        super().__init__(tag_name='Data', value=[])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        indices = element.text.strip().replace("\n", "").split()
        new.value = [int(i) for i in indices]

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        columns = 24
        text = []

        for index, vert_index in enumerate(self.value):
            text.append(str(vert_index))
            if index < len(self.value) - 1:
                text.append(' ')
            if index % columns == 0 and index > 0:
                text.append('\n')

        element.text = ''.join(text)

        return element


class IndexBuffer(ElementTree):
    tag_name = "IndexBuffer"

    def __init__(self):
        super().__init__()
        self.data = IndexDataProperty()


class GeometryItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.shader_index = ValueProperty("ShaderIndex", 0)
        self.bounding_box_min = VectorProperty("BoundingBoxMin")
        self.bounding_box_max = VectorProperty("BoundingBoxMax")
        self.vertex_buffer = VertexBuffer()
        self.index_buffer = IndexBuffer()


class GeometriesListProperty(ListProperty):
    list_type = GeometryItem

    def __init__(self, tag_name: str = None, value=None):
        super().__init__(tag_name=tag_name or "Geometries", value=value or [])


class DrawableModelItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.render_mask = ValueProperty("RenderMask", 0)
        self.flags = ValueProperty("Flags", 0)
        self.has_skin = ValueProperty("HasSkin", 0)  # 0 = false, 1 = true
        self.bone_index = ValueProperty("BoneIndex", 0)
        self.unknown_1 = ValueProperty("Unknown1", 0)
        self.geometries = GeometriesListProperty()


class DrawableModelListProperty(ListProperty):
    list_type = DrawableModelItem

    def __init__(self, tag_name: str = None, value=None):
        super().__init__(tag_name=tag_name or "DrawableModels", value=value or [])


class Drawable(ElementTree, AbstractClass):
    tag_name = "Drawable"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.matrix = TextProperty("Matrix")  # yft field
        self.bounding_sphere_center = VectorProperty("BoundingSphereCenter")
        self.bounding_sphere_radius = ValueProperty("BoundingSphereRadius", 0)
        self.bounding_box_min = VectorProperty("BoundingBoxMin")
        self.bounding_box_max = VectorProperty("BoundingBoxMax")
        self.lod_dist_high = ValueProperty('LodDistHigh', 0)  # 9998?
        self.lod_dist_med = ValueProperty('LodDistMed', 0)  # 9998?
        self.lod_dist_low = ValueProperty('LodDistLow', 0)  # 9998?
        self.lod_dist_vlow = ValueProperty('LodDistVlow', 0)  # 9998?
        self.flags_high = ValueProperty('FlagsHigh', 0)
        self.flags_med = ValueProperty('FlagsMed', 0)
        self.flags_low = ValueProperty('FlagsLow', 0)
        self.flags_vlow = ValueProperty('FlagsVlow', 0)
        self.unknown_9A = ValueProperty('Unknown9A', 0)

        self.shader_group = ShaderGroupProperty()
        self.skeleton = SkeletonProperty()
        # is embedded collision always type of composite? have to check
        self.bound = BoundsComposite()
        self.drawable_models_high = DrawableModelListProperty(
            "DrawableModelsHigh")
        self.drawable_models_med = DrawableModelListProperty(
            "DrawableModelsMedium")
        self.drawable_models_low = DrawableModelListProperty(
            "DrawableModelsLow")
        self.drawable_models_vlow = DrawableModelListProperty(
            "DrawableModelsVeryLow")


class DrawableDictionary(ListProperty):
    list_type = Drawable

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name=tag_name or "DrawableDictionary", value=value or [])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        new.tag_name = "Item"
        children = element.findall(new.tag_name)

        for child in children:
            new.value.append(new.list_type.from_xml(child))

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        for item in self.value:
            if isinstance(item, self.list_type):
                item.tag_name = "Item"
                element.append(item.to_xml())
            else:
                raise TypeError(
                    f"{type(self).__name__} can only hold objects of type '{self.list_type.__name__}', not '{type(item)}'")

        return element
