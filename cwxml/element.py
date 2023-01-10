"""Manages reading/writing Codewalker XML files"""
from mathutils import Vector, Quaternion, Matrix
from abc import abstractmethod, ABC as AbstractClass, abstractclassmethod
from dataclasses import dataclass
from typing import Any
from xml.etree import ElementTree as ET
from numpy import float32


def indent(elem: ET.Element, level=0):
    """Custom indentation to get elements like <VerticesProperty /> to output nicely"""
    amount = "  "
    i = "\n" + level * amount
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + amount
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level + 1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

        # Indent innertext of elements on new lines. Used in cases like <VerticesProperty />
        if elem.text and len(elem.text.strip()) > 0 and elem.text.find("\n") != -1:
            lines = elem.text.strip().split("\n")
            for index, line in enumerate(lines):
                lines[index] = ((level + 1) * amount) + line
            elem.text = "\n" + "\n".join(lines) + i


def get_str_type(value: str):
    """Determine if a string is a bool, int, or float"""
    if isinstance(value, str):
        if value.lower() == "true" or value.lower() == "false":
            return bool(value)

        try:
            return int(value)
        except:
            pass
        try:
            return float(value)
        except:
            pass

    return value


class Element(AbstractClass):
    """Abstract XML element to base all other XML elements off of"""
    @property
    @abstractmethod
    def tag_name(self):
        raise NotImplementedError

    @classmethod
    def read_value_error(cls, element):
        raise ValueError(
            f"Invalid XML element '<{element.tag} />' for type '{cls.__name__}'!")

    @abstractclassmethod
    def from_xml(cls, element: ET.Element):
        """Convert ET.Element object to Element"""
        raise NotImplementedError

    @abstractmethod
    def to_xml(self):
        """Convert object to ET.Element object"""
        raise NotImplementedError

    @classmethod
    def from_xml_file(cls, filepath):
        """Read XML from filepath"""
        element_tree = ET.ElementTree()
        element_tree.parse(filepath)
        return cls.from_xml(element_tree.getroot())

    def write_xml(self, filepath):
        """Write object as XML to filepath"""
        element = self.to_xml()
        indent(element)
        elementTree = ET.ElementTree(element)
        elementTree.write(filepath, encoding="UTF-8", xml_declaration=True)


class ElementTree(Element):
    """XML element that contains children defined by it's properties"""

    @classmethod
    def from_xml(cls: Element, element: ET.Element):
        """Convert ET.Element object to ElementTree"""
        new = cls()

        for prop_name, obj_element in vars(new).items():
            if isinstance(obj_element, Element):
                child = element.find(obj_element.tag_name)
                if child is not None and obj_element.tag_name == child.tag:
                    # Add element to object if tag is defined in class definition
                    setattr(new, prop_name, type(obj_element).from_xml(child))
            elif isinstance(obj_element, AttributeProperty):
                # Add attribute to element if attribute is defined in class definition
                if obj_element.name in element.attrib and new.tag_name == element.tag:
                    obj_element.value = element.get(obj_element.name)

        return new

    def to_xml(self):
        """Convert ElementTree to ET.Element object"""
        root = ET.Element(self.tag_name)
        for child in vars(self).values():
            if isinstance(child, Element):
                element = child.to_xml()
                if element is not None:
                    root.append(element)
            elif isinstance(child, AttributeProperty):
                root.set(child.name, str(child.value))

        return root

    def __getattribute__(self, key: str, onlyValue: bool = True):
        obj = None
        # Try and see if key exists
        try:
            obj = object.__getattribute__(self, key)
            if isinstance(obj, (ElementProperty, AttributeProperty)) and onlyValue:
                # If the property is an ElementProperty or AttributeProperty, and onlyValue is true, return just the value of the Element property
                return obj.value
            else:
                return obj
        except AttributeError:
            # Key doesn't exist, return None
            return None

    def __setattr__(self, name: str, value) -> None:
        # Get the full object
        obj = self.__getattribute__(name, False)
        if obj and isinstance(obj, (ElementProperty, AttributeProperty)) and not isinstance(value, (ElementProperty, AttributeProperty)):
            # If the object is an ElementProperty or AttributeProperty, set it's value
            obj.value = value
            super().__setattr__(name, obj)
        else:
            super().__setattr__(name, value)

    def get_element(self, key):
        obj = self.__getattribute__(key, False)

        if isinstance(obj, ElementProperty):
            return obj


@dataclass
class AttributeProperty:
    name: str
    _value: Any = None

    @property
    def value(self):
        return get_str_type(self._value)

    @value.setter
    def value(self, value):
        self._value = value


