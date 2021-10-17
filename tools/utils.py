import numpy
from io import StringIO

def ReadQuaternion(node):
    return [float(node.attrib["x"]), float(node.attrib["y"]), float(node.attrib["z"]), float(node.attrib["w"])]

def StringToFloatList(string):
    return numpy.loadtxt(StringIO(string), delimiter=', ') #https://numpy.org/doc/stable/reference/generated/numpy.loadtxt.html

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

def FixShaderName(name):
    if("." in name):
        name = name[:-4]
    return name