"""Manages reading/writing Codewalker XML files"""

from abc import abstractmethod, ABC, abstractclassmethod
from dataclasses import dataclass
from typing import Any
from mathutils import Vector, Quaternion
from xml.etree import ElementTree as ET

# Custom indentation to get elements like <XMLVerticesList /> to output nicely
def indent(elem: ET.Element, level=0):
    amount = "  "
    i = "\n" + level*amount
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + amount
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

        # Indent innertext of elements on new lines. Used in cases like <XMLVerticesList />
        if elem.text and len(elem.text.strip()) > 0 and elem.text.find('\n') != -1:
            lines = elem.text.strip().split('\n')
            for index, line in enumerate(lines):
                print(line)
                lines[index] = ((level + 1) * amount) + line
            elem.text = '\n' + '\n'.join(lines) + i


"""Abstract XML element to base all other XML elements off of"""
class XMLElement(ABC):
    def __init__(self, tag_name):
        self.tag_name = tag_name

    @classmethod
    def read_value_error(cls):
        return ValueError(f"Invalid XML element for type '{cls.__name__}'!")

    """Convert ET.Element object to XMLElement"""
    @abstractclassmethod
    def from_xml(cls, element: ET.Element):
        pass
    
    """Convert object to ET.Element object"""
    @abstractmethod
    def to_xml(self):
        pass
    
    """Write object as XML to filepath"""
    def write_xml(self, filepath):
        element = self.to_xml()
        indent(element)
        elementTree = ET.ElementTree(element)
        # ET.indent(element)
        elementTree.write(filepath, encoding="UTF-8", xml_declaration=True)


"""XML element that contains children defined by it's properties"""
class XMLElementTree(XMLElement):
    def __init__(self, tag_name: str):
        super().__init__(tag_name)
    
    """Convert ET.Element object to XMLElementTree"""
    @classmethod
    def from_xml(cls, element: ET.Element):
        new = cls()

        for child in element.iter():
            for prop_name, obj_element in vars(new).items:
                if isinstance(obj_element, XMLElement):
                    # Add element to object if tag is defined in class definition
                    if obj_element.tag_name == child.tag:
                        setattr(new, prop_name, type(obj_element).from_xml(child))
                elif isinstance(obj_element, XMLAttributeProperty):
                    # Add attribute to element if attribute is defined in class definition
                    if obj_element.name in child.attrib:
                        obj_element.value = child[obj_element.name]

    
    """Convert XMLElementTree to ET.Element object"""
    def to_xml(self):
        root = ET.Element(self.tag_name)
        for child in vars(self).values():
            if isinstance(child, XMLElement):
                root.append(child.to_xml())
            elif isinstance(child, XMLAttributeProperty):
                root.set(child.name, child.value)

        return root

    def __getattribute__(self, key: str, onlyValue: bool=True):
        obj = None
        # Try and see if key exists
        try:
            obj = object.__getattribute__(self, key)
            if isinstance(obj, (XMLElementProperty, XMLAttributeProperty)) and onlyValue:
                # If the property is an XMLElementProperty or XMLAttributeProperty, and onlyValue is true, return just the value of the XMLElement property
                return obj.value
            else:
                return obj
        except AttributeError:
            # Key doesn't exist, return None
            return None
    
    def __setattr__(self, name: str, value) -> None:
        # Get the full object
        obj = self.__getattribute__(name, False)
        if obj and isinstance(obj, (XMLElementProperty, XMLAttributeProperty)):
            # If the object is an XMLElementProperty or XMLAttributeProperty, set it's value
            obj.value = value
            super().__setattr__(name, obj)
        else:
            super().__setattr__(name, value)

    def get_element(self, key):
        obj = self.__getattribute__(key, False)

        if isinstance(obj, XMLElementProperty):
       
            return obj
    

@dataclass
class XMLAttributeProperty:
    name: str
    _value: Any = ''

    @property
    def value(self):
        return str(self._value)
    
    @value.setter
    def value(self, new_value):
        self._value = str(new_value)


class XMLElementProperty(XMLElement, ABC):
    value_types = (None)

    """Convert ET.Element to XMLElementProperty"""
    @abstractclassmethod
    def from_xml(cls, element: ET.Element):
        pass

    
    """Convert XMLElementProperty to ET.Element object"""
    @abstractmethod
    def to_xml(self):
        pass


    def __init__(self, tag_name: str, value):
        super().__init__(tag_name)
        if value and not isinstance(value, self.value_types):
            raise TypeError(f'Value of {type(self).__name__} must be one of {self.value_types}, not {type(value)}!')
        self.value = value


