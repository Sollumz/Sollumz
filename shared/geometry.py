"""
Various functions related to geometry math.
"""
import numpy as np
from numpy.typing import NDArray
from mathutils import Vector
from typing import NamedTuple
from collections.abc import Sequence


class Centroid(NamedTuple):
    centroid: Vector
    radius_around_centroid: float


class MassProperties(NamedTuple):
    volume: float
    center_of_gravity: Vector
    inertia: Vector


def get_centroid_of_cylinder(radius: float, length: float) -> Centroid:
    half_length = length * 0.5

    # Assume a cylinder placed at origin
    centroid = Vector((0.0, 0.0, 0.0))

    # For cylinders the radius of the sphere that circumscribes the cylinder is equal to
    # half the diagonal of the cylinder
    # diagonal = length of hypotenuse of a right triangle with sides equal to cylinder
    #            diameter and length (or radius and half length)
    radius_around_centroid = np.sqrt(radius * radius + half_length * half_length)

    return Centroid(centroid, radius_around_centroid)


def get_mass_properties_of_cylinder(radius: float, length: float) -> MassProperties:
    radius2 = radius * radius
    length2 = length * length

    # Assume a cylinder placed at origin
    cg = Vector((0.0, 0.0, 0.0))

    volume = np.pi * radius2 * length

    # https://scienceworld.wolfram.com/physics/MomentofInertiaCylinder.html
    ixx = length2 / 12 + radius2 / 4
    iyy = radius2 / 2
    izz = ixx
    inertia = Vector((ixx, iyy, izz))

    return MassProperties(volume, cg, inertia)


def get_centroid_of_disc(radius: float) -> Centroid:
    # Assume a disc placed at origin
    centroid = Vector((0.0, 0.0, 0.0))

    # For discs just the radius is used for radius_around_centroid, unlike cylinders
    radius_around_centroid = radius

    return Centroid(centroid, radius_around_centroid)


def get_mass_properties_of_disc(radius: float, length: float) -> MassProperties:
    # Disc mass properties are the same as a cylinder
    return get_mass_properties_of_cylinder(radius, length)


def get_centroid_of_capsule(radius: float, length: float) -> Centroid:
    half_length = length * 0.5

    # Assume a capsule placed at origin
    centroid = Vector((0.0, 0.0, 0.0))
    radius_around_centroid = half_length + radius

    return Centroid(centroid, radius_around_centroid)


def get_mass_properties_of_capsule(radius: float, length: float) -> MassProperties:
    radius2 = radius * radius
    radius3 = radius2 * radius
    length2 = length * length
    length3 = length2 * length

    # Assume a capsule placed at origin
    cg = Vector((0.0, 0.0, 0.0))

    # volume capsule = volume cylinder + sphere
    volume_sphere = (4 / 3) * np.pi * radius3
    volume_cylinder = np.pi * radius2 * length
    volume = volume_cylinder + volume_sphere

    # https://www.wolframalpha.com/input?i=moment+of+inertia+of+a+capsule
    ixx = (5 * length3 + 20 * length2 * radius + 45 * length * radius2 + 32 * radius3) / (60 * length + 80 * radius)
    iyy = (radius2 * (15 * length + 16 * radius)) / (30 * length + 40 * radius)
    izz = ixx
    inertia = Vector((ixx, iyy, izz))

    return MassProperties(volume, cg, inertia)


def get_centroid_of_sphere(radius: float) -> Centroid:
    # Assume a sphere placed at origin
    centroid = Vector((0.0, 0.0, 0.0))
    radius_around_centroid = radius

    return Centroid(centroid, radius_around_centroid)


def get_mass_properties_of_sphere(radius: float) -> MassProperties:
    radius2 = radius * radius
    radius3 = radius2 * radius

    # Assume a sphere placed at origin
    cg = Vector((0.0, 0.0, 0.0))

    volume = (4 / 3) * np.pi * radius3

    # https://scienceworld.wolfram.com/physics/MomentofInertiaSphere.html
    ixx = iyy = izz = 2 * radius2 / 5
    inertia = Vector((ixx, iyy, izz))

    return MassProperties(volume, cg, inertia)


