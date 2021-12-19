from .codewalker_xml import *
from xml.etree import ElementTree as ET


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
    tag_name = "Portals"


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


class NavPolygonItem(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.flags = TextProperty("Flags")
        self.vertices = TextProperty("Vertices")
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
