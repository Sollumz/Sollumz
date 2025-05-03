import xml.etree.ElementTree as ET
import os
from abc import ABC, abstractmethod
from .element import (
    ElementProperty,
    ElementTree,
    ListProperty,
    TextProperty,
    AttributeProperty,
)
from .drawable import VertexLayoutList
from ..tools import jenkhash
from typing import Optional
from enum import Enum, Flag, auto


class FileNameList(ListProperty):
    class FileName(TextProperty):
        tag_name = "Item"

    list_type = FileName
    tag_name = "FileName"


class LayoutList(ListProperty):
    class Layout(VertexLayoutList):
        tag_name = "Item"

    list_type = Layout
    tag_name = "Layout"


class ShaderParameterType(str, Enum):
    TEXTURE = "Texture"
    FLOAT = "float"
    FLOAT2 = "float2"
    FLOAT3 = "float3"
    FLOAT4 = "float4"
    FLOAT4X4 = "float4x4"


class ShaderParameterSubtype(str, Enum):
    RGB = "rgb"
    RGBA = "rgba"
    BOOL = "bool"


class ShaderParameterDef(ElementTree, ABC):
    tag_name = "Item"

    @property
    @abstractmethod
    def type() -> ShaderParameterType:
        raise NotImplementedError

    def __init__(self):
        super().__init__()
        self.name = AttributeProperty("name")
        self.type = AttributeProperty("type", self.type)
        self.subtype = AttributeProperty("subtype")
        self.hidden = AttributeProperty("hidden", False)


class ShaderParameterTextureDef(ShaderParameterDef):
    type = ShaderParameterType.TEXTURE

    def __init__(self):
        super().__init__()
        self.uv = AttributeProperty("uv")


class ShaderParameterFloatVectorDef(ShaderParameterDef, ABC):
    def __init__(self):
        super().__init__()
        self.count = AttributeProperty("count", 0)

    @property
    def is_array(self):
        return self.count > 0


class ShaderParameterFloatDef(ShaderParameterFloatVectorDef):
    type = ShaderParameterType.FLOAT

    def __init__(self):
        super().__init__()
        self.x = AttributeProperty("x", 0.0)


class ShaderParameterFloat2Def(ShaderParameterFloatVectorDef):
    type = ShaderParameterType.FLOAT2

    def __init__(self):
        super().__init__()
        self.x = AttributeProperty("x", 0.0)
        self.y = AttributeProperty("y", 0.0)


class ShaderParameterFloat3Def(ShaderParameterFloatVectorDef):
    type = ShaderParameterType.FLOAT3

    def __init__(self):
        super().__init__()
        self.x = AttributeProperty("x", 0.0)
        self.y = AttributeProperty("y", 0.0)
        self.z = AttributeProperty("z", 0.0)


class ShaderParameterFloat4Def(ShaderParameterFloatVectorDef):
    type = ShaderParameterType.FLOAT4

    def __init__(self):
        super().__init__()
        self.x = AttributeProperty("x", 0.0)
        self.y = AttributeProperty("y", 0.0)
        self.z = AttributeProperty("z", 0.0)
        self.w = AttributeProperty("w", 0.0)


class ShaderParameterFloat4x4Def(ShaderParameterDef):
    type = ShaderParameterType.FLOAT4X4

    def __init__(self):
        super().__init__()


class ShaderParameterDefsList(ListProperty):
    list_type = ShaderParameterDef
    tag_name = "Parameters"

    @staticmethod
    def from_xml(element: ET.Element):
        new = ShaderParameterDefsList()

        for child in element.iter():
            if "type" in child.attrib:
                param_type = child.get("type")
                match param_type:
                    case ShaderParameterType.TEXTURE:
                        param = ShaderParameterTextureDef.from_xml(child)
                    case ShaderParameterType.FLOAT:
                        param = ShaderParameterFloatDef.from_xml(child)
                    case ShaderParameterType.FLOAT2:
                        param = ShaderParameterFloat2Def.from_xml(child)
                    case ShaderParameterType.FLOAT3:
                        param = ShaderParameterFloat3Def.from_xml(child)
                    case ShaderParameterType.FLOAT4:
                        param = ShaderParameterFloat4Def.from_xml(child)
                    case ShaderParameterType.FLOAT4X4:
                        param = ShaderParameterFloat4x4Def.from_xml(child)
                    case _:
                        assert False, f"Unknown shader parameter type '{param_type}'"

                new.value.append(param)

        return new


