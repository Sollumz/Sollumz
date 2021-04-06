from xml.etree.ElementTree import Element
from mathutils import Vector, Quaternion

def ReadValue(node, default=None, formatter=lambda x: x):
    if node is None:
        return default

    if 'value' not in node.attrib:
        return default

    return formatter(node.attrib['value'])

def ReadText(node, default=None, formatter=lambda x: x):
    if node is None:
        return default

    if node.text is None:
        return default

    return formatter(node.text)

def ReadVector(node, default=None, formatter=lambda x: x):
    if node is None:
        return default

    try:
        x = float(node.get('x'))
        y = float(node.get('y'))
        z = float(node.get('z'))
    except ValueError:
        return default

    return formatter(Vector((x, y, z)))

def ReadQuaternion(node, default=None, formatter=lambda x: x):
    if node is None:
        return default

    try:
        x = float(node.get('x'))
        y = float(node.get('y'))
        z = float(node.get('z'))
        w = float(node.get('w'))
    except ValueError:
        return default

    return formatter(Quaternion((w, x, y, z)))

def CreateNode(name, parent=None):
    node = Element(name)

    if parent is not None:
        parent.append(node)

    return node


def CreateTextNode(name, text, parent=None):
    node = CreateNode(name, parent)
    node.text = str(text)

    return node

def CreateValueNode(name, value, parent=None):
    node = CreateNode(name, parent)
    node.set('value', str(value))

    return node
