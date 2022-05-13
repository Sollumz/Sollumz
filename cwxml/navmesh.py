from .element import (
    ElementTree,
    ListProperty,
    TextProperty,
    ValueProperty,
    VectorProperty
)
from xml.etree import ElementTree as ET
from mathutils import Vector


class YNV:

    file_extension = ".ynv.xml"

    @staticmethod
    def from_xml_file(filepath):
        return Navmesh.from_xml_file(filepath)

    @staticmethod
    def write_xml(nav, filepath):
        return nav.write_xml(filepath)


class NavPointItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = ValueProperty("Type")
        self.angle = ValueProperty("Angle")
        self.position = VectorProperty("Position")


class NavPointListProperty(ListProperty):
    list_type = NavPointItem
    tag_name = "Points"


class NavPortalItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = ValueProperty("Value")
        self.angle = ValueProperty("Angle")
        self.poly_from = ValueProperty("PolyFrom")
        self.poly_to = ValueProperty("PolyTo")
        self.position_from = VectorProperty("PositionFrom")
        self.position_to = VectorProperty("PositionTo")


class NavPortalListProperty(ListProperty):
    list_type = NavPortalItem
    tag_name = "Portals"


class NavPolygonVertices(ListProperty):
    list_type = Vector
    tag_name = "Vertices"

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name=tag_name, value=value)

    @ classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        verts = []
        if element.text:
            txts = element.text.strip().split("\n")
            for txt in txts:
                txt = txt.strip()
            for txt in txts:
                nums = txt.split(", ")
                v0 = float(nums[0])
                v1 = float(nums[1])
                v2 = float(nums[2])
                verts.append(Vector((v0, v1, v2)))
        new.value = verts
        return new


class NavPolygonItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.flags = TextProperty("Flags")
        self.vertices = NavPolygonVertices("Vertices")
        self.edges = TextProperty("Edges")


class NavPolygonListProperty(ListProperty):
    list_type = NavPolygonItem
    tag_name = "Polygons"


class Navmesh(ElementTree):
    tag_name = "NavMesh"

    def __init__(self):
        super().__init__()
        self.content_flags = TextProperty("ContentFlags")
        self.area_id = ValueProperty("AreaID")
        self.bb_min = VectorProperty("BBMin")
        self.bb_max = VectorProperty("BBMax")
        self.bb_size = VectorProperty("BBSize")
        self.polygons = NavPolygonListProperty()
        self.portals = NavPortalListProperty()
        self.points = NavPointListProperty()