class ShaderDefFlag(Flag):
    IS_CLOTH = auto()
    IS_PED_CLOTH = auto()
    IS_TERRAIN = auto()
    IS_TERRAIN_MASK_ONLY = auto()


class ShaderDefFlagProperty(ElementProperty):
    value_types = (ShaderDefFlag)

    def __init__(self, tag_name: str = "Flags", value: ShaderDefFlag = ShaderDefFlag(0)):
        super().__init__(tag_name, value)

    @staticmethod
    def from_xml(element: ET.Element):
        new = ShaderDefFlagProperty(element.tag)
        if element.text:
            text = element.text.split()
            for flag in text:
                if flag in ShaderDefFlag.__members__:
                    new.value = new.value | ShaderDefFlag[flag]
                else:
                    ShaderDefFlagProperty.read_value_error(element)

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        if len(self.value) > 0:
            element.text = " ".join(f.name for f in self.value)
        return element


class ShaderDef(ElementTree):
    tag_name = "Item"

    render_bucket: int
    uv_maps: dict[str, int]
    parameter_map: dict[str, ShaderParameterDef]
    parameter_ui_order: dict[str, int]

    def __init__(self):
        super().__init__()
        self.filename = TextProperty("Name", "")
        self.flags = ShaderDefFlagProperty()
        self.layouts = LayoutList()
        self.parameters = ShaderParameterDefsList("Parameters")
        self.render_bucket = 0
        self.uv_maps = {}
        self.parameter_map = {}
        self.parameter_ui_order = {}

    @property
    def required_tangent(self):
        for layout in self.layouts:
            if "Tangent" in layout.value:
                return True
        return False

    @property
    def required_normal(self):
        for layout in self.layouts:
            if "Normal" in layout.value:
                return True
        return False

    @property
    def used_texcoords(self) -> set[str]:
        names = set()
        for layout in self.layouts:
            for field_name in layout.value:
                if "TexCoord" in field_name:
                    names.add(field_name)

        return names

    @property
    def used_texcoords_indices(self) -> set[int]:
        indices = set()
        for layout in self.layouts:
            for field_name in layout.value:
                if "TexCoord" in field_name:
                    indices.add(int(field_name[8:]))

        return indices

    @property
    def used_colors(self) -> set[str]:
        names = set()
        for layout in self.layouts:
            for field_name in layout.value:
                if "Colour" in field_name:
                    names.add(field_name)

        return names

    @property
    def used_colors_indices(self) -> set[int]:
        indices = set()
        for layout in self.layouts:
            for field_name in layout.value:
                if "Colour" in field_name:
                    indices.add(int(field_name[6:]))

        return indices

    @property
    def is_uv_animation_supported(self) -> bool:
        return "globalAnimUV0" in self.parameter_map and "globalAnimUV1" in self.parameter_map

    @property
    def is_cloth(self) -> bool:
        return ShaderDefFlag.IS_CLOTH in self.flags

    @property
    def is_ped_cloth(self) -> bool:
        return ShaderDefFlag.IS_PED_CLOTH in self.flags

    @property
    def is_terrain(self) -> bool:
        return ShaderDefFlag.IS_TERRAIN in self.flags

    @property
    def is_terrain_mask_only(self) -> bool:
        return ShaderDefFlag.IS_TERRAIN_MASK_ONLY in self.flags

    @property
    def is_alpha(self) -> bool:
        return self.render_bucket == 1

    @property
    def is_decal(self) -> bool:
        return self.render_bucket == 2

    @property
    def is_cutout(self) -> bool:
        return self.render_bucket == 3

    @classmethod
    def from_xml(cls, element: ET.Element) -> "ShaderDef":
        new: ShaderDef = super().from_xml(element)
        new.uv_maps = {
            p.name: p.uv for p in new.parameters if p.type == ShaderParameterType.TEXTURE and p.uv is not None
        }
        new.parameter_map = {p.name: p for p in new.parameters}
        new.parameter_ui_order = {p.name: i for i, p in enumerate(new.parameters)}
        return new


