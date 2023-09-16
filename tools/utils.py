import os
import numpy
from numpy.typing import NDArray
from math import sqrt
from typing import Iterable, Tuple
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


def float32_tuple(items: Iterable):
    """Cast all ``items`` to float32 and return a tuple containing the items."""
    result: list[numpy.float32] = []

    for item in items:
        result.append(numpy.float32(item))

    return tuple(result)


def abs_vector(v):
    return Vector((abs(v.x), abs(v.y), abs(v.z)))


def vector_inv(v):
    r = Vector((0, 0, 0))
    r.x = 1 / v.x if v.x != 0 else 0
    r.y = 1 / v.y if v.y != 0 else 0
    r.z = 1 / v.z if v.z != 0 else 0
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


def get_min_vector_list(vecs: list[Vector]):
    """Get a Vector composed of the smallest components of all given Vectors."""
    if not vecs:
        return Vector()

    x = []
    y = []
    z = []
    for v in vecs:
        x.append(v[0])
        y.append(v[1])
        z.append(v[2])
    return Vector((min(x), min(y), min(z)))


def get_max_vector_list(vecs: list[Vector]):
    """Get a Vector composed of the largest components of all given Vectors."""
    if not vecs:
        return Vector()

    x = []
    y = []
    z = []
    for v in vecs:
        x.append(v[0])
        y.append(v[1])
        z.append(v[2])
    return Vector((max(x), max(y), max(z)))


def get_distance_of_vectors(a, b):
    locx = b.x - a.x
    locy = b.y - a.y
    locz = b.z - a.z

    distance = sqrt((locx) ** 2 + (locy) ** 2 + (locz) ** 2)
    return distance


def get_direction_of_vectors(a, b):
    direction = (a - b).normalized()
    axis_align = Vector((0.0, 0.0, 1.0))

    if a == b:
        direction = axis_align

    angle = axis_align.angle(direction)
    axis = axis_align.cross(direction)

    q = Quaternion(axis, angle)

    return q.to_euler("XYZ")


def multiply_homogeneous(m: Matrix, v: Vector):
    """Multiply a 4x4 matrix by a 3d vector and get a 3d vector out. Takes the
    resulting 4d vector and divides by the homogeneous coordinate 'w' to get a 3d vector."""
    x = (((m[0][0] * v.x) + (m[1][0] * v.y)) + (m[2][0] * v.z)) + m[3][0]
    y = (((m[0][1] * v.x) + (m[1][1] * v.y)) + (m[2][1] * v.z)) + m[3][1]
    z = (((m[0][2] * v.x) + (m[1][2] * v.y)) + (m[2][2] * v.z)) + m[3][2]
    w = (((m[0][3] * v.x) + (m[1][3] * v.y)) + (m[2][3] * v.z)) + m[3][3]
    iw = 1.0 / abs(w)
    return Vector((x * iw, y * iw, z * iw))


def list_index_exists(ls, i):
    return (0 <= i < len(ls)) or (-len(ls) <= i < 0)


def prop_array_to_vector(prop, size=3):
    if size == 4:
        return Quaternion((prop[0], prop[1], prop[2], prop[3]))
    return Vector((prop[0], prop[1], prop[2]))


def get_filename(filepath: str):
    """Get file name from path without extension."""
    return os.path.basename(filepath).split(".")[0]


def np_arr_to_str(arr: NDArray, fmt: str):
    """Convert numpy array to formatted string (faster than np.savetxt)"""
    n_fmt_chars = fmt.count('%')

    if arr.ndim == 1 and n_fmt_chars == 1:
        fmt = ' '.join([fmt] * arr.size)
    else:
        if n_fmt_chars == 1:
            fmt = ' '.join([fmt] * arr.shape[1])

        fmt = '\n'.join([fmt] * arr.shape[0])

    return fmt % tuple(arr.ravel())


def get_matrix_without_scale(matrix: Matrix) -> Matrix:
    """Apply scale to transformation matrix"""
    scale = matrix.to_scale()
    return matrix @ Matrix.Diagonal(scale).inverted().to_4x4()


def reshape_mat_3x4(mat_4x4: Matrix):
    return Matrix((
        mat_4x4[0],
        mat_4x4[1],
        mat_4x4[2],
    ))


def reshape_mat_4x3(mat_4x4: Matrix):
    return Matrix((
        mat_4x4[0][:3],
        mat_4x4[1][:3],
        mat_4x4[2][:3],
        mat_4x4[3][:3],
    ))


def color_hash(data: str) -> Tuple[float, float, float, float]:
    from hashlib import md5

    m = md5(usedforsecurity=False)
    m.update(data.encode("utf-8"))
    data_hash = m.digest()
    r = data_hash[0] / 255
    g = data_hash[1] / 255
    b = data_hash[2] / 255
    return r, g, b, 1.0
