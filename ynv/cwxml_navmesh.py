from xml.etree import ElementTree as ET

import numpy as np

from szio.types import Vector
from szio.xml import (
    ElementTree,
    ListProperty,
    TextProperty,
    ValueProperty,
    VectorProperty,
)


def fmt_float(v) -> str:
    # Mimics .NET ToString("R"): G7 if it round-trips, otherwise G9.
    # Required for byte-identical round-trips against CodeWalker output.
    f32 = np.float32(float(v))
    f = float(f32)
    if f == int(f):
        return str(int(f))
    s = f"{f:.7g}"
    if np.float32(float(s)) == f32:
        return s
    return f"{f:.9g}"


class NavmeshVectorProperty(VectorProperty):
    def to_xml(self):
        return ET.Element(self.tag_name, attrib={
            "x": fmt_float(self.value.x),
            "y": fmt_float(self.value.y),
            "z": fmt_float(self.value.z),
        })


class NavmeshFloatValueProperty(ValueProperty):
    # Stock ValueProperty always emits G7; CodeWalker can store G9.
    # Use fmt_float to keep round-trips stable.
    def to_xml(self):
        value = self.value
        if isinstance(value, float):
            value = str(int(value)) if value.is_integer() else fmt_float(value)
        else:
            value = str(value)
        return ET.Element(self.tag_name, attrib={"value": value})


class NavPolygonVertices(ListProperty):
    list_type = Vector
    tag_name = "Vertices"

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name=tag_name, value=value)

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()
        verts = []
        if element.text:
            for line in element.text.strip().split("\n"):
                nums = line.strip().split(",")
                if len(nums) != 3:
                    continue
                verts.append(Vector((float(nums[0]), float(nums[1]), float(nums[2]))))
        new.value = verts
        return new

    def to_xml(self):
        if not self.value:
            return None
        elem = ET.Element(self.tag_name)
        lines = [f"{fmt_float(v[0])}, {fmt_float(v[1])}, {fmt_float(v[2])}" for v in self.value]
        elem.text = "\n" + "\n".join(lines) + "\n"
        return elem


class NavPoint(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = ValueProperty("Type")
        self.angle = NavmeshFloatValueProperty("Angle")
        self.position = NavmeshVectorProperty("Position")


class NavPointList(ListProperty):
    list_type = NavPoint
    tag_name = "Points"


class NavPortal(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.type = ValueProperty("Type")
        self.angle = NavmeshFloatValueProperty("Angle")
        self.poly_from = ValueProperty("PolyFrom")
        self.poly_to = ValueProperty("PolyTo")
        self.position_from = NavmeshVectorProperty("PositionFrom")
        self.position_to = NavmeshVectorProperty("PositionTo")


class NavPortalList(ListProperty):
    list_type = NavPortal
    tag_name = "Portals"


class NavPolygon(ElementTree):
    tag_name = "Item"

    def __init__(self):
        super().__init__()
        self.flags = TextProperty("Flags")
        self.vertices = NavPolygonVertices("Vertices")
        self.edges = TextProperty("Edges")


class NavPolygonList(ListProperty):
    list_type = NavPolygon
    tag_name = "Polygons"


def _indent_one_space(elem: ET.Element, level: int = 0) -> None:
    # szio's indent helper but with a single-space step to match CodeWalker.
    amount = " "
    i = "\n" + level * amount
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + amount
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for child in elem:
            _indent_one_space(child, level + 1)
        if not child.tail or not child.tail.strip():
            child.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i
        if elem.text and len(elem.text.strip()) > 0 and elem.text.find("\n") != -1:
            lines = elem.text.strip().split("\n")
            for idx, line in enumerate(lines):
                lines[idx] = ((level + 1) * amount) + line
            elem.text = "\n" + "\n".join(lines) + i


class Navmesh(ElementTree):
    tag_name = "NavMesh"

    def __init__(self):
        super().__init__()
        self.content_flags = TextProperty("ContentFlags")
        self.area_id = ValueProperty("AreaID")
        self.bb_min = NavmeshVectorProperty("BBMin")
        self.bb_max = NavmeshVectorProperty("BBMax")
        self.bb_size = NavmeshVectorProperty("BBSize")
        self.polygons = NavPolygonList()
        self.portals = NavPortalList()
        self.points = NavPointList()

    def write_xml(self, filepath):
        # Hand-writing the header so we get a double-quoted XML declaration
        # and `" />` self-closing tags — both required by CodeWalker.
        element = self.to_xml()
        _indent_one_space(element)
        body = ET.tostring(element, encoding="unicode", short_empty_elements=True)
        body = body.replace('"/>', '" />')
        if not body.endswith("\n"):
            body += "\n"
        with open(filepath, "w", encoding="utf-8") as f:
            f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
            f.write(body)


class YNV:
    file_extension = ".ynv.xml"

    @staticmethod
    def from_xml_file(filepath):
        return Navmesh.from_xml_file(filepath)

    @staticmethod
    def write_xml(nav, filepath):
        return nav.write_xml(filepath)
