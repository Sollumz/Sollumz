from mathutils import Vector
import numpy


class StringHelper():

    @staticmethod
    def FixShaderName(name):
        if("." in name):
            name = name[:-4]
        return name


class ListHelper():

    @staticmethod
    def divide_list(list, d):
        result = []
        for item in list:
            answer = item / d
            result.append(answer)
        return result

    @staticmethod
    def float32_list(list):
        result = []
        for item in list:
            result.append(numpy.float32(item))
        return result


class VectorHelper():

    @staticmethod
    def subtract_from_vector(v, f):
        r = Vector((0, 0, 0))
        r.x = v.x - f
        r.y = v.y - f
        r.z = v.z - f
        return r

    @staticmethod
    def add_to_vector(v, f):
        r = Vector((0, 0, 0))
        r.x = v.x + f
        r.y = v.y + f
        r.z = v.z + f
        return r

    @staticmethod
    def get_min_vector(v, c):
        r = Vector((0, 0, 0))
        r.x = min(v.x, c.x)
        r.y = min(v.y, c.y)
        r.z = min(v.z, c.z)
        return r

    @staticmethod
    def get_max_vector(v, c):
        r = Vector((0, 0, 0))
        r.x = max(v.x, c.x)
        r.y = max(v.y, c.y)
        r.z = max(v.z, c.z)
        return r
