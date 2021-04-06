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

def WriteClass(object):
    print("WIP")
