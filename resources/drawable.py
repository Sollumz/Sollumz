from abc import ABC as AbstractClass, abstractclassmethod, abstractmethod, abstractstaticmethod
from xml.etree import ElementTree as ET
from .codewalker_xml import *
from .bound import Bounds, BoundsComposite
from enum import Enum

class YDR(ElementTree):
    tag_name = "Drawable"

    def __init__(self):
        super().__init__()
        self.drawable = Drawable()

class ParameterItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = AttributeProperty("Name", "") 
        self.type = AttributeProperty("Type", "") #ENUM?


class TextureNameElement(ElementTree):
    tag_name = "Name"

    def __init__(self):
        super().__init__()
        self.text = TextProperty("Name", "")


class TextureParameterItem(ParameterItem):
    
    def __init__(self):
        super().__init__()
        self.texture_name = TextureNameElement()


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


class ShaderItem(ElementTree):
    tag_name = 'Item'

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.filename = TextProperty("FileName", "")
        self.render_bucket = ValueProperty("RenderBucket", 0)
        self.parameters = ParametersListProperty()


class ShadersListProperty(ListProperty):
    list_type = ShaderItem

    def __init__(self, tag_name: str=None, value=None):
        super().__init__(tag_name=tag_name or 'Shaders', value=value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = ShadersListProperty()

        for child in element.iter():
            new.value.append(ShaderItem.from_xml(ShaderItem.from_xml(child)))

        return new


class TextureItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.unk32 = ValueProperty("Unk32", 0)
        self.usage = FlagsProperty("Usage")
        self.usage_flags = FlagsProperty("UsageFlags")
        self.extra_flags = ValueProperty("ExtraFlags", 0)
        self.width = ValueProperty("Width", 0)
        self.height = ValueProperty("Height", 0)
        self.miplevels = ValueProperty("MipLevels", 0)
        self.format = FlagsProperty("Format")
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

    def __init__(self, tag_name: str, value=None):
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


class VertexLayoutItem(ElementTree):
    tag_name = ""

    def __init__(self):
        super().__init__()


class VertexLayoutListProperty(ListProperty):
    list_type = VertexLayoutItem

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name=tag_name or "Layout", value=value or [])
        self.type = AttributeProperty("Type", "")


class VertexBufferProperty(ElementTree):
    tag_name = "VertexBuffer"
    
    def __init__(self):
        super().__init__()
        self.flags = ValueProperty("Flags", 0)
        self.layout = VertexLayoutListProperty()
        self.data = TextProperty("Data", "")


class IndexBufferProperty(ElementTree):
    tag_name = "IndexBuffer"

    def __init__(self):
        super().__init__()
        self.data = TextProperty("Data", "")

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

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name=tag_name or "DrawableModels", value=value or [])


class DrawableModelItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.render_mask = ValueProperty("RenderMask", 0)
        self.flags = ValueProperty("Flags", 0)
        self.has_skin = ValueProperty("Flags", 0) #0 = false, 1 = true
        self.bone_index = ValueProperty("BoneIndex", 0)
        self.unknown_1 = ValueProperty("Unknown1", 0)
        self.geometries = GeometriesListProperty()


class DrawableModelListProperty(ListProperty):
    list_type = DrawableModelItem

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name=tag_name or "DrawableModels", value=value or [])


class Drawable(ElementTree, AbstractClass):
    tag_name = "Drawable"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.bounding_sphere_center = VectorProperty("BoundingSphereCenter")
        self.bounding_sphere_radius = VectorProperty("BoundingSphereRadius")
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

