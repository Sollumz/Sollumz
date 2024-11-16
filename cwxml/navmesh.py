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
        return NavMesh.from_xml_file(filepath)

    @staticmethod
    def write_xml(nav, filepath):
        return nav.write_xml(filepath)


class NavCoverPoint(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = ValueProperty("Type")
        self.angle = ValueProperty("Angle")
        self.position = VectorProperty("Position")


class NavCoverPointList(ListProperty):
    list_type = NavCoverPoint
    tag_name = "Points"


class NavLink(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = ValueProperty("Type")
        self.angle = ValueProperty("Angle")
        self.poly_from = ValueProperty("PolyFrom")
        self.poly_to = ValueProperty("PolyTo")
        self.position_from = VectorProperty("PositionFrom")
        self.position_to = VectorProperty("PositionTo")


class NavLinkList(ListProperty):
    list_type = NavLink
    tag_name = "Portals"


class NavPolygonVertices(ListProperty):
    list_type = Vector
    tag_name = "Vertices"

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name=tag_name, value=value)

    @staticmethod
    def from_xml(element: ET.Element):
        new = NavPolygonVertices(element.tag, [])
        text = element.text.strip().split("\n")
        if len(text) > 0:
            for line in text:
                coords = line.strip().split(",")
                if not len(coords) == 3:
                    return NavPolygonVertices.read_value_error(element)

                new.value.append(
                    Vector((float(coords[0]), float(coords[1]), float(coords[2]))))

        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)
        text = ["\n"]

        if not self.value:
            return

        for vertex in self.value:
            if not isinstance(vertex, Vector):
                raise TypeError(
                    f"NavPolygonVertices can only contain Vector objects, not '{type(self.value)}'!")
            for index, component in enumerate(vertex):
                text.append(str(component))
                if index < len(vertex) - 1:
                    text.append(", ")
            text.append("\n")

        element.text = "".join(text)

        return element


class NavPolygon(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.flags = TextProperty("Flags")
        self.vertices = NavPolygonVertices("Vertices")
        self.edges = TextProperty("Edges")
        self.edges_flags = TextProperty("EdgesFlags")


class NavPolygonList(ListProperty):
    list_type = NavPolygon
    tag_name = "Polygons"


class NavMesh(ElementTree):
    tag_name = "NavMesh"

    def __init__(self):
        super().__init__()
        self.content_flags = TextProperty("ContentFlags")
        self.area_id = ValueProperty("AreaID")
        self.bb_min = VectorProperty("BBMin")
        self.bb_max = VectorProperty("BBMax")
        self.bb_size = VectorProperty("BBSize")
        self.polygons = NavPolygonList()
        self.links = NavLinkList()
        self.cover_points = NavCoverPointList()