class XMLVector(XMLElementProperty):
    value_types = (Vector)

    def __init__(self, tag_name: str, value = None):
        super().__init__(tag_name, value or Vector((0, 0, 0)))

    @staticmethod
    def from_xml(element: ET.Element):
        if not all(x in element.attrib.keys() for x in ['x', 'y', 'z']):
            return XMLElement.read_value_error()

        return XMLVector(element.tag, Vector((element.get('x'),element.get('y'),element.get('z'))))

    def to_xml(self):
        return ET.Element(self.tag_name, attrib={'x': str(self.value.x), 'y': str(self.value.y), 'z': str(self.value.z)})
    

class XMLQuaternion(XMLElementProperty):
    value_types = (Quaternion)

    def __init__(self, tag_name: str, value = None):
        super().__init__(tag_name, value or Quaternion((0, 0, 0), 1))

    @staticmethod
    def from_xml(element: ET.Element):
        if not all(x in element.attrib.keys() for x in ['x', 'y', 'z', 'w']):
            XMLElement.read_value_error()

        return XMLQuaternion(element.tag, Vector((element.get('x'),element.get('y'),element.get('z'), element.get('w'))))

    def to_xml(self):
        return ET.Element(self.tag_name, attrib={'x': str(self.value.x), 'y': str(self.value.y), 'z': str(self.value.z)})


class XMLList(XMLElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str, list_type: XMLElement, value = None):
        super().__init__(tag_name, value or [])
        if not issubclass(list_type, XMLElement):
            raise TypeError('XMLList can only hold XMLElements!')
        self.list_type = list_type

    @staticmethod
    def from_xml(element: ET.Element, list_type: XMLElement):
        new = XMLList(element.tag, list_type)
        for child in element.iter():
            new.value.append(list_type.from_xml(child))
        return new


    def to_xml(self):
        element = ET.Element(self.tag_name)
        for item in self.value:
            if isinstance(item, self.list_type):
                element.append(item.to_xml())
        return element


class XMLVerticesList(XMLElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str = 'Vertices', value = None):
        super().__init__(tag_name, value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = XMLVerticesList(element.tag, [])
        text = element.text.strip().split('\n')
        if not len(text) > 0:
            return XMLElement.read_value_error()

        for line in text:
            coords = enumerate(line.strip(','))
            if not len(coords) == 3:
                return XMLElement.read_value_error()
            new.value.append(Vector(coords[0], coords[1], coords[2]))
        
        return new


    def to_xml(self):
        element = ET.Element(self.tag_name)
        element.text = '\n'
        for vertex in self.value:
            # Should be a list of Vectors
            if not isinstance(vertex, Vector):
                raise TypeError('XMLVerticesList can only contain Vector objects!')
            for index, component in enumerate(vertex):
                element.text += str(component)
                if index < len(vertex) - 1:
                    element.text += ', '
            element.text += '\n'

        return element


class XMLFlags(XMLElementProperty):
    value_types = (list)

    def __init__(self, tag_name: str = 'Flags', value = None):
        super().__init__(tag_name, value or [])

    @staticmethod
    def from_xml(element: ET.Element):
        new = XMLVerticesList(element.tag, [])
        text = element.text.strip().split('\n')
        if not len(text) > 0:
            return XMLElement.read_value_error()

        for line in text:
            coords = enumerate(line.strip(','))
            if not len(coords) == 3:
                return XMLElement.read_value_error()
            new.value.append(Vector(coords[0], coords[1], coords[2]))
        
        return new


    def to_xml(self):
        element = ET.Element(self.tag_name)
        for item in self.value:
            # Should be a list of strings
            if not isinstance(item, str):
                return TypeError('XMLFlags can only contain str objects!')

        if len(self.value) > 0:
            element.text = ','.join(self.value)
        return element


class XMLValue(XMLElementProperty):
    value_types = (int, str, bool, float)

    def __init__(self, tag_name: str, value):
        super().__init__(tag_name, value)

    @staticmethod
    def from_xml(element: ET.Element):
        if not 'value' in element.attrib:
            XMLElement.read_value_error()

        return XMLValue(element.tag, element.get('value'))

    def to_xml(self):
        return ET.Element(self.tag_name, attrib={'value': str(self.value)})