def get_centroid_of_box(box_min: Vector, box_max: Vector) -> Centroid:
    # Assume a box placed at origin
    centroid = Vector((0.0, 0.0, 0.0))
    radius_around_centroid = 0.5 * (box_max - box_min).length

    return Centroid(centroid, radius_around_centroid)


def get_mass_properties_of_box(box_min: Vector, box_max: Vector) -> MassProperties:
    x, y, z = box_max - box_min
    x2, y2, z2 = x * x, y * y, z * z

    # Assume a box placed at origin
    cg = Vector((0.0, 0.0, 0.0))

    volume = x * y * z

    # moment of inertia of a solid rectangular cuboid
    # https://en.wikipedia.org/wiki/List_of_moments_of_inertia#List_of_3D_inertia_tensors
    ixx = (y2 + z2) / 12
    iyy = (z2 + x2) / 12
    izz = (x2 + y2) / 12
    inertia = Vector((ixx, iyy, izz))

    return MassProperties(volume, cg, inertia)


def _bounding_ball_ritter(points: NDArray[np.float64]):
    """
    Compute a tight bounding ball using Ritter's algorithm.
    Returns the center and squared radius. The result is typically within a few percent
    of the minimum enclosing ball, which is sufficient for collision bound spheres.
    """
    n = len(points)
    if n == 0:
        return np.zeros(points.shape[1]), 0.0
    if n == 1:
        return points[0].copy(), 0.0

    # Find approximate diameter, pick arbitrary point, find farthest, find farthest from that
    dists_sq = np.sum((points - points[0]) ** 2, axis=1)
    i = np.argmax(dists_sq)
    dists_sq = np.sum((points - points[i]) ** 2, axis=1)
    j = np.argmax(dists_sq)

    # Initial ball from diameter endpoints
    center = (points[i] + points[j]) * 0.5
    radius_sq = np.sum((points[i] - center) ** 2)

    # Expand ball to include all points
    for _ in range(50):
        dists_sq = np.sum((points - center) ** 2, axis=1)
        max_idx = np.argmax(dists_sq)
        max_dist_sq = dists_sq[max_idx]
        if max_dist_sq <= radius_sq * (1 + 1e-10):
            break

        max_dist = np.sqrt(max_dist_sq)
        radius = np.sqrt(radius_sq)
        new_radius = (radius + max_dist) * 0.5
        shift_ratio = (new_radius - radius) / max_dist
        center = center + (points[max_idx] - center) * shift_ratio
        radius_sq = new_radius * new_radius

    return center, radius_sq


def get_centroid_of_mesh(mesh_vertices) -> Centroid:
    mesh_vertices = np.asarray(mesh_vertices, dtype=np.float64)

    C, r2 = _bounding_ball_ritter(mesh_vertices)

    centroid = Vector(C)
    radius_around_centroid = np.sqrt(r2)
    return Centroid(centroid, radius_around_centroid)


