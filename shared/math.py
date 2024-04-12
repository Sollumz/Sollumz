from mathutils import Vector

def distance_point_to_line(start: Vector, end: Vector, point: Vector) -> float:
    A = (point - start).cross(point - end).length
    L = (end - start).length
    return A / L
