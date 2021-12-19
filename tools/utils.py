from mathutils import Vector
import numpy
from math import inf, sqrt
from mathutils import Vector, Quaternion, Matrix


def get_list_item(list, index):
    """Get item of list without the risk of an error being thrown"""
    if 0 <= index < len(list):
        return list[index]
    else:
        return None


def flag_list_to_int(flag_list):
    flags = 0
    for i, enabled in enumerate(flag_list):
        if enabled == True:
            flags += (1 << i)
    return flags


def int_to_bool_list(num, size=None):
    return [bool(num & (1 << n)) for n in range(size or 32)]


def flag_prop_to_list(prop_type, data_block, size=None):
    size = (size or 32) + 1
    flags = [False] * size
    i = 0
    for flag_name in prop_type.__annotations__:
        if i < size:
            if flag_name in data_block:
                flags[i] = data_block[flag_name] != 0
        i += 1
    return flags


def divide_list(list, d):
    result = []
    for item in list:
        answer = item / d
        result.append(answer)
    return result


def float32_list(list):
    result = []
    for item in list:
        result.append(numpy.float32(item))
    return result


def abs_vector(v):
    return Vector((abs(v.x), abs(v.y), abs(v.z)))


def divide_vector_inv(v):
    r = Vector((0, 0, 0))
    r.x = 1 / v.x
    r.y = 1 / v.y
    r.z = 1 / v.z
    return r


def subtract_from_vector(v, f):
    r = Vector((0, 0, 0))
    r.x = v.x - f
    r.y = v.y - f
    r.z = v.z - f
    return r


def add_to_vector(v, f):
    r = Vector((0, 0, 0))
    r.x = v.x + f
    r.y = v.y + f
    r.z = v.z + f
    return r


def get_min_vector(v, c):
    r = Vector((0, 0, 0))
    r.x = min(v.x, c.x)
    r.y = min(v.y, c.y)
    r.z = min(v.z, c.z)
    return r


def get_max_vector(v, c):
    r = Vector((0, 0, 0))
    r.x = max(v.x, c.x)
    r.y = max(v.y, c.y)
    r.z = max(v.z, c.z)
    return r


def get_min_vector_list(vecs):
    x = []
    y = []
    z = []
    for v in vecs:
        x.append(v[0])
        y.append(v[1])
        z.append(v[2])
    return Vector((min(x), min(y), min(z)))


def get_max_vector_list(vecs):
    x = []
    y = []
    z = []
    for v in vecs:
        x.append(v[0])
        y.append(v[1])
        z.append(v[2])
    return Vector((max(x), max(y), max(z)))


def add_vector_list(list1, list2):
    x = list1[0] + list2[0]
    y = list1[1] + list2[1]
    z = list1[2] + list2[2]
    return [x, y, z]


def subtract_vector_list(list1, list2):
    x = list1[0] - list2[0]
    y = list1[1] - list2[1]
    z = list1[2] - list2[2]
    return [x, y, z]


def multiple_vector_list(list, num):
    x = list[0] * num
    y = list[1] * num
    z = list[2] * num
    return [x, y, z]


def get_vector_list_length(list):
    sx = list[0] ** 2
    sy = list[1] ** 2
    sz = list[2] ** 2
    length = (sx + sy + sz) ** 0.5
    return length


def divide_vectors(a, b):
    return Vector((a.x/b.x, a.y/b.y, a.z/b.z))


def get_closest_axis_point(axis, center, points):

    closest = None
    closestDist = inf

    for p in points:

        rel = (p - center).normalized()
        dist = (rel - axis).length

        if dist < closestDist:
            closest = p
            closestDist = dist

    return closest


def get_distance_of_vectors(a, b):
    locx = b.x - a.x
    locy = b.y - a.y
    locz = b.z - a.z

    distance = sqrt((locx) ** 2 + (locy) ** 2 + (locz) ** 2)
    return distance


def get_direction_of_vectors(a, b):
    direction = (a - b).normalized()
    axis_align = Vector((0.0, 0.0, 1.0))

    angle = axis_align.angle(direction)
    axis = axis_align.cross(direction)

    q = Quaternion(axis, angle)

    return q.to_euler("XYZ")


def lookatlh(eye, target, up):
    mz = Vector((eye[0]-target[0], eye[1]-target[1], eye[2] -
                target[2])).normalized()  # inverse line of sight
    mx = Vector(up.cross(mz)).normalized()
    my = Vector(mz.cross(mx)).normalized()
    tx = mx.dot(eye)
    ty = my.dot(eye)
    tz = mz.dot(eye) * -1
    mat = Matrix()
    mat[0] = mx[0], mz[0], my[0], 0
    mat[1] = mx[2], mz[2], my[2], 0
    mat[2] = mx[1], mz[1], my[1], 0
    mat[3] = tx, tz, ty, 1

    return mat


def multiW(m, v):
    x = (((m[0][0] * v.x) + (m[1][0] * v.y)) + (m[2][0] * v.z)) + m[3][0]
    y = (((m[0][1] * v.x) + (m[1][1] * v.y)) + (m[2][1] * v.z)) + m[3][1]
    z = (((m[0][2] * v.x) + (m[1][2] * v.y)) + (m[2][2] * v.z)) + m[3][2]
    w = (((m[0][3] * v.x) + (m[1][3] * v.y)) + (m[2][3] * v.z)) + m[3][3]
    iw = 1.0 / abs(w)
    return Vector((x * iw, y * iw, z * iw))
