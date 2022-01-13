from abc import ABC as AbstractClass, abstractmethod
from xml.etree import ElementTree as ET
from .codewalker_xml import *
from ..tools.utils import *
from .bound import *
from collections import namedtuple
from collections.abc import MutableSequence
from enum import Enum


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
    tag_name = "TextureDictionary"


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
        self.texture_name = TextProperty("Name")


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
    tag_name = "Item"


class ParametersListProperty(ListProperty):
    list_type = ShaderParameter
    tag_name = "Parameters"

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
        self.parameters = ParametersListProperty()


class ShadersListProperty(ListProperty):
    list_type = ShaderItem
    tag_name = "Shaders"


class ShaderGroupProperty(ElementTree):
    tag_name = "ShaderGroup"

    def __init__(self):
        super().__init__()
        self.unknown_30 = ValueProperty("Unknown30", 0)
        self.texture_dictionary = TextureDictionaryListProperty()
        self.shaders = ShadersListProperty()


class BoneIDProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str = "BoneIDs", value=None):
        super().__init__(tag_name, value or [])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        if element.text:
            txt = element.text.split(", ")
            new.value = []
            for id in txt:
                new.value.append(int(id))
        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.text = ", ".join([str(id) for id in self.value])
        return element


class BoneItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        # make enum in the future with all of the specific bone names?
        self.name = TextProperty("Name", "")
        self.tag = ValueProperty("Tag", 0)
        self.index = ValueProperty("Index", 0)
        # by default if a bone don't have parent or sibling there should be -1 instead of 0
        self.parent_index = ValueProperty("ParentIndex", -1)
        self.sibling_index = ValueProperty("SiblingIndex", -1)
        self.flags = FlagsProperty("Flags")
        self.translation = VectorProperty("Translation")
        self.rotation = QuaternionProperty("Rotation")
        self.scale = VectorProperty("Scale")
        self.transform_unk = QuaternionProperty("TransformUnk")


class BonesListProperty(ListProperty):
    list_type = BoneItem
    tag_name = "Bones"


class SkeletonProperty(ElementTree):
    tag_name = "Skeleton"

    def __init__(self):
        super().__init__()
        # copied from player_zero.yft
        # what do the following 4 unks mean and what are they for still remain unknown
        # before we've been using 0 for default value
        # but it turns out that if unk50 and unk54 are 0 it would just crash the game in some cases, e.g. modifying the yft of a streamedped, player_zero.yft for example
        # as we don't know how to calc all those unks we should use a hacky default value working in most if not all cases, so I replace 0 with the stuff from player_zero.yft
        # unknown_1c is either 0 or 16777216, the latter in most cases
        # oiv seems to get unknown_50 and unknown_54 correct somehow
        # unknown_58 is DataCRC in gims, oiv doesn't seem to calc it correctly so they leave it for user to edit this

        # UPDATE
        # from: NcProductions and ArthurLopes
        # to my knowledge, having two addon peds with the same unknown 1C, 50, 54 and 58 value will cause one of them to be messed up when spawned together. for example, first add-on will spawn without problem, the second will have the bones messed up. 
        # fixing this issue is simple by changing the value like you mentioned.
        self.unknown_1c = ValueProperty("Unknown1C", 16777216)
        self.unknown_50 = ValueProperty("Unknown50", 567032952)
        self.unknown_54 = ValueProperty("Unknown54", 2134582703)
        self.unknown_58 = ValueProperty("Unknown58", 2503907467)
        self.bones = BonesListProperty("Bones")


class RotationLimitItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.bone_id = ValueProperty("BoneId", 0)
        self.unk_a = ValueProperty("UnknownA", 0)
        self.min = VectorProperty("Min")
        self.max = VectorProperty("Max")


class RotationLimitsListProperty(ListProperty):
    list_type = RotationLimitItem
    tag_name = "RotationLimits"


class JointsProperty(ElementTree):
    tag_name = "Joints"

    def __init__(self):
        super().__init__()
        # there should be more joint types than RotationLimits
        self.rotation_limits = RotationLimitsListProperty("RotationLimits")


class LightItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.position = VectorProperty("Position")
        self.color = ColorProperty("Colour")
        self.flashiness = ValueProperty("Flashiness")
        self.intensity = ValueProperty("Intensity")
        self.flags = ValueProperty("Flags")
        self.bone_id = ValueProperty("BoneId")
        self.type = TextProperty("Type")
        self.group_id = ValueProperty("GroupId")
        self.time_flags = ValueProperty("TimeFlags")
        self.falloff = ValueProperty("Falloff")
        self.falloff_exponent = ValueProperty("FalloffExponent")
        self.culling_plane_normal = VectorProperty("CullingPlaneNormal")
        self.culling_plane_offset = ValueProperty("CullingPlaneOffset")
        self.unknown_45 = ValueProperty("Unknown45")
        self.unknown_46 = ValueProperty("Unknown46")
        self.volume_intensity = ValueProperty("VolumeIntensity")
        self.volume_size_scale = ValueProperty("VolumeSizeScale")
        self.volume_outer_color = ColorProperty("VolumeOuterColour")
        self.light_hash = ValueProperty("LightHash")
        self.volume_outer_intensity = ValueProperty("VolumeOuterIntensity")
        self.corona_size = ValueProperty("CoronaSize")
        self.volume_outer_exponent = ValueProperty("VolumeOuterExponent")
        self.light_fade_distance = ValueProperty("LightFadeDistance")
        self.shadow_fade_distance = ValueProperty("ShadowFadeDistance")
        self.specular_fade_distance = ValueProperty("SpecularFadeDistance")
        self.volumetric_fade_distance = ValueProperty("VolumetricFadeDistance")
        self.shadow_near_clip = ValueProperty("ShadowNearClip")
        self.corona_intensity = ValueProperty("CoronaIntensity")
        self.corona_z_bias = ValueProperty("CoronaZBias")
        self.direction = VectorProperty("Direction")
        self.tangent = VectorProperty("Tangent")
        self.cone_inner_angle = ValueProperty("ConeInnerAngle")
        self.cone_outer_angle = ValueProperty("ConeOuterAngle")
        self.extent = VectorProperty("Extent")
        self.projected_texture_hash = TextProperty("ProjectedTextureHash")


class LightsProperty(ListProperty):
    list_type = LightItem
    tag_name = "Lights"


class VertexSemantic(str, Enum):
    position = "P"
    blend_weight = "B"
    blend_index = "B"
    normal = "N"
    color = "C"
    texcoord = "T"
    tangent = "T"


class VertexLayoutListProperty(ElementProperty):
    value_types = (list)
    tag_name = 'Layout'

    # Generate a namedtuple from a vertex layout
    @ property
    def vertex_type(self):
        return namedtuple('Vertex', [name.lower() for name in self.value])

    @ property
    def pretty_vertex_semantic(self):
        result = []
        vgs = False
        cidx = 0
        tidx = 0
        for item in self.value:
            semantic = item
            if "colour" in item.lower():
                cidx += 1
                continue
            elif "texcoord" in item.lower():
                tidx += 1
                continue
            elif "blend" in item.lower():
                if not vgs:
                    semantic = "Vertex Group"
                    vgs = True
                else:
                    continue
            result.append(semantic)
        if cidx != 0:
            result.append(f"{cidx} Color Layer{'s' if cidx > 1 else ''}")
        if tidx != 0:
            result.append(f"{tidx} UV Layer{'s' if tidx > 1 else ''}")
        return ", ".join(result)

    @ property
    def vertex_semantic(self):
        return "".join([item[0] for item in self.value])

    def __init__(self, tag_name=None):
        super().__init__(self.tag_name, [])
        self.type = 'GTAV1'

    @ classmethod
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

    @ classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        if not element.text:
            return new

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
        if len(self.value) < 1:
            return None

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

    def get_data(self):
        if len(self.data) > 0:
            return self.data
        else:
            return self.data2

    def get_vertex_type(self):
        return self.get_element('layout').vertex_type

    @ classmethod
    def from_xml(cls: Element, element: ET.Element):
        new = super().from_xml(element)
        # Convert data to namedtuple matching the layout
        vert_type = new.get_vertex_type()
        new.data = list(map(lambda vert: vert_type(*vert), new.data))
        new.data2 = list(map(lambda vert: vert_type(*vert), new.data2))
        return new


