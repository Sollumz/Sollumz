# Source: https://github.com/patmo141/object_bounding_box

# Copyright (C) 2015  Patrick Moore  patrick.moore.bu@gmail.com

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.

# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

import bpy
import bmesh
import math
import time
from mathutils import Vector, Matrix
import numpy as np


def bbox_orient(bme_verts, mx):
    """
    takes a lsit of BMverts ora  list of vectors
    """
    if hasattr(bme_verts[0], "co"):
        verts = [mx @ v.co for v in bme_verts]
    else:
        verts = [mx @ v for v in bme_verts]

    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]

    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def bbox_vol(box):

    V = (box[1] - box[0]) * (box[3] - box[2]) * (box[5] - box[4])

    return V


def box_coords(box):
    """
    returns vertices in same configuration as default cube in blender
    easy to asign v.co of a cube primitive
    """
    coords = [Vector((box[0], box[2], box[4])),
              Vector((box[0], box[2], box[5])),
              Vector((box[0], box[3], box[4])),
              Vector((box[0], box[3], box[5])),
              Vector((box[1], box[2], box[4])),
              Vector((box[1], box[2], box[5])),
              Vector((box[1], box[3], box[4])),
              Vector((box[1], box[3], box[5])),
              ]

    return coords


def get_obb_extents(obb):
    np_obb = np.array(obb, dtype=Vector)
    return Vector(np_obb.min(axis=0)), Vector(np_obb.max(axis=0))


def get_obb(verts):
    world_mx = Matrix.Identity(4)
    scale = world_mx.to_scale()
    trans = world_mx.to_translation()

    tr_mx = Matrix.Identity(4)
    sc_mx = Matrix.Identity(4)

    tr_mx[0][3], tr_mx[1][3], tr_mx[2][3] = trans[0], trans[1], trans[2]
    sc_mx[0][0], sc_mx[1][1], sc_mx[2][2] = scale[0], scale[1], scale[2]
    r_mx = world_mx.to_quaternion().to_matrix().to_4x4()

    mesh = bpy.data.meshes.new("obb")
    bme = bmesh.new()
    bme.from_mesh(mesh)

    for vert in verts:
        bme.verts.new(vert)

    convex_hull = bmesh.ops.convex_hull(
        bme, input=bme.verts, use_existing_faces=True)
    total_hull = convex_hull["geom"]

    hull_verts = [item for item in total_hull if hasattr(item, "co")]

    min_mx = Matrix.Identity(4)
    min_box = bbox_orient(hull_verts, min_mx)
    min_V = bbox_vol(min_box)
    axes = []
    # Iterate through all degrees to obtain a more predictable result
    for i in range(0, 360):
        theta = math.radians(i)
        phi = (1 + 5 ** 0.5) / 2

        x = math.cos(theta) * math.sin(phi)
        y = math.sin(theta) * math.sin(phi)
        z = math.cos(phi)

        axis = Vector((x, y, z))
        axes.append(axis)
        for n in range(0, 40):
            angle = math.pi / 2 * n / 40
            rot_mx = Matrix.Rotation(angle, 4, axis)

            box = bbox_orient(hull_verts, rot_mx)
            test_V = bbox_vol(box)

            if test_V < min_V:
                min_V = test_V
                min_box = box
                min_axis = axis
                min_mx = rot_mx

    bme.free()
    fmx = tr_mx @ r_mx @ min_mx.inverted_safe() @ sc_mx

    box_verts = box_coords(min_box)

    return box_verts, fmx
