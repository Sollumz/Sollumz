from mathutils import Vector


def distance_point_to_line(start: Vector, end: Vector, point: Vector) -> float:
    L = (end - start).length
    if L == 0.0:
        return (point - start).length
    A = (point - start).cross(point - end).length
    return A / L