def get_mass_properties_of_mesh(mesh_vertices, mesh_faces):
    triangles = mesh_vertices[mesh_faces]

    v0 = triangles[:, 0, :]
    v1 = triangles[:, 1, :]
    v2 = triangles[:, 2, :]

    tri_tetrahedron_volumes = (v0 * np.cross(v1, v2, axis=1)).sum(axis=1) / 6
    volume = abs(tri_tetrahedron_volumes.sum())

    if is_mesh_solid(mesh_vertices, mesh_faces):
        tri_tetrahedron_cgs = (v0 + v1 + v2) / 4
        tri_tetrahedron_cgs *= tri_tetrahedron_volumes[:, np.newaxis]
        cg = tri_tetrahedron_cgs.sum(axis=0) / volume
    else:
        # Since the mesh is open, we approximate the center of gravity with the average of the triangle
        # centroids scaled by their area.
        tri_areas = np.linalg.norm(np.cross(v0 - v1, v2 - v1, axis=1), axis=1) / 2
        tri_cgs = (v0 + v1 + v2) / 3
        tri_cgs *= tri_areas[:, np.newaxis]
        cg = tri_cgs.sum(axis=0) / tri_areas.sum()

    cg = Vector(cg)

    # Based on https://github.com/bulletphysics/bullet3/blob/e9c461b0ace140d5c73972760781d94b7b5eee53/src/BulletCollision/CollisionShapes/btConvexTriangleMeshShape.cpp#L236
    cg_np = np.array(cg, dtype=np.float64)
    a = v0 - cg_np
    b = v1 - cg_np
    c = v2 - cg_np

    # Per-axis: a^2 + b^2 + c^2 + a*b + a*c + b*c (simplification of the original formula
    # where each cross-term appeared twice with 0.05 coefficient, equivalent to once with 0.1)
    axis_sums = a * a + b * b + c * c + a * b + a * c + b * c  # (N_tris, 3)

    # i_pos[j] = vol * 0.1 * axis_sums[j] (negation of the original i[j] = -vol * 0.1 * ...)
    i_pos = tri_tetrahedron_volumes[:, np.newaxis] * 0.1 * axis_sums  # (N_tris, 3)
    i_sum = i_pos.sum(axis=0)  # (3,) = [sum_i00, sum_i11, sum_i22]

    ixx = (i_sum[1] + i_sum[2]) / volume
    iyy = (i_sum[2] + i_sum[0]) / volume
    izz = (i_sum[0] + i_sum[1]) / volume

    inertia = Vector((ixx, iyy, izz))
    return MassProperties(volume, cg, inertia)


def is_mesh_solid(mesh_vertices, mesh_faces) -> bool:
    """Gets whether the mesh is a closed oriented manifold."""
    faces = np.asarray(mesh_faces)

    e0 = faces[:, [0, 1]]
    e1 = faces[:, [1, 2]]
    e2 = faces[:, [2, 0]]
    edges = np.vstack([e0, e1, e2])

    edges_sorted = np.sort(edges, axis=1)

    _, counts = np.unique(edges_sorted, axis=0, return_counts=True)

    return bool(np.all(counts == 2))


def transform_inertia(inertia: Vector, mass: float, translation: Vector) -> Vector:
    """Uses Principal Axis Theorem to change the axis of a moment of inertia. Returns the new moment of intertia."""
    # https://dspace.mit.edu/bitstream/handle/1721.1/60691/16-07-fall-2004/contents/lecture-notes/d23.pdf
    ixx, iyy, izz = inertia

    dx, dy, dz = translation
    dx2 = dx * dx
    dy2 = dy * dy
    dz2 = dz * dz

    ixx += mass * (dy2 + dz2)
    iyy += mass * (dx2 + dz2)
    izz += mass * (dx2 + dy2)
    return Vector((ixx, iyy, izz))


def calculate_composite_inertia(
    root_cg: Vector,
    parts_cg: list[Vector],
    parts_mass: list[float],
    parts_inertia: list[Vector]
) -> Vector:
    assert len(parts_cg) == len(parts_mass)
    assert len(parts_cg) == len(parts_inertia)

    total_inertia = Vector((0.0, 0.0, 0.0))
    for cg, mass, inertia in zip(parts_cg, parts_mass, parts_inertia):
        cg_offset = cg - root_cg
        total_inertia += transform_inertia(inertia, mass, cg_offset)

    return total_inertia


NO_NEIGHBOR = -1


def shrink_mesh(mesh_vertices, mesh_faces):
    margin = 0.04

    bb_min = mesh_vertices.min(axis=0)
    bb_max = mesh_vertices.max(axis=0)
    half_size = (bb_max - bb_min) * 0.5

    margin = min(margin, *half_size)

    neighbors = _compute_neighbors(mesh_vertices, mesh_faces)

    shrunk_vertices = None
    while margin > 0.000001:
        shrunk_vertices = _try_shrink_mesh(mesh_vertices, mesh_faces, neighbors, margin)
        if shrunk_vertices is not None:
            break

        margin /= 2.0

    margin = max(margin, 0.025)

    return shrunk_vertices, margin


