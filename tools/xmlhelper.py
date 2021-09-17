import xml.etree.ElementTree as ET

def ReadInt(node):
    return int(node.attrib["value"])

def ReadFloat(node):
    return float(node.attrib["value"])

def ReadVector(node):
    return [float(node.attrib["x"]), float(node.attrib["y"]), float(node.attrib["z"])]

def ReadQuaternion(node):
    return [float(node.attrib["x"]), float(node.attrib["y"]), float(node.attrib["z"]), float(node.attrib["w"])]

def StringListToFloatList(lst):
    result = []
    for num in lst:
        result.append(float(num))
    return result

def StringListToIntList(lst):
    result = []
    for num in lst:
        result.append(int(num))
    return result

def WriteType(node, type):
    node.set("type", type)

def WriteValue(node, value):
    node.set("value", str(value))

def WriteVector(node, vector):
    node.set("x", str(vector[0]))
    node.set("y", str(vector[1]))
    node.set("z", str(vector[2]))

def WriteQuaternion(node, quaternion):
    node.set("x", str(quaternion[0]))
    node.set("y", str(quaternion[1]))
    node.set("z", str(quaternion[2]))
    node.set("w", str(quaternion[2]))

def WriteClass(object):
    class_type = type(object)
    root = ET.Element(class_type.__name__)

    for prop in dir(object):
        var = getattr(object, prop)
        print("")
        print(prop)
        print(type(var))
        print(var)

    return root


