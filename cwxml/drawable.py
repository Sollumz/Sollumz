import io
import os
from mathutils import Matrix
import numpy as np
from numpy.typing import NDArray
from ..tools.utils import np_arr_to_str
from typing import Optional
from abc import ABC as AbstractClass, abstractmethod
from xml.etree import ElementTree as ET
from .element import (
    AttributeProperty,
    FlagsProperty,
    Element,
    ColorProperty,
    ElementTree,
    ElementProperty,
    ListProperty,
    QuaternionProperty,
    TextProperty,
    ValueProperty,
    VectorProperty,
    Vector4Property,
    MatrixProperty
)
from .bound import (
    BoundBox,
    BoundCapsule,
    BoundPlane,
    BoundComposite,
    BoundCylinder,
    BoundDisc,
    BoundGeometry,
    BoundGeometryBVH,
    BoundSphere
)
from collections.abc import MutableSequence


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


class Texture(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.unk32 = ValueProperty("Unk32", 0)
        self.usage = TextProperty("Usage", "UNKNOWN")
        self.usage_flags = FlagsProperty("UsageFlags")
        self.extra_flags = ValueProperty("ExtraFlags", 0)
        self.width = ValueProperty("Width", 0)
        self.height = ValueProperty("Height", 0)
        self.miplevels = ValueProperty("MipLevels", 0)
        self.format = TextProperty("Format", "D3DFMT_DXT1")
        self.filename = TextProperty("FileName", "")


class TextureDictionaryList(ListProperty):
    list_type = Texture
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
        self.type = AttributeProperty("type", self.type)


class TextureShaderParameter(ShaderParameter):
    type = "Texture"

    def __init__(self):
        super().__init__()
        self.texture_name = TextProperty("Name")

    def __hash__(self) -> int:
        return hash((self.name, self.type, self.texture_name))


class VectorShaderParameter(ShaderParameter):
    type = "Vector"

    def __init__(self):
        super().__init__()
        self.x = AttributeProperty("x", 0)
        self.y = AttributeProperty("y", 0)
        self.z = AttributeProperty("z", 0)
        self.w = AttributeProperty("w", 0)

    def __hash__(self) -> int:
        return hash((self.name, self.type, self.x, self.y, self.z, self.w))


class ArrayShaderParameter(ShaderParameter):
    type = "Array"

    def __init__(self):
        super().__init__()
        self.values = []

    @staticmethod
    def from_xml(element: ET.Element):
        new = super(ArrayShaderParameter,
                    ArrayShaderParameter).from_xml(element)

        for item in element:
            new.values.append(Vector4Property.from_xml(item).value)

        return new

    def to_xml(self):
        element = super().to_xml()

        for value in self.values:
            child_elem = Vector4Property("Value", value).to_xml()
            element.append(child_elem)

        return element

    def __hash__(self) -> int:
        values_unpacked = [x for vector in self.values for x in [
            vector.x, vector.y, vector.z, vector.w]]
        return hash((self.name, self.type, *values_unpacked))


class ParametersList(ListProperty):
    list_type = ShaderParameter
    tag_name = "Parameters"

    @staticmethod
    def from_xml(element: ET.Element):
        new = ParametersList()

        for child in element.iter():
            if "type" in child.attrib:
                param_type = child.get("type")
                if param_type == TextureShaderParameter.type:
                    new.value.append(TextureShaderParameter.from_xml(child))
                if param_type == VectorShaderParameter.type:
                    new.value.append(VectorShaderParameter.from_xml(child))
                if param_type == ArrayShaderParameter.type:
                    new.value.append(
                        ArrayShaderParameter.from_xml(child))

        return new

    def __hash__(self) -> int:
        return hash(tuple(hash(param) for param in self.value))


class Shader(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.name = TextProperty("Name", "")
        self.filename = TextProperty("FileName", "")
        self.render_bucket = ValueProperty("RenderBucket", 0)
        self.parameters = ParametersList()

    def __hash__(self) -> int:
        params_elem = self.get_element("parameters")
        return hash((hash(self.name), hash(self.filename), hash(self.render_bucket), hash(params_elem)))

    def __eq__(self, other) -> bool:
        if not isinstance(other, Shader):
            return False

        return hash(self) == hash(other)


class ShadersList(ListProperty):
    list_type = Shader
    tag_name = "Shaders"


class ShaderGroup(ElementTree):
    tag_name = "ShaderGroup"

    def __init__(self):
        super().__init__()
        self.texture_dictionary = TextureDictionaryList()
        self.shaders = ShadersList()


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

        if not self.value:
            return None

        element.text = ", ".join([str(id) for id in self.value])
        return element


class Bone(ElementTree):
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


class BonesList(ListProperty):
    list_type = Bone
    tag_name = "Bones"


class Skeleton(ElementTree):
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
        self.bones = BonesList("Bones")


class BoneLimit(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.bone_id = ValueProperty("BoneId", 0)
        self.min = VectorProperty("Min")
        self.max = VectorProperty("Max")


class RotationLimit(BoneLimit):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.unk_a = ValueProperty("UnknownA", 0)


class RotationLimitsList(ListProperty):
    list_type = RotationLimit
    tag_name = "RotationLimits"


class TranslationLimitsList(ListProperty):
    list_type = BoneLimit
    tag_name = "TranslationLimits"


class Joints(ElementTree):
    tag_name = "Joints"

    def __init__(self):
        super().__init__()
        self.rotation_limits = RotationLimitsList("RotationLimits")
        self.translation_limits = TranslationLimitsList("TranslationLimits")


class Light(ElementTree):
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
        self.shadow_blur = ValueProperty("ShadowBlur")
        self.projected_texture_hash = TextProperty("ProjectedTextureHash")


class Lights(ListProperty):
    list_type = Light
    tag_name = "Lights"


class VertexLayoutList(ElementProperty):
    value_types = (list)
    tag_name = "Layout"

    def __init__(self, type: str = "GTAV1", value: list[str] = None):
        super().__init__(self.tag_name, value or [])
        self.type = type

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        new.type = element.get("type")
        for child in element:
            new.value.append(child.tag)
        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.set("type", self.type)
        for item in self.value:
            element.append(ET.Element(item))
        return element


class VertexBuffer(ElementTree):
    # Dtypes for vertex buffer structured numpy array
    # Based off of CodeWalker.GameFiles.VertexTypeGTAV1
    VERT_ATTR_DTYPES = {
        "Position": ("Position", np.float32, 3),
        "BlendWeights": ("BlendWeights", np.uint32, 4),
        "BlendIndices": ("BlendIndices", np.uint32, 4),
        "Normal": ("Normal", np.float32, 3),
        "Colour0": ("Colour0", np.uint32, 4),
        "Colour1": ("Colour1", np.uint32, 4),
        "TexCoord0": ("TexCoord0", np.float32, 2),
        "TexCoord1": ("TexCoord1", np.float32, 2),
        "TexCoord2": ("TexCoord2", np.float32, 2),
        "TexCoord3": ("TexCoord3", np.float32, 2),
        "TexCoord4": ("TexCoord4", np.float32, 2),
        "TexCoord5": ("TexCoord5", np.float32, 2),
        "TexCoord6": ("TexCoord6", np.float32, 2),
        "TexCoord7": ("TexCoord7", np.float32, 2),
        "Tangent": ("Tangent", np.float32, 4),
    }

    tag_name = "VertexBuffer"

    def __init__(self):
        super().__init__()
        self.flags = ValueProperty("Flags", 0)
        self.data: Optional[NDArray] = None

        self.layout = VertexLayoutList()

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = super().from_xml(element)

        data_elem = element.find("Data")
        data2_elem = element.find("Data2")

        if data_elem is None and data2_elem is not None:
            data_elem = data2_elem

        if data_elem is None or not data_elem.text:
            return new

        new._load_data_from_str(data_elem.text)

        return new

    def to_xml(self):
        self.layout = self.data.dtype.names
        element = super().to_xml()

        if self.data is None:
            return element

        data_elem = ET.Element("Data")
        data_elem.text = self._data_to_str()

        element.append(data_elem)

        return element

    def _load_data_from_str(self, _str: str):
        layout = self.get_element("layout")
        struct_dtype = np.dtype([self.VERT_ATTR_DTYPES[attr_name] for attr_name in layout.value])
        if layout.type == "GTAV2":
            # FVF with value GTAV2 (used for cloth) has Normal with format RGBA8 (though A is unused), which CW now
            # exports as 4 floats. Other code assumes that Normal always has 3 floats.
            # This is the only case (given vanilla assets at least) where a vertex element can have a different number
            # of components depending on FVF so just hack it in here. Read the 4 floats and drop the last float.
            normal_fmt = ("Normal", np.float32, 4)
            raw_struct_dtype = np.dtype([normal_fmt if attr_name == "Normal" else self.VERT_ATTR_DTYPES[attr_name]
                                         for attr_name in layout.value])

            raw_data = np.loadtxt(io.StringIO(_str), dtype=raw_struct_dtype)

            data = np.empty_like(raw_data, dtype=struct_dtype)
            for comp in layout.value:
                if comp == "Normal":
                    data["Normal"] = raw_data["Normal"][:, :3]
                else:
                    data[comp] = raw_data[comp]

            self.data = data
        else:
            self.data = np.loadtxt(io.StringIO(_str), dtype=struct_dtype)

    def _data_to_str(self):
        layout = self.get_element("layout")
        vert_arr = self.data

        if layout.type == "GTAV2":
            # Add back the 4th float of Normal element required by FVF GTAV2
            new_struct_dtype = np.dtype([(name, dtype if name != "Normal" else (np.float32, 4))
                                         for name, (dtype, _) in vert_arr.dtype.fields.items()])
            new_vert_arr = np.empty_like(vert_arr, dtype=new_struct_dtype)
            for comp in vert_arr.dtype.fields.keys():
                if comp == "Normal":
                    new_vert_arr["Normal"] = np.c_[vert_arr["Normal"], np.zeros(len(vert_arr))]
                else:
                    new_vert_arr[comp] = vert_arr[comp]

            vert_arr = new_vert_arr

        FLOAT_FMT = "%.7f"
        INT_FMT = "%.0u"
        ATTR_SEP = "   "

        formats: list[str] = []

        for field_name in vert_arr.dtype.names:
            attr_dtype = vert_arr.dtype[field_name].base
            column = vert_arr[field_name]

            attr_fmt = INT_FMT if attr_dtype == np.uint32 else FLOAT_FMT
            formats.append(" ".join([attr_fmt] * column.shape[1]))

        fmt = ATTR_SEP.join(formats)
        vert_arr_2d = np.column_stack([vert_arr[name] for name in vert_arr.dtype.names])

        return np_arr_to_str(vert_arr_2d, fmt)


class IndexBuffer(ElementTree):
    tag_name = "IndexBuffer"

    def __init__(self):
        super().__init__()
        self.data: Optional[NDArray] = None

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()

        data_elem = element.find("Data")

        if data_elem is None or not data_elem.text:
            return new

        new.data = np.fromstring(data_elem.text, sep=" ", dtype=np.uint32)
        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)

        if self.data is None:
            return element

        data_elem = ET.Element("Data")
        data_elem.text = self._inds_to_str()

        element.append(data_elem)

        return element

    def _inds_to_str(self):
        indices_arr = self.data

        num_inds = len(indices_arr)

        # Get number of rows that can be split into 24 columns
        num_divisble_inds = num_inds - (num_inds % 24)
        num_rows = int(num_divisble_inds / 24)

        indices_arr_2d = indices_arr[:num_divisble_inds].reshape(
            (num_rows, 24))

        index_buffer_str = np_arr_to_str(indices_arr_2d, fmt="%.0u")
        # Add the last row
        last_row_str = np_arr_to_str(
            indices_arr[num_divisble_inds:], fmt="%.0u")

        return f"{index_buffer_str}\n{last_row_str}"


class Geometry(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.shader_index = ValueProperty("ShaderIndex", 0)
        self.bounding_box_min = VectorProperty("BoundingBoxMin")
        self.bounding_box_max = VectorProperty("BoundingBoxMax")
        self.bone_ids = BoneIDProperty()
        self.vertex_buffer = VertexBuffer()
        self.index_buffer = IndexBuffer()


class GeometriesList(ListProperty):
    list_type = Geometry
    tag_name = "Geometries"


class DrawableModel(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.render_mask = ValueProperty("RenderMask", 0)
        self.flags = ValueProperty("Flags", 0)
        self.has_skin = ValueProperty("HasSkin", 0)  # 0 = false, 1 = true
        self.bone_index = ValueProperty("BoneIndex", 0)
        self.matrix_count = ValueProperty("Unknown1", 0)
        self.geometries = GeometriesList()


class DrawableModelList(ListProperty):
    list_type = DrawableModel
    tag_name = "DrawableModels"


class Drawable(ElementTree, AbstractClass):
    tag_name = None

    @property
    def is_empty(self) -> bool:
        return len(self.all_models) == 0

    @property
    def all_geoms(self) -> list[Geometry]:
        return [geom for model in self.all_models for geom in model.geometries]

    @property
    def all_models(self) -> list[DrawableModel]:
        return self.drawable_models_high + self.drawable_models_med + self.drawable_models_low + self.drawable_models_vlow

    def __init__(self, tag_name: str = "Drawable"):
        super().__init__()
        self.tag_name = tag_name

        # Only in fragment drawables
        self.frag_bound_matrix = MatrixProperty("Matrix")
        self.frag_extra_bound_matrices = DrawableMatrices("Matrices")

        self.name = TextProperty("Name", "")
        self.bounding_sphere_center = VectorProperty("BoundingSphereCenter")
        self.bounding_sphere_radius = ValueProperty("BoundingSphereRadius")
        self.bounding_box_min = VectorProperty("BoundingBoxMin")
        self.bounding_box_max = VectorProperty("BoundingBoxMax")
        self.lod_dist_high = ValueProperty("LodDistHigh", 0)  # 9998?
        self.lod_dist_med = ValueProperty("LodDistMed", 0)  # 9998?
        self.lod_dist_low = ValueProperty("LodDistLow", 0)  # 9998?
        self.lod_dist_vlow = ValueProperty("LodDistVlow", 0)  # 9998?
        self.flags_high = ValueProperty("FlagsHigh", 0)
        self.flags_med = ValueProperty("FlagsMed", 0)
        self.flags_low = ValueProperty("FlagsLow", 0)
        self.flags_vlow = ValueProperty("FlagsVlow", 0)

        self.shader_group = ShaderGroup()
        self.skeleton = Skeleton()
        self.joints = Joints()
        self.drawable_models_high = DrawableModelList(
            "DrawableModelsHigh")
        self.drawable_models_med = DrawableModelList(
            "DrawableModelsMedium")
        self.drawable_models_low = DrawableModelList(
            "DrawableModelsLow")
        self.drawable_models_vlow = DrawableModelList(
            "DrawableModelsVeryLow")
        self.lights = Lights()
        self.bounds = None

        # For merging hi Drawables after import
        self.hi_models: list[DrawableModel] = []

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = super().from_xml(element)

        bounds_elem = element.find("Bounds")
        if bounds_elem is not None:
            bound_type = bounds_elem.get("type")
            bound = None
            if bound_type == "Composite":
                bound = BoundComposite.from_xml(bounds_elem)
            elif bound_type == "Box":
                bound = BoundBox.from_xml(bounds_elem)
            elif bound_type == "Sphere":
                bound = BoundSphere.from_xml(bounds_elem)
            elif bound_type == "Capsule":
                bound = BoundCapsule.from_xml(bounds_elem)
            elif bound_type == "Cylinder":
                bound = BoundCylinder.from_xml(bounds_elem)
            elif bound_type == "Disc":
                bound = BoundDisc.from_xml(bounds_elem)
            elif bound_type == "Cloth":
                bound = BoundPlane.from_xml(bounds_elem)
            elif bound_type == "Geometry":
                bound = BoundGeometry.from_xml(bounds_elem)
            elif bound_type == "GeometryBVH":
                bound = BoundGeometryBVH.from_xml(bounds_elem)

            if bound:
                bound.tag_name = "Bounds"
                new.bounds = bound

        return new

    def to_xml(self):
        if self.bounds:
            self.bounds.tag_name = "Bounds"
        return super().to_xml()


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

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        new.tag_name = "Item"
        children = element.findall(new.tag_name)

        for child in children:
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


class DrawableMatrices(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str = "Matrices", value: list[Matrix] = None):
        super().__init__(tag_name, value)
        self.value = value or []

    @classmethod
    def from_xml(cls, element: Element):
        # Import not needed (this should be eventually calculated in CW anyway)
        return cls()

    def to_xml(self):
        if self.value is None or len(self.value) == 0:
            return

        elem = ET.Element("Matrices", attrib={"capacity": "64"})

        for mat in self.value:
            mat_prop = MatrixProperty("Item", mat)
            mat_elem = mat_prop.to_xml()
            mat_elem.attrib["id"] = "0"

            elem.append(mat_elem)

        return elem


class BonePropertiesManager:
    dictionary_xml = os.path.join(
        os.path.dirname(__file__), "BoneProperties.xml")
    bones = {}

    @staticmethod
    def load_bones():
        tree = ET.parse(BonePropertiesManager.dictionary_xml)
        for node in tree.getroot():
            bone = Bone.from_xml(node)
            BonePropertiesManager.bones[bone.name] = bone


BonePropertiesManager.load_bones()