def _try_shrink_mesh(mesh_vertices, mesh_faces, neighbors, margin: float):
    shrunk_vertices = _shrink_polys(mesh_vertices, mesh_faces, neighbors, margin)

    num_polys = len(mesh_faces)
    num_verts = len(mesh_vertices)

    # Make sure that no polygons collide with each other
    for vert_idx in range(num_verts):
        vertex = mesh_vertices[vert_idx]
        shrunk_vertex = shrunk_vertices[vert_idx]

        segment_pos = Vector(shrunk_vertex)
        segment_dir = Vector(vertex - shrunk_vertex)
        segment_length = segment_dir.length
        segment_dir /= segment_length

        max_distance = segment_length

        def _intersect_test(v1, v2, v3):
            from mathutils import geometry
            intersect_pos = geometry.intersect_ray_tri(v1, v2, v3, segment_dir, segment_pos)
            if intersect_pos is None:
                return False

            distance = (intersect_pos - segment_pos).length
            return distance <= max_distance

        for poly_idx in range(num_polys):
            poly_verts = mesh_faces[poly_idx]

            # Intersection test is done against other polygons, so we must exclude polygons that share current vertex
            if (poly_verts == vert_idx).any():
                continue

            v1, v2, v3 = [Vector(mesh_vertices[vi]) for vi in poly_verts]
            if _intersect_test(v1, v2, v3):
                return None

            vs1, vs2, vs3 = [Vector(shrunk_vertices[vi]) for vi in poly_verts]
            if _intersect_test(vs1, vs2, vs3):
                return None

    return shrunk_vertices