class ElementProperty(Element, AbstractClass):
    @property
    @abstractmethod
    def value_types(self):
        raise NotImplementedError

    tag_name = None

    def __init__(self, tag_name, value):
        super().__init__()
        self.tag_name = tag_name
        if value and not isinstance(value, self.value_types):
            raise TypeError(
                f"Value of {type(self).__name__} must be one of {self.value_types}, not {type(value)}!")
        self.value = value


class ListProperty(ElementProperty, AbstractClass):
    """Holds a list value. List can only contain values of one type."""

    value_types = (list)

    @property
    @abstractmethod
    def list_type(self) -> Element:
        raise NotImplementedError

    @property
    @abstractmethod
    def tag_name(self) -> Element:
        raise NotImplementedError

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or type(self).tag_name, value or [])

    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls(element.tag)

        children = element.findall(new.list_type.tag_name)

        for child in children:
            new.value.append(new.list_type.from_xml(child))
        return new

    def to_xml(self):
        element = ET.Element(self.tag_name)

        for child in vars(self).values():
            if isinstance(child, AttributeProperty):
                element.set(child.name, str(child.value))

        if self.value and len(self.value) > 0:
            for item in self.value:
                if isinstance(item, self.list_type):
                    element.append(item.to_xml())
                else:
                    raise TypeError(
                        f"{type(self).__name__} can only hold objects of type '{self.list_type.__name__}', not '{type(item)}'")

            return element

        return None


class ListPropertyRequired(ListProperty):
    """Same as ListProperty but returns an empty element rather then None in case the passed element's value is empty or None"""

    def __init__(self, tag_name=None, value=None):
        super().__init__(tag_name or type(self).tag_name, value or [])

    def to_xml(self):
        element = ET.Element(self.tag_name)

        for child in vars(self).values():
            if isinstance(child, AttributeProperty):
                element.set(child.name, str(child.value))

        if self.value and len(self.value) > 0:
            for item in self.value:
                if isinstance(item, self.list_type):
                    element.append(item.to_xml())
                else:
                    raise TypeError(
                        f"{type(self).__name__} can only hold objects of type '{self.list_type.__name__}', not '{type(item)}'")

        return element


class TextProperty(ElementProperty):
    value_types = (str)

    def __init__(self, tag_name: str = "Name", value=None):
        super().__init__(tag_name, value or "")

    @staticmethod
    def from_xml(element: ET.Element):
        return TextProperty(element.tag, element.text)

    def to_xml(self):
        if not self.value or len(self.value) < 1:
            return None

        result = ET.Element(self.tag_name)
        result.text = self.value
        return result


class TextPropertyRequired(ElementProperty):
    """Same as TextProperty but returns an empty element rather then None in case the passed element's value is empty or None"""
    value_types = (str)

    def __init__(self, tag_name: str = "Name", value=None):
        super().__init__(tag_name, value or "")

    @staticmethod
    def from_xml(element: ET.Element):
        return TextPropertyRequired(element.tag, element.text)

    def to_xml(self):
        result = ET.Element(self.tag_name)
        if self.value or len(self.value) != 0:
            result.text = self.value

        return result


class ColorProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name, value or [0, 0, 0])

    @staticmethod
    def from_xml(element: ET.Element):
        if not all(x in element.attrib.keys() for x in ["r", "g", "b"]):
            return ColorProperty.read_value_error(element)

        return ColorProperty(element.tag, [float(element.get("r")), float(element.get("g")), float(element.get("b"))])

    def to_xml(self):
        r = str(int(self.value.r))
        g = str(int(self.value.g))
        b = str(int(self.value.b))
        return ET.Element(self.tag_name, attrib={"r": r, "g": g, "b": b})


class Vector2Property(ElementProperty):
    value_types = (Vector)

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name, value or Vector((0, 0)))

    @staticmethod
    def from_xml(element: ET.Element):
        if not all(x in element.attrib.keys() for x in ["x", "y"]):
            return VectorProperty.read_value_error(element)

        return VectorProperty(element.tag, Vector((float(element.get("x")), float(element.get("y")))))

    def to_xml(self):
        x = str(float32(self.value.x))
        y = str(float32(self.value.y))
        return ET.Element(self.tag_name, attrib={"x": x, "y": y})


class VectorProperty(ElementProperty):
    value_types = (Vector)

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name, value or Vector((0, 0, 0)))

    @staticmethod
    def from_xml(element: ET.Element):
        if not all(x in element.attrib.keys() for x in ["x", "y", "z"]):
            return VectorProperty.read_value_error(element)

        return VectorProperty(element.tag, Vector((float(element.get("x")), float(element.get("y")), float(element.get("z")))))

    def to_xml(self):
        x = str(float32(self.value.x))
        y = str(float32(self.value.y))
        z = str(float32(self.value.z))
        return ET.Element(self.tag_name, attrib={"x": x, "y": y, "z": z})


