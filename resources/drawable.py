from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod, abstractstaticmethod
from xml.etree import ElementTree as ET
from enum import Enum
from .codewalker_xml import *
from Sollumz.tools.utils import *
from .bound import Bounds, BoundsComposite

class YDD:
    
    @staticmethod
    def from_xml_file(filepath):
        return DrawableDictionary.from_xml_file(filepath)

    @staticmethod
    def write_xml(drawable_dict, filepath):
        return drawable_dict.write_xml(filepath)

class YDR:
    
    @staticmethod
    def from_xml_file(filepath):
        return Drawable.from_xml_file(filepath)

    @staticmethod
    def write_xml(drawable, filepath):
        return drawable.write_xml(filepath)

class ParameterItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = AttributeProperty("name", "") 
        self.type = AttributeProperty("type", "") #ENUM?

class TextureParameterItem(ParameterItem):
    
    def __init__(self):
        super().__init__()
        self.texture_name = TextProperty("Name", "")

class ValueParameterItem(ParameterItem):
    
    def __init__(self):
        super().__init__()
        self.quaternion_x = AttributeProperty("x", 0)
        self.quaternion_y = AttributeProperty("y", 0)
        self.quaternion_z = AttributeProperty("z", 0)
        self.quaternion_w = AttributeProperty("w", 0)

class ParametersListProperty(ListProperty):
    list_type = ParameterItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Shaders', value=value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = ParametersListProperty()

        for child in element.iter():
            if 'type' in child.attrib:
                param_type = child.get('type')
                if(param_type == "Texture"):
                    new.value.append(TextureParameterItem.from_xml(child))
                if(param_type == "Vector"):
                    new.value.append(ValueParameterItem.from_xml(child))

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

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Shaders', value=value or [])

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

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "TextureDictionary", value=value or [])

class ShaderGroupProperty(ElementTree):
    tag_name = "ShaderGroup"

    def __init__(self):
        super().__init__()
        self.unknown_30 = ValueProperty("Unknown30", 0)
        self.shaders = ShadersListProperty()
        self.texture_dictionary = TextureDictionaryListProperty()

class BoneItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "") #make enum in the future with all of the specific bone names?
        self.tag = ValueProperty("Tag", 0)
        self.index = ValueProperty("Index", 0)
        self.parent_index = ValueProperty("ParentIndex", 0)
        self.sibling_index =ValueProperty("SiblingIndex", 0)
        self.flags = FlagsProperty("Flags")
        self.translation = VectorProperty("Translation")
        self.rotation = QuaternionProperty("Rotation")
        self.scale = VectorProperty("Scale")
        self.transform_unk = QuaternionProperty("TransformUnk")

class BonesListProperty(ListProperty):
    list_type = BoneItem

    def __init__(self, tag_name: str=None, value=None):
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

class IndexBufferProperty(ElementTree):
    tag_name = "IndexBuffer"

    def __init__(self):
        super().__init__()

class Vertex:

    def __init__(self):
        self.position = None
        self.blendweights = None
        self.blendindices = None
        self.colors0 = None
        self.colors1 = None
        self.texcoord0 = None
        self.texcoord1 = None
        self.texcoord2 = None
        self.texcoord3 = None
        self.texcoord4 = None
        self.texcoord5 = None
        self.texcoord6 = None
        self.texcoord7 = None
        self.tangent = None
        self.normal = None

    @staticmethod    
    def from_xml(layout, data):

        result = Vertex()

        for i in range(len(layout)):
            current_data = data[i].split()
            current_layout_key = layout[i].tag_name
            if(current_layout_key == "Position"):
                result.position = StringListToFloatList(current_data)
            elif(current_layout_key == "BlendWeights"):
                result.blendweights = StringListToIntList(current_data)
            elif(current_layout_key == "BlendIndices"):
                result.blendindices = StringListToIntList(current_data)
            elif(current_layout_key == "Colour0"):
                result.colors0 = StringListToFloatList(current_data)
            elif(current_layout_key == "Colour1"):
                result.colors1 = StringListToFloatList(current_data)
            elif(current_layout_key == "TexCoord0"):
                result.texcoord0 = StringListToFloatList(current_data)
            elif(current_layout_key == "TexCoord1"):
                result.texcoord1 = StringListToFloatList(current_data)
            elif(current_layout_key == "TexCoord2"):
                result.texcoord2 = StringListToFloatList(current_data)
            elif(current_layout_key == "TexCoord3"):
                result.texcoord3 = StringListToFloatList(current_data)
            elif(current_layout_key == "TexCoord4"):
                result.texcoord4 = StringListToFloatList(current_data)
            elif(current_layout_key == "TexCoord5"):
                result.texcoord5 = StringListToFloatList(current_data)
            elif(current_layout_key == "TexCoord6"):
                result.texcoord6 = StringListToFloatList(current_data)
            elif(current_layout_key == "TexCoord7"):
                result.texcoord7 = StringListToFloatList(current_data)
            elif(current_layout_key == "Tangent"):
                result.tangent = StringListToFloatList(current_data)
            elif(current_layout_key == "Normal"):
                result.normal = StringListToFloatList(current_data)

        return result