def _shrink_polys(mesh_vertices, mesh_faces, neighbors, margin):
    # TODO: copied from rageAm's C++ code, very unoptimized Python code, vectorize with Numpy somehow
    from mathutils import geometry

    output_vertices = np.empty_like(mesh_vertices)
    processed_verts = set()
    num_polys = len(mesh_faces)
    poly_normals = [geometry.normal([mesh_vertices[vi] for vi in poly_verts]) for poly_verts in mesh_faces]
    neighbor_normals = []
    for poly_idx in range(num_polys):
        poly_verts = mesh_faces[poly_idx]
        normal = poly_normals[poly_idx]
        for poly_vert_idx, vert_idx in enumerate(poly_verts):
            if vert_idx in processed_verts:
                continue
            processed_verts.add(vert_idx)

            vertex = mesh_vertices[vert_idx]

            neighbor_normals.clear()

            # Compute average normal from all surrounding polygons (that share at least one vertex)
            # and all them in normal list for further weighted normal computation
            average_normal = Vector(normal)
            prev_neighbor_poly_idx = poly_idx

            # Find starting neighbor index
            neighbor_poly_idx = neighbors[poly_idx][(poly_vert_idx + 2) % 3]
            if neighbor_poly_idx == NO_NEIGHBOR:
                neighbor_poly_idx = neighbors[poly_idx][poly_vert_idx]

            # Search for neighbors and accumulate normal...
            while neighbor_poly_idx != NO_NEIGHBOR:
                neighbor_normal = poly_normals[neighbor_poly_idx]
                average_normal += neighbor_normal
                neighbor_normals.append(neighbor_normal)

                # Lookup for new neighbor
                new_neighbor_poly_idx = NO_NEIGHBOR
                for j in range(3):
                    next_idx = (j + 1) % 3
                    if mesh_faces[neighbor_poly_idx][next_idx] == vert_idx:
                        new_neighbor_poly_idx = neighbors[neighbor_poly_idx][j]
                        if new_neighbor_poly_idx == prev_neighbor_poly_idx:
                            new_neighbor_poly_idx = neighbors[neighbor_poly_idx][next_idx]
                        prev_neighbor_poly_idx = neighbor_poly_idx
                        neighbor_poly_idx = new_neighbor_poly_idx
                        break
                else:
                    break

                # Check if we've closed circle and iterated through all neighbors
                if new_neighbor_poly_idx == poly_idx:
                    break

            # After adding bunch of normals together we have to re-normalize it
            average_normal.normalize()

            if len(neighbor_normals) == 0:
                output_vertices[vert_idx] = vertex - normal * margin
            elif len(neighbor_normals) == 1:
                cross = normal.cross(neighbor_normals[0])
                cross_mag2 = cross.length_squared

                # Very small angle between two normals, just shrink using base normal
                if cross_mag2 < 0.1:
                    output_vertices[vert_idx] = vertex - normal * margin
                    continue

                # Insert new normal in weighted set
                neighbor_normals.append(cross.normalized())

            if len(neighbor_normals) < 2:
                continue

            # Default shrink by average normal
            shrunk = vertex - average_normal * margin

            # Traverse all normal & compute weighted normals
            normals = [normal]
            normals.extend(neighbor_normals)
            for i in range(len(neighbor_normals) - 1):
                for j in range(len(neighbor_normals) - i - 1):
                    for k in range(len(neighbor_normals) - j - i - 1):
                        normal1 = normals[i]
                        normal2 = normals[i + j + 1]
                        normal3 = normals[i + j + k + 2]

                        cross23 = normal2.cross(normal3)
                        dot = normal1.dot(cross23)

                        # Check out neighbors whose normals direction is too similar (small angle between neighbor normals & polygon normal)
                        if abs(dot) > 0.25:
                            # More neighbors normals are aligned with polygon normal, less weight will be applied
                            # Normals with higher angle (closer to 0.25) will contribute more to weighted normal

                            # Compute new weighted normal
                            cross31 = normal3.cross(normal1)
                            cross12 = normal1.cross(normal2)
                            new_normal = (cross23 + cross31 + cross12) / dot
                            new_shrunk = vertex - new_normal * margin

                            # Pick shrunk vertex that's more distant from original vertex
                            if Vector(new_shrunk - vertex).length_squared > Vector(shrunk - vertex).length_squared:
                                shrunk = new_shrunk

            # Insert final shrunk vertex in out buffer
            output_vertices[vert_idx] = shrunk

    return output_vertices


def _compute_neighbors(mesh_vertices, mesh_faces):
    # Each triangle has up to 3 neighbors, so same shape as the mesh_faces array
    neighbors = np.full_like(mesh_faces, NO_NEIGHBOR, dtype=int)

    num_polys = len(mesh_faces)

    vertex_to_polys = [[] for _ in range(len(mesh_vertices))]
    for i, poly_verts in enumerate(mesh_faces):
        for vi in poly_verts:
            vertex_to_polys[vi].append(i)

    def _get_next_l(idx):
        return (idx + 1) % 3

    def _get_next_r(idx):
        return 2 if idx == 0 else idx - 1

    for lhs_poly_idx in range(num_polys):
        lhs_poly_verts = mesh_faces[lhs_poly_idx]
        for lhs_poly_vert_idx, lhs_vert_idx in enumerate(lhs_poly_verts):
            lhs_vert_idx_next = lhs_poly_verts[_get_next_l(lhs_poly_vert_idx)]

            adjacent_polys = vertex_to_polys[lhs_vert_idx]
            for rhs_poly_idx in adjacent_polys:
                if lhs_poly_idx == rhs_poly_idx:
                    continue

                if rhs_poly_idx <= lhs_poly_idx:
                    continue

                found = False
                rhs_poly_verts = mesh_faces[rhs_poly_idx]
                for rhs_poly_vert_idx, rhs_vert_idx in enumerate(rhs_poly_verts):
                    if lhs_vert_idx != rhs_vert_idx:
                        continue

                    rhs_poly_vert_idx_next = _get_next_r(rhs_poly_vert_idx)
                    rhs_vert_idx_next = rhs_poly_verts[rhs_poly_vert_idx_next]

                    if lhs_vert_idx_next != rhs_vert_idx_next:
                        continue

                    neighbors[lhs_poly_idx][lhs_poly_vert_idx] = rhs_poly_idx
                    neighbors[rhs_poly_idx][rhs_poly_vert_idx_next] = lhs_poly_idx
                    found = True
                    break

                if found:
                    break

    return neighbors