class ShaderManager:
    shaderxml = os.path.join(os.path.dirname(__file__), "Shaders.xml")
    # Map shader filenames to base shader names
    _shaders_base_names: dict[ShaderDef, str] = {}
    _shaders: dict[str, ShaderDef] = {}
    _shaders_by_hash: dict[int, ShaderDef] = {}

    # Tint shaders that use colour1 instead of colour0 to index the tint palette
    tint_colour1_shaders = ["trees_normal_diffspec_tnt.sps", "trees_tnt.sps", "trees_normal_spec_tnt.sps"]
    palette_shaders = ["ped_palette.sps", "ped_default_palette.sps", "weapon_normal_spec_cutout_palette.sps",
                       "weapon_normal_spec_detail_palette.sps", "weapon_normal_spec_palette.sps"]
    em_shaders = ["normal_spec_emissive.sps", "normal_spec_reflect_emissivenight.sps", "emissive.sps", "emissive_speclum.sps", "emissive_tnt.sps", "emissivenight.sps",
                  "emissivenight_geomnightonly.sps", "emissivestrong_alpha.sps", "emissivestrong.sps", "glass_emissive.sps", "glass_emissivenight.sps", "glass_emissivenight_alpha.sps",
                  "glass_emissive_alpha.sps", "decal_emissive_only.sps", "decal_emissivenight_only.sps",

                  "vehicle_blurredrotor_emissive.sps",
                  "vehicle_dash_emissive.sps", "vehicle_dash_emissive_opaque.sps",
                  "vehicle_paint4_emissive.sps",
                  "vehicle_emissive_alpha.sps", "vehicle_emissive_opaque.sps",
                  "vehicle_tire_emissive.sps",
                  "vehicle_track_emissive.sps", "vehicle_track2_emissive.sps", "vehicle_track_siren.sps",
                  "vehicle_lightsemissive.sps", "vehicle_lightsemissive_siren.sps",
                  ]
    water_shaders = ["water_fountain.sps",
                     "water_poolenv.sps", "water_decal.sps", "water_terrainfoam.sps", "water_riverlod.sps", "water_shallow.sps", "water_riverfoam.sps", "water_riverocean.sps", "water_rivershallow.sps"]

    veh_paints = ["vehicle_paint1.sps", "vehicle_paint1_enveff.sps",
                  "vehicle_paint2.sps", "vehicle_paint2_enveff.sps", "vehicle_paint3.sps", "vehicle_paint3_enveff.sps", "vehicle_paint3_lvr.sps", "vehicle_paint4.sps", "vehicle_paint4_emissive.sps",
                  "vehicle_paint4_enveff.sps", "vehicle_paint5_enveff.sps", "vehicle_paint6.sps", "vehicle_paint6_enveff.sps", "vehicle_paint7.sps", "vehicle_paint7_enveff.sps", "vehicle_paint8.sps",
                  "vehicle_paint9.sps",]

    @staticmethod
    def load_shaders():
        tree = ET.parse(ShaderManager.shaderxml)

        for node in tree.getroot():
            base_name = node.find("Name").text
            for filename_elem in node.findall("./FileName//*"):
                filename = filename_elem.text

                if filename is None:
                    continue

                filename_hash = jenkhash.Generate(filename)
                render_bucket = int(filename_elem.attrib["bucket"])

                shader = ShaderDef.from_xml(node)
                shader.filename = filename
                shader.render_bucket = render_bucket
                ShaderManager._shaders[filename] = shader
                ShaderManager._shaders_by_hash[filename_hash] = shader
                ShaderManager._shaders_base_names[shader] = base_name

    @staticmethod
    def find_shader(filename: str) -> Optional[ShaderDef]:
        shader = ShaderManager._shaders.get(filename, None)
        if shader is None and filename.startswith("hash_"):
            filename_hash = int(filename[5:], 16)
            shader = ShaderManager._shaders_by_hash.get(filename_hash, None)
        return shader

    @staticmethod
    def find_shader_base_name(filename: str) -> Optional[str]:
        shader = ShaderManager.find_shader(filename)
        if shader is None:
            return None
        return ShaderManager._shaders_base_names[shader]


ShaderManager.load_shaders()
