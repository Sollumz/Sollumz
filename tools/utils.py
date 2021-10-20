import numpy
from io import StringIO

def ReadQuaternion(node):
    return [float(node.attrib["x"]), float(node.attrib["y"]), float(node.attrib["z"]), float(node.attrib["w"])]

#def StringToFloatList(string):
    #return numpy.loadtxt(StringIO(string), delimiter=', ') #https://numpy.org/doc/stable/reference/generated/numpy.loadtxt.html

def StringListToFloatList(lst, colors = False):
    result = []
    for num in lst:
        if colors:
            result.append(float(num) / 255)
        else:
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

def vector_tostring(vector):
    string = [str(vector.x), str(vector.y)]
    if(hasattr(vector, "z")):
        string.append(str(vector.z))

    if(hasattr(vector, "w")):
        string.append(str(vector.w))

    return " ".join(string)

def meshloopcolor_tostring(color):
    string = " ".join(str(round(color[i] * 255)) for i in range(4))
    return string 