class VertexLayoutItem(ElementTree):
    tag_name = ""

    def __init__(self, tag_name = ""):
        super().__init__()
        self.tag_name = tag_name

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        new.tag_name = element.tag

        return new

class VertexLayoutListProperty(ListProperty):
    list_type = VertexLayoutItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "Layout", value=value or [])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls(element.tag)

        for child in element:
            new.value.append(new.list_type.from_xml(child))

        return new

    #only way I could figure out how to add an attribute to a list property, 
    #dont like how it is hard coded but its the only case we need it so maybe its fine?
    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.set("type", "GTAV1")
        for item in self.value:
            if isinstance(item, self.list_type):
                element.append(item.to_xml())
            else:
                raise TypeError(f"{type(self).__name__} can only hold objects of type '{self.list_type.__name__}', not '{type(item)}'")

        return element

class VertexBufferProperty(ElementTree):
    tag_name = "VertexBuffer"
    
    def __init__(self):
        super().__init__()
        self.flags = ValueProperty("Flags", 0)
        self.layout = VertexLayoutListProperty("Layout")
        self.data = TextProperty("Data", "")

    def data_to_vertices(self):
        vertices = []
        text = self.data.strip().split('\n')
        if len(text) > 0:
            for line in text:
                v = Vertex.from_xml(self.layout, line.strip().split(" " * 3))
                vertices.append(v)

        return vertices

class IndexBufferProperty(ElementTree):
    tag_name = "IndexBuffer"

    def __init__(self):
        super().__init__()
        self.data = TextProperty("Data", "")

    def data_to_indices(self):
        indices = []
        text = self.data.strip().replace("\n", "").split()
        i_buf = []
        for num in text:
            i_buf.append(int(num))

        if len(text) > 0:
            indices = [i_buf[i * 3:(i + 1) * 3] for i in range((len(i_buf) + 3 - 1) // 3 )] #split index buffer into 3s for each triangle

        return indices

class GeometryItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.shader_index = ValueProperty("ShaderIndex", 0)
        self.bounding_box_min = VectorProperty("BoundingBoxMin")
        self.bounding_box_max = VectorProperty("BoundingBoxMax")
        self.vertex_buffer = VertexBufferProperty()
        self.index_buffer = IndexBufferProperty()

class GeometriesListProperty(ListProperty):
    list_type = GeometryItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "DrawableModels", value=value or [])

class DrawableModelItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.render_mask = ValueProperty("RenderMask", 0)
        self.flags = ValueProperty("Flags", 0)
        self.has_skin = ValueProperty("HasSkin", 0) #0 = false, 1 = true
        self.bone_index = ValueProperty("BoneIndex", 0)
        self.unknown_1 = ValueProperty("Unknown1", 0)
        self.geometries = GeometriesListProperty("Geometries")

class DrawableModelListProperty(ListProperty):
    list_type = DrawableModelItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or "DrawableModels", value=value or [])

class Drawable(ElementTree, AbstractClass):
    tag_name = "Drawable"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.bounding_sphere_center = VectorProperty("BoundingSphereCenter")
        self.bounding_sphere_radius = ValueProperty("BoundingSphereRadius", 0)
        self.bounding_box_min = VectorProperty("BoundingBoxMin")
        self.bounding_box_max = VectorProperty("BoundingBoxMax")
        self.lod_dist_high = ValueProperty('LodDistHigh', 0) #9998?
        self.lod_dist_med= ValueProperty('LodDistMed', 0) #9998?
        self.lod_dist_low = ValueProperty('LodDistLow', 0) #9998?
        self.lod_dist_vlow = ValueProperty('LodDistVlow', 0) #9998?
        self.flags_high = ValueProperty('FlagsHigh', 0) 
        self.flags_med = ValueProperty('FlagsMed', 0) 
        self.flags_low = ValueProperty('FlagsLow', 0)  
        self.flags_vlow = ValueProperty('FlagsVlow', 0)
        self.unknown_9A = ValueProperty('Unknown9A', 0)

        self.shader_group = ShaderGroupProperty()
        self.skeleton = SkeletonProperty()
        self.bound = BoundsComposite() #is embedded collision always type of composite? have to check
        self.drawable_models_high = DrawableModelListProperty("DrawableModelsHigh")
        self.drawable_models_med = DrawableModelListProperty("DrawableModelsMed")
        self.drawable_models_low = DrawableModelListProperty("DrawableModelsLow")
        self.drawable_models_vlow = DrawableModelListProperty("DrawableModelsVlow")

class DrawableDictionary(ListProperty):
    list_type = Drawable

    def __init__(self, tag_name: str=None, value=None):
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
                raise TypeError(f"{type(self).__name__} can only hold objects of type '{self.list_type.__name__}', not '{type(item)}'")

        return element