class IndexDataProperty(ElementProperty):
    value_types = (int)

    def __init__(self):
        super().__init__(tag_name='Data', value=[])

    @ classmethod
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
            if (index + 1) % columns == 0:
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
        self.bone_ids = BoneIDProperty()
        self.vertex_buffer = VertexBuffer()
        self.index_buffer = IndexBuffer()


class GeometriesListProperty(ListProperty):
    list_type = GeometryItem
    tag_name = "Geometries"


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
    tag_name = "DrawableModels"


class Drawable(ElementTree, AbstractClass):
    tag_name = "Drawable"

    @ property
    def all_models(self):
        return self.drawable_models_high + self.drawable_models_med + self.drawable_models_low + self.drawable_models_vlow

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.bounding_sphere_center = VectorProperty("BoundingSphereCenter")
        self.bounding_sphere_radius = ValueProperty("BoundingSphereRadius")
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
        self.joints = JointsProperty()
        # is embedded collision always type of composite? have to check
        self.drawable_models_high = DrawableModelListProperty(
            "DrawableModelsHigh")
        self.drawable_models_med = DrawableModelListProperty(
            "DrawableModelsMedium")
        self.drawable_models_low = DrawableModelListProperty(
            "DrawableModelsLow")
        self.drawable_models_vlow = DrawableModelListProperty(
            "DrawableModelsVeryLow")
        self.lights = LightsProperty()
        self.bounds = []

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = super().from_xml(element)
        bounds = element.findall("Bounds")
        for child in bounds:
            bound_type = child.get("type")
            bound = None
            if bound_type == "Composite":
                bound = BoundsComposite.from_xml(child)
            elif bound_type == "Box":
                bound = BoundBox.from_xml(child)
            elif bound_type == "Sphere":
                bound = BoundSphere.from_xml(child)
            elif bound_type == "Capsule":
                bound = BoundCapsule.from_xml(child)
            elif bound_type == "Cylinder":
                bound = BoundCylinder.from_xml(child)
            elif bound_type == "Disc":
                bound = BoundDisc.from_xml(child)
            elif bound_type == "Cloth":
                bound = BoundCloth.from_xml(child)
            elif bound_type == "Geometry":
                bound = BoundGeometry.from_xml(child)
            elif bound_type == "GeometryBVH":
                bound = BoundGeometryBVH.from_xml(child)

            if bound:
                bound.tag_name = "Bounds"
                new.bounds.append(bound)

        return new

    def to_xml(self):
        element = super().to_xml()
        for bound in self.bounds:
            bound.tag_name = "Bounds"
            element.append(bound.to_xml())
        return element


class DrawableDictionary(MutableSequence, Element):
    tag_name = "DrawableDictionary"

    def __init__(self, value=None):
        super().__init__()
        self._value = value or []

    def __getitem__(self, name):
        return self._value[name]

    def __setitem__(self, key, value):
        self._value[key] = value

    def __delitem__(self, key):
        del self._value[key]

    def __iter__(self):
        return iter(self._value)

    def __len__(self):
        return len(self._value)

    def insert(self, index, value):
        self._value.insert(index, value)

    def sort(self, key):
        self._value.sort(key=key)

    @ classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        new.tag_name = "Item"
        children = element.findall(new.tag_name)

        for child in children:
            print(child)
            drawable = Drawable.from_xml(child)
            new.append(drawable)

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        for drawable in self._value:
            if isinstance(drawable, Drawable):
                drawable.tag_name = "Item"
                element.append(drawable.to_xml())
            else:
                raise TypeError(
                    f"{type(self).__name__}s can only hold '{Drawable.__name__}' objects, not '{type(drawable)}'!")

        return element