class Vector4Property(ElementProperty):
    value_types = (Vector)

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name, value or Vector((0, 0, 0, 0)))

    @staticmethod
    def from_xml(element: ET.Element):
        if not all(x in element.attrib.keys() for x in ["x", "y", "z", "w"]):
            return VectorProperty.read_value_error(element)

        return VectorProperty(element.tag, Vector((float(element.get("x")), float(element.get("y")), float(element.get("z")), float(element.get("w")))))

    def to_xml(self):
        x = str(float32(self.value.x))
        y = str(float32(self.value.y))
        z = str(float32(self.value.z))
        w = str(float32(self.value.w))
        return ET.Element(self.tag_name, attrib={"x": x, "y": y, "z": z, "w": w})


class QuaternionProperty(ElementProperty):
    value_types = (Quaternion)

    def __init__(self, tag_name: str, value=None):
        super().__init__(tag_name, value or Quaternion())

    @staticmethod
    def from_xml(element: ET.Element):
        if not all(x in element.attrib.keys() for x in ["x", "y", "z", "w"]):
            QuaternionProperty.read_value_error(element)

        return QuaternionProperty(element.tag, Quaternion((float(element.get("w")), float(element.get("x")), float(element.get("y")), float(element.get("z")))))

    def to_xml(self):
        x = str(float32(self.value.x))
        y = str(float32(self.value.y))
        z = str(float32(self.value.z))
        w = str(float32(self.value.w))
        return ET.Element(self.tag_name, attrib={"x": x, "y": y, "z": z, "w": w})


class MatrixProperty(ElementProperty):
    value_types = (Matrix)
    size = 4

    def __init__(self, tag_name: str, value=None, size=4):
        super().__init__(tag_name, value or Matrix())
        self.size = size

    @staticmethod
    def from_xml(element: ET.Element):
        s_mtx = element.text.strip().replace("\n", "").split("   ")
        s_mtx = [s for s in s_mtx if s]  # removes empty strings
        m = Matrix()
        r_idx = 0
        for item in s_mtx:
            v_idx = 0
            for value in item.strip().split(" "):
                m[r_idx][v_idx] = float(value)
                v_idx += 1
            r_idx += 1
        return MatrixProperty(element.tag, m)

    def to_xml(self):
        txt = "\n"
        for i in range(self.size):
            txt += f"{str(self.value[i][0])} "
            txt += f"{str(self.value[i][1])} "
            txt += f"{str(self.value[i][2])} "
            txt += f"{str(self.value[i][3])}"
            txt += "\n"
        element = ET.Element(self.tag_name)
        element.text = txt
        return element


class FlagsProperty(ElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str = "Flags", value=None):
        super().__init__(tag_name, value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = FlagsProperty(element.tag, [])
        if element.text and len(element.text.strip()) > 0:
            text = element.text.replace(" ", "").split(",")
            if not len(text) > 0:
                return FlagsProperty.read_value_error(element)

            for flag in text:
                new.value.append(flag)

        return new

    def to_xml(self):
        if len(self.value) < 1:
            return None

        element = ET.Element(self.tag_name)
        for item in self.value:
            # Should be a list of strings
            if not isinstance(item, str):
                return TypeError("FlagsProperty can only contain str objects!")

        if len(self.value) > 0:
            element.text = ", ".join(self.value)
        return element


class ValueProperty(ElementProperty):
    value_types = (int, str, bool, float)

    def __init__(self, tag_name: str, value=0):
        super().__init__(tag_name, value)

    @staticmethod
    def from_xml(element: ET.Element):
        if not "value" in element.attrib:
            ValueProperty.read_value_error(element)

        return ValueProperty(element.tag, get_str_type(element.get("value")))

    def to_xml(self):
        value = self.value
        if type(value) is int:
            value = int(self.value)
        elif type(value) is float:
            value = int(self.value) if self.value.is_integer(
            ) else float32(self.value)
        return ET.Element(self.tag_name, attrib={"value": str(value)})


class TextListProperty(ElementProperty):
    """Separates each word of an element's text into a list"""
    value_types = (list)

    def __init__(self, tag_name, value=None):
        super().__init__(tag_name, value or [])

    @staticmethod
    def from_xml(element):
        return TextListProperty(element.tag, value=element.text.split(" "))

    def to_xml(self):
        if not self.value or len(self.value) < 1:
            return None

        elem = ET.Element(self.tag_name)
        elem.text = " ".join(self.value)
        return elem
