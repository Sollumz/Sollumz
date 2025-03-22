from abc import ABC as AbstractClass
from .element import (
    ElementTree,
    ValueProperty,
    ListPropertyRequired,
)


class WATER:

    file_extension = "water.xml"

    @staticmethod
    def from_xml_file(filepath):
        return WaterData.from_xml_file(filepath)

    @staticmethod
    def write_xml(water_data, filepath):
        return water_data.write_xml(filepath)

class Water(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.minX =           ValueProperty("minX")
        self.maxX =           ValueProperty("maxX")
        self.minY =           ValueProperty("minY")
        self.maxY =           ValueProperty("maxY")
        self.type =           ValueProperty("Type")
        self.invisible =      ValueProperty("IsInvisible")
        self.limited_depth =  ValueProperty("HasLimitedDepth")
        self.z =              ValueProperty("z")
        self.a1 =             ValueProperty("a1")
        self.a2 =             ValueProperty("a2")
        self.a3 =             ValueProperty("a3")
        self.a4 =             ValueProperty("a4")
        self.no_stencil =     ValueProperty("NoStencil")

class Calming(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.minX =           ValueProperty("minX")
        self.maxX =           ValueProperty("maxX")
        self.minY =           ValueProperty("minY")
        self.maxY =           ValueProperty("maxY")
        self.dampening =      ValueProperty("fDampening")

class Wave(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.minX =           ValueProperty("minX")
        self.maxX =           ValueProperty("maxX")
        self.minY =           ValueProperty("minY")
        self.maxY =           ValueProperty("maxY")
        self.amplitude =      ValueProperty("Amplitude")
        self.xdirection =     ValueProperty("XDirection")
        self.ydirection =     ValueProperty("YDirection")


class WaterList(ListPropertyRequired):
    list_type = Water
    tag_name = "WaterQuads"

class CalmingList(ListPropertyRequired):
    list_type = Calming
    tag_name = "CalmingQuads"
    
class WaveList(ListPropertyRequired):
    list_type = Wave
    tag_name = "WaveQuads"


class WaterData(ElementTree, AbstractClass):
    tag_name = "WaterData"

    def __init__(self):
        super().__init__()
        self.water = WaterList()
        self.calming = CalmingList()
        self.wave = WaveList()