def grow_sphere(center: Vector, radius: float, point: Vector, point_radius: float) -> float:
    """Calculates the new radius of a sphere that needs to grow such that the point (with its radius) is enclosed
    within the sphere. If the current radius is already sufficient to include the point and its radius, returns the
    current radius.
    """
    dist = (point - center).length + point_radius
    return dist if dist > radius else radius


def tris_areas(tris_array: NDArray) -> NDArray:
    """Calculate the area of each triangle in the array."""
    assert tris_array.ndim == 3 and tris_array.shape[1:] == (3, 3), \
        f"Expected shape (N, 3, 3) for 'tris_array', got: {tris_array.shape}"

    v0, v1, v2 = tris_array[:, 0], tris_array[:, 1], tris_array[:, 2]

    areas = np.linalg.norm(np.cross(v0 - v1, v2 - v1, axis=1), axis=1) / 2
    return areas


def tris_areas_from_verts(v0: NDArray, v1: NDArray, v2: NDArray) -> NDArray:
    """Calculate the area of each triangle in the arrays. Triangle vertices passed as separate arrays."""
    assert v0.ndim == 2 and v0.shape[1] == 3, \
        f"Expected shape (N, 3) for 'v0', got: {v0.shape}"
    assert v1.ndim == 2 and v1.shape[1] == 3, \
        f"Expected shape (N, 3) for 'v1', got: {v1.shape}"
    assert v2.ndim == 2 and v2.shape[1] == 3, \
        f"Expected shape (N, 3) for 'v2', got: {v2.shape}"

    areas = np.linalg.norm(np.cross(v0 - v1, v2 - v1, axis=1), axis=1) / 2
    return areas


def tris_normals(tris_array: NDArray) -> NDArray:
    """Calculate the normal of each triangle in the array."""
    assert tris_array.ndim == 3 and tris_array.shape[1:] == (3, 3), \
        f"Expected shape (N, 3, 3), got: {tris_array.shape}"

    v0, v1, v2 = tris_array[:, 0], tris_array[:, 1], tris_array[:, 2]

    normals = np.cross(v0 - v1, v2 - v1)

    # normalize normal vectors
    lengths = np.linalg.norm(normals, axis=1, keepdims=True)
    np.divide(normals, lengths, out=normals, where=lengths != 0)

    return normals


def distance_signed_point_to_planes(point_3d: Sequence[float], planes_co: NDArray, planes_normals: NDArray) -> NDArray[np.float32]:
    """Calculate the signed distances of a point to each plane represented by the `planes_co` and `planes_normals` arrays."""
    point_3d = np.array(point_3d)

    assert point_3d.ndim == 1 and point_3d.shape[0] == 3, \
        f"Expected shape (3) for 'point_3d', got: {point_3d.shape}"
    assert planes_co.ndim == 2 and planes_co.shape[1] == 3, \
        f"Expected shape (N, 3) for 'planes_co', got: {planes_co.shape}"
    assert planes_normals.ndim == 2 and planes_normals.shape[1] == 3, \
        f"Expected shape (N, 3) for 'planes_normals', got: {planes_normals.shape}"
    assert len(planes_co) == len(planes_normals), \
        f"Expected same number of plane coordinates and normals, got: {len(planes_co)} and {len(planes_normals)}"

    D = -np.sum(planes_normals * planes_co, axis=1)

    # Assumes plane normals are already normalized
    distances = np.sum(planes_normals * point_3d, axis=1) + D

    return distances
