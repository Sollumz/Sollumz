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
import random
import time
from mathutils import Vector, Matrix
from bpy.props import BoolProperty, FloatProperty, IntProperty, EnumProperty
import numpy as np
from Sollumz.meshhelper import get_distance_of_vectors, create_box_from_extents


def bbox_orient(bme_verts, mx):
    '''
    takes a lsit of BMverts ora  list of vectors
    '''
    if hasattr(bme_verts[0], 'co'):
        verts = [mx @ v.co for v in bme_verts]
    else:
        verts = [mx @ v for v in bme_verts]

    xs = [v[0] for v in verts]
    ys = [v[1] for v in verts]
    zs = [v[2] for v in verts]

    return (min(xs), max(xs), min(ys), max(ys), min(zs), max(zs))


def bbox_vol(box):

    V = (box[1]-box[0]) * (box[3]-box[2]) * (box[5]-box[4])

    return V


def box_cords(box):
    '''
    returns vertices in same configuration as default cube in blender
    easy to asign v.co of a cube primitive
    '''
    cords = [Vector((box[0], box[2], box[4])),
             Vector((box[0], box[2], box[5])),
             Vector((box[0], box[3], box[4])),
             Vector((box[0], box[3], box[5])),
             Vector((box[1], box[2], box[4])),
             Vector((box[1], box[2], box[5])),
             Vector((box[1], box[3], box[4])),
             Vector((box[1], box[3], box[5])),
             ]

    return cords


def get_obb_dimensions(bbmin, bbmax):
    bbox = bpy.data.meshes.new('bbox')
    create_box_from_extents(
        bbox, bbmin, bbmax)
    edge_lengths = []
    for edge in bbox.edges:
        v1 = bbox.vertices[edge.vertices[0]].co
        v2 = bbox.vertices[edge.vertices[1]].co
        edge_lengths.append(get_distance_of_vectors(v1, v2))
    edge_lengths = np.array(edge_lengths)
    height = edge_lengths.max(axis=0)
    width = edge_lengths.min(axis=0)
    return height, width


def get_obb_extents(obb):
    np_obb = np.array(obb)
    return Vector(np_obb.min(axis=0)), Vector(np_obb.max(axis=0))


def get_obb(verts):
    start = time.time()
    # rand_sample = 400  #randomly select this many directions on a solid hemisphere to measure from
    # spin_res = 180   #180 steps is 0.5 degrees

    world_mx = Matrix.Identity(4)
    scale = world_mx.to_scale()
    trans = world_mx.to_translation()

    tr_mx = Matrix.Identity(4)
    sc_mx = Matrix.Identity(4)

    tr_mx[0][3], tr_mx[1][3], tr_mx[2][3] = trans[0], trans[1], trans[2]
    sc_mx[0][0], sc_mx[1][1], sc_mx[2][2] = scale[0], scale[1], scale[2]
    r_mx = world_mx.to_quaternion().to_matrix().to_4x4()

    mesh = bpy.data.meshes.new('obb')
    bme = bmesh.new()
    bme.from_mesh(mesh)

    for vert in verts:
        bme.verts.new(vert)

    convex_hull = bmesh.ops.convex_hull(
        bme, input=bme.verts, use_existing_faces=True)
    total_hull = convex_hull['geom']

    hull_verts = [item for item in total_hull if hasattr(item, 'co')]

    min_mx = Matrix.Identity(4)
    min_box = bbox_orient(hull_verts, min_mx)
    min_axis = Vector((0, 0, 1))
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
            angle = math.pi/2 * n/40
            rot_mx = Matrix.Rotation(angle, 4, axis)

            box = bbox_orient(hull_verts, rot_mx)
            test_V = bbox_vol(box)

            if test_V < min_V:
                min_V = test_V
                min_box = box
                min_axis = axis
                min_mx = rot_mx
    elapsed_time = time.time() - start
    bme.free()
    fmx = tr_mx @ r_mx @ min_mx.inverted_safe() @ sc_mx
    rot_mat = fmx.decompose()[1].to_matrix().to_4x4()
    print(rot_mat.to_quaternion(), axis)

    box_verts = box_cords(min_box)

    return box_verts, axis, fmx
