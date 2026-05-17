"""Local CWXML wrapper for GTA V .ynv navmesh.

The stock ``szio.gta5.cwxml.navmesh`` can't write a navmesh back:
  1. NavPolygonVertices doesn't override ``to_xml()`` so the default list
     serializer tries to call ``Vector.to_xml()`` and crashes.
  2. NavPortal.type uses the ``Value`` tag but CodeWalker writes ``Type``.

Both are fixed here. We also override ``write_xml`` and provide a custom
VectorProperty so a plain import → export round-trips the file
byte-identically against the original CodeWalker output:

* 1-space indent per level (szio defaults to 2)
* XML declaration with double quotes (Python's ElementTree defaults to single)
* BB attributes formatted without trailing ``.0`` for whole numbers

Without these, the data is correct but the textual form drifts on every
re-export — git diff churn and broken file-comparison testing.
"""
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
    """Format a float32 coordinate the way CodeWalker does.

    CodeWalker runs on .NET Framework, which serializes ``Single`` values
    through ``ToString("R")`` — round-trip format. That implementation
    tries 7 significant digits first; if the result round-trips back to
    the original ``Single``, it's used. Otherwise it falls back to 9.
    Never 8 — .NET goes straight from 7 to 9.

    Outputs match the source files byte-for-byte:
      * ``152.9984``  (G7 round-trips; G9 would add noise: 152.998398)
      * ``-750.0023`` (G7)
      * ``241.155212`` (G7 truncates to 241.1552 — fall back to G9)
      * ``4.41054964`` (G9)
      * ``150``       (integer-valued, no fractional part)
    """
    f32 = np.float32(float(v))
    f = float(f32)
    if f == int(f):
        return str(int(f))
    s = f"{f:.7g}"
    if np.float32(float(s)) == f32:
        return s
    return f"{f:.9g}"


class NavmeshVectorProperty(VectorProperty):
    """VectorProperty that emits ``x="150"`` instead of ``x="150.0"`` for whole numbers."""

    def to_xml(self):
        return ET.Element(self.tag_name, attrib={
            "x": fmt_float(self.value.x),
            "y": fmt_float(self.value.y),
            "z": fmt_float(self.value.z),
        })


class NavmeshFloatValueProperty(ValueProperty):
    """ValueProperty for float fields (Angle), formatted via :func:`fmt_float`.

    Stock ``ValueProperty.to_xml`` does ``str(float32(value))``, which always
    emits 7 significant digits — even when CodeWalker stored 9. Round-trip
    output then drifts on every save.
    """

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
    """Copy of szio's ``indent`` but with a single-space step (matches CodeWalker)."""
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
        # Multi-line text (Vertices, Edges) — indent each line under its parent.
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
        """Serialize with CodeWalker-style indent + XML declaration.

        Hand-writing the header avoids two ElementTree defaults we can't
        configure: single-quoted XML declaration and zero-space before the
        self-closing slash. CodeWalker uses double-quoted declaration and
        ``<Tag attr="..." />`` with a leading space.
        """
        element = self.to_xml()
        _indent_one_space(element)
        body = ET.tostring(element, encoding="unicode", short_empty_elements=True)
        # CodeWalker emits self-closing tags with a leading space (`" />`).
        # ElementTree emits no space (`"/>`). Normalize.
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
